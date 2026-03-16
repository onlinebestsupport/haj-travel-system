from flask import Blueprint, request, jsonify, session
from app.database import get_db, release_db
from datetime import datetime
import json

bp = Blueprint('receipts', __name__, url_prefix='/api/receipts')

@bp.route('', methods=['GET'])
def get_receipts():
    """Get all receipts"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT * FROM receipts ORDER BY created_at DESC")
        receipts = cursor.fetchall()
        return jsonify({
            'success': True,
            'receipts': [dict(r) for r in receipts]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:receipt_id>', methods=['GET'])
def get_receipt(receipt_id):
    """Get single receipt"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT * FROM receipts WHERE id = %s", (receipt_id,))
        receipt = cursor.fetchone()
        
        if not receipt:
            return jsonify({'success': False, 'error': 'Receipt not found'}), 404
        
        return jsonify({'success': True, 'receipt': dict(receipt)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('', methods=['POST'])
def create_receipt():
    """Create new receipt"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.json

    required = ['traveler_id', 'amount', 'receipt_date', 'payment_method']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400

    # Generate receipt number
    timestamp = int(datetime.now().timestamp())
    receipt_number = f"REC-{datetime.now().strftime('%Y%m%d')}-{timestamp}"

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()

        cursor.execute("""
            INSERT INTO receipts (
                receipt_number, traveler_id, payment_id, amount, receipt_date,
                payment_method, notes, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            receipt_number,
            data['traveler_id'],
            data.get('payment_id'),
            data['amount'],
            data['receipt_date'],
            data['payment_method'],
            data.get('notes'),
            datetime.now()
        ))

        result = cursor.fetchone()
        receipt_id = result['id'] if result else None
        conn.commit()

        return jsonify({
            'success': True,
            'receipt_id': receipt_id,
            'receipt_number': receipt_number,
            'message': 'Receipt created successfully'
        })

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/payment/<int:payment_id>', methods=['GET'])
def get_payment_receipts(payment_id):
    """Get receipts for a specific payment"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT * FROM receipts WHERE payment_id = %s ORDER BY created_at DESC", (payment_id,))
        receipts = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'receipts': [dict(r) for r in receipts]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/traveler/<int:traveler_id>', methods=['GET'])
def get_traveler_receipts(traveler_id):
    """Get receipts for a specific traveler"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT * FROM receipts WHERE traveler_id = %s ORDER BY created_at DESC", (traveler_id,))
        receipts = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'receipts': [dict(r) for r in receipts]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:receipt_id>/print', methods=['GET'])
def print_receipt(receipt_id):
    """Print receipt (returns HTML for printing)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("""
            SELECT r.*, t.first_name, t.last_name, t.passport_no 
            FROM receipts r
            JOIN travelers t ON r.traveler_id = t.id
            WHERE r.id = %s
        """, (receipt_id,))
        
        receipt = cursor.fetchone()
        
        if not receipt:
            return jsonify({'success': False, 'error': 'Receipt not found'}), 404
        
        # Generate HTML for printing
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Receipt {receipt['receipt_number']}</title>
            <style>
                body {{ font-family: Arial; padding: 20px; }}
                .receipt {{ max-width: 800px; margin: 0 auto; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .details {{ margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; border: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <div class="receipt">
                <div class="header">
                    <h1>Payment Receipt</h1>
                    <h3>Receipt #: {receipt['receipt_number']}</h3>
                </div>
                <div class="details">
                    <p><strong>Traveler:</strong> {receipt['first_name']} {receipt['last_name']}</p>
                    <p><strong>Passport:</strong> {receipt['passport_no']}</p>
                    <p><strong>Date:</strong> {receipt['receipt_date']}</p>
                    <p><strong>Amount:</strong> ₹{receipt['amount']}</p>
                    <p><strong>Payment Method:</strong> {receipt['payment_method']}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html, 200, {'Content-Type': 'text/html'}
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:receipt_id>', methods=['DELETE'])
def delete_receipt(receipt_id):
    """Delete receipt"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute('DELETE FROM receipts WHERE id = %s', (receipt_id,))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Receipt deleted successfully'})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/range', methods=['GET'])
def get_receipts_by_date_range():
    """Get receipts by date range"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'success': False, 'error': 'Start date and end date required'}), 400

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("""
            SELECT * FROM receipts 
            WHERE receipt_date BETWEEN %s AND %s 
            ORDER BY receipt_date DESC
        """, (start_date, end_date))
        
        receipts = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'receipts': [dict(r) for r in receipts],
            'count': len(receipts)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/stats', methods=['GET'])
def get_receipt_stats():
    """Get receipt statistics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        # Today's receipts
        cursor.execute("""
            SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
            FROM receipts 
            WHERE DATE(receipt_date) = CURRENT_DATE
        """)
        today = cursor.fetchone()
        
        # This month's receipts
        cursor.execute("""
            SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
            FROM receipts 
            WHERE EXTRACT(MONTH FROM receipt_date) = EXTRACT(MONTH FROM CURRENT_DATE)
            AND EXTRACT(YEAR FROM receipt_date) = EXTRACT(YEAR FROM CURRENT_DATE)
        """)
        month = cursor.fetchone()
        
        # Total receipts
        cursor.execute("""
            SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
            FROM receipts
        """)
        total = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'stats': {
                'today': dict(today) if today else {'count': 0, 'total': 0},
                'this_month': dict(month) if month else {'count': 0, 'total': 0},
                'total': dict(total) if total else {'count': 0, 'total': 0}
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)