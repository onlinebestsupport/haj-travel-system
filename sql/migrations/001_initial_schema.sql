-- 001_initial_schema.sql
-- Run this to create the initial database schema

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    role VARCHAR(50) DEFAULT 'staff',
    permissions JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    password_updated_at TIMESTAMP,
    reset_token VARCHAR(255),
    reset_token_expires TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create batches table
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
);

-- Create travelers table
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
);

-- Create payments table
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    traveler_id INTEGER REFERENCES travelers(id) ON DELETE CASCADE,
    batch_id INTEGER REFERENCES batches(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    reference VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create invoices table
CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    traveler_id INTEGER REFERENCES travelers(id) ON DELETE CASCADE,
    batch_id INTEGER REFERENCES batches(id) ON DELETE CASCADE,
    invoice_number VARCHAR(100) UNIQUE,
    amount DECIMAL(10,2) NOT NULL,
    due_date DATE,
    status VARCHAR(50) DEFAULT 'pending',
    items JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create receipts table
CREATE TABLE IF NOT EXISTS receipts (
    id SERIAL PRIMARY KEY,
    traveler_id INTEGER REFERENCES travelers(id) ON DELETE CASCADE,
    payment_id INTEGER REFERENCES payments(id) ON DELETE SET NULL,
    receipt_number VARCHAR(100) UNIQUE,
    amount DECIMAL(10,2) NOT NULL,
    receipt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create activity_log table
CREATE TABLE IF NOT EXISTS activity_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    module VARCHAR(100),
    description TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default admin user (password: admin123)
INSERT INTO users (username, password_hash, name, email, role, is_active)
SELECT 'superadmin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2c6l9vQsBm', 'Super Admin', 'admin@alhudha.com', 'super_admin', true
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'superadmin');

INSERT INTO users (username, password_hash, name, email, role, is_active)
SELECT 'admin1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2c6l9vQsBm', 'Admin User', 'admin1@alhudha.com', 'admin', true
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin1');
