"""
Proxmox models - Host configurations and node management
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import User
from apps.core.fields import EncryptedCharField


class ProxmoxHost(models.Model):
    """
    Proxmox host configuration.
    Supports multi-host management architecture.
    """
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text='Friendly name for this Proxmox host'
    )
    host = models.CharField(
        max_length=255,
        help_text='Hostname or IP address'
    )
    port = models.IntegerField(
        default=8006,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
        help_text='Proxmox API port'
    )
    ssh_port = models.IntegerField(
        default=22,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
        help_text='SSH port for pct exec commands'
    )
    user = models.CharField(
        max_length=100,
        default='root@pam',
        help_text='Proxmox user (e.g., root@pam)'
    )
    password = EncryptedCharField(
        max_length=500,
        help_text='Encrypted password for Proxmox API'
    )
    ssh_key_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text='Path to SSH private key for key-based authentication (optional)'
    )
    verify_ssl = models.BooleanField(
        default=False,
        help_text='Verify SSL certificate'
    )
    
    # Status and metadata
    is_active = models.BooleanField(
        default=True,
        help_text='Enable/disable this host'
    )
    is_default = models.BooleanField(
        default=False,
        help_text='Use as default target for deployments'
    )
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last successful connection'
    )
    
    # Resource tracking
    total_cpu = models.IntegerField(null=True, blank=True)
    total_memory = models.BigIntegerField(null=True, blank=True)
    total_storage = models.BigIntegerField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='proxmox_hosts'
    )
    
    class Meta:
        db_table = 'proxmox_hosts'
        verbose_name = 'Proxmox Host'
        verbose_name_plural = 'Proxmox Hosts'
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.host})"
    
    def save(self, *args, **kwargs):
        """Ensure only one default host."""
        if self.is_default:
            ProxmoxHost.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class ProxmoxNode(models.Model):
    """
    Proxmox node information (cached from API).
    """
    host = models.ForeignKey(
        ProxmoxHost,
        on_delete=models.CASCADE,
        related_name='nodes'
    )
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default='unknown')
    node_type = models.CharField(max_length=50, default='node')
    
    # Resource information
    cpu_count = models.IntegerField(null=True, blank=True)
    cpu_usage = models.FloatField(null=True, blank=True)
    memory_total = models.BigIntegerField(null=True, blank=True)
    memory_used = models.BigIntegerField(null=True, blank=True)
    storage_total = models.BigIntegerField(null=True, blank=True)
    storage_used = models.BigIntegerField(null=True, blank=True)
    uptime = models.BigIntegerField(null=True, blank=True)
    
    # Network
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Metadata
    pve_version = models.CharField(max_length=50, null=True, blank=True)
    lxc_count = models.IntegerField(default=0)
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'proxmox_nodes'
        verbose_name = 'Proxmox Node'
        verbose_name_plural = 'Proxmox Nodes'
        unique_together = [['host', 'name']]
    
    def __str__(self):
        return f"{self.host.name}:{self.name}"
