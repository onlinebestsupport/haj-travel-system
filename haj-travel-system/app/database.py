import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db():
    """Get database connection with error handling"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        return None
    
    try:
        conn = psycopg2.connect(database_url)
        print("✅ Database connected successfully!")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def init_db():
    """Initialize database tables"""
    conn = get_db()
    if not conn:
        print("❌ Cannot initialize database - no connection")
        return
    
    try:
        cur = conn.cursor()
        
        # Create batches table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS batches (
                id SERIAL PRIMARY KEY,
                batch_name TEXT NOT NULL UNIQUE,
                departure_date DATE,
                return_date DATE,
                total_seats INTEGER DEFAULT 150,
                booked_seats INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create travelers table with 33 fields
        cur.execute("""
            CREATE TABLE IF NOT EXISTS travelers (
                id SERIAL PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                passport_name TEXT GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
                batch_id INTEGER REFERENCES batches(id) ON DELETE SET NULL,
                passport_no TEXT UNIQUE NOT NULL,
                passport_issue_date DATE,
                passport_expiry_date DATE,
                passport_status TEXT DEFAULT 'Active',
                gender TEXT,
                dob DATE,
                mobile TEXT NOT NULL,
                email TEXT,
                aadhaar TEXT UNIQUE,
                pan TEXT UNIQUE,
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
                extra_fields JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_travelers_passport ON travelers(passport_no);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_travelers_batch ON travelers(batch_id);")
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
