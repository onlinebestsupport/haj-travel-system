-- Initialize database
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE,
    role TEXT DEFAULT 'admin',
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
);

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
);

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
);
