from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime
import json

bp = Blueprint('receipts', __name__, url_prefix='/api/receipts')

@bp.route('', methods=['GET'])
def get_receipts():
    """Get all receipts"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    cursor.execute('''
        SELECT 
            r.*,
            t.first_name,
            t.last_name,
            t.passport_no,
            p.amount as payment_amount,
            p.payment_date
        FROM receipts r
        LEFT JOIN travelers t ON r.traveler_id = t.id
        LEFT JOIN payments p ON r.payment_id = p.id
        ORDER BY r.created_at DESC
    ''')
    
    receipts = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify({
        'success': True,
        'receipts': [dict(r) for r in receipts]
    })

@bp.route('/<int:receipt_id>', methods=['GET'])
def get_receipt(receipt_id):
    """Get single receipt"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    cursor.execute('''
        SELECT 
            r.*,
            t.first_name,
            t.last_name,
            t.passport_no,
            p.amount as payment_amount,
            p.payment_date,
            p.payment_method,
            i.invoice_number
        FROM receipts r
        LEFT JOIN travelers t ON r.traveler_id = t.id
        LEFT JOIN payments p ON r.payment_id = p.id
        LEFT JOIN invoices i ON r.invoice_id = i.id
        WHERE r.id = %s
    ''', (receipt_id,))
    
    receipt = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not receipt:
        return jsonify({'success': False, 'error': 'Receipt not found'}), 404
    
    return jsonify({'success': True, 'receipt': dict(receipt)})

@bp.route('', methods=['POST'])
def create_receipt():
    """Create new receipt"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    required = ['payment_id', 'traveler_id', 'receipt_date', 'amount']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    # Validate amount
    try:
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Amount must be greater than 0'}), 400
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid amount format'}), 400
    
    # Generate receipt number
    timestamp = int(datetime.now().timestamp())
    receipt_number = f"REC-{datetime.now().strftime('%Y%m%d')}-{data['traveler_id']}-{timestamp}"
    
    conn, cursor = get_db()
    
    try:
        # Check if payment exists
        cursor.execute('SELECT id, amount FROM payments WHERE id = %s', (data['payment_id'],))
        payment = cursor.fetchone()
        
        if not payment:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Payment not found'}), 404
        
        # Check if invoice exists if invoice_id provided
        if data.get('invoice_id'):
            cursor.execute('SELECT id FROM invoices WHERE id = %s', (data['invoice_id'],))
            if not cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': 'Invoice not found'}), 404
        
        cursor.execute('''
            INSERT INTO receipts (
                receipt_number, traveler_id, payment_id, invoice_id,
                receipt_date, amount, payment_method, transaction_id,
                receipt_type, installment_info, remarks, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            receipt_number,
            data['traveler_id'],
            data['payment_id'],
            data.get('invoice_id'),
            data['receipt_date'],
            amount,
            data.get('payment_method'),
            data.get('transaction_id'),
            data.get('receipt_type', 'payment'),
            data.get('installment_info'),
            data.get('remarks'),
            datetime.now()
        ))
        
        result = cursor.fetchone()
        receipt_id = result['id'] if result else None
        
        # Log activity
        log_activity(
            session['user_id'], 
            'create', 
            'receipt', 
            f'Created receipt: {receipt_number} for amount ₹{amount}'
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'receipt_id': receipt_id,
            'receipt_number': receipt_number,
            'message': 'Receipt created successfully'
        })
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/payment/<int:payment_id>', methods=['GET'])
def get_payment_receipts(payment_id):
    """Get receipts for a specific payment"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    cursor.execute('''
        SELECT * FROM receipts 
        WHERE payment_id = %s
        ORDER BY created_at DESC
    ''', (payment_id,))
    
    receipts = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify({
        'success': True,
        'receipts': [dict(r) for r in receipts]
    })

@bp.route('/traveler/<int:traveler_id>', methods=['GET'])
def get_traveler_receipts(traveler_id):
    """Get receipts for a specific traveler"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    cursor.execute('''
        SELECT 
            r.*,
            p.amount as payment_amount,
            p.payment_date,
            i.invoice_number
        FROM receipts r
        LEFT JOIN payments p ON r.payment_id = p.id
        LEFT JOIN invoices i ON r.invoice_id = i.id
        WHERE r.traveler_id = %s
        ORDER BY r.created_at DESC
    ''', (traveler_id,))
    
    receipts = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify({
        'success': True,
        'receipts': [dict(r) for r in receipts]
    })

@bp.route('/stats', methods=['GET'])
def get_receipt_stats():
    """Get receipt statistics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_receipts,
            COALESCE(SUM(amount), 0) as total_amount,
            COUNT(DISTINCT traveler_id) as unique_travelers,
            COUNT(DISTINCT payment_id) as unique_payments
        FROM receipts
    ''')
    
    stats = cursor.fetchone()
    cursor.close()
    conn.close()
    
    # Convert Decimal to float for JSON serialization
    if stats:
        stats_dict = dict(stats)
        if stats_dict.get('total_amount'):
            stats_dict['total_amount'] = float(stats_dict['total_amount'])
    else:
        stats_dict = {}
    
    return jsonify({
        'success': True,
        'stats': stats_dict
    })

@bp.route('/<int:receipt_id>/print', methods=['GET'])
def print_receipt(receipt_id):
    """Get receipt data formatted for printing"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    cursor.execute('''
        SELECT 
            r.*,
            t.first_name,
            t.last_name,
            t.passport_no,
            t.mobile,
            t.email,
            p.amount as payment_amount,
            p.payment_date,
            p.payment_method,
            p.transaction_id,
            b.batch_name,
            i.invoice_number,
            i.total_amount as invoice_total
        FROM receipts r
        LEFT JOIN travelers t ON r.traveler_id = t.id
        LEFT JOIN payments p ON r.payment_id = p.id
        LEFT JOIN batches b ON p.batch_id = b.id
        LEFT JOIN invoices i ON r.invoice_id = i.id
        WHERE r.id = %s
    ''', (receipt_id,))
    
    receipt = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not receipt:
        return jsonify({'success': False, 'error': 'Receipt not found'}), 404
    
    receipt_dict = dict(receipt)
    
    # Format for printing
    print_data = {
        'receipt_number': receipt_dict.get('receipt_number'),
        'date': receipt_dict.get('receipt_date'),
        'traveler_name': f"{receipt_dict.get('first_name', '')} {receipt_dict.get('last_name', '')}".strip(),
        'passport': receipt_dict.get('passport_no'),
        'mobile': receipt_dict.get('mobile'),
        'batch': receipt_dict.get('batch_name'),
        'amount': float(receipt_dict.get('amount', 0)),
        'amount_in_words': number_to_words(float(receipt_dict.get('amount', 0))),
        'payment_method': receipt_dict.get('payment_method'),
        'transaction_id': receipt_dict.get('transaction_id'),
        'payment_date': receipt_dict.get('payment_date'),
        'invoice_number': receipt_dict.get('invoice_number'),
        'remarks': receipt_dict.get('remarks'),
        'generated_on': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return jsonify({
        'success': True,
        'print_data': print_data
    })

# Helper function to convert number to words (simplified)
def number_to_words(n):
    """Convert number to words (simplified for Indian Rupees)"""
    if n == 0:
        return "Zero Rupees Only"
    
    # This is a simplified version - you might want to use a library for production
    return f"Rupees {n:,.2f} Only"

# Helper function to log activity
def log_activity(user_id, action, module, description):
    """Log user activity"""
    try:
        conn, cursor = get_db()
        cursor.execute(
            'INSERT INTO activity_log (user_id, action, module, description, ip_address, created_at) VALUES (%s, %s, %s, %s, %s, %s)',
            (user_id, action, module, description, request.remote_addr, datetime.now())
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Activity log error: {e}")

@bp.route('/<int:receipt_id>', methods=['DELETE'])
def delete_receipt(receipt_id):
    """Delete receipt"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    try:
        # Get receipt details for logging
        cursor.execute('SELECT receipt_number FROM receipts WHERE id = %s', (receipt_id,))
        receipt = cursor.fetchone()
        
        if not receipt:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Receipt not found'}), 404
        
        cursor.execute('DELETE FROM receipts WHERE id = %s', (receipt_id,))
        
        # Log activity
        log_activity(
            session['user_id'], 
            'delete', 
            'receipt', 
            f'Deleted receipt: {receipt["receipt_number"]}'
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Receipt deleted successfully'})
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/range', methods=['GET'])
def get_receipts_by_date_range():
    """Get receipts within a date range"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'success': False, 'error': 'Start date and end date are required'}), 400
    
    conn, cursor = get_db()
    
    cursor.execute('''
        SELECT 
            r.*,
            t.first_name,
            t.last_name,
            t.passport_no
        FROM receipts r
        LEFT JOIN travelers t ON r.traveler_id = t.id
        WHERE r.receipt_date BETWEEN %s AND %s
        ORDER BY r.receipt_date DESC
    ''', (start_date, end_date))
    
    receipts = cursor.fetchall()
    
    # Calculate totals
    cursor.execute('''
        SELECT 
            COUNT(*) as count,
            COALESCE(SUM(amount), 0) as total
        FROM receipts
        WHERE receipt_date BETWEEN %s AND %s
    ''', (start_date, end_date))
    
    totals = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'success': True,
        'receipts': [dict(r) for r in receipts],
        'summary': {
            'count': totals['count'] if totals else 0,
            'total': float(totals['total']) if totals and totals['total'] else 0,
            'start_date': start_date,
            'end_date': end_date
        }
    })
