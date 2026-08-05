from flask import Blueprint, request, jsonify, session, current_app
from app.database import get_db, release_db
from datetime import datetime
import json

bp = Blueprint('batches', __name__, url_prefix='/api/batches')

# ============================================================
# DATABASE MIGRATION - Add return_date column if missing
# ============================================================
def migrate_batches_table():
    """Add return_date column to batches table if it doesn't exist"""
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        # Check if return_date column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'batches' AND column_name = 'return_date'
        """)
        
        if not cursor.fetchone():
            print("🔄 Adding return_date column to batches table...")
            cursor.execute("""
                ALTER TABLE batches 
                ADD COLUMN return_date DATE
            """)
            conn.commit()
            print("✅ return_date column added successfully!")
        else:
            print("✅ return_date column already exists")
            
    except Exception as e:
        print(f"⚠️ Migration error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_db(conn, cursor)

# Run migration on import
try:
    migrate_batches_table()
except Exception as e:
    print(f"⚠️ Migration failed: {e}")

# ============================================================
# ROUTES
# ============================================================

@bp.route('', methods=['GET'])
def get_batches():
    """Get all batches with return_date included"""
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        # Select all fields including return_date
        cursor.execute("""
            SELECT 
                id, batch_name, total_seats, booked_seats, price, 
                departure_date, return_date, status, description, 
                created_at, updated_at
            FROM batches 
            ORDER BY created_at DESC
        """)
        batches = cursor.fetchall()
        
        # Convert to dict and ensure return_date is included
        result = []
        for b in batches:
            batch_dict = dict(b)
            # Ensure return_date is in the response even if None
            if 'return_date' not in batch_dict:
                batch_dict['return_date'] = None
            result.append(batch_dict)
            
        return jsonify({'success': True, 'batches': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:batch_id>', methods=['GET'])
def get_batch(batch_id):
    """Get single batch with return_date"""
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("""
            SELECT 
                id, batch_name, total_seats, booked_seats, price, 
                departure_date, return_date, status, description, 
                created_at, updated_at
            FROM batches 
            WHERE id = %s
        """, (batch_id,))
        batch = cursor.fetchone()
        if not batch:
            return jsonify({'success': False, 'error': 'Batch not found'}), 404
            
        batch_dict = dict(batch)
        if 'return_date' not in batch_dict:
            batch_dict['return_date'] = None
            
        return jsonify({'success': True, 'batch': batch_dict})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/for-traveler/<int:batch_id>', methods=['GET'])
def get_batch_for_traveler(batch_id):
    """
    Get batch details specifically for traveler form
    Includes return_date for auto-population
    """
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("""
            SELECT 
                id, batch_name, return_date, departure_date,
                price, total_seats, booked_seats, status
            FROM batches 
            WHERE id = %s
        """, (batch_id,))
        batch = cursor.fetchone()
        
        if not batch:
            return jsonify({'success': False, 'error': 'Batch not found'}), 404
        
        batch_dict = dict(batch)
        if 'return_date' not in batch_dict:
            batch_dict['return_date'] = None
            
        return jsonify({
            'success': True,
            'batch': batch_dict,
            'has_return_date': batch_dict.get('return_date') is not None
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('', methods=['POST'])
def create_batch():
    """Create new batch with return_date"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    # Validate required fields
    if not data.get('batch_name'):
        return jsonify({'success': False, 'error': 'Batch name is required'}), 400
    
    # Validate return date is after departure date
    departure_date = data.get('departure_date')
    return_date = data.get('return_date')
    
    if departure_date and return_date and return_date < departure_date:
        return jsonify({
            'success': False, 
            'error': 'Return date must be after departure date'
        }), 400
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute('''
            INSERT INTO batches (
                batch_name, total_seats, price, 
                departure_date, return_date, 
                status, description, created_at, updated_at
            )
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
        batch_id = result['id'] if result else None
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'message': 'Batch created successfully',
            'return_date': data.get('return_date')
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
    """Update batch with return_date"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    # Validate return date is after departure date
    departure_date = data.get('departure_date')
    return_date = data.get('return_date')
    
    if departure_date and return_date and return_date < departure_date:
        return jsonify({
            'success': False, 
            'error': 'Return date must be after departure date'
        }), 400
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        # Check if batch exists
        cursor.execute("SELECT id FROM batches WHERE id = %s", (batch_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Batch not found'}), 404
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        field_mapping = {
            'batch_name': data.get('batch_name'),
            'total_seats': data.get('total_seats'),
            'price': data.get('price'),
            'departure_date': data.get('departure_date'),
            'return_date': data.get('return_date'),
            'status': data.get('status'),
            'description': data.get('description')
        }
        
        for field, value in field_mapping.items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                params.append(value)
        
        update_fields.append("updated_at = %s")
        params.append(datetime.now())
        params.append(batch_id)
        
        if update_fields:
            query = f"UPDATE batches SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, params)
        
        conn.commit()
        
        # Get updated batch
        cursor.execute("""
            SELECT 
                id, batch_name, total_seats, booked_seats, price, 
                departure_date, return_date, status, description, 
                created_at, updated_at
            FROM batches WHERE id = %s
        """, (batch_id,))
        updated_batch = cursor.fetchone()
        
        return jsonify({
            'success': True, 
            'message': 'Batch updated successfully',
            'batch': dict(updated_batch) if updated_batch else None,
            'return_date': return_date
        })
        
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

# ============================================================
# ADDITIONAL ENDPOINTS
# ============================================================

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
            SELECT 
                t.id, t.first_name, t.last_name, t.passport_no, 
                t.mobile, t.email, t.passport_status,
                t.expected_return_date
            FROM travelers t
            WHERE t.batch_id = %s
            ORDER BY t.created_at DESC
        ''', (batch_id,))
        
        travelers = cursor.fetchall()
        return jsonify({'success': True, 'travelers': [dict(t) for t in travelers]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/summary', methods=['GET'])
def get_batches_summary():
    """Get summary of all batches including return date stats"""
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
                SUM(CASE WHEN status = 'Closing Soon' THEN 1 ELSE 0 END) as closing_batches,
                SUM(CASE WHEN status = 'Full' THEN 1 ELSE 0 END) as full_batches,
                COALESCE(SUM(total_seats), 0) as total_seats,
                COALESCE(SUM(booked_seats), 0) as total_booked,
                COUNT(CASE WHEN return_date IS NOT NULL THEN 1 END) as batches_with_return_date
            FROM batches
        ''')
        
        summary = cursor.fetchone()
        return jsonify({'success': True, 'summary': dict(summary) if summary else {}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/with-return-date', methods=['GET'])
def get_batches_with_return_date():
    """Get only batches that have a return date set"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("""
            SELECT 
                id, batch_name, return_date, departure_date,
                total_seats, booked_seats, status
            FROM batches 
            WHERE return_date IS NOT NULL
            ORDER BY return_date ASC
        """)
        batches = cursor.fetchall()
        return jsonify({
            'success': True, 
            'batches': [dict(b) for b in batches],
            'count': len(batches)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

print("✅ batches.py loaded successfully with return_date support!")
