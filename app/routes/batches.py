from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime

bp = Blueprint('batches', __name__, url_prefix='/api/batches')

@bp.route('', methods=['GET'])
def get_batches():
    """Get all batches"""
    db = get_db()
    batches = db.execute('''
        SELECT b.*, 
               (SELECT COUNT(*) FROM travelers WHERE batch_id = b.id) as booked_seats
        FROM batches b
        ORDER BY b.created_at DESC
    ''').fetchall()
    
    return jsonify({
        'success': True,
        'batches': [dict(batch) for batch in batches]
    })

@bp.route('/<int:batch_id>', methods=['GET'])
def get_batch(batch_id):
    """Get single batch"""
    db = get_db()
    batch = db.execute(
        'SELECT * FROM batches WHERE id = ?',
        (batch_id,)
    ).fetchone()
    
    if batch:
        return jsonify({'success': True, 'batch': dict(batch)})
    return jsonify({'success': False, 'error': 'Batch not found'}), 404

@bp.route('', methods=['POST'])
def create_batch():
    """Create new batch"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    db = get_db()
    cursor = db.execute('''
        INSERT INTO batches (
            batch_name, total_seats, price, departure_date, 
            return_date, status, description, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['batch_name'],
        data.get('total_seats', 150),
        data.get('price'),
        data.get('departure_date'),
        data.get('return_date'),
        data.get('status', 'Open'),
        data.get('description', ''),
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    
    db.commit()
    
    return jsonify({
        'success': True,
        'batch_id': cursor.lastrowid,
        'message': 'Batch created successfully'
    })

@bp.route('/<int:batch_id>', methods=['PUT'])
def update_batch(batch_id):
    """Update batch"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    db = get_db()
    db.execute('''
        UPDATE batches SET
            batch_name = ?, total_seats = ?, price = ?,
            departure_date = ?, return_date = ?, status = ?,
            description = ?, updated_at = ?
        WHERE id = ?
    ''', (
        data['batch_name'],
        data.get('total_seats', 150),
        data.get('price'),
        data.get('departure_date'),
        data.get('return_date'),
        data.get('status', 'Open'),
        data.get('description', ''),
        datetime.now().isoformat(),
        batch_id
    ))
    
    db.commit()
    
    return jsonify({'success': True, 'message': 'Batch updated successfully'})

@bp.route('/<int:batch_id>', methods=['DELETE'])
def delete_batch(batch_id):
    """Delete batch"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    
    # Check if batch has travelers
    travelers = db.execute(
        'SELECT COUNT(*) as count FROM travelers WHERE batch_id = ?',
        (batch_id,)
    ).fetchone()
    
    if travelers['count'] > 0:
        return jsonify({
            'success': False, 
            'error': 'Cannot delete batch with assigned travelers'
        }), 400
    
    db.execute('DELETE FROM batches WHERE id = ?', (batch_id,))
    db.commit()
    
    return jsonify({'success': True, 'message': 'Batch deleted successfully'})
