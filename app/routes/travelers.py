from flask import Blueprint, request, jsonify
from app.database import get_db
import json
import psycopg2
import psycopg2.extras

travelers_bp = Blueprint('travelers', __name__)

@travelers_bp.route('/', methods=['GET'])
def get_all_travelers():
    """Get all travelers with their batch names"""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("""
            SELECT t.*, b.batch_name 
            FROM travelers t 
            LEFT JOIN batches b ON t.batch_id = b.id 
            ORDER BY t.created_at DESC
        """)
        
        travelers = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'travelers': travelers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/<int:traveler_id>', methods=['GET'])
def get_traveler(traveler_id):
    """Get a single traveler by ID"""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("SELECT * FROM travelers WHERE id = %s", (traveler_id,))
        traveler = cur.fetchone()
        cur.close()
        conn.close()
        
        if traveler:
            return jsonify({'success': True, 'traveler': traveler})
        else:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/', methods=['POST'])
def create_traveler():
    """Create a new traveler"""
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        
        # Handle extra_fields JSON
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
                extra_fields, pin
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s::jsonb, %s
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
            data.get('pin', '0000')
        ))
        
        traveler_id = cur.fetchone()[0]
        
        # Update booked seats in batch
        if data.get('batch_id'):
            cur.execute("""
                UPDATE batches 
                SET booked_seats = booked_seats + 1 
                WHERE id = %s
            """, (data.get('batch_id'),))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'traveler_id': traveler_id, 'message': 'Traveler created successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/<int:traveler_id>', methods=['PUT'])
def update_traveler(traveler_id):
    """Update an existing traveler"""
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        
        # Handle extra_fields JSON
        extra_fields = data.get('extra_fields', '{}')
        if isinstance(extra_fields, dict):
            extra_fields = json.dumps(extra_fields)
        
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
                passport_scan = %s, aadhaar_scan = %s,
                pan_scan = %s, vaccine_scan = %s,
                extra_fields = %s::jsonb, pin = %s,
                updated_at = CURRENT_TIMESTAMP
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
            data.get('spouse_name'), data.get('passport_scan'), data.get('aadhaar_scan'),
            data.get('pan_scan'), data.get('vaccine_scan'), extra_fields,
            data.get('pin', '0000'), traveler_id
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Traveler updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/<int:traveler_id>', methods=['DELETE'])
def delete_traveler(traveler_id):
    """Delete a traveler"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Get batch_id before deleting
        cur.execute("SELECT batch_id FROM travelers WHERE id = %s", (traveler_id,))
        result = cur.fetchone()
        batch_id = result[0] if result else None
        
        # Delete traveler
        cur.execute("DELETE FROM travelers WHERE id = %s", (traveler_id,))
        
        # Update batch seats if needed
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

@travelers_bp.route('/passport/<passport_no>', methods=['GET'])
def get_traveler_by_passport(passport_no):
    """Get traveler by passport number"""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("SELECT * FROM travelers WHERE passport_no = %s", (passport_no,))
        traveler = cur.fetchone()
        cur.close()
        conn.close()
        
        if traveler:
            return jsonify({'success': True, 'traveler': traveler})
        else:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/stats/summary', methods=['GET'])
def get_traveler_stats():
    """Get traveler statistics summary"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM travelers")
        total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM travelers WHERE DATE(created_at) = CURRENT_DATE")
        today = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM batches WHERE status IN ('Open', 'Closing Soon')")
        active_batches = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'totalTravelers': total,
                'todayRegistrations': today,
                'openBatches': active_batches
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
