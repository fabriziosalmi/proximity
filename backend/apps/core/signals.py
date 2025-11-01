"""
Core app signals for user management.

Automatically sets the first registered user as staff and superuser
to ease out the UX for initial setup.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def auto_make_first_user_admin(sender, instance, created, **kwargs):
    """
    Signal handler that automatically promotes the first registered user
    to staff and superuser when they are created.

    This ensures the first user has full admin access without requiring
    manual setup via management commands.
    """
    if created:  # Only process newly created users
        # Check if this is the first user (no other admin users exist)
        admin_count = User.objects.filter(is_superuser=True).count()

        if admin_count == 0:  # No admin users exist yet
            # Make this user staff and superuser
            instance.is_staff = True
            instance.is_superuser = True
            # Use update() to avoid triggering the signal again
            User.objects.filter(pk=instance.pk).update(
                is_staff=True, is_superuser=True
            )
