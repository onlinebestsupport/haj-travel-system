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
                i.id,
                i.invoice_number,
                i.amount,
                i.status,
                i.due_date,
                i.invoice_date,
                i.created_at,
                i.items,
                i.traveler_id,
                i.batch_id,
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
            # Convert Decimal to float for JSON
            if inv_dict.get('amount'):
                inv_dict['amount'] = float(inv_dict['amount'])
            
            # Parse items JSON for GST/TCS details
            if inv_dict.get('items'):
                try:
                    items_data = inv_dict['items'] if isinstance(inv_dict['items'], dict) else json.loads(inv_dict['items'])
                    inv_dict['base_amount'] = items_data.get('base_amount', inv_dict['amount'])
                    inv_dict['gst_percent'] = items_data.get('gst_percent', 5)
                    inv_dict['gst_amount'] = items_data.get('gst_amount', 0)
                    inv_dict['tcs_percent'] = items_data.get('tcs_percent', 1)
                    inv_dict['tcs_amount'] = items_data.get('tcs_amount', 0)
                except:
                    pass
            
            inv_dict['traveler_name'] = f"{inv_dict.get('first_name', '')} {inv_dict.get('last_name', '')}".strip()
            result.append(inv_dict)
        
        return jsonify({'success': True, 'invoices': result})
    except Exception as e:
        print(f"Error in get_invoices: {str(e)}")
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
        cursor.execute("""
            SELECT 
                COUNT(*) as total_invoices,
                SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_count,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                COALESCE(SUM(amount), 0) as total_amount
            FROM invoices
        """)
        stats = cursor.fetchone()
        
        stats_dict = {
            'total_invoices': stats['total_invoices'] or 0,
            'paid_count': stats['paid_count'] or 0,
            'pending_count': stats['pending_count'] or 0,
            'total_amount': float(stats['total_amount'] or 0)
        }
        
        return jsonify({'success': True, 'stats': stats_dict})
    except Exception as e:
        print(f"Error in get_invoice_stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('', methods=['POST'])
def create_invoice():
    """Create new invoice with GST/TCS calculation"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.json
    print(f"Creating invoice with data: {data}")

    # Validate required fields
    if not data.get('traveler_id'):
        return jsonify({'success': False, 'error': 'traveler_id is required'}), 400
    
    # Get base amount (without GST/TCS)
    base_amount = float(data.get('amount', 0))
    if base_amount <= 0:
        return jsonify({'success': False, 'error': 'Valid amount is required'}), 400

    # Calculate GST and TCS
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
            total_amount,  # Store total amount with taxes
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
        print(f"Error creating invoice: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    """Get single invoice details"""
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
                t.email,
                t.mobile,
                b.batch_name,
                b.amount as batch_amount
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            LEFT JOIN batches b ON i.batch_id = b.id
            WHERE i.id = %s
        """, (invoice_id,))
        
        invoice = cursor.fetchone()
        if not invoice:
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404
        
        inv_dict = dict(invoice)
        if inv_dict.get('amount'):
            inv_dict['amount'] = float(inv_dict['amount'])
        
        if inv_dict.get('items'):
            try:
                items_data = inv_dict['items'] if isinstance(inv_dict['items'], dict) else json.loads(inv_dict['items'])
                inv_dict.update(items_data)
            except:
                pass
        
        inv_dict['traveler_name'] = f"{inv_dict.get('first_name', '')} {inv_dict.get('last_name', '')}".strip()
        
        return jsonify({'success': True, 'invoice': inv_dict})
    except Exception as e:
        print(f"Error getting invoice: {str(e)}")
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
                due_date = %s,
                status = %s,
                updated_at = %s
            WHERE id = %s
        """, (
            data.get('amount'),
            data.get('due_date'),
            data.get('status', 'pending'),
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

@bp.route('/<int:invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    """Delete invoice"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute('DELETE FROM invoices WHERE id = %s RETURNING id', (invoice_id,))
        result = cursor.fetchone()
        conn.commit()
        
        if result:
            return jsonify({'success': True, 'message': 'Invoice deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/batch/<int:batch_id>', methods=['GET'])
def get_batch_details(batch_id):
    """Get batch details including amount"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT id, batch_name, amount FROM batches WHERE id = %s", (batch_id,))
        batch = cursor.fetchone()
        
        if batch:
            return jsonify({
                'success': True,
                'batch': {
                    'id': batch['id'],
                    'batch_name': batch['batch_name'],
                    'amount': float(batch['amount']) if batch['amount'] else 0
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Batch not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)