import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Connect to default 'postgres' database first
database_url = os.getenv('DATABASE_URL')
# Replace the database name with 'postgres' to list databases
base_url = database_url.rsplit('/', 1)[0] + '/postgres'

try:
    print(f"Connecting to: {base_url}")
    conn = psycopg2.connect(base_url)
    conn.autocommit = True
    cursor = conn.cursor()
    
    cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    databases = cursor.fetchall()
    
    print("\n✅ Available databases:")
    for db in databases:
        print(f"  - {db[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
