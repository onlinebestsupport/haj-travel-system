from flask import Blueprint, request, jsonify, session
from app.database import get_db
import psycopg2
import psycopg2.extras
from functools import wraps
from datetime import datetime

batches_bp = Blueprint('batches', __name__)

# ============ HELPER FUNCTIONS ============

def login_required(f):
    """Decorator to check if admin is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def convert_decimal_to_float(data):
    """Convert decimal.Decimal objects to float for JSON serialization"""
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

# ============ PUBLIC ROUTES (No Login Required) ============

@batches_bp.route('/', methods=['GET'])
def get_all_batches():
    """Get all batches/packages - Public access"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Order by status (Open first) and departure date
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
        
        # Convert decimal to float for JSON serialization
        batches = convert_decimal_to_float(batches)
        
        return jsonify({'success': True, 'batches': batches})
    except Exception as e:
        print(f"Error in batches: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@batches_bp.route('/<int:batch_id>', methods=['GET'])
def get_batch(batch_id):
    """Get single batch by ID - Public access"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM batches WHERE id = %s", (batch_id,))
        batch = cur.fetchone()
        cur.close()
        conn.close()
        
        if batch:
            batch = convert_decimal_to_float(batch)
            return jsonify({'success': True, 'batch': batch})
        return jsonify({'success': False, 'error': 'Batch not found'}), 404
    except Exception as e:
        print(f"Error in get_batch: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@batches_bp.route('/active', methods=['GET'])
def get_active_batches():
    """Get only active/open batches - For front page"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("""
            SELECT * FROM batches 
            WHERE status IN ('Open', 'Closing Soon')
            ORDER BY departure_date ASC
        """)
        
        batches = cur.fetchall()
        cur.close()
        conn.close()
        
        batches = convert_decimal_to_float(batches)
        
        return jsonify({'success': True, 'batches': batches})
    except Exception as e:
        print(f"Error in active batches: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ ADMIN ROUTES (Login Required) ============

@batches_bp.route('/', methods=['POST'])
@login_required
def create_batch():
    """Create a new batch/package - Admin only"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['batch_name']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'success': False, 
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO batches (
                batch_name, departure_date, return_date, 
                total_seats, booked_seats, price, status, description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get('batch_name'),
            data.get('departure_date'),
            data.get('return_date'),
            data.get('total_seats', 150),
            0,  # New batches start with 0 booked seats
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
        
    except psycopg2.IntegrityError as e:
        if 'duplicate key' in str(e):
            return jsonify({'success': False, 'error': 'Batch name already exists'}), 400
        return jsonify({'success': False, 'error': 'Database integrity error'}), 400
    except Exception as e:
        print(f"Error creating batch: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@batches_bp.route('/<int:batch_id>', methods=['PUT'])
@login_required
def update_batch(batch_id):
    """Update an existing batch - Admin only"""
    try:
        data = request.json
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur = conn.cursor()
        
        # Build dynamic update query
        update_fields = []
        params = []
        
        updatable_fields = {
            'batch_name': data.get('batch_name'),
            'departure_date': data.get('departure_date'),
            'return_date': data.get('return_date'),
            'total_seats': data.get('total_seats'),
            'price': data.get('price'),
            'status': data.get('status'),
            'description': data.get('description')
        }
        
        for field, value in updatable_fields.items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                params.append(value)
        
        if not update_fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        
        params.append(batch_id)
        
        cur.execute(f"""
            UPDATE batches 
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING id
        """, params)
        
        updated = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        if updated:
            return jsonify({'success': True, 'message': 'Batch updated successfully'})
        return jsonify({'success': False, 'error': 'Batch not found'}), 404
        
    except psycopg2.IntegrityError as e:
        if 'duplicate key' in str(e):
            return jsonify({'success': False, 'error': 'Batch name already exists'}), 400
        return jsonify({'success': False, 'error': 'Database integrity error'}), 400
    except Exception as e:
        print(f"Error updating batch: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@batches_bp.route('/<int:batch_id>', methods=['DELETE'])
@login_required
def delete_batch(batch_id):
    """Delete a batch - Admin only"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur = conn.cursor()
        
        # Check if batch has travelers
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
        print(f"Error deleting batch: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ STATS ROUTES ============

@batches_bp.route('/stats', methods=['GET'])
def get_batch_stats():
    """Get batch statistics"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur = conn.cursor()
        
        # Total batches
        cur.execute("SELECT COUNT(*) FROM batches")
        total = cur.fetchone()[0]
        
        # Active batches
        cur.execute("SELECT COUNT(*) FROM batches WHERE status IN ('Open', 'Closing Soon')")
        active = cur.fetchone()[0]
        
        # Total seats
        cur.execute("SELECT COALESCE(SUM(total_seats), 0) FROM batches")
        total_seats = cur.fetchone()[0]
        
        # Booked seats
        cur.execute("SELECT COALESCE(SUM(booked_seats), 0) FROM batches")
        booked_seats = cur.fetchone()[0]
        
        # Available seats
        available_seats = total_seats - booked_seats
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_batches': total,
                'active_batches': active,
                'total_seats': total_seats,
                'booked_seats': booked_seats,
                'available_seats': available_seats,
                'occupancy_rate': round((booked_seats / total_seats * 100) if total_seats > 0 else 0, 2)
            }
        })
    except Exception as e:
        print(f"Error in batch stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ BULK OPERATIONS ============

@batches_bp.route('/bulk/status', methods=['POST'])
@login_required
def bulk_update_status():
    """Update status for multiple batches"""
    try:
        data = request.json
        batch_ids = data.get('batch_ids', [])
        new_status = data.get('status')
        
        if not batch_ids or not new_status:
            return jsonify({'success': False, 'error': 'Batch IDs and status are required'}), 400
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur = conn.cursor()
        cur.execute("""
            UPDATE batches 
            SET status = %s 
            WHERE id = ANY(%s)
            RETURNING id
        """, (new_status, batch_ids))
        
        updated = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Updated {updated} batches',
            'updated': updated
        })
    except Exception as e:
        print(f"Error in bulk update: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
