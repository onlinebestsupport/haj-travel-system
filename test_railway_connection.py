# test_railway_connection.py
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
print(f"📊 DATABASE_URL: {DATABASE_URL[:50]}...")

try:
    # Try to connect
    conn = psycopg2.connect(DATABASE_URL)
    print("✅ Successfully connected to Railway database!")
    
    # Test query
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"📦 PostgreSQL version: {version[0]}")
    
    # Check if users table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'users'
        )
    """)
    users_exists = cursor.fetchone()[0]
    print(f"👥 Users table exists: {users_exists}")
    
    if users_exists:
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"👤 Number of users: {user_count}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n🔧 Troubleshooting tips:")
    print("1. Make sure your DATABASE_URL in .env is correct")
    print("2. Check if Railway allows external connections")
    print("3. Your IP might need to be whitelisted")