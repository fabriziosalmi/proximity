"""
Backup API endpoints.
Handles backup creation, listing, restoration, and deletion.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from models.database import get_db, User, App, Backup as BackupModel
from models.schemas import (
    Backup, BackupCreate, BackupList, APIResponse, ErrorResponse,
    BackupStatus, TokenData
)
from services.backup_service import BackupService
from api.middleware.auth import get_current_user


router = APIRouter()


def get_app_and_check_ownership(app_id: str, db: Session, current_user: TokenData) -> App:
    """
    Helper function to get app and verify ownership.

    Args:
        app_id: Application ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        App object

    Raises:
        HTTPException: If app not found or user doesn't have access
    """
    app = db.query(App).filter(App.id == app_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"App {app_id} not found"
        )

    # Check ownership (admins can access all)
    if current_user.role != "admin" and app.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this app"
        )

    return app


@router.post("/apps/{app_id}/backups", status_code=status.HTTP_202_ACCEPTED)
async def create_backup(
    app_id: str,
    backup_request: BackupCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Create a backup for an application.

    This is an asynchronous operation that returns immediately with status 202.
    The backup will be created in the background.

    Args:
        app_id: Application ID
        backup_request: Backup creation parameters
        db: Database session
        current_user: Current authenticated user

    Returns:
        Backup creation response with backup ID and status

    Raises:
        HTTPException: If app not found, user lacks permission, or backup creation fails
    """
    # Verify app exists and user has access
    app = get_app_and_check_ownership(app_id, db, current_user)

    try:
        # Create backup service
        backup_service = BackupService(db)

        # Create backup
        backup = await backup_service.create_backup(
            app_id=app_id,
            storage=backup_request.storage or "local",
            compress=backup_request.compress or "zstd",
            mode=backup_request.mode or "snapshot"
        )

        return {
            "backup_id": backup.id,
            "app_id": backup.app_id,
            "filename": backup.filename,
            "status": backup.status,
            "message": "Backup creation started. Check status for completion."
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backup: {str(e)}"
        )


@router.get("/apps/{app_id}/backups", response_model=BackupList)
async def list_backups(
    app_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    List all backups for an application.

    Args:
        app_id: Application ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of backups for the app

    Raises:
        HTTPException: If app not found or user lacks permission
    """
    # Verify app exists and user has access
    app = get_app_and_check_ownership(app_id, db, current_user)

    try:
        backup_service = BackupService(db)
        backups = await backup_service.list_backups_for_app(app_id)

        return {
            "backups": [Backup.model_validate(b) for b in backups],
            "total": len(backups)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}"
        )


@router.get("/apps/{app_id}/backups/{backup_id}", response_model=Backup)
async def get_backup(
    app_id: str,
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get details of a specific backup.

    Args:
        app_id: Application ID
        backup_id: Backup ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Backup details

    Raises:
        HTTPException: If app/backup not found or user lacks permission
    """
    # Verify app exists and user has access
    app = get_app_and_check_ownership(app_id, db, current_user)

    try:
        backup_service = BackupService(db)
        backup = await backup_service.get_backup(backup_id)

        # Verify backup belongs to this app
        if backup.app_id != app_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found for this app"
            )

        return Backup.model_validate(backup)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backup: {str(e)}"
        )


@router.post("/apps/{app_id}/backups/{backup_id}/restore", status_code=status.HTTP_202_ACCEPTED)
async def restore_backup(
    app_id: str,
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Restore an application from a backup.

    This is an asynchronous operation that:
    1. Stops the container
    2. Restores from backup
    3. Starts the container

    Args:
        app_id: Application ID
        backup_id: Backup ID to restore from
        db: Database session
        current_user: Current authenticated user

    Returns:
        Restore operation status

    Raises:
        HTTPException: If backup not available, app not found, or restore fails
    """
    # Verify app exists and user has access
    app = get_app_and_check_ownership(app_id, db, current_user)

    try:
        backup_service = BackupService(db)

        # Get backup and verify it belongs to this app
        backup = await backup_service.get_backup(backup_id)
        if backup.app_id != app_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found for this app"
            )

        # Check backup is available
        if backup.status != "available":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Backup is not available for restore (status: {backup.status})"
            )

        # Restore from backup
        result = await backup_service.restore_from_backup(backup_id)

        return {
            "success": True,
            "message": "Restore operation started",
            "backup_id": backup_id,
            "app_id": app_id
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore backup: {str(e)}"
        )


@router.delete("/apps/{app_id}/backups/{backup_id}")
async def delete_backup(
    app_id: str,
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Delete a backup.

    This permanently removes the backup file from Proxmox storage
    and deletes the backup record from the database.

    Args:
        app_id: Application ID
        backup_id: Backup ID to delete
        db: Database session
        current_user: Current authenticated user

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If backup not found or deletion fails
    """
    # Verify app exists and user has access
    app = get_app_and_check_ownership(app_id, db, current_user)

    try:
        backup_service = BackupService(db)

        # Get backup and verify it belongs to this app
        backup = await backup_service.get_backup(backup_id)
        if backup.app_id != app_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found for this app"
            )

        # Delete backup
        result = await backup_service.delete_backup(backup_id)

        return {
            "success": True,
            "message": "Backup deleted successfully",
            "backup_id": backup_id
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete backup: {str(e)}"
        )
