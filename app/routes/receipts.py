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
    
    db = get_db()
    cursor = db.cursor()
    
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
    db.close()
    
    return jsonify({
        'success': True,
        'receipts': [dict(r) for r in receipts]
    })

@bp.route('/<int:receipt_id>', methods=['GET'])
def get_receipt(receipt_id):
    """Get single receipt"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
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
        WHERE r.id = ?
    ''', (receipt_id,))
    
    receipt = cursor.fetchone()
    db.close()
    
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
    
    # Generate receipt number
    receipt_number = f"REC-{datetime.now().strftime('%Y%m%d')}-{data['traveler_id']}-{int(datetime.now().timestamp())}"
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO receipts (
                receipt_number, traveler_id, payment_id, invoice_id,
                receipt_date, amount, payment_method, transaction_id,
                receipt_type, installment_info, remarks, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            receipt_number,
            data['traveler_id'],
            data['payment_id'],
            data.get('invoice_id'),
            data['receipt_date'],
            data['amount'],
            data.get('payment_method'),
            data.get('transaction_id'),
            data.get('receipt_type', 'payment'),
            data.get('installment_info'),
            data.get('remarks'),
            datetime.now().isoformat()
        ))
        
        receipt_id = cursor.lastrowid
        db.commit()
        db.close()
        
        return jsonify({
            'success': True,
            'receipt_id': receipt_id,
            'receipt_number': receipt_number,
            'message': 'Receipt created successfully'
        })
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/payment/<int:payment_id>', methods=['GET'])
def get_payment_receipts(payment_id):
    """Get receipts for a specific payment"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT * FROM receipts 
        WHERE payment_id = ?
        ORDER BY created_at DESC
    ''', (payment_id,))
    
    receipts = cursor.fetchall()
    db.close()
    
    return jsonify({
        'success': True,
        'receipts': [dict(r) for r in receipts]
    })

@bp.route('/stats', methods=['GET'])
def get_receipt_stats():
    """Get receipt statistics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_receipts,
            SUM(amount) as total_amount,
            COUNT(DISTINCT traveler_id) as unique_travelers,
            COUNT(DISTINCT payment_id) as unique_payments
        FROM receipts
    ''')
    
    stats = cursor.fetchone()
    db.close()
    
    return jsonify({
        'success': True,
        'stats': dict(stats) if stats else {}
    })
