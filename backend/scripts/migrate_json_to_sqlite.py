#!/usr/bin/env python3
"""
Migration Script: JSON to SQLite
=================================

This script migrates application state from data/apps.json to the SQLite database.

It is idempotent and can be run multiple times safely:
- Creates new apps that don't exist in the database
- Updates existing apps with data from JSON
- Skips apps that are already in sync

Usage:
    python scripts/migrate_json_to_sqlite.py

Author: Proximity Team
Date: October 2025
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from models.database import SessionLocal, App as DBApp
from models.schemas import AppStatus
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_json_datetime(dt_str: str) -> datetime:
    """Parse datetime string from JSON with multiple format support"""
    if not dt_str:
        return datetime.utcnow()

    # Try different datetime formats
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO format with microseconds
        "%Y-%m-%dT%H:%M:%S",     # ISO format without microseconds
        "%Y-%m-%d %H:%M:%S.%f",  # Standard format with microseconds
        "%Y-%m-%d %H:%M:%S",     # Standard format without microseconds
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue

    # If all formats fail, return current time
    logger.warning(f"Could not parse datetime '{dt_str}', using current time")
    return datetime.utcnow()


def migrate_apps(db: Session, json_file_path: Path) -> dict:
    """
    Migrate apps from JSON file to SQLite database.

    Args:
        db: SQLAlchemy database session
        json_file_path: Path to apps.json file

    Returns:
        dict: Migration statistics
    """
    stats = {
        'total_in_json': 0,
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }

    # Check if JSON file exists
    if not json_file_path.exists():
        logger.warning(f"JSON file not found: {json_file_path}")
        logger.info("No apps to migrate. This is normal for a fresh installation.")
        return stats

    # Load JSON data
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
            apps_data = data.get('apps', [])
            stats['total_in_json'] = len(apps_data)

        logger.info(f"Found {len(apps_data)} apps in JSON file")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file: {e}")
        return stats
    except Exception as e:
        logger.error(f"Failed to read JSON file: {e}")
        return stats

    # Migrate each app
    for app_data in apps_data:
        try:
            app_id = app_data.get('id')
            if not app_id:
                logger.warning(f"Skipping app without ID: {app_data.get('name', 'Unknown')}")
                stats['skipped'] += 1
                continue

            # Check if app already exists in database
            existing_app = db.query(DBApp).filter(DBApp.id == app_id).first()

            # Parse datetime fields
            created_at = parse_json_datetime(app_data.get('created_at', ''))
            updated_at = parse_json_datetime(app_data.get('updated_at', ''))

            # Parse status
            status_str = app_data.get('status', 'unknown')
            if isinstance(status_str, str):
                # Handle both string values and AppStatus enum values
                status = status_str
            else:
                status = str(status_str)

            if existing_app:
                # Update existing app
                existing_app.catalog_id = app_data.get('catalog_id', existing_app.catalog_id)
                existing_app.name = app_data.get('name', existing_app.name)
                existing_app.hostname = app_data.get('hostname', existing_app.hostname)
                existing_app.status = status
                existing_app.url = app_data.get('url')
                existing_app.lxc_id = app_data.get('lxc_id', existing_app.lxc_id)
                existing_app.node = app_data.get('node', existing_app.node)
                existing_app.config = app_data.get('config', {})
                existing_app.ports = app_data.get('ports', {})
                existing_app.volumes = app_data.get('volumes', [])
                existing_app.environment = app_data.get('environment', {})
                existing_app.updated_at = updated_at

                logger.info(f"  ✓ Updated: {existing_app.name} (ID: {app_id})")
                stats['updated'] += 1
            else:
                # Create new app
                new_app = DBApp(
                    id=app_id,
                    catalog_id=app_data.get('catalog_id', ''),
                    name=app_data.get('name', 'Unknown'),
                    hostname=app_data.get('hostname', ''),
                    status=status,
                    url=app_data.get('url'),
                    lxc_id=app_data.get('lxc_id', 0),
                    node=app_data.get('node', ''),
                    created_at=created_at,
                    updated_at=updated_at,
                    config=app_data.get('config', {}),
                    ports=app_data.get('ports', {}),
                    volumes=app_data.get('volumes', []),
                    environment=app_data.get('environment', {}),
                    owner_id=None  # Will be set by user when they claim the app
                )
                db.add(new_app)

                logger.info(f"  ✓ Created: {new_app.name} (ID: {app_id})")
                stats['created'] += 1

        except Exception as e:
            logger.error(f"  ✗ Failed to migrate app {app_data.get('id', 'unknown')}: {e}")
            stats['errors'] += 1
            continue

    # Commit all changes
    try:
        db.commit()
        logger.info(f"✓ Successfully committed all changes to database")
    except Exception as e:
        logger.error(f"✗ Failed to commit changes: {e}")
        db.rollback()
        raise

    return stats


def main():
    """Main migration function"""
    logger.info("=" * 60)
    logger.info("PROXIMITY: JSON to SQLite Migration")
    logger.info("=" * 60)

    # Determine paths
    backend_dir = Path(__file__).parent.parent
    json_file = backend_dir / "data" / "apps.json"

    logger.info(f"Backend directory: {backend_dir}")
    logger.info(f"JSON file: {json_file}")

    # Create database session
    db = SessionLocal()

    try:
        # Run migration
        logger.info("\nStarting migration...")
        logger.info("-" * 60)

        stats = migrate_apps(db, json_file)

        # Print summary
        logger.info("-" * 60)
        logger.info("MIGRATION SUMMARY")
        logger.info("-" * 60)
        logger.info(f"Total apps in JSON:  {stats['total_in_json']}")
        logger.info(f"Created:             {stats['created']}")
        logger.info(f"Updated:             {stats['updated']}")
        logger.info(f"Skipped:             {stats['skipped']}")
        logger.info(f"Errors:              {stats['errors']}")
        logger.info("-" * 60)

        if stats['errors'] > 0:
            logger.warning(f"⚠️  Migration completed with {stats['errors']} errors")
            return 1
        else:
            logger.info("✅ Migration completed successfully!")

            # Backup JSON file
            if json_file.exists() and (stats['created'] > 0 or stats['updated'] > 0):
                backup_file = json_file.with_suffix('.json.backup')
                import shutil
                shutil.copy2(json_file, backup_file)
                logger.info(f"📦 JSON file backed up to: {backup_file}")
                logger.info("   You can safely delete apps.json after verifying the migration")

            return 0

    except Exception as e:
        logger.error(f"✗ Migration failed: {e}", exc_info=True)
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
