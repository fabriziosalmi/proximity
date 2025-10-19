"""
Celery tasks for application lifecycle management.
All long-running operations are offloaded to Celery workers.
"""
import logging
import time
from typing import Dict, Any, Optional
from celery import shared_task
from django.utils import timezone
from django.conf import settings

from apps.proxmox.services import ProxmoxService, ProxmoxError
from apps.applications.models import Application, DeploymentLog
from apps.applications.port_manager import PortManagerService

logger = logging.getLogger(__name__)


def log_deployment(app_id: str, level: str, message: str, step: Optional[str] = None):
    """
    Helper to log deployment events.
    
    Args:
        app_id: Application ID
        level: Log level (info, warning, error)
        message: Log message
        step: Optional step name
    """
    try:
        app = Application.objects.get(id=app_id)
        DeploymentLog.objects.create(
            application=app,
            level=level,
            message=message,
            step=step
        )
        logger.info(f"[{app_id}] {message}")
    except Application.DoesNotExist:
        logger.error(f"Application {app_id} not found for logging")
    except Exception as e:
        logger.error(f"Failed to log deployment event: {e}")


@shared_task(bind=True, max_retries=3)
def deploy_app_task(
    self,
    app_id: str,
    catalog_id: str,
    hostname: str,
    host_id: int,
    node: str,
    config: Dict[str, Any],
    environment: Dict[str, str],
    owner_id: int
) -> Dict[str, Any]:
    """
    Deploy a new application as a Celery task.
    
    This is a long-running operation that creates an LXC container,
    configures it, and starts the application.
    
    Args:
        app_id: Unique application ID
        catalog_id: Catalog item ID
        hostname: Application hostname
        host_id: Proxmox host ID
        node: Target Proxmox node
        config: Application configuration
        environment: Environment variables
        owner_id: User ID who owns this app
        
    Returns:
        Deployment result dictionary
    """
    try:
        log_deployment(app_id, 'info', f'Starting deployment of {hostname}', 'init')
        logger.info(f"[{app_id}] 🚀 DEPLOYMENT STARTED - hostname={hostname}, node={node}, host_id={host_id}")
        
        # Get application record
        app = Application.objects.get(id=app_id)
        app.status = 'deploying'
        app.save(update_fields=['status'])
        logger.info(f"[{app_id}] ✓ Application status set to 'deploying'")
        
        # TESTING MODE: Simulate deployment without Proxmox
        if settings.TESTING_MODE:
            logger.warning(f"[{app_id}] ⚠️  TESTING MODE ACTIVE - Simulating deployment (NO REAL PROXMOX DEPLOYMENT)")
            log_deployment(app_id, 'info', '[TEST MODE] Simulating deployment...', 'test_mode')
            time.sleep(2)  # Simulate deployment time

            # Assign unique fake VMID (find next available starting from 9000)
            test_vmid = 9000
            while Application.objects.filter(lxc_id=test_vmid).exists():
                test_vmid += 1

            logger.info(f"[{app_id}] 🔢 [TEST MODE] Allocated test VMID: {test_vmid}")

            app.lxc_id = test_vmid
            app.status = 'running'
            app.lxc_root_password = 'test-password'
            app.updated_at = timezone.now()
            app.save(update_fields=['lxc_id', 'status', 'lxc_root_password', 'updated_at'])

            log_deployment(app_id, 'info', '[TEST MODE] Deployment simulated successfully', 'complete')

            return {
                'success': True,
                'app_id': app_id,
                'vmid': test_vmid,
                'hostname': hostname,
                'status': 'running',
                'testing_mode': True
            }
        
        # REAL DEPLOYMENT MODE
        logger.info(f"[{app_id}] 🔥 REAL DEPLOYMENT MODE - Deploying to Proxmox!")
        
        # Initialize services
        logger.info(f"[{app_id}] 📡 Initializing ProxmoxService for host_id={host_id}...")
        proxmox_service = ProxmoxService(host_id=host_id)
        logger.info(f"[{app_id}] ✓ ProxmoxService initialized successfully")
        
        log_deployment(app_id, 'info', f'Allocating VMID...', 'vmid')

        # Get next available VMID (with conflict resolution)
        logger.info(f"[{app_id}] 🔢 Requesting next available VMID from Proxmox...")
        max_attempts = 10
        vmid = None

        for attempt in range(max_attempts):
            candidate_vmid = proxmox_service.get_next_vmid()

            # Check if this VMID is already in use in our database
            existing_app = Application.objects.filter(lxc_id=candidate_vmid).first()

            if not existing_app:
                # VMID is unique, use it
                vmid = candidate_vmid
                logger.info(f"[{app_id}] ✓ Allocated unique VMID: {vmid}")
                break
            else:
                # VMID conflict - check if it's an orphaned record
                logger.warning(
                    f"[{app_id}] ⚠️  VMID {candidate_vmid} already in use by {existing_app.hostname} "
                    f"(status: {existing_app.status})"
                )

                if existing_app.status == 'error':
                    # Clear the lxc_id from the orphaned application
                    logger.info(f"[{app_id}] 🧹 Clearing lxc_id from orphaned application: {existing_app.hostname}")
                    existing_app.lxc_id = None
                    existing_app.save(update_fields=['lxc_id'])

                    # Now we can use this VMID
                    vmid = candidate_vmid
                    logger.info(f"[{app_id}] ✓ Allocated VMID after cleanup: {vmid}")
                    break
                else:
                    # VMID is legitimately in use, try again
                    logger.info(f"[{app_id}] 🔄 VMID {candidate_vmid} is in use, trying again...")
                    continue

        if vmid is None:
            raise Exception(f"Failed to allocate unique VMID after {max_attempts} attempts")

        app.lxc_id = vmid
        app.save(update_fields=['lxc_id'])

        log_deployment(app_id, 'info', f'Allocated VMID: {vmid}', 'vmid')
        
        # Generate root password (TODO: Use encryption service from v1.0)
        import secrets
        root_password = secrets.token_urlsafe(16)
        logger.info(f"[{app_id}] 🔐 Generated root password (length: {len(root_password)})")
        
        log_deployment(app_id, 'info', 'Creating LXC container...', 'lxc_create')
        
        # Create LXC container with Alpine Linux
        # Alpine is lightweight and perfect for Docker containers
        # TODO: Get ostemplate from catalog configuration
        ostemplate = config.get('ostemplate', 'local:vztmpl/alpine-3.22-default_20250617_amd64.tar.xz')
        memory = config.get('memory', 2048)
        cores = config.get('cores', 2)
        disk_size = config.get('disk_size', '8')
        
        logger.info(f"[{app_id}] 📦 LXC Configuration:")
        logger.info(f"[{app_id}]    - Template: {ostemplate}")
        logger.info(f"[{app_id}]    - Memory: {memory}MB")
        logger.info(f"[{app_id}]    - Cores: {cores}")
        logger.info(f"[{app_id}]    - Disk: {disk_size}GB")
        logger.info(f"[{app_id}]    - Hostname: {hostname}")
        logger.info(f"[{app_id}]    - VMID: {vmid}")
        logger.info(f"[{app_id}]    - Node: {node}")
        
        logger.info(f"[{app_id}] 🏗️  Calling Proxmox API to create LXC container...")
        create_result = proxmox_service.create_lxc(
            node_name=node,
            vmid=vmid,
            hostname=hostname,
            ostemplate=ostemplate,
            password=root_password,
            memory=memory,
            cores=cores,
            disk_size=disk_size
        )
        
        logger.info(f"[{app_id}] ✓ LXC container created successfully!")
        logger.info(f"[{app_id}] 📋 Create result: {create_result}")
        log_deployment(app_id, 'info', f'LXC container created: {create_result}', 'lxc_create')
        
        # Wait for container to be ready
        logger.info(f"[{app_id}] ⏳ Waiting 5 seconds for container to be ready...")
        time.sleep(5)
        
        log_deployment(app_id, 'info', 'Starting LXC container...', 'lxc_start')
        
        # Start container
        logger.info(f"[{app_id}] ▶️  Starting LXC container (VMID: {vmid})...")
        proxmox_service.start_lxc(node, vmid)
        logger.info(f"[{app_id}] ✓ LXC container started successfully!")
        
        # Wait for container to start
        logger.info(f"[{app_id}] ⏳ Waiting 10 seconds for container to fully start...")
        time.sleep(10)
        
        log_deployment(app_id, 'info', 'Container started, checking Docker...', 'docker_setup')
        
        # Setup Docker inside the container
        logger.info(f"[{app_id}] 🐋 Setting up Docker in Alpine LXC container...")
        from apps.applications.docker_setup import DockerSetupService

        docker_service = DockerSetupService(proxmox_service)

        # Always install Docker in Alpine (fast with apk)
        # TODO: Implement template caching for even faster deployments
        logger.info(f"[{app_id}] 📦 Installing Docker in Alpine container...")
        docker_installed = docker_service.setup_docker_in_alpine(node, vmid)
        if not docker_installed:
            raise Exception("Failed to install Docker in container")

        logger.info(f"[{app_id}] ✓ Docker installed successfully")
        log_deployment(app_id, 'info', 'Docker installed successfully', 'docker_setup')

        log_deployment(app_id, 'info', 'Docker ready, deploying application...', 'app_deploy')

        # Deploy the application with Docker Compose
        logger.info(f"[{app_id}] 🚀 Deploying application with Docker Compose...")

        # Generate docker-compose configuration based on catalog_id
        if catalog_id == 'adminer':
            docker_compose_config = docker_service.generate_adminer_compose(port=80)
        else:
            # TODO: Get docker-compose from catalog
            raise Exception(f"Unsupported app: {catalog_id}")

        app_deployed = docker_service.deploy_app_with_docker_compose(
            node, vmid, catalog_id, docker_compose_config
        )

        if not app_deployed:
            raise Exception("Failed to deploy application")
        
        logger.info(f"[{app_id}] 💾 Updating application status to 'running'...")
        # Update application status
        app.status = 'running'
        app.lxc_root_password = root_password  # TODO: Encrypt this
        app.updated_at = timezone.now()
        app.save(update_fields=['status', 'lxc_root_password', 'updated_at'])
        logger.info(f"[{app_id}] ✓ Application status updated")
        
        log_deployment(app_id, 'info', f'Deployment complete: {hostname}', 'complete')
        logger.info(f"[{app_id}] 🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
        logger.info(f"[{app_id}] 📊 Summary: VMID={vmid}, Hostname={hostname}, Status=running")
        
        return {
            'success': True,
            'app_id': app_id,
            'vmid': vmid,
            'hostname': hostname,
            'status': 'running'
        }
        
    except Exception as e:
        logger.error(f"[{app_id}] ❌ DEPLOYMENT FAILED: {type(e).__name__}: {e}")
        logger.exception(f"[{app_id}] Full traceback:")
        log_deployment(app_id, 'error', f'Deployment failed: {str(e)}', 'error')
        
        # Update application status to error
        try:
            app = Application.objects.get(id=app_id)
            app.status = 'error'
            app.save(update_fields=['status'])
        except:
            pass
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True)
def start_app_task(self, app_id: str) -> Dict[str, Any]:
    """
    Start an application (start its LXC container).
    
    Args:
        app_id: Application ID
        
    Returns:
        Operation result
    """
    try:
        app = Application.objects.get(id=app_id)
        log_deployment(app_id, 'info', 'Starting application...', 'start')
        
        proxmox_service = ProxmoxService(host_id=app.host_id)
        proxmox_service.start_lxc(app.node, app.lxc_id)
        
        # Wait for container to start
        time.sleep(5)
        
        app.status = 'running'
        app.updated_at = timezone.now()
        app.save(update_fields=['status', 'updated_at'])
        
        log_deployment(app_id, 'info', 'Application started', 'start')
        
        return {'success': True, 'status': 'running'}
        
    except Exception as e:
        logger.error(f"Failed to start app {app_id}: {e}")
        log_deployment(app_id, 'error', f'Start failed: {str(e)}', 'start')
        raise


@shared_task(bind=True)
def stop_app_task(self, app_id: str, force: bool = False) -> Dict[str, Any]:
    """
    Stop an application (stop its LXC container).
    
    Args:
        app_id: Application ID
        force: Force stop (immediate)
        
    Returns:
        Operation result
    """
    try:
        app = Application.objects.get(id=app_id)
        log_deployment(app_id, 'info', 'Stopping application...', 'stop')
        
        proxmox_service = ProxmoxService(host_id=app.host_id)
        proxmox_service.stop_lxc(app.node, app.lxc_id, force=force)
        
        # Wait for container to stop
        time.sleep(5)
        
        app.status = 'stopped'
        app.updated_at = timezone.now()
        app.save(update_fields=['status', 'updated_at'])
        
        log_deployment(app_id, 'info', 'Application stopped', 'stop')
        
        return {'success': True, 'status': 'stopped'}
        
    except Exception as e:
        logger.error(f"Failed to stop app {app_id}: {e}")
        log_deployment(app_id, 'error', f'Stop failed: {str(e)}', 'stop')
        raise


@shared_task(bind=True)
def restart_app_task(self, app_id: str) -> Dict[str, Any]:
    """
    Restart an application (stop then start).
    
    Args:
        app_id: Application ID
        
    Returns:
        Operation result
    """
    try:
        log_deployment(app_id, 'info', 'Restarting application...', 'restart')
        
        # Stop the app
        stop_app_task(app_id, force=False)
        time.sleep(2)
        
        # Start the app
        start_app_task(app_id)
        
        log_deployment(app_id, 'info', 'Application restarted', 'restart')
        
        return {'success': True, 'status': 'running'}
        
    except Exception as e:
        logger.error(f"Failed to restart app {app_id}: {e}")
        log_deployment(app_id, 'error', f'Restart failed: {str(e)}', 'restart')
        raise


@shared_task(bind=True)
def delete_app_task(self, app_id: str, force: bool = True) -> Dict[str, Any]:
    """
    Delete an application (destroy LXC container and release resources).
    
    Args:
        app_id: Application ID
        force: Force deletion even if running
        
    Returns:
        Operation result
    """
    try:
        app = Application.objects.get(id=app_id)
        log_deployment(app_id, 'info', 'Deleting application...', 'delete')
        
        app.status = 'removing'
        app.save(update_fields=['status'])
        
        # Delete LXC container
        proxmox_service = ProxmoxService(host_id=app.host_id)
        proxmox_service.delete_lxc(app.node, app.lxc_id, force=force)
        
        # Wait for deletion to complete
        time.sleep(5)
        
        # Release ports
        port_manager = PortManagerService()
        port_manager.release_ports(app.public_port, app.internal_port)
        
        # Delete application record
        app_name = app.name
        app.delete()
        
        logger.info(f"Application {app_name} deleted successfully")
        
        return {'success': True, 'message': f'Application {app_name} deleted'}
        
    except Application.DoesNotExist:
        logger.warning(f"Application {app_id} not found for deletion")
        return {'success': False, 'message': 'Application not found'}
        
    except Exception as e:
        logger.error(f"Failed to delete app {app_id}: {e}")
        log_deployment(app_id, 'error', f'Delete failed: {str(e)}', 'delete')
        raise
