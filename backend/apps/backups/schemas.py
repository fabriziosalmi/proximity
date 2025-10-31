"""
Pydantic schemas for Backup API.
"""

from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator


class BackupSchema(BaseModel):
    """Schema for backup responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: str = Field(alias="application")
    file_name: str
    storage_name: str
    size: Optional[int] = None
    size_mb: Optional[float] = None
    size_gb: Optional[float] = None
    backup_type: str
    compression: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    is_completed: bool
    is_in_progress: bool

    @field_validator("application_id", mode="before")
    @classmethod
    def convert_application_to_id(cls, v: Any) -> str:
        """Convert Application object to its ID string."""
        if v is None:
            return None
        # If it's already a string, return as-is
        if isinstance(v, str):
            return v
        # If it's an object with an 'id' attribute, extract the ID
        if hasattr(v, "id"):
            return str(v.id)
        # Otherwise return the string representation
        return str(v)


class BackupListSchema(BaseModel):
    """Schema for list of backups."""

    backups: list[BackupSchema]
    total: int


class BackupCreateRequest(BaseModel):
    """Request schema for creating a backup."""

    backup_type: str = Field(
        default="snapshot", description="Backup mode: snapshot (fastest), suspend, or stop"
    )
    compression: str = Field(
        default="zstd", description="Compression algorithm: zstd, gzip, or lzo"
    )


class BackupCreateResponse(BaseModel):
    """Response schema for backup creation."""

    id: int
    status: str
    message: str


class BackupRestoreResponse(BaseModel):
    """Response schema for backup restore operation."""

    backup_id: int
    application_id: str
    status: str
    message: str


class BackupDeleteResponse(BaseModel):
    """Response schema for backup deletion."""

    backup_id: int
    status: str
    message: str


class BackupStatsSchema(BaseModel):
    """Schema for backup statistics."""

    total_backups: int
    completed_backups: int
    failed_backups: int
    in_progress_backups: int
    total_size_gb: float
    average_size_mb: float
