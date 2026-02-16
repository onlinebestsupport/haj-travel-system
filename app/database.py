import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

def get_db():
    """Get database connection with error handling"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        print("⚠️ Using fallback connection string for development")
        # Fallback for development - Railway will override this with actual DATABASE_URL
        database_url = "postgresql://postgres:postgres@localhost:5432/haj_travel"
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        print("✅ Database connected successfully!")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def init_db():
    """Initialize ALL database tables needed for the Haj Travel System"""
    conn = get_db()
    if not conn:
        print("❌ Cannot initialize database - no connection")
        return False
    
    try:
        cur = conn.cursor()
        
        # ============ CREATE TABLES IN CORRECT ORDER ============
        
        # 1. Create admin_users table (for staff login)
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
        
        # 2. Create roles table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT
            );
        """)
        print("✅ roles table ready")
        
        # 3. Create permissions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT
            );
        """)
        print("✅ permissions table ready")
        
        # 4. Create role_permissions junction table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
                permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
                PRIMARY KEY (role_id, permission_id)
            );
        """)
        print("✅ role_permissions table ready")
        
        # 5. Create user_roles junction table
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
        
        # 6. Create batches table (Haj/Umrah packages)
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
        
        # 7. Create travelers table with ALL 33 fields
        cur.execute("""
            CREATE TABLE IF NOT EXISTS travelers (
                id SERIAL PRIMARY KEY,
                -- Personal Information (10 fields)
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
                
                -- Contact Information (7 fields)
                mobile VARCHAR(20) NOT NULL,
                email VARCHAR(100),
                aadhaar VARCHAR(20),
                pan VARCHAR(20),
                aadhaar_pan_linked VARCHAR(20) DEFAULT 'No',
                vaccine_status VARCHAR(50) DEFAULT 'Not Vaccinated',
                wheelchair VARCHAR(10) DEFAULT 'No',
                
                -- Address & Family (6 fields)
                place_of_birth VARCHAR(100),
                place_of_issue VARCHAR(100),
                passport_address TEXT,
                father_name VARCHAR(100),
                mother_name VARCHAR(100),
                spouse_name VARCHAR(100),
                
                -- Documents (4 fields)
                passport_scan VARCHAR(255),
                aadhaar_scan VARCHAR(255),
                pan_scan VARCHAR(255),
                vaccine_scan VARCHAR(255),
                
                -- Additional Fields (6 fields)
                extra_fields JSONB DEFAULT '{}'::jsonb,
                pin VARCHAR(4) DEFAULT '0000',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Tracking (automated)
                created_by INTEGER REFERENCES admin_users(id),
                updated_by INTEGER REFERENCES admin_users(id)
            );
        """)
        print("✅ travelers table ready (33 fields)")
        
        # 8. Create payments table
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
        
        # 9. Create login_logs table
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
        
        # 10. Create backups table
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
        
        # 11. Create payment_reversals table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payment_reversals (
                id SERIAL PRIMARY KEY,
                original_payment_id INTEGER REFERENCES payments(id) ON DELETE CASCADE,
                amount DECIMAL(10,2) NOT NULL,
                reason TEXT NOT NULL,
                reversed_by INTEGER REFERENCES admin_users(id),
                reversed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_full_reversal BOOLEAN DEFAULT true
            );
        """)
        print("✅ payment_reversals table ready")
        
        # 12. Create invoices table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id SERIAL PRIMARY KEY,
                traveler_id INTEGER REFERENCES travelers(id) ON DELETE CASCADE,
                invoice_number VARCHAR(50) UNIQUE,
                base_amount DECIMAL(10,2),
                gst_rate DECIMAL(5,2),
                gst_amount DECIMAL(10,2),
                tcs_rate DECIMAL(5,2),
                tcs_amount DECIMAL(10,2),
                total_amount DECIMAL(10,2),
                total_paid DECIMAL(10,2),
                balance_due DECIMAL(10,2),
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                generated_by INTEGER REFERENCES admin_users(id),
                pdf_path TEXT
            );
        """)
        print("✅ invoices table ready")
        
        # ============ CREATE INDEXES FOR PERFORMANCE ============
        cur.execute("CREATE INDEX IF NOT EXISTS idx_travelers_passport ON travelers(passport_no);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_travelers_mobile ON travelers(mobile);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_travelers_batch ON travelers(batch_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_payments_traveler ON payments(traveler_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_login_logs_user ON login_logs(user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_login_logs_time ON login_logs(login_time);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_batches_status ON batches(status);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_batches_dates ON batches(departure_date, return_date);")
        print("✅ indexes created")
        
        # ============ INSERT DEFAULT DATA ============
        
        # Insert default roles
        cur.execute("""
            INSERT INTO roles (name, description) VALUES 
            ('super_admin', 'Full system access - can manage users and all data'),
            ('admin', 'Can manage all data except users'),
            ('manager', 'Can manage batches and travelers'),
            ('staff', 'Can add and edit travelers'),
            ('viewer', 'Read-only access')
            ON CONFLICT (name) DO NOTHING;
        """)
        
        # Insert default permissions
        cur.execute("""
            INSERT INTO permissions (name, description) VALUES 
            ('manage_users', 'Create, edit, delete users'),
            ('view_users', 'View user list'),
            ('manage_batches', 'Create, edit, delete batches'),
            ('view_batches', 'View batches'),
            ('manage_travelers', 'Create, edit, delete travelers'),
            ('view_travelers', 'View travelers'),
            ('create_payment', 'Record payments'),
            ('view_payments', 'View payments'),
            ('reverse_payment', 'Reverse/cancel payments'),
            ('view_reports', 'View reports'),
            ('create_backup', 'Create database backups'),
            ('restore_backup', 'Restore from backup'),
            ('export_data', 'Export data'),
            ('view_logs', 'View login logs')
            ON CONFLICT (name) DO NOTHING;
        """)
        
        # Super Admin gets all permissions
        cur.execute("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id FROM roles r, permissions p
            WHERE r.name = 'super_admin'
            ON CONFLICT DO NOTHING;
        """)
        
        # Admin permissions
        cur.execute("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id FROM roles r, permissions p
            WHERE r.name = 'admin' AND p.name IN (
                'manage_batches', 'view_batches',
                'manage_travelers', 'view_travelers',
                'create_payment', 'view_payments',
                'reverse_payment', 'view_reports',
                'create_backup', 'export_data', 'view_logs'
            )
            ON CONFLICT DO NOTHING;
        """)
        
        # Manager permissions
        cur.execute("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id FROM roles r, permissions p
            WHERE r.name = 'manager' AND p.name IN (
                'manage_batches', 'view_batches',
                'manage_travelers', 'view_travelers',
                'create_payment', 'view_payments',
                'view_reports'
            )
            ON CONFLICT DO NOTHING;
        """)
        
        # Staff permissions
        cur.execute("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id FROM roles r, permissions p
            WHERE r.name = 'staff' AND p.name IN (
                'view_batches',
                'manage_travelers', 'view_travelers',
                'create_payment', 'view_payments'
            )
            ON CONFLICT DO NOTHING;
        """)
        
        # Viewer permissions
        cur.execute("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id FROM roles r, permissions p
            WHERE r.name = 'viewer' AND p.name IN (
                'view_batches', 'view_travelers', 'view_payments'
            )
            ON CONFLICT DO NOTHING;
        """)
        
        # Insert default admin users (password: admin123)
        # SHA256 hash for "admin123" with salt "alhudha-salt-2026"
        admin_password_hash = 'L5Ks5qk2Y8O+c1CXzX6hWpPxG69RyB5+2n4O7U+DmVQ='
        
        cur.execute("""
            INSERT INTO admin_users (username, password_hash, email, full_name, is_active) VALUES 
            ('superadmin', %s, 'super@alhudha.com', 'Super Admin', true),
            ('admin', %s, 'admin@alhudha.com', 'Admin User', true),
            ('manager', %s, 'manager@alhudha.com', 'Manager', true),
            ('staff', %s, 'staff@alhudha.com', 'Staff Member', true),
            ('viewer', %s, 'viewer@alhudha.com', 'Viewer Only', true)
            ON CONFLICT (username) DO NOTHING;
        """, (admin_password_hash, admin_password_hash, admin_password_hash, admin_password_hash, admin_password_hash))
        
        # Assign roles to users
        cur.execute("""
            INSERT INTO user_roles (user_id, role_id)
            SELECT u.id, r.id FROM admin_users u, roles r
            WHERE u.username = 'superadmin' AND r.name = 'super_admin'
            ON CONFLICT DO NOTHING;
        """)
        
        cur.execute("""
            INSERT INTO user_roles (user_id, role_id)
            SELECT u.id, r.id FROM admin_users u, roles r
            WHERE u.username = 'admin' AND r.name = 'admin'
            ON CONFLICT DO NOTHING;
        """)
        
        cur.execute("""
            INSERT INTO user_roles (user_id, role_id)
            SELECT u.id, r.id FROM admin_users u, roles r
            WHERE u.username = 'manager' AND r.name = 'manager'
            ON CONFLICT DO NOTHING;
        """)
        
        cur.execute("""
            INSERT INTO user_roles (user_id, role_id)
            SELECT u.id, r.id FROM admin_users u, roles r
            WHERE u.username = 'staff' AND r.name = 'staff'
            ON CONFLICT DO NOTHING;
        """)
        
        cur.execute("""
            INSERT INTO user_roles (user_id, role_id)
            SELECT u.id, r.id FROM admin_users u, roles r
            WHERE u.username = 'viewer' AND r.name = 'viewer'
            ON CONFLICT DO NOTHING;
        """)
        
        # Insert sample batches
        cur.execute("""
            INSERT INTO batches (batch_name, departure_date, return_date, total_seats, price, status, description) VALUES 
            ('Haj Silver 2026', '2026-06-15', '2026-07-30', 150, 350000.00, 'Open', 'Economy Haj package with shared accommodation in Azizia. Includes visa processing, transportation, and meals.'),
            ('Haj Gold 2026', '2026-06-15', '2026-07-30', 100, 550000.00, 'Open', 'Comfort Haj package with private rooms in Makkah (500m from Haram) and Madinah (300m from Masjid Nabawi).'),
            ('Haj Platinum 2026', '2026-06-14', '2026-07-31', 50, 850000.00, 'Open', 'Premium Haj package with luxury hotels overlooking Haram in Makkah and Madinah. VIP transportation and guided tours.'),
            ('Umrah Ramadhan Special', '2026-03-01', '2026-03-20', 200, 125000.00, 'Open', '20-day Umrah package during Ramadhan. Stay in Makkah (10 days) and Madinah (10 days). All meals included.'),
            ('Umrah Winter', '2026-12-10', '2026-12-25', 150, 95000.00, 'Open', '15-day Umrah package with pleasant weather. Includes Ziyarat visits to historical sites.')
            ON CONFLICT (batch_name) DO NOTHING;
        """)
        
        # Insert sample travelers
        cur.execute("""
            INSERT INTO travelers (
                first_name, last_name, passport_no, mobile, email, pin, 
                gender, dob, passport_issue_date, passport_expiry_date,
                aadhaar, pan, vaccine_status, place_of_birth, father_name, mother_name,
                extra_fields, batch_id
            ) 
            SELECT 
                'Ahmed', 'Khan', 'A1234567', '9876543210', 'ahmed.khan@email.com', '1234',
                'Male', '1985-05-20', '2020-01-15', '2030-01-14',
                '1234-5678-9012', 'ABCDE1234F', 'Fully Vaccinated', 'Mumbai', 'Abdul Khan', 'Aisha Khan',
                '{"blood_group": "O+", "allergies": "None", "emergency_contact": "Brother - Abdul", "emergency_phone": "9876543211"}',
                id FROM batches WHERE batch_name = 'Haj Platinum 2026'
            ON CONFLICT (passport_no) DO NOTHING;
        """)
        
        cur.execute("""
            INSERT INTO travelers (
                first_name, last_name, passport_no, mobile, email, pin,
                gender, dob, passport_issue_date, passport_expiry_date,
                aadhaar, pan, vaccine_status, place_of_birth, father_name, mother_name,
                extra_fields, batch_id
            ) 
            SELECT 
                'Fatima', 'Begum', 'B7654321', '9876543211', 'fatima.begum@email.com', '5678',
                'Female', '1990-08-15', '2021-03-10', '2031-03-09',
                '2345-6789-0123', 'FGHIJ5678K', 'Fully Vaccinated', 'Delhi', 'Mohammed Ali', 'Zainab Ali',
                '{"blood_group": "A+", "allergies": "Dust", "emergency_contact": "Hassan Khan", "emergency_phone": "9876543212"}',
                id FROM batches WHERE batch_name = 'Haj Gold 2026'
            ON CONFLICT (passport_no) DO NOTHING;
        """)
        
        cur.execute("""
            INSERT INTO travelers (
                first_name, last_name, passport_no, mobile, email, pin,
                gender, dob, passport_issue_date, passport_expiry_date,
                aadhaar, pan, vaccine_status, place_of_birth, father_name, mother_name,
                extra_fields, batch_id
            ) 
            SELECT 
                'Mohammed', 'Rafi', 'C9876543', '9876543212', 'mohammed.rafi@email.com', '9012',
                'Male', '1982-11-30', '2019-12-05', '2029-12-04',
                '3456-7890-1234', 'KLMNO9012P', 'Fully Vaccinated', 'Hyderabad', 'Ibrahim Rafi', 'Zahara Rafi',
                '{"blood_group": "B+", "allergies": "Pollen", "emergency_contact": "Sister - Aisha", "emergency_phone": "9876543213"}',
                id FROM batches WHERE batch_name = 'Haj Silver 2026'
            ON CONFLICT (passport_no) DO NOTHING;
        """)
        
        cur.execute("""
            INSERT INTO travelers (
                first_name, last_name, passport_no, mobile, email, pin,
                gender, dob, passport_issue_date, passport_expiry_date,
                aadhaar, pan, vaccine_status, place_of_birth, father_name, mother_name,
                extra_fields, batch_id
            ) 
            SELECT 
                'Aisha', 'Begum', 'D2468135', '9876543213', 'aisha.begum@email.com', '3456',
                'Female', '1988-03-25', '2022-07-20', '2032-07-19',
                '4567-8901-2345', 'PQRST3456U', 'Fully Vaccinated', 'Chennai', 'Yusuf Begum', 'Khadija Begum',
                '{"blood_group": "AB+", "allergies": "None", "emergency_contact": "Husband - Salman", "emergency_phone": "9876543214"}',
                id FROM batches WHERE batch_name = 'Umrah Ramadhan Special'
            ON CONFLICT (passport_no) DO NOTHING;
        """)
        
        # Insert sample payments
        cur.execute("""
            INSERT INTO payments (traveler_id, installment, amount, payment_date, status, payment_method, transaction_id)
            SELECT id, 'Booking Amount', 85000, CURRENT_DATE - INTERVAL '30 days', 'Paid', 'Bank Transfer', 'TXN' || floor(random() * 1000000)::text
            FROM travelers WHERE passport_no = 'A1234567'
            ON CONFLICT DO NOTHING;
        """)
        
        cur.execute("""
            INSERT INTO payments (traveler_id, installment, amount, payment_date, status, payment_method, transaction_id)
            SELECT id, '1st Installment', 170000, CURRENT_DATE - INTERVAL '15 days', 'Paid', 'UPI', 'TXN' || floor(random() * 1000000)::text
            FROM travelers WHERE passport_no = 'A1234567'
            ON CONFLICT DO NOTHING;
        """)
        
        cur.execute("""
            INSERT INTO payments (traveler_id, installment, amount, due_date, status)
            SELECT id, '2nd Installment', 255000, CURRENT_DATE + INTERVAL '15 days', 'Pending'
            FROM travelers WHERE passport_no = 'A1234567'
            ON CONFLICT DO NOTHING;
        """)
        
        cur.execute("""
            INSERT INTO payments (traveler_id, installment, amount, payment_date, status, payment_method, transaction_id)
            SELECT id, 'Booking Amount', 55000, CURRENT_DATE - INTERVAL '25 days', 'Paid', 'Credit Card', 'TXN' || floor(random() * 1000000)::text
            FROM travelers WHERE passport_no = 'B7654321'
            ON CONFLICT DO NOTHING;
        """)
        
        cur.execute("""
            INSERT INTO payments (traveler_id, installment, amount, due_date, status)
            SELECT id, '1st Installment', 110000, CURRENT_DATE + INTERVAL '10 days', 'Pending'
            FROM travelers WHERE passport_no = 'B7654321'
            ON CONFLICT DO NOTHING;
        """)
        
        conn.commit()
        print("✅ Default data inserted successfully")
        
        cur.close()
        conn.close()
        print("🎉 Database initialization COMPLETE! All tables ready.")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def get_db_cursor(dictionary=False):
    """Get database connection and cursor with optional dictionary cursor"""
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

def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """Execute a query with automatic connection handling"""
    conn = get_db()
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        cur.execute(query, params or ())
        
        result = None
        if fetch_one:
            result = cur.fetchone()
        elif fetch_all:
            result = cur.fetchall()
        
        if commit:
            conn.commit()
        
        cur.close()
        conn.close()
        return result
    except Exception as e:
        print(f"❌ Query error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return None

def execute_query_with_dict(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """Execute a query and return results as dictionary"""
    conn = get_db()
    if not conn:
        return None
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params or ())
        
        result = None
        if fetch_one:
            result = cur.fetchone()
        elif fetch_all:
            result = cur.fetchall()
        
        if commit:
            conn.commit()
        
        cur.close()
        conn.close()
        return result
    except Exception as e:
        print(f"❌ Query error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return None

def check_database():
    """Check if all required tables exist"""
    conn = get_db()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # List of required tables
        required_tables = [
            'admin_users', 'roles', 'permissions', 'role_permissions', 'user_roles',
            'batches', 'travelers', 'payments', 'login_logs', 'backups',
            'payment_reversals', 'invoices'
        ]
        
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        existing_tables = [row[0] for row in cur.fetchall()]
        
        missing_tables = []
        for table in required_tables:
            if table not in existing_tables:
                missing_tables.append(table)
        
        if missing_tables:
            print(f"❌ Missing tables: {', '.join(missing_tables)}")
            return False
        else:
            print("✅ All required tables exist!")
            
            # Get counts for verification
            cur.execute("SELECT COUNT(*) FROM admin_users")
            admin_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM batches")
            batch_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM travelers")
            traveler_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM payments")
            payment_count = cur.fetchone()[0]
            
            print(f"📊 Database stats: {admin_count} admins, {batch_count} batches, {traveler_count} travelers, {payment_count} payments")
            return True
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_table_counts():
    """Get counts from all major tables"""
    conn = get_db()
    if not conn:
        return {}
    
    try:
        cur = conn.cursor()
        counts = {}
        
        tables = ['admin_users', 'batches', 'travelers', 'payments', 'login_logs', 'backups']
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        return counts
    except Exception as e:
        print(f"❌ Error getting counts: {e}")
        return {}

def reset_database(confirm=False):
    """WARNING: This will delete all data and recreate tables"""
    if not confirm:
        print("⚠️ This will DELETE ALL DATA! Set confirm=True to proceed.")
        return False
    
    conn = get_db()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Drop all tables in reverse order
        tables = [
            'payment_reversals', 'invoices', 'payments', 'travelers', 
            'batches', 'login_logs', 'backups', 'user_roles', 
            'role_permissions', 'permissions', 'roles', 'admin_users'
        ]
        
        for table in tables:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"✅ Dropped {table}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("🎉 Database reset complete! Now run init_db()")
        return True
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        conn.rollback()
        conn.close()
        return False

# Run initialization if this file is executed directly
if __name__ == "__main__":
    print("🚀 Initializing database...")
    if init_db():
        print("✅ Database initialization successful!")
        check_database()
        counts = get_table_counts()
        print("📊 Table counts:", counts)
    else:
        print("❌ Database initialization failed!")
