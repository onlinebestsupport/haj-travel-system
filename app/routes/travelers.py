from flask import Blueprint, request, jsonify, session
from app.database import get_db, get_db_cursor
import psycopg2
import psycopg2.extras
from functools import wraps
from datetime import datetime
import json

travelers_bp = Blueprint('travelers', __name__)

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

@travelers_bp.route('/', methods=['GET'])
def get_all_travelers():
    try:
        conn, cur = get_db_cursor(dictionary=True)
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        if session.get('admin_logged_in'):
            cur.execute("""
                SELECT t.*, b.batch_name 
                FROM travelers t 
                LEFT JOIN batches b ON t.batch_id = b.id 
                ORDER BY t.created_at DESC
            """)
        else:
            cur.execute("""
                SELECT 
                    t.id, t.first_name, t.last_name, t.passport_no,
                    t.mobile, t.created_at,
                    b.batch_name 
                FROM travelers t 
                LEFT JOIN batches b ON t.batch_id = b.id 
                ORDER BY t.created_at DESC
                LIMIT 50
            """)
        
        travelers = cur.fetchall()
        cur.close()
        conn.close()
        
        travelers = convert_decimal_to_float(travelers)
        
        return jsonify({'success': True, 'travelers': travelers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/<int:traveler_id>', methods=['GET'])
def get_traveler(traveler_id):
    try:
        conn, cur = get_db_cursor(dictionary=True)
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur.execute("SELECT * FROM travelers WHERE id = %s", (traveler_id,))
        traveler = cur.fetchone()
        cur.close()
        conn.close()
        
        if traveler:
            traveler = convert_decimal_to_float(traveler)
            return jsonify({'success': True, 'traveler': traveler})
        return jsonify({'success': False, 'error': 'Traveler not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/passport/<passport_no>', methods=['GET'])
def get_traveler_by_passport(passport_no):
    try:
        conn, cur = get_db_cursor(dictionary=True)
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur.execute("""
            SELECT * FROM travelers 
            WHERE passport_no = %s
        """, (passport_no,))
        
        traveler = cur.fetchone()
        cur.close()
        conn.close()
        
        if traveler:
            traveler = convert_decimal_to_float(traveler)
            return jsonify({'success': True, 'traveler': traveler})
        return jsonify({'success': False, 'error': 'Traveler not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/', methods=['POST'])
@login_required
def create_traveler():
    try:
        data = request.json
        required_fields = ['first_name', 'last_name', 'passport_no', 'mobile']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        conn, cur = get_db_cursor()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        extra_fields = data.get('extra_fields', '{}')
        if isinstance(extra_fields, dict):
            extra_fields = json.dumps(extra_fields)
        
        cur.execute("""
            INSERT INTO travelers (
                first_name, last_name, batch_id, passport_no,
                passport_issue_date, passport_expiry_date, passport_status,
                gender, dob, mobile, email, aadhaar, pan,
                aadhaar_pan_linked, vaccine_status, wheelchair,
                place_of_birth, place_of_issue, passport_address,
                father_name, mother_name, spouse_name,
                passport_scan, aadhaar_scan, pan_scan, vaccine_scan,
                extra_fields, pin, created_by
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s::jsonb, %s, %s
            ) RETURNING id
        """, (
            data.get('first_name'), data.get('last_name'), data.get('batch_id'),
            data.get('passport_no'), data.get('passport_issue_date'),
            data.get('passport_expiry_date'), data.get('passport_status', 'Active'),
            data.get('gender'), data.get('dob'), data.get('mobile'),
            data.get('email'), data.get('aadhaar'), data.get('pan'),
            data.get('aadhaar_pan_linked', 'No'), data.get('vaccine_status', 'Not Vaccinated'),
            data.get('wheelchair', 'No'), data.get('place_of_birth'), data.get('place_of_issue'),
            data.get('passport_address'), data.get('father_name'), data.get('mother_name'),
            data.get('spouse_name'), data.get('passport_scan'), data.get('aadhaar_scan'),
            data.get('pan_scan'), data.get('vaccine_scan'), extra_fields,
            data.get('pin', '0000'), session.get('admin_user_id')
        ))
        
        traveler_id = cur.fetchone()[0]
        
        if data.get('batch_id'):
            cur.execute("""
                UPDATE batches 
                SET booked_seats = booked_seats + 1 
                WHERE id = %s
            """, (data.get('batch_id'),))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'traveler_id': traveler_id, 
            'message': 'Traveler created successfully'
        }), 201
        
    except psycopg2.IntegrityError as e:
        if 'duplicate key' in str(e):
            return jsonify({'success': False, 'error': 'Duplicate passport number'}), 400
        return jsonify({'success': False, 'error': 'Database integrity error'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/<int:traveler_id>', methods=['PUT'])
@login_required
def update_traveler(traveler_id):
    try:
        data = request.json
        conn, cur = get_db_cursor()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        extra_fields_data = data.get('extra_fields', '{}')
        if isinstance(extra_fields_data, str):
            try:
                parsed_extra = json.loads(extra_fields_data)
                extra_fields_json = json.dumps(parsed_extra)
            except json.JSONDecodeError:
                extra_fields_json = '{}'
        else:
            extra_fields_json = json.dumps(extra_fields_data)
        
        cur.execute("""
            UPDATE travelers SET
                first_name = %s, last_name = %s, batch_id = %s,
                passport_no = %s, passport_issue_date = %s,
                passport_expiry_date = %s, passport_status = %s,
                gender = %s, dob = %s, mobile = %s, email = %s,
                aadhaar = %s, pan = %s, aadhaar_pan_linked = %s,
                vaccine_status = %s, wheelchair = %s,
                place_of_birth = %s, place_of_issue = %s,
                passport_address = %s, father_name = %s,
                mother_name = %s, spouse_name = %s,
                extra_fields = %s::jsonb, pin = %s,
                updated_at = CURRENT_TIMESTAMP,
                updated_by = %s
            WHERE id = %s
        """, (
            data.get('first_name'), data.get('last_name'), data.get('batch_id'),
            data.get('passport_no'), data.get('passport_issue_date'),
            data.get('passport_expiry_date'), data.get('passport_status', 'Active'),
            data.get('gender'), data.get('dob'), data.get('mobile'),
            data.get('email'), data.get('aadhaar'), data.get('pan'),
            data.get('aadhaar_pan_linked', 'No'), data.get('vaccine_status', 'Not Vaccinated'),
            data.get('wheelchair', 'No'), data.get('place_of_birth'), data.get('place_of_issue'),
            data.get('passport_address'), data.get('father_name'), data.get('mother_name'),
            data.get('spouse_name'), extra_fields_json,
            data.get('pin', '0000'), session.get('admin_user_id'),
            traveler_id
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Traveler updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/<int:traveler_id>', methods=['DELETE'])
@login_required
def delete_traveler(traveler_id):
    try:
        conn, cur = get_db_cursor()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur.execute("SELECT batch_id FROM travelers WHERE id = %s", (traveler_id,))
        result = cur.fetchone()
        
        if not result:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
            
        batch_id = result[0] if result else None
        
        cur.execute("DELETE FROM travelers WHERE id = %s", (traveler_id,))
        
        if batch_id:
            cur.execute("""
                UPDATE batches 
                SET booked_seats = booked_seats - 1 
                WHERE id = %s AND booked_seats > 0
            """, (batch_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Traveler deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/login', methods=['POST'])
def traveler_login():
    try:
        data = request.json
        passport_no = data.get('passport_no')
        pin = data.get('pin')
        
        if not passport_no or not pin:
            return jsonify({'success': False, 'message': 'Passport and PIN required'}), 400
        
        conn, cur = get_db_cursor(dictionary=True)
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur.execute("""
            SELECT id, first_name, last_name, passport_no, mobile, email
            FROM travelers 
            WHERE passport_no = %s AND pin = %s
        """, (passport_no, pin))
        
        traveler = cur.fetchone()
        cur.close()
        conn.close()
        
        if traveler:
            session['traveler_id'] = traveler['id']
            session['traveler_name'] = f"{traveler['first_name']} {traveler['last_name']}"
            session['traveler_passport'] = traveler['passport_no']
            
            return jsonify({
                'success': True,
                'traveler_id': traveler['id'],
                'name': f"{traveler['first_name']} {traveler['last_name']}",
                'redirect': '/traveler_dashboard.html'
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/logout', methods=['POST'])
def traveler_logout():
    session.pop('traveler_id', None)
    session.pop('traveler_name', None)
    session.pop('traveler_passport', None)
    return jsonify({'success': True, 'message': 'Logged out'})
