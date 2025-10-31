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
from django.db import transaction

from apps.proxmox import ProxmoxService, ProxmoxError
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
        DeploymentLog.objects.create(application=app, level=level, message=message, step=step)
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
    owner_id: int,
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
    logger.info("=" * 100)
    logger.info(f"[TASK START] --- Starting deployment for Application ID: {app_id} ---")
    logger.info(
        f"[TASK START] Parameters: hostname={hostname}, catalog_id={catalog_id}, node={node}, host_id={host_id}"
    )
    logger.info(f"[TASK START] Config: {config}")
    logger.info(f"[TASK START] Environment: {environment}")
    logger.info(f"[TASK START] Owner ID: {owner_id}")
    logger.info("=" * 100)

    try:
        log_deployment(app_id, "info", f"Starting deployment of {hostname}", "init")

        # STEP 0: Use transaction to ensure we read committed data
        logger.info(f"[{app_id}] STEP 0: Acquiring application record with transaction lock...")
        with transaction.atomic():
            app = Application.objects.select_for_update().get(id=app_id)
            logger.info(
                f"[{app_id}] ✓ Application locked: current_status={app.status}, lxc_id={app.lxc_id}"
            )

            logger.info(f"[{app_id}] → Setting status to 'deploying'...")
            app.status = "deploying"
            app.save(update_fields=["status"])
            logger.info(f"[{app_id}] ✓ Database committed: status='deploying'")

        logger.info(f"[{app_id}] STEP 0 COMPLETE: Application status set to 'deploying'")

        # TESTING MODE: Simulate deployment without Proxmox
        # Also activate when USE_MOCK_PROXMOX=1 for E2E tests
        import os

        is_mock_mode = os.getenv("USE_MOCK_PROXMOX") == "1"

        if settings.TESTING_MODE or is_mock_mode:
            mode_name = "TEST MODE" if settings.TESTING_MODE else "MOCK MODE"
            logger.warning(
                f"[{app_id}] ⚠️  {mode_name} ACTIVE - Simulating deployment (NO REAL PROXMOX DEPLOYMENT)"
            )
            log_deployment(app_id, "info", f"[{mode_name}] Simulating deployment...", "test_mode")
            time.sleep(2)  # Simulate deployment time

            # Assign unique fake VMID (find next available starting from 9000)
            test_vmid = 9000
            while Application.objects.filter(lxc_id=test_vmid).exists():
                test_vmid += 1

            logger.info(f"[{app_id}] 🔢 [TEST MODE] Allocated test VMID: {test_vmid}")

            app.lxc_id = test_vmid
            app.status = "running"
            app.lxc_root_password = "test-password"
            app.updated_at = timezone.now()
            app.save(update_fields=["lxc_id", "status", "lxc_root_password", "updated_at"])

            log_deployment(
                app_id, "info", "[TEST MODE] Deployment simulated successfully", "complete"
            )

            return {
                "success": True,
                "app_id": app_id,
                "vmid": test_vmid,
                "hostname": hostname,
                "status": "running",
                "testing_mode": True,
            }

        # REAL DEPLOYMENT MODE
        logger.info(f"[{app_id}] STEP 1: REAL DEPLOYMENT MODE - Deploying to Proxmox!")

        # Initialize services
        logger.info(f"[{app_id}] STEP 1.1: Initializing ProxmoxService for host_id={host_id}...")
        try:
            proxmox_service = ProxmoxService(host_id=host_id)
            logger.info(f"[{app_id}] ✓ ProxmoxService initialized successfully")
        except Exception as e:
            logger.error(f"[{app_id}] ❌ Failed to initialize ProxmoxService: {e}", exc_info=True)
            raise

        log_deployment(app_id, "info", "Allocating VMID...", "vmid")

        # 🔐 RACE CONDITION FIX: Use database transaction lock to prevent VMID conflicts
        # Without locking, two concurrent tasks could get the same VMID:
        # Task A: gets candidate_vmid=100, checks (unused)
        # Task B: gets candidate_vmid=100, checks (unused)
        # Task A: assigns 100
        # Task B: assigns 100 (DUPLICATE!)
        # Solution: Lock the Application record while allocating

        logger.info(f"[{app_id}] 🔢 Requesting next available VMID from Proxmox...")
        max_attempts = 10
        vmid = None

        # Lock the current application to prevent concurrent VMID allocation
        with transaction.atomic():
            app_locked = Application.objects.select_for_update().get(id=app_id)

            for attempt in range(max_attempts):
                candidate_vmid = proxmox_service.get_next_vmid()

                # Check if this VMID is already in use in our database
                # (this query is now protected by the row lock above)
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

                    if existing_app.status == "error":
                        # Clear the lxc_id from the orphaned application
                        logger.info(
                            f"[{app_id}] 🧹 Clearing lxc_id from orphaned application: {existing_app.hostname}"
                        )
                        existing_app.lxc_id = None
                        existing_app.save(update_fields=["lxc_id"])

                        # Now we can use this VMID
                        vmid = candidate_vmid
                        logger.info(f"[{app_id}] ✓ Allocated VMID after cleanup: {vmid}")
                        break
                    else:
                        # VMID is legitimately in use, try again
                        logger.info(
                            f"[{app_id}] 🔄 VMID {candidate_vmid} is in use, trying again..."
                        )
                        continue

            if vmid is None:
                raise Exception(f"Failed to allocate unique VMID after {max_attempts} attempts")

            # Assign VMID within the same transaction to ensure atomicity
            app_locked.lxc_id = vmid
            app_locked.save(update_fields=["lxc_id"])
            logger.info(f"[{app_id}] ✓ VMID {vmid} committed atomically to database")

        log_deployment(app_id, "info", f"Allocated VMID: {vmid}", "vmid")

        # Generate root password (TODO: Use encryption service from v1.0)
        import secrets

        root_password = secrets.token_urlsafe(16)
        logger.info(f"[{app_id}] 🔐 Generated root password (length: {len(root_password)})")

        log_deployment(app_id, "info", "Creating LXC container...", "lxc_create")

        # Create LXC container with Alpine Linux
        # Alpine is lightweight and perfect for Docker containers
        # TODO: Get ostemplate from catalog configuration
        ostemplate = config.get(
            "ostemplate", "local:vztmpl/alpine-3.22-default_20250617_amd64.tar.xz"
        )
        memory = config.get("memory", 2048)
        cores = config.get("cores", 2)
        disk_size = config.get("disk_size", "8")

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
            disk_size=disk_size,
        )

        logger.info(f"[{app_id}] ✓ LXC container created successfully!")
        logger.info(f"[{app_id}] 📋 Create result: {create_result}")
        log_deployment(app_id, "info", f"LXC container created: {create_result}", "lxc_create")

        # Wait for container to be ready
        logger.info(f"[{app_id}] ⏳ Waiting 5 seconds for container to be ready...")
        time.sleep(5)

        # Configure container for Docker BEFORE starting it
        logger.info(f"[{app_id}] 🔧 Configuring LXC for Docker support (AppArmor: unconfined)...")
        proxmox_service.configure_lxc_for_docker(node, vmid)
        logger.info(f"[{app_id}] ✓ LXC configured for Docker!")

        log_deployment(app_id, "info", "Starting LXC container...", "lxc_start")

        # Start container
        logger.info(f"[{app_id}] ▶️  Starting LXC container (VMID: {vmid})...")
        proxmox_service.start_lxc(node, vmid)
        logger.info(f"[{app_id}] ✓ LXC container started successfully!")

        # Wait for container to start
        logger.info(f"[{app_id}] ⏳ Waiting 10 seconds for container to fully start...")
        time.sleep(10)

        log_deployment(app_id, "info", "Container started, checking Docker...", "docker_setup")

        # STEP 4: Setup Docker inside the container
        logger.info(f"[{app_id}] STEP 4: Setting up Docker in Alpine LXC container...")
        logger.info(f"[{app_id}] STEP 4.1: Importing DockerSetupService...")
        from apps.applications.docker_setup import DockerSetupService

        logger.info(f"[{app_id}] STEP 4.2: Initializing DockerSetupService...")
        docker_service = DockerSetupService(proxmox_service)

        logger.info(
            f"[{app_id}] STEP 4.3: Installing Docker in Alpine container (VMID={vmid}, Node={node})..."
        )
        try:
            docker_installed = docker_service.setup_docker_in_alpine(node, vmid)
            logger.info(f"[{app_id}] ✓ Docker installation returned: {docker_installed}")

            if not docker_installed:
                logger.error(f"[{app_id}] ❌ Docker installation returned False!")
                raise Exception("Failed to install Docker in container")

            logger.info(f"[{app_id}] STEP 4 COMPLETE: Docker installed successfully")
            log_deployment(app_id, "info", "Docker installed successfully", "docker_setup")
        except Exception as e:
            logger.error(
                f"[{app_id}] ❌ STEP 4 FAILED: Docker installation error: {e}", exc_info=True
            )
            raise

        # STEP 5: Deploy application with Docker Compose
        logger.info(f"[{app_id}] STEP 5: Deploying application with Docker Compose...")
        log_deployment(app_id, "info", "Docker ready, deploying application...", "app_deploy")

        logger.info(
            f"[{app_id}] STEP 5.1: Generating docker-compose configuration for {catalog_id}..."
        )
        if catalog_id == "adminer":
            docker_compose_config = docker_service.generate_adminer_compose(port=80)
            logger.info(
                f"[{app_id}] ✓ Generated Adminer docker-compose config: {docker_compose_config}"
            )
        else:
            # TODO: Get docker-compose from catalog
            logger.error(f"[{app_id}] ❌ Unsupported catalog_id: {catalog_id}")
            raise Exception(f"Unsupported app: {catalog_id}")

        logger.info(
            f"[{app_id}] STEP 5.2: Deploying with docker-compose (VMID={vmid}, Node={node})..."
        )
        try:
            app_deployed = docker_service.deploy_app_with_docker_compose(
                node, vmid, catalog_id, docker_compose_config
            )
            logger.info(f"[{app_id}] ✓ Docker compose deployment returned: {app_deployed}")

            if not app_deployed:
                logger.error(f"[{app_id}] ❌ Docker compose deployment returned False!")
                raise Exception("Failed to deploy application")

            logger.info(f"[{app_id}] STEP 5 COMPLETE: Application deployed successfully")
        except Exception as e:
            logger.error(
                f"[{app_id}] ❌ STEP 5 FAILED: Docker compose deployment error: {e}", exc_info=True
            )
            raise

        # STEP 6: Update application status to 'running'
        logger.info(f"[{app_id}] STEP 6: Updating application status to 'running'...")
        try:
            with transaction.atomic():
                # Re-fetch to get latest state
                app = Application.objects.select_for_update().get(id=app_id)
                logger.info(
                    f"[{app_id}] ✓ Re-fetched app: current_status={app.status}, lxc_id={app.lxc_id}"
                )

                logger.info(
                    f"[{app_id}] → Setting status='running', lxc_root_password=<hidden>, updated_at=now"
                )
                app.status = "running"
                app.lxc_root_password = root_password  # TODO: Encrypt this
                app.updated_at = timezone.now()
                app.save(update_fields=["status", "lxc_root_password", "updated_at"])
                logger.info(f"[{app_id}] ✓ Database committed: status='running'")

            logger.info(f"[{app_id}] STEP 6 COMPLETE: Application status updated to 'running'")
        except Exception as e:
            logger.error(f"[{app_id}] ❌ STEP 6 FAILED: Status update error: {e}", exc_info=True)
            raise

        log_deployment(app_id, "info", f"Deployment complete: {hostname}", "complete")

        logger.info("=" * 100)
        logger.info(f"[TASK SUCCESS] --- Deployment for {hostname} COMPLETED SUCCESSFULLY ---")
        logger.info(
            f"[TASK SUCCESS] VMID={vmid}, Hostname={hostname}, Status=running, App ID={app_id}"
        )
        logger.info("=" * 100)

        return {
            "success": True,
            "app_id": app_id,
            "vmid": vmid,
            "hostname": hostname,
            "status": "running",
        }

    except Exception as e:
        logger.error("=" * 100)
        logger.error(f"[TASK FAILED] --- Deployment for Application ID: {app_id} FAILED ---")
        logger.error(f"[TASK FAILED] Exception Type: {type(e).__name__}")
        logger.error(f"[TASK FAILED] Exception Message: {str(e)}")
        logger.error(f"[TASK FAILED] Hostname: {hostname}")
        logger.error(f"[TASK FAILED] Catalog ID: {catalog_id}")
        logger.error(f"[TASK FAILED] Node: {node}")
        logger.error(f"[TASK FAILED] Current Retry: {self.request.retries}/{self.max_retries}")
        logger.error("=" * 100)
        logger.exception("[TASK FAILED] Full traceback:")
        log_deployment(app_id, "error", f"Deployment failed: {str(e)}", "error")

        # 🔐 RETRY LOGIC FIX: Don't set to error before retrying
        # Only mark as error if retries are exhausted
        if self.request.retries < self.max_retries:
            # Still have retries left - don't set to error yet
            # Calculate exponential backoff with cap at 15 minutes
            retry_countdown = min(60 * (2**self.request.retries), 900)  # Cap at 15 minutes
            logger.error(
                f"[{app_id}] 🔄 Retrying... (attempt {self.request.retries + 1}/{self.max_retries}) in {retry_countdown}s"
            )
            raise self.retry(exc=e, countdown=retry_countdown)
        else:
            # All retries exhausted - NOW mark as error
            logger.error(
                f"[{app_id}] ❌ All {self.max_retries} retries exhausted. Marking as error."
            )
            try:
                with transaction.atomic():
                    app_error = Application.objects.select_for_update().get(id=app_id)
                    logger.error(
                        f"[{app_id}] Current state before error update: status={app_error.status}, lxc_id={app_error.lxc_id}"
                    )
                    app_error.status = "error"
                    app_error.updated_at = timezone.now()
                    app_error.save(update_fields=["status", "updated_at"])
                    logger.error(f"[{app_id}] ✓ Status set to 'error' after retry exhaustion")
            except Exception as db_error:
                logger.error(
                    f"[{app_id}] ❌ Failed to update status to 'error': {db_error}", exc_info=True
                )

            # Re-raise the original exception
            raise


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
        log_deployment(app_id, "info", "Starting application...", "start")

        proxmox_service = ProxmoxService(host_id=app.host_id)
        proxmox_service.start_lxc(app.node, app.lxc_id)

        # Wait for container to start
        time.sleep(5)

        app.status = "running"
        app.updated_at = timezone.now()
        app.save(update_fields=["status", "updated_at"])

        log_deployment(app_id, "info", "Application started", "start")

        return {"success": True, "status": "running"}

    except Exception as e:
        logger.error(f"Failed to start app {app_id}: {e}")
        log_deployment(app_id, "error", f"Start failed: {str(e)}", "start")
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
        log_deployment(app_id, "info", "Stopping application...", "stop")

        proxmox_service = ProxmoxService(host_id=app.host_id)
        proxmox_service.stop_lxc(app.node, app.lxc_id, force=force)

        # Wait for container to stop
        time.sleep(5)

        app.status = "stopped"
        app.updated_at = timezone.now()
        app.save(update_fields=["status", "updated_at"])

        log_deployment(app_id, "info", "Application stopped", "stop")

        return {"success": True, "status": "stopped"}

    except Exception as e:
        logger.error(f"Failed to stop app {app_id}: {e}")
        log_deployment(app_id, "error", f"Stop failed: {str(e)}", "stop")
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
        log_deployment(app_id, "info", "Restarting application...", "restart")

        # Stop the app
        stop_app_task(app_id, force=False)
        time.sleep(2)

        # Start the app
        start_app_task(app_id)

        log_deployment(app_id, "info", "Application restarted", "restart")

        return {"success": True, "status": "running"}

    except Exception as e:
        logger.error(f"Failed to restart app {app_id}: {e}")
        log_deployment(app_id, "error", f"Restart failed: {str(e)}", "restart")
        raise


@shared_task(bind=True, max_retries=3)
def clone_app_task(self, source_app_id: str, new_hostname: str, owner_id: int) -> Dict[str, Any]:
    """
    Clone an existing application to create a duplicate with a new hostname.

    This task orchestrates the complete cloning process:
    1. Fetch source application
    2. Create new Application record with 'cloning' status
    3. Assign new ports using PortManager
    4. Clone LXC container via Proxmox
    5. Start the cloned container
    6. Update new Application status to 'running'

    If any step fails, rollback is performed (delete new Application record and LXC if created).

    Args:
        source_app_id: ID of the application to clone
        new_hostname: Hostname for the cloned application
        owner_id: User ID who owns the new clone

    Returns:
        Clone operation result with new app_id
    """
    import uuid

    new_app = None
    new_lxc_created = False

    logger.info("=" * 100)
    logger.info(f"[CLONE TASK START] --- Cloning Application {source_app_id} ---")
    logger.info(f"[CLONE TASK] New hostname: {new_hostname}, Owner ID: {owner_id}")
    logger.info("=" * 100)

    try:
        # STEP 1: Fetch source application
        logger.info(f"[CLONE] STEP 1/6: Fetching source application {source_app_id}...")
        source_app = Application.objects.get(id=source_app_id)
        logger.info(f"[CLONE] ✓ Source app found: {source_app.name} (VMID: {source_app.lxc_id})")

        # Validate source app is in a stable state
        if source_app.status not in ["running", "stopped"]:
            raise ValueError(
                f"Cannot clone app in status '{source_app.status}'. Only running/stopped apps can be cloned."
            )

        # STEP 2: Create new Application record with 'cloning' status
        logger.info("[CLONE] STEP 2/6: Creating new Application record...")
        new_app_id = str(uuid.uuid4())

        # Assign new ports using PortManager
        port_manager = PortManagerService()
        public_port, internal_port = port_manager.allocate_ports()
        logger.info(f"[CLONE] ✓ Assigned ports: public={public_port}, internal={internal_port}")

        # Determine new VMID (get next available from Proxmox)
        proxmox_service = ProxmoxService(host_id=source_app.host_id)
        new_vmid = proxmox_service.get_next_vmid()
        logger.info(f"[CLONE] ✓ Next available VMID: {new_vmid}")

        # Create new Application record
        new_app = Application.objects.create(
            id=new_app_id,
            catalog_id=source_app.catalog_id,
            name=f"{source_app.name}-clone",
            hostname=new_hostname,
            status="cloning",
            public_port=public_port,
            internal_port=internal_port,
            lxc_id=new_vmid,
            lxc_root_password=source_app.lxc_root_password,  # Copy same password
            host=source_app.host,
            node=source_app.node,
            config=source_app.config.copy() if source_app.config else {},
            ports=source_app.ports.copy() if source_app.ports else {},
            volumes=source_app.volumes.copy() if source_app.volumes else [],
            environment=source_app.environment.copy() if source_app.environment else {},
            owner_id=owner_id,
        )
        logger.info(f"[CLONE] ✓ Created new Application: {new_app.id} (name: {new_app.name})")
        log_deployment(new_app.id, "info", f"Cloning from {source_app.name}", "clone")

        # STEP 3: Clone LXC container via Proxmox API
        logger.info(f"[CLONE] STEP 3/6: Cloning LXC {source_app.lxc_id} → {new_vmid}...")
        log_deployment(
            new_app.id, "info", "Cloning LXC container (may take several minutes)...", "clone"
        )

        proxmox_service.clone_lxc(
            node_name=source_app.node,
            source_vmid=source_app.lxc_id,
            new_vmid=new_vmid,
            new_hostname=new_hostname,
            full=True,  # Full clone (not linked)
            timeout=600,  # 10 minutes timeout
        )
        new_lxc_created = True
        logger.info("[CLONE] ✓ LXC cloned successfully")
        log_deployment(new_app.id, "info", "Container cloned successfully", "clone")

        # STEP 4: Configure cloned LXC for Docker (if source had Docker)
        logger.info("[CLONE] STEP 4/6: Configuring cloned container...")
        if source_app.config.get("supports_docker", False):
            logger.info("[CLONE]   → Source app supports Docker, configuring clone...")
            proxmox_service.configure_lxc_for_docker(new_vmid)
            logger.info("[CLONE]   ✓ Docker configuration applied")

        # STEP 5: Start the cloned container
        logger.info(f"[CLONE] STEP 5/6: Starting cloned container {new_vmid}...")
        log_deployment(new_app.id, "info", "Starting cloned container...", "clone")

        start_task = proxmox_service.start_lxc(source_app.node, new_vmid)
        if start_task:
            proxmox_service.wait_for_task(source_app.node, start_task, timeout=120)
        logger.info("[CLONE] ✓ Container started successfully")

        # Wait for container to be fully running
        time.sleep(5)

        # STEP 6: Update new Application status to 'running'
        logger.info("[CLONE] STEP 6/6: Updating application status to 'running'...")
        new_app.status = "running"
        new_app.url = f"http://{new_hostname}:{public_port}"
        new_app.save(update_fields=["status", "url"])

        logger.info(
            f"[CLONE] ✅ CLONE COMPLETE: {new_app.name} (ID: {new_app.id}, VMID: {new_vmid})"
        )
        log_deployment(new_app.id, "info", "Clone completed successfully", "clone")

        return {
            "success": True,
            "message": "Application cloned successfully",
            "new_app_id": new_app.id,
            "new_hostname": new_hostname,
            "new_vmid": new_vmid,
        }

    except Exception as e:
        logger.error(f"[CLONE] ❌ CLONE FAILED: {e}")

        # ROLLBACK: Clean up on failure
        try:
            if new_app:
                logger.warning("[CLONE] 🔄 ROLLBACK: Cleaning up failed clone...")
                log_deployment(new_app.id, "error", f"Clone failed: {str(e)}", "clone")

                # Delete LXC if it was created
                if new_lxc_created:
                    try:
                        logger.warning(f"[CLONE]   → Deleting LXC {new_app.lxc_id}...")
                        proxmox_service.delete_lxc(source_app.node, new_app.lxc_id, force=True)
                        logger.warning("[CLONE]   ✓ LXC deleted")
                    except Exception as lxc_error:
                        logger.error(
                            f"[CLONE]   ✗ Failed to delete LXC during rollback: {lxc_error}"
                        )

                # Release assigned ports
                try:
                    logger.warning("[CLONE]   → Releasing ports...")
                    port_manager.release_ports(new_app.public_port, new_app.internal_port)
                    logger.warning("[CLONE]   ✓ Ports released")
                except Exception as port_error:
                    logger.error(
                        f"[CLONE]   ✗ Failed to release ports during rollback: {port_error}"
                    )

                # Delete Application record
                try:
                    logger.warning("[CLONE]   → Deleting Application record...")
                    new_app.delete()
                    logger.warning("[CLONE]   ✓ Application record deleted")
                except Exception as db_error:
                    logger.error(
                        f"[CLONE]   ✗ Failed to delete Application during rollback: {db_error}"
                    )

                logger.warning("[CLONE] 🔄 ROLLBACK COMPLETE")
        except Exception as rollback_error:
            logger.error(f"[CLONE] ❌ ROLLBACK FAILED: {rollback_error}")

        raise


@shared_task(bind=True)
def delete_app_task(self, app_id: str, force: bool = True) -> Dict[str, Any]:
    """
    Delete an application with differentiated deletion based on adoption status.

    DOCTRINE POINT #1: ADOPTION-AWARE DELETION

    For ADOPTED containers (is_adopted=True):
        - SOFT DELETE: Release Proximity-managed resources only
        - Container remains untouched on Proxmox
        - Only removes database record and frees ports

    For NATIVE/DEPLOYED containers (is_adopted=False):
        - HARD DELETE: Full container destruction
        - Stops container, deletes from Proxmox, releases resources
        - Complete cleanup of all artifacts

    Args:
        app_id: Application ID
        force: Force deletion even if running (applies to native containers only)

    Returns:
        Operation result with adoption status
    """
    try:
        app = Application.objects.get(id=app_id)

        # DOCTRINE CHECK: Determine deletion strategy based on adoption status
        is_adopted = app.config.get("adopted", False)

        if is_adopted:
            # ═══════════════════════════════════════════════════════════════
            # SOFT DELETE PATH: Adopted Container
            # ═══════════════════════════════════════════════════════════════
            logger.info(
                f"[{app.name}] 🔖 ADOPTION-AWARE DELETE: Performing SOFT delete (adopted container)"
            )
            logger.info(
                f"[{app.name}] Strategy: Release Proximity resources, preserve container on Proxmox"
            )
            log_deployment(
                app_id,
                "info",
                "SOFT DELETE: Removing Proximity management (container preserved)",
                "soft_delete_start",
            )

            app.status = "removing"
            app.save(update_fields=["status"])

            # Release ports allocated by Proximity
            logger.info(
                f"[{app.name}] → Releasing Proximity-allocated ports (public={app.public_port}, internal={app.internal_port})..."
            )
            port_manager = PortManagerService()
            port_manager.release_ports(app.public_port, app.internal_port)
            logger.info(f"[{app.name}] ✓ Ports released successfully")

            # Delete ONLY the Application record - container remains untouched
            app_name = app.name
            original_vmid = app.config.get("original_vmid", app.lxc_id)
            original_node = app.node
            app.delete()

            logger.info(f"[{app_name}] ✅ SOFT DELETE COMPLETE")
            logger.info(f"[{app_name}] - Proximity management record removed")
            logger.info(
                f"[{app_name}] - Container VMID {original_vmid} preserved on node '{original_node}'"
            )
            logger.info(f"[{app_name}] - Container continues running independently on Proxmox")

            return {
                "success": True,
                "message": f"Adopted container {app_name} removed from Proximity (container preserved on Proxmox)",
                "deletion_type": "soft",
                "adopted": True,
                "vmid_preserved": original_vmid,
                "node": original_node,
            }

        # ═══════════════════════════════════════════════════════════════
        # HARD DELETE PATH: Native/Deployed Container
        # ═══════════════════════════════════════════════════════════════
        logger.info(
            f"[{app.name}] 🗑️  ADOPTION-AWARE DELETE: Performing HARD delete (native container)"
        )
        logger.info(f"[{app.name}] Strategy: Stop container → Delete container → Release resources")
        log_deployment(
            app_id,
            "info",
            "HARD DELETE: Destroying container and cleaning up resources",
            "hard_delete_start",
        )

        app.status = "removing"
        app.save(update_fields=["status"])

        # Initialize Proxmox service
        proxmox_service = ProxmoxService(host_id=app.host_id)

        # STEP 1/4: Issue STOP command and wait for task completion
        logger.info(
            f"[{app.name}] HARD DELETE - STEP 1/4: Issuing STOP command for LXC {app.lxc_id}..."
        )
        try:
            stop_task = proxmox_service.stop_lxc(app.node, app.lxc_id, force=True)
            logger.info(f"[{app.name}] ✓ STOP command issued successfully, UPID: {stop_task}")

            # Wait for the stop task to complete (crucial!)
            if stop_task:
                logger.info(f"[{app.name}] ⏳ Waiting for stop task to complete...")
                proxmox_service.wait_for_task(app.node, stop_task, timeout=120)
                logger.info(f"[{app.name}] ✓ Stop task completed successfully")
        except Exception as stop_error:
            # If already stopped, that's fine - we'll verify in next step
            logger.warning(
                f"[{app.name}] Stop command failed (may already be stopped): {stop_error}"
            )

        # STEP 2/4: VERIFY container is STOPPED (quick check after task completion)
        logger.info(
            f"[{app.name}] HARD DELETE - STEP 2/4: Verifying LXC {app.lxc_id} is STOPPED..."
        )
        max_wait_seconds = 30  # Reduced since task should already be done
        wait_interval = 3
        elapsed_time = 0

        while elapsed_time < max_wait_seconds:
            try:
                status_info = proxmox_service.get_lxc_status(app.node, app.lxc_id)
                current_status = status_info.get("status", "unknown")
                logger.info(
                    f"[{app.name}]   → Current status: '{current_status}' (waiting for 'stopped')"
                )

                if current_status == "stopped":
                    logger.info(f"[{app.name}]   ✓ CONFIRMED: Container {app.lxc_id} is STOPPED")
                    break

            except Exception as status_error:
                # Container might already be deleted or unreachable - treat as stopped
                logger.warning(
                    f"[{app.name}]   → Status check failed (container may be gone): {status_error}"
                )
                break

            time.sleep(wait_interval)
            elapsed_time += wait_interval
        else:
            # Loop finished without break - timeout!
            error_msg = (
                f"FATAL: Container {app.lxc_id} did not stop within {max_wait_seconds} seconds"
            )
            logger.error(f"[{app.name}] {error_msg}")
            raise ProxmoxError(error_msg)

        # STEP 3/4: Delete LXC container (now guaranteed to be stopped)
        logger.info(
            f"[{app.name}] HARD DELETE - STEP 3/4: Deleting LXC {app.lxc_id} from Proxmox..."
        )
        proxmox_service.delete_lxc(app.node, app.lxc_id, force=force)
        logger.info(f"[{app.name}] ✓ Container deleted successfully from Proxmox")

        # Wait for deletion to complete
        time.sleep(5)

        # STEP 4/4: Release resources and cleanup
        logger.info(
            f"[{app.name}] HARD DELETE - STEP 4/4: Releasing ports and cleaning up database..."
        )

        # Release ports
        port_manager = PortManagerService()
        port_manager.release_ports(app.public_port, app.internal_port)
        logger.info(f"[{app.name}] ✓ Ports released")

        # Delete application record
        app_name = app.name
        app_lxc_id = app.lxc_id
        app.delete()
        logger.info(f"[{app_name}] ✓ Database record removed")

        logger.info(f"[{app_name}] ✅ HARD DELETE COMPLETE")
        logger.info(f"[{app_name}] - Container VMID {app_lxc_id} destroyed on Proxmox")
        logger.info(f"[{app_name}] - All resources released")
        logger.info(f"[{app_name}] - All 4 steps completed successfully")

        return {
            "success": True,
            "message": f"Application {app_name} completely deleted",
            "deletion_type": "hard",
            "adopted": False,
            "vmid_destroyed": app_lxc_id,
        }

    except Application.DoesNotExist:
        logger.warning(f"Application {app_id} not found for deletion")
        return {"success": False, "message": "Application not found"}

    except Exception as e:
        logger.error(f"Failed to delete app {app_id}: {e}")
        log_deployment(app_id, "error", f"Delete failed: {str(e)}", "delete")
        raise


@shared_task(bind=True)
def reconciliation_task(self) -> Dict[str, Any]:
    """
    Periodic reconciliation task to identify and clean up orphan applications.

    This task compares the list of applications in the Proximity database with
    the actual list of LXC containers on all Proxmox hosts. Any applications
    that reference non-existent containers (orphans) are automatically purged.

    This ensures database consistency when containers are manually deleted from
    Proxmox without going through the Proximity interface.

    Scheduled to run periodically via Celery Beat.

    Returns:
        Reconciliation result dictionary
    """
    logger.info("🔄 [RECONCILIATION TASK] Starting scheduled reconciliation...")

    try:
        from apps.applications.services import ApplicationService

        result = ApplicationService.reconcile_applications()

        if result["success"]:
            logger.info(
                f"✅ [RECONCILIATION TASK] Completed successfully - "
                f"Purged {result['orphans_purged']}/{result['orphans_found']} orphan(s)"
            )
        else:
            logger.error(f"❌ [RECONCILIATION TASK] Failed - Errors: {result.get('errors', [])}")

        return result

    except Exception as e:
        logger.error(f"❌ [RECONCILIATION TASK] Unexpected error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@shared_task(bind=True)
def janitor_task(self) -> Dict[str, Any]:
    """
    Periodic janitor task to clean up applications stuck in transitional states.

    This task scans for applications that have been in transitional states
    (deploying, cloning, removing, updating) for longer than the allowed timeout
    period (1 hour). These "zombie" applications are marked as error to prevent
    them from being stuck in limbo indefinitely.

    The reconciliation service will handle actual cleanup of orphaned containers.
    This service focuses on ending transitional states safely.

    Scheduled to run every 6 hours via Celery Beat.

    Returns:
        Cleanup result dictionary
    """
    logger.info("🧹 [JANITOR TASK] Starting scheduled stuck applications cleanup...")

    try:
        from apps.applications.services import ApplicationService

        result = ApplicationService.cleanup_stuck_applications()

        if result["success"]:
            logger.info(
                f"✅ [JANITOR TASK] Completed successfully - "
                f"Marked {result['stuck_marked_error']}/{result['stuck_found']} stuck app(s) as error"
            )
        else:
            logger.error(f"❌ [JANITOR TASK] Failed - Errors: {result.get('errors', [])}")

        return result

    except Exception as e:
        logger.error(f"❌ [JANITOR TASK] Unexpected error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@shared_task(bind=True, max_retries=3)
def adopt_app_task(self, adoption_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adopt an existing LXC container into Proximity management.

    DOCTRINE POINT #4: THE "INFORMED" ADOPTION PROCESS

    This adoption process captures comprehensive container metadata to create
    a complete "clinical record" of the adopted container. This includes:
    - Actual runtime status (running/stopped) from Proxmox
    - Complete container configuration snapshot (pct config output)
    - Network configuration and IP addresses
    - Resource allocation (CPU, memory, disk)
    - Original creation date and metadata

    This rich metadata allows us to:
    1. Restore original configuration if needed
    2. Detect configuration drift over time
    3. Provide detailed history for troubleshooting
    4. Make informed decisions during lifecycle operations

    Args:
        adoption_data: Dictionary containing:
            - vmid: Container VMID to adopt
            - node_name: Node where container is running
            - suggested_type: Optional type hint (custom, nginx, postgres, etc.)
            - port_to_expose: Optional specific port to expose

    Returns:
        Adoption result dictionary
    """
    vmid = adoption_data["vmid"]
    node_name = adoption_data["node_name"]
    suggested_type = adoption_data.get("suggested_type", "custom")
    port_to_expose = adoption_data.get("port_to_expose")

    logger.info("=" * 100)
    logger.info(f"[ADOPT TASK START] --- Starting INFORMED adoption for Container VMID: {vmid} ---")
    logger.info("[ADOPT TASK START] DOCTRINE: Capture complete container metadata and state")
    logger.info(
        f"[ADOPT TASK START] Parameters: node={node_name}, suggested_type={suggested_type}, port={port_to_expose or 'auto-detect'}"
    )
    logger.info("=" * 100)

    app = None
    app_id = None

    try:
        from apps.proxmox.models import ProxmoxNode
        import uuid

        # Get node and host information
        logger.info(f"[ADOPT {vmid}] STEP 1/8: Retrieving node information...")
        try:
            node = ProxmoxNode.objects.get(name=node_name)
            host = node.host
            logger.info(
                f"[ADOPT {vmid}] ✓ Found node '{node_name}' on host '{host.name}' (ID: {host.id})"
            )
        except ProxmoxNode.DoesNotExist:
            logger.error(f"[ADOPT {vmid}] ❌ Node '{node_name}' not found in database")
            raise Exception(f"Node '{node_name}' not found")

        # Initialize Proxmox service
        logger.info(f"[ADOPT {vmid}] STEP 2/8: Connecting to Proxmox host...")
        try:
            proxmox_service = ProxmoxService(host_id=host.id)
            logger.info(f"[ADOPT {vmid}] ✓ ProxmoxService initialized")
        except Exception as e:
            logger.error(f"[ADOPT {vmid}] ❌ Failed to connect to Proxmox: {e}", exc_info=True)
            raise

        # DOCTRINE: Get comprehensive container information from Proxmox
        logger.info(f"[ADOPT {vmid}] STEP 3/8: Fetching comprehensive container information...")
        try:
            containers = proxmox_service.get_lxc_containers(node_name)
            container_info = next((c for c in containers if int(c.get("vmid")) == int(vmid)), None)

            if not container_info:
                logger.error(f"[ADOPT {vmid}] ❌ Container {vmid} not found on node {node_name}")
                raise Exception(f"Container {vmid} not found on node {node_name}")

            # DOCTRINE: Capture actual runtime status (not assumed)
            container_status = container_info.get("status", "unknown")
            container_name = container_info.get("name", f"container-{vmid}")
            container_uptime = container_info.get("uptime", 0)
            container_cpus = container_info.get("cpus", 1)
            container_maxmem = container_info.get("maxmem", 0)
            container_maxdisk = container_info.get("maxdisk", 0)

            logger.info(f"[ADOPT {vmid}] ✓ Container basic info:")
            logger.info(f"[ADOPT {vmid}]   - Name: {container_name}")
            logger.info(f"[ADOPT {vmid}]   - Status: {container_status}")
            logger.info(f"[ADOPT {vmid}]   - Uptime: {container_uptime}s")
            logger.info(f"[ADOPT {vmid}]   - CPUs: {container_cpus}")
            logger.info(f"[ADOPT {vmid}]   - Memory: {container_maxmem / (1024**3):.2f}GB")
            logger.info(f"[ADOPT {vmid}]   - Disk: {container_maxdisk / (1024**3):.2f}GB")

            # Use the container's original name as hostname
            hostname = container_name
            logger.info(
                f"[ADOPT {vmid}] 📝 Using original container name as hostname: '{hostname}'"
            )

        except StopIteration:
            logger.error(f"[ADOPT {vmid}] ❌ Container {vmid} not found")
            raise Exception(f"Container {vmid} not found")
        except Exception as e:
            logger.error(f"[ADOPT {vmid}] ❌ Error fetching container info: {e}", exc_info=True)
            raise

        # DOCTRINE: Capture complete container configuration snapshot
        logger.info(
            f"[ADOPT {vmid}] STEP 4/8: Capturing complete container configuration snapshot..."
        )
        container_config_snapshot = {}
        try:
            # Get detailed configuration (equivalent to 'pct config <vmid>')
            config_response = proxmox_service.proxmox.nodes(node_name).lxc(vmid).config.get()
            container_config_snapshot = dict(config_response)

            logger.info(f"[ADOPT {vmid}] ✓ Configuration snapshot captured:")
            logger.info(
                f"[ADOPT {vmid}]   - Hostname: {container_config_snapshot.get('hostname', 'N/A')}"
            )
            logger.info(
                f"[ADOPT {vmid}]   - OS Type: {container_config_snapshot.get('ostype', 'N/A')}"
            )
            logger.info(
                f"[ADOPT {vmid}]   - Architecture: {container_config_snapshot.get('arch', 'N/A')}"
            )
            logger.info(
                f"[ADOPT {vmid}]   - Memory: {container_config_snapshot.get('memory', 'N/A')}MB"
            )
            logger.info(
                f"[ADOPT {vmid}]   - Swap: {container_config_snapshot.get('swap', 'N/A')}MB"
            )
            logger.info(
                f"[ADOPT {vmid}]   - Root FS: {container_config_snapshot.get('rootfs', 'N/A')}"
            )

            # Extract network configuration
            net_configs = {
                k: v for k, v in container_config_snapshot.items() if k.startswith("net")
            }
            if net_configs:
                logger.info(f"[ADOPT {vmid}]   - Network interfaces: {len(net_configs)}")
                for net_key, net_value in net_configs.items():
                    logger.info(f"[ADOPT {vmid}]     • {net_key}: {net_value}")

        except Exception as config_error:
            logger.warning(
                f"[ADOPT {vmid}] ⚠️  Could not capture full config snapshot: {config_error}"
            )
            # Continue with adoption even if config capture fails
            container_config_snapshot = {"error": str(config_error)}

        # Detect listening ports (if container is running and port not specified)
        logger.info(f"[ADOPT {vmid}] STEP 5/8: Detecting listening ports...")
        detected_ports = []
        if not port_to_expose and container_status == "running":
            try:
                # Try to detect listening ports (this will require SSH or exec into container)
                # For now, we'll log that this feature is TODO
                logger.info(f"[ADOPT {vmid}] ⚠️  Auto port detection not yet implemented")
                logger.info(
                    f"[ADOPT {vmid}] 💡 Future: Will SSH into container and run 'netstat -tuln' or 'ss -tuln'"
                )
            except Exception as e:
                logger.warning(f"[ADOPT {vmid}] ⚠️  Could not detect ports: {e}")
        else:
            logger.info(
                f"[ADOPT {vmid}] ⊘ Skipping port detection (status={container_status}, manual_port={port_to_expose})"
            )

        # Determine which port to expose
        logger.info(f"[ADOPT {vmid}] STEP 6/8: Determining port to expose...")
        if port_to_expose:
            container_port = port_to_expose
            logger.info(f"[ADOPT {vmid}] 📌 Using user-specified port: {container_port}")
        elif detected_ports:
            container_port = detected_ports[0]
            logger.info(f"[ADOPT {vmid}] 🔍 Using detected port: {container_port}")
        else:
            # Default fallback - common HTTP port
            container_port = 80
            logger.info(f"[ADOPT {vmid}] 🔌 Using default fallback port: {container_port}")

        # Allocate public port for external access
        logger.info(f"[ADOPT {vmid}] STEP 7/8: Allocating public port...")
        try:
            port_manager = PortManagerService()
            public_port, _ = port_manager.allocate_ports()  # We only need public_port
            logger.info(f"[ADOPT {vmid}] ✓ Allocated public port: {public_port}")
            logger.info(
                f"[ADOPT {vmid}] 📌 Port mapping: {public_port} -> container:{container_port}"
            )
        except Exception as e:
            logger.error(f"[ADOPT {vmid}] ❌ Failed to allocate port: {e}", exc_info=True)
            raise

        # Generate application ID based on suggested type
        app_id = f"{suggested_type}-{uuid.uuid4().hex[:8]}"
        logger.info(f"[ADOPT {vmid}] 📋 Generated application ID: {app_id}")

        # DOCTRINE: Create Application record with COMPLETE metadata
        logger.info(
            f"[ADOPT {vmid}] STEP 8/8: Creating Application record with complete metadata..."
        )
        try:
            with transaction.atomic():
                app = Application.objects.create(
                    id=app_id,
                    catalog_id=suggested_type,  # Use suggested_type as catalog_id
                    name=hostname,  # Use original container name
                    hostname=hostname,  # Keep original hostname
                    status="adopting",  # Initial status
                    lxc_id=vmid,
                    node=node_name,
                    host_id=host.id,
                    public_port=public_port,
                    internal_port=container_port,  # Store the container's internal port
                    config={
                        # DOCTRINE: Rich adoption metadata
                        "adopted": True,
                        "original_vmid": vmid,
                        "original_name": container_name,
                        "adoption_date": timezone.now().isoformat(),
                        "suggested_type": suggested_type,
                        "container_port": container_port,
                        "detected_ports": detected_ports,
                        # DOCTRINE: Complete configuration snapshot (clinical record)
                        "proxmox_config_snapshot": container_config_snapshot,
                        # DOCTRINE: Resource allocation at adoption time
                        "resources_at_adoption": {
                            "cpus": container_cpus,
                            "memory_bytes": container_maxmem,
                            "disk_bytes": container_maxdisk,
                            "uptime_seconds": container_uptime,
                        },
                        # DOCTRINE: Original runtime status
                        "status_at_adoption": container_status,
                    },
                    environment={},
                )

                # Create adoption log
                DeploymentLog.objects.create(
                    application=app,
                    level="INFO",
                    message=f'Starting INFORMED adoption of existing container "{container_name}" (VMID {vmid}) with complete metadata capture',
                    step="adoption_start",
                )

                logger.info(
                    f"[ADOPT {vmid}] ✓ Application record created with complete metadata: {app_id}"
                )
        except Exception as e:
            logger.error(
                f"[ADOPT {vmid}] ❌ Failed to create Application record: {e}", exc_info=True
            )
            raise

        # DOCTRINE: Update status to match container's ACTUAL state (not assumed)
        logger.info(f"[ADOPT {vmid}] Finalizing adoption with actual container state...")

        # Set status based on actual container state from Proxmox
        final_status = "running" if container_status == "running" else "stopped"
        app.status = final_status
        app.save(update_fields=["status"])

        DeploymentLog.objects.create(
            application=app,
            level="INFO",
            message=(
                f'Successfully adopted container "{container_name}" with complete metadata. '
                f"Status: {final_status}, Port: {public_port}->{container_port}, "
                f"Resources: {container_cpus} CPUs, {container_maxmem / (1024**3):.2f}GB RAM"
            ),
            step="adoption_complete",
        )

        logger.info(f"[ADOPT {vmid}] ✅ INFORMED ADOPTION COMPLETED SUCCESSFULLY!")
        logger.info(f"[ADOPT {vmid}] Summary:")
        logger.info(f"[ADOPT {vmid}]   - Name: {hostname}")
        logger.info(f"[ADOPT {vmid}]   - Status: {final_status} (actual from Proxmox)")
        logger.info(f"[ADOPT {vmid}]   - URL: http://{host.host}:{public_port}")
        logger.info(f"[ADOPT {vmid}]   - Port mapping: {public_port} -> {container_port}")
        logger.info(
            f"[ADOPT {vmid}]   - Resources: {container_cpus} CPUs, {container_maxmem / (1024**3):.2f}GB RAM, {container_maxdisk / (1024**3):.2f}GB disk"
        )
        logger.info(
            f"[ADOPT {vmid}]   - Config snapshot: {len(container_config_snapshot)} keys captured"
        )
        logger.info("=" * 100)

        return {
            "success": True,
            "app_id": app_id,
            "vmid": vmid,
            "hostname": hostname,
            "original_name": container_name,
            "status": final_status,
            "public_port": public_port,
            "container_port": container_port,
            "suggested_type": suggested_type,
            "config_snapshot_captured": True,
            "config_keys_count": len(container_config_snapshot),
        }

    except ProxmoxError as e:
        # Proxmox-specific errors (connection, API errors)
        logger.error(f"[ADOPT {vmid}] ❌ Proxmox error during adoption: {str(e)}", exc_info=True)

        # Mark application as error if it was created
        if app and app_id:
            try:
                app.status = "error"
                app.save(update_fields=["status"])

                DeploymentLog.objects.create(
                    application=app,
                    level="ERROR",
                    message=f"Adoption failed - Proxmox error: {str(e)}",
                    step="adoption_error",
                )
            except Exception as log_error:
                logger.error(f"[ADOPT {vmid}] Failed to log error: {log_error}")

        # Retry Proxmox errors (likely transient)
        if self.request.retries < self.max_retries:
            retry_delay = min(2**self.request.retries * 60, 600)  # Cap at 10 minutes
            logger.info(
                f"[ADOPT {vmid}] 🔄 Retrying... (attempt {self.request.retries + 1}/{self.max_retries}) in {retry_delay}s"
            )
            raise self.retry(exc=e, countdown=retry_delay)

        logger.error(f"[ADOPT {vmid}] ❌ Adoption failed after {self.max_retries} retries")
        raise

    except Exception as e:
        # Generic/unexpected errors
        logger.error(f"[ADOPT {vmid}] ❌ Unexpected error during adoption: {str(e)}", exc_info=True)

        # Mark application as error if it was created
        if app and app_id:
            try:
                app.status = "error"
                app.save(update_fields=["status"])

                DeploymentLog.objects.create(
                    application=app,
                    level="ERROR",
                    message=f"Adoption failed - Unexpected error: {str(e)}",
                    step="adoption_error",
                )
            except Exception as log_error:
                logger.error(f"[ADOPT {vmid}] Failed to log error: {log_error}")

        # Don't retry unexpected errors - these are likely bugs
        logger.error(
            f"[ADOPT {vmid}] ❌ Not retrying unexpected error - this likely requires developer investigation"
        )
        raise
