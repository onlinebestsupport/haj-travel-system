import os
import psycopg2
import psycopg2.extras
import psycopg2.pool  # 🔥 CONNECTION POOLING
from datetime import datetime
import json
import threading
import time
from dotenv import load_dotenv

load_dotenv()

# ==================== 🔥 DATABASE CONFIGURATION ====================
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL environment variable REQUIRED")

print(f"📡 PostgreSQL: {DATABASE_URL.split('@')[1].split('/')[0]}")

# ==================== 🔥 GLOBAL CONNECTION POOL ====================
_pool = None
_init_lock = threading.Lock()
_INITIALIZED = False
_INITIALIZING = False

def get_connection_pool():
    """🔥 Thread-safe connection pool initialization"""
    global _pool
    if _pool is None:
        with _init_lock:
            if _pool is None:
                _pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1, maxconn=20, dsn=DATABASE_URL, idle_timeout=300
                )
                print("✅ Connection pool: 1-20 connections")
    return _pool

def get_db():
    """🔥 Get pooled connection - middleware/server safe"""
    pool = get_connection_pool()
    try:
        conn = pool.getconn()
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        return conn, cursor
    except Exception as e:
        print(f"❌ Pool error: {e}")
        raise

def release_db(conn=None, cursor=None):
    """🔥 CRITICAL: Return to pool - session saver"""
    if cursor:
        cursor.close()
    if conn:
        try:
            pool = get_connection_pool()
            pool.putconn(conn)
        except Exception as e:
            print(f"⚠️ Pool return error: {e}")

# ==================== 🗄️ TABLES (YOUR ORIGINAL SCHEMA - PERFECT) ====================
# [ALL your create_*_table functions EXACTLY SAME - NO CHANGES NEEDED]
def create_users_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY, username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL, full_name VARCHAR(255),
            email VARCHAR(255) UNIQUE, phone VARCHAR(50), department VARCHAR(255),
            role VARCHAR(50) DEFAULT 'staff', permissions JSONB DEFAULT '{}',
            is_active BOOLEAN DEFAULT TRUE, last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

# ... [ALL OTHER create_*_table functions IDENTICAL to your original] ...
def create_company_settings_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_settings (
            id SERIAL PRIMARY KEY, legal_name VARCHAR(255), display_name VARCHAR(255),
            address_line1 VARCHAR(255), address_line2 VARCHAR(255), city VARCHAR(100),
            state VARCHAR(100), country VARCHAR(100), pin_code VARCHAR(20),
            phone VARCHAR(50), mobile VARCHAR(50), email VARCHAR(255), website VARCHAR(255),
            gstin VARCHAR(50), pan VARCHAR(50), tan VARCHAR(50), tcs_no VARCHAR(50),
            tin VARCHAR(50), cin VARCHAR(50), iec VARCHAR(50), msme VARCHAR(50),
            bank_name VARCHAR(255), bank_branch VARCHAR(255), account_name VARCHAR(255),
            account_no VARCHAR(100), ifsc_code VARCHAR(50), micr_code VARCHAR(50),
            upi_id VARCHAR(100), qr_code TEXT, logo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        INSERT INTO company_settings (id, legal_name, display_name, country)
        VALUES (1, 'Alhudha Haj Service P Ltd.', 'Alhudha Haj Travel', 'India')
        ON CONFLICT (id) DO NOTHING
    """)

def seed_default_users(conn, cursor):
    """✅ Your original seeding - perfect"""
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()['count'] == 0:
        users = [
            ('superadmin', 'admin123', 'Super Admin', 'super@alhudha.com', 'super_admin'),
            ('admin1', 'admin123', 'Admin User', 'admin@alhudha.com', 'admin')
        ]
        for u, p, n, e, r in users:
            cursor.execute("INSERT INTO users (username, password, full_name, email, role, permissions) VALUES (%s,%s,%s,%s,%s,'{}')", (u,p,n,e,r))
        conn.commit()
        print("✅ Default users seeded")

def init_db():
    """🔥 Thread-safe pooled initialization"""
    global _INITIALIZED, _INITIALIZING
    with _init_lock:
        if _INITIALIZED: return True
        if _INITIALIZING:
            for i in range(30):
                if _INITIALIZED: return True
                time.sleep(1)
            return False
        _INITIALIZING = True

    conn = cursor = None
    try:
        print("🚀 Initializing database...")
        conn, cursor = get_db()
        
        # Create all your tables [EXACT SAME ORDER AS ORIGINAL]
        create_users_table(cursor)
        # ... [ALL your create_* functions - unchanged] ...
        create_company_settings_table(cursor)
        
        conn.commit()
        seed_default_users(conn, cursor)
        
        cursor.execute("SELECT version()")
        print(f"✅ PostgreSQL: {cursor.fetchone()['version'][:50]}")
        
        _INITIALIZED = True
        print("✅ Database ready - pooled!")
        return True
    except Exception as e:
        print(f"❌ Init failed: {e}")
        if conn: conn.rollback()
        return False
    finally:
        release_db(conn, cursor)

# ==================== 🛠️ POOL-SAFE HELPERS ====================
def execute_query(query, params=None):
    conn = cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute(query, params or ())
        return cursor.fetchall() if query.strip().upper().startswith('SELECT') else cursor.rowcount
        conn.commit()
    finally:
        release_db(conn, cursor)

# [All your other helper functions with release_db() - same pattern]

__all__ = ['get_db', 'release_db', 'init_db', 'execute_query']  # ✅ middleware compatible
