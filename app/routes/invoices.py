from flask import Blueprint, request, jsonify, session
from app.database import release_db, get_db
from datetime import datetime
import json

bp = Blueprint('invoices', __name__, url_prefix='/api/invoices')

@bp.route('', methods=['GET'])
def get_invoice(invoice_id):
    """Get single invoice"""
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT * FROM invoices WHERE id = %s", (invoice_id,))
        invoice = cursor.fetchone()
        if not invoice:
            return jsonify({"success": False, "error": "Invoice not found"}), 404
        return jsonify({"success": True, "invoice": dict(invoice)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

def get_invoice(invoice_id):
    """Get single invoice"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    try:
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
        WHERE i.id = %s
    ''', (invoice_id,))
    
    invoice = cursor.fetchone()
    cursor.close()
    conn.close()
    finally:
        release_db(conn, cursor)
    
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
    timestamp = int(datetime.now().timestamp())
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{data['traveler_id']}-{timestamp}"
    
    # Calculate GST and TCS
    try:
        base_amount = float(data['base_amount'])
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid base amount'}), 400
    
    gst_percent = float(data.get('gst_percent', 5))
    tcs_percent = float(data.get('tcs_percent', 1))
    
    gst_amount = base_amount * (gst_percent / 100)
    tcs_amount = base_amount * (tcs_percent / 100)
    total_amount = base_amount + gst_amount + tcs_amount
    
    conn, cursor = get_db()
    
    try:
        try:
        cursor.execute('''
            INSERT INTO invoices (
                invoice_number, traveler_id, batch_id, invoice_date, due_date,
                base_amount, gst_percent, gst_amount, tcs_percent, tcs_amount,
                total_amount, hsn_code, place_of_supply, notes, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
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
            datetime.now(),
            datetime.now()
        ))
        
        result = cursor.fetchone()
        invoice_id = result['id'] if result else None
        
        # Log activity
        log_activity(session['user_id'], 'create', 'invoice', f'Created invoice: {invoice_number}')
        
        conn.commit()
        cursor.close()
        conn.close()
    finally:
        release_db(conn, cursor)
        
        return jsonify({
            'success': True,
            'invoice_id': invoice_id,
            'invoice_number': invoice_number,
            'message': 'Invoice created successfully'
        })
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/<int:invoice_id>', methods=['PUT'])
def update_invoice(invoice_id):
    """Update invoice"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    conn, cursor = get_db()
    
    try:
        # Check if invoice exists
        try:
        cursor.execute('SELECT id FROM invoices WHERE id = %s', (invoice_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
    finally:
        release_db(conn, cursor)
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404
        
        # Recalculate if base_amount changed
        base_amount = float(data.get('base_amount', 0))
        gst_percent = float(data.get('gst_percent', 5))
        tcs_percent = float(data.get('tcs_percent', 1))
        
        gst_amount = base_amount * (gst_percent / 100)
        tcs_amount = base_amount * (tcs_percent / 100)
        total_amount = base_amount + gst_amount + tcs_amount
        
        try:
        cursor.execute('''
            UPDATE invoices SET
                invoice_date = %s,
                due_date = %s,
                base_amount = %s,
                gst_percent = %s,
                gst_amount = %s,
                tcs_percent = %s,
                tcs_amount = %s,
                total_amount = %s,
                paid_amount = %s,
                status = %s,
                hsn_code = %s,
                place_of_supply = %s,
                notes = %s,
                updated_at = %s
            WHERE id = %s
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
            datetime.now(),
            invoice_id
        ))
        
        # Log activity
        log_activity(session['user_id'], 'update', 'invoice', f'Updated invoice ID: {invoice_id}')
        
        conn.commit()
        cursor.close()
        conn.close()
    finally:
        release_db(conn, cursor)
        
        return jsonify({'success': True, 'message': 'Invoice updated successfully'})
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/<int:invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    """Delete invoice"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    try:
        # Check if invoice has receipts
        try:
        cursor.execute('SELECT COUNT(*) as count FROM receipts WHERE invoice_id = %s', (invoice_id,))
        result = cursor.fetchone()
        
        if result and result['count'] > 0:
            cursor.close()
            conn.close()
    finally:
        release_db(conn, cursor)
            return jsonify({
                'success': False, 
                'error': 'Cannot delete invoice with associated receipts. Delete receipts first.'
            }), 400
        
        try:
        cursor.execute('DELETE FROM invoices WHERE id = %s', (invoice_id,))
        
        # Log activity
        log_activity(session['user_id'], 'delete', 'invoice', f'Deleted invoice ID: {invoice_id}')
        
        conn.commit()
        cursor.close()
        conn.close()
    finally:
        release_db(conn, cursor)
        
        return jsonify({'success': True, 'message': 'Invoice deleted successfully'})
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/stats', methods=['GET'])
def get_invoice_stats():
    """Get invoice statistics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    try:
        try:
        cursor.execute('''
            SELECT 
                COUNT(*) as total_invoices,
                SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_count,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                SUM(CASE WHEN status = 'overdue' THEN 1 ELSE 0 END) as overdue_count,
                COALESCE(SUM(total_amount), 0) as total_amount,
                COALESCE(SUM(paid_amount), 0) as total_paid
            FROM invoices
        ''')
        stats = cursor.fetchone()
        cursor.close()
        conn.close()
    finally:
        release_db(conn, cursor)
        
        if stats:
            stats_dict = dict(stats)
            for key in ['total_amount', 'total_paid']:
                if key in stats_dict and stats_dict[key] is not None:
                    stats_dict[key] = float(stats_dict[key])
        else:
            stats_dict = {}
        
        return jsonify({'success': True, 'stats': stats_dict})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    # Convert Decimal to float for JSON serialization
    if stats:
        stats_dict = dict(stats)
        for key in ['total_amount', 'total_paid', 'total_due']:
            if key in stats_dict and stats_dict[key] is not None:
                stats_dict[key] = float(stats_dict[key])
    else:
        stats_dict = {}
    
    return jsonify({
        'success': True,
        'stats': stats_dict
    })

@bp.route('/traveler/<int:traveler_id>', methods=['GET'])
def get_traveler_invoices(traveler_id):
    """Get invoices for a specific traveler"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    try:
        cursor.execute('''
        SELECT 
            i.*,
            b.batch_name
        FROM invoices i
        LEFT JOIN batches b ON i.batch_id = b.id
        WHERE i.traveler_id = %s
        ORDER BY i.created_at DESC
    ''', (traveler_id,))
    
    invoices = cursor.fetchall()
        conn.commit()
    except Exception as e:
        return jsonify({\'success\': False, \'error\': str(e)}), 500
    finally:
        release_db(conn, cursor)
        conn.commit()
    except Exception as e:
        return jsonify({\'success\': False, \'error\': str(e)}), 500
    finally:
        release_db(conn, cursor)    cursor.close()
    conn.close()
    finally:
        release_db(conn, cursor)
    
    return jsonify({
        'success': True,
        'invoices': [dict(inv) for inv in invoices]
    })

@bp.route('/number/<string:invoice_number>', methods=['GET'])
def get_invoice_by_number(invoice_number):
    """Get invoice by invoice number"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    try:
        cursor.execute('''
        SELECT 
            i.*,
            t.first_name,
            t.last_name,
            t.passport_no,
            t.mobile,
            t.email,
            b.batch_name
        FROM invoices i
        LEFT JOIN travelers t ON i.traveler_id = t.id
        LEFT JOIN batches b ON i.batch_id = b.id
        WHERE i.invoice_number = %s
    ''', (invoice_number,))
    
    invoice = cursor.fetchone()
    cursor.close()
    conn.close()
    finally:
        release_db(conn, cursor)
    
    if not invoice:
        return jsonify({'success': False, 'error': 'Invoice not found'}), 404
    
    return jsonify({'success': True, 'invoice': dict(invoice)})

@bp.route('/<int:invoice_id>/mark-paid', methods=['POST'])
def mark_invoice_paid(invoice_id):
    """Mark invoice as paid"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    amount = float(data.get('amount', 0))
    
    conn, cursor = get_db()
    
    try:
        # Get current invoice
        try:
        cursor.execute('SELECT total_amount, paid_amount, status FROM invoices WHERE id = %s', (invoice_id,))
        invoice = cursor.fetchone()
        
        if not invoice:
            cursor.close()
            conn.close()
    finally:
        release_db(conn, cursor)
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404
        
        total_amount = float(invoice['total_amount'])
        current_paid = float(invoice['paid_amount']) if invoice['paid_amount'] else 0
        
        new_paid = current_paid + amount
        if new_paid > total_amount:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False, 
                'error': f'Payment amount (₹{amount}) exceeds remaining balance (₹{total_amount - current_paid})'
            }), 400
        
        # Update paid amount
        new_status = 'paid' if abs(new_paid - total_amount) < 0.01 else 'partial'
        
        try:
        cursor.execute('''
            UPDATE invoices SET
                paid_amount = %s,
                status = %s,
                updated_at = %s
            WHERE id = %s
        ''', (new_paid, new_status, datetime.now(), invoice_id))
        
        # Log activity
        log_activity(
            session['user_id'], 
            'mark_paid', 
            'invoice', 
            f'Marked invoice {invoice_id} as paid: ₹{amount}'
        )
        
        conn.commit()
        cursor.close()
        conn.close()
    finally:
        release_db(conn, cursor)
        
        return jsonify({
            'success': True,
            'message': 'Invoice payment recorded',
            'remaining': total_amount - new_paid,
            'status': new_status
        })
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 400

# Helper function to log activity
def log_activity(user_id, action, module, description):
    """Log user activity"""
    try:
        conn, cursor = get_db()
        try:
        cursor.execute(
            'INSERT INTO activity_log (user_id, action, module, description, ip_address, created_at) VALUES (%s, %s, %s, %s, %s, %s)',
            (user_id, action, module, description, request.remote_addr, datetime.now())
        )
        conn.commit()
        cursor.close()
        conn.close()
    finally:
        release_db(conn, cursor)
    except Exception as e:
        print(f"⚠️ Activity log error: {e}")
