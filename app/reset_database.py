#!/usr/bin/env python3
"""
Database Reset Script
Run with: python app/reset_database.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import get_db, init_db, release_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Reset the database by dropping and recreating all tables"""
    print("=" * 60)
    print("🔄 RESETTING DATABASE")
    print("=" * 60)
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        # Drop all tables in correct order (respect foreign keys)
        print("Dropping existing tables...")
        
        cursor.execute("DROP TABLE IF EXISTS receipts CASCADE")
        cursor.execute("DROP TABLE IF EXISTS payments CASCADE")
        cursor.execute("DROP TABLE IF EXISTS invoices CASCADE")
        cursor.execute("DROP TABLE IF EXISTS travelers CASCADE")
        cursor.execute("DROP TABLE IF EXISTS batches CASCADE")
        cursor.execute("DROP TABLE IF EXISTS users CASCADE")
        cursor.execute("DROP TABLE IF EXISTS activity_log CASCADE")
        cursor.execute("DROP TABLE IF EXISTS backup_history CASCADE")
        cursor.execute("DROP TABLE IF EXISTS backup_settings CASCADE")
        cursor.execute("DROP TABLE IF EXISTS company_settings CASCADE")
        cursor.execute("DROP TABLE IF EXISTS critical_logs CASCADE")
        cursor.execute("DROP TABLE IF EXISTS email_settings CASCADE")
        cursor.execute("DROP TABLE IF EXISTS frontpage_settings CASCADE")
        cursor.execute("DROP TABLE IF EXISTS whatsapp_settings CASCADE")
        
        conn.commit()
        print("✅ Tables dropped successfully")
        
        # Reinitialize database
        print("Recreating tables...")
        init_db()
        print("✅ Tables created successfully")
        
        print("\n✅ Database reset complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error resetting database: {e}")
        return False
    finally:
        if conn:
            release_db(conn, cursor)

if __name__ == "__main__":
    reset_database()