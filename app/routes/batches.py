from flask import Blueprint, request, jsonify, session
from app.database import get_db, get_db_cursor
import psycopg2
import psycopg2.extras
from functools import wraps
from datetime import datetime

batches_bp = Blueprint('batches', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def convert_decimal_to_float(data):
    if isinstance(data, list):
        for item in data:
            for key, value in item.items():
                if hasattr(value, 'scale'):
                    item[key] = float(value)
    elif isinstance(data, dict):
        for key, value in data.items():
            if hasattr(value, 'scale'):
                data[key] = float(value)
    return data

@batches_bp.route('/', methods=['GET'])
def get_all_batches():
    try:
        conn, cur = get_db_cursor(dictionary=True)
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur.execute("""
            SELECT * FROM batches 
            ORDER BY 
                CASE 
                    WHEN status = 'Open' THEN 1
                    WHEN status = 'Closing Soon' THEN 2
                    ELSE 3
                END,
                departure_date ASC
        """)
        
        batches = cur.fetchall()
        cur.close()
        conn.close()
        
        batches = convert_decimal_to_float(batches)
        
        return jsonify({'success': True, 'batches': batches})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@batches_bp.route('/<int:batch_id>', methods=['GET'])
def get_batch(batch_id):
    try:
        conn, cur = get_db_cursor(dictionary=True)
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur.execute("SELECT * FROM batches WHERE id = %s", (batch_id,))
        batch = cur.fetchone()
        cur.close()
        conn.close()
        
        if batch:
            batch = convert_decimal_to_float(batch)
            return jsonify({'success': True, 'batch': batch})
        return jsonify({'success': False, 'error': 'Batch not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@batches_bp.route('/', methods=['POST'])
@login_required
def create_batch():
    try:
        data = request.json
        required_fields = ['batch_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        conn, cur = get_db_cursor()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur.execute("""
            INSERT INTO batches (
                batch_name, departure_date, return_date, 
                total_seats, price, status, description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get('batch_name'),
            data.get('departure_date'),
            data.get('return_date'),
            data.get('total_seats', 150),
            data.get('price'),
            data.get('status', 'Open'),
            data.get('description')
        ))
        
        batch_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Batch created successfully',
            'batch_id': batch_id
        }), 201
        
    except psycopg2.IntegrityError:
        return jsonify({'success': False, 'error': 'Batch name already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@batches_bp.route('/<int:batch_id>', methods=['PUT'])
@login_required
def update_batch(batch_id):
    try:
        data = request.json
        conn, cur = get_db_cursor()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur.execute("""
            UPDATE batches SET
                batch_name = COALESCE(%s, batch_name),
                departure_date = COALESCE(%s, departure_date),
                return_date = COALESCE(%s, return_date),
                total_seats = COALESCE(%s, total_seats),
                price = COALESCE(%s, price),
                status = COALESCE(%s, status),
                description = COALESCE(%s, description)
            WHERE id = %s
            RETURNING id
        """, (
            data.get('batch_name'),
            data.get('departure_date'),
            data.get('return_date'),
            data.get('total_seats'),
            data.get('price'),
            data.get('status'),
            data.get('description'),
            batch_id
        ))
        
        updated = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        if updated:
            return jsonify({'success': True, 'message': 'Batch updated successfully'})
        return jsonify({'success': False, 'error': 'Batch not found'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@batches_bp.route('/<int:batch_id>', methods=['DELETE'])
@login_required
def delete_batch(batch_id):
    try:
        conn, cur = get_db_cursor()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur.execute("SELECT COUNT(*) FROM travelers WHERE batch_id = %s", (batch_id,))
        traveler_count = cur.fetchone()[0]
        
        if traveler_count > 0:
            return jsonify({
                'success': False, 
                'error': f'Cannot delete batch with {traveler_count} travelers assigned'
            }), 400
        
        cur.execute("DELETE FROM batches WHERE id = %s", (batch_id,))
        deleted = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        if deleted:
            return jsonify({'success': True, 'message': 'Batch deleted successfully'})
        return jsonify({'success': False, 'error': 'Batch not found'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
