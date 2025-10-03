import asyncio
import json
import logging
import os
import tempfile
import yaml
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

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


class AppService:
    """Business logic layer for application management"""
    
    def __init__(self, proxmox_service: ProxmoxService, proxy_manager=None):
        self.proxmox_service = proxmox_service
        self._proxy_manager = proxy_manager  # ReverseProxyManager for network appliance Caddy
        # In production, this would be a proper database
        self._apps_db: Dict[str, App] = {}
        self._deployment_status: Dict[str, DeploymentStatus] = {}
        self._catalog_cache: Optional[CatalogResponse] = None
        self._apps_file = Path(__file__).parent.parent / "data" / "apps.json"
        self._caddy_service = None  # Legacy Caddy service (deprecated)
        self._catalog_loaded = False  # Track if catalog has been loaded
        self._apps_loaded = False  # Track if apps have been loaded
        
        # Ensure data directory exists
        self._apps_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Note: Catalog and apps are now loaded lazily on first access
        # to avoid event loop issues during dependency injection
    
    @property
    def proxy_manager(self):
        """Lazy-load proxy_manager from FastAPI app state if not set"""
        if self._proxy_manager is None:
            try:
                # Try to get from FastAPI app state
                from fastapi import Request
                from starlette.concurrency import run_in_threadpool
                # This will be None if not in request context
                # In that case, it will be set later
            except:
                pass
        return self._proxy_manager
    
    def set_proxy_manager(self, proxy_manager):
        """Set the proxy manager (called from main.py after initialization)"""
        self._proxy_manager = proxy_manager

    async def _load_apps(self) -> None:
        """Load deployed apps from disk"""
        if self._apps_loaded:
            return  # Already loaded
        
        try:
            if self._apps_file.exists():
                with open(self._apps_file, 'r') as f:
                    data = json.load(f)
                    apps_data = data.get('apps', [])
                    for app_data in apps_data:
                        try:
                            app = App(**app_data)
                            self._apps_db[app.id] = app
                        except Exception as e:
                            logger.error(f"Failed to load app {app_data.get('id')}: {e}")
                    logger.info(f"Loaded {len(self._apps_db)} apps from disk")
            else:
                # Create empty apps file
                await self._save_apps()
            
            self._apps_loaded = True  # Mark as loaded
        except Exception as e:
            logger.error(f"Failed to load apps: {e}")
            self._apps_loaded = True  # Mark as attempted to prevent retry loops

    async def _save_apps(self) -> None:
        """Save deployed apps to disk"""
        try:
            apps_data = [app.model_dump() for app in self._apps_db.values()]
            with open(self._apps_file, 'w') as f:
                json.dump({"apps": apps_data}, f, indent=2, default=str)
            logger.debug(f"Saved {len(apps_data)} apps to disk")
        except Exception as e:
            logger.error(f"Failed to save apps: {e}")

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
            },
            {
                "id": "nextcloud",
                "name": "Nextcloud",
                "description": "Self-hosted file sync and share platform",
                "version": "latest",
                "category": "Storage",
                "docker_compose": {
                    "version": "3.8",
                    "services": {
                        "nextcloud": {
                            "image": "nextcloud:latest",
                            "ports": ["80:80"],
                            "environment": {
                                "MYSQL_HOST": "db",
                                "MYSQL_USER": "nextcloud",
                                "MYSQL_PASSWORD": "nextcloud",
                                "MYSQL_DATABASE": "nextcloud"
                            },
                            "volumes": ["nextcloud_data:/var/www/html"],
                            "depends_on": ["db"]
                        },
                        "db": {
                            "image": "mysql:8.0",
                            "environment": {
                                "MYSQL_DATABASE": "nextcloud",
                                "MYSQL_USER": "nextcloud",
                                "MYSQL_PASSWORD": "nextcloud",
                                "MYSQL_ROOT_PASSWORD": "rootpassword"
                            },
                            "volumes": ["db_data:/var/lib/mysql"]
                        }
                    },
                    "volumes": {
                        "nextcloud_data": {},
                        "db_data": {}
                    }
                },
                "ports": [80],
                "min_memory": 2048,
                "min_cpu": 2
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

    async def get_all_apps(self) -> List[App]:
        """Get all deployed applications"""
        # Lazy load apps from disk if not already loaded
        if not self._apps_loaded:
            await self._load_apps()
        
        # Sync with actual LXC containers
        await self._sync_apps_with_containers()
        return list(self._apps_db.values())

    async def get_app(self, app_id: str) -> App:
        """Get specific application"""
        # Lazy load apps from disk if not already loaded
        if not self._apps_loaded:
            await self._load_apps()
        
        if app_id not in self._apps_db:
            raise AppServiceError(f"App '{app_id}' not found")
        
        # Update status from container
        app = self._apps_db[app_id]
        try:
            lxc_status = await self.proxmox_service.get_lxc_status(app.node, app.lxc_id)
            if lxc_status.status.value == "running":
                app.status = AppStatus.RUNNING
            elif lxc_status.status.value == "stopped":
                app.status = AppStatus.STOPPED
            else:
                app.status = AppStatus.ERROR
        except ProxmoxError:
            app.status = AppStatus.ERROR
            
        return app

    async def _sync_apps_with_containers(self) -> None:
        """Sync app database with actual LXC containers and update URLs"""
        try:
            # Lazy-load Caddy service if needed
            if self._caddy_service is None:
                from services.caddy_service import get_caddy_service
                self._caddy_service = get_caddy_service(self.proxmox_service)
            
            containers = await self.proxmox_service.get_lxc_containers()
            status_changed = False
            
            for app_id, app in self._apps_db.items():
                # Find corresponding container
                container = next((c for c in containers if c.vmid == app.lxc_id), None)
                old_status = app.status
                old_url = app.url
                
                if container:
                    if container.status.value == "running":
                        app.status = AppStatus.RUNNING
                        
                        # Always refresh URL to ensure it's current
                        try:
                            # Get container IP
                            container_ip = await self.proxmox_service.get_lxc_ip(app.node, app.lxc_id)
                            
                            if container_ip:
                                # Determine port (use first port from catalog or default to 80)
                                catalog_item = next((item for item in self._catalog_cache.items if item.id == app.catalog_id), None) if self._catalog_cache else None
                                primary_port = catalog_item.ports[0] if catalog_item and catalog_item.ports else 80
                                
                                # Check if Caddy is deployed
                                if self._caddy_service and self._caddy_service.is_deployed:
                                    is_caddy_running = await self._caddy_service.is_caddy_running()
                                    caddy_ip = await self._caddy_service.get_caddy_ip()
                                    
                                    if is_caddy_running and caddy_ip:
                                        # Use Caddy proxy URL
                                        new_url = f"http://{caddy_ip}:8080/{app.hostname}"
                                    else:
                                        # Caddy not running, use direct access
                                        new_url = f"http://{container_ip}:{primary_port}"
                                else:
                                    # Caddy not deployed, use direct access
                                    new_url = f"http://{container_ip}:{primary_port}"
                                
                                # Update URL if changed
                                if app.url != new_url:
                                    logger.info(f"Updated URL for {app_id}: {old_url} → {new_url}")
                                    app.url = new_url
                            else:
                                logger.warning(f"Could not get IP for {app_id} (LXC {app.lxc_id})")
                                
                        except Exception as url_error:
                            logger.warning(f"Failed to update URL for {app_id}: {url_error}")
                    
                    elif container.status.value == "stopped":
                        app.status = AppStatus.STOPPED
                    else:
                        app.status = AppStatus.ERROR
                else:
                    # Container not found, mark as error
                    app.status = AppStatus.ERROR
                
                if old_status != app.status or old_url != app.url:
                    status_changed = True
            
            # Save if any status changed
            if status_changed:
                await self._save_apps()
                    
        except Exception as e:
            logger.error(f"Failed to sync apps with containers: {e}")

    async def start_app(self, app_id: str) -> App:
        """Start an application"""
        app = await self.get_app(app_id)
        
        try:
            # Start LXC container
            await self.proxmox_service.start_lxc(app.node, app.lxc_id)
            
            # Wait a bit for container to start
            await asyncio.sleep(2)
            
            # Start Docker Compose
            await self.proxmox_service.execute_in_container(
                app.node, app.lxc_id,
                "cd /root && docker compose up -d"
            )
            
            # Update status
            app.status = AppStatus.RUNNING
            self._apps_db[app_id] = app
            await self._save_apps()
            
            logger.info(f"Started app {app_id}")
            return app
            
        except Exception as e:
            app.status = AppStatus.ERROR
            self._apps_db[app_id] = app
            await self._save_apps()
            raise AppServiceError(f"Failed to start app: {e}")
    
    async def stop_app(self, app_id: str) -> App:
        """Stop an application"""
        app = await self.get_app(app_id)
        
        try:
            # Stop Docker Compose
            await self.proxmox_service.execute_in_container(
                app.node, app.lxc_id,
                "cd /root && docker compose down"
            )
            
            # Stop LXC container
            await self.proxmox_service.stop_lxc(app.node, app.lxc_id)
            
            # Update status
            app.status = AppStatus.STOPPED
            self._apps_db[app_id] = app
            await self._save_apps()
            
            logger.info(f"Stopped app {app_id}")
            return app
            
        except Exception as e:
            app.status = AppStatus.ERROR
            self._apps_db[app_id] = app
            await self._save_apps()
            raise AppServiceError(f"Failed to stop app: {e}")
    
    async def restart_app(self, app_id: str) -> App:
        """Restart an application"""
        await self.stop_app(app_id)
        await asyncio.sleep(2)
        return await self.start_app(app_id)
    
    async def delete_app(self, app_id: str) -> None:
        """Delete an application and its LXC container"""
        app = await self.get_app(app_id)
        
        try:
            # Stop if running
            if app.status == AppStatus.RUNNING:
                await self.stop_app(app_id)
            
            # Remove from Caddy reverse proxy if available
            if self._caddy_service is not None:
                try:
                    await self._caddy_service.remove_application(app_id)
                    logger.info(f"Removed {app_id} from reverse proxy")
                except Exception as caddy_error:
                    logger.warning(f"Failed to remove app from Caddy: {caddy_error}")
            
            # Delete LXC container
            await self.proxmox_service.delete_lxc(app.node, app.lxc_id)
            
            # Remove from database
            del self._apps_db[app_id]
            await self._save_apps()
            
            logger.info(f"Deleted app {app_id}")
            
        except Exception as e:
            raise AppServiceError(f"Failed to delete app: {e}")
    
    async def deploy_app(self, app_data: AppCreate) -> App:
        """Deploy a new application"""
        app_id = f"{app_data.catalog_id}-{app_data.hostname}"
        
        if app_id in self._apps_db:
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
            
            # Don't specify rootfs - let create_lxc auto-select best storage
            lxc_config = {
                "hostname": app_data.hostname,
                "cores": max(catalog_item.min_cpu, settings.LXC_CORES),
                "memory": max(catalog_item.min_memory, settings.LXC_MEMORY),
                "description": f"Proximity App: {catalog_item.name}"
            }
            
            create_result = await self.proxmox_service.create_lxc(target_node, vmid, lxc_config)
            
            # Wait for container creation
            await self.proxmox_service.wait_for_task(target_node, create_result["task_id"])
            
            # Step 4: Start container
            await self._log_deployment(app_id, "info", "Starting container")
            deployment_status.progress = 40
            deployment_status.current_step = "Starting container"
            
            start_task = await self.proxmox_service.start_lxc(target_node, vmid)
            await self.proxmox_service.wait_for_task(target_node, start_task)
            
            # Step 4.5: Setup Docker in Alpine
            await self._log_deployment(app_id, "info", "Installing Docker in Alpine container")
            deployment_status.progress = 50
            deployment_status.current_step = "Setting up Docker"
            
            await self.proxmox_service.setup_docker_in_alpine(target_node, vmid)
            
            # Wait for Docker to be fully ready
            await asyncio.sleep(5)
            
            # Step 5: Setup Docker Compose
            await self._log_deployment(app_id, "info", "Setting up application")
            deployment_status.progress = 70
            deployment_status.current_step = "Pulling Docker images (this may take a few minutes)"
            
            await self._setup_docker_compose(target_node, vmid, catalog_item, app_data)
            
            # Step 6: Configure reverse proxy via Network Appliance
            deployment_status.progress = 80
            deployment_status.current_step = "Configuring reverse proxy"
            
            # Get container IP address
            await asyncio.sleep(3)  # Wait for network to be ready
            
            container_ip = await self.proxmox_service.get_lxc_ip(target_node, vmid)
            primary_port = catalog_item.ports[0] if catalog_item.ports else 80
            
            # Configure reverse proxy in network appliance (if available)
            if self.proxy_manager and container_ip:
                try:
                    # Create virtual host for this app
                    vhost_created = await self.proxy_manager.create_vhost(
                        app_name=app_data.hostname,
                        backend_ip=container_ip,
                        backend_port=primary_port
                    )
                    
                    if vhost_created:
                        # Access via hostname through network appliance
                        # Apps are accessible via: http://<appliance-wan-ip>/<app-hostname>
                        # Or via hostname: http://<app-hostname>.prox.local (with proper DNS)
                        appliance_hostname = f"{app_data.hostname}.prox.local"
                        access_url = f"http://{appliance_hostname}"
                        await self._log_deployment(app_id, "info", f"✓ Reverse proxy configured: {appliance_hostname} → {container_ip}:{primary_port}")
                        await self._log_deployment(app_id, "info", f"✓ Access via: {access_url}")
                    else:
                        # Fallback to direct access
                        access_url = f"http://{container_ip}:{primary_port}" if container_ip else None
                        await self._log_deployment(app_id, "warning", "Reverse proxy configuration failed - using direct access")
                        
                except Exception as proxy_error:
                    logger.warning(f"Failed to configure reverse proxy: {proxy_error}")
                    access_url = f"http://{container_ip}:{primary_port}" if container_ip else None
                    await self._log_deployment(app_id, "warning", f"Reverse proxy error: {proxy_error} - using direct access")
            else:
                # No proxy manager available - use direct access
                access_url = f"http://{container_ip}:{primary_port}" if container_ip else None
                if not self.proxy_manager:
                    await self._log_deployment(app_id, "info", "Reverse proxy not available - using direct access")
                elif not container_ip:
                    await self._log_deployment(app_id, "warning", "Could not determine container IP")
            
            app = App(
                id=app_id,
                catalog_id=app_data.catalog_id,
                name=catalog_item.name,
                hostname=app_data.hostname,
                status=AppStatus.RUNNING,
                url=access_url,
                lxc_id=vmid,
                node=target_node,
                config=app_data.config,
                environment=app_data.environment,
                ports={port: port for port in catalog_item.ports}  # Simplified port mapping
            )
            
            self._apps_db[app_id] = app
            
            # Save to disk
            await self._save_apps()
            
            # Complete deployment
            deployment_status.status = AppStatus.RUNNING
            deployment_status.progress = 100
            deployment_status.current_step = "Deployment complete"
            
            await self._log_deployment(app_id, "info", f"Application deployed successfully at {app.url}")
            
            return app
            
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
            
            # Escape single quotes in YAML for shell
            escaped_yaml = compose_yaml.replace("'", "'\\\"'\\\"'")
            
            # Create docker-compose.yml and start services using multi-line command
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
                timeout=600  # 10 minutes for pulling images
            )
            
            # Start services
            logger.info(f"Starting Docker services in LXC {vmid}...")
            await self.proxmox_service.execute_in_container(
                node, vmid,
                "cd /root && docker compose up -d",
                timeout=300  # 5 minutes for starting services
            )
            
            # Verify services are running
            await asyncio.sleep(5)
            logger.info(f"Verifying Docker services in LXC {vmid}...")
            status = await self.proxmox_service.execute_in_container(
                node, vmid,
                "cd /root && docker compose ps",
                timeout=30
            )
            logger.info(f"Docker Compose status:\\n{status}")
                
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

    async def update_app(self, app_id: str, app_update: AppUpdate) -> App:
        """Update an existing application"""
        if app_id not in self._apps_db:
            raise AppServiceError(f"App '{app_id}' not found")
        
        app = self._apps_db[app_id]
        
        if app_update.config is not None:
            app.config.update(app_update.config)
        
        if app_update.environment is not None:
            app.environment.update(app_update.environment)
            # Would need to update container environment and restart
        
        if app_update.status is not None:
            app.status = app_update.status
        
        app.updated_at = datetime.now()
        return app

    async def start_app(self, app_id: str) -> App:
        """Start an application"""
        app = await self.get_app(app_id)
        
        try:
            task_id = await self.proxmox_service.start_lxc(app.node, app.lxc_id)
            await self.proxmox_service.wait_for_task(app.node, task_id)
            
            app.status = AppStatus.RUNNING
            app.updated_at = datetime.now()
            
            # Save updated status
            await self._save_apps()
            
            return app
        except ProxmoxError as e:
            raise AppServiceError(f"Failed to start app: {e}")

    async def stop_app(self, app_id: str) -> App:
        """Stop an application"""
        app = await self.get_app(app_id)
        
        try:
            task_id = await self.proxmox_service.stop_lxc(app.node, app.lxc_id)
            await self.proxmox_service.wait_for_task(app.node, task_id)
            
            app.status = AppStatus.STOPPED
            app.updated_at = datetime.now()
            
            # Save updated status
            await self._save_apps()
            
            return app
        except ProxmoxError as e:
            raise AppServiceError(f"Failed to stop app: {e}")

    async def restart_app(self, app_id: str) -> App:
        """Restart an application"""
        await self.stop_app(app_id)
        await asyncio.sleep(5)
        app = await self.start_app(app_id)
        # Save is already called in start_app
        return app

    async def delete_app(self, app_id: str) -> None:
        """Delete an application and its container"""
        if app_id not in self._apps_db:
            raise AppServiceError(f"App '{app_id}' not found")
        
        app = self._apps_db[app_id]
        
        try:
            # Stop container first if running
            try:
                await self.proxmox_service.stop_lxc(app.node, app.lxc_id, force=True)
                await asyncio.sleep(5)  # Wait for clean shutdown
            except ProxmoxError:
                pass  # Container might already be stopped
            
            # Destroy container (force=True ensures it stops if still running)
            task_id = await self.proxmox_service.destroy_lxc(app.node, app.lxc_id, force=True)
            await self.proxmox_service.wait_for_task(app.node, task_id)
            
            # Remove from database
            del self._apps_db[app_id]
            
            # Save to disk
            await self._save_apps()
            
            # Clean up deployment status
            if app_id in self._deployment_status:
                del self._deployment_status[app_id]
                
        except ProxmoxError as e:
            raise AppServiceError(f"Failed to delete app: {e}")


# Singleton instance - will be injected with proxmox_service
app_service: Optional[AppService] = None


def get_app_service() -> AppService:
    """Dependency injection for AppService"""
    global app_service
    if app_service is None:
        from services.proxmox_service import proxmox_service
        app_service = AppService(proxmox_service)
    return app_service