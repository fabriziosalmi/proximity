"""
Django Management Command: make_admin

Sets a user as staff and optionally as superuser to grant admin access.

Usage:
    # Set user as staff only
    python manage.py make_admin <username>

    # Set user as both staff and superuser
    python manage.py make_admin <username> --superuser

    # Docker usage
    docker-compose exec backend python manage.py make_admin <username> --superuser
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Sets a user as staff and optionally as superuser"

    def add_arguments(self, parser):
        """Add command-line arguments."""
        parser.add_argument(
            "username",
            type=str,
            help="Username of the user to promote to staff",
        )
        parser.add_argument(
            "--superuser",
            action="store_true",
            help="Also set the user as superuser (full admin access)",
        )

    def handle(self, *args, **options):
        """
        Main command logic.

        Promotes a user to staff and optionally to superuser.
        """
        username = options["username"]
        is_superuser = options.get("superuser", False)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User with username "{username}" does not exist')

        # Update user permissions
        user.is_staff = True
        if is_superuser:
            user.is_superuser = True

        user.save()

        # Build success message
        permissions = ["staff"]
        if is_superuser:
            permissions.append("superuser")

        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"=" * 70}\n'
                f"✅ USER PROMOTED TO ADMIN\n"
                f'{"=" * 70}\n'
                f"Username: {user.username}\n"
                f"Email: {user.email}\n"
                f"Permissions granted: {', '.join(permissions)}\n"
                f'{"=" * 70}\n'
            )
        )
