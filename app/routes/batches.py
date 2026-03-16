from flask import Blueprint, request, jsonify, session, current_app
from app.database import get_db, release_db
from datetime import datetime
import json

bp = Blueprint('batches', __name__, url_prefix='/api/batches')

@bp.route('', methods=['GET'])
def get_batches():
    """Get all batches"""
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT * FROM batches ORDER BY created_at DESC")
        batches = cursor.fetchall()
        return jsonify({'success': True, 'batches': [dict(b) for b in batches]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:batch_id>', methods=['GET'])
def get_batch(batch_id):
    """Get single batch"""
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT * FROM batches WHERE id = %s", (batch_id,))
        batch = cursor.fetchone()
        if not batch:
            return jsonify({'success': False, 'error': 'Batch not found'}), 404
        return jsonify({'success': True, 'batch': dict(batch)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('', methods=['POST'])
def create_batch():
    """Create new batch"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    # Validate required fields
    required = ['batch_name']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute('''
            INSERT INTO batches (batch_name, total_seats, price, departure_date, return_date, 
                                 status, description, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            data['batch_name'],
            data.get('total_seats', 150),
            data.get('price'),
            data.get('departure_date'),
            data.get('return_date'),
            data.get('status', 'Open'),
            data.get('description'),
            datetime.now(),
            datetime.now()
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        return jsonify({
            'success': True,
            'batch_id': result['id'],
            'message': 'Batch created successfully'
        })
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:batch_id>', methods=['PUT'])
def update_batch(batch_id):
    """Update batch"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        # Check if batch exists
        cursor.execute("SELECT id FROM batches WHERE id = %s", (batch_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Batch not found'}), 404
        
        # Build update query dynamically
        updates = []
        values = []
        
        updateable_fields = ['batch_name', 'total_seats', 'price', 'departure_date', 
                            'return_date', 'status', 'description']
        
        for field in updateable_fields:
            if field in data:
                updates.append(f"{field} = %s")
                values.append(data[field])
        
        if updates:
            values.append(datetime.now())
            values.append(batch_id)
            query = f"UPDATE batches SET {', '.join(updates)}, updated_at = %s WHERE id = %s"
            cursor.execute(query, values)
            conn.commit()
        
        return jsonify({'success': True, 'message': 'Batch updated successfully'})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:batch_id>', methods=['DELETE'])
def delete_batch(batch_id):
    """Delete batch"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        # Check if batch has travelers
        cursor.execute("SELECT COUNT(*) as count FROM travelers WHERE batch_id = %s", (batch_id,))
        result = cursor.fetchone()
        if result and result['count'] > 0:
            return jsonify({
                'success': False,
                'error': 'Cannot delete batch with associated travelers'
            }), 400
        
        cursor.execute("DELETE FROM batches WHERE id = %s", (batch_id,))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Batch deleted successfully'})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:batch_id>/travelers', methods=['GET'])
def get_batch_travelers(batch_id):
    """Get travelers in a batch"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute('''
            SELECT id, first_name, last_name, passport_no, mobile, email, passport_status
            FROM travelers
            WHERE batch_id = %s
            ORDER BY created_at DESC
        ''', (batch_id,))
        
        travelers = cursor.fetchall()
        return jsonify({'success': True, 'travelers': [dict(t) for t in travelers]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:batch_id>/payments', methods=['GET'])
def get_batch_payments(batch_id):
    """Get payments for a batch"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute('''
            SELECT p.*, t.first_name, t.last_name, t.passport_no
            FROM payments p
            JOIN travelers t ON p.traveler_id = t.id
            WHERE p.batch_id = %s
            ORDER BY p.payment_date DESC
        ''', (batch_id,))
        
        payments = cursor.fetchall()
        
        # Get payment summary
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
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:batch_id>/stats', methods=['GET'])
def get_batch_stats(batch_id):
    """Get statistics for a batch"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        # Get batch details with traveler count
        cursor.execute('''
            SELECT 
                b.*,
                COUNT(t.id) as traveler_count,
                COALESCE(SUM(CASE WHEN p.status = 'completed' THEN p.amount ELSE 0 END), 0) as total_collected
            FROM batches b
            LEFT JOIN travelers t ON b.id = t.batch_id
            LEFT JOIN payments p ON b.id = p.batch_id AND p.status = 'completed'
            WHERE b.id = %s
            GROUP BY b.id
        ''', (batch_id,))
        
        batch = cursor.fetchone()
        
        if not batch:
            return jsonify({'success': False, 'error': 'Batch not found'}), 404
        
        return jsonify({'success': True, 'stats': dict(batch)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/summary', methods=['GET'])
def get_batches_summary():
    """Get summary of all batches"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        cursor.execute('''
            SELECT
                COUNT(*) as total_batches,
                SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open_batches,
                SUM(CASE WHEN status = 'Closed' THEN 1 ELSE 0 END) as closed_batches,
                SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled_batches,
                COALESCE(SUM(total_seats), 0) as total_seats,
                COALESCE(SUM(booked_seats), 0) as total_booked,
                COALESCE(SUM(price * booked_seats), 0) as estimated_revenue
            FROM batches
        ''')
        
        summary = cursor.fetchone()
        
        return jsonify({'success': True, 'summary': dict(summary) if summary else {}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)