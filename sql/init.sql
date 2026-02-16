-- =====================================================
-- HAJ TRAVEL SYSTEM - COMPLETE DATABASE INITIALIZATION
-- =====================================================
-- This script creates all tables for the Haj Travel System
-- Includes: admin_users, roles, permissions, batches, travelers, payments
-- =====================================================

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- PART 1: ADMINISTRATION AND AUTHENTICATION TABLES
-- =====================================================

-- 1.1 Create admin_users table (for staff login)
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    created_by INTEGER REFERENCES admin_users(id)
);

-- 1.2 Create roles table
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- 1.3 Create permissions table
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- 1.4 Create role_permissions junction table
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- 1.5 Create user_roles junction table
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER REFERENCES admin_users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    assigned_by INTEGER REFERENCES admin_users(id),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

-- 1.6 Create login_logs table for tracking
CREATE TABLE IF NOT EXISTS login_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES admin_users(id) ON DELETE SET NULL,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_time TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- =====================================================
-- PART 2: CORE APPLICATION TABLES
-- =====================================================

-- 2.1 Create batches table (Haj/Umrah packages)
CREATE TABLE IF NOT EXISTS batches (
    id SERIAL PRIMARY KEY,
    batch_name VARCHAR(100) NOT NULL UNIQUE,
    departure_date DATE,
    return_date DATE,
    total_seats INTEGER DEFAULT 150,
    booked_seats INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'Open',
    price DECIMAL(12,2),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2.2 Create travelers table with ALL 33 fields
CREATE TABLE IF NOT EXISTS travelers (
    id SERIAL PRIMARY KEY,
    
    -- Personal Information (10 fields)
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    passport_name VARCHAR(101) GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
    batch_id INTEGER REFERENCES batches(id) ON DELETE SET NULL,
    passport_no VARCHAR(50) UNIQUE NOT NULL,
    passport_issue_date DATE,
    passport_expiry_date DATE,
    passport_status VARCHAR(50) DEFAULT 'Active',
    gender VARCHAR(10),
    dob DATE,
    
    -- Contact Information (7 fields)
    mobile VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    aadhaar VARCHAR(20),
    pan VARCHAR(20),
    aadhaar_pan_linked VARCHAR(20) DEFAULT 'No',
    vaccine_status VARCHAR(50) DEFAULT 'Not Vaccinated',
    wheelchair VARCHAR(10) DEFAULT 'No',
    
    -- Address & Family (6 fields)
    place_of_birth VARCHAR(100),
    place_of_issue VARCHAR(100),
    passport_address TEXT,
    father_name VARCHAR(100),
    mother_name VARCHAR(100),
    spouse_name VARCHAR(100),
    
    -- Documents (4 fields)
    passport_scan VARCHAR(255),
    aadhaar_scan VARCHAR(255),
    pan_scan VARCHAR(255),
    vaccine_scan VARCHAR(255),
    
    -- Additional Fields (6 fields)
    extra_fields JSONB DEFAULT '{}'::jsonb,
    pin VARCHAR(4) DEFAULT '0000',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Tracking (automated)
    created_by INTEGER REFERENCES admin_users(id),
    updated_by INTEGER REFERENCES admin_users(id)
);

-- 2.3 Create payments table
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    traveler_id INTEGER REFERENCES travelers(id) ON DELETE CASCADE,
    installment VARCHAR(50),
    amount DECIMAL(10,2) NOT NULL,
    due_date DATE,
    payment_date DATE,
    payment_method VARCHAR(50),
    transaction_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Pending',
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recorded_by INTEGER REFERENCES admin_users(id)
);

-- 2.4 Create payment_reversals table
CREATE TABLE IF NOT EXISTS payment_reversals (
    id SERIAL PRIMARY KEY,
    original_payment_id INTEGER REFERENCES payments(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    reason TEXT NOT NULL,
    reversed_by INTEGER REFERENCES admin_users(id),
    reversed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_full_reversal BOOLEAN DEFAULT true
);

-- 2.5 Create invoices table
CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    traveler_id INTEGER REFERENCES travelers(id) ON DELETE CASCADE,
    invoice_number VARCHAR(50) UNIQUE,
    base_amount DECIMAL(10,2),
    gst_rate DECIMAL(5,2),
    gst_amount DECIMAL(10,2),
    tcs_rate DECIMAL(5,2),
    tcs_amount DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    total_paid DECIMAL(10,2),
    balance_due DECIMAL(10,2),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generated_by INTEGER REFERENCES admin_users(id),
    pdf_path TEXT
);

-- 2.6 Create backups table
CREATE TABLE IF NOT EXISTS backups (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255),
    size_bytes BIGINT,
    traveler_count INTEGER,
    batch_count INTEGER,
    payment_count INTEGER,
    status VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES admin_users(id)
);

-- =====================================================
-- PART 3: CREATE INDEXES FOR PERFORMANCE
-- =====================================================

-- Traveler indexes
CREATE INDEX IF NOT EXISTS idx_travelers_passport ON travelers(passport_no);
CREATE INDEX IF NOT EXISTS idx_travelers_mobile ON travelers(mobile);
CREATE INDEX IF NOT EXISTS idx_travelers_batch ON travelers(batch_id);
CREATE INDEX IF NOT EXISTS idx_travelers_email ON travelers(email);
CREATE INDEX IF NOT EXISTS idx_travelers_created ON travelers(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_travelers_status ON travelers(passport_status);

-- Payment indexes
CREATE INDEX IF NOT EXISTS idx_payments_traveler ON payments(traveler_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_payments_due ON payments(due_date);

-- Login logs indexes
CREATE INDEX IF NOT EXISTS idx_login_logs_user ON login_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_login_logs_time ON login_logs(login_time);

-- Batch indexes
CREATE INDEX IF NOT EXISTS idx_batches_status ON batches(status);
CREATE INDEX IF NOT EXISTS idx_batches_dates ON batches(departure_date, return_date);

-- =====================================================
-- PART 4: INSERT DEFAULT DATA
-- =====================================================

-- Insert default roles
INSERT INTO roles (name, description) VALUES 
('super_admin', 'Full system access - can manage users and all data'),
('admin', 'Can manage all data except users'),
('manager', 'Can manage batches and travelers'),
('staff', 'Can add and edit travelers'),
('viewer', 'Read-only access')
ON CONFLICT (name) DO NOTHING;

-- Insert default permissions
INSERT INTO permissions (name, description) VALUES 
('manage_users', 'Create, edit, delete users'),
('view_users', 'View user list'),
('manage_batches', 'Create, edit, delete batches'),
('view_batches', 'View batches'),
('manage_travelers', 'Create, edit, delete travelers'),
('view_travelers', 'View travelers'),
('create_payment', 'Record payments'),
('view_payments', 'View payments'),
('reverse_payment', 'Reverse/cancel payments'),
('view_reports', 'View reports'),
('create_backup', 'Create database backups'),
('restore_backup', 'Restore from backup'),
('export_data', 'Export data'),
('view_logs', 'View login logs')
ON CONFLICT (name) DO NOTHING;

-- Assign permissions to roles
-- Admin permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'admin' AND p.name IN (
    'manage_batches', 'view_batches',
    'manage_travelers', 'view_travelers',
    'create_payment', 'view_payments',
    'reverse_payment', 'view_reports',
    'export_data', 'view_logs'
)
ON CONFLICT DO NOTHING;

-- Manager permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'manager' AND p.name IN (
    'manage_batches', 'view_batches',
    'manage_travelers', 'view_travelers',
    'create_payment', 'view_payments'
)
ON CONFLICT DO NOTHING;

-- Staff permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'staff' AND p.name IN (
    'manage_travelers', 'view_travelers',
    'create_payment', 'view_payments'
)
ON CONFLICT DO NOTHING;

-- Viewer permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'viewer' AND p.name IN (
    'view_batches', 'view_travelers', 'view_payments'
)
ON CONFLICT DO NOTHING;

-- Insert default admin users (password: admin123)
-- SHA256 hash for "admin123" with salt "alhudha-salt-2026"
INSERT INTO admin_users (username, password_hash, email, full_name, is_active) VALUES 
('superadmin', 'L5Ks5qk2Y8O+c1CXzX6hWpPxG69RyB5+2n4O7U+DmVQ=', 'super@alhudha.com', 'Super Admin', true),
('admin1', 'L5Ks5qk2Y8O+c1CXzX6hWpPxG69RyB5+2n4O7U+DmVQ=', 'admin@alhudha.com', 'Admin User', true),
('manager1', 'L5Ks5qk2Y8O+c1CXzX6hWpPxG69RyB5+2n4O7U+DmVQ=', 'manager@alhudha.com', 'Manager', true),
('staff1', 'L5Ks5qk2Y8O+c1CXzX6hWpPxG69RyB5+2n4O7U+DmVQ=', 'staff@alhudha.com', 'Staff Member', true),
('viewer1', 'L5Ks5qk2Y8O+c1CXzX6hWpPxG69RyB5+2n4O7U+DmVQ=', 'viewer@alhudha.com', 'Viewer Only', true)
ON CONFLICT (username) DO NOTHING;

-- Assign roles to users
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM admin_users u, roles r
WHERE u.username = 'superadmin' AND r.name = 'super_admin'
ON CONFLICT DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM admin_users u, roles r
WHERE u.username = 'admin1' AND r.name = 'admin'
ON CONFLICT DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM admin_users u, roles r
WHERE u.username = 'manager1' AND r.name = 'manager'
ON CONFLICT DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM admin_users u, roles r
WHERE u.username = 'staff1' AND r.name = 'staff'
ON CONFLICT DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM admin_users u, roles r
WHERE u.username = 'viewer1' AND r.name = 'viewer'
ON CONFLICT DO NOTHING;

-- =====================================================
-- PART 5: INSERT SAMPLE DATA
-- =====================================================

-- Insert sample batches
INSERT INTO batches (batch_name, departure_date, return_date, total_seats, price, status, description) VALUES 
('Haj Silver 2026', '2026-05-15', '2026-06-20', 150, 350000.00, 'Open', 'Economy Haj package with shared accommodation near Azizia. Includes visa processing, transportation, and meals.'),
('Haj Gold 2026', '2026-05-10', '2026-06-25', 100, 550000.00, 'Open', 'Premium Haj package with private rooms in Makkah (500m from Haram) and Madinah (300m from Masjid Nabawi).'),
('Haj Platinum 2026', '2026-05-05', '2026-06-30', 50, 850000.00, 'Open', 'Luxury Haj package with VIP services, 5-star hotels overlooking Haram, private transport, and guided tours.'),
('Umrah Winter 2026', '2026-01-10', '2026-01-30', 200, 95000.00, 'Open', 'Winter Umrah package with pleasant weather. 15-day package with Ziyarat visits.'),
('Umrah Spring 2026', '2026-03-15', '2026-04-05', 200, 110000.00, 'Open', 'Spring Umrah package during pleasant weather. Includes stay in Makkah (10 days) and Madinah (10 days).'),
('Umrah Summer 2026', '2026-07-10', '2026-07-30', 200, 85000.00, 'Open', 'Summer Umrah package with economical rates. All meals and transportation included.'),
('Haj Economy Plus', '2026-06-16', '2026-07-29', 120, 425000.00, 'Open', 'Value Haj package with good accommodation, bus transportation, and experienced guides.'),
('Umrah Ramadhan Special', '2026-03-01', '2026-03-20', 200, 125000.00, 'Open', '20-day Umrah package during Ramadhan. Stay in Makkah (10 days) and Madinah (10 days). All meals included.')
ON CONFLICT (batch_name) DO NOTHING;

-- Insert sample travelers with complete data
DO $$
DECLARE
    silver_batch_id INTEGER;
    gold_batch_id INTEGER;
    platinum_batch_id INTEGER;
    umrah_winter_id INTEGER;
    umrah_spring_id INTEGER;
    umrah_summer_id INTEGER;
    economy_id INTEGER;
    ramadhan_id INTEGER;
BEGIN
    -- Get batch IDs
    SELECT id INTO silver_batch_id FROM batches WHERE batch_name = 'Haj Silver 2026';
    SELECT id INTO gold_batch_id FROM batches WHERE batch_name = 'Haj Gold 2026';
    SELECT id INTO platinum_batch_id FROM batches WHERE batch_name = 'Haj Platinum 2026';
    SELECT id INTO umrah_winter_id FROM batches WHERE batch_name = 'Umrah Winter 2026';
    SELECT id INTO umrah_spring_id FROM batches WHERE batch_name = 'Umrah Spring 2026';
    SELECT id INTO umrah_summer_id FROM batches WHERE batch_name = 'Umrah Summer 2026';
    SELECT id INTO economy_id FROM batches WHERE batch_name = 'Haj Economy Plus';
    SELECT id INTO ramadhan_id FROM batches WHERE batch_name = 'Umrah Ramadhan Special';

    -- Insert travelers
    INSERT INTO travelers (
        first_name, last_name, batch_id, passport_no, passport_issue_date, passport_expiry_date,
        passport_status, gender, dob, mobile, email, aadhaar, pan, aadhaar_pan_linked,
        vaccine_status, wheelchair, place_of_birth, place_of_issue, passport_address,
        father_name, mother_name, spouse_name, extra_fields, pin
    ) VALUES
    -- Traveler 1: Ahmed Mohammed (Haj Silver)
    ('Ahmed', 'Mohammed', silver_batch_id, 'A1234567', '2020-05-15', '2030-05-14',
     'Active', 'Male', '1985-03-12', '9876543210', 'ahmed.mohammed@email.com', 
     '123456789012', 'ABCDE1234F', 'Yes', 'Fully Vaccinated', 'No',
     'Mumbai', 'Mumbai', 'House No. 123, Gulshan Colony, Andheri East, Mumbai - 400093',
     'Mohammed Ibrahim', 'Fatima Begum', 'Aisha Ahmed',
     '{"emergency_contact": "9876543211", "blood_group": "O+", "nationality": "Indian", "profession": "Engineer"}', '1234'),

    -- Traveler 2: Fatima Khan (Haj Gold)
    ('Fatima', 'Khan', gold_batch_id, 'B7654321', '2021-08-20', '2031-08-19',
     'Active', 'Female', '1990-07-25', '9876543211', 'fatima.khan@email.com',
     '234567890123', 'FGHIJ5678K', 'Yes', 'Fully Vaccinated', 'No',
     'Delhi', 'Delhi', 'Flat 45, Park View Apartments, Saket, New Delhi - 110017',
     'Khan Abdul', 'Zainab Khan', NULL,
     '{"emergency_contact": "9876543212", "blood_group": "A+", "nationality": "Indian", "profession": "Teacher"}', '2234'),

    -- Traveler 3: Mohammed Ali (Haj Platinum)
    ('Mohammed', 'Ali', platinum_batch_id, 'C9876543', '2019-11-10', '2029-11-09',
     'Active', 'Male', '1978-12-03', '9876543212', 'mohammed.ali@email.com',
     '345678901234', 'KLMNO9012P', 'Pending', 'Partially Vaccinated', 'No',
     'Hyderabad', 'Hyderabad', '16-11-567, Old City, Hyderabad - 500002',
     'Ali Akbar', 'Ayesha Begum', 'Sameena Ali',
     '{"emergency_contact": "9876543213", "blood_group": "B+", "nationality": "Indian", "profession": "Business"}', '3234'),

    -- Traveler 4: Aisha Begum (Haj Platinum)
    ('Aisha', 'Begum', platinum_batch_id, 'D4567890', '2022-01-15', '2032-01-14',
     'Active', 'Female', '1988-09-18', '9876543213', 'aisha.begum@email.com',
     '456789012345', 'PQRST3456U', 'Yes', 'Fully Vaccinated', 'No',
     'Lucknow', 'Lucknow', '34, Hazratganj, Lucknow - 226001',
     'Begum Ahmed', 'Kulsum Begum', 'Hassan Raza',
     '{"emergency_contact": "9876543214", "blood_group": "AB+", "nationality": "Indian", "profession": "Doctor"}', '4234'),

    -- Traveler 5: Omar Hassan (Haj Silver)
    ('Omar', 'Hassan', silver_batch_id, 'E1122334', '2020-03-22', '2030-03-21',
     'Active', 'Male', '1982-06-30', '9876543214', 'omar.hassan@email.com',
     '567890123456', 'UVWXY6789Z', 'No', 'Not Vaccinated', 'Yes',
     'Bangalore', 'Bangalore', '789, 3rd Cross, Indiranagar, Bangalore - 560038',
     'Hassan Malik', 'Razia Hassan', 'Zainab Hassan',
     '{"emergency_contact": "9876543215", "blood_group": "B-", "nationality": "Indian", "profession": "Architect"}', '5234'),

    -- Traveler 6: Zainab Ahmed (Umrah Winter)
    ('Zainab', 'Ahmed', umrah_winter_id, 'F5566778', '2023-02-10', '2033-02-09',
     'Active', 'Female', '1995-11-12', '9876543215', 'zainab.ahmed@email.com',
     '678901234567', 'ABCDE8901F', 'Yes', 'Booster', 'No',
     'Chennai', 'Chennai', '56, TTK Road, Alwarpet, Chennai - 600018',
     'Ahmed Raza', 'Fatima Raza', NULL,
     '{"emergency_contact": "9876543216", "blood_group": "O-", "nationality": "Indian", "profession": "Software Developer"}', '6234'),

    -- Traveler 7: Yusuf Ibrahim (Umrah Spring)
    ('Yusuf', 'Ibrahim', umrah_spring_id, 'G9988776', '2021-07-05', '2031-07-04',
     'Active', 'Male', '1975-04-20', '9876543216', 'yusuf.ibrahim@email.com',
     '789012345678', 'FGHIJ2345K', 'No', 'Fully Vaccinated', 'No',
     'Kolkata', 'Kolkata', '12, Park Street, Kolkata - 700016',
     'Ibrahim Khan', 'Shamima Khan', 'Nasreen Begum',
     '{"emergency_contact": "9876543217", "blood_group": "A-", "nationality": "Indian", "profession": "Lawyer"}', '7234'),

    -- Traveler 8: Maryam Hassan (Umrah Summer)
    ('Maryam', 'Hassan', umrah_summer_id, 'H4433221', '2022-09-18', '2032-09-17',
     'Active', 'Female', '1987-08-08', '9876543217', 'maryam.hassan@email.com',
     '890123456789', 'KLMNO5678P', 'Yes', 'Partially Vaccinated', 'No',
     'Pune', 'Pune', '234, FC Road, Shivajinagar, Pune - 411004',
     'Hassan Ali', 'Zahra Ali', 'Abbas Hassan',
     '{"emergency_contact": "9876543218", "blood_group": "AB-", "nationality": "Indian", "profession": "Professor"}', '8234'),

    -- Traveler 9: Ibrahim Khan (Haj Economy Plus)
    ('Ibrahim', 'Khan', economy_id, 'I7788990', '2020-12-01', '2030-11-30',
     'Active', 'Male', '1968-03-15', '9876543218', 'ibrahim.khan@email.com',
     '901234567890', 'PQRST9012U', 'No', 'Fully Vaccinated', 'Yes',
     'Ahmedabad', 'Ahmedabad', '67, CG Road, Navrangpura, Ahmedabad - 380009',
     'Khan Mohammed', 'Amina Khan', 'Saira Khan',
     '{"emergency_contact": "9876543219", "blood_group": "B+", "nationality": "Indian", "profession": "Businessman"}', '9234'),

    -- Traveler 10: Khadija Begum (Umrah Ramadhan)
    ('Khadija', 'Begum', ramadhan_id, 'J2233445', '2023-03-25', '2033-03-24',
     'Active', 'Female', '1992-12-25', '9876543219', 'khadija.begum@email.com',
     '012345678901', 'UVWXY3456Z', 'Pending', 'Booster', 'No',
     'Jaipur', 'Jaipur', '89, MI Road, Jaipur - 302001',
     'Begum Ahmed', 'Nasreen Begum', 'Omar Farooq',
     '{"emergency_contact": "9876543220", "blood_group": "O+", "nationality": "Indian", "profession": "Designer"}', '0234')
    ON CONFLICT (passport_no) DO NOTHING;

    -- Update booked seats in batches
    UPDATE batches SET booked_seats = (
        SELECT COUNT(*) FROM travelers WHERE batch_id = batches.id
    );
END $$;

-- Insert sample payments
DO $$
DECLARE
    traveler1_id INTEGER;
    traveler2_id INTEGER;
    traveler3_id INTEGER;
    traveler4_id INTEGER;
    traveler5_id INTEGER;
    traveler6_id INTEGER;
    traveler7_id INTEGER;
    traveler8_id INTEGER;
    traveler9_id INTEGER;
    traveler10_id INTEGER;
BEGIN
    -- Get traveler IDs
    SELECT id INTO traveler1_id FROM travelers WHERE passport_no = 'A1234567';
    SELECT id INTO traveler2_id FROM travelers WHERE passport_no = 'B7654321';
    SELECT id INTO traveler3_id FROM travelers WHERE passport_no = 'C9876543';
    SELECT id INTO traveler4_id FROM travelers WHERE passport_no = 'D4567890';
    SELECT id INTO traveler5_id FROM travelers WHERE passport_no = 'E1122334';
    SELECT id INTO traveler6_id FROM travelers WHERE passport_no = 'F5566778';
    SELECT id INTO traveler7_id FROM travelers WHERE passport_no = 'G9988776';
    SELECT id INTO traveler8_id FROM travelers WHERE passport_no = 'H4433221';
    SELECT id INTO traveler9_id FROM travelers WHERE passport_no = 'I7788990';
    SELECT id INTO traveler10_id FROM travelers WHERE passport_no = 'J2233445';

    -- Insert payments for traveler 1 (Ahmed)
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (traveler1_id, 'Booking Amount', 50000, '2026-01-15', '2026-01-10', 'Bank Transfer', 'Paid', 'Initial booking amount paid via NEFT'),
    (traveler1_id, '1st Installment', 100000, '2026-02-15', '2026-02-12', 'Credit Card', 'Paid', 'First installment - online payment'),
    (traveler1_id, '2nd Installment', 100000, '2026-03-15', NULL, NULL, 'Pending', NULL),
    (traveler1_id, 'Final Payment', 100000, '2026-04-15', NULL, NULL, 'Pending', NULL)
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 2 (Fatima)
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (traveler2_id, 'Full Payment', 550000, '2026-01-20', '2026-01-18', 'Bank Transfer', 'Paid', 'Full payment received')
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 3 (Mohammed)
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (traveler3_id, 'Booking Amount', 50000, '2026-01-25', '2026-01-22', 'Cash', 'Paid', 'Paid at office'),
    (traveler3_id, '1st Installment', 150000, '2026-02-25', '2026-02-20', 'Bank Transfer', 'Paid', 'Online transfer'),
    (traveler3_id, '2nd Installment', 150000, '2026-03-25', NULL, NULL, 'Pending', NULL)
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 4 (Aisha)
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (traveler4_id, 'Booking Amount', 85000, '2026-02-01', '2026-01-28', 'Credit Card', 'Paid', 'Online booking'),
    (traveler4_id, '1st Installment', 250000, '2026-03-01', NULL, NULL, 'Pending', NULL)
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 5 (Omar)
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (traveler5_id, 'Full Payment', 850000, '2026-01-10', '2026-01-05', 'Bank Transfer', 'Paid', 'Full payment - Platinum package')
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 6 (Zainab)
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (traveler6_id, 'Booking Amount', 25000, '2026-02-10', '2026-02-05', 'UPI', 'Paid', 'Google Pay'),
    (traveler6_id, '1st Installment', 50000, '2026-03-10', NULL, NULL, 'Pending', NULL)
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 7 (Yusuf)
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (traveler7_id, 'Full Payment', 95000, '2026-01-15', '2026-01-12', 'Bank Transfer', 'Paid', 'Winter Umrah package')
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 8 (Maryam)
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (traveler8_id, 'Booking Amount', 35000, '2026-01-20', '2026-01-18', 'Credit Card', 'Paid', 'Summer booking'),
    (traveler8_id, '1st Installment', 45000, '2026-02-20', NULL, NULL, 'Pending', NULL)
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 9 (Ibrahim)
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (traveler9_id, 'Full Payment', 95000, '2026-01-05', '2026-01-03', 'Cash', 'Paid', 'Office payment - discount applied')
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 10 (Khadija)
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (traveler10_id, 'Booking Amount', 40000, '2026-02-05', '2026-02-01', 'Bank Transfer', 'Paid', 'Ramadhan special'),
    (traveler10_id, '1st Installment', 80000, '2026-03-05', NULL, NULL, 'Pending', NULL)
    ON CONFLICT DO NOTHING;

END $$;

-- =====================================================
-- PART 6: CREATE VIEWS FOR COMMON QUERIES
-- =====================================================

-- View for traveler summary
CREATE OR REPLACE VIEW traveler_summary AS
SELECT 
    t.id,
    t.first_name || ' ' || t.last_name AS full_name,
    t.passport_no,
    t.mobile,
    t.email,
    b.batch_name,
    b.departure_date,
    b.return_date,
    t.passport_status,
    t.vaccine_status,
    t.pin,
    t.created_at
FROM travelers t
LEFT JOIN batches b ON t.batch_id = b.id;

-- View for payment summary
CREATE OR REPLACE VIEW payment_summary AS
SELECT 
    p.id,
    t.first_name || ' ' || t.last_name AS traveler_name,
    t.passport_no,
    p.installment,
    p.amount,
    p.due_date,
    p.payment_date,
    p.status,
    p.payment_method,
    b.batch_name
FROM payments p
JOIN travelers t ON p.traveler_id = t.id
LEFT JOIN batches b ON t.batch_id = b.id;

-- View for batch occupancy
CREATE OR REPLACE VIEW batch_occupancy AS
SELECT 
    b.id,
    b.batch_name,
    b.departure_date,
    b.return_date,
    b.total_seats,
    b.booked_seats,
    (b.total_seats - b.booked_seats) AS available_seats,
    ROUND((b.booked_seats::DECIMAL / b.total_seats * 100), 2) AS occupancy_percentage,
    b.status,
    b.price
FROM batches b;

-- =====================================================
-- PART 7: CREATE FUNCTIONS FOR COMMON OPERATIONS
-- =====================================================

-- Function to update booked seats when traveler is added
CREATE OR REPLACE FUNCTION update_batch_seats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE batches SET booked_seats = booked_seats + 1 WHERE id = NEW.batch_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE batches SET booked_seats = booked_seats - 1 WHERE id = OLD.batch_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.batch_id != NEW.batch_id THEN
        UPDATE batches SET booked_seats = booked_seats - 1 WHERE id = OLD.batch_id;
        UPDATE batches SET booked_seats = booked_seats + 1 WHERE id = NEW.batch_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic seat updates
DROP TRIGGER IF EXISTS trigger_update_batch_seats ON travelers;
CREATE TRIGGER trigger_update_batch_seats
AFTER INSERT OR DELETE OR UPDATE OF batch_id ON travelers
FOR EACH ROW
EXECUTE FUNCTION update_batch_seats();

-- Function to update traveler's updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic updated_at
DROP TRIGGER IF EXISTS trigger_update_traveler_timestamp ON travelers;
CREATE TRIGGER trigger_update_traveler_timestamp
BEFORE UPDATE ON travelers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- PART 8: COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE travelers IS 'Main table storing all 33 fields of traveler information';
COMMENT ON TABLE batches IS 'Haj and Umrah package details';
COMMENT ON TABLE payments IS 'Payment records for travelers';
COMMENT ON TABLE admin_users IS 'System users with admin access';
COMMENT ON TABLE login_logs IS 'Audit log for user logins';
COMMENT ON COLUMN travelers.extra_fields IS 'JSON field for dynamic data like emergency contact, blood group, allergies';
COMMENT ON COLUMN travelers.pin IS '4-digit PIN for traveler login';

-- =====================================================
-- PART 9: FINAL VERIFICATION
-- =====================================================

-- Display summary of created tables
SELECT 
    table_name, 
    pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size,
    obj_description(c.oid) as description
FROM information_schema.tables t
JOIN pg_class c ON t.table_name = c.relname
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Show counts
SELECT 'admin_users' as table_name, COUNT(*) as count FROM admin_users
UNION ALL
SELECT 'roles', COUNT(*) FROM roles
UNION ALL
SELECT 'permissions', COUNT(*) FROM permissions
UNION ALL
SELECT 'batches', COUNT(*) FROM batches
UNION ALL
SELECT 'travelers', COUNT(*) FROM travelers
UNION ALL
SELECT 'payments', COUNT(*) FROM payments;

-- Show success message
DO $$
BEGIN
    RAISE NOTICE '==========================================';
    RAISE NOTICE 'HAJ TRAVEL SYSTEM DATABASE INITIALIZED';
    RAISE NOTICE '==========================================';
    RAISE NOTICE 'Tables created: 12';
    RAISE NOTICE 'Admin users: 5';
    RAISE NOTICE 'Batches: 8';
    RAISE NOTICE 'Travelers: 10';
    RAISE NOTICE 'Payments: 18';
    RAISE NOTICE '==========================================';
    RAISE NOTICE 'Default admin login: superadmin / admin123';
    RAISE NOTICE '==========================================';
END $$;
