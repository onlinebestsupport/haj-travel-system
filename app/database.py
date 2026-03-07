import os
import psycopg2
import psycopg2.extras
from datetime import datetime
import json
import threading
import time
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()

# ==================== DATABASE CONFIGURATION ====================
DATABASE_URL = os.environ.get('DATABASE_URL')

# Optional: explicitly set SSL mode via environment variable.
# Accepted values: 'require', 'verify-ca', 'verify-full', 'prefer', 'allow', 'disable'
# Defaults to 'require' when connecting to a public Railway host (*.up.railway.app)
# because the postgres-ssl Railway image mandates SSL on public connections.
DATABASE_SSL_MODE = os.environ.get('DATABASE_SSL_MODE', '')

if not DATABASE_URL:
    print("⚠️  WARNING: DATABASE_URL environment variable is not set. Database operations will fail.")
else:
    # Railway (and some other providers) supply postgres:// but psycopg2 requires postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    try:
        _parsed = urlparse(DATABASE_URL)
        _hostname = _parsed.hostname or ''
        print(f"📡 Connecting to database: {_hostname if _hostname else 'unknown'}")

        # Add sslmode to the URL when it is not already present as a query parameter.
        # Public Railway PostgreSQL hosts (*.up.railway.app) require SSL;
        # the postgres-ssl image enforces this on every public connection.
        _query_params = parse_qs(_parsed.query)
        if 'sslmode' not in _query_params:
            _ssl_mode = DATABASE_SSL_MODE or (
                'require' if _hostname.endswith('.up.railway.app') else ''
            )
            if _ssl_mode:
                _sep = '&' if _parsed.query else '?'
                DATABASE_URL = f"{DATABASE_URL}{_sep}sslmode={_ssl_mode}"
                print(f"🔒 SSL mode set to '{_ssl_mode}' for database connection")
    except Exception:
        print("📡 Connecting to database: (URL parsing failed)")

# Global flags to prevent double initialization
_INITIALIZED = False
_INITIALIZING = False
_init_lock = threading.Lock()

# ==================== DATABASE CONNECTION ====================

def get_db():
    """Get PostgreSQL database connection"""
    if not DATABASE_URL:
        raise RuntimeError("❌ DATABASE_URL environment variable is not set. Please configure it in your environment.")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        return conn, cursor
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise e

# ==================== 🔥 ADD MISSING release_db FUNCTION ====================
def release_db(conn=None, cursor=None):
    """🔥 Release database connection back to pool / close it"""
    if cursor:
        try:
            cursor.close()
        except:
            pass
    if conn:
        try:
            conn.close()
        except:
            pass

# ==================== TABLE CREATION FUNCTIONS ====================

def create_users_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            email VARCHAR(255) UNIQUE,
            phone VARCHAR(50),
            department VARCHAR(255),
            role VARCHAR(50) DEFAULT 'staff',
            permissions JSONB DEFAULT '{}',
            is_active BOOLEAN DEFAULT TRUE,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def create_batches_table(cursor):
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

def create_travelers_table(cursor):
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

def create_payments_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            traveler_id INTEGER NOT NULL REFERENCES travelers(id) ON DELETE CASCADE,
            batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
            installment VARCHAR(255),
            amount DECIMAL(10,2) NOT NULL,
            payment_date DATE NOT NULL,
            due_date DATE,
            payment_method VARCHAR(100),
            transaction_id VARCHAR(255),
            status VARCHAR(50) DEFAULT 'completed',
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def create_invoices_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id SERIAL PRIMARY KEY,
            invoice_number VARCHAR(255) UNIQUE NOT NULL,
            traveler_id INTEGER NOT NULL REFERENCES travelers(id) ON DELETE CASCADE,
            batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
            invoice_date DATE NOT NULL,
            due_date DATE,
            base_amount DECIMAL(10,2) NOT NULL,
            gst_percent DECIMAL(5,2) DEFAULT 5,
            gst_amount DECIMAL(10,2),
            tcs_percent DECIMAL(5,2) DEFAULT 1,
            tcs_amount DECIMAL(10,2),
            total_amount DECIMAL(10,2) NOT NULL,
            paid_amount DECIMAL(10,2) DEFAULT 0,
            status VARCHAR(50) DEFAULT 'pending',
            hsn_code VARCHAR(50) DEFAULT '9985',
            place_of_supply VARCHAR(255),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def create_receipts_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id SERIAL PRIMARY KEY,
            receipt_number VARCHAR(255) UNIQUE NOT NULL,
            traveler_id INTEGER NOT NULL REFERENCES travelers(id) ON DELETE CASCADE,
            payment_id INTEGER NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
            invoice_id INTEGER REFERENCES invoices(id) ON DELETE SET NULL,
            receipt_date DATE NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            payment_method VARCHAR(100),
            transaction_id VARCHAR(255),
            receipt_type VARCHAR(50) DEFAULT 'payment',
            installment_info TEXT,
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def create_activity_log_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            action VARCHAR(255) NOT NULL,
            module VARCHAR(255),
            description TEXT,
            ip_address VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def create_critical_logs_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS critical_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            action VARCHAR(255) NOT NULL,
            description TEXT,
            ip_address VARCHAR(50),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def create_backup_history_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS backup_history (
            id SERIAL PRIMARY KEY,
            backup_name VARCHAR(255) NOT NULL,
            backup_type VARCHAR(50) DEFAULT 'manual',
            file_size VARCHAR(50),
            tables_count INTEGER,
            status VARCHAR(50) DEFAULT 'completed',
            location VARCHAR(255),
            description TEXT,
            is_restore_point BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER REFERENCES users(id) ON DELETE SET NULL
        )
    """)

def create_backup_settings_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS backup_settings (
            id SERIAL PRIMARY KEY,
            schedule VARCHAR(50) DEFAULT 'weekly',
            retention_days INTEGER DEFAULT 30,
            location VARCHAR(50) DEFAULT 'both',
            compression VARCHAR(50) DEFAULT 'normal',
            encryption VARCHAR(50) DEFAULT 'aes256',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER REFERENCES users(id)
        )
    """)
    
    cursor.execute("""
        INSERT INTO backup_settings (id, schedule, retention_days, location, compression, encryption)
        VALUES (1, 'weekly', 30, 'both', 'normal', 'aes256')
        ON CONFLICT (id) DO NOTHING
    """)

def create_frontpage_settings_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frontpage_settings (
            id SERIAL PRIMARY KEY,
            hero_heading VARCHAR(255),
            hero_subheading TEXT,
            hero_button_text VARCHAR(100),
            hero_button_link VARCHAR(255),
            packages_title VARCHAR(255),
            footer_text TEXT,
            footer_phone VARCHAR(50),
            footer_email VARCHAR(255),
            facebook_url VARCHAR(255),
            twitter_url VARCHAR(255),
            instagram_url VARCHAR(255),
            alert_enabled BOOLEAN DEFAULT FALSE,
            alert_message TEXT,
            alert_link VARCHAR(255),
            alert_color VARCHAR(50),
            alert_style VARCHAR(50),
            whatsapp_number VARCHAR(50),
            whatsapp_message TEXT,
            booking_email VARCHAR(255),
            email_subject VARCHAR(255),
            whatsapp_enabled BOOLEAN DEFAULT FALSE,
            email_enabled BOOLEAN DEFAULT FALSE,
            packages JSONB DEFAULT '[]',
            features JSONB DEFAULT '[]',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        INSERT INTO frontpage_settings (id, hero_heading, hero_subheading, footer_text)
        VALUES (1, 'Welcome to Alhudha Haj Travel', 'Your trusted partner for Haj and Umrah', '© 2026 Alhudha Haj Travel')
        ON CONFLICT (id) DO NOTHING
    """)

def create_email_settings_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_settings (
            id SERIAL PRIMARY KEY,
            from_email VARCHAR(255),
            reply_to VARCHAR(255),
            subject_prefix VARCHAR(255),
            smtp_server VARCHAR(255),
            smtp_port INTEGER,
            smtp_username VARCHAR(255),
            smtp_password VARCHAR(255),
            use_tls BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        INSERT INTO email_settings (id, from_email, reply_to, subject_prefix)
        VALUES (1, 'noreply@alhudha.com', 'info@alhudha.com', '[Alhudha Haj]')
        ON CONFLICT (id) DO NOTHING
    """)

def create_whatsapp_settings_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS whatsapp_settings (
            id SERIAL PRIMARY KEY,
            number VARCHAR(50),
            message_template TEXT,
            api_key VARCHAR(255),
            api_url VARCHAR(255),
            enabled BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        INSERT INTO whatsapp_settings (id, number, message_template, enabled)
        VALUES (1, '+919876543210', 'Hello! Thank you for contacting Alhudha Haj Travel. How can we help you?', false)
        ON CONFLICT (id) DO NOTHING
    """)

def create_company_settings_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_settings (
            id SERIAL PRIMARY KEY,
            legal_name VARCHAR(255),
            display_name VARCHAR(255),
            address_line1 VARCHAR(255),
            address_line2 VARCHAR(255),
            city VARCHAR(100),
            state VARCHAR(100),
            country VARCHAR(100),
            pin_code VARCHAR(20),
            phone VARCHAR(50),
            mobile VARCHAR(50),
            email VARCHAR(255),
            website VARCHAR(255),
            gstin VARCHAR(50),
            pan VARCHAR(50),
            tan VARCHAR(50),
            tcs_no VARCHAR(50),
            tin VARCHAR(50),
            cin VARCHAR(50),
            iec VARCHAR(50),
            msme VARCHAR(50),
            bank_name VARCHAR(255),
            bank_branch VARCHAR(255),
            account_name VARCHAR(255),
            account_no VARCHAR(100),
            ifsc_code VARCHAR(50),
            micr_code VARCHAR(50),
            upi_id VARCHAR(100),
            qr_code TEXT,
            logo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        INSERT INTO company_settings (id, legal_name, display_name, country)
        VALUES (1, 'Alhudha Haj Service P Ltd.', 'Alhudha Haj Travel', 'India')
        ON CONFLICT (id) DO NOTHING
    """)

# ==================== SEED DEFAULT USERS ====================

def seed_default_users(conn, cursor):
    """Insert default users if table is empty"""
    cursor.execute("SELECT COUNT(*) as count FROM users")
    result = cursor.fetchone()
    
    if result['count'] == 0:
        default_users = [
            ('superadmin', 'admin123', 'Super Admin', 'super@alhudha.com', 'super_admin'),
            ('admin1', 'admin123', 'Admin User', 'admin@alhudha.com', 'admin'),
            ('manager1', 'admin123', 'Manager User', 'manager@alhudha.com', 'manager'),
            ('staff1', 'admin123', 'Staff User', 'staff@alhudha.com', 'staff'),
            ('viewer1', 'admin123', 'Viewer User', 'viewer@alhudha.com', 'viewer')
        ]

        for username, password, name, email, role in default_users:
            cursor.execute("""
                INSERT INTO users (username, password, full_name, email, role, permissions)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, password, name, email, role, '{}'))
        
        conn.commit()
        print("✅ Default users seeded")

# ==================== MIGRATION FUNCTIONS ====================

def migrate_receipts_table():
    """Add invoice_id column to receipts table if not exists"""
    conn, cursor = get_db()
    try:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='receipts' AND column_name='invoice_id'
        """)
        result = cursor.fetchone()
        
        if not result:
            cursor.execute("""
                ALTER TABLE receipts 
                ADD COLUMN invoice_id INTEGER 
                REFERENCES invoices(id) ON DELETE SET NULL
            """)
            conn.commit()
            print("✅ Added invoice_id column to receipts table")
        else:
            print("✅ invoice_id column already exists")
            
    except Exception as e:
        print(f"⚠️ Migration error: {e}")
        conn.rollback()
    finally:
        release_db(conn, cursor)

# ==================== MAIN INITIALIZATION ====================

def init_db():
    """Initialize database with all tables and seed data"""
    global _INITIALIZED, _INITIALIZING
    
    with _init_lock:
        if _INITIALIZED:
            print("✅ Database already initialized, skipping...")
            return True
        
        if _INITIALIZING:
            print("⏳ Database initialization already in progress, waiting...")
            for i in range(30):
                if _INITIALIZED:
                    return True
                time.sleep(1)
            print("⚠️ Initialization timeout, continuing...")
            return False
        
        _INITIALIZING = True
    
    conn = None
    cursor = None
    
    try:
        print("🚀 Starting database initialization...")
        conn, cursor = get_db()
        
        create_users_table(cursor)
        create_batches_table(cursor)
        create_travelers_table(cursor)
        create_payments_table(cursor)
        create_invoices_table(cursor)
        create_receipts_table(cursor)
        create_activity_log_table(cursor)
        create_critical_logs_table(cursor)
        create_backup_history_table(cursor)
        create_backup_settings_table(cursor)
        create_frontpage_settings_table(cursor)
        create_email_settings_table(cursor)
        create_whatsapp_settings_table(cursor)
        create_company_settings_table(cursor)
        
        conn.commit()
        print("✅ All tables created")
        
        seed_default_users(conn, cursor)
        migrate_receipts_table()
        
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL connected: {version['version'][:50]}...")
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables_count = cursor.fetchone()['count']
        print(f"📊 Tables created: {tables_count}")
        
        with _init_lock:
            _INITIALIZED = True
            _INITIALIZING = False
        
        print("✅ Database initialization complete")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        with _init_lock:
            _INITIALIZING = False
        return False
        
    finally:
        release_db(conn, cursor)

# ==================== HELPER FUNCTIONS ====================

def execute_query(query, params=None):
    """Execute a query and return results"""
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute(query, params or ())
        if query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
            return results
        else:
            conn.commit()
            return cursor.rowcount
    finally:
        release_db(conn, cursor)

def get_table_counts():
    """Get count of records in all tables"""
    conn, cursor = get_db()
    try:
        tables = ['users', 'batches', 'travelers', 'payments', 'invoices', 'receipts', 'backup_history']
        counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            result = cursor.fetchone()
            counts[table] = result['count'] if result else 0
        return counts
    finally:
        release_db(conn, cursor)

def get_backup_settings():
    """Get backup settings"""
    conn, cursor = get_db()
    try:
        cursor.execute("SELECT * FROM backup_settings WHERE id = 1")
        settings = cursor.fetchone()
        return dict(settings) if settings else None
    finally:
        release_db(conn, cursor)

def update_backup_settings(schedule, retention_days, location, compression, encryption, updated_by):
    """Update backup settings"""
    conn, cursor = get_db()
    try:
        cursor.execute("""
            UPDATE backup_settings SET
                schedule = %s,
                retention_days = %s,
                location = %s,
                compression = %s,
                encryption = %s,
                updated_at = %s,
                updated_by = %s
            WHERE id = 1
        """, (schedule, retention_days, location, compression, encryption, datetime.now(), updated_by))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating backup settings: {e}")
        conn.rollback()
        return False
    finally:
        release_db(conn, cursor)

# ==================== EXPORTED FUNCTIONS ====================

__all__ = [
    'get_db', 
    'release_db',  # 🔥 NOW INCLUDED
    'init_db', 
    'execute_query', 
    'get_table_counts', 
    'migrate_receipts_table',
    'get_backup_settings',
    'update_backup_settings'
]
