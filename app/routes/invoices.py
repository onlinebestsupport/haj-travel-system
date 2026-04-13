from flask import Blueprint, request, jsonify, session
from app.database import get_db, release_db
from datetime import datetime
import json

bp = Blueprint('invoices', __name__, url_prefix='/api/invoices')

@bp.route('', methods=['GET'])
def get_invoices():
    """Get all invoices with traveler and batch details"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("""
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
        """)
        invoices = cursor.fetchall()
        
        result = []
        for inv in invoices:
            inv_dict = dict(inv)
            # Parse items JSON to extract GST/TCS details for display
            if inv_dict.get('items'):
                try:
                    items_data = json.loads(inv_dict['items']) if isinstance(inv_dict['items'], str) else inv_dict['items']
                    inv_dict['gst_percent'] = items_data.get('gst_percent', 5)
                    inv_dict['gst_amount'] = items_data.get('gst_amount', 0)
                    inv_dict['tcs_percent'] = items_data.get('tcs_percent', 1)
                    inv_dict['tcs_amount'] = items_data.get('tcs_amount', 0)
                    inv_dict['base_amount'] = items_data.get('base_amount', inv_dict.get('amount', 0))
                except:
                    pass
            
            inv_dict['traveler_name'] = f"{inv_dict.get('first_name', '')} {inv_dict.get('last_name', '')}".strip()
            result.append(inv_dict)
        
        return jsonify({'success': True, 'invoices': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('', methods=['POST'])
def create_invoice():
    """Create new invoice with GST/TCS stored in items JSON"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.json
    required = ['traveler_id', 'amount']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400

    # Calculate taxes
    base_amount = float(data.get('amount', 0))
    gst_percent = float(data.get('gst_percent', 5))
    tcs_percent = float(data.get('tcs_percent', 1))
    gst_amount = base_amount * (gst_percent / 100)
    subtotal = base_amount + gst_amount
    tcs_amount = subtotal * (tcs_percent / 100)
    total_amount = subtotal + tcs_amount
    
    # Store all tax details in items JSON
    items_data = {
        'base_amount': base_amount,
        'gst_percent': gst_percent,
        'gst_amount': gst_amount,
        'tcs_percent': tcs_percent,
        'tcs_amount': tcs_amount,
        'total_amount': total_amount,
        'description': data.get('description', 'Travel Package'),
        'hsn_code': data.get('hsn_code', '9985')
    }
    
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{data['traveler_id']}-{int(datetime.now().timestamp())}"
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("""
            INSERT INTO invoices (
                invoice_number, traveler_id, batch_id, amount, paid_amount, 
                due_date, status, items, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            invoice_number,
            data['traveler_id'],
            data.get('batch_id'),
            total_amount,  # Store total amount with taxes
            data.get('paid_amount', 0),
            data.get('due_date'),
            data.get('status', 'pending'),
            json.dumps(items_data),
            datetime.now(),
            datetime.now()
        ))
        
        result = cursor.fetchone()
        invoice_id = result['id'] if result else None
        conn.commit()
        
        return jsonify({
            'success': True,
            'invoice_id': invoice_id,
            'invoice_number': invoice_number,
            'total_amount': total_amount,
            'message': 'Invoice created successfully'
        })
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    """Get single invoice with parsed items"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("""
            SELECT i.*, t.first_name, t.last_name, t.passport_no, t.email, t.mobile,
                   b.batch_name
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            LEFT JOIN batches b ON i.batch_id = b.id
            WHERE i.id = %s
        """, (invoice_id,))
        invoice = cursor.fetchone()
        
        if not invoice:
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404
        
        inv_dict = dict(invoice)
        if inv_dict.get('items'):
            try:
                items_data = json.loads(inv_dict['items']) if isinstance(inv_dict['items'], str) else inv_dict['items']
                inv_dict.update(items_data)
            except:
                pass
        
        return jsonify({'success': True, 'invoice': inv_dict})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:invoice_id>', methods=['PUT'])
def update_invoice(invoice_id):
    """Update invoice"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.json
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute('SELECT id FROM invoices WHERE id = %s', (invoice_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404
        
        cursor.execute("""
            UPDATE invoices SET
                amount = %s,
                paid_amount = %s,
                due_date = %s,
                status = %s,
                items = %s,
                updated_at = %s
            WHERE id = %s
        """, (
            data.get('amount'),
            data.get('paid_amount', 0),
            data.get('due_date'),
            data.get('status', 'pending'),
            json.dumps(data.get('items', {})),
            datetime.now(),
            invoice_id
        ))
        conn.commit()
        return jsonify({'success': True, 'message': 'Invoice updated successfully'})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/stats', methods=['GET'])
def get_invoice_stats():
    """Get invoice statistics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("""
            SELECT
                COUNT(*) as total_invoices,
                SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_count,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                SUM(CASE WHEN status = 'partial' THEN 1 ELSE 0 END) as partial_count,
                COALESCE(SUM(amount), 0) as total_amount,
                COALESCE(SUM(paid_amount), 0) as total_paid,
                COALESCE(SUM(amount) - SUM(paid_amount), 0) as total_due
            FROM invoices
        """)
        stats = cursor.fetchone()
        stats_dict = dict(stats) if stats else {}
        for key in ['total_amount', 'total_paid', 'total_due']:
            if key in stats_dict and stats_dict[key] is not None:
                stats_dict[key] = float(stats_dict[key])
        
        return jsonify({'success': True, 'stats': stats_dict})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:invoice_id>/mark-paid', methods=['POST'])
def mark_invoice_paid(invoice_id):
    """Mark invoice as paid (full or partial)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.json
    amount = float(data.get('amount', 0))
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute('SELECT amount, paid_amount, status FROM invoices WHERE id = %s', (invoice_id,))
        invoice = cursor.fetchone()
        
        if not invoice:
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404
        
        total_amount = float(invoice['amount'])
        current_paid = float(invoice['paid_amount']) if invoice['paid_amount'] else 0
        new_paid = current_paid + amount
        
        if new_paid > total_amount + 0.01:
            return jsonify({'success': False, 'error': 'Payment exceeds remaining balance'}), 400
        
        new_status = 'paid' if abs(new_paid - total_amount) < 0.01 else ('partial' if new_paid > 0 else 'pending')
        
        cursor.execute("""
            UPDATE invoices SET paid_amount = %s, status = %s, updated_at = %s WHERE id = %s
        """, (new_paid, new_status, datetime.now(), invoice_id))
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment recorded',
            'remaining': total_amount - new_paid,
            'status': new_status
        })
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if conn:
            release_db(conn, cursor)