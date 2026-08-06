import os

# Use PUBLIC URL (not internal)
DB_URL = 'postgresql://postgres:cbZOkSkTGHUBzcIKZQOLmcClIVhHqNAI@yamanote.proxy.rlwy.net:39010/railway?sslmode=require'
os.environ['DATABASE_URL'] = DB_URL

from app.database import init_db, get_db, release_db

print("=" * 60)
print("🚀 Setting up database with PUBLIC URL")
print("=" * 60)

try:
    # Initialize database
    init_db()
    print("✅ Tables created successfully!")
    
    # List all tables
    conn, cursor = get_db()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
    tables = [row[0] for row in cursor.fetchall()]
    release_db(conn, cursor)
    
    print(f"\n📊 Total tables: {len(tables)}")
    print("Tables:")
    for table in tables:
        print(f"  - {table}")
        
    # Check important tables
    important = ['users', 'travelers', 'batches', 'payments', 'invoices', 'receipts']
    print("\n🔍 Important tables check:")
    for table in important:
        status = '✅' if table in tables else '❌'
        print(f"  {status} {table}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)