"""
Database Cleanup Service

This service handles automated cleanup of stale database records, particularly:
1. "Ghost" apps - Failed deployments that exist in DB but not in Proxmox
2. Old error status apps - Configurable retention period
3. Orphaned resources - Ports, volumes, etc. from deleted apps

Configuration via environment variables:
- CLEANUP_ENABLED: Enable automatic cleanup (default: true)
- ERROR_RETENTION_HOURS: Hours to keep error status apps (default: 24)
- GHOST_CLEANUP_ENABLED: Clean apps not in Proxmox (default: true)
- CLEANUP_INTERVAL_MINUTES: How often to run cleanup (default: 60)
- CLEANUP_DRY_RUN: Log what would be deleted without deleting (default: false)
"""

import asyncio
import logging
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Optional, Set
from sqlalchemy.orm import Session

from models.database import App as DBApp, get_db
from services.proxmox_service import ProxmoxService, ProxmoxError
from core.config import settings

logger = logging.getLogger(__name__)


class CleanupConfig:
    """Configuration for cleanup service (loaded from environment)"""
    
    def __init__(self):
        # Read from environment with defaults
        self.enabled = settings.get_bool("CLEANUP_ENABLED", True)
        self.error_retention_hours = settings.get_int("ERROR_RETENTION_HOURS", 24)
        self.ghost_cleanup_enabled = settings.get_bool("GHOST_CLEANUP_ENABLED", True)
        self.cleanup_interval_minutes = settings.get_int("CLEANUP_INTERVAL_MINUTES", 60)
        self.dry_run = settings.get_bool("CLEANUP_DRY_RUN", False)
        
        # Validation
        if self.error_retention_hours < 1:
            logger.warning(f"ERROR_RETENTION_HOURS too low ({self.error_retention_hours}), setting to 1")
            self.error_retention_hours = 1
        
        if self.cleanup_interval_minutes < 5:
            logger.warning(f"CLEANUP_INTERVAL_MINUTES too low ({self.cleanup_interval_minutes}), setting to 5")
            self.cleanup_interval_minutes = 5
    
    def __str__(self):
        return (
            f"CleanupConfig(enabled={self.enabled}, "
            f"error_retention={self.error_retention_hours}h, "
            f"ghost_cleanup={self.ghost_cleanup_enabled}, "
            f"interval={self.cleanup_interval_minutes}m, "
            f"dry_run={self.dry_run})"
        )


class CleanupStats:
    """Statistics for cleanup operations"""
    
    def __init__(self):
        self.ghost_apps_removed = 0
        self.old_errors_removed = 0
        self.ports_freed = 0
        self.total_removed = 0
        self.last_run: Optional[datetime] = None
        self.errors: List[str] = []
    
    def reset(self):
        """Reset counters for new cleanup run"""
        self.ghost_apps_removed = 0
        self.old_errors_removed = 0
        self.ports_freed = 0
        self.total_removed = 0
        self.errors = []
    
    def __str__(self):
        return (
            f"CleanupStats(ghosts={self.ghost_apps_removed}, "
            f"old_errors={self.old_errors_removed}, "
            f"ports_freed={self.ports_freed}, "
            f"total={self.total_removed})"
        )


class CleanupService:
    """Service for cleaning up stale database records"""
    
    def __init__(self, proxmox_service: ProxmoxService, db: Session):
        self.proxmox_service = proxmox_service
        self.db = db
        self.config = CleanupConfig()
        self.stats = CleanupStats()
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info(f"🧹 CleanupService initialized: {self.config}")
    
    async def get_proxmox_lxc_ids(self) -> Set[int]:
        """
        Get all LXC container IDs that actually exist in Proxmox.
        
        Returns:
            Set of VMIDs that exist across all nodes
        """
        lxc_ids = set()
        
        try:
            nodes = await self.proxmox_service.get_nodes()
            
            for node in nodes:
                node_name = node.node if hasattr(node, 'node') else str(node)
                try:
                    containers = await self.proxmox_service.get_lxc_containers(node_name)
                    for container in containers:
                        vmid = container['vmid'] if isinstance(container, dict) else container.vmid
                        lxc_ids.add(int(vmid))
                except ProxmoxError as e:
                    logger.warning(f"Failed to get containers from node {node_name}: {e}")
                    continue
            
            logger.info(f"📦 Found {len(lxc_ids)} LXC containers in Proxmox: {sorted(lxc_ids)}")
            return lxc_ids
            
        except Exception as e:
            logger.error(f"Failed to get Proxmox LXC IDs: {e}")
            self.stats.errors.append(f"Proxmox query failed: {str(e)}")
            return set()
    
    async def find_ghost_apps(self) -> List[DBApp]:
        """
        Find "ghost" apps - records in DB but containers don't exist in Proxmox.
        
        Returns:
            List of DBApp records that should be cleaned up
        """
        if not self.config.ghost_cleanup_enabled:
            logger.debug("Ghost cleanup disabled, skipping")
            return []
        
        # Get actual LXC IDs from Proxmox
        proxmox_lxc_ids = await self.get_proxmox_lxc_ids()
        
        if not proxmox_lxc_ids:
            logger.warning("No Proxmox LXC IDs found - skipping ghost cleanup to be safe")
            return []
        
        # Query all apps from database
        db_apps = self.db.query(DBApp).all()
        
        # Find apps with LXC IDs not in Proxmox
        ghost_apps = []
        for app in db_apps:
            if app.lxc_id not in proxmox_lxc_ids:
                ghost_apps.append(app)
        
        if ghost_apps:
            logger.info(f"👻 Found {len(ghost_apps)} ghost apps (DB records without Proxmox containers)")
            for app in ghost_apps[:5]:  # Log first 5
                logger.info(f"  - {app.hostname} (LXC {app.lxc_id}, status: {app.status})")
            if len(ghost_apps) > 5:
                logger.info(f"  ... and {len(ghost_apps) - 5} more")
        
        return ghost_apps
    
    async def find_old_error_apps(self) -> List[DBApp]:
        """
        Find old apps with 'error' status based on retention policy.
        
        Returns:
            List of DBApp records that should be cleaned up
        """
        retention_cutoff = datetime.now(UTC) - timedelta(hours=self.config.error_retention_hours)
        
        old_errors = (
            self.db.query(DBApp)
            .filter(DBApp.status == 'error')
            .filter(DBApp.created_at < retention_cutoff)
            .all()
        )
        
        if old_errors:
            logger.info(
                f"🗑️  Found {len(old_errors)} old error apps "
                f"(older than {self.config.error_retention_hours} hours)"
            )
        
        return old_errors
    
    def delete_app_record(self, app: DBApp) -> bool:
        """
        Delete an app record from database.
        
        Args:
            app: DBApp record to delete
        
        Returns:
            True if deleted, False if error
        """
        try:
            if self.config.dry_run:
                logger.info(f"[DRY RUN] Would delete: {app.hostname} (LXC {app.lxc_id})")
                return True
            
            # Track ports being freed
            if app.public_port:
                self.stats.ports_freed += 1
            if app.internal_port:
                self.stats.ports_freed += 1
            
            self.db.delete(app)
            logger.debug(f"✓ Deleted: {app.hostname} (LXC {app.lxc_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete app {app.hostname}: {e}")
            self.stats.errors.append(f"Delete failed for {app.hostname}: {str(e)}")
            return False
    
    async def cleanup_ghost_apps(self) -> int:
        """
        Clean up ghost apps (DB records without Proxmox containers).
        
        Returns:
            Number of apps cleaned up
        """
        ghost_apps = await self.find_ghost_apps()
        
        if not ghost_apps:
            return 0
        
        cleaned = 0
        for app in ghost_apps:
            if self.delete_app_record(app):
                cleaned += 1
        
        if cleaned > 0 and not self.config.dry_run:
            self.db.commit()
            logger.info(f"✓ Cleaned up {cleaned} ghost apps")
        
        self.stats.ghost_apps_removed = cleaned
        return cleaned
    
    async def cleanup_old_errors(self) -> int:
        """
        Clean up old error status apps based on retention policy.
        
        Returns:
            Number of apps cleaned up
        """
        old_errors = await self.find_old_error_apps()
        
        if not old_errors:
            return 0
        
        cleaned = 0
        for app in old_errors:
            if self.delete_app_record(app):
                cleaned += 1
        
        if cleaned > 0 and not self.config.dry_run:
            self.db.commit()
            logger.info(f"✓ Cleaned up {cleaned} old error apps")
        
        self.stats.old_errors_removed = cleaned
        return cleaned
    
    async def run_cleanup(self) -> CleanupStats:
        """
        Run full cleanup cycle.
        
        Returns:
            CleanupStats with results
        """
        if not self.config.enabled:
            logger.debug("Cleanup disabled, skipping")
            return self.stats
        
        logger.info("🧹 Starting cleanup cycle...")
        self.stats.reset()
        self.stats.last_run = datetime.now(UTC)
        
        try:
            # Phase 1: Ghost apps (DB records without Proxmox containers)
            ghost_cleaned = await self.cleanup_ghost_apps()
            
            # Phase 2: Old error status apps
            error_cleaned = await self.cleanup_old_errors()
            
            self.stats.total_removed = ghost_cleaned + error_cleaned
            
            if self.stats.total_removed > 0:
                mode = "[DRY RUN] " if self.config.dry_run else ""
                logger.info(
                    f"✅ {mode}Cleanup complete: {self.stats} "
                    f"(freed {self.stats.ports_freed} ports)"
                )
            else:
                logger.info("✅ Cleanup complete: No records to clean")
            
            if self.stats.errors:
                logger.warning(f"⚠️  Cleanup had {len(self.stats.errors)} errors")
        
        except Exception as e:
            logger.error(f"Cleanup cycle failed: {e}", exc_info=True)
            self.stats.errors.append(f"Cleanup cycle error: {str(e)}")
        
        return self.stats
    
    async def start_background_cleanup(self):
        """Start background cleanup task that runs periodically"""
        if self._cleanup_task and not self._cleanup_task.done():
            logger.warning("Cleanup task already running")
            return
        
        logger.info(
            f"🧹 Starting background cleanup "
            f"(interval: {self.config.cleanup_interval_minutes} minutes)"
        )
        
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Background loop for periodic cleanup"""
        while True:
            try:
                # Wait for interval (convert minutes to seconds)
                await asyncio.sleep(self.config.cleanup_interval_minutes * 60)
                
                # Run cleanup
                await self.run_cleanup()
                
            except asyncio.CancelledError:
                logger.info("Cleanup loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
                # Continue running despite errors
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def stop_background_cleanup(self):
        """Stop background cleanup task"""
        if self._cleanup_task and not self._cleanup_task.done():
            logger.info("Stopping background cleanup...")
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("✓ Background cleanup stopped")
    
    def get_stats(self) -> Dict:
        """Get current cleanup statistics as dict"""
        return {
            "enabled": self.config.enabled,
            "last_run": self.stats.last_run.isoformat() if self.stats.last_run else None,
            "ghost_apps_removed": self.stats.ghost_apps_removed,
            "old_errors_removed": self.stats.old_errors_removed,
            "ports_freed": self.stats.ports_freed,
            "total_removed": self.stats.total_removed,
            "errors": self.stats.errors,
            "config": {
                "error_retention_hours": self.config.error_retention_hours,
                "ghost_cleanup_enabled": self.config.ghost_cleanup_enabled,
                "cleanup_interval_minutes": self.config.cleanup_interval_minutes,
                "dry_run": self.config.dry_run
            }
        }


# Singleton instance - will be initialized in main.py
_cleanup_service: Optional[CleanupService] = None


def get_cleanup_service(
    proxmox_service: ProxmoxService = None,
    db: Session = None
) -> Optional[CleanupService]:
    """
    Get or create cleanup service instance.
    
    Args:
        proxmox_service: ProxmoxService instance (required for first call)
        db: Database session (required for first call)
    
    Returns:
        CleanupService instance or None if not initialized
    """
    global _cleanup_service
    
    if _cleanup_service is None:
        if proxmox_service is None or db is None:
            logger.warning("CleanupService not initialized and dependencies not provided")
            return None
        
        _cleanup_service = CleanupService(proxmox_service, db)
    
    return _cleanup_service
