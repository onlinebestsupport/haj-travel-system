import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sql', 'alhudha.db')

def get_db():
    """Get SQLite database connection"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables with all required fields"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Drop existing tables if they exist (comment out if you want to preserve data)
    cursor.execute('DROP TABLE IF EXISTS payments')
    cursor.execute('DROP TABLE IF EXISTS receipts')
    cursor.execute('DROP TABLE IF EXISTS invoices')
    cursor.execute('DROP TABLE IF EXISTS travelers')
    cursor.execute('DROP TABLE IF EXISTS batches')
    cursor.execute('DROP TABLE IF EXISTS users')
    cursor.execute('DROP TABLE IF EXISTS company_settings')
    cursor.execute('DROP TABLE IF EXISTS frontpage_settings')
    cursor.execute('DROP TABLE IF EXISTS whatsapp_settings')
    cursor.execute('DROP TABLE IF EXISTS email_settings')
    cursor.execute('DROP TABLE IF EXISTS backup_history')
    cursor.execute('DROP TABLE IF EXISTS activity_log')
    
    # Create users table (enhanced with permissions)
    cursor.execute('''
        CREATE TABLE users (
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
    ''')
    
    # Create batches table (enhanced)
    cursor.execute('''
        CREATE TABLE batches (
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
    ''')
    
    # Create travelers table (ALL 33 FIELDS + more)
    cursor.execute('''
        CREATE TABLE travelers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- Personal Information (10 fields)
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
            
            -- Contact Information (7 fields)
            mobile TEXT NOT NULL,
            email TEXT,
            aadhaar TEXT,
            pan TEXT,
            aadhaar_pan_linked TEXT DEFAULT 'No',
            vaccine_status TEXT DEFAULT 'Not Vaccinated',
            wheelchair TEXT DEFAULT 'No',
            
            -- Address & Family (7 fields)
            place_of_birth TEXT,
            place_of_issue TEXT,
            passport_address TEXT,
            father_name TEXT,
            mother_name TEXT,
            spouse_name TEXT,
            
            -- Document Uploads (5 fields)
            passport_scan TEXT,
            aadhaar_scan TEXT,
            pan_scan TEXT,
            vaccine_scan TEXT,
            photo TEXT,
            
            -- Additional Information (4 fields)
            pin TEXT DEFAULT '0000',
            emergency_contact TEXT,
            emergency_phone TEXT,
            medical_notes TEXT,
            
            -- Extra fields (JSON for flexibility)
            extra_fields TEXT DEFAULT '{}',
            
            -- Metadata
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (batch_id) REFERENCES batches (id) ON DELETE SET NULL
        )
    ''')
    
    # Create payments table (enhanced)
    cursor.execute('''
        CREATE TABLE payments (
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
            FOREIGN KEY (traveler_id) REFERENCES travelers (id) ON DELETE CASCADE,
            FOREIGN KEY (batch_id) REFERENCES batches (id) ON DELETE CASCADE
        )
    ''')
    
    # Create invoices table
    cursor.execute('''
        CREATE TABLE invoices (
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
            FOREIGN KEY (traveler_id) REFERENCES travelers (id) ON DELETE CASCADE,
            FOREIGN KEY (batch_id) REFERENCES batches (id) ON DELETE CASCADE
        )
    ''')
    
    # Create receipts table
    cursor.execute('''
        CREATE TABLE receipts (
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
            FOREIGN KEY (traveler_id) REFERENCES travelers (id) ON DELETE CASCADE,
            FOREIGN KEY (payment_id) REFERENCES payments (id) ON DELETE CASCADE
        )
    ''')
    
    # Create company_settings table (COMPREHENSIVE)
    cursor.execute('''
        CREATE TABLE company_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            -- Company Details
            legal_name TEXT NOT NULL,
            display_name TEXT,
            
            -- Address
            address_line1 TEXT,
            address_line2 TEXT,
            city TEXT,
            state TEXT,
            country TEXT DEFAULT 'India',
            pin_code TEXT,
            
            -- Contact
            phone TEXT,
            mobile TEXT,
            email TEXT,
            website TEXT,
            
            -- Tax Information
            gstin TEXT,
            pan TEXT,
            tan TEXT,
            tcs_no TEXT,
            tin TEXT,
            cin TEXT,
            iec TEXT,
            msme TEXT,
            
            -- Bank Details
            bank_name TEXT,
            bank_branch TEXT,
            account_name TEXT,
            account_no TEXT,
            ifsc_code TEXT,
            micr_code TEXT,
            upi_id TEXT,
            qr_code TEXT,
            
            -- Logo
            logo TEXT,
            
            -- Metadata
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create frontpage_settings table
    cursor.execute('''
        CREATE TABLE frontpage_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            -- Hero Section
            hero_heading TEXT,
            hero_subheading TEXT,
            hero_button_text TEXT,
            hero_button_link TEXT,
            hero_color1 TEXT DEFAULT '#1e3c72',
            hero_color2 TEXT DEFAULT '#3498db',
            
            -- Packages Section
            packages_title TEXT DEFAULT 'Our Haj & Umrah Packages',
            
            -- Footer
            footer_text TEXT,
            footer_phone TEXT,
            footer_email TEXT,
            
            -- Social Links
            facebook_url TEXT,
            twitter_url TEXT,
            instagram_url TEXT,
            
            -- Global Settings
            font_family TEXT DEFAULT "'Segoe UI', sans-serif",
            primary_color TEXT DEFAULT '#3498db',
            secondary_color TEXT DEFAULT '#27ae60',
            
            -- Urgent Alert
            alert_enabled INTEGER DEFAULT 0,
            alert_message TEXT,
            alert_link TEXT,
            alert_color TEXT DEFAULT '#f39c12',
            alert_style TEXT DEFAULT 'pulse',
            alert_start_date TEXT,
            alert_end_date TEXT,
            
            -- Contact Settings
            whatsapp_number TEXT,
            whatsapp_message TEXT,
            booking_email TEXT,
            email_subject TEXT,
            whatsapp_enabled INTEGER DEFAULT 1,
            email_enabled INTEGER DEFAULT 1,
            
            -- Packages (JSON)
            packages TEXT DEFAULT '[]',
            features TEXT DEFAULT '[]',
            
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create whatsapp_settings table
    cursor.execute('''
        CREATE TABLE whatsapp_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            number TEXT,
            message_template TEXT,
            enabled INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create email_settings table
    cursor.execute('''
        CREATE TABLE email_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            smtp_server TEXT,
            smtp_port INTEGER,
            encryption TEXT,
            from_email TEXT,
            reply_to TEXT,
            subject_prefix TEXT,
            enabled INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create backup_history table
    cursor.execute('''
        CREATE TABLE backup_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            backup_name TEXT NOT NULL,
            backup_type TEXT DEFAULT 'manual',
            file_size TEXT,
            tables_count INTEGER,
            status TEXT DEFAULT 'completed',
            location TEXT DEFAULT 'local',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create activity_log table
    cursor.execute('''
        CREATE TABLE activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            module TEXT,
            description TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        )
    ''')
    
    # Insert default users with permissions
    users = [
        ('superadmin', 'admin123', 'Super Admin', 'super@alhudha.com', '9999999999', 'Management', 'super_admin', 
         json.dumps({
             'dashboard': True, 'batches': True, 'travelers': True, 'payments': True, 'invoices': True,
             'receipts': True, 'reports': True, 'users': True, 'frontpage': True, 'whatsapp': True,
             'email': True, 'backup': True, 'settings': True
         })),
        ('admin1', 'admin123', 'Admin User', 'admin@alhudha.com', '8888888888', 'Operations', 'admin',
         json.dumps({
             'dashboard': True, 'batches': True, 'travelers': True, 'payments': True, 'invoices': True,
             'receipts': True, 'reports': True, 'users': False, 'frontpage': False, 'whatsapp': True,
             'email': True, 'backup': False, 'settings': False
         })),
        ('manager1', 'admin123', 'Manager User', 'manager@alhudha.com', '7777777777', 'Sales', 'manager',
         json.dumps({
             'dashboard': True, 'batches': True, 'travelers': True, 'payments': True, 'invoices': True,
             'receipts': True, 'reports': True, 'users': False, 'frontpage': False, 'whatsapp': False,
             'email': False, 'backup': False, 'settings': False
         })),
        ('staff1', 'admin123', 'Staff User', 'staff@alhudha.com', '6666666666', 'Customer Service', 'staff',
         json.dumps({
             'dashboard': True, 'batches': False, 'travelers': True, 'payments': True, 'invoices': False,
             'receipts': True, 'reports': False, 'users': False, 'frontpage': False, 'whatsapp': False,
             'email': False, 'backup': False, 'settings': False
         })),
        ('viewer1', 'admin123', 'Viewer User', 'viewer@alhudha.com', '5555555555', 'Accounts', 'viewer',
         json.dumps({
             'dashboard': True, 'batches': True, 'travelers': True, 'payments': True, 'invoices': True,
             'receipts': True, 'reports': True, 'users': False, 'frontpage': False, 'whatsapp': False,
             'email': False, 'backup': False, 'settings': False
         }))
    ]
    
    for username, password, name, email, phone, dept, role, perms in users:
        cursor.execute(
            "INSERT INTO users (username, password, full_name, email, phone, department, role, permissions) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (username, password, name, email, phone, dept, role, perms)
        )
    
    # Insert sample batches
    batches = [
        ('Haj Platinum 2026', 50, 850000, '2026-06-14', '2026-07-31', 'Open', 
         'Premium Haj package with 5-star accommodation near Haram',
         'Day 1: Arrival, Day 2-7: Makkah, Day 8-13: Mina/Arafat/Muzdalifah, Day 14-20: Madinah',
         '5-star hotel, VIP transport, expert guide, meals, visa processing',
         'Airfare not included, personal expenses',
         'Pullman ZamZam Makkah (5-star)',
         'Private AC buses',
         'Full board (breakfast, lunch, dinner)'),
        
        ('Haj Gold 2026', 100, 550000, '2026-06-15', '2026-07-30', 'Open',
         'Standard Haj package with 4-star accommodation',
         'Day 1-20: Standard Haj itinerary',
         '4-star hotel, transport, guide, meals',
         'Airfare, personal expenses',
         'Makkah Hotel (4-star)',
         'Shared AC buses',
         'Half board (breakfast & dinner)'),
        
        ('Umrah Ramadhan Special', 200, 125000, '2026-03-01', '2026-03-20', 'Closing Soon',
         'Special Umrah package for the last 10 days of Ramadhan',
         'Day 1-20: Umrah itinerary with focus on Ramadhan',
         '3-star hotel, transport, guide',
         'Airfare, meals',
         'Dar Al Tawhid (3-star)',
         'Shared buses',
         'Breakfast only'),
        
        ('Haj Silver 2026', 150, 350000, '2026-06-20', '2026-07-28', 'Open',
         'Economy Haj package for budget-conscious pilgrims',
         'Day 1-20: Standard Haj itinerary',
         '3-star hotel, transport, basic guidance',
         'Airfare, meals, extras',
         'Al Safwah Hotel (3-star)',
         'Economy buses',
         'No meals included')
    ]
    
    for batch in batches:
        cursor.execute(
            """INSERT INTO batches (
                batch_name, total_seats, price, departure_date, return_date, status, description,
                itinerary, inclusions, exclusions, hotel_details, transport_details, meal_plan
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            batch
        )
    
    # Insert sample travelers with all 33 fields
    travelers = [
        # Ahmed Khan - All fields populated
        ('Ahmed', 'Khan', 'Ahmed Khan', 1, 'A1234567', '2020-01-15', '2030-01-14', 'Active', 'Male', '1985-06-15',
         '9876543210', 'ahmed@email.com', '1234-5678-9012', 'ABCDE1234F', 'Yes', 'Fully Vaccinated', 'No',
         'Mumbai', 'Mumbai', '123, Green Street, Andheri East, Mumbai - 400093',
         'Abdullah Khan', 'Amina Khan', 'N/A',
         None, None, None, None, None,
         '1234', 'Brother', '9876543211', 'No known allergies'),
        
        # Fatima Begum - Some fields empty
        ('Fatima', 'Begum', 'Fatima Begum', 2, 'B7654321', '2019-08-20', '2029-08-19', 'Active', 'Female', '1990-11-22',
         '8765432109', 'fatima@email.com', '2345-6789-0123', 'FGHIJ5678K', 'Pending', 'Partially Vaccinated', 'No',
         'Delhi', 'Delhi', '456, Lotus Apartments, Saket, New Delhi - 110017',
         'Mohammed Ali', 'Zainab Ali', 'Hasan Raza',
         None, None, None, None, None,
         '5678', 'Husband', '8765432100', 'Diabetic'),
        
        # Mohammed Rafiq - With wheelchair requirement
        ('Mohammed', 'Rafiq', 'Mohammed Rafiq', 3, 'C9876543', '2021-03-10', '2031-03-09', 'Processing', 'Male', '1978-03-08',
         '7654321098', 'rafiq@email.com', '3456-7890-1234', 'KLMNO9012P', 'No', 'Not Vaccinated', 'Yes',
         'Hyderabad', 'Hyderabad', '789, Old City, Hyderabad - 500002',
         'Abdul Rafiq', 'Razia Sultana', 'N/A',
         None, None, None, None, None,
         '9012', 'Son', '7654321000', 'Requires wheelchair assistance')
    ]
    
    for traveler in travelers:
        cursor.execute(
            """INSERT INTO travelers (
                first_name, last_name, passport_name, batch_id, passport_no, passport_issue_date,
                passport_expiry_date, passport_status, gender, dob, mobile, email, aadhaar, pan,
                aadhaar_pan_linked, vaccine_status, wheelchair, place_of_birth, place_of_issue,
                passport_address, father_name, mother_name, spouse_name, passport_scan, aadhaar_scan,
                pan_scan, vaccine_scan, photo, pin, emergency_contact, emergency_phone, medical_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            traveler
        )
        cursor.execute("UPDATE batches SET booked_seats = booked_seats + 1 WHERE id = ?", (traveler[3],))
    
    # Insert sample payments
    payments = [
        (1, 1, 'Booking Amount', 85000, '2026-01-15', '2026-01-15', 'Bank Transfer', 'TXN123456', 'completed', 'Booking payment received'),
        (1, 1, '1st Installment', 85000, '2026-02-15', '2026-02-15', 'Bank Transfer', 'TXN123457', 'completed', '1st installment'),
        (2, 2, 'Full Payment', 550000, '2026-01-20', '2026-01-20', 'UPI', 'UPI123456', 'completed', 'Full payment'),
        (3, 3, 'Booking Amount', 25000, '2026-02-01', '2026-03-01', 'Cash', 'CASH001', 'pending', 'Booking amount pending')
    ]
    
    for traveler_id, batch_id, installment, amount, date, due, method, trans, status, remarks in payments:
        cursor.execute(
            "INSERT INTO payments (traveler_id, batch_id, installment, amount, payment_date, due_date, payment_method, transaction_id, status, remarks) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (traveler_id, batch_id, installment, amount, date, due, method, trans, status, remarks)
        )
    
    # Insert sample invoices
    invoices = [
        ('INV-2026-001', 1, 1, '2026-01-15', '2026-02-14', 850000, 5, 42500, 1, 8925, 901425, 180285, 'partial', '9985', 'Maharashtra', '50% advance payment required'),
        ('INV-2026-002', 2, 2, '2026-01-20', '2026-02-19', 550000, 5, 27500, 1, 5775, 583275, 583275, 'paid', '9985', 'Maharashtra', 'Full payment received'),
        ('INV-2026-003', 3, 3, '2026-02-01', '2026-03-03', 125000, 5, 6250, 1, 1312, 132562, 26512, 'pending', '9985', 'Maharashtra', 'Booking amount received')
    ]
    
    for inv in invoices:
        cursor.execute(
            "INSERT INTO invoices (invoice_number, traveler_id, batch_id, invoice_date, due_date, base_amount, gst_percent, gst_amount, tcs_percent, tcs_amount, total_amount, paid_amount, status, hsn_code, place_of_supply, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            inv
        )
    
    # Insert sample receipts
    receipts = [
        ('REC-2026-001', 1, 1, '2026-01-15', 85000, 'Bank Transfer', 'TXN123456', 'installment', '1st Installment', 'Booking payment'),
        ('REC-2026-002', 1, 2, '2026-02-15', 85000, 'Bank Transfer', 'TXN123457', 'installment', '2nd Installment', ''),
        ('REC-2026-003', 2, 3, '2026-01-20', 550000, 'UPI', 'UPI123456', 'final', 'Final Settlement', 'Full payment')
    ]
    
    for receipt in receipts:
        cursor.execute(
            "INSERT INTO receipts (receipt_number, traveler_id, payment_id, receipt_date, amount, payment_method, transaction_id, receipt_type, installment_info, remarks) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            receipt
        )
    
    # Insert default company settings (COMPREHENSIVE)
    cursor.execute('''
        INSERT INTO company_settings (
            legal_name, display_name, address_line1, address_line2, city, state, country, pin_code,
            phone, mobile, email, website, gstin, pan, tan, tcs_no, tin, cin, iec, msme,
            bank_name, bank_branch, account_name, account_no, ifsc_code, micr_code, upi_id, qr_code
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Alhudha Haj Service P Ltd.', 'Alhudha Haj Travel',
        '2/117, Second Floor, Armenian Street', 'Mannady', 'Chennai', 'Tamil Nadu', 'India', '600001',
        '+91 44 1234 5678', '+91 98765 43210', 'info@alhudha.com', 'www.alhudha.com',
        '33ABCDE1234F1Z5', 'ABCDE1234F', 'ABCD12345E', 'TCS123456789', '33123456789', 'U12345TN1998PTC123456', '1234567890', 'UDYAM-TN-01-1234567',
        'State Bank of India', 'Armenian Street, Chennai', 'Alhudha Haj Service P Ltd.', '12345678901', 'SBIN0012345', '600002123', 'alhudha@okhdfcbank', 'upi://pay?pa=alhudha@okhdfcbank&pn=Alhudha'
    ))
    
    # Insert default frontpage settings
    cursor.execute('''
        INSERT INTO frontpage_settings (
            hero_heading, hero_subheading, hero_button_text, hero_button_link,
            packages_title, footer_text, footer_phone, footer_email,
            facebook_url, twitter_url, instagram_url,
            alert_enabled, alert_message, alert_link,
            whatsapp_number, whatsapp_message, booking_email, email_subject
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Your Journey to the Holy Land',
        'Experience the spiritual journey of a lifetime with our premium Haj and Umrah packages',
        'View Packages', '#packages',
        'Our Haj & Umrah Packages',
        '© 2026 Alhudha Haj Travel System. All rights reserved.',
        '+91 98765 43210', 'info@alhudha.com',
        '#', '#', '#',
        1, '⚠️ Important: Visa requirements updated for 2026 Hajj. Please submit documents by March 15th.', '/visa-update',
        '919876543210', 'Hi, I\'m interested in your Haj/Umrah packages. Can you please share more details?',
        'bookings@alhudha.com', 'Package Inquiry: '
    ))
    
    # Insert default whatsapp settings
    cursor.execute('''
        INSERT INTO whatsapp_settings (number, message_template)
        VALUES (?, ?)
    ''', (
        '919876543210',
        'Hi, I\'m interested in your Haj/Umrah packages. Can you please share more details?'
    ))
    
    # Insert default email settings
    cursor.execute('''
        INSERT INTO email_settings (smtp_server, smtp_port, encryption, from_email, reply_to, subject_prefix)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        'smtp.gmail.com', 587, 'TLS',
        'bookings@alhudha.com', 'info@alhudha.com',
        '[Alhudha] '
    ))
    
    # Insert sample backup history
    backup_history = [
        ('Full Backup - 2026-02-21 03:00 AM', 'auto', '2.4 MB', 12, 'completed', 'local'),
        ('Pre-Haj Registration Restore Point', 'manual', '1.8 MB', 8, 'completed', 'both'),
        ('Before Payment Structure Change', 'manual', '2.2 MB', 12, 'completed', 'both')
    ]
    
    for backup in backup_history:
        cursor.execute(
            "INSERT INTO backup_history (backup_name, backup_type, file_size, tables_count, status, location) VALUES (?, ?, ?, ?, ?, ?)",
            backup
        )
    
    # Insert sample activity log
    activities = [
        (1, 'login', 'auth', 'Super admin logged in', '192.168.1.1'),
        (2, 'create', 'traveler', 'Added new traveler: Ahmed Khan', '192.168.1.2'),
        (1, 'payment', 'payment', 'Recorded payment of ₹85,000', '192.168.1.1'),
        (2, 'update', 'batch', 'Updated batch: Haj Platinum 2026', '192.168.1.2')
    ]
    
    for user_id, action, module, desc, ip in activities:
        cursor.execute(
            "INSERT INTO activity_log (user_id, action, module, description, ip_address) VALUES (?, ?, ?, ?, ?)",
            (user_id, action, module, desc, ip)
        )
    
    conn.commit()
    conn.close()
    print("✅ SQLite database initialized successfully with comprehensive sample data")
    print("\n📊 Tables created:")
    print("   - users (with permissions)")
    print("   - batches (enhanced)")
    print("   - travelers (33 fields)")
    print("   - payments (enhanced)")
    print("   - invoices")
    print("   - receipts")
    print("   - company_settings (comprehensive)")
    print("   - frontpage_settings")
    print("   - whatsapp_settings")
    print("   - email_settings")
    print("   - backup_history")
    print("   - activity_log")
    print("\n👥 Demo Users:")
    print("   - superadmin / admin123 (Super Admin)")
    print("   - admin1 / admin123 (Admin)")
    print("   - manager1 / admin123 (Manager)")
    print("   - staff1 / admin123 (Staff)")
    print("   - viewer1 / admin123 (Viewer)")
    print("\n🛂 Demo Travelers:")
    print("   - Ahmed Khan (A1234567 / 1234)")
    print("   - Fatima Begum (B7654321 / 5678)")
    print("   - Mohammed Rafiq (C9876543 / 9012)")

if __name__ == "__main__":
    init_db()
