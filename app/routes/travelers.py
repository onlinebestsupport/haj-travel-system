from flask import Blueprint, request, jsonify, session
from app.database import get_db, get_db_cursor
import psycopg2
import psycopg2.extras
from functools import wraps
from datetime import datetime

travelers_bp = Blueprint('travelers', __name__)

# ============ HELPER FUNCTIONS ============

def login_required(f):
    """Decorator to check if admin is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def has_permission(permission_name):
    """Check if current user has a specific permission"""
    if not session.get('admin_logged_in'):
        return False
    if 'super_admin' in session.get('admin_roles', []):
        return True
    permissions = session.get('admin_permissions', [])
    return permission_name in permissions

def permission_required(permission_name):
    """Decorator to check if user has specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not has_permission(permission_name):
                return jsonify({'success': False, 'error': 'Permission denied'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

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

def validate_traveler_data(data, is_update=False):
    """Validate traveler data before insert/update"""
    errors = []
    
    # Required fields (for create)
    if not is_update:
        required_fields = ['first_name', 'last_name', 'passport_no', 'mobile']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"{field} is required")
    
    # Passport number format (basic check)
    passport_no = data.get('passport_no')
    if passport_no and len(passport_no) < 5:
        errors.append("Passport number must be at least 5 characters")
    
    # Mobile number format
    mobile = data.get('mobile')
    if mobile and (len(mobile) < 10 or not mobile.isdigit()):
        errors.append("Mobile number must be at least 10 digits")
    
    # PIN format
    pin = data.get('pin')
    if pin and (len(pin) != 4 or not pin.isdigit()):
        errors.append("PIN must be exactly 4 digits")
    
    # Email format (if provided)
    email = data.get('email')
    if email and '@' not in email:
        errors.append("Invalid email format")
    
    # Date validations
    issue_date = data.get('passport_issue_date')
    expiry_date = data.get('passport_expiry_date')
    if issue_date and expiry_date and issue_date > expiry_date:
        errors.append("Passport expiry date must be after issue date")
    
    return errors

# ============ PUBLIC ROUTES (No Login Required) ============

@travelers_bp.route('/', methods=['GET'])
def get_all_travelers():
    """Get all travelers with their batch names - Public limited view"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # For public access, only return limited fields
        # Check if this is an admin request (with session)
        if session.get('admin_logged_in'):
            # Admin gets all fields
            cur.execute("""
                SELECT t.*, b.batch_name 
                FROM travelers t 
                LEFT JOIN batches b ON t.batch_id = b.id 
                ORDER BY t.created_at DESC
            """)
        else:
            # Public gets limited fields
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
        
        # Convert decimal to float for JSON serialization
        travelers = convert_decimal_to_float(travelers)
        
        return jsonify({
            'success': True, 
            'travelers': travelers,
            'count': len(travelers)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/<int:traveler_id>', methods=['GET'])
def get_traveler(traveler_id):
    """Get a single traveler by ID - Public limited view or full view for admin"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        if session.get('admin_logged_in'):
            # Admin gets all fields
            cur.execute("SELECT * FROM travelers WHERE id = %s", (traveler_id,))
        else:
            # Public gets limited fields
            cur.execute("""
                SELECT 
                    id, first_name, last_name, passport_no,
                    mobile, email, gender, created_at
                FROM travelers 
                WHERE id = %s
            """, (traveler_id,))
        
        traveler = cur.fetchone()
        cur.close()
        conn.close()
        
        if traveler:
            # Convert decimal to float
            traveler = convert_decimal_to_float(traveler)
            return jsonify({'success': True, 'traveler': traveler})
        else:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/passport/<passport_no>', methods=['GET'])
def get_traveler_by_passport(passport_no):
    """Get traveler by passport number - For traveler login"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # For traveler portal, we need more fields but not all admin fields
        cur.execute("""
            SELECT 
                id, first_name, last_name, passport_no, mobile, email,
                gender, dob, vaccine_status, wheelchair,
                father_name, mother_name, spouse_name,
                passport_issue_date, passport_expiry_date, passport_status,
                place_of_birth, place_of_issue, passport_address,
                aadhaar, pan, aadhaar_pan_linked,
                extra_fields, created_at
            FROM travelers 
            WHERE passport_no = %s
        """, (passport_no,))
        
        traveler = cur.fetchone()
        cur.close()
        conn.close()
        
        if traveler:
            # Convert decimal to float
            traveler = convert_decimal_to_float(traveler)
            return jsonify({'success': True, 'traveler': traveler})
        else:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ ADMIN ROUTES (Login Required) ============

@travelers_bp.route('', methods=['POST'])
@login_required
@permission_required('manage_travelers')
def create_traveler():
    """Create a new traveler with all 33 fields - Admin only"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
        data = request.json
        
        # Validate data
        errors = validate_traveler_data(data)
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
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
        }), 201
        
    except psycopg2.IntegrityError as e:
        if 'duplicate key' in str(e):
            return jsonify({'success': False, 'error': 'Duplicate entry - Passport number must be unique'}), 400
        return jsonify({'success': False, 'error': 'Database integrity error'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/<int:traveler_id>', methods=['PUT'])
@login_required
@permission_required('manage_travelers')
def update_traveler(traveler_id):
    """Update an existing traveler with all 33 fields - Admin only"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400

        data = request.json
        
        # Validate data (for update, only validate provided fields)
        errors = validate_traveler_data(data, is_update=True)
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
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
        if not old_batch:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
            
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
                updated_at = CURRENT_TIMESTAMP,
                updated_by = %s
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
            data.get('pin', '0000'), session.get('admin_user_id'),
            traveler_id
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
        if 'duplicate key' in str(e):
            return jsonify({'success': False, 'error': 'Duplicate entry - Passport number must be unique'}), 400
        return jsonify({'success': False, 'error': 'Database integrity error'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/<int:traveler_id>', methods=['DELETE'])
@login_required
@permission_required('manage_travelers')
def delete_traveler(traveler_id):
    """Delete a traveler - Admin only"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor()
        
        # Get batch_id before deleting
        cur.execute("SELECT batch_id FROM travelers WHERE id = %s", (traveler_id,))
        result = cur.fetchone()
        
        if not result:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
            
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

# ============ ADMIN ROUTES - STATS AND SEARCH ============

@travelers_bp.route('/stats/summary', methods=['GET'])
def get_traveler_stats():
    """Get traveler statistics summary - Admin only"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor()
        
        # Total travelers
        cur.execute("SELECT COUNT(*) FROM travelers")
        total = cur.fetchone()[0]
        
        # Travelers added today
        cur.execute("""
            SELECT COUNT(*) FROM travelers 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        today = cur.fetchone()[0]
        
        # Travelers by status
        cur.execute("""
            SELECT passport_status, COUNT(*) 
            FROM travelers 
            GROUP BY passport_status
        """)
        status_counts = {}
        for row in cur.fetchall():
            status_counts[row[0]] = row[1]
        
        # Travelers by batch
        cur.execute("""
            SELECT b.batch_name, COUNT(t.id) 
            FROM batches b
            LEFT JOIN travelers t ON b.id = t.batch_id
            GROUP BY b.id, b.batch_name
            ORDER BY COUNT(t.id) DESC
            LIMIT 5
        """)
        batch_counts = []
        for row in cur.fetchall():
            batch_counts.append({
                'batch_name': row[0],
                'count': row[1]
            })
        
        # Active batches
        cur.execute("""
            SELECT COUNT(*) FROM batches 
            WHERE status IN ('Open', 'Closing Soon')
        """)
        active_batches = cur.fetchone()[0]
        
        # Recent travelers (last 10)
        cur.execute("""
            SELECT 
                t.id, t.first_name, t.last_name, 
                t.passport_no, t.created_at, 
                b.batch_name
            FROM travelers t
            LEFT JOIN batches b ON t.batch_id = b.id
            ORDER BY t.created_at DESC
            LIMIT 10
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
                'batchCounts': batch_counts,
                'recentTravelers': recent
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/search', methods=['GET'])
@login_required
def search_travelers():
    """Search travelers by name, passport, or mobile - Admin only"""
    try:
        query = request.args.get('q', '')
        if len(query) < 2:
            return jsonify({'success': True, 'travelers': []})
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Search in multiple fields with better ranking
        cur.execute("""
            SELECT 
                t.*, b.batch_name,
                CASE 
                    WHEN t.passport_no ILIKE %s THEN 3
                    WHEN t.mobile ILIKE %s THEN 2
                    WHEN t.first_name ILIKE %s OR t.last_name ILIKE %s OR t.email ILIKE %s THEN 1
                    ELSE 0
                END as relevance
            FROM travelers t
            LEFT JOIN batches b ON t.batch_id = b.id
            WHERE 
                t.first_name ILIKE %s OR
                t.last_name ILIKE %s OR
                t.passport_no ILIKE %s OR
                t.mobile ILIKE %s OR
                t.email ILIKE %s
            ORDER BY relevance DESC, t.created_at DESC
            LIMIT 30
        """, (
            f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%',
            f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'
        ))
        
        travelers = cur.fetchall()
        cur.close()
        conn.close()
        
        # Remove relevance field from output
        for traveler in travelers:
            if 'relevance' in traveler:
                del traveler['relevance']
        
        # Convert decimal to float
        travelers = convert_decimal_to_float(travelers)
        
        return jsonify({'success': True, 'travelers': travelers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/batch/<int:batch_id>', methods=['GET'])
@login_required
def get_travelers_by_batch(batch_id):
    """Get all travelers in a specific batch - Admin only"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
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
        travelers = convert_decimal_to_float(travelers)
        
        return jsonify({'success': True, 'travelers': travelers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/export', methods=['GET'])
@login_required
@permission_required('export_data')
def export_travelers():
    """Export all travelers data (for admin use) - Admin only"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get all fields for export
        cur.execute("""
            SELECT 
                t.id, t.first_name, t.last_name, t.passport_no,
                t.mobile, t.email, t.gender, 
                TO_CHAR(t.dob, 'YYYY-MM-DD') as dob,
                t.vaccine_status, t.wheelchair,
                t.father_name, t.mother_name, t.spouse_name,
                t.passport_status, t.pin,
                t.place_of_birth, t.place_of_issue, t.passport_address,
                t.aadhaar, t.pan, t.aadhaar_pan_linked,
                t.passport_issue_date, t.passport_expiry_date,
                b.batch_name, b.departure_date, b.return_date,
                TO_CHAR(t.created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                TO_CHAR(t.updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at
            FROM travelers t
            LEFT JOIN batches b ON t.batch_id = b.id
            ORDER BY t.created_at DESC
        """)
        
        travelers = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'travelers': travelers,
            'count': len(travelers),
            'exported_at': datetime.now().isoformat(),
            'exported_by': session.get('admin_username')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
# ============ TRAVELER LOGIN ENDPOINT ============

@travelers_bp.route('/login', methods=['POST'])
def traveler_login():
    """Handle traveler login with passport number and PIN"""
    try:
        data = request.json
        passport_no = data.get('passport_no')
        pin = data.get('pin')
        
        if not passport_no or not pin:
            return jsonify({'success': False, 'message': 'Passport number and PIN required'}), 400
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Check if traveler exists with this passport and PIN
        cur.execute("""
            SELECT id, first_name, last_name, passport_no, mobile, email
            FROM travelers 
            WHERE passport_no = %s AND pin = %s
        """, (passport_no, pin))
        
        traveler = cur.fetchone()
        cur.close()
        conn.close()
        
        if traveler:
            # Store traveler info in session
            session['traveler_id'] = traveler['id']
            session['traveler_name'] = f"{traveler['first_name']} {traveler['last_name']}"
            session['traveler_passport'] = traveler['passport_no']
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'traveler_id': traveler['id'],
                'name': f"{traveler['first_name']} {traveler['last_name']}",
                'redirect': '/traveler_dashboard.html'
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid passport number or PIN'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/logout', methods=['POST'])
def traveler_logout():
    """Handle traveler logout"""
    session.pop('traveler_id', None)
    session.pop('traveler_name', None)
    session.pop('traveler_passport', None)
    return jsonify({'success': True, 'message': 'Logged out successfully'})
# ============ BULK OPERATIONS ============

@travelers_bp.route('/bulk/status', methods=['POST'])
@login_required
@permission_required('manage_travelers')
def bulk_update_status():
    """Update status for multiple travelers at once"""
    try:
        data = request.json
        traveler_ids = data.get('traveler_ids', [])
        new_status = data.get('status')
        
        if not traveler_ids or not new_status:
            return jsonify({'success': False, 'error': 'Traveler IDs and status are required'}), 400
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE travelers 
            SET passport_status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = ANY(%s)
        """, (new_status, traveler_ids))
        
        updated_count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'Updated {updated_count} travelers',
            'updated': updated_count
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/bulk/delete', methods=['POST'])
@login_required
@permission_required('manage_travelers')
def bulk_delete():
    """Delete multiple travelers at once"""
    try:
        data = request.json
        traveler_ids = data.get('traveler_ids', [])
        
        if not traveler_ids:
            return jsonify({'success': False, 'error': 'No traveler IDs provided'}), 400
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor()
        
        # Get batch IDs before deleting to update seat counts
        cur.execute("""
            SELECT batch_id, COUNT(*) 
            FROM travelers 
            WHERE id = ANY(%s) AND batch_id IS NOT NULL
            GROUP BY batch_id
        """, (traveler_ids,))
        
        batch_updates = cur.fetchall()
        
        # Delete travelers
        cur.execute("DELETE FROM travelers WHERE id = ANY(%s)", (traveler_ids,))
        deleted_count = cur.rowcount
        
        # Update batch seat counts
        for batch_id, count in batch_updates:
            cur.execute("""
                UPDATE batches 
                SET booked_seats = booked_seats - %s 
                WHERE id = %s AND booked_seats >= %s
            """, (count, batch_id, count))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'Deleted {deleted_count} travelers',
            'deleted': deleted_count
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
