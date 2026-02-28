import os
import sqlite3
import json
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'sql', 'alhudha.db')


# ==================== DATABASE CONNECTION ====================

def get_db():
    """Return SQLite connection with foreign keys enabled"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ==================== INITIALIZE DATABASE ====================

def init_db():
    """Create tables if they do not exist (SAFE MODE)"""

    conn = get_db()
    cursor = conn.cursor()

    # ==================== USERS ====================
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

    # ==================== BATCHES ====================
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

    # ==================== TRAVELERS ====================
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

    # ==================== PAYMENTS ====================
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

    # ==================== INVOICES ====================
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

    # ==================== RECEIPTS ====================
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

    # ==================== ACTIVITY LOG ====================
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

    conn.commit()

    # ==================== SEED DEFAULT USERS IF EMPTY ====================
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

        conn.commit()
        print("✅ Default users seeded")

    conn.close()
    print("✅ Database initialized safely (NO DATA LOSS)")
