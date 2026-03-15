import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import time
from datetime import datetime

# Global connection pool
connection_pool = None
pool_created = False

def init_connection_pool(min_conn=2, max_conn=10):
    """Initialize PostgreSQL connection pool"""
    global connection_pool, pool_created
    
    if pool_created:
        return connection_pool
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("⚠️ DATABASE_URL not set, using default")
        database_url = "postgresql://postgres:postgres@localhost:5432/railway"
    
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            min_conn,
            max_conn,
            database_url,
            cursor_factory=RealDictCursor
        )
        pool_created = True
        print(f"✅ Database connection pool created with {min_conn}-{max_conn} connections")
        return connection_pool
    except Exception as e:
        print(f"❌ Failed to create connection pool: {e}")
        return None

@contextmanager
def get_db_connection():
    """Get a connection from the pool using context manager"""
    global connection_pool
    if not connection_pool:
        connection_pool = init_connection_pool()
    
    conn = None
    try:
        conn = connection_pool.getconn()
        yield conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)

@contextmanager
def get_db_cursor(commit=False):
    """Get a database cursor with automatic cleanup"""
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

# Legacy functions for backward compatibility
def get_db():
    """Legacy: Get a database connection (for compatibility)"""
    conn = psycopg2.connect(os.getenv('DATABASE_URL'), cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    return conn, cursor

def release_db(conn, cursor):
    """Legacy: Release database connection"""
    if cursor:
        cursor.close()
    if conn:
        conn.close()

def init_db():
    """Initialize database tables if they don't exist"""
    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if tables exist
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
            """)
            tables_exist = cursor.fetchone()['exists']
            
            if tables_exist:
                print("✅ Database tables already exist")
                return
            
            print("🚀 Creating database tables...")
            
            # Create users table (with password_hash)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255),
                    password VARCHAR(255),  -- Legacy, will be deprecated
                    name VARCHAR(255),
                    email VARCHAR(255) UNIQUE,
                    role VARCHAR(50) DEFAULT 'staff',
                    permissions JSONB DEFAULT '{}',
                    is_active BOOLEAN DEFAULT true,
                    last_login TIMESTAMP,
                    password_updated_at TIMESTAMP,
                    reset_token VARCHAR(255),
                    reset_token_expires TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create batches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS batches (
                    id SERIAL PRIMARY KEY,
                    batch_name VARCHAR(255) NOT NULL,
                    total_seats INTEGER DEFAULT 150,
                    booked_seats INTEGER DEFAULT 0,
                    price DECIMAL(10,2),
                    departure_date DATE,
                    return_date DATE,
                    status VARCHAR(50) DEFAULT 'Open',
                    description TEXT,
                    itinerary TEXT,
                    inclusions TEXT,
                    exclusions TEXT,
                    hotel_details TEXT,
                    transport_details TEXT,
                    meal_plan TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create travelers table (33 fields)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS travelers (
                    id SERIAL PRIMARY KEY,
                    first_name VARCHAR(255) NOT NULL,
                    last_name VARCHAR(255) NOT NULL,
                    passport_name VARCHAR(255),
                    batch_id INTEGER REFERENCES batches(id) ON DELETE SET NULL,
                    passport_no VARCHAR(50) UNIQUE NOT NULL,
                    passport_issue_date DATE,
                    passport_expiry_date DATE,
                    passport_status VARCHAR(50) DEFAULT 'Active',
                    gender VARCHAR(20),
                    dob DATE,
                    mobile VARCHAR(20) NOT NULL,
                    email VARCHAR(255),
                    aadhaar VARCHAR(20),
                    pan VARCHAR(20),
                    aadhaar_pan_linked VARCHAR(20) DEFAULT 'No',
                    vaccine_status VARCHAR(50) DEFAULT 'Not Vaccinated',
                    wheelchair VARCHAR(10) DEFAULT 'No',
                    place_of_birth VARCHAR(255),
                    place_of_issue VARCHAR(255),
                    passport_address TEXT,
                    father_name VARCHAR(255),
                    mother_name VARCHAR(255),
                    spouse_name VARCHAR(255),
                    passport_scan TEXT,
                    aadhaar_scan TEXT,
                    pan_scan TEXT,
                    vaccine_scan TEXT,
                    photo TEXT,
                    pin VARCHAR(10) DEFAULT '0000',
                    emergency_contact VARCHAR(255),
                    emergency_phone VARCHAR(20),
                    medical_notes TEXT,
                    extra_fields JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create payments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    traveler_id INTEGER REFERENCES travelers(id) ON DELETE CASCADE,
                    batch_id INTEGER REFERENCES batches(id) ON DELETE CASCADE,
                    amount DECIMAL(10,2) NOT NULL,
                    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    payment_method VARCHAR(50),
                    status VARCHAR(50) DEFAULT 'pending',
                    reference VARCHAR(100),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create invoices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id SERIAL PRIMARY KEY,
                    traveler_id INTEGER REFERENCES travelers(id) ON DELETE CASCADE,
                    batch_id INTEGER REFERENCES batches(id) ON DELETE CASCADE,
                    invoice_number VARCHAR(100) UNIQUE,
                    amount DECIMAL(10,2) NOT NULL,
                    due_date DATE,
                    status VARCHAR(50) DEFAULT 'pending',
                    items JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create receipts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS receipts (
                    id SERIAL PRIMARY KEY,
                    traveler_id INTEGER REFERENCES travelers(id) ON DELETE CASCADE,
                    payment_id INTEGER REFERENCES payments(id) ON DELETE SET NULL,
                    receipt_number VARCHAR(100) UNIQUE,
                    amount DECIMAL(10,2) NOT NULL,
                    receipt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create activity_log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    action VARCHAR(100) NOT NULL,
                    module VARCHAR(100),
                    description TEXT,
                    ip_address VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create backup_settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backup_settings (
                    id SERIAL PRIMARY KEY,
                    auto_backup BOOLEAN DEFAULT true,
                    backup_frequency VARCHAR(50) DEFAULT 'daily',
                    backup_time TIME DEFAULT '02:00:00',
                    retention_days INTEGER DEFAULT 30,
                    last_backup TIMESTAMP,
                    next_backup TIMESTAMP,
                    backup_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create company_settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company_settings (
                    id SERIAL PRIMARY KEY,
                    company_name VARCHAR(255) DEFAULT 'Alhudha Haj Travel',
                    address TEXT,
                    phone VARCHAR(50),
                    email VARCHAR(255),
                    website VARCHAR(255),
                    logo TEXT,
                    gst VARCHAR(50),
                    pan VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default admin user if not exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'superadmin'")
            if cursor.fetchone()['count'] == 0:
                from werkzeug.security import generate_password_hash
                password_hash = generate_password_hash('admin123')
                
                cursor.execute("""
                    INSERT INTO users (username, password_hash, name, email, role, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, ('superadmin', password_hash, 'Super Admin', 'admin@alhudha.com', 'super_admin', True))
                
                cursor.execute("""
                    INSERT INTO users (username, password_hash, name, email, role, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, ('admin1', generate_password_hash('admin123'), 'Admin User', 'admin1@alhudha.com', 'admin', True))
            
            print("✅ Database initialization complete")
            
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        raise e
