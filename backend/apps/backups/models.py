"""
Backup models - Application backup management
"""

from django.db import models
from apps.applications.models import Application


class Backup(models.Model):
    """
    Application backup record.
    Tracks the lifecycle of LXC container backups.
    """

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="backups",
        help_text="The application this backup belongs to",
    )

    # File information
    file_name = models.CharField(max_length=500, help_text="Backup filename on Proxmox storage")
    storage_name = models.CharField(
        max_length=100, default="local", help_text="Proxmox storage name where backup is stored"
    )
    size = models.BigIntegerField(null=True, blank=True, help_text="Backup size in bytes")

    # Backup metadata
    backup_type = models.CharField(
        max_length=50,
        default="snapshot",
        choices=[
            ("snapshot", "Snapshot"),
            ("suspend", "Suspend"),
            ("stop", "Stop"),
        ],
        help_text="Backup mode used",
    )
    compression = models.CharField(
        max_length=20,
        default="zstd",
        choices=[
            ("zstd", "Zstandard"),
            ("gzip", "Gzip"),
            ("lzo", "LZO"),
        ],
        help_text="Compression algorithm",
    )

    # Status tracking
    status = models.CharField(
        max_length=50,
        default="creating",
        db_index=True,
        choices=[
            ("creating", "Creating"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("restoring", "Restoring"),
            ("deleting", "Deleting"),
        ],
        help_text="Current backup status",
    )

    # Error tracking
    error_message = models.TextField(
        null=True, blank=True, help_text="Error message if backup failed"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True, db_index=True, help_text="When backup was initiated"
    )
    updated_at = models.DateTimeField(auto_now=True, help_text="Last status update")
    completed_at = models.DateTimeField(
        null=True, blank=True, help_text="When backup completed successfully"
    )

    class Meta:
        db_table = "backups"
        verbose_name = "Backup"
        verbose_name_plural = "Backups"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["application", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"{self.application.name} - {self.file_name} ({self.status})"

    @property
    def size_mb(self) -> float:
        """Get backup size in megabytes."""
        if self.size:
            return round(self.size / (1024 * 1024), 2)
        return 0.0

    @property
    def size_gb(self) -> float:
        """Get backup size in gigabytes."""
        if self.size:
            return round(self.size / (1024 * 1024 * 1024), 2)
        return 0.0

    @property
    def is_completed(self) -> bool:
        """Check if backup is completed and available for restore."""
        return self.status == "completed"

    @property
    def is_in_progress(self) -> bool:
        """Check if backup operation is in progress."""
        return self.status in ["creating", "restoring", "deleting"]
