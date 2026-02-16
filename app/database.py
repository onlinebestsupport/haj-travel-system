import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

def get_db():
    """Get database connection with error handling"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("⚠️ DATABASE_URL not set - using SQLite fallback for development")
        # For Railway, this should be set automatically when you add PostgreSQL
        return None
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        print("✅ Database connected")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def init_db():
    """Initialize database tables"""
    conn = get_db()
    if not conn:
        print("⚠️ No database connection - skipping initialization")
        return False
    
    try:
        cur = conn.cursor()
        
        # Create admin_users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                full_name VARCHAR(100),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        
        # Create batches table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS batches (
                id SERIAL PRIMARY KEY,
                batch_name VARCHAR(100) NOT NULL UNIQUE,
                departure_date DATE,
                return_date DATE,
                total_seats INTEGER DEFAULT 150,
                booked_seats INTEGER DEFAULT 0,
                status VARCHAR(50) DEFAULT 'Open',
                price DECIMAL(12,2),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create travelers table (simplified for now)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS travelers (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                passport_no VARCHAR(50) UNIQUE NOT NULL,
                mobile VARCHAR(20) NOT NULL,
                email VARCHAR(100),
                batch_id INTEGER REFERENCES batches(id) ON DELETE SET NULL,
                pin VARCHAR(4) DEFAULT '0000',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create payments table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                traveler_id INTEGER REFERENCES travelers(id) ON DELETE CASCADE,
                amount DECIMAL(10,2) NOT NULL,
                status VARCHAR(50) DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("✅ Tables created/verified")
        
        # Insert default admin if not exists
        cur.execute("SELECT COUNT(*) FROM admin_users")
        if cur.fetchone()[0] == 0:
            # Default password: admin123 (hash will be set by server)
            cur.execute("""
                INSERT INTO admin_users (username, password_hash, email, full_name) 
                VALUES ('admin', 'dummy_hash', 'admin@alhudha.com', 'Admin User')
            """)
            conn.commit()
            print("✅ Default admin created")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def check_database():
    """Check if database is accessible"""
    conn = get_db()
    if conn:
        conn.close()
        return True
    return False

def get_db_cursor(dictionary=False):
    """Get database cursor"""
    conn = get_db()
    if not conn:
        return None, None
    if dictionary:
        cur = conn.cursor(cursor_factory=RealDictCursor)
    else:
        cur = conn.cursor()
    return conn, cur
