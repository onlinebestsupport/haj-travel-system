from flask import Blueprint, request, jsonify, session, current_app, send_file
from app.database import get_db, release_db
from datetime import datetime, timedelta
import json
import traceback
import io
import csv

bp = Blueprint('payments', __name__, url_prefix='/api/payments')

# ============================================================
# ROUTES
# ============================================================

@bp.route('', methods=['GET'])
def get_payments():
    """Get all payments with enhanced details"""
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()

        cursor.execute('''
            SELECT
                p.id, p.traveler_id, p.batch_id, p.amount, 
                p.payment_date, p.payment_method, p.status, 
                p.reference, p.notes, p.created_at, p.updated_at,
                p.installment, p.due_date,
                t.first_name, t.last_name, t.passport_no,
                b.batch_name
            FROM payments p
            LEFT JOIN travelers t ON p.traveler_id = t.id
            LEFT JOIN batches b ON p.batch_id = b.id
            ORDER BY p.payment_date DESC
        ''')

        payments = cursor.fetchall()
        
        result = []
        for p in payments:
            payment_dict = dict(p)
            # Format dates
            if payment_dict.get('payment_date'):
                payment_dict['payment_date'] = payment_dict['payment_date'].isoformat() if hasattr(payment_dict['payment_date'], 'isoformat') else str(payment_dict['payment_date'])
            if payment_dict.get('due_date'):
                payment_dict['due_date'] = payment_dict['due_date'].isoformat() if hasattr(payment_dict['due_date'], 'isoformat') else str(payment_dict['due_date'])
            if payment_dict.get('created_at'):
                payment_dict['created_at'] = payment_dict['created_at'].isoformat() if hasattr(payment_dict['created_at'], 'isoformat') else str(payment_dict['created_at'])
            if payment_dict.get('updated_at'):
                payment_dict['updated_at'] = payment_dict['updated_at'].isoformat() if hasattr(payment_dict['updated_at'], 'isoformat') else str(payment_dict['updated_at'])
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
        if conn:
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

        result = dict(payment)
        # Format dates
        if result.get('payment_date'):
            result['payment_date'] = result['payment_date'].isoformat() if hasattr(result['payment_date'], 'isoformat') else str(result['payment_date'])
        if result.get('due_date'):
            result['due_date'] = result['due_date'].isoformat() if hasattr(result['due_date'], 'isoformat') else str(result['due_date'])
        if result.get('created_at'):
            result['created_at'] = result['created_at'].isoformat() if hasattr(result['created_at'], 'isoformat') else str(result['created_at'])

        return jsonify({'success': True, 'payment': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
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
        result = []
        for p in payments:
            payment_dict = dict(p)
            if payment_dict.get('payment_date'):
                payment_dict['payment_date'] = payment_dict['payment_date'].isoformat() if hasattr(payment_dict['payment_date'], 'isoformat') else str(payment_dict['payment_date'])
            if payment_dict.get('due_date'):
                payment_dict['due_date'] = payment_dict['due_date'].isoformat() if hasattr(payment_dict['due_date'], 'isoformat') else str(payment_dict['due_date'])
            result.append(payment_dict)

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
        totals_dict = dict(totals) if totals else {}
        if totals_dict.get('last_payment_date'):
            totals_dict['last_payment_date'] = totals_dict['last_payment_date'].isoformat() if hasattr(totals_dict['last_payment_date'], 'isoformat') else str(totals_dict['last_payment_date'])

        return jsonify({
            'success': True,
            'payments': result,
            'totals': totals_dict
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
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
        result = []
        for p in payments:
            payment_dict = dict(p)
            if payment_dict.get('payment_date'):
                payment_dict['payment_date'] = payment_dict['payment_date'].isoformat() if hasattr(payment_dict['payment_date'], 'isoformat') else str(payment_dict['payment_date'])
            result.append(payment_dict)

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
            'payments': result,
            'summary': dict(summary) if summary else {}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('', methods=['POST'])
def create_payment():
    """Create new payment"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.json

    # Validate required fields
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

        # Check if batch exists
        cursor.execute('SELECT id FROM batches WHERE id = %s', (data['batch_id'],))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Batch not found'}), 400

        # Insert payment
        cursor.execute('''
            INSERT INTO payments (
                traveler_id, batch_id, amount, payment_date, 
                payment_method, status, reference, notes, 
                installment, due_date, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            data['traveler_id'],
            data['batch_id'],
            amount,
            data['payment_date'],
            data.get('payment_method'),
            data.get('status', 'completed'),
            data.get('transaction_id') or data.get('reference'),
            data.get('remarks') or data.get('notes'),
            data.get('installment'),
            data.get('due_date'),
            datetime.now()
        ))

        result = cursor.fetchone()
        payment_id = result['id'] if result else None

        conn.commit()

        return jsonify({
            'success': True,
            'payment_id': payment_id,
            'message': 'Payment recorded successfully',
            'amount': amount
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

        # Build update query dynamically
        update_fields = []
        params = []

        field_mapping = {
            'amount': data.get('amount'),
            'payment_date': data.get('payment_date'),
            'payment_method': data.get('payment_method'),
            'status': data.get('status'),
            'reference': data.get('reference') or data.get('transaction_id'),
            'notes': data.get('notes') or data.get('remarks'),
            'installment': data.get('installment'),
            'due_date': data.get('due_date')
        }

        for field, value in field_mapping.items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                params.append(value)

        if not update_fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400

        update_fields.append("updated_at = %s")
        params.append(datetime.now())
        params.append(payment_id)

        query = f"UPDATE payments SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, params)

        conn.commit()

        return jsonify({'success': True, 'message': 'Payment updated successfully'})

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:payment_id>', methods=['DELETE'])
def delete_payment(payment_id):
    """Delete a payment"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()

        cursor.execute('SELECT id FROM payments WHERE id = %s', (payment_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Payment not found'}), 404

        cursor.execute('DELETE FROM payments WHERE id = %s', (payment_id,))
        conn.commit()

        return jsonify({'success': True, 'message': 'Payment deleted successfully'})

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:payment_id>/reverse', methods=['POST'])
def reverse_payment(payment_id):
    """Reverse a payment"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.json

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()

        # Check if payment exists
        cursor.execute('SELECT id, amount, status FROM payments WHERE id = %s', (payment_id,))
        payment = cursor.fetchone()
        if not payment:
            return jsonify({'success': False, 'error': 'Payment not found'}), 404

        if payment['status'] == 'reversed':
            return jsonify({'success': False, 'error': 'Payment already reversed'}), 400

        # Update payment status
        cursor.execute('''
            UPDATE payments 
            SET status = 'reversed', 
                notes = CONCAT(COALESCE(notes, ''), ' | Reversed: ', %s, ' | Reason: ', %s),
                updated_at = %s
            WHERE id = %s
        ''', (
            datetime.now().isoformat(),
            data.get('reason', 'Not specified'),
            datetime.now(),
            payment_id
        ))

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Payment reversed successfully',
            'payment_id': payment_id
        })

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
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

        # Status counts
        cursor.execute('''
            SELECT 
                status, 
                COUNT(*) as count,
                COALESCE(SUM(amount), 0) as total_amount
            FROM payments
            GROUP BY status
        ''')
        status_counts = cursor.fetchall()

        return jsonify({
            'success': True,
            'stats': {
                'total_transactions': overall['total_transactions'] if overall else 0,
                'total_collected': float(overall['total_collected']) if overall and overall['total_collected'] else 0,
                'pending_amount': float(overall['total_pending']) if overall and overall['total_pending'] else 0,
                'completed_count': overall['completed_count'] if overall else 0,
                'pending_count': overall['pending_count'] if overall else 0,
                'reversed_count': overall['reversed_count'] if overall else 0
            },
            'payment_methods': [dict(m) for m in method_breakdown],
            'monthly_summary': [dict(m) for m in monthly],
            'status_counts': [dict(s) for s in status_counts]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/export', methods=['GET'])
def export_payments():
    """Export payments to CSV"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()

        cursor.execute('''
            SELECT
                p.id, p.amount, p.payment_date, p.payment_method, p.status, 
                p.reference, p.notes, p.installment, p.due_date,
                t.first_name, t.last_name, t.passport_no,
                b.batch_name
            FROM payments p
            LEFT JOIN travelers t ON p.traveler_id = t.id
            LEFT JOIN batches b ON p.batch_id = b.id
            ORDER BY p.payment_date DESC
        ''')

        payments = cursor.fetchall()

        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow([
            'ID', 'Traveler Name', 'Passport Number', 'Batch', 
            'Amount', 'Payment Date', 'Payment Method', 'Status',
            'Transaction ID', 'Installment', 'Due Date', 'Remarks'
        ])

        # Write data
        for p in payments:
            writer.writerow([
                p['id'],
                f"{p['first_name'] or ''} {p['last_name'] or ''}".strip(),
                p['passport_no'] or '',
                p['batch_name'] or '',
                p['amount'] or 0,
                p['payment_date'].isoformat() if p['payment_date'] else '',
                p['payment_method'] or '',
                p['status'] or '',
                p['reference'] or '',
                p['installment'] or '',
                p['due_date'].isoformat() if p['due_date'] else '',
                p['notes'] or ''
            ])

        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'payments_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

print("✅ payments.py loaded successfully!")
