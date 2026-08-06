import psycopg2

DB_URL = 'postgresql://postgres:cbZOkSkTGHUBzcIKZQOLmcClIVhHqNAI@yamanote.proxy.rlwy.net:39010/railway?sslmode=require'

print("=" * 60)
print("Creating database tables...")
print("=" * 60)

try:
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            name VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            role VARCHAR(50) DEFAULT 'user',
            is_active BOOLEAN DEFAULT TRUE,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ users table created")
    
    # Create batches table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batches (
            id SERIAL PRIMARY KEY,
            batch_name VARCHAR(100) NOT NULL,
            status VARCHAR(50) DEFAULT 'Open',
            start_date DATE,
            end_date DATE,
            departure_date DATE,
            return_date DATE,
            total_seats INTEGER DEFAULT 0,
            booked_seats INTEGER DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ batches table created")
    
    # Create travelers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS travelers (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            passport_name VARCHAR(200),
            passport_no VARCHAR(50) UNIQUE NOT NULL,
            passport_expiry_date DATE,
            expected_return_date DATE,
            mobile VARCHAR(20) NOT NULL,
            email VARCHAR(100),
            address TEXT,
            batch_id INTEGER REFERENCES batches(id),
            passport_status VARCHAR(50) DEFAULT 'Active',
            vaccine_status VARCHAR(50) DEFAULT 'Not Vaccinated',
            wheelchair VARCHAR(10) DEFAULT 'No',
            emergency_contact VARCHAR(100),
            emergency_phone VARCHAR(20),
            extra_fields JSONB,
            passport_scan VARCHAR(255),
            aadhaar_scan VARCHAR(255),
            pan_scan VARCHAR(255),
            vaccine_scan VARCHAR(255),
            photo VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ travelers table created")
    
    # Create payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            traveler_id INTEGER REFERENCES travelers(id),
            batch_id INTEGER REFERENCES batches(id),
            amount DECIMAL(10,2) NOT NULL,
            payment_date DATE,
            due_date DATE,
            status VARCHAR(50) DEFAULT 'pending',
            payment_method VARCHAR(50),
            reference_no VARCHAR(100),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ payments table created")
    
    # Create invoices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id SERIAL PRIMARY KEY,
            invoice_number VARCHAR(50) UNIQUE NOT NULL,
            traveler_id INTEGER REFERENCES travelers(id),
            batch_id INTEGER REFERENCES batches(id),
            amount DECIMAL(10,2) NOT NULL,
            base_amount DECIMAL(10,2),
            gst_percent DECIMAL(5,2),
            gst_amount DECIMAL(10,2),
            tcs_percent DECIMAL(5,2),
            tcs_amount DECIMAL(10,2),
            status VARCHAR(50) DEFAULT 'pending',
            issue_date DATE,
            due_date DATE,
            items JSONB,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ invoices table created")
    
    # Create receipts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS receipts (
            id SERIAL PRIMARY KEY,
            receipt_number VARCHAR(50) UNIQUE NOT NULL,
            traveler_id INTEGER REFERENCES travelers(id),
            payment_id INTEGER REFERENCES payments(id),
            amount DECIMAL(10,2) NOT NULL,
            receipt_date DATE,
            payment_method VARCHAR(50),
            reference_no VARCHAR(100),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ receipts table created")
    
    # Create company_settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_settings (
            id SERIAL PRIMARY KEY,
            company_name VARCHAR(200),
            company_address TEXT,
            company_phone VARCHAR(50),
            company_email VARCHAR(100),
            company_website VARCHAR(100),
            gst_no VARCHAR(50),
            pan_no VARCHAR(50),
            bank_name VARCHAR(100),
            bank_account_no VARCHAR(50),
            bank_ifsc VARCHAR(50),
            logo VARCHAR(255),
            primary_color VARCHAR(50) DEFAULT '#3498db',
            secondary_color VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ company_settings table created")
    
    # Create backup_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS backup_history (
            id SERIAL PRIMARY KEY,
            backup_name VARCHAR(100),
            backup_file VARCHAR(255),
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ backup_history table created")
    
    conn.commit()
    print("\n" + "=" * 60)
    print("✅ ALL TABLES CREATED SUCCESSFULLY!")
    print("=" * 60)
    
    # List all tables
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\n📊 Total tables: {len(tables)}")
    print("Tables:")
    for table in tables:
        print(f"  - {table}")
    
    # Check important tables
    important = ['users', 'travelers', 'batches', 'payments', 'invoices', 'receipts', 'company_settings']
    print("\n🔍 Important tables check:")
    for table in important:
        status = '✅' if table in tables else '❌'
        print(f"  {status} {table}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)