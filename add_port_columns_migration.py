#!/usr/bin/env python3
"""
Database migration: Add public_port and internal_port columns to apps table

This migration adds the required port columns for the Platinum Edition
port-based access architecture introduced in v2.0.

Run this script once to update your database schema.
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from sqlalchemy import text
from models.database import engine


def run_migration():
    """Add public_port and internal_port columns to apps table"""

    print("🔧 Starting database migration: add port columns to apps table")
    print()

    # Create connection
    with engine.connect() as connection:
        # Start transaction
        trans = connection.begin()

        try:
            # Check if columns already exist
            result = connection.execute(text("PRAGMA table_info(apps)"))
            columns = [row[1] for row in result.fetchall()]

            if "public_port" in columns and "internal_port" in columns:
                print("✓ Columns already exist - migration already applied")
                print()
                return

            # Add public_port column
            if "public_port" not in columns:
                print("  Adding column: public_port (Integer, nullable, unique, index)")
                connection.execute(text("ALTER TABLE apps ADD COLUMN public_port INTEGER"))
                # Note: SQLite doesn't support adding UNIQUE constraints to existing tables
                # in ALTER TABLE, so we'll add a unique index instead
                connection.execute(
                    text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS ix_apps_public_port ON apps(public_port)"
                    )
                )
                print("  ✓ public_port column added")

            # Add internal_port column
            if "internal_port" not in columns:
                print("  Adding column: internal_port (Integer, nullable, unique, index)")
                connection.execute(text("ALTER TABLE apps ADD COLUMN internal_port INTEGER"))
                connection.execute(
                    text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS ix_apps_internal_port ON apps(internal_port)"
                    )
                )
                print("  ✓ internal_port column added")

            # Commit transaction
            trans.commit()

            print()
            print("✅ Migration completed successfully!")
            print()
            print("New schema:")
            print("  apps.public_port: INTEGER, NULLABLE, UNIQUE, INDEXED")
            print("  apps.internal_port: INTEGER, NULLABLE, UNIQUE, INDEXED")
            print()

        except Exception as e:
            trans.rollback()
            print(f"❌ Migration failed: {e}")
            raise


if __name__ == "__main__":
    run_migration()
