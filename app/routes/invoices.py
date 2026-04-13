from flask import Blueprint, request, jsonify, session, send_file
from app.database import get_db, release_db
from datetime import datetime
import json
import io

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
                b.batch_name,
                b.amount as batch_amount
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            LEFT JOIN batches b ON i.batch_id = b.id
            ORDER BY i.created_at DESC
        """)
        invoices = cursor.fetchall()
        
        result = []
        for inv in invoices:
            inv_dict = dict(inv)
            # Parse items JSON to extract GST/TCS
            if inv_dict.get('items'):
                try:
                    items_data = inv_dict['items'] if isinstance(inv_dict['items'], dict) else json.loads(inv_dict['items'])
                    inv_dict['gst_percent'] = items_data.get('gst_percent', 5)
                    inv_dict['gst_amount'] = items_data.get('gst_amount', 0)
                    inv_dict['tcs_percent'] = items_data.get('tcs_percent', 1)
                    inv_dict['tcs_amount'] = items_data.get('tcs_amount', 0)
                    inv_dict['base_amount'] = items_data.get('base_amount', inv_dict.get('amount', 0))
                except:
                    pass
            
            inv_dict['traveler_name'] = f"{inv_dict.get('first_name', '')} {inv_dict.get('last_name', '')}".strip()
            inv_dict['batch_name'] = inv_dict.get('batch_name', '')
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

    # Validate required fields
    if not data.get('traveler_id'):
        return jsonify({'success': False, 'error': 'traveler_id is required'}), 400

    # Calculate taxes
    base_amount = float(data.get('amount', 0))
    gst_percent = float(data.get('gst_percent', 5))
    tcs_percent = float(data.get('tcs_percent', 1))
    
    gst_amount = base_amount * (gst_percent / 100)
    subtotal = base_amount + gst_amount
    tcs_amount = subtotal * (tcs_percent / 100)
    total_amount = subtotal + tcs_amount
    
    # Store ALL tax details in items JSON (since no separate columns)
    items_data = {
        'base_amount': base_amount,
        'gst_percent': gst_percent,
        'gst_amount': gst_amount,
        'tcs_percent': tcs_percent,
        'tcs_amount': tcs_amount,
        'total_amount': total_amount,
        'description': data.get('description', 'Travel Package'),
        'hsn_code': data.get('hsn_code', '9985'),
        'place_of_supply': data.get('place_of_supply', 'Maharashtra'),
        'notes': data.get('notes', '')
    }
    
    # Generate invoice number
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{data['traveler_id']}-{int(datetime.now().timestamp())}"
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        # Note: paid_amount column doesn't exist, so we track payments separately
        cursor.execute("""
            INSERT INTO invoices (
                invoice_number, traveler_id, batch_id, amount, 
                due_date, status, items, invoice_date, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            invoice_number,
            data['traveler_id'],
            data.get('batch_id'),
            total_amount,  # Store total with taxes
            data.get('due_date'),
            data.get('status', 'pending'),
            json.dumps(items_data),
            data.get('invoice_date', datetime.now().date()),
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
                items_data = inv_dict['items'] if isinstance(inv_dict['items'], dict) else json.loads(inv_dict['items'])
                inv_dict.update(items_data)
            except:
                pass
        
        return jsonify({'success': True, 'invoice': inv_dict})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
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
        
        # Since no paid_amount column, get payments from receipts table
        cursor.execute("""
            SELECT 
                COUNT(*) as total_invoices,
                SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_count,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                COALESCE(SUM(amount), 0) as total_amount
            FROM invoices
        """)
        stats = cursor.fetchone()
        
        # Get total paid from receipts
        cursor.execute("SELECT COALESCE(SUM(amount), 0) as total_paid FROM receipts")
        paid_result = cursor.fetchone()
        total_paid = float(paid_result['total_paid']) if paid_result else 0
        total_amount = float(stats['total_amount']) if stats else 0
        
        stats_dict = {
            'total_invoices': stats['total_invoices'] if stats else 0,
            'paid_count': stats['paid_count'] if stats else 0,
            'pending_count': stats['pending_count'] if stats else 0,
            'total_amount': total_amount,
            'total_paid': total_paid,
            'total_due': total_amount - total_paid
        }
        
        return jsonify({'success': True, 'stats': stats_dict})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:invoice_id>/payments', methods=['GET'])
def get_invoice_payments(invoice_id):
    """Get all payments for an invoice from receipts table"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("""
            SELECT id, amount, payment_date, payment_method, reference_no, notes
            FROM receipts
            WHERE invoice_id = %s
            ORDER BY payment_date DESC
        """, (invoice_id,))
        payments = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'payments': [dict(p) for p in payments],
            'total_paid': sum(float(p['amount']) for p in payments) if payments else 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)