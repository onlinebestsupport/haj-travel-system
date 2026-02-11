-- Initialize Database Schema for Haj Travel System

-- Create batches table
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

-- Create travelers table with 33 fields
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_travelers_passport ON travelers(passport_no);
CREATE INDEX IF NOT EXISTS idx_travelers_batch ON travelers(batch_id);
CREATE INDEX IF NOT EXISTS idx_travelers_created ON travelers(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_travelers_status ON travelers(passport_status);

-- Insert sample batches
INSERT INTO batches (batch_name, departure_date, return_date, total_seats, status) 
VALUES 
  ('Haj-2024-001', '2024-06-15', '2024-07-30', 150, 'Open'),
  ('Haj-2024-002', '2024-07-01', '2024-08-15', 150, 'Open'),
  ('Haj-2024-003', '2024-07-15', '2024-08-30', 150, 'Open')
ON CONFLICT (batch_name) DO NOTHING;