"""
Backup Service for managing application backups.
Handles backup creation, listing, restoration, and deletion.
"""

from datetime import datetime
from typing import List, Optional
import asyncio
from sqlalchemy.orm import Session
from models.database import Backup, App
from services.proxmox_service import ProxmoxService


class BackupService:
    """Service for managing application backups."""

    def __init__(self, db: Session, proxmox_service: Optional[ProxmoxService] = None):
        """
        Initialize backup service.

        Args:
            db: Database session
            proxmox_service: Optional Proxmox service instance (for testing)
        """
        self.db = db
        self.proxmox = proxmox_service or ProxmoxService()

    async def create_backup(
        self,
        app_id: str,
        storage: str = "local",
        compress: str = "zstd",
        mode: str = "snapshot"
    ) -> Backup:
        """
        Create a backup for an application.

        Args:
            app_id: Application ID
            storage: Proxmox storage name
            compress: Compression type (zstd, gzip, none)
            mode: Backup mode (snapshot, stop)

        Returns:
            Backup object

        Raises:
            ValueError: If app not found
            Exception: If Proxmox backup creation fails
        """
        # Get app
        app = self.db.query(App).filter(App.id == app_id).first()
        if not app:
            raise ValueError(f"App {app_id} not found")

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y_%m_%d-%H_%M_%S")
        extension = ".tar.zst" if compress == "zstd" else ".tar.gz" if compress == "gzip" else ".tar"
        filename = f"vzdump-lxc-{app.lxc_id}-{timestamp}{extension}"

        # Create backup record
        backup = Backup(
            app_id=app_id,
            filename=filename,
            storage_name=storage,
            backup_type="vzdump",
            status="creating"
        )
        self.db.add(backup)
        self.db.commit()
        self.db.refresh(backup)

        try:
            # Start Proxmox backup
            task_id = await self.proxmox.create_vzdump(
                node=app.node,
                vmid=app.lxc_id,
                storage=storage,
                compress=compress,
                mode=mode
            )

            # Start background polling for completion
            asyncio.create_task(self._poll_backup_completion(backup.id))

            return backup

        except Exception as e:
            # Mark backup as failed
            backup.status = "failed"
            backup.error_message = str(e)
            self.db.commit()
            raise

    async def list_backups_for_app(self, app_id: str) -> List[Backup]:
        """
        List all backups for an application.

        Args:
            app_id: Application ID

        Returns:
            List of backups ordered by creation date (newest first)
        """
        backups = self.db.query(Backup).filter(
            Backup.app_id == app_id
        ).order_by(Backup.created_at.desc()).all()

        return backups

    async def get_backup(self, backup_id: int) -> Backup:
        """
        Get a specific backup.

        Args:
            backup_id: Backup ID

        Returns:
            Backup object

        Raises:
            ValueError: If backup not found
        """
        backup = self.db.query(Backup).filter(Backup.id == backup_id).first()
        if not backup:
            raise ValueError(f"Backup {backup_id} not found")

        return backup

    async def restore_from_backup(self, backup_id: int) -> dict:
        """
        Restore an application from a backup.

        Args:
            backup_id: Backup ID

        Returns:
            Restore operation result

        Raises:
            ValueError: If backup not found or not available
        """
        # Get backup
        backup = await self.get_backup(backup_id)

        # Check backup is available
        if backup.status != "available":
            raise ValueError(f"Backup is not available for restore (status: {backup.status})")

        # Get app
        app = self.db.query(App).filter(App.id == backup.app_id).first()
        if not app:
            raise ValueError(f"App {backup.app_id} not found")

        # Update backup status
        backup.status = "restoring"
        self.db.commit()

        try:
            # Stop container
            await self.proxmox.stop_lxc(app.node, app.lxc_id)

            # Restore from backup
            restore_task = await self.proxmox.restore_backup(
                node=app.node,
                vmid=app.lxc_id,
                backup_file=backup.filename,
                storage=backup.storage_name
            )

            # Start container
            await self.proxmox.start_lxc(app.node, app.lxc_id)

            # Update backup status
            backup.status = "available"
            self.db.commit()

            return {
                "success": True,
                "message": "Restore completed successfully",
                "backup_id": backup_id,
                "app_id": app.id
            }

        except Exception as e:
            # Mark backup as available again
            backup.status = "available"
            backup.error_message = f"Restore failed: {str(e)}"
            self.db.commit()
            raise

    async def delete_backup(self, backup_id: int) -> dict:
        """
        Delete a backup.

        Args:
            backup_id: Backup ID

        Returns:
            Deletion result

        Raises:
            ValueError: If backup not found
        """
        # Get backup
        backup = await self.get_backup(backup_id)

        # Get app for node info
        app = self.db.query(App).filter(App.id == backup.app_id).first()
        if not app:
            raise ValueError(f"App {backup.app_id} not found")

        try:
            # Delete from Proxmox storage
            await self.proxmox.delete_backup(
                node=app.node,
                storage=backup.storage_name,
                backup_file=backup.filename
            )

            # Delete from database
            self.db.delete(backup)
            self.db.commit()

            return {
                "success": True,
                "message": "Backup deleted successfully",
                "backup_id": backup_id
            }

        except Exception as e:
            raise Exception(f"Failed to delete backup: {str(e)}")

    async def _poll_backup_completion(self, backup_id: int, timeout: int = 3600):
        """
        Poll for backup completion in the background.

        Args:
            backup_id: Backup ID to poll
            timeout: Maximum time to wait in seconds (default 1 hour)
        """
        start_time = datetime.utcnow().timestamp()
        poll_interval = 5  # seconds

        while True:
            await asyncio.sleep(poll_interval)

            # Get current backup state
            backup = self.db.query(Backup).filter(Backup.id == backup_id).first()
            if not backup or backup.status != "creating":
                break

            # Get app
            app = self.db.query(App).filter(App.id == backup.app_id).first()
            if not app:
                break

            try:
                # Check if backup exists in Proxmox
                backup_list = await self.proxmox.get_backup_list(app.node, app.lxc_id)

                # Find our backup
                for proxmox_backup in backup_list:
                    if backup.filename in proxmox_backup.get("volid", ""):
                        # Backup completed!
                        backup.status = "available"
                        backup.size_bytes = proxmox_backup.get("size", 0)
                        backup.completed_at = datetime.utcnow()
                        self.db.commit()
                        return

            except Exception as e:
                # Log error but continue polling
                print(f"Error polling backup {backup_id}: {e}")

            # Check timeout
            if datetime.utcnow().timestamp() - start_time > timeout:
                backup.status = "failed"
                backup.error_message = "Backup creation timeout"
                self.db.commit()
                break
