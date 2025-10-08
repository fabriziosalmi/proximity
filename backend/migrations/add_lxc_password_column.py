#!/usr/bin/env python3
"""
Database migration: Add lxc_root_password column to apps table

This migration adds support for storing encrypted root passwords for LXC containers.
The column is nullable to maintain backward compatibility with existing deployments.

Run this migration with:
    python backend/migrations/add_lxc_password_column.py

Or use the migrate_db.py utility:
    python backend/migrate_db.py add_lxc_password_column
"""

import sys
import logging
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from models.database import engine

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def migrate():
    """Add lxc_root_password column to apps table"""
    
    logger.info("Starting migration: add_lxc_password_column")
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('apps') 
                WHERE name='lxc_root_password'
            """))
            
            row = result.fetchone()
            if row and row[0] > 0:
                logger.info("✓ Column 'lxc_root_password' already exists in 'apps' table")
                return True
            
            # Add the column
            logger.info("Adding 'lxc_root_password' column to 'apps' table...")
            conn.execute(text("""
                ALTER TABLE apps 
                ADD COLUMN lxc_root_password VARCHAR(500)
            """))
            conn.commit()
            
            logger.info("✓ Successfully added 'lxc_root_password' column")
            logger.info("✓ Migration completed successfully")
            
            # Show table info
            result = conn.execute(text("SELECT name, type FROM pragma_table_info('apps')"))
            columns = result.fetchall()
            logger.info(f"✓ Table 'apps' now has {len(columns)} columns")
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Migration failed: {e}")
        return False


def rollback():
    """Remove lxc_root_password column from apps table"""
    
    logger.info("Starting rollback: add_lxc_password_column")
    
    try:
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('apps') 
                WHERE name='lxc_root_password'
            """))
            
            row = result.fetchone()
            if not row or row[0] == 0:
                logger.info("✓ Column 'lxc_root_password' does not exist in 'apps' table")
                return True
            
            # SQLite doesn't support DROP COLUMN directly, need to recreate table
            logger.warning("⚠ SQLite doesn't support DROP COLUMN - manual intervention required")
            logger.warning("To rollback, you would need to:")
            logger.warning("1. Create a new table without the lxc_root_password column")
            logger.warning("2. Copy data from old table to new table")
            logger.warning("3. Drop old table and rename new table")
            logger.warning("Or restore from a backup taken before the migration")
            
            return False
            
    except Exception as e:
        logger.error(f"✗ Rollback failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate database to add lxc_root_password column')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback()
    else:
        success = migrate()
    
    sys.exit(0 if success else 1)
