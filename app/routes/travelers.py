from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime
import json

bp = Blueprint('travelers', __name__, url_prefix='/api/travelers')

@bp.route('', methods=['GET'])
def get_travelers():
    """Get all travelers"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT t.*, b.batch_name 
        FROM travelers t
        LEFT JOIN batches b ON t.batch_id = b.id
        ORDER BY t.created_at DESC
    ''')
    travelers = cursor.fetchall()
    db.close()
    return jsonify({'success': True, 'travelers': [dict(t) for t in travelers]})

@bp.route('/<int:traveler_id>', methods=['GET'])
def get_traveler(traveler_id):
    """Get single traveler"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT t.*, b.batch_name, b.price as batch_price, b.departure_date, b.return_date, b.status as batch_status
        FROM travelers t
        LEFT JOIN batches b ON t.batch_id = b.id
        WHERE t.id = ?
    ''', (traveler_id,))
    traveler = cursor.fetchone()
    
    if traveler:
        # Get payment history
        cursor.execute('''
            SELECT * FROM payments 
            WHERE traveler_id = ? 
            ORDER BY payment_date DESC
        ''', (traveler_id,))
        payments = cursor.fetchall()
        
        db.close()
        result = dict(traveler)
        result['payments'] = [dict(p) for p in payments]
        return jsonify({'success': True, 'traveler': result})
    
    db.close()
    return jsonify({'success': False, 'error': 'Traveler not found'}), 404

@bp.route('/passport/<string:passport_no>', methods=['GET'])
def get_traveler_by_passport(passport_no):
    """Get traveler by passport number"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT t.*, b.batch_name, b.price as batch_price, b.departure_date, b.return_date, b.status as batch_status
        FROM travelers t
        LEFT JOIN batches b ON t.batch_id = b.id
        WHERE t.passport_no = ?
    ''', (passport_no,))
    traveler = cursor.fetchone()
    
    if traveler:
        # Get payment history
        cursor.execute('''
            SELECT * FROM payments 
            WHERE traveler_id = ? 
            ORDER BY payment_date DESC
        ''', (traveler['id'],))
        payments = cursor.fetchall()
        
        db.close()
        result = dict(traveler)
        result['payments'] = [dict(p) for p in payments]
        return jsonify({'success': True, 'traveler': result})
    
    db.close()
    return jsonify({'success': False, 'error': 'Traveler not found'}), 404

@bp.route('', methods=['POST'])
def create_traveler():
    """Create new traveler"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    # Validate required fields
    required = ['first_name', 'last_name', 'passport_no', 'mobile', 'batch_id']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    passport_name = data.get('passport_name') or f"{data['first_name']} {data['last_name']}".strip()
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO travelers (
                first_name, last_name, passport_name, batch_id,
                passport_no, passport_issue_date, passport_expiry_date,
                passport_status, gender, dob, mobile, email,
                aadhaar, pan, aadhaar_pan_linked, vaccine_status,
                wheelchair, place_of_birth, place_of_issue,
                passport_address, father_name, mother_name, spouse_name,
                passport_scan, aadhaar_scan, pan_scan, vaccine_scan,
                extra_fields, pin, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['first_name'], data['last_name'], passport_name, data['batch_id'],
            data['passport_no'], data.get('passport_issue_date'), data.get('passport_expiry_date'),
            data.get('passport_status', 'Active'), data.get('gender'), data.get('dob'),
            data['mobile'], data.get('email'), data.get('aadhaar'), data.get('pan'),
            data.get('aadhaar_pan_linked', 'No'), data.get('vaccine_status', 'Not Vaccinated'),
            data.get('wheelchair', 'No'), data.get('place_of_birth'), data.get('place_of_issue'),
            data.get('passport_address'), data.get('father_name'), data.get('mother_name'),
            data.get('spouse_name'), data.get('passport_scan'), data.get('aadhaar_scan'),
            data.get('pan_scan'), data.get('vaccine_scan'), data.get('extra_fields', '{}'),
            data.get('pin', '0000'), datetime.now().isoformat(), datetime.now().isoformat()
        ))
        traveler_id = cursor.lastrowid
        
        # Update batch booked seats
        cursor.execute('UPDATE batches SET booked_seats = booked_seats + 1 WHERE id = ?', (data['batch_id'],))
        
        db.commit()
        db.close()
        
        return jsonify({
            'success': True,
            'traveler_id': traveler_id,
            'message': 'Traveler created successfully'
        })
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/<int:traveler_id>', methods=['PUT'])
def update_traveler(traveler_id):
    """Update traveler"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('''
            UPDATE travelers SET
                first_name = ?, last_name = ?, passport_name = ?,
                batch_id = ?, passport_no = ?, passport_issue_date = ?,
                passport_expiry_date = ?, passport_status = ?, gender = ?,
                dob = ?, mobile = ?, email = ?, aadhaar = ?, pan = ?,
                aadhaar_pan_linked = ?, vaccine_status = ?, wheelchair = ?,
                place_of_birth = ?, place_of_issue = ?, passport_address = ?,
                father_name = ?, mother_name = ?, spouse_name = ?,
                extra_fields = ?, pin = ?, updated_at = ?
            WHERE id = ?
        ''', (
            data['first_name'], data['last_name'], data.get('passport_name'),
            data.get('batch_id'), data['passport_no'], data.get('passport_issue_date'),
            data.get('passport_expiry_date'), data.get('passport_status', 'Active'),
            data.get('gender'), data.get('dob'), data['mobile'], data.get('email'),
            data.get('aadhaar'), data.get('pan'), data.get('aadhaar_pan_linked', 'No'),
            data.get('vaccine_status', 'Not Vaccinated'), data.get('wheelchair', 'No'),
            data.get('place_of_birth'), data.get('place_of_issue'),
            data.get('passport_address'), data.get('father_name'),
            data.get('mother_name'), data.get('spouse_name'),
            data.get('extra_fields', '{}'), data.get('pin', '0000'),
            datetime.now().isoformat(), traveler_id
        ))
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'message': 'Traveler updated successfully'})
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/<int:traveler_id>', methods=['DELETE'])
def delete_traveler(traveler_id):
    """Delete traveler"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM travelers WHERE id = ?', (traveler_id,))
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Traveler deleted successfully'})