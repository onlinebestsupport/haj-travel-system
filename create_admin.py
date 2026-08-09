import psycopg2
import os
import hashlib

DB_URL = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

cursor.execute("SELECT id FROM users WHERE username='admin'")
if not cursor.fetchone():
    password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
    cursor.execute("""
        INSERT INTO users (username, password, name, email, role, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, ('admin', password_hash, 'Administrator', 'admin@alhudhahaj.work', 'super_admin', True))
    conn.commit()
    print('=' * 50)
    print('✅ ADMIN USER CREATED!')
    print('=' * 50)
    print('Username: admin')
    print('Password: admin123')
    print('=' * 50)
else:
    print('✅ Admin user already exists')

cursor.close()
conn.close()