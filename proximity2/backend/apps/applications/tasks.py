"""
Celery tasks for application lifecycle management.
All long-running operations are offloaded to Celery workers.
"""
import logging
import time
from typing import Dict, Any, Optional
from celery import shared_task
from django.utils import timezone

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
        
        # Get application record
        app = Application.objects.get(id=app_id)
        app.status = 'deploying'
        app.save(update_fields=['status'])
        
        # Initialize services
        proxmox_service = ProxmoxService(host_id=host_id)
        
        log_deployment(app_id, 'info', f'Allocating VMID...', 'vmid')
        
        # Get next available VMID
        vmid = proxmox_service.get_next_vmid()
        app.lxc_id = vmid
        app.save(update_fields=['lxc_id'])
        
        log_deployment(app_id, 'info', f'Allocated VMID: {vmid}', 'vmid')
        
        # Generate root password (TODO: Use encryption service from v1.0)
        import secrets
        root_password = secrets.token_urlsafe(16)
        
        log_deployment(app_id, 'info', 'Creating LXC container...', 'lxc_create')
        
        # Create LXC container
        # TODO: Get ostemplate from catalog configuration
        ostemplate = config.get('ostemplate', 'local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst')
        memory = config.get('memory', 2048)
        cores = config.get('cores', 2)
        disk_size = config.get('disk_size', '8')
        
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
        
        log_deployment(app_id, 'info', f'LXC container created: {create_result}', 'lxc_create')
        
        # Wait for container to be ready
        time.sleep(5)
        
        log_deployment(app_id, 'info', 'Starting LXC container...', 'lxc_start')
        
        # Start container
        proxmox_service.start_lxc(node, vmid)
        
        # Wait for container to start
        time.sleep(10)
        
        log_deployment(app_id, 'info', 'Container started, configuring application...', 'app_config')
        
        # TODO: Execute setup scripts inside container
        # This would use the command execution service from v1.0
        # For now, we'll mark as running
        
        # Update application status
        app.status = 'running'
        app.lxc_root_password = root_password  # TODO: Encrypt this
        app.updated_at = timezone.now()
        app.save(update_fields=['status', 'lxc_root_password', 'updated_at'])
        
        log_deployment(app_id, 'info', f'Deployment complete: {hostname}', 'complete')
        
        return {
            'success': True,
            'app_id': app_id,
            'vmid': vmid,
            'hostname': hostname,
            'status': 'running'
        }
        
    except Exception as e:
        logger.error(f"Deployment failed for {app_id}: {e}")
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
