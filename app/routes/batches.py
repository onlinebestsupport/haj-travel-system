from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime
import json

bp = Blueprint('batches', __name__, url_prefix='/api/batches')

@bp.route('', methods=['GET'])
def get_batches():
    """Get all batches with enhanced details"""
    db = get_db()
    cursor = db.cursor()
    
    # Get all batches with booked seats count
    cursor.execute('''
        SELECT 
            b.*, 
            (SELECT COUNT(*) FROM travelers WHERE batch_id = b.id) as booked_seats,
            (SELECT SUM(amount) FROM payments WHERE batch_id = b.id AND status = 'completed') as total_collected
        FROM batches b
        ORDER BY 
            CASE 
                WHEN b.status = 'Open' THEN 1
                WHEN b.status = 'Closing Soon' THEN 2
                WHEN b.status = 'Full' THEN 3
                WHEN b.status = 'Closed' THEN 4
                ELSE 5
            END,
            b.departure_date ASC
    ''')
    
    batches = cursor.fetchall()
    db.close()
    
    return jsonify({
        'success': True, 
        'batches': [dict(b) for b in batches]
    })

@bp.route('/<int:batch_id>', methods=['GET'])
def get_batch(batch_id):
    """Get single batch with complete details"""
    db = get_db()
    cursor = db.cursor()
    
    # Get batch details
    cursor.execute('''
        SELECT 
            b.*, 
            (SELECT COUNT(*) FROM travelers WHERE batch_id = b.id) as booked_seats,
            (SELECT COUNT(*) FROM travelers WHERE batch_id = b.id AND passport_status = 'Active') as active_travelers,
            (SELECT SUM(amount) FROM payments WHERE batch_id = b.id AND status = 'completed') as total_collected,
            (SELECT SUM(amount) FROM payments WHERE batch_id = b.id AND status = 'pending') as pending_amount
        FROM batches b
        WHERE b.id = ?
    ''', (batch_id,))
    
    batch = cursor.fetchone()
    
    if not batch:
        db.close()
        return jsonify({'success': False, 'error': 'Batch not found'}), 404
    
    # Get travelers in this batch
    cursor.execute('''
        SELECT id, first_name, last_name, passport_no, mobile, email, passport_status
        FROM travelers 
        WHERE batch_id = ?
        ORDER BY created_at DESC
    ''', (batch_id,))
    
    travelers = cursor.fetchall()
    
    # Get recent payments for this batch
    cursor.execute('''
        SELECT p.*, t.first_name, t.last_name 
        FROM payments p
        JOIN travelers t ON p.traveler_id = t.id
        WHERE p.batch_id = ?
        ORDER BY p.payment_date DESC
        LIMIT 10
    ''', (batch_id,))
    
    payments = cursor.fetchall()
    
    db.close()
    
    return jsonify({
        'success': True, 
        'batch': dict(batch),
        'travelers': [dict(t) for t in travelers],
        'recent_payments': [dict(p) for p in payments]
    })

@bp.route('', methods=['POST'])
def create_batch():
    """Create new batch with all fields"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    # Validate required fields
    if not data.get('batch_name'):
        return jsonify({'success': False, 'error': 'Batch name is required'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO batches (
            batch_name, total_seats, booked_seats, price, 
            departure_date, return_date, status, description,
            itinerary, inclusions, exclusions, hotel_details,
            transport_details, meal_plan, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['batch_name'],
        data.get('total_seats', 150),
        0,  # booked_seats starts at 0
        data.get('price'),
        data.get('departure_date'),
        data.get('return_date'),
        data.get('status', 'Open'),
        data.get('description', ''),
        data.get('itinerary', ''),
        data.get('inclusions', ''),
        data.get('exclusions', ''),
        data.get('hotel_details', ''),
        data.get('transport_details', ''),
        data.get('meal_plan', ''),
        now,
        now
    ))
    
    batch_id = cursor.lastrowid
    db.commit()
    
    # Log activity
    log_activity(session['user_id'], 'create', 'batch', f'Created batch: {data["batch_name"]}')
    
    db.close()
    
    return jsonify({
        'success': True, 
        'batch_id': batch_id,
        'message': 'Batch created successfully'
    })

@bp.route('/<int:batch_id>', methods=['PUT'])
def update_batch(batch_id):
    """Update batch with all fields"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if batch exists
    cursor.execute('SELECT id FROM batches WHERE id = ?', (batch_id,))
    if not cursor.fetchone():
        db.close()
        return jsonify({'success': False, 'error': 'Batch not found'}), 404
    
    now = datetime.now().isoformat()
    
    cursor.execute('''
        UPDATE batches SET
            batch_name = ?,
            total_seats = ?,
            price = ?,
            departure_date = ?,
            return_date = ?,
            status = ?,
            description = ?,
            itinerary = ?,
            inclusions = ?,
            exclusions = ?,
            hotel_details = ?,
            transport_details = ?,
            meal_plan = ?,
            updated_at = ?
        WHERE id = ?
    ''', (
        data.get('batch_name'),
        data.get('total_seats', 150),
        data.get('price'),
        data.get('departure_date'),
        data.get('return_date'),
        data.get('status', 'Open'),
        data.get('description', ''),
        data.get('itinerary', ''),
        data.get('inclusions', ''),
        data.get('exclusions', ''),
        data.get('hotel_details', ''),
        data.get('transport_details', ''),
        data.get('meal_plan', ''),
        now,
        batch_id
    ))
    
    db.commit()
    
    # Log activity
    log_activity(session['user_id'], 'update', 'batch', f'Updated batch ID: {batch_id}')
    
    db.close()
    
    return jsonify({
        'success': True, 
        'message': 'Batch updated successfully'
    })

@bp.route('/<int:batch_id>', methods=['DELETE'])
def delete_batch(batch_id):
    """Delete batch"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if batch has travelers
    cursor.execute('SELECT COUNT(*) as count FROM travelers WHERE batch_id = ?', (batch_id,))
    count = cursor.fetchone()['count']
    
    if count > 0:
        db.close()
        return jsonify({
            'success': False, 
            'error': f'Cannot delete batch with {count} traveler(s). Reassign travelers first.'
        }), 400
    
    # Delete batch
    cursor.execute('DELETE FROM batches WHERE id = ?', (batch_id,))
    db.commit()
    
    # Log activity
    log_activity(session['user_id'], 'delete', 'batch', f'Deleted batch ID: {batch_id}')
    
    db.close()
    
    return jsonify({
        'success': True, 
        'message': 'Batch deleted successfully'
    })

@bp.route('/<int:batch_id>/travelers', methods=['GET'])
def get_batch_travelers(batch_id):
    """Get all travelers in a specific batch"""
    db = get_db()
    cursor = db.cursor()
    
    # Check if batch exists
    cursor.execute('SELECT id, batch_name FROM batches WHERE id = ?', (batch_id,))
    batch = cursor.fetchone()
    
    if not batch:
        db.close()
        return jsonify({'success': False, 'error': 'Batch not found'}), 404
    
    # Get travelers
    cursor.execute('''
        SELECT 
            id, first_name, last_name, passport_no, mobile, email,
            passport_status, vaccine_status, wheelchair, pin
        FROM travelers 
        WHERE batch_id = ?
        ORDER BY created_at DESC
    ''', (batch_id,))
    
    travelers = cursor.fetchall()
    
    # Get payment summary
    cursor.execute('''
        SELECT 
            COUNT(*) as payment_count,
            SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as total_paid,
            SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as total_pending
        FROM payments 
        WHERE batch_id = ?
    ''', (batch_id,))
    
    payment_summary = cursor.fetchone()
    
    db.close()
    
    return jsonify({
        'success': True,
        'batch': dict(batch),
        'travelers': [dict(t) for t in travelers],
        'payment_summary': dict(payment_summary) if payment_summary else {}
    })

@bp.route('/<int:batch_id>/payments', methods=['GET'])
def get_batch_payments(batch_id):
    """Get all payments for a specific batch"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            p.*,
            t.first_name,
            t.last_name,
            t.passport_no
        FROM payments p
        JOIN travelers t ON p.traveler_id = t.id
        WHERE p.batch_id = ?
        ORDER BY p.payment_date DESC
    ''', (batch_id,))
    
    payments = cursor.fetchall()
    
    db.close()
    
    return jsonify({
        'success': True,
        'payments': [dict(p) for p in payments]
    })

@bp.route('/<int:batch_id>/stats', methods=['GET'])
def get_batch_stats(batch_id):
    """Get comprehensive statistics for a batch"""
    db = get_db()
    cursor = db.cursor()
    
    # Basic batch info
    cursor.execute('''
        SELECT 
            batch_name,
            total_seats,
            (SELECT COUNT(*) FROM travelers WHERE batch_id = ?) as booked_seats,
            price,
            departure_date,
            return_date,
            status
        FROM batches WHERE id = ?
    ''', (batch_id, batch_id))
    
    batch_info = cursor.fetchone()
    
    if not batch_info:
        db.close()
        return jsonify({'success': False, 'error': 'Batch not found'}), 404
    
    # Payment statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total_transactions,
            SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as total_collected,
            SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as pending_amount,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count
        FROM payments 
        WHERE batch_id = ?
    ''', (batch_id,))
    
    payment_stats = cursor.fetchone()
    
    # Payment method breakdown
    cursor.execute('''
        SELECT 
            payment_method,
            COUNT(*) as count,
            SUM(amount) as total
        FROM payments 
        WHERE batch_id = ? AND status = 'completed'
        GROUP BY payment_method
    ''', (batch_id,))
    
    method_breakdown = cursor.fetchall()
    
    # Traveler status breakdown
    cursor.execute('''
        SELECT 
            passport_status,
            COUNT(*) as count
        FROM travelers 
        WHERE batch_id = ?
        GROUP BY passport_status
    ''', (batch_id,))
    
    traveler_status = cursor.fetchall()
    
    # Vaccine status breakdown
    cursor.execute('''
        SELECT 
            vaccine_status,
            COUNT(*) as count
        FROM travelers 
        WHERE batch_id = ?
        GROUP BY vaccine_status
    ''', (batch_id,))
    
    vaccine_status = cursor.fetchall()
    
    # Recent activity
    cursor.execute('''
        SELECT 
            'payment' as type,
            p.amount,
            p.payment_date as date,
            t.first_name || ' ' || t.last_name as traveler
        FROM payments p
        JOIN travelers t ON p.traveler_id = t.id
        WHERE p.batch_id = ?
        UNION ALL
        SELECT 
            'traveler' as type,
            NULL as amount,
            t.created_at as date,
            t.first_name || ' ' || t.last_name as traveler
        FROM travelers t
        WHERE t.batch_id = ?
        ORDER BY date DESC
        LIMIT 10
    ''', (batch_id, batch_id))
    
    recent_activity = cursor.fetchall()
    
    db.close()
    
    return jsonify({
        'success': True,
        'batch_info': dict(batch_info),
        'payment_stats': dict(payment_stats) if payment_stats else {},
        'payment_methods': [dict(m) for m in method_breakdown],
        'traveler_status': [dict(s) for s in traveler_status],
        'vaccine_status': [dict(v) for v in vaccine_status],
        'recent_activity': [dict(a) for a in recent_activity]
    })

@bp.route('/summary', methods=['GET'])
def get_batches_summary():
    """Get summary statistics for all batches"""
    db = get_db()
    cursor = db.cursor()
    
    # Overall statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total_batches,
            SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open_batches,
            SUM(CASE WHEN status = 'Closing Soon' THEN 1 ELSE 0 END) as closing_soon,
            SUM(CASE WHEN status = 'Full' THEN 1 ELSE 0 END) as full_batches,
            SUM(CASE WHEN status = 'Closed' THEN 1 ELSE 0 END) as closed_batches,
            SUM(total_seats) as total_seats,
            SUM(booked_seats) as booked_seats,
            SUM(price * booked_seats) as total_value
        FROM batches
    ''')
    
    summary = cursor.fetchone()
    
    # Upcoming departures
    cursor.execute('''
        SELECT 
            id, batch_name, departure_date, booked_seats, total_seats,
            (booked_seats * 100.0 / total_seats) as occupancy_rate
        FROM batches
        WHERE departure_date >= date('now')
            AND status != 'Closed'
        ORDER BY departure_date ASC
        LIMIT 5
    ''')
    
    upcoming = cursor.fetchall()
    
    db.close()
    
    return jsonify({
        'success': True,
        'summary': dict(summary) if summary else {},
        'upcoming_departures': [dict(u) for u in upcoming]
    })

# Helper function to log activity
def log_activity(user_id, action, module, description):
    """Log user activity"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO activity_log (user_id, action, module, description, ip_address) VALUES (?, ?, ?, ?, ?)',
            (user_id, action, module, description, request.remote_addr)
        )
        db.commit()
        db.close()
    except:
        pass  # Fail silently
