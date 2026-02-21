import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sql', 'alhudha.db')

def get_db():
    """Get database connection"""
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            email TEXT UNIQUE,
            role TEXT DEFAULT 'admin',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create batches table
    cursor.execute('''
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create travelers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS travelers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            passport_name TEXT,
            batch_id INTEGER,
            passport_no TEXT NOT NULL,
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
            extra_fields TEXT,
            pin TEXT DEFAULT '0000',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (batch_id) REFERENCES batches (id)
        )
    ''')
    
    # Create payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            traveler_id INTEGER NOT NULL,
            batch_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date TEXT NOT NULL,
            payment_method TEXT,
            transaction_id TEXT,
            status TEXT DEFAULT 'completed',
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (traveler_id) REFERENCES travelers (id),
            FOREIGN KEY (batch_id) REFERENCES batches (id)
        )
    ''')
    
    # Insert default users
    users = [
        ('superadmin', 'admin123', 'Super Admin', 'super@alhudha.com', 'super_admin'),
        ('admin1', 'admin123', 'Admin User', 'admin@alhudha.com', 'admin'),
        ('manager1', 'admin123', 'Manager User', 'manager@alhudha.com', 'manager')
    ]
    
    for username, password, name, email, role in users:
        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (username, password, name, email, role) VALUES (?, ?, ?, ?, ?)",
                (username, password, name, email, role)
            )
    
    # Insert sample batches
    batches = [
        ('Haj Platinum 2026', 50, 850000, '2026-06-14', '2026-07-31', 'Open', 'Premium Haj package with 5-star accommodation'),
        ('Haj Gold 2026', 100, 550000, '2026-06-15', '2026-07-30', 'Open', 'Standard Haj package with 4-star accommodation'),
        ('Umrah Ramadhan Special', 200, 125000, '2026-03-01', '2026-03-20', 'Closing Soon', 'Special Umrah package for Ramadhan'),
        ('Haj Silver 2026', 150, 350000, '2026-06-20', '2026-07-28', 'Open', 'Economy Haj package')
    ]
    
    for name, seats, price, dep, ret, status, desc in batches:
        cursor.execute(
            "SELECT * FROM batches WHERE batch_name = ?",
            (name,)
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO batches (batch_name, total_seats, price, departure_date, return_date, status, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, seats, price, dep, ret, status, desc)
            )
    
    # Insert sample travelers
    travelers = [
        ('Ahmed', 'Khan', 1, 'A1234567', '9876543210', 'ahmed@email.com', 'Male', 'Active', '1234'),
        ('Fatima', 'Begum', 2, 'B7654321', '8765432109', 'fatima@email.com', 'Female', 'Active', '5678'),
        ('Mohammed', 'Rafiq', 3, 'C9876543', '7654321098', 'rafiq@email.com', 'Male', 'Active', '9012')
    ]
    
    for first, last, batch, passport, mobile, email, gender, status, pin in travelers:
        cursor.execute(
            "SELECT * FROM travelers WHERE passport_no = ?",
            (passport,)
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO travelers (first_name, last_name, batch_id, passport_no, mobile, email, gender, passport_status, pin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (first, last, batch, passport, mobile, email, gender, status, pin)
            )
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully with sample data")
