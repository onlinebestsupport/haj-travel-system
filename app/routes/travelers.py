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
        
        # Convert decimal to float for JSON serialization
        for traveler in travelers:
            for key, value in traveler.items():
                if hasattr(value, 'scale'):
                    traveler[key] = float(value)
        
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
            # Convert decimal to float
            for key, value in traveler.items():
                if hasattr(value, 'scale'):
                    traveler[key] = float(value)
            return jsonify({'success': True, 'traveler': traveler})
        else:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/', methods=['POST'])
def create_traveler():
    """Create a new traveler with all 33 fields"""
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        
        # Handle extra_fields JSON
        extra_fields = data.get('extra_fields', '{}')
        if isinstance(extra_fields, dict):
            extra_fields = json.dumps(extra_fields)
        
        # Insert traveler with all 33 fields
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
        
        return jsonify({
            'success': True, 
            'traveler_id': traveler_id, 
            'message': 'Traveler created successfully with 33 fields'
        })
    except psycopg2.IntegrityError as e:
        return jsonify({'success': False, 'error': 'Duplicate entry - Passport number must be unique'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/<int:traveler_id>', methods=['PUT'])
def update_traveler(traveler_id):
    """Update an existing traveler with all 33 fields"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400

        data = request.json
        conn = get_db()
        cur = conn.cursor()

        # Handle extra_fields JSON
        extra_fields_data = data.get('extra_fields', '{}')
        if isinstance(extra_fields_data, str):
            try:
                # Validate JSON
                parsed_extra = json.loads(extra_fields_data)
                extra_fields_json = json.dumps(parsed_extra)
            except json.JSONDecodeError:
                extra_fields_json = '{}'
        else:
            extra_fields_json = json.dumps(extra_fields_data)

        # Get current batch_id to check if it changed
        cur.execute("SELECT batch_id FROM travelers WHERE id = %s", (traveler_id,))
        old_batch = cur.fetchone()
        old_batch_id = old_batch[0] if old_batch else None
        new_batch_id = data.get('batch_id')

        # Update traveler with all 33 fields
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
            data.get('first_name'), data.get('last_name'), new_batch_id,
            data.get('passport_no'), data.get('passport_issue_date'),
            data.get('passport_expiry_date'), data.get('passport_status', 'Active'),
            data.get('gender'), data.get('dob'), data.get('mobile'),
            data.get('email'), data.get('aadhaar'), data.get('pan'),
            data.get('aadhaar_pan_linked', 'No'), data.get('vaccine_status', 'Not Vaccinated'),
            data.get('wheelchair', 'No'), data.get('place_of_birth'), data.get('place_of_issue'),
            data.get('passport_address'), data.get('father_name'), data.get('mother_name'),
            data.get('spouse_name'), data.get('passport_scan'), data.get('aadhaar_scan'),
            data.get('pan_scan'), data.get('vaccine_scan'), extra_fields_json,
            data.get('pin', '0000'), traveler_id
        ))

        # Update batch seat counts if batch changed
        if old_batch_id != new_batch_id:
            if old_batch_id:
                cur.execute("UPDATE batches SET booked_seats = booked_seats - 1 WHERE id = %s", (old_batch_id,))
            if new_batch_id:
                cur.execute("UPDATE batches SET booked_seats = booked_seats + 1 WHERE id = %s", (new_batch_id,))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Traveler updated successfully with 33 fields'})
    except psycopg2.IntegrityError as e:
        return jsonify({'success': False, 'error': 'Duplicate entry - Passport number must be unique'}), 400
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
            # Convert decimal to float
            for key, value in traveler.items():
                if hasattr(value, 'scale'):
                    traveler[key] = float(value)
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
        
        # Total travelers
        cur.execute("SELECT COUNT(*) FROM travelers")
        total = cur.fetchone()[0]
        
        # Travelers added today
        cur.execute("SELECT COUNT(*) FROM travelers WHERE DATE(created_at) = CURRENT_DATE")
        today = cur.fetchone()[0]
        
        # Travelers by status
        cur.execute("SELECT passport_status, COUNT(*) FROM travelers GROUP BY passport_status")
        status_counts = {}
        for row in cur.fetchall():
            status_counts[row[0]] = row[1]
        
        # Active batches
        cur.execute("SELECT COUNT(*) FROM batches WHERE status IN ('Open', 'Closing Soon')")
        active_batches = cur.fetchone()[0]
        
        # Recent travelers (last 5)
        cur.execute("""
            SELECT t.id, t.first_name, t.last_name, t.passport_no, t.created_at, b.batch_name
            FROM travelers t
            LEFT JOIN batches b ON t.batch_id = b.id
            ORDER BY t.created_at DESC
            LIMIT 5
        """)
        
        recent = []
        for row in cur.fetchall():
            recent.append({
                'id': row[0],
                'name': f"{row[1]} {row[2]}",
                'passport': row[3],
                'created_at': row[4].isoformat() if row[4] else None,
                'batch': row[5]
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'totalTravelers': total,
                'todayRegistrations': today,
                'openBatches': active_batches,
                'statusCounts': status_counts,
                'recentTravelers': recent
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/search', methods=['GET'])
def search_travelers():
    """Search travelers by name, passport, or mobile"""
    try:
        query = request.args.get('q', '')
        if len(query) < 2:
            return jsonify({'success': True, 'travelers': []})
        
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Search in multiple fields
        cur.execute("""
            SELECT t.*, b.batch_name 
            FROM travelers t
            LEFT JOIN batches b ON t.batch_id = b.id
            WHERE 
                t.first_name ILIKE %s OR
                t.last_name ILIKE %s OR
                t.passport_no ILIKE %s OR
                t.mobile ILIKE %s OR
                t.email ILIKE %s
            ORDER BY t.created_at DESC
            LIMIT 20
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        
        travelers = cur.fetchall()
        cur.close()
        conn.close()
        
        # Convert decimal to float
        for traveler in travelers:
            for key, value in traveler.items():
                if hasattr(value, 'scale'):
                    traveler[key] = float(value)
        
        return jsonify({'success': True, 'travelers': travelers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/batch/<int:batch_id>', methods=['GET'])
def get_travelers_by_batch(batch_id):
    """Get all travelers in a specific batch"""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("""
            SELECT t.*, b.batch_name 
            FROM travelers t
            JOIN batches b ON t.batch_id = b.id
            WHERE t.batch_id = %s
            ORDER BY t.last_name, t.first_name
        """, (batch_id,))
        
        travelers = cur.fetchall()
        cur.close()
        conn.close()
        
        # Convert decimal to float
        for traveler in travelers:
            for key, value in traveler.items():
                if hasattr(value, 'scale'):
                    traveler[key] = float(value)
        
        return jsonify({'success': True, 'travelers': travelers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/export', methods=['GET'])
def export_travelers():
    """Export all travelers data (for admin use)"""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("""
            SELECT 
                t.id, t.first_name, t.last_name, t.passport_no,
                t.mobile, t.email, t.gender, t.dob,
                t.vaccine_status, t.wheelchair,
                t.father_name, t.mother_name, t.spouse_name,
                t.passport_status, t.pin,
                b.batch_name, b.departure_date, b.return_date,
                t.created_at, t.updated_at
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
