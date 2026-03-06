#!/usr/bin/env python3
"""
Database Reset Tool - PostgreSQL Version for Railway
Run: python app/reset_database.py
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def reset_database():
    """Reset the database - drops and recreates all tables"""
    print("="*60)
    print("🔥 DATABASE RESET TOOL")
    print("="*60)
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment!")
        print("   Make sure .env file exists with DATABASE_URL")
        return False
    
    print(f"📊 Connecting to database...")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL")
        
        # Drop all tables
        print("
🗑️  Dropping all tables...")
        cursor.execute("""
            DROP TABLE IF EXISTS 
                activity_log,
                backup_history,
                batches,
                company_settings,
                email_settings,
                frontpage_settings,
                invoices,
                payments,
                receipts,
                travelers,
                users,
                whatsapp_settings
            CASCADE;
        """)
        print("✅ Tables dropped")
        
        # Recreate tables by importing from database.py
        print("
🔄 Recreating tables...")
        
        # Import and run init_db
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from app.database import init_db
        
        with conn:
            init_db()
        
        print("✅ Tables recreated successfully!")
        
        cursor.close()
        conn.close()
        
        print("
" + "="*60)
        print("✅ DATABASE RESET COMPLETE!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    reset_database()
