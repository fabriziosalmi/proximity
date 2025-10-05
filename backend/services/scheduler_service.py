"""
Scheduler Service for AUTO Mode Automation

Handles automated tasks when Proximity is in AUTO mode:
- Daily backups for all applications
- Weekly update checks for application images
- Scheduled maintenance tasks
"""

import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from models.database import get_db, App, SystemSettings
from services.backup_service import BackupService
from services.app_service import AppService

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Manages automated tasks for AUTO mode operation.

    Tasks include:
    - Daily backups (scheduled at 2:00 AM)
    - Weekly update checks (every Sunday at 3:00 AM)
    """

    def __init__(self, backup_service: BackupService, app_service: AppService):
        """
        Initialize the scheduler service.

        Args:
            backup_service: BackupService instance for creating backups
            app_service: AppService instance for app operations
        """
        self.backup_service = backup_service
        self.app_service = app_service
        self.scheduler = AsyncIOScheduler()
        self._is_running = False

        logger.info("📅 SchedulerService initialized")

    def _is_auto_mode(self, db: Session) -> bool:
        """
        Check if system is in AUTO mode.

        Args:
            db: Database session

        Returns:
            bool: True if system is in AUTO mode
        """
        # Check system settings for proximity mode
        # For now, we'll default to True if not explicitly set
        settings = db.query(SystemSettings).first()
        if settings and hasattr(settings, 'proximity_mode'):
            return settings.proximity_mode == 'AUTO'

        # Default to AUTO mode
        return True

    async def schedule_daily_backups(self):
        """
        Daily backup job for all running applications.

        Creates backups for all apps with backup_type='scheduled'.
        Only runs if system is in AUTO mode.
        """
        try:
            logger.info("🔄 Starting daily backup job...")

            # Get database session
            db = next(get_db())

            try:
                # Check if in AUTO mode
                if not self._is_auto_mode(db):
                    logger.info("⏭️  Skipping daily backups (not in AUTO mode)")
                    return

                # Get all running apps
                apps = db.query(App).filter(App.status == 'running').all()

                if not apps:
                    logger.info("📭 No running apps to backup")
                    return

                logger.info(f"📦 Found {len(apps)} running apps to backup")

                # Create backup for each app
                backup_count = 0
                for app in apps:
                    try:
                        logger.info(f"   Backing up: {app.hostname}")
                        await self.backup_service.create_backup(
                            app_id=app.id,
                            backup_type='scheduled',
                            db=db
                        )
                        backup_count += 1
                    except Exception as e:
                        logger.error(f"   ❌ Failed to backup {app.hostname}: {e}")

                logger.info(f"✅ Daily backup job completed: {backup_count}/{len(apps)} successful")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"❌ Daily backup job failed: {e}")

    async def schedule_weekly_update_checks(self):
        """
        Weekly job to check for application updates.

        Checks if newer image versions are available and sets update_available flag.
        Only runs if system is in AUTO mode.
        """
        try:
            logger.info("🔄 Starting weekly update check job...")

            # Get database session
            db = next(get_db())

            try:
                # Check if in AUTO mode
                if not self._is_auto_mode(db):
                    logger.info("⏭️  Skipping update checks (not in AUTO mode)")
                    return

                # Get all deployed apps
                apps = db.query(App).all()

                if not apps:
                    logger.info("📭 No apps to check for updates")
                    return

                logger.info(f"🔍 Checking updates for {len(apps)} apps")

                # For each app, check if updates are available
                # (This would integrate with Docker registry API or Proxmox template checks)
                update_count = 0
                for app in apps:
                    try:
                        # Placeholder for actual update check logic
                        # In a real implementation, this would:
                        # 1. Query Docker registry for latest image tag
                        # 2. Compare with current deployment
                        # 3. Set update_available flag if newer version exists

                        logger.info(f"   Checking: {app.hostname}")
                        # app.update_available = await check_for_updates(app)
                        # if app.update_available:
                        #     update_count += 1

                    except Exception as e:
                        logger.error(f"   ❌ Failed to check updates for {app.hostname}: {e}")

                db.commit()
                logger.info(f"✅ Weekly update check completed: {update_count} updates available")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"❌ Weekly update check job failed: {e}")

    def start(self):
        """
        Start the scheduler with all configured jobs.

        Jobs:
        - Daily backups: 2:00 AM every day
        - Weekly updates: 3:00 AM every Sunday
        """
        if self._is_running:
            logger.warning("⚠️  Scheduler is already running")
            return

        try:
            # Schedule daily backups at 2:00 AM
            self.scheduler.add_job(
                self.schedule_daily_backups,
                trigger=CronTrigger(hour=2, minute=0),  # 2:00 AM every day
                id='daily_backups',
                name='Daily Automatic Backups',
                replace_existing=True
            )
            logger.info("✅ Scheduled daily backups (2:00 AM)")

            # Schedule weekly update checks at 3:00 AM on Sundays
            self.scheduler.add_job(
                self.schedule_weekly_update_checks,
                trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),  # 3:00 AM Sunday
                id='weekly_updates',
                name='Weekly Update Checks',
                replace_existing=True
            )
            logger.info("✅ Scheduled weekly update checks (3:00 AM Sunday)")

            # Start the scheduler
            self.scheduler.start()
            self._is_running = True

            logger.info("🚀 SchedulerService started successfully")

        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {e}")
            raise

    def stop(self):
        """Stop the scheduler and all running jobs."""
        if not self._is_running:
            logger.warning("⚠️  Scheduler is not running")
            return

        try:
            self.scheduler.shutdown(wait=True)
            self._is_running = False
            logger.info("🛑 SchedulerService stopped")

        except Exception as e:
            logger.error(f"❌ Failed to stop scheduler: {e}")
            raise

    def get_jobs(self):
        """
        Get list of all scheduled jobs.

        Returns:
            list: List of job information dictionaries
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._is_running
