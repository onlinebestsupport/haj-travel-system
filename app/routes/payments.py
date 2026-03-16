from flask import Blueprint, request, jsonify, session
from app.database import get_db, release_db
from datetime import datetime, timedelta
import json
import traceback

bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@bp.route('', methods=['GET'])
def get_payments():
    """Get all payments with enhanced details"""
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()

        # Explicitly list all columns from payments table
        cursor.execute('''
            SELECT
                p.id, p.traveler_id, p.batch_id, p.amount, 
                p.payment_date, p.payment_method, p.status, 
                p.reference, p.notes, p.created_at, p.updated_at,
                t.first_name, t.last_name, t.passport_no,
                b.batch_name
            FROM payments p
            LEFT JOIN travelers t ON p.traveler_id = t.id
            LEFT JOIN batches b ON p.batch_id = b.id
            ORDER BY p.payment_date DESC
        ''')

        payments = cursor.fetchall()
        
        # Convert to list of dicts
        result = []
        for p in payments:
            payment_dict = dict(p)
            result.append(payment_dict)

        return jsonify({
            'success': True,
            'payments': result
        })
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"❌ Payments API error: {str(e)}")
        print(f"❌ Traceback: {error_details}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)

@bp.route('/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    """Get single payment with complete details"""
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()

        cursor.execute('''
            SELECT
                p.*,
                t.first_name, t.last_name, t.passport_no, t.mobile, t.email,
                b.batch_name
            FROM payments p
            LEFT JOIN travelers t ON p.traveler_id = t.id
            LEFT JOIN batches b ON p.batch_id = b.id
            WHERE p.id = %s
        ''', (payment_id,))

        payment = cursor.fetchone()

        if not payment:
            return jsonify({'success': False, 'error': 'Payment not found'}), 404

        # Get receipt if exists
        cursor.execute('SELECT * FROM receipts WHERE payment_id = %s', (payment_id,))
        receipt = cursor.fetchone()

        result = dict(payment)
        if receipt:
            result['receipt'] = dict(receipt)

        return jsonify({'success': True, 'payment': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)

@bp.route('/traveler/<int:traveler_id>', methods=['GET'])
def get_traveler_payments(traveler_id):
    """Get payments for a specific traveler"""
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()

        cursor.execute('''
            SELECT
                p.*,
                b.batch_name
            FROM payments p
            LEFT JOIN batches b ON p.batch_id = b.id
            WHERE p.traveler_id = %s
            ORDER BY p.payment_date DESC
        ''', (traveler_id,))

        payments = cursor.fetchall()

        # Calculate totals
        cursor.execute('''
            SELECT
                COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as total_paid,
                COALESCE(SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END), 0) as total_pending,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as paid_count,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
                MAX(CASE WHEN status = 'completed' THEN payment_date END) as last_payment_date
            FROM payments
            WHERE traveler_id = %s
        ''', (traveler_id,))

        totals = cursor.fetchone()

        return jsonify({
            'success': True,
            'payments': [dict(p) for p in payments],
            'totals': dict(totals) if totals else {}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)

@bp.route('/batch/<int:batch_id>', methods=['GET'])
def get_batch_payments(batch_id):
    """Get all payments for a specific batch"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()

        cursor.execute('''
            SELECT
                p.*,
                t.first_name, t.last_name, t.passport_no
            FROM payments p
            LEFT JOIN travelers t ON p.traveler_id = t.id
            WHERE p.batch_id = %s
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
            WHERE batch_id = %s
        ''', (batch_id,))

        summary = cursor.fetchone()

        return jsonify({
            'success': True,
            'payments': [dict(p) for p in payments],
            'summary': dict(summary) if summary else {}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)

@bp.route('', methods=['POST'])
def create_payment():
    """Create new payment"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.json

    # Validate required fields based on actual schema
    required = ['traveler_id', 'batch_id', 'amount', 'payment_date']
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

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()

        # Check if traveler exists
        cursor.execute('SELECT id, first_name, last_name FROM travelers WHERE id = %s', (data['traveler_id'],))
        traveler = cursor.fetchone()
        if not traveler:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 400

        # Insert payment - based on actual schema: id, traveler_id, batch_id, amount, payment_date, status, created_at
        cursor.execute('''
            INSERT INTO payments (
                traveler_id, batch_id, amount, payment_date, status, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            data['traveler_id'],
            data['batch_id'],
            amount,
            data['payment_date'],
            data.get('status', 'completed'),
            datetime.now()
        ))

        result = cursor.fetchone()
        payment_id = result['id'] if result else None

        conn.commit()

        return jsonify({
            'success': True,
            'payment_id': payment_id,
            'message': 'Payment recorded successfully'
        })

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:payment_id>', methods=['PUT'])
def update_payment(payment_id):
    """Update payment details"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.json

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()

        # Check if payment exists
        cursor.execute('SELECT id FROM payments WHERE id = %s', (payment_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Payment not found'}), 404

        # Update payment
        cursor.execute('''
            UPDATE payments SET
                amount = COALESCE(%s, amount),
                payment_date = COALESCE(%s, payment_date),
                payment_method = COALESCE(%s, payment_method),
                reference = COALESCE(%s, reference),
                notes = COALESCE(%s, notes),
                status = COALESCE(%s, status),
                updated_at = %s
            WHERE id = %s
        ''', (
            data.get('amount'),
            data.get('payment_date'),
            data.get('payment_method'),
            data.get('reference'),
            data.get('notes'),
            data.get('status'),
            datetime.now(),
            payment_id
        ))

        conn.commit()

        return jsonify({'success': True, 'message': 'Payment updated successfully'})

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        release_db(conn, cursor)

@bp.route('/stats', methods=['GET'])
def get_payment_stats():
    """Get payment statistics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()

        # Overall statistics
        cursor.execute('''
            SELECT
                COUNT(*) as total_transactions,
                COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as total_collected,
                COALESCE(SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END), 0) as total_pending,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count
            FROM payments
        ''')
        overall = cursor.fetchone()

        # Payment method breakdown
        cursor.execute('''
            SELECT
                payment_method,
                COUNT(*) as count,
                COALESCE(SUM(amount), 0) as total
            FROM payments
            WHERE status = 'completed'
            GROUP BY payment_method
            ORDER BY total DESC
        ''')
        method_breakdown = cursor.fetchall()

        # Monthly summary (last 6 months)
        cursor.execute('''
            SELECT
                TO_CHAR(payment_date, 'YYYY-MM') as month,
                COUNT(*) as transactions,
                COALESCE(SUM(amount), 0) as total
            FROM payments
            WHERE status = 'completed'
              AND payment_date >= CURRENT_DATE - INTERVAL '6 months'
            GROUP BY TO_CHAR(payment_date, 'YYYY-MM')
            ORDER BY month DESC
        ''')
        monthly = cursor.fetchall()

        return jsonify({
            'success': True,
            'stats': {
                'total_transactions': overall['total_transactions'] if overall else 0,
                'total_collected': float(overall['total_collected']) if overall and overall['total_collected'] else 0,
                'pending_amount': float(overall['total_pending']) if overall and overall['total_pending'] else 0,
                'completed_count': overall['completed_count'] if overall else 0,
                'pending_count': overall['pending_count'] if overall else 0
            },
            'payment_methods': [dict(m) for m in method_breakdown],
            'monthly_summary': [dict(m) for m in monthly]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)

@bp.route('/<int:payment_id>/receipt', methods=['GET'])
def get_payment_receipt(payment_id):
    """Get receipt for a payment"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()

        cursor.execute('''
            SELECT r.*, p.*, t.first_name, t.last_name, t.passport_no, b.batch_name
            FROM receipts r
            JOIN payments p ON r.payment_id = p.id
            JOIN travelers t ON p.traveler_id = t.id
            JOIN batches b ON p.batch_id = b.id
            WHERE r.payment_id = %s
        ''', (payment_id,))

        receipt = cursor.fetchone()

        if receipt:
            return jsonify({'success': True, 'receipt': dict(receipt)})
        else:
            return jsonify({'success': False, 'error': 'Receipt not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)