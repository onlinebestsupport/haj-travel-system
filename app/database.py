import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_db():
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        return None
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        print("✅ Database connected successfully!")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def init_db():
    conn = get_db()
    if not conn:
        print("❌ Cannot initialize database - no connection")
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
                last_login TIMESTAMP,
                created_by INTEGER REFERENCES admin_users(id)
            );
        """)
        print("✅ admin_users table ready")
        
        # Create roles table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT
            );
        """)
        print("✅ roles table ready")
        
        # Create permissions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT
            );
        """)
        print("✅ permissions table ready")
        
        # Create role_permissions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
                permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
                PRIMARY KEY (role_id, permission_id)
            );
        """)
        print("✅ role_permissions table ready")
        
        # Create user_roles table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER REFERENCES admin_users(id) ON DELETE CASCADE,
                role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
                assigned_by INTEGER REFERENCES admin_users(id),
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, role_id)
            );
        """)
        print("✅ user_roles table ready")
        
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
            );
        """)
        print("✅ batches table ready")
        
        # Create travelers table with 33 fields
        cur.execute("""
            CREATE TABLE IF NOT EXISTS travelers (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                passport_name VARCHAR(101) GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
                batch_id INTEGER REFERENCES batches(id) ON DELETE SET NULL,
                passport_no VARCHAR(50) UNIQUE NOT NULL,
                passport_issue_date DATE,
                passport_expiry_date DATE,
                passport_status VARCHAR(50) DEFAULT 'Active',
                gender VARCHAR(10),
                dob DATE,
                mobile VARCHAR(20) NOT NULL,
                email VARCHAR(100),
                aadhaar VARCHAR(20),
                pan VARCHAR(20),
                aadhaar_pan_linked VARCHAR(20) DEFAULT 'No',
                vaccine_status VARCHAR(50) DEFAULT 'Not Vaccinated',
                wheelchair VARCHAR(10) DEFAULT 'No',
                place_of_birth VARCHAR(100),
                place_of_issue VARCHAR(100),
                passport_address TEXT,
                father_name VARCHAR(100),
                mother_name VARCHAR(100),
                spouse_name VARCHAR(100),
                passport_scan VARCHAR(255),
                aadhaar_scan VARCHAR(255),
                pan_scan VARCHAR(255),
                vaccine_scan VARCHAR(255),
                extra_fields JSONB DEFAULT '{}'::jsonb,
                pin VARCHAR(4) DEFAULT '0000',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER REFERENCES admin_users(id),
                updated_by INTEGER REFERENCES admin_users(id)
            );
        """)
        print("✅ travelers table ready (33 fields)")
        
        # Create payments table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                traveler_id INTEGER REFERENCES travelers(id) ON DELETE CASCADE,
                installment VARCHAR(50),
                amount DECIMAL(10,2) NOT NULL,
                due_date DATE,
                payment_date DATE,
                payment_method VARCHAR(50),
                transaction_id VARCHAR(100),
                status VARCHAR(50) DEFAULT 'Pending',
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                recorded_by INTEGER REFERENCES admin_users(id)
            );
        """)
        print("✅ payments table ready")
        
        # Create login_logs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS login_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES admin_users(id) ON DELETE SET NULL,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                logout_time TIMESTAMP,
                ip_address VARCHAR(45),
                user_agent TEXT
            );
        """)
        print("✅ login_logs table ready")
        
        # Create backups table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS backups (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255),
                size_bytes BIGINT,
                traveler_count INTEGER,
                batch_count INTEGER,
                payment_count INTEGER,
                status VARCHAR(50),
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER REFERENCES admin_users(id)
            );
        """)
        print("✅ backups table ready")
        
        # Create indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_travelers_passport ON travelers(passport_no);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_travelers_mobile ON travelers(mobile);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_travelers_batch ON travelers(batch_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_payments_traveler ON payments(traveler_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);")
        print("✅ indexes created")
        
        # Insert default data if not exists
        cur.execute("SELECT COUNT(*) FROM roles")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO roles (name, description) VALUES 
                ('super_admin', 'Full system access'),
                ('admin', 'Can manage all data except users'),
                ('manager', 'Can manage batches and travelers'),
                ('staff', 'Can add and edit travelers'),
                ('viewer', 'Read-only access')
            """)
            print("✅ Default roles inserted")
        
        cur.execute("SELECT COUNT(*) FROM admin_users")
        if cur.fetchone()[0] == 0:
            admin_password_hash = 'L5Ks5qk2Y8O+c1CXzX6hWpPxG69RyB5+2n4O7U+DmVQ='
            cur.execute("""
                INSERT INTO admin_users (username, password_hash, email, full_name, is_active) VALUES 
                ('superadmin', %s, 'admin@alhudha.com', 'Super Administrator', true),
                ('admin1', %s, 'admin1@alhudha.com', 'Ahmed Khan', true),
                ('manager1', %s, 'manager@alhudha.com', 'Manager', true),
                ('staff1', %s, 'staff1@alhudha.com', 'Omar Hassan', true),
                ('staff2', %s, 'staff2@alhudha.com', 'Aisha Rahman', true),
                ('viewer1', %s, 'viewer1@alhudha.com', 'Zainab Ali', true)
            """, (admin_password_hash, admin_password_hash, admin_password_hash, admin_password_hash, admin_password_hash, admin_password_hash))
            print("✅ Default admin users created")
        
        conn.commit()
        print("🎉 Database initialization COMPLETE!")
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
        conn.close()
        return False

def get_db_cursor(dictionary=False):
    conn = get_db()
    if not conn:
        return None, None
    
    try:
        if dictionary:
            cur = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cur = conn.cursor()
        return conn, cur
    except Exception as e:
        print(f"❌ Error creating cursor: {e}")
        conn.close()
        return None, None
