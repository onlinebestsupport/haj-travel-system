import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    # Get database URL from .env file
    database_url = os.getenv('DATABASE_URL')
    print(f"Attempting to connect to PostgreSQL...")
    print(f"Connection string: {database_url}")
    
    # Try to connect
    conn = psycopg2.connect(database_url)
    print("✅ SUCCESS! Connected to PostgreSQL database!")
    
    # Get database version
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"PostgreSQL version: {version[0]}")
    
    # Close connection
    cursor.close()
    conn.close()
    print("Connection closed.")
    
except Exception as e:
    print(f"❌ FAILED to connect: {e}")
    print("\nPlease check:")
    print("1. Your DATABASE_URL in .env file has the correct password")
    print("2. Your PostgreSQL database is running on Railway")
    print("3. Your internet connection is working")