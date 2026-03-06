# create_users.py
import sqlite3
from datetime import datetime

print("🚀 Creating users in SQLite database...")

# Connect to SQLite database
conn = sqlite3.connect('local.db')
cursor = conn.cursor()

# Create users table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT,
        email TEXT UNIQUE,
        role TEXT DEFAULT 'staff',
        permissions TEXT DEFAULT '{}',
        is_active INTEGER DEFAULT 1,
        last_login TIMESTAMP,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
''')
print("✅ Users table ready")

# Create test users
test_users = [
    ('superadmin', 'admin123', 'Super Admin', 'super@alhudha.com', 'super_admin'),
    ('admin1', 'admin123', 'Admin User', 'admin@alhudha.com', 'admin'),
    ('manager1', 'admin123', 'Manager User', 'manager@alhudha.com', 'manager'),
    ('staff1', 'admin123', 'Staff User', 'staff@alhudha.com', 'staff'),
    ('viewer1', 'admin123', 'Viewer User', 'viewer@alhudha.com', 'viewer')
]

for username, password, full_name, email, role in test_users:
    cursor.execute('''
        INSERT OR IGNORE INTO users 
        (username, password, full_name, email, role, permissions, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (username, password, full_name, email, role, '{}', 1, datetime.now()))
    print(f"  ✅ Created: {username}")

conn.commit()

# Verify users were created
cursor.execute("SELECT username, role FROM users")
users = cursor.fetchall()
print(f"\n📊 Total users in database: {len(users)}")
for user in users:
    print(f"  - {user[0]} ({user[1]})")

conn.close()
print("\n✅ Database setup complete!")