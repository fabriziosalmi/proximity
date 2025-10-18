"""
Backup models - Application backup management
"""
from django.db import models
from apps.applications.models import Application


class Backup(models.Model):
    """
    Application backup record.
    """
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='backups'
    )
    filename = models.CharField(max_length=500)
    storage_name = models.CharField(max_length=100, default='local')
    size_bytes = models.BigIntegerField(null=True, blank=True)
    backup_type = models.CharField(
        max_length=50,
        default='vzdump',
        choices=[
            ('vzdump', 'VZDump'),
            ('snapshot', 'Snapshot'),
        ]
    )
    status = models.CharField(
        max_length=50,
        default='creating',
        db_index=True,
        choices=[
            ('creating', 'Creating'),
            ('available', 'Available'),
            ('failed', 'Failed'),
            ('restoring', 'Restoring'),
        ]
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'backups'
        verbose_name = 'Backup'
        verbose_name_plural = 'Backups'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.application.name} - {self.filename}"
