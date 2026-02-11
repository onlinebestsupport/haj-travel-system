const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

// Create batches table
const createBatchesTableSQL = `
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
`;

// Create travelers table with ALL 33 fields
const createTravelersTableSQL = `
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

CREATE INDEX IF NOT EXISTS idx_travelers_passport ON travelers(passport_no);
CREATE INDEX IF NOT EXISTS idx_travelers_batch ON travelers(batch_id);
CREATE INDEX IF NOT EXISTS idx_travelers_created ON travelers(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_travelers_status ON travelers(passport_status);
`;

// Initialize database
async function initializeDatabase() {
  const client = await pool.connect();
  try {
    await client.query(createBatchesTableSQL);
    console.log('✅ Batches table ready');
    
    await client.query(createTravelersTableSQL);
    console.log('✅ Travelers table ready with 33 fields');
    
    // Insert sample batches if none exist
    const batchCheck = await client.query('SELECT COUNT(*) FROM batches');
    if (parseInt(batchCheck.rows[0].count) === 0) {
      await client.query(`
        INSERT INTO batches (batch_name, departure_date, return_date, total_seats, status) 
        VALUES 
          ('Haj-2024-001', '2024-06-15', '2024-07-30', 150, 'Open'),
          ('Haj-2024-002', '2024-07-01', '2024-08-15', 150, 'Open'),
          ('Haj-2024-003', '2024-07-15', '2024-08-30', 150, 'Open')
        ON CONFLICT (batch_name) DO NOTHING;
      `);
      console.log('✅ Sample batches created');
    }
  } catch (error) {
    console.error('❌ Database initialization error:', error);
    throw error;
  } finally {
    client.release();
  }
}

module.exports = { pool, initializeDatabase };