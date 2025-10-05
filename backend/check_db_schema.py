#!/usr/bin/env python3
"""
Database schema checker and fixer for Proximity.

Checks if the database schema matches the model definitions
and recreates if necessary.
"""

import os
import sqlite3
from datetime import datetime
import shutil

def check_and_fix_database():
    """Check database schema and fix if needed"""
    db_path = "proximity.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file not found. Run migrate_db.py first.")
        return False
    
    # Connect to database and check users table schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get users table schema
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("\n📋 Current users table schema:")
        email_nullable = False
        
        for col in columns:
            col_id, name, type_, notnull, default, pk = col
            nullable_str = "NOT NULL" if notnull else "NULL"
            print(f"   {name}: {type_} ({nullable_str})")
            
            if name == "email":
                email_nullable = not notnull
        
        if not email_nullable:
            print("\n❌ PROBLEM FOUND: email column is NOT NULL, but should be nullable")
            print("   This will cause registration to fail when email is not provided")
            
            # Offer to fix
            response = input("\n🔧 Do you want to fix this? (y/n): ").lower().strip()
            
            if response == 'y':
                conn.close()
                
                # Backup
                backup_path = f"proximity_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                print(f"\n📦 Backing up database to: {backup_path}")
                shutil.copy2(db_path, backup_path)
                
                # Remove old database
                print(f"🗑️  Removing old database...")
                os.remove(db_path)
                
                # Recreate with correct schema
                print(f"🔨 Creating new database with correct schema...")
                from models.database import init_db
                init_db()
                
                print("\n✅ Database fixed!")
                print("   • email is now nullable")
                print("   • Old database backed up")
                return True
            else:
                print("\n⏭️  Skipping fix. Database unchanged.")
                return False
        else:
            print("\n✅ Database schema is correct! email column is nullable.")
            return True
            
    except sqlite3.OperationalError as e:
        print(f"\n❌ Error checking database: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    print("=" * 70)
    print("  PROXIMITY DATABASE SCHEMA CHECKER")
    print("=" * 70)
    
    check_and_fix_database()
