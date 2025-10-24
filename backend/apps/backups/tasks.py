"""
Celery tasks for backup and restore operations.
All backup operations are asynchronous to handle long-running vzdump processes.
"""
import logging
from typing import Optional
from celery import shared_task
from django.utils import timezone
from django.db import transaction

from apps.proxmox import ProxmoxService, ProxmoxError
from apps.backups.models import Backup
from apps.applications.models import Application

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def create_backup_task(
    self,
    application_id: str,
    backup_type: str = 'snapshot',
    compression: str = 'zstd'
):
    """
    Create a backup of an application's LXC container.
    
    Args:
        application_id: Application ID
        backup_type: Backup mode (snapshot, suspend, stop)
        compression: Compression algorithm (zstd, gzip, lzo)
        
    Returns:
        Dictionary with backup_id and status
    """
    backup = None
    
    try:
        # Get application
        try:
            app = Application.objects.select_related('host').get(id=application_id)
        except Application.DoesNotExist:
            logger.error(f"Application {application_id} not found")
            return {
                'success': False,
                'error': f'Application {application_id} not found'
            }
        
        # Create backup record
        backup = Backup.objects.create(
            application=app,
            file_name='',  # Will be updated after backup completes
            storage_name='local',
            backup_type=backup_type,
            compression=compression,
            status='creating'
        )
        
        logger.info(
            f"Starting backup for app {app.name} (LXC {app.lxc_id}), "
            f"backup_id={backup.id}"
        )
        
        # Initialize Proxmox service
        proxmox = ProxmoxService(host_id=app.host.id)
        
        # Create the backup
        result = proxmox.create_lxc_backup(
            node_name=app.node,
            vmid=app.lxc_id,
            storage='local',
            mode=backup_type,
            compress=compression
        )
        
        # Update backup record with results
        backup.file_name = result['file_name']
        backup.size = result.get('size', 0)
        backup.status = 'completed'
        backup.completed_at = timezone.now()
        backup.save()
        
        logger.info(
            f"Backup completed successfully: {backup.file_name} "
            f"({backup.size_mb} MB)"
        )
        
        return {
            'success': True,
            'backup_id': backup.id,
            'file_name': backup.file_name,
            'size': backup.size
        }
        
    except ProxmoxError as e:
        logger.error(f"Proxmox error during backup creation: {e}")
        
        if backup:
            backup.status = 'failed'
            backup.error_message = str(e)
            backup.save()
        
        # Retry on certain errors
        if 'timeout' in str(e).lower() or 'connection' in str(e).lower():
            raise self.retry(exc=e, countdown=60)
        
        return {
            'success': False,
            'backup_id': backup.id if backup else None,
            'error': str(e)
        }
        
    except Exception as e:
        logger.exception(f"Unexpected error during backup creation: {e}")
        
        if backup:
            backup.status = 'failed'
            backup.error_message = f"Internal error: {str(e)}"
            backup.save()
        
        return {
            'success': False,
            'backup_id': backup.id if backup else None,
            'error': str(e)
        }


@shared_task(bind=True, max_retries=2)
def restore_backup_task(self, backup_id: int):
    """
    Restore an application from a backup.
    
    This is a DESTRUCTIVE operation that will overwrite the current container.
    
    Args:
        backup_id: Backup ID to restore from
        
    Returns:
        Dictionary with restore status
    """
    try:
        # Get backup and related application
        try:
            backup = Backup.objects.select_related(
                'application',
                'application__host'
            ).get(id=backup_id)
        except Backup.DoesNotExist:
            logger.error(f"Backup {backup_id} not found")
            return {
                'success': False,
                'error': f'Backup {backup_id} not found'
            }
        
        app = backup.application
        
        # Check if backup is available
        if backup.status != 'completed':
            error = f"Backup {backup_id} is not in completed state (status: {backup.status})"
            logger.error(error)
            return {
                'success': False,
                'error': error
            }
        
        logger.info(
            f"Starting restore for app {app.name} (LXC {app.lxc_id}) "
            f"from backup {backup.file_name}"
        )
        
        # Update statuses
        with transaction.atomic():
            backup.status = 'restoring'
            backup.save()
            
            app.status = 'updating'
            app.save()
        
        # Initialize Proxmox service
        proxmox = ProxmoxService(host_id=app.host.id)
        
        # Stop the container if it's running
        try:
            status = proxmox.get_lxc_status(app.node, app.lxc_id)
            if status.get('status') == 'running':
                logger.info(f"Stopping LXC {app.lxc_id} before restore")
                proxmox.stop_lxc(app.node, app.lxc_id, force=True)
        except Exception as e:
            logger.warning(f"Could not stop container before restore: {e}")
        
        # Perform the restore
        result = proxmox.restore_lxc_backup(
            node_name=app.node,
            vmid=app.lxc_id,
            backup_file=backup.file_name,
            storage=backup.storage_name,
            force=True
        )
        
        # Update statuses back to normal
        with transaction.atomic():
            backup.status = 'completed'
            backup.save()
            
            # Container should be stopped after restore
            app.status = 'stopped'
            app.save()
        
        logger.info(f"Restore completed successfully for app {app.name}")
        
        return {
            'success': True,
            'backup_id': backup.id,
            'application_id': app.id,
            'message': 'Restore completed successfully'
        }
        
    except ProxmoxError as e:
        logger.error(f"Proxmox error during restore: {e}")
        
        # Update backup status back to completed (it's still usable)
        backup.status = 'completed'
        backup.save()
        
        # Mark application as error
        app.status = 'error'
        app.save()
        
        # Retry on certain errors
        if 'timeout' in str(e).lower() or 'connection' in str(e).lower():
            raise self.retry(exc=e, countdown=60)
        
        return {
            'success': False,
            'backup_id': backup_id,
            'error': str(e)
        }
        
    except Exception as e:
        logger.exception(f"Unexpected error during restore: {e}")
        
        # Revert statuses
        try:
            backup.status = 'completed'
            backup.save()
            
            app.status = 'error'
            app.save()
        except:
            pass
        
        return {
            'success': False,
            'backup_id': backup_id,
            'error': str(e)
        }


@shared_task(bind=True, max_retries=2)
def delete_backup_task(self, backup_id: int):
    """
    Delete a backup file from Proxmox storage and database.
    
    Args:
        backup_id: Backup ID to delete
        
    Returns:
        Dictionary with deletion status
    """
    try:
        # Get backup
        try:
            backup = Backup.objects.select_related(
                'application',
                'application__host'
            ).get(id=backup_id)
        except Backup.DoesNotExist:
            logger.error(f"Backup {backup_id} not found")
            return {
                'success': False,
                'error': f'Backup {backup_id} not found'
            }
        
        app = backup.application
        
        logger.info(
            f"Deleting backup {backup.file_name} for app {app.name} "
            f"(backup_id={backup_id})"
        )
        
        # Update status
        backup.status = 'deleting'
        backup.save()
        
        # Initialize Proxmox service
        proxmox = ProxmoxService(host_id=app.host.id)
        
        # Delete the backup file from storage
        try:
            proxmox.delete_backup_file(
                node_name=app.node,
                storage=backup.storage_name,
                backup_file=backup.file_name
            )
        except ProxmoxError as e:
            # If file doesn't exist, that's okay - we still want to delete the record
            if 'not found' not in str(e).lower() and 'does not exist' not in str(e).lower():
                raise
            logger.warning(f"Backup file not found in storage, will delete record anyway")
        
        # Delete the database record
        backup.delete()
        
        logger.info(f"Backup {backup_id} deleted successfully")
        
        return {
            'success': True,
            'backup_id': backup_id,
            'message': 'Backup deleted successfully'
        }
        
    except ProxmoxError as e:
        logger.error(f"Proxmox error during backup deletion: {e}")
        
        # Revert status
        try:
            backup.status = 'completed'
            backup.save()
        except:
            pass
        
        # Retry on certain errors
        if 'timeout' in str(e).lower() or 'connection' in str(e).lower():
            raise self.retry(exc=e, countdown=30)
        
        return {
            'success': False,
            'backup_id': backup_id,
            'error': str(e)
        }
        
    except Exception as e:
        logger.exception(f"Unexpected error during backup deletion: {e}")
        
        # Revert status
        try:
            backup.status = 'completed'
            backup.save()
        except:
            pass
        
        return {
            'success': False,
            'backup_id': backup_id,
            'error': str(e)
        }
