import os
import sqlite3
import json
import shutil
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ==================== DATABASE PATH CONFIGURATION ====================
# Support Railway persistent volumes
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Priority 1: Use Railway volume if available (persistent storage)
RAILWAY_VOLUME = os.environ.get('RAILWAY_VOLUME_PATH', '/railway/volume')
PERSISTENT_DB_PATH = os.path.join(RAILWAY_VOLUME, 'alhudha.db')

# Priority 2: Use local SQL directory (may be ephemeral)
LOCAL_DB_PATH = os.path.join(BASE_DIR, 'sql', 'alhudha.db')

# Priority 3: Use temporary directory as last resort
TEMP_DB_PATH = os.path.join('/tmp', 'alhudha.db')

# Choose the best available path
if os.path.exists(RAILWAY_VOLUME) and os.access(RAILWAY_VOLUME, os.W_OK):
    DB_PATH = PERSISTENT_DB_PATH
    print(f"📁 Using persistent volume: {DB_PATH}")
elif os.path.exists(os.path.dirname(LOCAL_DB_PATH)):
    DB_PATH = LOCAL_DB_PATH
    print(f"📁 Using local SQL directory: {DB_PATH}")
else:
    DB_PATH = TEMP_DB_PATH
    print(f"📁 Using temporary storage: {DB_PATH} (WARNING: Data will be lost on restart!)")

# Backup directory
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

# ==================== DATABASE CONNECTION ====================

def get_db():
    """Return SQLite connection with foreign keys enabled and retry logic"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Connection retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=20)  # 20 second timeout
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging for better concurrency
            conn.execute("PRAGMA synchronous = NORMAL")  # Balance safety and performance
            return conn
        except sqlite3.OperationalError as e:
            if 'locked' in str(e) and attempt < max_retries - 1:
                import time
                time.sleep(1)  # Wait and retry
                continue
            raise e
    return None

# ==================== BACKUP FUNCTIONS ====================

def backup_database():
    """Create a timestamped backup of the database"""
    try:
        if not os.path.exists(DB_PATH):
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(BACKUP_DIR, f'alhudha_backup_{timestamp}.db')
        
        # Use SQLite backup API for safe backup
        conn = sqlite3.connect(DB_PATH)
        backup_conn = sqlite3.connect(backup_path)
        conn.backup(backup_conn)
        backup_conn.close()
        conn.close()
        
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def restore_latest_backup():
    """Restore the most recent database backup"""
    try:
        backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('alhudha_backup_')])
        if not backups:
            return False
        
        latest_backup = os.path.join(BACKUP_DIR, backups[-1])
        
        # Close any existing connections
        conn = sqlite3.connect(DB_PATH)
        conn.close()
        
        # Restore backup
        shutil.copy2(latest_backup, DB_PATH)
        print(f"✅ Restored from backup: {latest_backup}")
        return True
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False

# ==================== DATABASE HEALTH CHECK ====================

def check_database_integrity():
    """Run integrity check on database"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == 'ok':
            print("✅ Database integrity check passed")
            return True
        else:
            print("❌ Database integrity check failed")
            return False
    except Exception as e:
        print(f"❌ Integrity check error: {e}")
        return False

# ==================== TABLE CREATION FUNCTIONS ====================

def create_users_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            department TEXT,
            role TEXT DEFAULT 'staff',
            permissions TEXT DEFAULT '{}',
            is_active INTEGER DEFAULT 1,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def create_batches_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_name TEXT NOT NULL,
            total_seats INTEGER DEFAULT 150,
            booked_seats INTEGER DEFAULT 0,
            price REAL,
            departure_date TEXT,
            return_date TEXT,
            status TEXT DEFAULT 'Open',
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            passport_name TEXT,
            batch_id INTEGER,
            passport_no TEXT NOT NULL UNIQUE,
            passport_issue_date TEXT,
            passport_expiry_date TEXT,
            passport_status TEXT DEFAULT 'Active',
            gender TEXT,
            dob TEXT,
            mobile TEXT NOT NULL,
            email TEXT,
            aadhaar TEXT,
            pan TEXT,
            aadhaar_pan_linked TEXT DEFAULT 'No',
            vaccine_status TEXT DEFAULT 'Not Vaccinated',
            wheelchair TEXT DEFAULT 'No',
            place_of_birth TEXT,
            place_of_issue TEXT,
            passport_address TEXT,
            father_name TEXT,
            mother_name TEXT,
            spouse_name TEXT,
            passport_scan TEXT,
            aadhaar_scan TEXT,
            pan_scan TEXT,
            vaccine_scan TEXT,
            photo TEXT,
            pin TEXT DEFAULT '0000',
            emergency_contact TEXT,
            emergency_phone TEXT,
            medical_notes TEXT,
            extra_fields TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (batch_id) REFERENCES batches(id) ON DELETE SET NULL
        )
    """)

def create_payments_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            traveler_id INTEGER NOT NULL,
            batch_id INTEGER NOT NULL,
            installment TEXT,
            amount REAL NOT NULL,
            payment_date TEXT NOT NULL,
            due_date TEXT,
            payment_method TEXT,
            transaction_id TEXT,
            status TEXT DEFAULT 'completed',
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (traveler_id) REFERENCES travelers(id) ON DELETE CASCADE,
            FOREIGN KEY (batch_id) REFERENCES batches(id) ON DELETE CASCADE
        )
    """)

def create_invoices_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            traveler_id INTEGER NOT NULL,
            batch_id INTEGER NOT NULL,
            invoice_date TEXT NOT NULL,
            due_date TEXT,
            base_amount REAL NOT NULL,
            gst_percent REAL DEFAULT 5,
            gst_amount REAL,
            tcs_percent REAL DEFAULT 1,
            tcs_amount REAL,
            total_amount REAL NOT NULL,
            paid_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            hsn_code TEXT DEFAULT '9985',
            place_of_supply TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (traveler_id) REFERENCES travelers(id) ON DELETE CASCADE,
            FOREIGN KEY (batch_id) REFERENCES batches(id) ON DELETE CASCADE
        )
    """)

def create_receipts_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_number TEXT UNIQUE NOT NULL,
            traveler_id INTEGER NOT NULL,
            payment_id INTEGER NOT NULL,
            receipt_date TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT,
            transaction_id TEXT,
            receipt_type TEXT DEFAULT 'payment',
            installment_info TEXT,
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (traveler_id) REFERENCES travelers(id) ON DELETE CASCADE,
            FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE
        )
    """)

def create_activity_log_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            module TEXT,
            description TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

def create_backup_history_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS backup_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            backup_name TEXT NOT NULL,
            backup_type TEXT,
            file_size TEXT,
            tables_count INTEGER,
            status TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

# ==================== SEED DEFAULT USERS ====================

def seed_default_users(cursor):
    """Insert default users if table is empty"""
    existing = cursor.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
    
    if existing == 0:
        default_users = [
            ('superadmin', 'admin123', 'Super Admin', 'super@alhudha.com', 'super_admin'),
            ('admin1', 'admin123', 'Admin User', 'admin@alhudha.com', 'admin'),
            ('manager1', 'admin123', 'Manager User', 'manager@alhudha.com', 'manager')
        ]

        for username, password, name, email, role in default_users:
            cursor.execute("""
                INSERT INTO users (username, password, full_name, email, role)
                VALUES (?, ?, ?, ?, ?)
            """, (username, password, name, email, role))
        
        print("✅ Default users seeded")

# ==================== MAIN INITIALIZATION ====================

def init_db():
    """Initialize database with all tables and seed data"""
    
    # Create backup before initialization if database exists
    if os.path.exists(DB_PATH):
        backup_database()
    
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Create all tables in order (respect foreign keys)
        create_users_table(cursor)
        create_batches_table(cursor)
        create_travelers_table(cursor)
        create_payments_table(cursor)
        create_invoices_table(cursor)
        create_receipts_table(cursor)
        create_activity_log_table(cursor)
        create_backup_history_table(cursor)
        
        # Seed default data
        seed_default_users(cursor)
        
        conn.commit()
        
        # Verify database integrity
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()
        
        if integrity and integrity[0] == 'ok':
            print("✅ Database initialized successfully")
            print(f"📍 Database location: {DB_PATH}")
            print(f"📍 Backup directory: {BACKUP_DIR}")
        else:
            print("⚠️ Database integrity check warning")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

# ==================== AUTO-RECOVERY ON STARTUP ====================

def ensure_database():
    """Ensure database exists and is valid, restore from backup if corrupted"""
    if not os.path.exists(DB_PATH):
        print("📦 Database file not found. Creating new database...")
        init_db()
        return
    
    # Check integrity
    if not check_database_integrity():
        print("⚠️ Database corruption detected! Attempting to restore from backup...")
        if restore_latest_backup():
            if check_database_integrity():
                print("✅ Database restored successfully")
            else:
                print("❌ Backup also corrupted. Creating fresh database...")
                os.remove(DB_PATH)
                init_db()
        else:
            print("❌ No valid backup found. Creating fresh database...")
            os.remove(DB_PATH)
            init_db()
    else:
        print("✅ Database integrity verified")

# ==================== RUN ON IMPORT ====================

# Run database check when module is imported
ensure_database()

# ==================== EXPORTED FUNCTIONS ====================

__all__ = ['get_db', 'init_db', 'backup_database', 'restore_latest_backup', 'check_database_integrity']
