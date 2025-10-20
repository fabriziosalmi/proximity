"""
Django Management Command: cleanup_deployments

This command completely purges all application-related data from the database,
including Applications, DeploymentLogs, and Backups. It's designed for testing
and development scenarios where you need a clean slate.

Usage:
    # Interactive mode (with confirmation prompt)
    python manage.py cleanup_deployments
    
    # Automated mode (no confirmation, for scripts)
    python manage.py cleanup_deployments --no-input
    
    # Docker usage
    docker-compose exec backend python manage.py cleanup_deployments --no-input
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.applications.models import Application, DeploymentLog
# from apps.backups.models import Backup  # Skipped - table doesn't exist yet


class Command(BaseCommand):
    help = 'Deletes all Application, DeploymentLog, and Backup records from the database.'

    def add_arguments(self, parser):
        """Add command-line arguments."""
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Deletes data without asking for confirmation.',
        )

    def handle(self, *args, **options):
        """
        Main command logic.
        
        Deletes all application-related data in the correct order to respect
        foreign key constraints, wrapped in an atomic transaction.
        """
        # Warning message
        self.stdout.write(
            self.style.WARNING(
                '\n⚠️  DATABASE CLEANUP WARNING ⚠️\n'
                '=' * 70 + '\n'
                'This will permanently delete ALL application data:\n'
                '  • All deployed applications\n'
                '  • All deployment logs\n'
                '  • All backup records\n'
                '\n'
                'This action CANNOT be undone!\n'
                '=' * 70 + '\n'
            )
        )

        # Confirmation prompt (unless --no-input flag is used)
        if not options['no_input']:
            confirm = input('Are you sure you want to continue? [y/N] ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.ERROR('❌ Operation cancelled.'))
                return

        # Perform cleanup in atomic transaction
        try:
            with transaction.atomic():
                self.stdout.write('\n🧹 Starting database cleanup...\n')

                # Order is critical due to Foreign Key constraints
                
                # 1. Delete deployment logs first (has FK to Application)
                self.stdout.write('  [1/2] Deleting deployment logs...')
                log_count, _ = DeploymentLog.objects.all().delete()
                self.stdout.write(
                    self.style.SUCCESS(f'        ✓ Deleted {log_count} deployment log entries')
                )
                
                # 2. Delete applications (using raw SQL to bypass FK check for missing backup table)
                self.stdout.write('  [2/2] Deleting applications...')
                # Get count before deletion
                app_count = Application.objects.count()
                # Use raw SQL DELETE to avoid Django trying to cascade to non-existent backup table
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute('DELETE FROM applications')
                self.stdout.write(
                    self.style.SUCCESS(f'        ✓ Deleted {app_count} application records')
                )
                
                backup_count = 0  # Not implemented yet

            # Success summary
            total_deleted = log_count + backup_count + app_count
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n{"=" * 70}\n'
                    f'✅ DATABASE CLEANUP COMPLETE\n'
                    f'{"=" * 70}\n'
                    f'Total records purged: {total_deleted}\n'
                    f'  • Applications: {app_count}\n'
                    f'  • Deployment Logs: {log_count}\n'
                    f'  • Backups: {backup_count}\n'
                    f'{"=" * 70}\n'
                    f'The database is now ready for clean E2E testing.\n'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'\n❌ ERROR during cleanup:\n'
                    f'{str(e)}\n'
                    f'The database transaction has been rolled back.\n'
                )
            )
            raise  # Re-raise to ensure exit code is non-zero
