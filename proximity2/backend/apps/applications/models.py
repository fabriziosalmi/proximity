"""
Application models - Deployed apps and configurations
"""
from django.db import models
from apps.core.models import User
from apps.proxmox.models import ProxmoxHost


class Application(models.Model):
    """
    Deployed application instance.
    """
    # Identity
    id = models.CharField(max_length=255, primary_key=True)
    catalog_id = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=255)
    hostname = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Status
    status = models.CharField(
        max_length=50,
        default='deploying',
        db_index=True,
        choices=[
            ('deploying', 'Deploying'),
            ('cloning', 'Cloning'),
            ('running', 'Running'),
            ('stopped', 'Stopped'),
            ('error', 'Error'),
            ('updating', 'Updating'),
            ('removing', 'Removing'),
        ]
    )
    
    # URLs
    url = models.URLField(max_length=512, null=True, blank=True)
    iframe_url = models.URLField(max_length=512, null=True, blank=True)
    
    # Ports
    public_port = models.IntegerField(null=True, blank=True, unique=True, db_index=True)
    internal_port = models.IntegerField(null=True, blank=True, unique=True, db_index=True)
    
    # LXC Configuration
    lxc_id = models.IntegerField(unique=True, db_index=True, null=True, blank=True)
    lxc_root_password = models.CharField(max_length=500, null=True, blank=True)
    
    # Proxmox references
    host = models.ForeignKey(
        ProxmoxHost,
        on_delete=models.PROTECT,
        related_name='applications'
    )
    node = models.CharField(max_length=100, db_index=True)
    
    # Configuration (JSON fields)
    config = models.JSONField(default=dict)
    ports = models.JSONField(default=dict)
    volumes = models.JSONField(default=list)
    environment = models.JSONField(default=dict)
    
    # Ownership
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='applications',
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'applications'
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.status})"


class DeploymentLog(models.Model):
    """
    Deployment event log for audit trail.
    """
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='deployment_logs'
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    level = models.CharField(
        max_length=20,
        choices=[
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('error', 'Error'),
        ]
    )
    message = models.TextField()
    step = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        db_table = 'deployment_logs'
        verbose_name = 'Deployment Log'
        verbose_name_plural = 'Deployment Logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.application.name} - {self.level} - {self.timestamp}"
