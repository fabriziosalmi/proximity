"""
Backup API endpoints - Create, list, restore, and delete application backups.

All endpoints are nested under /api/apps/{app_id}/backups
"""

import logging
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Avg, Count, Q
from ninja import Router
from ninja.errors import HttpError

# TODO: Implement proper authentication
# from apps.core.auth import AuthBearer
from apps.applications.models import Application
from apps.backups.models import Backup
from apps.backups.schemas import (
    BackupSchema,
    BackupListSchema,
    BackupCreateRequest,
    BackupCreateResponse,
    BackupRestoreResponse,
    BackupDeleteResponse,
    BackupStatsSchema,
)
from apps.backups.tasks import create_backup_task, restore_backup_task, delete_backup_task

logger = logging.getLogger(__name__)
router = Router()  # TODO: Add auth=AuthBearer() when implemented


@router.get(
    "/apps/{app_id}/backups",
    response=BackupListSchema,
    auth=None,  # TODO: Add proper authentication once AuthBearer is implemented
    summary="List all backups for an application",
    description="Get a list of all backups (completed and in-progress) for a specific application.",
)
def list_app_backups(request, app_id: str):
    """
    List all backups for an application.

    Returns backups ordered by creation date (newest first).
    """
    # Check authentication
    if not request.user or not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")

    # Verify application exists and user has permission
    app = get_object_or_404(Application.objects.filter(owner=request.user), id=app_id)

    # Get all backups for this application
    backups = Backup.objects.filter(application=app).order_by("-created_at")

    # Convert to schema - prepare data with application_id instead of application object
    backup_schemas = []
    for backup in backups:
        # Get backup data and replace application ForeignKey with its ID
        backup_data = BackupSchema.model_validate(backup)
        backup_schemas.append(backup_data)

    return BackupListSchema(backups=backup_schemas, total=len(backup_schemas))


@router.post(
    "/apps/{app_id}/backups",
    response={202: BackupCreateResponse},
    auth=None,  # TODO: Add proper authentication once AuthBearer is implemented
    summary="Create a new backup",
    description="Initiate a backup operation for an application. Returns 202 Accepted immediately.",
)
def create_app_backup(request, app_id: str, payload: BackupCreateRequest = None):
    """
    Create a new backup for an application.

    The backup operation is asynchronous and will run in the background.
    Use GET /apps/{app_id}/backups/{backup_id} to check status.
    """
    # Check authentication
    if not request.user or not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")

    # Verify application exists and user has permission
    app = get_object_or_404(Application.objects.filter(owner=request.user), id=app_id)

    # Check if application is in a state that can be backed up
    if app.status in ["removing", "error"]:
        raise HttpError(400, f"Cannot backup application in '{app.status}' state")

    # Check if there's already a backup in progress
    in_progress = Backup.objects.filter(
        application=app, status__in=["creating", "restoring"]
    ).exists()

    if in_progress:
        raise HttpError(
            409, "A backup or restore operation is already in progress for this application"
        )

    # Get backup parameters
    backup_type = "snapshot"
    compression = "zstd"

    if payload:
        backup_type = payload.backup_type
        compression = payload.compression

    logger.info(f"Creating backup for app {app.name} (type={backup_type}, compress={compression})")

    # Create backup record
    backup = Backup.objects.create(
        application=app,
        file_name="",  # Will be filled by task
        storage_name="local",
        backup_type=backup_type,
        compression=compression,
        status="creating",
    )

    # Trigger async backup task
    create_backup_task.delay(
        application_id=app_id, backup_type=backup_type, compression=compression
    )

    return 202, BackupCreateResponse(
        id=backup.id, status="creating", message=f"Backup creation started for {app.name}"
    )


@router.get(
    "/apps/{app_id}/backups/stats",
    response=BackupStatsSchema,
    auth=None,  # TODO: Add proper authentication once AuthBearer is implemented
    summary="Get backup statistics",
    description="Get statistics about backups for an application.",
)
def get_backup_stats(request, app_id: str):
    """Get statistics about backups for an application."""
    # Check authentication
    if not request.user or not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")

    # Verify application exists and user has permission
    app = get_object_or_404(Application.objects.filter(owner=request.user), id=app_id)

    # Aggregate statistics
    stats = Backup.objects.filter(application=app).aggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status="completed")),
        failed=Count("id", filter=Q(status="failed")),
        in_progress=Count("id", filter=Q(status__in=["creating", "restoring", "deleting"])),
        total_size=Sum("size", filter=Q(status="completed")),
        avg_size=Avg("size", filter=Q(status="completed")),
    )

    # Convert sizes to GB/MB
    total_size_gb = (stats["total_size"] or 0) / (1024**3)
    avg_size_mb = (stats["avg_size"] or 0) / (1024**2)

    return BackupStatsSchema(
        total_backups=stats["total"] or 0,
        completed_backups=stats["completed"] or 0,
        failed_backups=stats["failed"] or 0,
        in_progress_backups=stats["in_progress"] or 0,
        total_size_gb=round(total_size_gb, 2),
        average_size_mb=round(avg_size_mb, 2),
    )


@router.get(
    "/apps/{app_id}/backups/{backup_id}",
    response=BackupSchema,
    auth=None,  # TODO: Add proper authentication once AuthBearer is implemented
    summary="Get backup details",
    description="Get detailed information about a specific backup.",
)
def get_backup_details(request, app_id: str, backup_id: int):
    """Get details of a specific backup."""
    # Check authentication
    if not request.user or not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")

    # Verify application and backup exist with proper permissions
    app = get_object_or_404(Application.objects.filter(owner=request.user), id=app_id)

    backup = get_object_or_404(Backup.objects.filter(application=app), id=backup_id)

    return BackupSchema.model_validate(backup)


@router.post(
    "/apps/{app_id}/backups/{backup_id}/restore",
    response={202: BackupRestoreResponse},
    auth=None,  # TODO: Add proper authentication once AuthBearer is implemented
    summary="Restore from backup",
    description="Restore an application from a backup. This is a DESTRUCTIVE operation. Returns 202 Accepted.",
)
def restore_from_backup(request, app_id: str, backup_id: int):
    """
    Restore an application from a backup.

    WARNING: This is a DESTRUCTIVE operation that will overwrite
    the current container state.
    """
    # Check authentication
    if not request.user or not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")

    # Verify application and backup exist with proper permissions
    app = get_object_or_404(Application.objects.filter(owner=request.user), id=app_id)

    backup = get_object_or_404(Backup.objects.filter(application=app), id=backup_id)

    # Check if backup is in a restorable state
    if backup.status != "completed":
        raise HttpError(
            400,
            f"Cannot restore from backup in '{backup.status}' state. Only completed backups can be restored.",
        )

    # Check if there's already an operation in progress
    in_progress = Backup.objects.filter(
        application=app, status__in=["creating", "restoring"]
    ).exists()

    if in_progress:
        raise HttpError(
            409, "A backup or restore operation is already in progress for this application"
        )

    logger.info(f"Initiating restore for app {app.name} from backup {backup.file_name}")

    # Trigger async restore task
    restore_backup_task.delay(backup_id=backup_id)

    return 202, BackupRestoreResponse(
        backup_id=backup_id,
        application_id=app_id,
        status="restoring",
        message=f"Restore operation started for {app.name} from {backup.file_name}",
    )


@router.delete(
    "/apps/{app_id}/backups/{backup_id}",
    response={202: BackupDeleteResponse},
    auth=None,  # TODO: Add proper authentication once AuthBearer is implemented
    summary="Delete a backup",
    description="Delete a backup file and its record. Returns 202 Accepted.",
)
def delete_backup(request, app_id: str, backup_id: int):
    """
    Delete a backup.

    This will delete both the backup file from Proxmox storage
    and the backup record from the database.
    """
    # Check authentication
    if not request.user or not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")

    # Verify application and backup exist with proper permissions
    app = get_object_or_404(Application.objects.filter(owner=request.user), id=app_id)

    backup = get_object_or_404(Backup.objects.filter(application=app), id=backup_id)

    # Check if backup is currently being used
    if backup.status in ["creating", "restoring", "deleting"]:
        raise HttpError(409, f"Cannot delete backup in '{backup.status}' state")

    logger.info(f"Deleting backup {backup.file_name} for app {app.name}")

    # Trigger async delete task
    delete_backup_task.delay(backup_id=backup_id)

    return 202, BackupDeleteResponse(
        backup_id=backup_id,
        status="deleting",
        message=f"Backup deletion started for {backup.file_name}",
    )
