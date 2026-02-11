const express = require('express');
const router = express.Router();
const { pool } = require('../database');

// GET all travelers
router.get('/', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT t.*, b.batch_name 
      FROM travelers t 
      LEFT JOIN batches b ON t.batch_id = b.id 
      ORDER BY t.created_at DESC
    `);
    res.json({
      success: true,
      count: result.rowCount,
      travelers: result.rows
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET single traveler by ID
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query(`
      SELECT t.*, b.batch_name 
      FROM travelers t 
      LEFT JOIN batches b ON t.batch_id = b.id 
      WHERE t.id = $1
    `, [id]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ success: false, error: 'Traveler not found' });
    }
    
    res.json({ success: true, traveler: result.rows[0] });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// POST create new traveler - COMPLETE 33 FIELDS
router.post('/', async (req, res) => {
  try {
    const {
      first_name,
      last_name,
      batch_id,
      passport_no,
      passport_issue_date,
      passport_expiry_date,
      passport_status,
      gender,
      dob,
      mobile,
      email,
      aadhaar,
      pan,
      aadhaar_pan_linked,
      vaccine_status,
      wheelchair,
      place_of_birth,
      place_of_issue,
      passport_address,
      father_name,
      mother_name,
      spouse_name,
      passport_scan,
      aadhaar_scan,
      pan_scan,
      vaccine_scan,
      extra_fields
    } = req.body;

    // Validate required fields
    if (!first_name || !last_name || !passport_no || !mobile) {
      return res.status(400).json({
        success: false,
        error: 'First name, last name, passport number, and mobile are required'
      });
    }

    // Insert ALL 28 input fields into database
    const result = await pool.query(
      `INSERT INTO travelers (
        first_name, last_name, batch_id, passport_no,
        passport_issue_date, passport_expiry_date, passport_status,
        gender, dob, mobile, email, aadhaar, pan,
        aadhaar_pan_linked, vaccine_status, wheelchair,
        place_of_birth, place_of_issue, passport_address,
        father_name, mother_name, spouse_name,
        passport_scan, aadhaar_scan, pan_scan, vaccine_scan,
        extra_fields
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28)
      RETURNING *`,
      [
        first_name, last_name, batch_id, passport_no,
        passport_issue_date, passport_expiry_date, passport_status || 'Active',
        gender, dob, mobile, email, aadhaar, pan,
        aadhaar_pan_linked || 'No', vaccine_status || 'Not Vaccinated', wheelchair || 'No',
        place_of_birth, place_of_issue, passport_address,
        father_name, mother_name, spouse_name,
        passport_scan, aadhaar_scan, pan_scan, vaccine_scan,
        extra_fields || {}
      ]
    );

    res.status(201).json({
      success: true,
      message: 'Traveler created successfully with all 33 fields',
      traveler: result.rows[0]
    });
  } catch (error) {
    if (error.code === '23505') {
      return res.status(400).json({
        success: false,
        error: 'Duplicate passport number, Aadhaar, or PAN'
      });
    }
    console.error('Error creating traveler:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// PUT update traveler - COMPLETE 33 FIELDS
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const updates = req.body;
    
    // Remove system fields from updates
    delete updates.id;
    delete updates.created_at;
    delete updates.updated_at;
    delete updates.passport_name;
    
    if (Object.keys(updates).length === 0) {
      return res.status(400).json({ success: false, error: 'No fields to update' });
    }

    // Build dynamic SET clause
    const setClause = Object.keys(updates)
      .map((key, index) => `${key} = $${index + 1}`)
      .join(', ');
    
    const values = Object.values(updates);
    values.push(id);

    const query = `
      UPDATE travelers 
      SET ${setClause}, updated_at = CURRENT_TIMESTAMP 
      WHERE id = $${values.length} 
      RETURNING *
    `;

    const result = await pool.query(query, values);

    if (result.rows.length === 0) {
      return res.status(404).json({ success: false, error: 'Traveler not found' });
    }

    res.json({
      success: true,
      message: 'Traveler updated successfully with all 33 fields',
      traveler: result.rows[0]
    });
  } catch (error) {
    console.error('Error updating traveler:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// DELETE traveler
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const result = await pool.query(
      'DELETE FROM travelers WHERE id = $1 RETURNING id',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ success: false, error: 'Traveler not found' });
    }

    res.json({
      success: true,
      message: 'Traveler deleted successfully',
      deletedId: result.rows[0].id
    });
  } catch (error) {
    console.error('Error deleting traveler:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET batches list
router.get('/batches/list', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT id, batch_name, departure_date, return_date, total_seats, booked_seats, status FROM batches ORDER BY departure_date'
    );
    res.json({ success: true, batches: result.rows });
  } catch (error) {
    console.error('Error fetching batches:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET statistics
router.get('/stats/summary', async (req, res) => {
  try {
    const totalTravelers = await pool.query('SELECT COUNT(*) FROM travelers');
    const activeTravelers = await pool.query("SELECT COUNT(*) FROM travelers WHERE passport_status = 'Active'");
    const batches = await pool.query("SELECT COUNT(*) FROM batches WHERE status = 'Open'");
    const todayRegistrations = await pool.query(
      "SELECT COUNT(*) FROM travelers WHERE created_at::date = CURRENT_DATE"
    );

    res.json({
      success: true,
      stats: {
        totalTravelers: parseInt(totalTravelers.rows[0].count),
        activeTravelers: parseInt(activeTravelers.rows[0].count),
        openBatches: parseInt(batches.rows[0].count),
        todayRegistrations: parseInt(todayRegistrations.rows[0].count)
      }
    });
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

module.exports = router;