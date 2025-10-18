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
