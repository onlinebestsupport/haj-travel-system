from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime
import json

bp = Blueprint('invoices', __name__, url_prefix='/api/invoices')

@bp.route('', methods=['GET'])
def get_invoices():
    """Get all invoices"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
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
            FOREIGN KEY (traveler_id) REFERENCES travelers(id) ON DELETE CASCADE,
            FOREIGN KEY (batch_id) REFERENCES batches(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        SELECT 
            i.*,
            t.first_name,
            t.last_name,
            t.passport_no,
            b.batch_name
        FROM invoices i
        LEFT JOIN travelers t ON i.traveler_id = t.id
        LEFT JOIN batches b ON i.batch_id = b.id
        ORDER BY i.created_at DESC
    ''')
    
    invoices = cursor.fetchall()
    db.close()
    
    return jsonify({
        'success': True,
        'invoices': [dict(inv) for inv in invoices]
    })

@bp.route('/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    """Get single invoice"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            i.*,
            t.first_name,
            t.last_name,
            t.passport_no,
            t.mobile,
            t.email,
            b.batch_name,
            b.price
        FROM invoices i
        LEFT JOIN travelers t ON i.traveler_id = t.id
        LEFT JOIN batches b ON i.batch_id = b.id
        WHERE i.id = ?
    ''', (invoice_id,))
    
    invoice = cursor.fetchone()
    db.close()
    
    if not invoice:
        return jsonify({'success': False, 'error': 'Invoice not found'}), 404
    
    return jsonify({'success': True, 'invoice': dict(invoice)})

@bp.route('', methods=['POST'])
def create_invoice():
    """Create new invoice"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    required = ['traveler_id', 'batch_id', 'base_amount', 'invoice_date']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    # Generate invoice number
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{data['traveler_id']}-{int(datetime.now().timestamp())}"
    
    # Calculate GST and TCS
    base_amount = float(data['base_amount'])
    gst_percent = float(data.get('gst_percent', 5))
    tcs_percent = float(data.get('tcs_percent', 1))
    
    gst_amount = base_amount * (gst_percent / 100)
    tcs_amount = base_amount * (tcs_percent / 100)
    total_amount = base_amount + gst_amount + tcs_amount
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO invoices (
                invoice_number, traveler_id, batch_id, invoice_date, due_date,
                base_amount, gst_percent, gst_amount, tcs_percent, tcs_amount,
                total_amount, hsn_code, place_of_supply, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            invoice_number,
            data['traveler_id'],
            data['batch_id'],
            data['invoice_date'],
            data.get('due_date'),
            base_amount,
            gst_percent,
            gst_amount,
            tcs_percent,
            tcs_amount,
            total_amount,
            data.get('hsn_code', '9985'),
            data.get('place_of_supply'),
            data.get('notes'),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        invoice_id = cursor.lastrowid
        db.commit()
        db.close()
        
        return jsonify({
            'success': True,
            'invoice_id': invoice_id,
            'invoice_number': invoice_number,
            'message': 'Invoice created successfully'
        })
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/<int:invoice_id>', methods=['PUT'])
def update_invoice(invoice_id):
    """Update invoice"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if invoice exists
        cursor.execute('SELECT id FROM invoices WHERE id = ?', (invoice_id,))
        if not cursor.fetchone():
            db.close()
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404
        
        # Recalculate if base_amount changed
        base_amount = float(data.get('base_amount', 0))
        gst_percent = float(data.get('gst_percent', 5))
        tcs_percent = float(data.get('tcs_percent', 1))
        
        gst_amount = base_amount * (gst_percent / 100)
        tcs_amount = base_amount * (tcs_percent / 100)
        total_amount = base_amount + gst_amount + tcs_amount
        
        cursor.execute('''
            UPDATE invoices SET
                invoice_date = ?,
                due_date = ?,
                base_amount = ?,
                gst_percent = ?,
                gst_amount = ?,
                tcs_percent = ?,
                tcs_amount = ?,
                total_amount = ?,
                paid_amount = ?,
                status = ?,
                hsn_code = ?,
                place_of_supply = ?,
                notes = ?,
                updated_at = ?
            WHERE id = ?
        ''', (
            data.get('invoice_date'),
            data.get('due_date'),
            base_amount,
            gst_percent,
            gst_amount,
            tcs_percent,
            tcs_amount,
            total_amount,
            data.get('paid_amount', 0),
            data.get('status', 'pending'),
            data.get('hsn_code', '9985'),
            data.get('place_of_supply'),
            data.get('notes'),
            datetime.now().isoformat(),
            invoice_id
        ))
        
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'message': 'Invoice updated successfully'})
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/<int:invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    """Delete invoice"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('DELETE FROM invoices WHERE id = ?', (invoice_id,))
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'message': 'Invoice deleted successfully'})
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/stats', methods=['GET'])
def get_invoice_stats():
    """Get invoice statistics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_invoices,
            SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_count,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
            SUM(CASE WHEN status = 'overdue' THEN 1 ELSE 0 END) as overdue_count,
            SUM(total_amount) as total_amount,
            SUM(paid_amount) as total_paid,
            SUM(total_amount - paid_amount) as total_due
        FROM invoices
    ''')
    
    stats = cursor.fetchone()
    db.close()
    
    return jsonify({
        'success': True,
        'stats': dict(stats) if stats else {}
    })

@bp.route('/traveler/<int:traveler_id>', methods=['GET'])
def get_traveler_invoices(traveler_id):
    """Get invoices for a specific traveler"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            i.*,
            b.batch_name
        FROM invoices i
        LEFT JOIN batches b ON i.batch_id = b.id
        WHERE i.traveler_id = ?
        ORDER BY i.created_at DESC
    ''', (traveler_id,))
    
    invoices = cursor.fetchall()
    db.close()
    
    return jsonify({
        'success': True,
        'invoices': [dict(inv) for inv in invoices]
    })
