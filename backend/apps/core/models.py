"""
Core models - User extensions and system configuration
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Extended User model for Proximity 2.0.
    Inherits from Django's AbstractUser for authentication.
    """
    # Additional fields beyond Django's default User
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    preferred_theme = models.CharField(
        max_length=50, 
        default='rack_proximity',
        help_text='UI theme/skin preference'
    )
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.username


class SystemSettings(models.Model):
    """
    Global system settings and configuration.
    Singleton model - only one instance should exist.
    """
    # GitOps configuration
    git_repo_path = models.CharField(max_length=500, default='/data/git/proximity-state')
    git_auto_commit = models.BooleanField(default=True)

    # UI configuration
    default_theme = models.CharField(max_length=50, default='rack_proximity')
    enable_animations = models.BooleanField(default=True)

    # Feature flags
    enable_ai_agent = models.BooleanField(default=False)
    enable_community_chat = models.BooleanField(default=False)
    enable_multi_host = models.BooleanField(default=True)

    # Default Resource Settings for new deployments
    default_cpu_cores = models.IntegerField(
        default=2,
        help_text='Default number of CPU cores for new LXC containers'
    )
    default_memory_mb = models.IntegerField(
        default=2048,
        help_text='Default memory allocation in MB for new LXC containers'
    )
    default_disk_gb = models.IntegerField(
        default=20,
        help_text='Default disk size in GB for new LXC containers'
    )
    default_swap_mb = models.IntegerField(
        default=512,
        help_text='Default swap size in MB for new LXC containers'
    )

    # Default Network Settings
    default_subnet = models.CharField(
        max_length=50,
        default='10.0.0.0/24',
        help_text='Default subnet for container network (CIDR notation)'
    )
    default_gateway = models.GenericIPAddressField(
        protocol='IPv4',
        default='10.0.0.1',
        help_text='Default gateway IP address'
    )
    default_dns_primary = models.GenericIPAddressField(
        protocol='both',
        default='8.8.8.8',
        help_text='Primary DNS server'
    )
    default_dns_secondary = models.GenericIPAddressField(
        protocol='both',
        default='8.8.4.4',
        null=True,
        blank=True,
        help_text='Secondary DNS server (optional)'
    )
    default_bridge = models.CharField(
        max_length=50,
        default='vmbr0',
        help_text='Default network bridge for containers'
    )

    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'system_settings'
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'
    
    def __str__(self):
        return "System Settings"
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)."""
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        """Load or create the singleton instance."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
