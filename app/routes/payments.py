from flask import Blueprint, request, jsonify
from app.database import get_db
import psycopg2
import psycopg2.extras
from datetime import datetime

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/', methods=['GET'])
def get_all_payments():
    """Get all payments"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("""
            SELECT 
                p.id,
                t.first_name || ' ' || t.last_name as traveler_name,
                p.installment,
                p.amount,
                TO_CHAR(p.due_date, 'YYYY-MM-DD') as due_date,
                TO_CHAR(p.payment_date, 'YYYY-MM-DD') as payment_date,
                p.status,
                p.payment_method,
                p.created_at
            FROM payments p
            JOIN travelers t ON p.traveler_id = t.id
            ORDER BY p.created_at DESC
        """)
        
        payments = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'payments': payments})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@payments_bp.route('/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    """Get single payment"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("""
            SELECT p.*, t.first_name, t.last_name, t.passport_no
            FROM payments p
            JOIN travelers t ON p.traveler_id = t.id
            WHERE p.id = %s
        """, (payment_id,))
        
        payment = cur.fetchone()
        cur.close()
        conn.close()
        
        if payment:
            return jsonify({'success': True, 'payment': payment})
        return jsonify({'success': False, 'error': 'Payment not found'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@payments_bp.route('/traveler/<int:traveler_id>', methods=['GET'])
def get_traveler_payments(traveler_id):
    """Get payments for a specific traveler"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("""
            SELECT 
                id, installment, amount,
                TO_CHAR(due_date, 'YYYY-MM-DD') as due_date,
                TO_CHAR(payment_date, 'YYYY-MM-DD') as payment_date,
                status, payment_method
            FROM payments
            WHERE traveler_id = %s
            ORDER BY due_date
        """, (traveler_id,))
        
        payments = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'payments': payments})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@payments_bp.route('/', methods=['POST'])
def create_payment():
    """Create a new payment"""
    try:
        data = request.json
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO payments (
                traveler_id, installment, amount, due_date, 
                payment_date, payment_method, status, remarks
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get('traveler_id'),
            data.get('installment'),
            data.get('amount'),
            data.get('due_date'),
            data.get('payment_date'),
            data.get('payment_method'),
            data.get('status', 'Pending'),
            data.get('remarks')
        ))
        
        payment_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'payment_id': payment_id}), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@payments_bp.route('/stats', methods=['GET'])
def get_payment_stats():
    """Get payment statistics"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor()
        
        # Total collected
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'Paid'")
        total_collected = cur.fetchone()[0]
        
        # Pending amount
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'Pending'")
        pending_amount = cur.fetchone()[0]
        
        # Count by status
        cur.execute("SELECT status, COUNT(*) FROM payments GROUP BY status")
        status_counts = {}
        for row in cur.fetchall():
            status_counts[row[0]] = row[1]
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_collected': float(total_collected),
                'pending_amount': float(pending_amount),
                'status_counts': status_counts
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
