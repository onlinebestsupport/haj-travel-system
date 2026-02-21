from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime

bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@bp.route('', methods=['GET'])
def get_payments():
    """Get all payments"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT p.*, 
               t.first_name, t.last_name, t.passport_no,
               b.batch_name
        FROM payments p
        JOIN travelers t ON p.traveler_id = t.id
        JOIN batches b ON p.batch_id = b.id
        ORDER BY p.payment_date DESC
    ''')
    payments = cursor.fetchall()
    db.close()
    
    return jsonify({'success': True, 'payments': [dict(p) for p in payments]})

@bp.route('/traveler/<int:traveler_id>', methods=['GET'])
def get_traveler_payments(traveler_id):
    """Get payments for a specific traveler"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT p.*, b.batch_name
        FROM payments p
        JOIN batches b ON p.batch_id = b.id
        WHERE p.traveler_id = ?
        ORDER BY p.payment_date DESC
    ''', (traveler_id,))
    payments = cursor.fetchall()
    
    # Calculate totals
    cursor.execute('''
        SELECT 
            COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as paid,
            COALESCE(SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END), 0) as pending
        FROM payments WHERE traveler_id = ?
    ''', (traveler_id,))
    totals = cursor.fetchone()
    
    db.close()
    
    return jsonify({
        'success': True,
        'payments': [dict(p) for p in payments],
        'totals': dict(totals)
    })

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
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO payments (
                traveler_id, batch_id, amount, payment_date,
                payment_method, transaction_id, status, remarks,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['traveler_id'],
            data['batch_id'],
            data['amount'],
            data['payment_date'],
            data.get('payment_method'),
            data.get('transaction_id'),
            data.get('status', 'completed'),
            data.get('remarks'),
            datetime.now().isoformat()
        ))
        payment_id = cursor.lastrowid
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