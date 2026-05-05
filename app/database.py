import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

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
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'), cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        return (conn, cursor)  # Returns tuple for compatibility
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return (None, None)

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
            result = cursor.fetchone()
            tables_exist = result['exists'] if result else False
            
            if tables_exist:
                print("✅ Database tables already exist")
                return
            
            print("🚀 Creating database tables...")
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255),
                    email VARCHAR(255) UNIQUE,
                    phone VARCHAR(50),
                    department VARCHAR(100),
                    role VARCHAR(50) DEFAULT 'staff',
                    permissions JSONB DEFAULT '{}',
                    is_active BOOLEAN DEFAULT true,
                    last_login TIMESTAMP,
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
                    installment VARCHAR(100),
                    amount DECIMAL(10,2) NOT NULL,
                    payment_date TIMESTAMP NOT NULL,
                    due_date DATE,
                    payment_method VARCHAR(50),
                    transaction_id VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'completed',
                    remarks TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create invoices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id SERIAL PRIMARY KEY,
                    invoice_number VARCHAR(100) UNIQUE NOT NULL,
                    traveler_id INTEGER REFERENCES travelers(id) ON DELETE CASCADE,
                    batch_id INTEGER REFERENCES batches(id) ON DELETE CASCADE,
                    invoice_date TIMESTAMP NOT NULL,
                    due_date DATE,
                    base_amount DECIMAL(10,2) NOT NULL,
                    gst_percent DECIMAL(5,2) DEFAULT 5,
                    gst_amount DECIMAL(10,2),
                    tcs_percent DECIMAL(5,2) DEFAULT 1,
                    tcs_amount DECIMAL(10,2),
                    total_amount DECIMAL(10,2) NOT NULL,
                    paid_amount DECIMAL(10,2) DEFAULT 0,
                    status VARCHAR(50) DEFAULT 'pending',
                    hsn_code VARCHAR(20) DEFAULT '9985',
                    place_of_supply VARCHAR(100),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create receipts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS receipts (
                    id SERIAL PRIMARY KEY,
                    receipt_number VARCHAR(100) UNIQUE NOT NULL,
                    traveler_id INTEGER REFERENCES travelers(id) ON DELETE CASCADE,
                    payment_id INTEGER REFERENCES payments(id) ON DELETE CASCADE,
                    receipt_date TIMESTAMP NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    payment_method VARCHAR(50),
                    transaction_id VARCHAR(100),
                    receipt_type VARCHAR(50) DEFAULT 'payment',
                    installment_info VARCHAR(255),
                    remarks TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create company_settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company_settings (
                    id SERIAL PRIMARY KEY,
                    legal_name TEXT NOT NULL,
                    display_name TEXT,
                    address_line1 TEXT,
                    address_line2 TEXT,
                    city TEXT,
                    state TEXT,
                    country TEXT DEFAULT 'India',
                    pin_code TEXT,
                    phone TEXT,
                    mobile TEXT,
                    email TEXT,
                    website TEXT,
                    gstin TEXT,
                    pan TEXT,
                    tan TEXT,
                    tcs_no TEXT,
                    tin TEXT,
                    cin TEXT,
                    iec TEXT,
                    msme TEXT,
                    bank_name TEXT,
                    bank_branch TEXT,
                    account_name TEXT,
                    account_no TEXT,
                    ifsc_code TEXT,
                    micr_code TEXT,
                    upi_id TEXT,
                    qr_code TEXT,
                    logo TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create frontpage_settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS frontpage_settings (
                    id SERIAL PRIMARY KEY,
                    hero_heading TEXT,
                    hero_subheading TEXT,
                    hero_button_text TEXT,
                    hero_button_link TEXT,
                    hero_color1 TEXT DEFAULT '#1e3c72',
                    hero_color2 TEXT DEFAULT '#3498db',
                    packages_title TEXT DEFAULT 'Our Haj & Umrah Packages',
                    footer_text TEXT,
                    footer_phone TEXT,
                    footer_email TEXT,
                    facebook_url TEXT,
                    twitter_url TEXT,
                    instagram_url TEXT,
                    font_family TEXT DEFAULT "'Segoe UI', sans-serif",
                    primary_color TEXT DEFAULT '#3498db',
                    secondary_color TEXT DEFAULT '#27ae60',
                    alert_enabled BOOLEAN DEFAULT false,
                    alert_message TEXT,
                    alert_link TEXT,
                    alert_color TEXT DEFAULT '#f39c12',
                    alert_style TEXT DEFAULT 'pulse',
                    alert_start_date DATE,
                    alert_end_date DATE,
                    whatsapp_number TEXT,
                    whatsapp_message TEXT,
                    booking_email TEXT,
                    email_subject TEXT,
                    whatsapp_enabled BOOLEAN DEFAULT true,
                    email_enabled BOOLEAN DEFAULT true,
                    packages JSONB DEFAULT '[]',
                    features JSONB DEFAULT '[]',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create whatsapp_settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS whatsapp_settings (
                    id SERIAL PRIMARY KEY,
                    number TEXT,
                    message_template TEXT,
                    enabled BOOLEAN DEFAULT true,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create email_settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_settings (
                    id SERIAL PRIMARY KEY,
                    smtp_server TEXT,
                    smtp_port INTEGER,
                    encryption TEXT,
                    from_email TEXT,
                    reply_to TEXT,
                    subject_prefix TEXT,
                    enabled BOOLEAN DEFAULT true,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create backup_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backup_history (
                    id SERIAL PRIMARY KEY,
                    backup_name TEXT NOT NULL,
                    backup_type TEXT DEFAULT 'manual',
                    file_size TEXT,
                    tables_count INTEGER,
                    status TEXT DEFAULT 'completed',
                    location TEXT DEFAULT 'local',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create activity_log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    action TEXT NOT NULL,
                    module TEXT,
                    description TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default users
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()['count']
            
            if count == 0:
                print("👤 Creating default users...")
                users = [
                    ('superadmin', 'admin123', 'Super Admin', 'super@alhudha.com', '9999999999', 'Management', 'super_admin', '{}'),
                    ('admin1', 'admin123', 'Admin User', 'admin@alhudha.com', '8888888888', 'Operations', 'admin', '{}'),
                    ('manager1', 'admin123', 'Manager User', 'manager@alhudha.com', '7777777777', 'Sales', 'manager', '{}'),
                    ('staff1', 'admin123', 'Staff User', 'staff@alhudha.com', '6666666666', 'Customer Service', 'staff', '{}'),
                    ('viewer1', 'admin123', 'Viewer User', 'viewer@alhudha.com', '5555555555', 'Accounts', 'viewer', '{}')
                ]
                
                for user in users:
                    cursor.execute("""
                        INSERT INTO users (username, password, full_name, email, phone, department, role, permissions)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, user)
                
                print("✅ Default users created")
            
            # Insert sample batches
            cursor.execute("SELECT COUNT(*) FROM batches")
            if cursor.fetchone()['count'] == 0:
                print("📦 Creating sample batches...")
                batches = [
                    ('Haj Platinum 2026', 50, 850000, '2026-06-14', '2026-07-31', 'Open', 'Premium Haj package with 5-star accommodation', '', '', '', '', '', ''),
                    ('Haj Gold 2026', 100, 550000, '2026-06-15', '2026-07-30', 'Open', 'Standard Haj package with 4-star accommodation', '', '', '', '', '', ''),
                    ('Umrah Ramadhan Special', 200, 125000, '2026-03-01', '2026-03-20', 'Closing Soon', 'Special Umrah package', '', '', '', '', '', ''),
                    ('Haj Silver 2026', 150, 350000, '2026-06-20', '2026-07-28', 'Open', 'Economy Haj package', '', '', '', '', '', '')
                ]
                
                for batch in batches:
                    cursor.execute("""
                        INSERT INTO batches (batch_name, total_seats, price, departure_date, return_date, status, description, itinerary, inclusions, exclusions, hotel_details, transport_details, meal_plan)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, batch)
                
                print("✅ Sample batches created")
            
            # Insert sample travelers
            cursor.execute("SELECT COUNT(*) FROM travelers")
            if cursor.fetchone()['count'] == 0:
                print("🛂 Creating sample travelers...")
                travelers = [
                    ('Ahmed', 'Khan', 'Ahmed Khan', 1, 'A1234567', '2020-01-15', '2030-01-14', 'Active', 'Male', '1985-06-15',
                     '9876543210', 'ahmed@email.com', '1234-5678-9012', 'ABCDE1234F', 'Yes', 'Fully Vaccinated', 'No',
                     'Mumbai', 'Mumbai', '123, Green Street, Mumbai', 'Abdullah Khan', 'Amina Khan', 'N/A',
                     None, None, None, None, None, '1234', 'Brother', '9876543211', 'No known allergies'),
                    ('Fatima', 'Begum', 'Fatima Begum', 2, 'B7654321', '2019-08-20', '2029-08-19', 'Active', 'Female', '1990-11-22',
                     '8765432109', 'fatima@email.com', '2345-6789-0123', 'FGHIJ5678K', 'Pending', 'Partially Vaccinated', 'No',
                     'Delhi', 'Delhi', '456, Lotus Apartments, Delhi', 'Mohammed Ali', 'Zainab Ali', 'Hasan Raza',
                     None, None, None, None, None, '5678', 'Husband', '8765432100', 'Diabetic')
                ]
                
                for traveler in travelers:
                    cursor.execute("""
                        INSERT INTO travelers (
                            first_name, last_name, passport_name, batch_id, passport_no, passport_issue_date,
                            passport_expiry_date, passport_status, gender, dob, mobile, email, aadhaar, pan,
                            aadhaar_pan_linked, vaccine_status, wheelchair, place_of_birth, place_of_issue,
                            passport_address, father_name, mother_name, spouse_name, passport_scan, aadhaar_scan,
                            pan_scan, vaccine_scan, photo, pin, emergency_contact, emergency_phone, medical_notes
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, traveler)
                
                print("✅ Sample travelers created")
            
            print("✅ Database initialization complete")
            
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        raise e

if __name__ == "__main__":
    init_db()