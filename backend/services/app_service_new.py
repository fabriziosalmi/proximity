import asyncio
import logging
import yaml
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session

from models.database import App as DBApp, DeploymentLog as DBDeploymentLog
from models.schemas import (
    App, AppCreate, AppUpdate, AppStatus, AppCatalogItem,
    DeploymentStatus, DeploymentLog, CatalogResponse
)
from services.proxmox_service import ProxmoxService, ProxmoxError
from core.config import settings

logger = logging.getLogger(__name__)


class AppServiceError(Exception):
    """Custom exception for App Service errors"""
    pass


def db_app_to_schema(db_app: DBApp) -> App:
    """Convert SQLAlchemy App model to Pydantic schema"""
    return App(
        id=db_app.id,
        catalog_id=db_app.catalog_id,
        name=db_app.name,
        hostname=db_app.hostname,
        status=AppStatus(db_app.status),
        url=db_app.url,
        lxc_id=db_app.lxc_id,
        node=db_app.node,
        created_at=db_app.created_at,
        updated_at=db_app.updated_at,
        config=db_app.config or {},
        ports=db_app.ports or {},
        volumes=db_app.volumes or [],
        environment=db_app.environment or {}
    )


class AppService:
    """Business logic layer for application management - SQLAlchemy backed"""

    def __init__(self, proxmox_service: ProxmoxService, proxy_manager=None):
        self.proxmox_service = proxmox_service
        self._proxy_manager = proxy_manager  # ReverseProxyManager for network appliance Caddy
        self._deployment_status: Dict[str, DeploymentStatus] = {}
        self._catalog_cache: Optional[CatalogResponse] = None
        self._caddy_service = None  # Legacy Caddy service (deprecated)
        self._catalog_loaded = False  # Track if catalog has been loaded

    @property
    def proxy_manager(self):
        """Lazy-load proxy_manager from FastAPI app state if not set"""
        return self._proxy_manager

    def set_proxy_manager(self, proxy_manager):
        """Set the proxy manager (called from main.py after initialization)"""
        self._proxy_manager = proxy_manager

    async def _load_catalog(self) -> None:
        """Load application catalog from individual app files"""
        if self._catalog_loaded and self._catalog_cache is not None:
            return  # Already loaded

        try:
            # Default to ./catalog relative to backend directory in development
            if settings.APP_CATALOG_PATH:
                catalog_path = Path(settings.APP_CATALOG_PATH)
            else:
                # Use relative path for development
                catalog_path = Path(__file__).parent.parent / "catalog"

            apps_dir = catalog_path / "apps"
            index_file = apps_dir / "index.json"

            logger.info(f"Looking for catalog in: {catalog_path}")

            # Check if new structure exists (individual app files)
            if apps_dir.exists() and index_file.exists():
                logger.info("Loading catalog from individual app files...")
                items = []

                # Read index to get list of app files
                import json
                with open(index_file, 'r') as f:
                    index_data = json.load(f)

                # Load each app file
                for app_file in index_data.get('apps', []):
                    app_path = apps_dir / app_file
                    if app_path.exists():
                        try:
                            with open(app_path, 'r') as f:
                                app_data = json.load(f)
                                items.append(AppCatalogItem(**app_data))
                                logger.debug(f"Loaded app: {app_data.get('name')}")
                        except Exception as e:
                            logger.error(f"Failed to load app from {app_file}: {e}")

                categories = list(set(item.category for item in items))

                self._catalog_cache = CatalogResponse(
                    items=items,
                    categories=categories,
                    total=len(items)
                )
                logger.info(f"✓ Loaded {len(items)} apps from {len(index_data.get('apps', []))} catalog files")

            # Fallback to old single catalog.json file
            elif (catalog_path / "catalog.json").exists():
                logger.info("Loading catalog from legacy catalog.json...")
                catalog_file = catalog_path / "catalog.json"
                import json
                with open(catalog_file, 'r') as f:
                    catalog_data = json.load(f)

                items = [AppCatalogItem(**item) for item in catalog_data.get('items', [])]
                categories = list(set(item.category for item in items))

                self._catalog_cache = CatalogResponse(
                    items=items,
                    categories=categories,
                    total=len(items)
                )
                logger.info(f"✓ Loaded {len(items)} items from legacy catalog")
            else:
                # Create default catalog
                logger.warning("No catalog found, creating default catalog...")
                await self._create_default_catalog()

            self._catalog_loaded = True  # Mark as loaded

        except Exception as e:
            logger.error(f"Failed to load catalog: {e}", exc_info=True)
            await self._create_default_catalog()
            self._catalog_loaded = True  # Mark as attempted

    async def _create_default_catalog(self) -> None:
        """Create a default catalog with common applications"""
        # ... (keep the same as original)
        default_items = [
            {
                "id": "wordpress",
                "name": "WordPress",
                "description": "Popular content management system",
                "version": "latest",
                "category": "CMS",
                "docker_compose": {
                    "version": "3.8",
                    "services": {
                        "wordpress": {
                            "image": "wordpress:latest",
                            "ports": ["80:80"],
                            "environment": {
                                "WORDPRESS_DB_HOST": "db",
                                "WORDPRESS_DB_USER": "wordpress",
                                "WORDPRESS_DB_PASSWORD": "wordpress",
                                "WORDPRESS_DB_NAME": "wordpress"
                            },
                            "volumes": ["wordpress_data:/var/www/html"],
                            "depends_on": ["db"]
                        },
                        "db": {
                            "image": "mysql:8.0",
                            "environment": {
                                "MYSQL_DATABASE": "wordpress",
                                "MYSQL_USER": "wordpress",
                                "MYSQL_PASSWORD": "wordpress",
                                "MYSQL_ROOT_PASSWORD": "rootpassword"
                            },
                            "volumes": ["db_data:/var/lib/mysql"]
                        }
                    },
                    "volumes": {
                        "wordpress_data": {},
                        "db_data": {}
                    }
                },
                "ports": [80],
                "min_memory": 1024,
                "min_cpu": 1
            }
        ]

        items = [AppCatalogItem(**item) for item in default_items]
        categories = list(set(item.category for item in items))

        self._catalog_cache = CatalogResponse(
            items=items,
            categories=categories,
            total=len(items)
        )
        logger.info("Created default catalog")

    async def get_catalog(self) -> CatalogResponse:
        """Get application catalog"""
        if self._catalog_cache is None:
            await self._load_catalog()
        return self._catalog_cache

    async def get_catalog_item(self, catalog_id: str) -> AppCatalogItem:
        """Get specific catalog item"""
        catalog = await self.get_catalog()
        for item in catalog.items:
            if item.id == catalog_id:
                return item
        raise AppServiceError(f"Catalog item '{catalog_id}' not found")

    async def get_all_apps(self, db: Session) -> List[App]:
        """Get all deployed applications from database"""
        try:
            db_apps = db.query(DBApp).all()

            # Sync with actual LXC containers
            await self._sync_apps_with_containers(db)

            # Convert to Pydantic schemas
            return [db_app_to_schema(app) for app in db_apps]

        except Exception as e:
            logger.error(f"Failed to get all apps: {e}")
            raise AppServiceError(f"Failed to get apps: {e}")

    async def get_app(self, db: Session, app_id: str) -> App:
        """Get specific application from database"""
        try:
            db_app = db.query(DBApp).filter(DBApp.id == app_id).first()

            if not db_app:
                raise AppServiceError(f"App '{app_id}' not found")

            # Update status from container
            try:
                lxc_status = await self.proxmox_service.get_lxc_status(db_app.node, db_app.lxc_id)
                if lxc_status.status.value == "running":
                    db_app.status = AppStatus.RUNNING.value
                elif lxc_status.status.value == "stopped":
                    db_app.status = AppStatus.STOPPED.value
                else:
                    db_app.status = AppStatus.ERROR.value

                db_app.updated_at = datetime.utcnow()
                db.commit()
            except ProxmoxError:
                db_app.status = AppStatus.ERROR.value
                db.commit()

            return db_app_to_schema(db_app)

        except AppServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to get app {app_id}: {e}")
            raise AppServiceError(f"Failed to get app: {e}")

    async def _sync_apps_with_containers(self, db: Session) -> None:
        """Sync app database with actual LXC containers and update URLs"""
        try:
            # Lazy-load Caddy service if needed
            if self._caddy_service is None:
                from services.caddy_service import get_caddy_service
                self._caddy_service = get_caddy_service(self.proxmox_service)

            containers = await self.proxmox_service.get_lxc_containers()
            db_apps = db.query(DBApp).all()

            for db_app in db_apps:
                # Find corresponding container
                container = next((c for c in containers if c.vmid == db_app.lxc_id), None)
                old_status = db_app.status

                if container:
                    if container.status.value == "running":
                        db_app.status = AppStatus.RUNNING.value

                        # Always refresh URL to ensure it's current
                        try:
                            # Get container IP
                            container_ip = await self.proxmox_service.get_lxc_ip(db_app.node, db_app.lxc_id)

                            if container_ip:
                                # Determine port (use first port from catalog or default to 80)
                                catalog_item = None
                                if self._catalog_cache:
                                    catalog_item = next((item for item in self._catalog_cache.items if item.id == db_app.catalog_id), None)
                                primary_port = catalog_item.ports[0] if catalog_item and catalog_item.ports else 80

                                # Check if Caddy is deployed
                                if self._caddy_service and self._caddy_service.is_deployed:
                                    is_caddy_running = await self._caddy_service.is_caddy_running()
                                    caddy_ip = await self._caddy_service.get_caddy_ip()

                                    if is_caddy_running and caddy_ip:
                                        # Use Caddy proxy URL
                                        new_url = f"http://{caddy_ip}:8080/{db_app.hostname}"
                                    else:
                                        # Caddy not running, use direct access
                                        new_url = f"http://{container_ip}:{primary_port}"
                                else:
                                    # Caddy not deployed, use direct access
                                    new_url = f"http://{container_ip}:{primary_port}"

                                # Update URL if changed
                                if db_app.url != new_url:
                                    logger.info(f"Updated URL for {db_app.id}: {db_app.url} → {new_url}")
                                    db_app.url = new_url
                            else:
                                logger.warning(f"Could not get IP for {db_app.id} (LXC {db_app.lxc_id})")

                        except Exception as url_error:
                            logger.warning(f"Failed to update URL for {db_app.id}: {url_error}")

                    elif container.status.value == "stopped":
                        db_app.status = AppStatus.STOPPED.value
                    else:
                        db_app.status = AppStatus.ERROR.value
                else:
                    # Container not found, mark as error
                    db_app.status = AppStatus.ERROR.value

                if old_status != db_app.status:
                    db_app.updated_at = datetime.utcnow()

            # Commit all changes
            db.commit()

        except Exception as e:
            logger.error(f"Failed to sync apps with containers: {e}")
            db.rollback()

    async def start_app(self, db: Session, app_id: str) -> App:
        """Start an application"""
        db_app = db.query(DBApp).filter(DBApp.id == app_id).first()

        if not db_app:
            raise AppServiceError(f"App '{app_id}' not found")

        try:
            # Start LXC container
            await self.proxmox_service.start_lxc(db_app.node, db_app.lxc_id)

            # Wait a bit for container to start
            await asyncio.sleep(2)

            # Start Docker Compose
            await self.proxmox_service.execute_in_container(
                db_app.node, db_app.lxc_id,
                "cd /root && docker compose up -d"
            )

            # Update status in database
            db_app.status = AppStatus.RUNNING.value
            db_app.updated_at = datetime.utcnow()
            db.commit()

            logger.info(f"Started app {app_id}")
            return db_app_to_schema(db_app)

        except Exception as e:
            db_app.status = AppStatus.ERROR.value
            db_app.updated_at = datetime.utcnow()
            db.commit()
            raise AppServiceError(f"Failed to start app: {e}")

    async def stop_app(self, db: Session, app_id: str) -> App:
        """Stop an application"""
        db_app = db.query(DBApp).filter(DBApp.id == app_id).first()

        if not db_app:
            raise AppServiceError(f"App '{app_id}' not found")

        try:
            # Stop Docker Compose
            await self.proxmox_service.execute_in_container(
                db_app.node, db_app.lxc_id,
                "cd /root && docker compose down"
            )

            # Stop LXC container
            await self.proxmox_service.stop_lxc(db_app.node, db_app.lxc_id)

            # Update status in database
            db_app.status = AppStatus.STOPPED.value
            db_app.updated_at = datetime.utcnow()
            db.commit()

            logger.info(f"Stopped app {app_id}")
            return db_app_to_schema(db_app)

        except Exception as e:
            db_app.status = AppStatus.ERROR.value
            db_app.updated_at = datetime.utcnow()
            db.commit()
            raise AppServiceError(f"Failed to stop app: {e}")

    async def restart_app(self, db: Session, app_id: str) -> App:
        """Restart an application"""
        await self.stop_app(db, app_id)
        await asyncio.sleep(2)
        return await self.start_app(db, app_id)

    async def delete_app(self, db: Session, app_id: str) -> None:
        """Delete an application and its LXC container"""
        db_app = db.query(DBApp).filter(DBApp.id == app_id).first()

        if not db_app:
            raise AppServiceError(f"App '{app_id}' not found")

        try:
            # Stop if running
            if db_app.status == AppStatus.RUNNING.value:
                await self.stop_app(db, app_id)

            # Remove from Caddy reverse proxy if available
            if self._caddy_service is not None:
                try:
                    await self._caddy_service.remove_application(app_id)
                    logger.info(f"Removed {app_id} from reverse proxy")
                except Exception as caddy_error:
                    logger.warning(f"Failed to remove app from Caddy: {caddy_error}")

            # Delete LXC container
            await self.proxmox_service.delete_lxc(db_app.node, db_app.lxc_id)

            # Remove from database (cascade will delete related deployment logs)
            db.delete(db_app)
            db.commit()

            logger.info(f"Deleted app {app_id}")

        except Exception as e:
            db.rollback()
            raise AppServiceError(f"Failed to delete app: {e}")

    async def deploy_app(self, db: Session, app_data: AppCreate, user_id: Optional[int] = None) -> App:
        """Deploy a new application"""
        app_id = f"{app_data.catalog_id}-{app_data.hostname}"

        # Check if app already exists
        existing_app = db.query(DBApp).filter(DBApp.id == app_id).first()
        if existing_app:
            raise AppServiceError(f"App with ID '{app_id}' already exists")

        # Get catalog item
        catalog_item = await self.get_catalog_item(app_data.catalog_id)

        # Initialize deployment status
        deployment_status = DeploymentStatus(
            app_id=app_id,
            status=AppStatus.DEPLOYING,
            progress=0,
            current_step="Initializing deployment"
        )
        self._deployment_status[app_id] = deployment_status

        try:
            # Step 1: Select target node
            await self._log_deployment(app_id, "info", "Selecting target node")
            deployment_status.progress = 10
            deployment_status.current_step = "Selecting target node"

            target_node = app_data.node or await self.proxmox_service.get_best_node()

            # Step 2: Get next VMID
            await self._log_deployment(app_id, "info", "Getting next VMID")
            deployment_status.progress = 20
            deployment_status.current_step = "Reserving container ID"

            vmid = await self.proxmox_service.get_next_vmid()

            # Step 3: Create LXC container
            await self._log_deployment(app_id, "info", f"Creating LXC container {vmid} on node {target_node}")
            deployment_status.progress = 30
            deployment_status.current_step = "Creating container"

            lxc_config = {
                "hostname": app_data.hostname,
                "cores": max(catalog_item.min_cpu, settings.LXC_CORES),
                "memory": max(catalog_item.min_memory, settings.LXC_MEMORY),
                "description": f"Proximity App: {catalog_item.name}"
            }

            create_result = await self.proxmox_service.create_lxc(target_node, vmid, lxc_config)
            await self.proxmox_service.wait_for_task(target_node, create_result["task_id"])

            # Step 4: Start container
            await self._log_deployment(app_id, "info", "Starting container")
            deployment_status.progress = 40
            deployment_status.current_step = "Starting container"

            start_task = await self.proxmox_service.start_lxc(target_node, vmid)
            await self.proxmox_service.wait_for_task(target_node, start_task)

            # Step 4.5: Setup Docker
            await self._log_deployment(app_id, "info", "Installing Docker in Alpine container")
            deployment_status.progress = 50
            deployment_status.current_step = "Setting up Docker"

            await self.proxmox_service.setup_docker_in_alpine(target_node, vmid)
            await asyncio.sleep(5)

            # Step 5: Setup Docker Compose
            await self._log_deployment(app_id, "info", "Setting up application")
            deployment_status.progress = 70
            deployment_status.current_step = "Pulling Docker images (this may take a few minutes)"

            await self._setup_docker_compose(target_node, vmid, catalog_item, app_data)

            # Step 6: Configure reverse proxy
            deployment_status.progress = 80
            deployment_status.current_step = "Configuring reverse proxy"

            await asyncio.sleep(3)  # Wait for network

            container_ip = await self.proxmox_service.get_lxc_ip(target_node, vmid)
            primary_port = catalog_item.ports[0] if catalog_item.ports else 80

            # Configure reverse proxy in network appliance (if available)
            access_url = None
            if self.proxy_manager and container_ip:
                try:
                    vhost_created = await self.proxy_manager.create_vhost(
                        app_name=app_data.hostname,
                        backend_ip=container_ip,
                        backend_port=primary_port
                    )

                    if vhost_created:
                        appliance_wan_ip = None
                        if hasattr(self.proxmox_service, 'network_manager') and self.proxmox_service.network_manager:
                            appliance_info = self.proxmox_service.network_manager.appliance_info
                            if appliance_info:
                                appliance_wan_ip = appliance_info.wan_ip

                        if appliance_wan_ip:
                            access_url = f"http://{appliance_wan_ip}/{app_data.hostname}"
                        else:
                            access_url = f"http://{app_data.hostname}.prox.local"
                    else:
                        access_url = f"http://{container_ip}:{primary_port}"
                except Exception as proxy_error:
                    logger.warning(f"Failed to configure reverse proxy: {proxy_error}")
                    access_url = f"http://{container_ip}:{primary_port}"
            else:
                access_url = f"http://{container_ip}:{primary_port}" if container_ip else None

            # Create new app record in database
            new_app = DBApp(
                id=app_id,
                catalog_id=app_data.catalog_id,
                name=catalog_item.name,
                hostname=app_data.hostname,
                status=AppStatus.RUNNING.value,
                url=access_url,
                lxc_id=vmid,
                node=target_node,
                config=app_data.config,
                environment=app_data.environment,
                ports={port: port for port in catalog_item.ports},
                owner_id=user_id
            )

            db.add(new_app)
            db.commit()
            db.refresh(new_app)

            # Complete deployment
            deployment_status.status = AppStatus.RUNNING
            deployment_status.progress = 100
            deployment_status.current_step = "Deployment complete"

            await self._log_deployment(app_id, "info", f"Application deployed successfully at {access_url}")

            return db_app_to_schema(new_app)

        except Exception as e:
            # Handle deployment failure
            deployment_status.status = AppStatus.ERROR
            deployment_status.error = str(e)
            await self._log_deployment(app_id, "error", f"Deployment failed: {e}")

            # Cleanup on failure
            try:
                if 'vmid' in locals() and 'target_node' in locals():
                    logger.info(f"Cleaning up failed deployment: destroying LXC {vmid}")
                    task_id = await self.proxmox_service.destroy_lxc(target_node, vmid, force=True)
                    await self.proxmox_service.wait_for_task(target_node, task_id, timeout=60)
                    logger.info(f"✓ Cleanup successful: LXC {vmid} destroyed")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup after deployment failure: {cleanup_error}")

            db.rollback()
            raise AppServiceError(f"Deployment failed: {e}")

    async def _setup_docker_compose(self, node: str, vmid: int, catalog_item: AppCatalogItem, app_data: AppCreate) -> None:
        """Setup Docker Compose configuration in the container"""
        try:
            # Merge environment variables
            env_vars = {**catalog_item.environment, **app_data.environment}

            # Update docker-compose with custom environment
            compose_config = catalog_item.docker_compose.copy()

            # Apply environment variables to services
            for service_name, service_config in compose_config.get("services", {}).items():
                if "environment" in service_config:
                    service_config["environment"].update(env_vars)
                else:
                    service_config["environment"] = env_vars

            # Convert to YAML
            compose_yaml = yaml.dump(compose_config, default_flow_style=False)

            # Create docker-compose.yml
            setup_command = f"""
cd /root && \\
cat > docker-compose.yml << 'COMPOSE_EOF'
{compose_yaml}
COMPOSE_EOF
"""

            logger.info(f"Writing docker-compose.yml to LXC {vmid}...")
            await self.proxmox_service.execute_in_container(node, vmid, setup_command.strip())

            # Pull images
            logger.info(f"Pulling Docker images for LXC {vmid}...")
            await self.proxmox_service.execute_in_container(
                node, vmid,
                "cd /root && docker compose pull",
                timeout=600
            )

            # Start services
            logger.info(f"Starting Docker services in LXC {vmid}...")
            await self.proxmox_service.execute_in_container(
                node, vmid,
                "cd /root && docker compose up -d",
                timeout=300
            )

            # Verify services are running
            await asyncio.sleep(5)

        except Exception as e:
            raise AppServiceError(f"Failed to setup Docker Compose: {e}")

    async def _log_deployment(self, app_id: str, level: str, message: str, step: Optional[str] = None) -> None:
        """Add log entry to deployment status"""
        if app_id in self._deployment_status:
            log_entry = DeploymentLog(
                timestamp=datetime.now(),
                level=level,
                message=message,
                step=step
            )
            self._deployment_status[app_id].logs.append(log_entry)
            logger.info(f"[{app_id}] {message}")

    async def get_deployment_status(self, app_id: str) -> DeploymentStatus:
        """Get deployment status for an app"""
        if app_id not in self._deployment_status:
            raise AppServiceError(f"No deployment status found for app '{app_id}'")
        return self._deployment_status[app_id]

    async def update_app(self, db: Session, app_id: str, app_update: AppUpdate) -> App:
        """Update an existing application"""
        db_app = db.query(DBApp).filter(DBApp.id == app_id).first()

        if not db_app:
            raise AppServiceError(f"App '{app_id}' not found")

        if app_update.config is not None:
            current_config = db_app.config or {}
            current_config.update(app_update.config)
            db_app.config = current_config

        if app_update.environment is not None:
            current_env = db_app.environment or {}
            current_env.update(app_update.environment)
            db_app.environment = current_env

        if app_update.status is not None:
            db_app.status = app_update.status.value

        db_app.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_app)

        return db_app_to_schema(db_app)


# Singleton instance - will be injected with proxmox_service
app_service: Optional[AppService] = None


def get_app_service() -> AppService:
    """Dependency injection for AppService"""
    global app_service
    if app_service is None:
        from services.proxmox_service import proxmox_service
        app_service = AppService(proxmox_service)
    return app_service
