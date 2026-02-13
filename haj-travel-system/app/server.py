from flask import Flask, send_from_directory, jsonify, request, redirect, url_for, session
from flask_cors import CORS
from app.database import init_db, get_db
import os
from functools import wraps

app = Flask(__name__)
CORS(app)

# Secret key for sessions - CHANGE THIS IN PRODUCTION!
app.secret_key = 'alhudha-haj-secret-key-2026'

# Public folder path - USING 'public' as per your GitHub
PUBLIC_DIR = '/app/public'

print(f"📁 Public folder: {PUBLIC_DIR}")
print(f"📁 Files: {os.listdir(PUBLIC_DIR) if os.path.exists(PUBLIC_DIR) else 'NOT FOUND'}")

# ============ ROLE-BASED ACCESS CONTROL ============

def has_permission(permission_name):
    """Check if logged-in user has specific permission"""
    if not session.get('admin_logged_in'):
        return False
    
    user_id = session.get('admin_user_id')
    if not user_id:
        return False
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Check if user has this permission through their roles
        cur.execute("""
            SELECT COUNT(*) FROM user_roles ur
            JOIN role_permissions rp ON ur.role_id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE ur.user_id = %s AND p.name = %s
        """, (user_id, permission_name))
        
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        return count > 0
    except Exception as e:
        print(f"Permission check error: {e}")
        return False

def permission_required(permission_name):
    """Decorator for route permission checking"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not has_permission(permission_name):
                return jsonify({'error': 'Permission denied'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============ LOGIN DECORATOR ============

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# ============ LOGIN ROUTES ============

@app.route('/login')
def login_page():
    """Serve the login page"""
    return send_from_directory(PUBLIC_DIR, 'login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for login"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Check admin_users table
        cur.execute("""
            SELECT id, username, password_hash, full_name 
            FROM admin_users 
            WHERE username = %s AND is_active = true
        """, (username,))
        
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        # In production, use proper password hashing!
        if user and password == 'admin123':  # Temporary - use hash in production
            session['admin_logged_in'] = True
            session['admin_user_id'] = user[0]
            session['admin_username'] = user[1]
            session['admin_name'] = user[3]
            
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """API endpoint for logout"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logout successful'})

# ============ PROTECTED ADMIN ROUTES ============

@app.route('/admin')
@login_required
def serve_admin():
    """Protected admin panel - requires login"""
    return send_from_directory(PUBLIC_DIR, 'admin.html')

@app.route('/admin/dashboard')
@login_required
def serve_admin_dashboard():
    """Redirect to main admin page"""
    return send_from_directory(PUBLIC_DIR, 'admin.html')

# ============ PUBLIC ROUTES ============

@app.route('/')
def serve_index():
    """Public main page - shows packages"""
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/traveler-login')
def traveler_login_page():
    """Serve traveler login page"""
    return send_from_directory(PUBLIC_DIR, 'traveler_login.html')

@app.route('/traveler/dashboard')
def traveler_dashboard():
    """Serve traveler dashboard"""
    return send_from_directory(PUBLIC_DIR, 'traveler_dashboard.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files - skip login for CSS, JS, images"""
    if path.endswith('.css') or path.endswith('.js') or path.endswith('.png') or path.endswith('.jpg') or path.endswith('.svg'):
        return send_from_directory(PUBLIC_DIR, path)
    return send_from_directory(PUBLIC_DIR, path)

# ============ API ROUTES ============

@app.route('/api')
def api():
    """Public API status"""
    return jsonify({
        "name": "Haj Travel System",
        "status": "active",
        "fields": 33,
        "message": "API is working!"
    })

@app.route('/api/health')
def health():
    """Healthcheck endpoint"""
    return jsonify({"status": "healthy"}), 200

# ============ BATCH ROUTES ============

@app.route('/api/batches', methods=['GET'])
def get_batches():
    """Get all batches - public"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, batch_name, departure_date, return_date, 
                   total_seats, booked_seats, status, price, description 
            FROM batches 
            ORDER BY departure_date
        """)
        
        batches = []
        for row in cur.fetchall():
            batches.append({
                'id': row[0],
                'batch_name': row[1],
                'departure_date': row[2],
                'return_date': row[3],
                'total_seats': row[4],
                'booked_seats': row[5],
                'status': row[6],
                'price': row[7],
                'description': row[8]
            })
        
        cur.close()
        conn.close()
        return jsonify({'success': True, 'batches': batches})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/batches', methods=['POST'])
@login_required
@permission_required('create_batch')
def create_batch():
    """Create new batch - requires create_batch permission"""
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO batches (batch_name, departure_date, return_date, total_seats, status, price, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get('batch_name'),
            data.get('departure_date'),
            data.get('return_date'),
            data.get('total_seats', 150),
            data.get('status', 'Open'),
            data.get('price'),
            data.get('description')
        ))
        
        batch_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Batch created', 'batch_id': batch_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ TRAVELER ROUTES ============

@app.route('/api/travelers', methods=['POST'])
@login_required
@permission_required('create_traveler')
def create_traveler():
    """Create new traveler - requires create_traveler permission"""
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        
        # Verify batch exists
        cur.execute("SELECT id, batch_name FROM batches WHERE id = %s", (data.get('batch_id'),))
        batch = cur.fetchone()
        if not batch:
            return jsonify({'success': False, 'error': 'Batch not found'}), 400
        
        # Insert traveler with PIN
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
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get('first_name'),
            data.get('last_name'),
            data.get('batch_id'),
            data.get('passport_no'),
            data.get('passport_issue_date'),
            data.get('passport_expiry_date'),
            data.get('passport_status', 'Active'),
            data.get('gender'),
            data.get('dob'),
            data.get('mobile'),
            data.get('email'),
            data.get('aadhaar'),
            data.get('pan'),
            data.get('aadhaar_pan_linked', 'No'),
            data.get('vaccine_status', 'Not Vaccinated'),
            data.get('wheelchair', 'No'),
            data.get('place_of_birth'),
            data.get('place_of_issue'),
            data.get('passport_address'),
            data.get('father_name'),
            data.get('mother_name'),
            data.get('spouse_name'),
            data.get('passport_scan'),
            data.get('aadhaar_scan'),
            data.get('pan_scan'),
            data.get('vaccine_scan'),
            data.get('extra_fields', '{}'),
            data.get('pin', '0000')  # Default PIN
        ))
        
        traveler_id = cur.fetchone()[0]
        
        # Update booked seats in batch
        cur.execute("""
            UPDATE batches 
            SET booked_seats = booked_seats + 1 
            WHERE id = %s
        """, (data.get('batch_id'),))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Traveler created', 'traveler_id': traveler_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/travelers', methods=['GET'])
@login_required
@permission_required('view_travelers')
def get_travelers():
    """Get all travelers - requires view_travelers permission"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT t.*, b.batch_name 
            FROM travelers t 
            LEFT JOIN batches b ON t.batch_id = b.id 
            ORDER BY t.created_at DESC
        """)
        
        travelers = []
        for row in cur.fetchall():
            travelers.append({
                'id': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'passport_name': row[3],
                'batch_id': row[4],
                'passport_no': row[5],
                'passport_issue_date': row[6],
                'passport_expiry_date': row[7],
                'passport_status': row[8],
                'gender': row[9],
                'dob': row[10],
                'mobile': row[11],
                'email': row[12],
                'aadhaar': row[13],
                'pan': row[14],
                'aadhaar_pan_linked': row[15],
                'vaccine_status': row[16],
                'wheelchair': row[17],
                'place_of_birth': row[18],
                'place_of_issue': row[19],
                'passport_address': row[20],
                'father_name': row[21],
                'mother_name': row[22],
                'spouse_name': row[23],
                'passport_scan': row[24],
                'aadhaar_scan': row[25],
                'pan_scan': row[26],
                'vaccine_scan': row[27],
                'extra_fields': row[28],
                'pin': row[29],
                'created_at': row[30],
                'updated_at': row[31],
                'batch_name': row[32] if len(row) > 32 else None
            })
        
        cur.close()
        conn.close()
        return jsonify({'success': True, 'travelers': travelers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ PAYMENT ROUTES ============

@app.route('/api/payments/verify/<int:traveler_id>', methods=['GET'])
@login_required
def verify_traveler_for_payment(traveler_id):
    """Get traveler and batch details for payment form"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT t.id, t.first_name, t.last_name, t.passport_no, 
                   b.id as batch_id, b.batch_name, b.departure_date, b.return_date,
                   b.price as batch_price
            FROM travelers t
            LEFT JOIN batches b ON t.batch_id = b.id
            WHERE t.id = %s
        """, (traveler_id,))
        
        traveler = cur.fetchone()
        cur.close()
        conn.close()
        
        if not traveler:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
        
        return jsonify({
            'success': True,
            'traveler': {
                'id': traveler[0],
                'name': f"{traveler[1]} {traveler[2]}",
                'passport': traveler[3]
            },
            'batch': {
                'id': traveler[4],
                'name': traveler[5],
                'departure': traveler[6],
                'return': traveler[7],
                'price': traveler[8]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/payments', methods=['POST'])
@login_required
@permission_required('create_payment')
def create_payment():
    """Create new payment - shows batch and traveler details for verification"""
    try:
        data = request.json
        traveler_id = data.get('traveler_id')
        
        conn = get_db()
        cur = conn.cursor()
        
        # Get traveler and batch details for verification
        cur.execute("""
            SELECT t.id, t.first_name, t.last_name, t.passport_no, 
                   b.id as batch_id, b.batch_name, b.departure_date, b.return_date,
                   b.price as batch_price
            FROM travelers t
            LEFT JOIN batches b ON t.batch_id = b.id
            WHERE t.id = %s
        """, (traveler_id,))
        
        traveler = cur.fetchone()
        if not traveler:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
        
        # Insert payment
        cur.execute("""
            INSERT INTO payments (traveler_id, installment, amount, due_date, status, payment_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            traveler_id,
            data.get('installment'),
            data.get('amount'),
            data.get('due_date'),
            data.get('status', 'Pending'),
            data.get('payment_date')
        ))
        
        payment_id = cur.fetchone()[0]
        conn.commit()
        
        # Get payment details
        cur.execute("SELECT * FROM payments WHERE id = %s", (payment_id,))
        payment_row = cur.fetchone()
        
        cur.close()
        conn.close()
        
        payment = {
            'id': payment_row[0],
            'installment': payment_row[2],
            'amount': payment_row[3],
            'due_date': payment_row[4],
            'status': payment_row[5],
            'payment_date': payment_row[6]
        }
        
        return jsonify({
            'success': True, 
            'message': 'Payment recorded',
            'payment': payment,
            'verification': {
                'traveler': {
                    'id': traveler[0],
                    'name': f"{traveler[1]} {traveler[2]}",
                    'passport': traveler[3]
                },
                'batch': {
                    'id': traveler[4],
                    'name': traveler[5],
                    'departure': traveler[6],
                    'return': traveler[7],
                    'price': traveler[8]
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ STATISTICS ROUTE ============

@app.route('/api/travelers/stats/summary', methods=['GET'])
@login_required
def get_stats_summary():
    """Get statistics for dashboard"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM travelers")
        total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM travelers WHERE passport_status = 'Active'")
        active = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM batches WHERE status = 'Open'")
        open_batches = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM travelers WHERE created_at::date = CURRENT_DATE")
        today = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'totalTravelers': total,
                'activeTravelers': active,
                'openBatches': open_batches,
                'todayRegistrations': today
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return jsonify({"error": "Server error"}), 500

# ============ STARTUP ============

if __name__ == '__main__':
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Server starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)


