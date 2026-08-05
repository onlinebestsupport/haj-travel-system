/**
 * invoices.js - Invoice Management API Routes
 * Handles CRUD operations for invoices with GST/TCS calculations
 * For Node.js/Express backend
 */

const express = require('express');
const router = express.Router();
const pool = require('../db'); // Your database connection pool

// ====== GET ALL INVOICES ======
router.get('/api/invoices', async (req, res) => {
    try {
        const [rows] = await pool.query(`
            SELECT 
                i.*,
                CONCAT(t.first_name, ' ', t.last_name) AS traveler_name,
                t.first_name,
                t.last_name,
                t.passport_no,
                t.phone,
                b.batch_name,
                b.price AS batch_price
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            LEFT JOIN batches b ON i.batch_id = b.id
            ORDER BY i.created_at DESC
        `);
        
        res.json({ 
            success: true, 
            invoices: rows,
            count: rows.length
        });
    } catch (error) {
        console.error('Error fetching invoices:', error);
        res.status(500).json({ 
            success: false, 
            message: error.message 
        });
    }
});

// ====== GET SINGLE INVOICE ======
router.get('/api/invoices/:id', async (req, res) => {
    try {
        const [rows] = await pool.query(`
            SELECT 
                i.*,
                CONCAT(t.first_name, ' ', t.last_name) AS traveler_name,
                t.first_name,
                t.last_name,
                t.passport_no,
                t.phone,
                t.email,
                b.batch_name,
                b.price AS batch_price,
                b.departure_date,
                b.return_date
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            LEFT JOIN batches b ON i.batch_id = b.id
            WHERE i.id = ?
        `, [req.params.id]);
        
        if (rows.length === 0) {
            return res.status(404).json({ 
                success: false, 
                message: 'Invoice not found' 
            });
        }
        
        res.json({ 
            success: true, 
            invoice: rows[0] 
        });
    } catch (error) {
        console.error('Error fetching invoice:', error);
        res.status(500).json({ 
            success: false, 
            message: error.message 
        });
    }
});

// ====== GET INVOICES BY TRAVELER ======
router.get('/api/invoices/traveler/:travelerId', async (req, res) => {
    try {
        const [rows] = await pool.query(`
            SELECT 
                i.*,
                b.batch_name
            FROM invoices i
            LEFT JOIN batches b ON i.batch_id = b.id
            WHERE i.traveler_id = ?
            ORDER BY i.created_at DESC
        `, [req.params.travelerId]);
        
        res.json({ 
            success: true, 
            invoices: rows 
        });
    } catch (error) {
        console.error('Error fetching traveler invoices:', error);
        res.status(500).json({ 
            success: false, 
            message: error.message 
        });
    }
});

// ====== CREATE INVOICE ======
router.post('/api/invoices', async (req, res) => {
    try {
        const {
            traveler_id,
            batch_id,
            base_amount,
            gst_percent,
            gst_amount,
            tcs_percent,
            tcs_amount,
            total_amount,
            status,
            due_date,
            notes,
            invoice_date
        } = req.body;

        // Validate required fields
        if (!traveler_id) {
            return res.status(400).json({ 
                success: false, 
                message: 'Traveler ID is required' 
            });
        }

        if (!base_amount || base_amount <= 0) {
            return res.status(400).json({ 
                success: false, 
                message: 'Base amount must be greater than 0' 
            });
        }

        // Check if traveler exists
        const [traveler] = await pool.query(
            'SELECT id, first_name, last_name FROM travelers WHERE id = ?',
            [traveler_id]
        );
        
        if (traveler.length === 0) {
            return res.status(404).json({ 
                success: false, 
                message: 'Traveler not found' 
            });
        }

        // Generate unique invoice number
        const [count] = await pool.query('SELECT COUNT(*) as count FROM invoices');
        const invoiceNumber = `INV-${String(count[0].count + 1).padStart(6, '0')}`;

        // Calculate amounts if not provided
        const gstPercent = gst_percent || 5;
        const gstAmount = gst_amount || (base_amount * gstPercent / 100);
        const subtotal = base_amount + gstAmount;
        const tcsPercent = tcs_percent || 1;
        const tcsAmount = tcs_amount || (subtotal * tcsPercent / 100);
        const total = total_amount || (subtotal + tcsAmount);

        // Insert invoice
        const [result] = await pool.query(`
            INSERT INTO invoices (
                invoice_number,
                traveler_id,
                batch_id,
                base_amount,
                gst_percent,
                gst_amount,
                tcs_percent,
                tcs_amount,
                total_amount,
                status,
                due_date,
                notes,
                invoice_date,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
        `, [
            invoiceNumber,
            traveler_id,
            batch_id || null,
            base_amount,
            gstPercent,
            gstAmount,
            tcsPercent,
            tcsAmount,
            total,
            status || 'pending',
            due_date || null,
            notes || null,
            invoice_date || new Date().toISOString().split('T')[0]
        ]);

        if (result.affectedRows === 0) {
            throw new Error('Failed to insert invoice');
        }

        // Update traveler's total_paid if status is 'paid'
        if (status === 'paid') {
            await pool.query(`
                UPDATE travelers 
                SET total_paid = COALESCE(total_paid, 0) + ? 
                WHERE id = ?
            `, [total, traveler_id]);
        }

        // Get the created invoice
        const [newInvoice] = await pool.query(`
            SELECT 
                i.*,
                CONCAT(t.first_name, ' ', t.last_name) AS traveler_name
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            WHERE i.id = ?
        `, [result.insertId]);

        res.json({ 
            success: true, 
            message: 'Invoice created successfully',
            invoice: newInvoice[0]
        });

    } catch (error) {
        console.error('Error creating invoice:', error);
        res.status(500).json({ 
            success: false, 
            message: error.message || 'Failed to create invoice' 
        });
    }
});

// ====== UPDATE INVOICE ======
router.put('/api/invoices/:id', async (req, res) => {
    try {
        const { 
            total_amount, 
            status, 
            due_date, 
            notes,
            gst_percent,
            gst_amount,
            tcs_percent,
            tcs_amount,
            base_amount
        } = req.body;
        const invoiceId = req.params.id;

        // Get current invoice data
        const [current] = await pool.query(
            'SELECT traveler_id, total_amount, status, base_amount FROM invoices WHERE id = ?',
            [invoiceId]
        );

        if (current.length === 0) {
            return res.status(404).json({ 
                success: false, 
                message: 'Invoice not found' 
            });
        }

        const oldStatus = current[0].status;
        const oldAmount = parseFloat(current[0].total_amount) || 0;
        const travelerId = current[0].traveler_id;

        // Build update query dynamically
        let updateFields = [];
        let updateValues = [];

        if (total_amount !== undefined) {
            updateFields.push('total_amount = ?');
            updateValues.push(total_amount);
        }
        if (status !== undefined) {
            updateFields.push('status = ?');
            updateValues.push(status);
        }
        if (due_date !== undefined) {
            updateFields.push('due_date = ?');
            updateValues.push(due_date);
        }
        if (notes !== undefined) {
            updateFields.push('notes = ?');
            updateValues.push(notes);
        }
        if (gst_percent !== undefined) {
            updateFields.push('gst_percent = ?');
            updateValues.push(gst_percent);
        }
        if (gst_amount !== undefined) {
            updateFields.push('gst_amount = ?');
            updateValues.push(gst_amount);
        }
        if (tcs_percent !== undefined) {
            updateFields.push('tcs_percent = ?');
            updateValues.push(tcs_percent);
        }
        if (tcs_amount !== undefined) {
            updateFields.push('tcs_amount = ?');
            updateValues.push(tcs_amount);
        }
        if (base_amount !== undefined) {
            updateFields.push('base_amount = ?');
            updateValues.push(base_amount);
        }

        if (updateFields.length === 0) {
            return res.status(400).json({ 
                success: false, 
                message: 'No fields to update' 
            });
        }

        updateFields.push('updated_at = NOW()');
        updateValues.push(invoiceId);

        const query = `UPDATE invoices SET ${updateFields.join(', ')} WHERE id = ?`;
        const [result] = await pool.query(query, updateValues);

        if (result.affectedRows === 0) {
            return res.status(404).json({ 
                success: false, 
                message: 'Invoice not found' 
            });
        }

        // Update traveler's total_paid based on status change
        if (oldStatus !== status) {
            const newAmount = parseFloat(total_amount || current[0].total_amount);
            
            if (status === 'paid') {
                // Add amount to total_paid
                await pool.query(
                    'UPDATE travelers SET total_paid = COALESCE(total_paid, 0) + ? WHERE id = ?',
                    [newAmount, travelerId]
                );
            } else if (oldStatus === 'paid') {
                // Subtract amount from total_paid
                await pool.query(
                    'UPDATE travelers SET total_paid = COALESCE(total_paid, 0) - ? WHERE id = ?',
                    [oldAmount, travelerId]
                );
            }
        } else if (status === 'paid' && parseFloat(total_amount) !== oldAmount) {
            // Update total_paid if amount changed while status is paid
            const diff = parseFloat(total_amount) - oldAmount;
            await pool.query(
                'UPDATE travelers SET total_paid = COALESCE(total_paid, 0) + ? WHERE id = ?',
                [diff, travelerId]
            );
        }

        // Get updated invoice
        const [updated] = await pool.query(`
            SELECT 
                i.*,
                CONCAT(t.first_name, ' ', t.last_name) AS traveler_name
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            WHERE i.id = ?
        `, [invoiceId]);

        res.json({ 
            success: true, 
            message: 'Invoice updated successfully',
            invoice: updated[0]
        });

    } catch (error) {
        console.error('Error updating invoice:', error);
        res.status(500).json({ 
            success: false, 
            message: error.message 
        });
    }
});

// ====== DELETE INVOICE ======
router.delete('/api/invoices/:id', async (req, res) => {
    try {
        // Get invoice data before deleting
        const [invoice] = await pool.query(
            'SELECT traveler_id, total_amount, status FROM invoices WHERE id = ?',
            [req.params.id]
        );

        if (invoice.length === 0) {
            return res.status(404).json({ 
                success: false, 
                message: 'Invoice not found' 
            });
        }

        // If invoice was paid, subtract from traveler's total_paid
        if (invoice[0].status === 'paid') {
            await pool.query(
                'UPDATE travelers SET total_paid = COALESCE(total_paid, 0) - ? WHERE id = ?',
                [parseFloat(invoice[0].total_amount) || 0, invoice[0].traveler_id]
            );
        }

        // Delete the invoice
        const [result] = await pool.query(
            'DELETE FROM invoices WHERE id = ?',
            [req.params.id]
        );

        if (result.affectedRows === 0) {
            return res.status(404).json({ 
                success: false, 
                message: 'Invoice not found' 
            });
        }

        res.json({ 
            success: true, 
            message: 'Invoice deleted successfully' 
        });

    } catch (error) {
        console.error('Error deleting invoice:', error);
        res.status(500).json({ 
            success: false, 
            message: error.message 
        });
    }
});

// ====== GET INVOICE STATISTICS ======
router.get('/api/invoices/stats', async (req, res) => {
    try {
        const [stats] = await pool.query(`
            SELECT 
                COUNT(*) as total_invoices,
                SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_count,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_count,
                COALESCE(SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END), 0) as total_revenue,
                COALESCE(SUM(CASE WHEN status = 'pending' THEN total_amount ELSE 0 END), 0) as pending_revenue
            FROM invoices
        `);
        
        res.json({ 
            success: true, 
            stats: stats[0] 
        });
    } catch (error) {
        console.error('Error fetching invoice stats:', error);
        res.status(500).json({ 
            success: false, 
            message: error.message 
        });
    }
});

// ====== GET INVOICE BY NUMBER ======
router.get('/api/invoices/number/:invoiceNumber', async (req, res) => {
    try {
        const [rows] = await pool.query(`
            SELECT 
                i.*,
                CONCAT(t.first_name, ' ', t.last_name) AS traveler_name,
                t.passport_no,
                b.batch_name
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            LEFT JOIN batches b ON i.batch_id = b.id
            WHERE i.invoice_number = ?
        `, [req.params.invoiceNumber]);
        
        if (rows.length === 0) {
            return res.status(404).json({ 
                success: false, 
                message: 'Invoice not found' 
            });
        }
        
        res.json({ 
            success: true, 
            invoice: rows[0] 
        });
    } catch (error) {
        console.error('Error fetching invoice:', error);
        res.status(500).json({ 
            success: false, 
            message: error.message 
        });
    }
});

module.exports = router;
