import asyncio
import json
import logging
import os
import tempfile
import yaml
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import Depends
from sqlalchemy.orm import Session
from models.database import App as DBApp, DeploymentLog as DBDeploymentLog, get_db
from models.schemas import (
    App, AppCreate, AppUpdate, AppStatus, AppCatalogItem, 
    DeploymentStatus, DeploymentLog, CatalogResponse
)
from services.proxmox_service import ProxmoxService, ProxmoxError
from core.config import settings
from core.exceptions import (
    AppNotFoundError,
    AppAlreadyExistsError,
    AppDeploymentError,
    AppOperationError,
    CatalogError,
    DatabaseError,
    ValidationError
)

logger = logging.getLogger(__name__)


class AppServiceError(Exception):
    """Custom exception for App Service errors - deprecated, use core.exceptions instead"""
    pass


class AppService:
    """Business logic layer for application management"""
    
    # Class-level deployment status storage (shared across all instances)
    _deployment_status: Dict[str, DeploymentStatus] = {}
    
    def __init__(self, proxmox_service: ProxmoxService, db: Session, proxy_manager=None, port_manager=None):
        self.proxmox_service = proxmox_service
        self.db = db
        self._proxy_manager = proxy_manager  # ReverseProxyManager for network appliance Caddy
        self._port_manager = port_manager  # PortManagerService for port allocation
        # Note: _deployment_status is now a class variable, not instance variable
        self._catalog_cache: Optional[CatalogResponse] = None
        self._caddy_service = None  # Legacy Caddy service (deprecated)
        self._catalog_loaded = False  # Track if catalog has been loaded
        
        # Initialize port manager if not provided
        if self._port_manager is None:
            from services.port_manager import PortManagerService
            self._port_manager = PortManagerService(db)
        
        # Note: Catalog is loaded lazily on first access
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
    
    @property
    def port_manager(self):
        """Get port manager instance"""
        return self._port_manager

    def _db_app_to_schema(self, db_app: DBApp) -> App:
        """Convert database App model to Pydantic schema"""
        # Keep volumes in their original format (dict list or string list)
        # The App schema now accepts both Union[List[str], List[Dict[str, str]]]
        volumes = db_app.volumes or []
        
        return App(
            id=db_app.id,
            catalog_id=db_app.catalog_id,
            name=db_app.name,
            hostname=db_app.hostname,
            status=AppStatus(db_app.status),
            url=db_app.url,
            iframe_url=db_app.iframe_url,
            lxc_id=db_app.lxc_id,
            node=db_app.node,
            created_at=db_app.created_at,
            updated_at=db_app.updated_at,
            config=db_app.config or {},
            ports=db_app.ports or {},
            volumes=volumes,
            environment=db_app.environment or {},
            public_port=db_app.public_port,
            internal_port=db_app.internal_port
        )

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
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            logger.error(f"Failed to load app from {app_file}: {e}")
                        except Exception as e:
                            logger.error(f"Unexpected error loading {app_file}: {e}", exc_info=True)
                
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
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Catalog file error: {e}")
            await self._create_default_catalog()
            self._catalog_loaded = True
        except Exception as e:
            logger.error(f"Unexpected error loading catalog: {e}", exc_info=True)
            await self._create_default_catalog()
            self._catalog_loaded = True

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
        # Query all apps from database
        db_apps = self.db.query(DBApp).all()
        
        # Convert to schema objects
        apps = [self._db_app_to_schema(db_app) for db_app in db_apps]
        
        # Sync with actual LXC containers
        await self._sync_apps_with_containers(apps)
        return apps

    async def get_app(self, app_id: str) -> App:
        """Get specific application"""
        # Query app from database
        db_app = self.db.query(DBApp).filter(DBApp.id == app_id).first()
        
        if not db_app:
            raise AppServiceError(f"App '{app_id}' not found")
        
        # Convert to schema
        app = self._db_app_to_schema(db_app)
        
        # Update status from container
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

    async def _sync_apps_with_containers(self, apps: List[App]) -> None:
        """Sync app database with actual LXC containers and update URLs"""
        try:
            # Lazy-load Caddy service if needed
            if self._caddy_service is None:
                from services.caddy_service import get_caddy_service
                self._caddy_service = get_caddy_service(self.proxmox_service)
            
            containers = await self.proxmox_service.get_lxc_containers()
            status_changed = False
            
            for app in apps:
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
                                    logger.info(f"Updated URL for {app.id}: {old_url} → {new_url}")
                                    app.url = new_url
                            else:
                                logger.warning(f"Could not get IP for {app.id} (LXC {app.lxc_id})")
                                
                        except ProxmoxError as url_error:
                            logger.warning(f"Proxmox error updating URL for {app.id}: {url_error}")
                        except Exception as url_error:
                            logger.warning(f"Unexpected error updating URL for {app.id}: {url_error}", exc_info=True)
                    
                    elif container.status.value == "stopped":
                        app.status = AppStatus.STOPPED
                    else:
                        app.status = AppStatus.ERROR
                else:
                    # Container not found, mark as error
                    app.status = AppStatus.ERROR
                
                # Update database if status or URL changed
                if old_status != app.status or old_url != app.url:
                    db_app = self.db.query(DBApp).filter(DBApp.id == app.id).first()
                    if db_app:
                        db_app.status = app.status.value
                        db_app.url = app.url
                        db_app.updated_at = datetime.now(UTC)
                        status_changed = True
            
            # Commit changes if any
            if status_changed:
                self.db.commit()
                    
        except ProxmoxError as e:
            logger.error(f"Proxmox error during app sync: {e}")
            self.db.rollback()
        except DatabaseError as e:
            logger.error(f"Database error during app sync: {e}")
            self.db.rollback()
        except Exception as e:
            logger.error(f"Unexpected error syncing apps with containers: {e}", exc_info=True)
            self.db.rollback()

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
            
            # Update status in database
            db_app = self.db.query(DBApp).filter(DBApp.id == app_id).first()
            if db_app:
                db_app.status = AppStatus.RUNNING.value
                db_app.updated_at = datetime.now(UTC)
                self.db.commit()
            
            app.status = AppStatus.RUNNING
            logger.info(f"Started app {app_id}", extra={"app_id": app_id, "vmid": app.lxc_id, "node": app.node})
            return app
            
        except ProxmoxError as e:
            logger.error(f"Proxmox error starting app {app_id}: {e}", extra={"app_id": app_id})
            # Update error status
            db_app = self.db.query(DBApp).filter(DBApp.id == app_id).first()
            if db_app:
                db_app.status = AppStatus.ERROR.value
                db_app.updated_at = datetime.now(UTC)
                self.db.commit()
            raise AppOperationError(
                f"Failed to start application: {str(e)}",
                details={"app_id": app_id, "operation": "start", "error_type": "proxmox"}
            ) from e
        except DatabaseError as e:
            logger.error(f"Database error starting app {app_id}: {e}", extra={"app_id": app_id})
            raise AppOperationError(
                f"Failed to update app status: {str(e)}",
                details={"app_id": app_id, "operation": "start", "error_type": "database"}
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error starting app {app_id}: {e}", extra={"app_id": app_id}, exc_info=True)
            # Update error status
            db_app = self.db.query(DBApp).filter(DBApp.id == app_id).first()
            if db_app:
                db_app.status = AppStatus.ERROR.value
                db_app.updated_at = datetime.now(UTC)
                self.db.commit()
            raise AppOperationError(
                f"Failed to start application: {str(e)}",
                details={"app_id": app_id, "operation": "start"}
            ) from e
    
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
            
            # Update status in database
            db_app = self.db.query(DBApp).filter(DBApp.id == app_id).first()
            if db_app:
                db_app.status = AppStatus.STOPPED.value
                db_app.updated_at = datetime.now(UTC)
                self.db.commit()
            
            app.status = AppStatus.STOPPED
            logger.info(f"Stopped app {app_id}", extra={"app_id": app_id, "vmid": app.lxc_id, "node": app.node})
            return app
            
        except ProxmoxError as e:
            logger.error(f"Proxmox error stopping app {app_id}: {e}", extra={"app_id": app_id})
            # Update error status
            db_app = self.db.query(DBApp).filter(DBApp.id == app_id).first()
            if db_app:
                db_app.status = AppStatus.ERROR.value
                db_app.updated_at = datetime.now(UTC)
                self.db.commit()
            raise AppOperationError(
                f"Failed to stop application: {str(e)}",
                details={"app_id": app_id, "operation": "stop", "error_type": "proxmox"}
            ) from e
        except DatabaseError as e:
            logger.error(f"Database error stopping app {app_id}: {e}", extra={"app_id": app_id})
            raise AppOperationError(
                f"Failed to update app status: {str(e)}",
                details={"app_id": app_id, "operation": "stop", "error_type": "database"}
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error stopping app {app_id}: {e}", extra={"app_id": app_id}, exc_info=True)
            # Update error status
            db_app = self.db.query(DBApp).filter(DBApp.id == app_id).first()
            if db_app:
                db_app.status = AppStatus.ERROR.value
                db_app.updated_at = datetime.now(UTC)
                self.db.commit()
            raise AppOperationError(
                f"Failed to stop application: {str(e)}",
                details={"app_id": app_id, "operation": "stop"}
            ) from e
    
    async def restart_app(self, app_id: str) -> App:
        """Restart an application"""
        await self.stop_app(app_id)
        await asyncio.sleep(2)
        return await self.start_app(app_id)
    
    async def delete_app(self, app_id: str) -> None:
        """Delete an application and its LXC container"""
        app = await self.get_app(app_id)
        
        errors = []
        
        try:
            # Stop if running
            if app.status == AppStatus.RUNNING:
                logger.info(f"Stopping app {app_id} before deletion")
                try:
                    await self.stop_app(app_id)
                except Exception as stop_error:
                    error_msg = f"Failed to stop container: {str(stop_error)}"
                    logger.warning(error_msg, extra={"app_id": app_id})
                    errors.append(error_msg)
            
            # Release allocated ports
            try:
                await self.port_manager.release_ports_for_app(app_id)
                logger.info(f"Released ports for app {app_id}")
            except Exception as port_error:
                error_msg = f"Failed to release ports: {str(port_error)}"
                logger.warning(error_msg, extra={"app_id": app_id})
                errors.append(error_msg)
            
            # Remove from Caddy reverse proxy if available
            if self._caddy_service is not None:
                try:
                    await self._caddy_service.remove_application(app_id)
                    logger.info(f"Removed {app_id} from reverse proxy")
                except (ConnectionError, TimeoutError) as caddy_error:
                    error_msg = f"Network error removing from Caddy: {str(caddy_error)}"
                    logger.warning(error_msg, extra={"app_id": app_id})
                    errors.append(error_msg)
                except Exception as caddy_error:
                    error_msg = f"Failed to remove from reverse proxy: {str(caddy_error)}"
                    logger.warning(error_msg, extra={"app_id": app_id})
                    errors.append(error_msg)
            
            # Delete LXC container
            try:
                await self.proxmox_service.destroy_lxc(app.node, app.lxc_id)
                logger.info(f"Destroyed LXC container {app.lxc_id} on node {app.node}")
            except ProxmoxError as pve_error:
                error_msg = f"Failed to destroy container: {str(pve_error)}"
                logger.error(error_msg, extra={"app_id": app_id, "vmid": app.lxc_id})
                errors.append(error_msg)
                # Don't raise here, try to clean up database anyway
            
            # Remove from database
            try:
                db_app = self.db.query(DBApp).filter(DBApp.id == app_id).first()
                if db_app:
                    self.db.delete(db_app)
                    self.db.commit()
                    logger.info(f"Removed app {app_id} from database")
                else:
                    logger.warning(f"App {app_id} not found in database")
            except Exception as db_error:
                error_msg = f"Database error: {str(db_error)}"
                logger.error(error_msg, extra={"app_id": app_id})
                self.db.rollback()
                errors.append(error_msg)
                raise AppOperationError(
                    f"Failed to remove app from database: {str(db_error)}",
                    details={"app_id": app_id, "operation": "delete", "error_type": "database"}
                ) from db_error
            
            # If there were any errors but we succeeded in removing from DB, log them
            if errors:
                logger.warning(
                    f"App {app_id} deleted with {len(errors)} warnings",
                    extra={"app_id": app_id, "warnings": errors}
                )
            else:
                logger.info(
                    f"Successfully deleted app {app_id}",
                    extra={"app_id": app_id, "vmid": app.lxc_id, "node": app.node}
                )
            
        except AppOperationError:
            # Re-raise our own exceptions
            raise
        except ProxmoxError as e:
            logger.error(f"Proxmox error deleting app {app_id}: {e}", extra={"app_id": app_id})
            self.db.rollback()
            raise AppOperationError(
                f"Failed to delete application infrastructure: {str(e)}",
                details={"app_id": app_id, "operation": "delete", "error_type": "proxmox"}
            ) from e
        except DatabaseError as e:
            logger.error(f"Database error deleting app {app_id}: {e}", extra={"app_id": app_id})
            self.db.rollback()
            raise AppOperationError(
                f"Failed to remove app from database: {str(e)}",
                details={"app_id": app_id, "operation": "delete", "error_type": "database"}
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error deleting app {app_id}: {e}", extra={"app_id": app_id}, exc_info=True)
            self.db.rollback()
            raise AppOperationError(
                f"Failed to delete application: {str(e)}",
                details={"app_id": app_id, "operation": "delete"}
            ) from e

    async def clone_app(self, source_app_id: str, new_hostname: str) -> App:
        """
        Clone an existing application to a new LXC container with copied volumes.

        This creates a complete duplicate of the source application including:
        - New LXC container with same configuration
        - Copied persistent volumes
        - Identical environment variables
        - Same Docker Compose configuration

        Args:
            source_app_id: ID of the application to clone
            new_hostname: Hostname for the new cloned application

        Returns:
            App: The newly created cloned application

        Raises:
            AppNotFoundError: Source app not found
            AppAlreadyExistsError: App with new_hostname already exists
            AppOperationError: Clone operation failed
        """
        logger.info(f"Starting clone operation: {source_app_id} → {new_hostname}")

        # Get source app from database to preserve original data formats
        source_db_app = self.db.query(DBApp).filter(DBApp.id == source_app_id).first()
        if not source_db_app:
            raise AppNotFoundError(
                f"Source app '{source_app_id}' not found",
                details={"source_app_id": source_app_id}
            )

        # Get source app schema for Proxmox operations
        source_app = self._db_app_to_schema(source_db_app)

        # Check if target hostname already exists
        new_app_id = f"{source_app.catalog_id}-{new_hostname}"
        existing = self.db.query(DBApp).filter(DBApp.hostname == new_hostname).first()
        if existing:
            raise AppAlreadyExistsError(
                f"Application with hostname '{new_hostname}' already exists",
                details={"hostname": new_hostname, "existing_app_id": existing.id}
            )

        # Get catalog item for source app
        catalog_item = await self.get_catalog_item(source_app.catalog_id)

        try:
            logger.info(f"Cloning LXC container {source_app.lxc_id} from node {source_app.node}")

            # Get next VMID for clone
            new_vmid = await self.proxmox_service.get_next_vmid()

            # Allocate ports for the cloned app
            public_port, internal_port = await self.port_manager.assign_next_available_ports(new_app_id)

            # Clone LXC container using Proxmox clone API
            # This automatically copies the container's filesystem including volumes
            clone_result = await self.proxmox_service.clone_lxc(
                node=source_app.node,
                vmid=source_app.lxc_id,
                newid=new_vmid,
                name=new_hostname,
                full=True  # Full clone (not linked)
            )

            # Wait for clone to complete
            await self.proxmox_service.wait_for_task(source_app.node, clone_result["task_id"])

            # Start the cloned container
            start_task = await self.proxmox_service.start_lxc(source_app.node, new_vmid)
            await self.proxmox_service.wait_for_task(source_app.node, start_task)

            # Wait for network to be ready
            await asyncio.sleep(5)

            # Get IP address of cloned container
            container_ip = await self.proxmox_service.get_lxc_ip(source_app.node, new_vmid)
            primary_port = catalog_item.ports[0] if catalog_item.ports else 80

            # Configure reverse proxy for cloned app
            if self.proxy_manager and container_ip:
                vhost_created = await self.proxy_manager.create_vhost(
                    app_name=new_hostname,
                    backend_ip=container_ip,
                    backend_port=primary_port,
                    public_port=public_port,
                    internal_port=internal_port
                )

                if vhost_created:
                    appliance_wan_ip = None
                    if hasattr(self.proxmox_service, 'network_manager') and self.proxmox_service.network_manager:
                        appliance_info = self.proxmox_service.network_manager.appliance_info
                        if appliance_info:
                            appliance_wan_ip = appliance_info.wan_ip

                    if appliance_wan_ip:
                        access_url = f"http://{appliance_wan_ip}:{public_port}"
                        iframe_url = f"http://{appliance_wan_ip}:{internal_port}"
                    else:
                        access_url = f"http://localhost:{public_port}"
                        iframe_url = f"http://localhost:{internal_port}"
                else:
                    access_url = f"http://{container_ip}:{primary_port}" if container_ip else None
                    iframe_url = None
            else:
                access_url = f"http://{container_ip}:{primary_port}" if container_ip else None
                iframe_url = None

            # Preserve data formats exactly as they are in source database
            # Use source_db_app to get original dict/int formats before schema conversion
            cloned_ports = source_db_app.ports if source_db_app.ports else {}
            cloned_volumes = source_db_app.volumes if source_db_app.volumes else []
            cloned_config = source_db_app.config if source_db_app.config else {}
            cloned_environment = source_db_app.environment if source_db_app.environment else {}

            # Convert volumes to string format for App schema (expects List[str])
            volumes_for_schema = cloned_volumes
            if cloned_volumes and isinstance(cloned_volumes[0], dict):
                volumes_for_schema = [f"{v.get('host_path', '')}:{v.get('container_path', '')}" for v in cloned_volumes]

            # Create database entry for cloned app
            cloned_app = App(
                id=new_app_id,
                catalog_id=source_app.catalog_id,
                name=source_app.name,
                hostname=new_hostname,
                status=AppStatus.RUNNING,
                url=access_url,
                iframe_url=iframe_url,
                lxc_id=new_vmid,
                node=source_app.node,
                config=cloned_config,  # Use preserved config
                environment=cloned_environment,  # Use preserved environment
                ports=cloned_ports,  # Use preserved ports (will be converted to string keys by Pydantic)
                volumes=volumes_for_schema,  # Use string format for schema
                public_port=public_port,
                internal_port=internal_port
            )

            # Save to database
            db_app = DBApp(
                id=cloned_app.id,
                catalog_id=cloned_app.catalog_id,
                name=cloned_app.name,
                hostname=cloned_app.hostname,
                status=cloned_app.status.value,
                url=cloned_app.url,
                iframe_url=cloned_app.iframe_url,
                lxc_id=cloned_app.lxc_id,
                node=cloned_app.node,
                config=cloned_config,  # Use preserved config
                ports=cloned_ports,  # Use preserved ports
                volumes=cloned_volumes,  # Use preserved volumes
                environment=cloned_environment,  # Use preserved environment
                public_port=public_port,
                internal_port=internal_port,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            self.db.add(db_app)
            self.db.commit()
            self.db.refresh(db_app)

            # Convert to schema with database-persisted formats
            result_app = self._db_app_to_schema(db_app)

            logger.info(f"✓ Successfully cloned {source_app_id} to {new_app_id}")
            return result_app

        except Exception as e:
            logger.error(f"Clone operation failed: {e}", exc_info=True)

            # Cleanup on failure
            if 'new_vmid' in locals():
                try:
                    await self.proxmox_service.destroy_lxc(source_app.node, new_vmid, force=True)
                except:
                    pass

            if 'public_port' in locals():
                try:
                    await self.port_manager.release_ports_for_app(new_app_id)
                except:
                    pass

            self.db.rollback()

            raise AppOperationError(
                f"Failed to clone application: {str(e)}",
                details={"source_app_id": source_app_id, "new_hostname": new_hostname}
            ) from e

    async def update_app_config(
        self,
        app_id: str,
        cpu_cores: Optional[int] = None,
        memory_mb: Optional[int] = None,
        disk_gb: Optional[int] = None
    ) -> App:
        """
        Update application resource configuration (CPU, RAM, disk).

        Modifies the LXC container configuration and restarts it to apply changes.

        Args:
            app_id: Application ID to update
            cpu_cores: New CPU cores allocation (1-16)
            memory_mb: New memory allocation in MB (512-32768)
            disk_gb: New disk size in GB (1-500)

        Returns:
            App: Updated application

        Raises:
            AppNotFoundError: App not found
            AppOperationError: Update failed
        """
        logger.info(f"Updating config for {app_id}: cpu={cpu_cores}, mem={memory_mb}, disk={disk_gb}")

        # Validate that at least one parameter is provided
        if cpu_cores is None and memory_mb is None and disk_gb is None:
            raise AppOperationError(
                "At least one configuration parameter must be provided",
                details={"app_id": app_id}
            )

        # Get app from database
        db_app = self.db.query(DBApp).filter(DBApp.id == app_id).first()
        if not db_app:
            raise AppNotFoundError(
                f"App '{app_id}' not found",
                details={"app_id": app_id}
            )
        
        # Convert to schema for status check
        app = self._db_app_to_schema(db_app)

        was_running = False
        try:
            # Stop container before modifying resources
            was_running = app.status == AppStatus.RUNNING
            if was_running:
                logger.info(f"Stopping {app_id} for config update")
                await self.stop_app(app_id)

            # Update database config first
            if db_app.config is None:
                db_app.config = {}
            
            # Create a new config dict to ensure SQLAlchemy detects changes
            new_config = db_app.config.copy()

            if cpu_cores is not None:
                new_config['cpu_cores'] = cpu_cores
            if memory_mb is not None:
                new_config['memory_mb'] = memory_mb
            if disk_gb is not None:
                new_config['disk_gb'] = disk_gb

            # Reassign to trigger SQLAlchemy update detection
            db_app.config = new_config
            db_app.updated_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(db_app)

            # Update LXC configuration
            config_updates = {}
            if cpu_cores is not None:
                config_updates['cores'] = cpu_cores
            if memory_mb is not None:
                config_updates['memory'] = memory_mb
            
            # Apply CPU/Memory changes
            if config_updates:
                await self.proxmox_service.update_lxc_config(
                    node=app.node,
                    vmid=app.lxc_id,
                    config=config_updates
                )
            
            # Handle disk resize separately
            if disk_gb is not None:
                await self.proxmox_service.resize_lxc_disk(
                    app.node,
                    app.lxc_id,
                    disk_gb
                )

            # Restart if it was running
            if was_running:
                logger.info(f"Restarting {app_id} with new configuration")
                await self.start_app(app_id)

            logger.info(f"✓ Successfully updated config for {app_id}")

            # Return updated app
            return await self.get_app(app_id)

        except Exception as e:
            logger.error(f"Config update failed for {app_id}: {e}", exc_info=True)
            self.db.rollback()

            # Try to restart app if it was running (rollback attempt)
            if was_running:
                try:
                    logger.info(f"Attempting to restart {app_id} after failed update")
                    await self.start_app(app_id)
                except Exception as restart_error:
                    logger.error(f"Failed to restart {app_id} after update failure: {restart_error}")

            raise AppOperationError(
                f"Failed to update configuration: {str(e)}",
                details={"app_id": app_id, "cpu_cores": cpu_cores, "memory_mb": memory_mb, "disk_gb": disk_gb}
            ) from e

    async def deploy_app(self, app_data: AppCreate) -> App:
        """Deploy a new application"""
        app_id = f"{app_data.catalog_id}-{app_data.hostname}"
        
        # Check if app already exists in database
        existing_app = self.db.query(DBApp).filter(DBApp.id == app_id).first()
        if existing_app:
            raise AppAlreadyExistsError(
                f"Application '{app_id}' already exists",
                details={"app_id": app_id, "existing_status": existing_app.status}
            )
        
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
        
        # Assign ports early (before container creation) so we can clean them up if deployment fails
        public_port = None
        internal_port = None
        
        try:
            # Step 0: Assign ports for this app
            await self._log_deployment(app_id, "info", "Assigning network ports")
            deployment_status.progress = 5
            deployment_status.current_step = "Assigning ports"
            
            public_port, internal_port = await self.port_manager.assign_next_available_ports(app_id)
            await self._log_deployment(app_id, "info", f"Assigned ports: public={public_port}, internal={internal_port}")
            
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

            volumes_info = await self._setup_docker_compose(target_node, vmid, catalog_item, app_data)
            
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
                    # Create virtual host for this app with port-based configuration
                    vhost_created = await self.proxy_manager.create_vhost(
                        app_name=app_data.hostname,
                        backend_ip=container_ip,
                        backend_port=primary_port,
                        public_port=public_port,
                        internal_port=internal_port
                    )
                    
                    if vhost_created:
                        # Get appliance WAN IP for port-based access
                        appliance_wan_ip = None
                        if hasattr(self.proxmox_service, 'network_manager') and self.proxmox_service.network_manager:
                            appliance_info = self.proxmox_service.network_manager.appliance_info
                            if appliance_info:
                                appliance_wan_ip = appliance_info.wan_ip
                        
                        # Generate both public and iframe URLs using port-based access
                        if appliance_wan_ip:
                            access_url = f"http://{appliance_wan_ip}:{public_port}"
                            iframe_url = f"http://{appliance_wan_ip}:{internal_port}"
                            await self._log_deployment(app_id, "info", f"✓ Reverse proxy configured")
                            await self._log_deployment(app_id, "info", f"  • LAN access: {access_url}")
                            await self._log_deployment(app_id, "info", f"  • Canvas access: {iframe_url}")
                            await self._log_deployment(app_id, "info", f"  • Direct access: http://{container_ip}:{primary_port}")
                        else:
                            # Fallback if we can't get appliance IP - use localhost with ports
                            access_url = f"http://localhost:{public_port}"
                            iframe_url = f"http://localhost:{internal_port}"
                            await self._log_deployment(app_id, "warning", "Could not determine appliance WAN IP")
                            await self._log_deployment(app_id, "info", f"  • Local access: {access_url}")
                            await self._log_deployment(app_id, "info", f"  • Direct access: http://{container_ip}:{primary_port}")
                    else:
                        # Fallback to direct access
                        access_url = f"http://{container_ip}:{primary_port}" if container_ip else None
                        iframe_url = None
                        await self._log_deployment(app_id, "warning", "Reverse proxy configuration failed - using direct access")
                        
                except (ConnectionError, TimeoutError) as proxy_error:
                    logger.warning(f"Network error configuring reverse proxy: {proxy_error}")
                    access_url = f"http://{container_ip}:{primary_port}" if container_ip else None
                    iframe_url = None
                    await self._log_deployment(app_id, "warning", f"Reverse proxy network error - using direct access")
                except Exception as proxy_error:
                    logger.warning(f"Unexpected error configuring reverse proxy: {proxy_error}", exc_info=True)
                    access_url = f"http://{container_ip}:{primary_port}" if container_ip else None
                    iframe_url = None
                    await self._log_deployment(app_id, "warning", f"Reverse proxy error - using direct access")
            else:
                # No proxy manager available - use direct access
                access_url = f"http://{container_ip}:{primary_port}" if container_ip else None
                iframe_url = None
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
                iframe_url=iframe_url,
                lxc_id=vmid,
                node=target_node,
                config=app_data.config,
                environment=app_data.environment,
                ports={port: port for port in catalog_item.ports},  # Simplified port mapping
                public_port=public_port,
                internal_port=internal_port
            )
            
            # Save to database
            db_app = DBApp(
                id=app.id,
                catalog_id=app.catalog_id,
                name=app.name,
                hostname=app.hostname,
                status=app.status.value,
                url=app.url,
                iframe_url=app.iframe_url,
                lxc_id=app.lxc_id,
                node=app.node,
                config=app.config,
                ports=app.ports,
                volumes=volumes_info,
                environment=app.environment,
                public_port=public_port,
                internal_port=internal_port,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            self.db.add(db_app)
            self.db.commit()
            self.db.refresh(db_app)
            
            # Complete deployment
            deployment_status.status = AppStatus.RUNNING
            deployment_status.progress = 100
            deployment_status.current_step = "Deployment complete"
            
            await self._log_deployment(app_id, "info", f"Application deployed successfully at {app.url}")
            
            return app
            
        except ProxmoxError as e:
            # Handle Proxmox-specific errors
            deployment_status.status = AppStatus.ERROR
            deployment_status.error = f"Proxmox error: {str(e)}"
            await self._log_deployment(app_id, "error", f"Proxmox error during deployment: {e}")
            logger.error(f"Proxmox error deploying {app_id}: {e}", extra={"app_id": app_id, "vmid": locals().get('vmid'), "node": locals().get('target_node')})
            
            await self._cleanup_failed_deployment(app_id, locals().get('vmid'), locals().get('target_node'))
            raise AppDeploymentError(
                f"Deployment failed due to Proxmox error: {str(e)}",
                details={"app_id": app_id, "error_type": "proxmox", "vmid": locals().get('vmid')}
            ) from e
            
        except DatabaseError as e:
            # Handle database errors
            deployment_status.status = AppStatus.ERROR
            deployment_status.error = f"Database error: {str(e)}"
            await self._log_deployment(app_id, "error", f"Database error during deployment: {e}")
            logger.error(f"Database error deploying {app_id}: {e}", extra={"app_id": app_id})
            
            await self._cleanup_failed_deployment(app_id, locals().get('vmid'), locals().get('target_node'))
            raise AppDeploymentError(
                f"Deployment failed due to database error: {str(e)}",
                details={"app_id": app_id, "error_type": "database"}
            ) from e
            
        except Exception as e:
            # Handle unexpected errors
            deployment_status.status = AppStatus.ERROR
            deployment_status.error = str(e)
            await self._log_deployment(app_id, "error", f"Unexpected deployment error: {e}")
            logger.error(
                f"Unexpected error deploying {app_id}: {e}",
                extra={"app_id": app_id, "vmid": locals().get('vmid'), "node": locals().get('target_node')},
                exc_info=True
            )
            
            await self._cleanup_failed_deployment(app_id, locals().get('vmid'), locals().get('target_node'))
            raise AppDeploymentError(
                f"Deployment failed: {str(e)}",
                details={"app_id": app_id, "error_type": "unexpected"}
            ) from e
    
    async def _cleanup_failed_deployment(self, app_id: str, vmid: Optional[int], target_node: Optional[str]) -> None:
        """Cleanup resources after a failed deployment"""
        try:
            # Release ports if they were assigned
            try:
                await self.port_manager.release_ports_for_app(app_id)
                logger.info(f"Released ports for failed deployment", extra={"app_id": app_id})
            except Exception as port_cleanup_error:
                logger.warning(f"Error releasing ports during cleanup: {port_cleanup_error}", extra={"app_id": app_id})
            
            # Destroy LXC container if it was created
            if vmid and target_node:
                logger.info(f"Cleaning up failed deployment: destroying LXC {vmid}", extra={"app_id": app_id, "vmid": vmid, "node": target_node})
                task_id = await self.proxmox_service.destroy_lxc(target_node, vmid, force=True)
                await self.proxmox_service.wait_for_task(target_node, task_id, timeout=60)
                logger.info(f"✓ Cleanup successful: LXC {vmid} destroyed", extra={"app_id": app_id, "vmid": vmid})
        except ProxmoxError as cleanup_error:
            logger.error(f"Proxmox error during cleanup of {vmid}: {cleanup_error}", extra={"app_id": app_id, "vmid": vmid})
        except Exception as cleanup_error:
            logger.error(f"Unexpected error during cleanup of {vmid}: {cleanup_error}", extra={"app_id": app_id, "vmid": vmid}, exc_info=True)

    async def _setup_docker_compose(self, node: str, vmid: int, catalog_item: AppCatalogItem, app_data: AppCreate) -> list:
        """
        Setup Docker Compose configuration in the container.

        Returns:
            list: Volume mappings [{"host_path": "...", "container_path": "..."}]
        """
        try:
            # Merge environment variables
            env_vars = {**catalog_item.environment, **app_data.environment}

            # Update docker-compose with custom environment
            compose_config = catalog_item.docker_compose.copy()

            # Extract and resolve volume paths
            volumes_info = []
            base_volumes_path = f"/var/lib/proximity/volumes/{app_data.hostname}"

            for service_name, service_config in compose_config.get("services", {}).items():
                if "volumes" in service_config:
                    for i, volume in enumerate(service_config["volumes"]):
                        if isinstance(volume, str) and ":" in volume:
                            parts = volume.split(":")
                            local_path = parts[0]
                            container_path = parts[1]

                            # Resolve host path
                            if local_path.startswith("./") or local_path.startswith("."):
                                # Relative path - resolve to absolute
                                resolved_local = local_path.replace("./", "").replace(".", "")
                                host_path = f"{base_volumes_path}/{resolved_local}" if resolved_local else base_volumes_path
                            else:
                                # Already absolute or named volume
                                host_path = f"{base_volumes_path}/{local_path}"

                            # Update compose config with resolved path
                            service_config["volumes"][i] = f"{host_path}:{container_path}"

                            # Track volume info
                            volumes_info.append({
                                "host_path": host_path,
                                "container_path": container_path
                            })
            
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

            return volumes_info

        except ProxmoxError as e:
            logger.error(f"Proxmox error setting up Docker Compose in LXC {vmid}: {e}")
            raise AppDeploymentError(
                f"Failed to setup Docker Compose: {str(e)}",
                details={"vmid": vmid, "node": node, "error_type": "proxmox"}
            ) from e
        except (yaml.YAMLError, ValueError) as e:
            logger.error(f"Invalid Docker Compose configuration: {e}")
            raise ValidationError(
                f"Invalid Docker Compose configuration: {str(e)}",
                details={"vmid": vmid, "catalog_id": catalog_item.id}
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error setting up Docker Compose in LXC {vmid}: {e}", exc_info=True)
            raise AppDeploymentError(
                f"Failed to setup Docker Compose: {str(e)}",
                details={"vmid": vmid, "node": node}
            ) from e

    async def _log_deployment(self, app_id: str, level: str, message: str, step: Optional[str] = None) -> None:
        """Add log entry to deployment status and database"""
        if app_id in self._deployment_status:
            log_entry = DeploymentLog(
                timestamp=datetime.now(),
                level=level,
                message=message,
                step=step
            )
            self._deployment_status[app_id].logs.append(log_entry)
            logger.info(f"[{app_id}] {message}")
            
            # Also save to database if app exists
            db_app = self.db.query(DBApp).filter(DBApp.id == app_id).first()
            if db_app:
                db_log = DBDeploymentLog(
                    app_id=app_id,
                    timestamp=datetime.now(UTC),
                    level=level,
                    message=message,
                    step=step
                )
                self.db.add(db_log)
                try:
                    self.db.commit()
                except DatabaseError as e:
                    logger.error(f"Database error saving deployment log for {app_id}: {e}", extra={"app_id": app_id})
                    self.db.rollback()
                except Exception as e:
                    logger.error(f"Unexpected error saving deployment log for {app_id}: {e}", extra={"app_id": app_id}, exc_info=True)
                    self.db.rollback()

    async def get_deployment_status(self, app_id: str) -> DeploymentStatus:
        """Get deployment status for an app"""
        if app_id not in self._deployment_status:
            raise AppNotFoundError(
                f"No deployment status found for application '{app_id}'",
                details={"app_id": app_id, "available_deployments": list(self._deployment_status.keys())}
            )
        return self._deployment_status[app_id]

    async def update_app(self, app_id: str, app_update: AppUpdate) -> App:
        """Update an existing application"""
        db_app = self.db.query(DBApp).filter(DBApp.id == app_id).first()
        if not db_app:
            raise AppNotFoundError(
                f"Application '{app_id}' not found",
                details={"app_id": app_id}
            )
        
        if app_update.config is not None:
            db_app.config = {**db_app.config, **app_update.config}
        
        if app_update.environment is not None:
            db_app.environment = {**db_app.environment, **app_update.environment}
            # Would need to update container environment and restart
        
        if app_update.status is not None:
            db_app.status = app_update.status.value
        
        db_app.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(db_app)

        return self._db_app_to_schema(db_app)

    async def update_app(self, app_id: str, user_id: int) -> App:
        """
        Update an application with pre-update backup and health check.

        This method implements the "Fearless Update" workflow:
        1. Create pre-update backup (safety net)
        2. Pull latest images
        3. Recreate containers
        4. Health check
        5. Rollback on failure (future)

        Args:
            app_id: Application ID to update
            user_id: User ID requesting the update

        Returns:
            Updated App object

        Raises:
            AppUpdateError: If update fails at any stage
        """
        from services.backup_service import BackupService
        from core.exceptions import AppUpdateError
        import httpx
        import asyncio

        # Get app
        app = self.db.query(DBApp).filter(DBApp.id == app_id).first()
        if not app:
            raise AppNotFoundError(f"App {app_id} not found")

        logger.info(f"🔄 Starting update for app '{app.hostname}' (ID: {app_id})")

        # Update app status
        app.status = "updating"
        self.db.commit()

        try:
            # ============================================================
            # PHASE 1: PRE-UPDATE SAFETY BACKUP (CRITICAL)
            # ============================================================
            logger.info(f"📦 Creating pre-update backup for '{app.hostname}'")

            backup_service = BackupService(self.db, self.proxmox_service)

            try:
                backup = await backup_service.create_backup(
                    app_id=app_id,
                    storage="local",  # Will auto-detect from container
                    compress="zstd",
                    mode="snapshot"
                )

                # Wait for backup to complete (with timeout)
                max_wait = 300  # 5 minutes
                wait_interval = 5
                elapsed = 0

                while elapsed < max_wait:
                    await asyncio.sleep(wait_interval)
                    self.db.refresh(backup)

                    if backup.status == "available":
                        logger.info(f"✅ Pre-update backup completed: {backup.filename}")
                        break
                    elif backup.status == "failed":
                        raise AppUpdateError(
                            f"Failed to create pre-update backup: {backup.error_message}. Update aborted."
                        )

                    elapsed += wait_interval

                if backup.status != "available":
                    raise AppUpdateError(
                        "Pre-update backup timeout. Update aborted for safety."
                    )

            except Exception as e:
                logger.error(f"❌ Backup creation failed: {e}")
                app.status = "running"  # Restore original status
                self.db.commit()
                raise AppUpdateError(f"Failed to create pre-update backup. Update aborted: {str(e)}")

            # ============================================================
            # PHASE 2: PERFORM UPDATE
            # ============================================================
            logger.info(f"🚀 Backup successful, proceeding with update for '{app.hostname}'")

            # Pull latest images
            logger.info(f"📥 Pulling latest images...")
            pull_result = await self.proxmox_service.execute_in_container(
                node=app.node,
                vmid=app.lxc_id,
                command="cd /root && docker compose pull"
            )
            logger.info(f"Pull result: {pull_result[:200]}..." if len(pull_result) > 200 else pull_result)

            # Recreate containers with new images
            logger.info(f"🔄 Recreating containers...")
            up_result = await self.proxmox_service.execute_in_container(
                node=app.node,
                vmid=app.lxc_id,
                command="cd /root && docker compose up -d --remove-orphans"
            )
            logger.info(f"Up result: {up_result[:200]}..." if len(up_result) > 200 else up_result)

            # ============================================================
            # PHASE 3: POST-UPDATE HEALTH CHECK
            # ============================================================
            logger.info(f"🏥 Waiting for services to initialize...")
            await asyncio.sleep(20)  # Allow services to start

            # Perform health check
            if app.url and app.url != "None" and app.url != "null":
                logger.info(f"🔍 Performing health check on {app.url}")

                try:
                    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                        response = await client.get(app.url)

                        if 200 <= response.status_code < 400:
                            logger.info(f"✅ Health check passed: {response.status_code}")

                            # Update success
                            app.status = "running"
                            app.updated_at = datetime.now(UTC)
                            self.db.commit()

                            logger.info(f"🎉 Update completed successfully for '{app.hostname}'")
                            return app
                        else:
                            raise AppUpdateError(
                                f"Health check failed with status {response.status_code}"
                            )

                except httpx.RequestError as e:
                    logger.error(f"❌ Health check failed: {e}")
                    raise AppUpdateError(f"Health check failed: {str(e)}")
            else:
                # No URL to check, assume success based on docker compose result
                logger.warning(f"⚠️  No URL available for health check, assuming success")
                app.status = "running"
                app.updated_at = datetime.now(UTC)
                self.db.commit()
                return app

        except AppUpdateError:
            # Already logged, just update status and re-raise
            app.status = "update_failed"
            self.db.commit()
            raise

        except Exception as e:
            logger.error(f"💥 Unexpected error during update: {e}", exc_info=True)
            app.status = "update_failed"
            self.db.commit()
            raise AppUpdateError(f"Update failed: {str(e)}")


# Singleton instance - will be injected with proxmox_service
app_service: Optional[AppService] = None


def get_app_service(db: Session = Depends(get_db)) -> AppService:
    """Dependency injection for AppService with database session"""
    from services.proxmox_service import proxmox_service
    
    # Try to get proxy_manager from app state if available
    proxy_manager = None
    try:
        from starlette.concurrency import iterate_in_threadpool
        from contextvars import ContextVar
        # This will be set if we're in a request context
        # For now, we'll pass None and let it be set later if needed
    except:
        pass
    
    # Create a new AppService instance with the database session
    # This ensures each request gets its own db session
    return AppService(proxmox_service, db, proxy_manager)