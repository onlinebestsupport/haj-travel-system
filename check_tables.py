# check_tables.py
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

print("="*50)
print("📊 DATABASE TABLE STRUCTURE")
print("="*50)

# Check batches table
try:
    try:
        cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'batches'
        ORDER BY ordinal_position
    """)
    rows = cursor.fetchall()
    print(f"\n📦 Batches table columns ({len(rows)} columns):")
    for col in rows:
        print(f"  - {col[0]}: {col[1]}")
except Exception as e:
    print(f"❌ Error checking batches table: {e}")

# Check travelers table
try:
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'travelers'
        ORDER BY ordinal_position
    """)
    rows = cursor.fetchall()
    print(f"\n👥 Travelers table columns ({len(rows)} columns):")
    for col in rows:
        print(f"  - {col[0]}: {col[1]}")
except Exception as e:
    print(f"❌ Error checking travelers table: {e}")

# Check users table
try:
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    """)
    rows = cursor.fetchall()
    print(f"\n👤 Users table columns ({len(rows)} columns):")
    for col in rows:
        print(f"  - {col[0]}: {col[1]}")
except Exception as e:
    print(f"❌ Error checking users table: {e}")

# Show existing data
print("\n" + "="*50)
print("📊 EXISTING DATA")
print("="*50)

try:
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"\n👤 Users: {user_count}")
    if user_count > 0:
        cursor.execute("SELECT id, username, role FROM users LIMIT 5")
        for user in cursor.fetchall():
            print(f"  - ID: {user[0]}, Username: {user[1]}, Role: {user[2]}")
except Exception as e:
    print(f"❌ Error checking users: {e}")

try:
    cursor.execute("SELECT COUNT(*) FROM batches")
    batch_count = cursor.fetchone()[0]
    print(f"\n📦 Batches: {batch_count}")
except Exception as e:
    print(f"❌ Error checking batches: {e}")

try:
    cursor.execute("SELECT COUNT(*) FROM travelers")
    traveler_count = cursor.fetchone()[0]
    print(f"\n👥 Travelers: {traveler_count}")
except Exception as e:
    print(f"❌ Error checking travelers: {e}")

cursor.close()
conn.close()
    finally:
        release_db(conn, cursor)
print("\n" + "="*50)