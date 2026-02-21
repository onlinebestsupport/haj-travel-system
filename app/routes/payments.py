from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime

bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@bp.route('', methods=['GET'])
def get_payments():
    db = get_db()
    payments = db.execute('''
        SELECT p.*, t.first_name, t.last_name, b.batch_name
        FROM payments p
        JOIN travelers t ON p.traveler_id = t.id
        JOIN batches b ON p.batch_id = b.id
        ORDER BY p.created_at DESC
    ''').fetchall()
    
    return jsonify({
        'success': True,
        'payments': [dict(p) for p in payments]
    })

@bp.route('', methods=['POST'])
def create_payment():
    data = request.json
    
    db = get_db()
    cursor = db.execute('''
        INSERT INTO payments (
            traveler_id, batch_id, amount, payment_date,
            payment_method, transaction_id, status, remarks,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['traveler_id'],
        data['batch_id'],
        data['amount'],
        data.get('payment_date', datetime.now().strftime('%Y-%m-%d')),
        data.get('payment_method'),
        data.get('transaction_id'),
        data.get('status', 'completed'),
        data.get('remarks'),
        datetime.now().isoformat()
    ))
    
    db.commit()
    
    return jsonify({
        'success': True,
        'payment_id': cursor.lastrowid,
        'message': 'Payment recorded successfully'
    })
