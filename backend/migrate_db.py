#!/usr/bin/env python3
"""
Database migration script for Proximity.

This script safely migrates the database schema by:
1. Backing up the existing database
2. Updating the schema to make email nullable
3. Recreating tables if necessary
"""

import os
import shutil
from datetime import datetime
from models.database import Base, engine, init_db

def migrate():
    """Migrate database schema"""
    db_path = "proximity.db"
    
    # Backup existing database if it exists
    if os.path.exists(db_path):
        backup_path = f"proximity_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        print(f"📦 Backing up existing database to: {backup_path}")
        shutil.copy2(db_path, backup_path)
        
        # For SQLite, we need to drop and recreate
        print(f"🗑️  Removing old database: {db_path}")
        os.remove(db_path)
    
    # Create new database with updated schema
    print("🔨 Creating new database with updated schema...")
    init_db()
    
    print("✅ Database migration complete!")
    print(f"   • Email field is now optional")
    print(f"   • Old database backed up (if existed)")
    print(f"   • Ready for first user registration")

if __name__ == "__main__":
    migrate()
