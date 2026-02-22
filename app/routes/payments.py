from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime, timedelta
import json

bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@bp.route('', methods=['GET'])
def get_payments():
    """Get all payments with enhanced details"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            p.*, 
            t.first_name, t.last_name, t.passport_no,
            b.batch_name,
            CASE 
                WHEN p.status = 'pending' AND date(p.due_date) < date('now') THEN 'overdue'
                ELSE p.status
            END as current_status
        FROM payments p
        JOIN travelers t ON p.traveler_id = t.id
        JOIN batches b ON p.batch_id = b.id
        ORDER BY 
            CASE 
                WHEN p.status = 'pending' AND date(p.due_date) < date('now') THEN 1
                WHEN p.status = 'pending' THEN 2
                ELSE 3
            END,
            p.payment_date DESC
    ''')
    
    payments = cursor.fetchall()
    db.close()
    
    return jsonify({
        'success': True, 
        'payments': [dict(p) for p in payments]
    })

@bp.route('/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    """Get single payment with complete details"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            p.*, 
            t.first_name, t.last_name, t.passport_no, t.mobile, t.email,
            b.batch_name, b.price as batch_price,
            CASE 
                WHEN p.status = 'pending' AND date(p.due_date) < date('now') THEN 'overdue'
                ELSE p.status
            END as current_status
        FROM payments p
        JOIN travelers t ON p.traveler_id = t.id
        JOIN batches b ON p.batch_id = b.id
        WHERE p.id = ?
    ''', (payment_id,))
    
    payment = cursor.fetchone()
    
    if not payment:
        db.close()
        return jsonify({'success': False, 'error': 'Payment not found'}), 404
    
    # Get receipt if exists
    cursor.execute('SELECT * FROM receipts WHERE payment_id = ?', (payment_id,))
    receipt = cursor.fetchone()
    
    db.close()
    
    result = dict(payment)
    if receipt:
        result['receipt'] = dict(receipt)
    
    return jsonify({'success': True, 'payment': result})

@bp.route('/traveler/<int:traveler_id>', methods=['GET'])
def get_traveler_payments(traveler_id):
    """Get payments for a specific traveler with enhanced details"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            p.*, 
            b.batch_name,
            CASE 
                WHEN p.status = 'pending' AND date(p.due_date) < date('now') THEN 'overdue'
                ELSE p.status
            END as current_status
        FROM payments p
        JOIN batches b ON p.batch_id = b.id
        WHERE p.traveler_id = ?
        ORDER BY p.payment_date DESC
    ''', (traveler_id,))
    
    payments = cursor.fetchall()
    
    # Calculate detailed totals
    cursor.execute('''
        SELECT 
            COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as total_paid,
            COALESCE(SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END), 0) as total_pending,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as paid_count,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
            MAX(CASE WHEN status = 'completed' THEN payment_date END) as last_payment_date
        FROM payments 
        WHERE traveler_id = ?
    ''', (traveler_id,))
    
    totals = cursor.fetchone()
    
    # Get overdue payments
    cursor.execute('''
        SELECT COUNT(*) as overdue_count,
               SUM(amount) as overdue_amount
        FROM payments 
        WHERE traveler_id = ? 
          AND status = 'pending' 
          AND date(due_date) < date('now')
    ''', (traveler_id,))
    
    overdue = cursor.fetchone()
    
    db.close()
    
    return jsonify({
        'success': True,
        'payments': [dict(p) for p in payments],
        'totals': dict(totals) if totals else {},
        'overdue': dict(overdue) if overdue else {'overdue_count': 0, 'overdue_amount': 0}
    })

@bp.route('/batch/<int:batch_id>', methods=['GET'])
def get_batch_payments(batch_id):
    """Get all payments for a specific batch"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            p.*, 
            t.first_name, t.last_name, t.passport_no,
            CASE 
                WHEN p.status = 'pending' AND date(p.due_date) < date('now') THEN 'overdue'
                ELSE p.status
            END as current_status
        FROM payments p
        JOIN travelers t ON p.traveler_id = t.id
        WHERE p.batch_id = ?
        ORDER BY p.payment_date DESC
    ''', (batch_id,))
    
    payments = cursor.fetchall()
    
    # Batch payment summary
    cursor.execute('''
        SELECT 
            COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as total_collected,
            COALESCE(SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END), 0) as total_pending,
            COUNT(DISTINCT traveler_id) as paying_travelers
        FROM payments 
        WHERE batch_id = ?
    ''', (batch_id,))
    
    summary = cursor.fetchone()
    
    db.close()
    
    return jsonify({
        'success': True,
        'payments': [dict(p) for p in payments],
        'summary': dict(summary) if summary else {}
    })

@bp.route('', methods=['POST'])
def create_payment():
    """Create new payment with enhanced features"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    # Validate required fields
    required = ['traveler_id', 'batch_id', 'amount', 'payment_date', 'payment_method']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    # Validate amount
    if data['amount'] <= 0:
        return jsonify({'success': False, 'error': 'Amount must be greater than 0'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if traveler exists and belongs to batch
        cursor.execute('''
            SELECT id, first_name, last_name FROM travelers 
            WHERE id = ? AND batch_id = ?
        ''', (data['traveler_id'], data['batch_id']))
        
        traveler = cursor.fetchone()
        if not traveler:
            db.close()
            return jsonify({'success': False, 'error': 'Traveler not found or does not belong to this batch'}), 400
        
        # Calculate due date if not provided (default 30 days)
        due_date = data.get('due_date')
        if not due_date:
            due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Insert payment
        cursor.execute('''
            INSERT INTO payments (
                traveler_id, batch_id, amount, payment_date, due_date,
                payment_method, transaction_id, installment, status, remarks,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['traveler_id'],
            data['batch_id'],
            data['amount'],
            data['payment_date'],
            due_date,
            data['payment_method'],
            data.get('transaction_id'),
            data.get('installment'),
            data.get('status', 'completed'),
            data.get('remarks'),
            datetime.now().isoformat()
        ))
        
        payment_id = cursor.lastrowid
        
        # Create receipt automatically for completed payments
        if data.get('status', 'completed') == 'completed':
            receipt_number = f"REC-{datetime.now().strftime('%Y%m%d')}-{payment_id}"
            
            cursor.execute('''
                INSERT INTO receipts (
                    receipt_number, traveler_id, payment_id, receipt_date,
                    amount, payment_method, transaction_id, receipt_type,
                    installment_info, remarks, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                receipt_number,
                data['traveler_id'],
                payment_id,
                data['payment_date'],
                data['amount'],
                data['payment_method'],
                data.get('transaction_id'),
                data.get('installment', 'payment'),
                data.get('installment_info'),
                f"Payment receipt for {data.get('installment', 'Payment')}",
                datetime.now().isoformat()
            ))
        
        # Log activity
        log_activity(
            session['user_id'], 
            'create', 
            'payment', 
            f'Recorded payment of ₹{data["amount"]} for traveler {traveler["first_name"]} {traveler["last_name"]}'
        )
        
        db.commit()
        db.close()
        
        return jsonify({
            'success': True,
            'payment_id': payment_id,
            'message': 'Payment recorded successfully'
        })
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/<int:payment_id>', methods=['PUT'])
def update_payment(payment_id):
    """Update payment details"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if payment exists
        cursor.execute('SELECT id, traveler_id, amount FROM payments WHERE id = ?', (payment_id,))
        payment = cursor.fetchone()
        
        if not payment:
            db.close()
            return jsonify({'success': False, 'error': 'Payment not found'}), 404
        
        # Update payment
        cursor.execute('''
            UPDATE payments SET
                amount = ?,
                payment_date = ?,
                due_date = ?,
                payment_method = ?,
                transaction_id = ?,
                installment = ?,
                status = ?,
                remarks = ?,
                updated_at = ?
            WHERE id = ?
        ''', (
            data.get('amount', payment['amount']),
            data.get('payment_date'),
            data.get('due_date'),
            data.get('payment_method'),
            data.get('transaction_id'),
            data.get('installment'),
            data.get('status'),
            data.get('remarks'),
            datetime.now().isoformat(),
            payment_id
        ))
        
        # Log activity
        log_activity(
            session['user_id'], 
            'update', 
            'payment', 
            f'Updated payment ID: {payment_id}'
        )
        
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'message': 'Payment updated successfully'})
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/<int:payment_id>/reverse', methods=['POST'])
def reverse_payment(payment_id):
    """Reverse/refund a payment"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if payment exists and is completed
        cursor.execute('''
            SELECT p.*, t.first_name, t.last_name 
            FROM payments p
            JOIN travelers t ON p.traveler_id = t.id
            WHERE p.id = ?
        ''', (payment_id,))
        
        payment = cursor.fetchone()
        
        if not payment:
            db.close()
            return jsonify({'success': False, 'error': 'Payment not found'}), 404
        
        if payment['status'] != 'completed':
            db.close()
            return jsonify({'success': False, 'error': 'Only completed payments can be reversed'}), 400
        
        # Update payment status to reversed
        cursor.execute('''
            UPDATE payments SET
                status = 'reversed',
                remarks = ?,
                updated_at = ?
            WHERE id = ?
        ''', (
            f"Reversed: {data.get('reason', 'No reason provided')} - {data.get('remarks', '')}",
            datetime.now().isoformat(),
            payment_id
        ))
        
        # Create reversal record (optional - could create negative payment)
        cursor.execute('''
            INSERT INTO payments (
                traveler_id, batch_id, amount, payment_date,
                payment_method, transaction_id, installment, status, remarks,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            payment['traveler_id'],
            payment['batch_id'],
            -payment['amount'],  # Negative amount for reversal
            datetime.now().strftime('%Y-%m-%d'),
            payment['payment_method'],
            f"REV-{payment['transaction_id']}" if payment['transaction_id'] else None,
            f"Reversal of {payment['installment']}" if payment['installment'] else 'Reversal',
            'reversed',
            f"Reversal of payment {payment_id}: {data.get('reason', '')} - {data.get('remarks', '')}",
            datetime.now().isoformat()
        ))
        
        # Log activity
        log_activity(
            session['user_id'], 
            'reverse', 
            'payment', 
            f'Reversed payment ID: {payment_id} of ₹{payment["amount"]}'
        )
        
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'message': 'Payment reversed successfully'})
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/stats', methods=['GET'])
def get_payment_stats():
    """Get payment statistics"""
    db = get_db()
    cursor = db.cursor()
    
    # Overall statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total_transactions,
            COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as total_collected,
            COALESCE(SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END), 0) as total_pending,
            COALESCE(SUM(CASE WHEN status = 'reversed' THEN amount ELSE 0 END), 0) as total_reversed,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
            COUNT(CASE WHEN status = 'reversed' THEN 1 END) as reversed_count
        FROM payments
    ''')
    
    overall = cursor.fetchone()
    
    # Payment method breakdown
    cursor.execute('''
        SELECT 
            payment_method,
            COUNT(*) as count,
            SUM(amount) as total
        FROM payments
        WHERE status = 'completed'
        GROUP BY payment_method
        ORDER BY total DESC
    ''')
    
    method_breakdown = cursor.fetchall()
    
    # Monthly summary (last 6 months)
    cursor.execute('''
        SELECT 
            strftime('%Y-%m', payment_date) as month,
            COUNT(*) as transactions,
            SUM(amount) as total
        FROM payments
        WHERE status = 'completed'
          AND date(payment_date) >= date('now', '-6 months')
        GROUP BY strftime('%Y-%m', payment_date)
        ORDER BY month DESC
    ''')
    
    monthly = cursor.fetchall()
    
    # Overdue payments
    cursor.execute('''
        SELECT 
            COUNT(*) as overdue_count,
            SUM(amount) as overdue_amount
        FROM payments
        WHERE status = 'pending'
          AND date(due_date) < date('now')
    ''')
    
    overdue = cursor.fetchone()
    
    db.close()
    
    # Format status counts
    status_counts = {}
    if overall:
        status_counts['completed'] = overall['completed_count']
        status_counts['pending'] = overall['pending_count']
        status_counts['reversed'] = overall['reversed_count']
    
    return jsonify({
        'success': True,
        'stats': {
            'total_transactions': overall['total_transactions'] if overall else 0,
            'total_collected': overall['total_collected'] if overall else 0,
            'pending_amount': overall['total_pending'] if overall else 0,
            'total_reversed': overall['total_reversed'] if overall else 0,
            'status_counts': status_counts,
            'overdue': dict(overdue) if overdue else {'overdue_count': 0, 'overdue_amount': 0}
        },
        'payment_methods': [dict(m) for m in method_breakdown],
        'monthly_summary': [dict(m) for m in monthly]
    })

@bp.route('/<int:payment_id>/receipt', methods=['GET'])
def get_payment_receipt(payment_id):
    """Get receipt for a payment"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT r.*, p.*, t.first_name, t.last_name, t.passport_no, b.batch_name
        FROM receipts r
        JOIN payments p ON r.payment_id = p.id
        JOIN travelers t ON p.traveler_id = t.id
        JOIN batches b ON p.batch_id = b.id
        WHERE r.payment_id = ?
    ''', (payment_id,))
    
    receipt = cursor.fetchone()
    db.close()
    
    if receipt:
        return jsonify({'success': True, 'receipt': dict(receipt)})
    else:
        return jsonify({'success': False, 'error': 'Receipt not found'}), 404

# Helper function to log activity
def log_activity(user_id, action, module, description):
    """Log user activity"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO activity_log (user_id, action, module, description, ip_address) VALUES (?, ?, ?, ?, ?)',
            (user_id, action, module, description, request.remote_addr)
        )
        db.commit()
        db.close()
    except:
        pass  # Fail silently
