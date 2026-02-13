from flask import Flask, send_from_directory, jsonify, request, redirect, url_for, session
from flask_cors import CORS
from app.database import init_db, get_db
import os
from functools import wraps
import psycopg2
import psycopg2.extras

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
        
        cur.execute("""
            SELECT id, username, password_hash, full_name 
            FROM admin_users 
            WHERE username = %s AND is_active = true
        """, (username,))
        
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user and password == 'admin123':
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
    """Public healthcheck"""
    return jsonify({"status": "healthy"}), 200

# ============ BATCHES API ============
@app.route('/api/batches', methods=['GET'])
def get_all_batches():
    """Get all batches for frontend"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM batches ORDER BY departure_date")
        batches = cur.fetchall()
        
        result = []
        for b in batches:
            # Convert date objects to strings safely
            departure_date = b[2].isoformat() if b[2] else None
            return_date = b[3].isoformat() if b[3] else None
            
            # Handle price conversion safely
            price = None
            if b[7] is not None:
                try:
                    price = float(b[7])
                except (TypeError, ValueError):
                    price = None
            
            result.append({
                'id': b[0],
                'batch_name': b[1],
                'departure_date': departure_date,
                'return_date': return_date,
                'total_seats': b[4],
                'booked_seats': b[5],
                'status': b[6],
                'price': price,
                'description': b[8] if len(b) > 8 else None
            })
        cur.close()
        conn.close()
        return jsonify({'success': True, 'batches': result})
    except Exception as e:
        print(f"Batches API error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/batches', methods=['POST'])
@login_required
def create_batch():
    """Create new batch"""
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

# ============ TRAVELER API ============

@app.route('/api/travelers', methods=['GET'])
def get_all_travelers():
    """Get all travelers"""
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
                'passport_issue_date': row[6].isoformat() if row[6] else None,
                'passport_expiry_date': row[7].isoformat() if row[7] else None,
                'passport_status': row[8],
                'gender': row[9],
                'dob': row[10].isoformat() if row[10] else None,
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
                'created_at': row[30].isoformat() if row[30] else None,
                'updated_at': row[31].isoformat() if row[31] else None,
                'batch_name': row[32] if len(row) > 32 else None
            })
        
        cur.close()
        conn.close()
        return jsonify({'success': True, 'travelers': travelers})
    except Exception as e:
        print(f"Travelers API error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/travelers/<int:traveler_id>', methods=['GET'])
def get_traveler_by_id(traveler_id):
    """Get traveler by ID"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM travelers WHERE id = %s", (traveler_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            traveler = {
                'id': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'passport_no': row[5],
                'mobile': row[11],
                'email': row[12],
                'batch_id': row[4]
            }
            return jsonify({'success': True, 'traveler': traveler})
        else:
            return jsonify({'success': False}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/travelers/passport/<passport_no>', methods=['GET'])
def get_traveler_by_passport(passport_no):
    """Get traveler by passport number"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM travelers WHERE passport_no = %s", (passport_no,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            traveler = {
                'id': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'passport_no': row[5],
                'mobile': row[11],
                'email': row[12],
                'batch_id': row[4]
            }
            return jsonify({'success': True, 'traveler': traveler})
        else:
            return jsonify({'success': False}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/travelers', methods=['POST'])
def create_traveler():
    """Create new traveler"""
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO travelers (
                first_name, last_name, batch_id, passport_no,
                mobile, email, pin
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get('first_name'),
            data.get('last_name'),
            data.get('batch_id'),
            data.get('passport_no'),
            data.get('mobile'),
            data.get('email'),
            data.get('pin', '0000')
        ))
        
        traveler_id = cur.fetchone()[0]
        
        # Update booked seats
        cur.execute("""
            UPDATE batches 
            SET booked_seats = booked_seats + 1 
            WHERE id = %s
        """, (data.get('batch_id'),))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'traveler_id': traveler_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ PAYMENTS API ============

@app.route('/api/payments', methods=['GET'])
def get_all_payments():
    """Get all payments with traveler details"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                p.id,
                t.first_name || ' ' || t.last_name as traveler_name,
                p.installment,
                p.amount,
                TO_CHAR(p.due_date, 'DD-MM-YYYY') as due_date,
                TO_CHAR(p.payment_date, 'DD-MM-YYYY') as payment_date,
                p.status,
                p.payment_method
            FROM payments p
            JOIN travelers t ON p.traveler_id = t.id
            ORDER BY 
                CASE 
                    WHEN p.status = 'Pending' THEN 1 
                    WHEN p.status = 'Paid' THEN 2 
                    ELSE 3 
                END,
                p.due_date ASC
        """)
        
        payments = []
        for row in cur.fetchall():
            payments.append({
                'id': row[0],
                'traveler_name': row[1],
                'installment': row[2],
                'amount': float(row[3]),
                'due_date': row[4],
                'payment_date': row[5],
                'status': row[6],
                'payment_method': row[7]
            })
        
        cur.close()
        conn.close()
        return jsonify({'success': True, 'payments': payments})
    except Exception as e:
        print(f"Payments API error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/payments/stats', methods=['GET'])
def get_payment_stats():
    """Get payment statistics for dashboard"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Total collected
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'Paid'")
        total_collected = cur.fetchone()[0]
        
        # Pending amount
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'Pending'")
        pending_amount = cur.fetchone()[0]
        
        # Payment count by status
        cur.execute("SELECT status, COUNT(*) FROM payments GROUP BY status")
        status_counts = {}
        for row in cur.fetchall():
            status_counts[row[0]] = row[1]
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_collected': float(total_collected),
                'pending_amount': float(pending_amount),
                'status_counts': status_counts
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/payments', methods=['POST'])
def create_payment():
    """Create a new payment record"""
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO payments (
                traveler_id, installment, amount, payment_date, 
                payment_method, transaction_id, remarks, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get('traveler_id'),
            data.get('installment'),
            data.get('amount'),
            data.get('payment_date'),
            data.get('payment_method'),
            data.get('transaction_id'),
            data.get('remarks'),
            data.get('status', 'Paid')
        ))
        
        payment_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'payment_id': payment_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ STATISTICS API ============

@app.route('/api/travelers/stats/summary', methods=['GET'])
def get_stats_summary():
    """Get dashboard statistics"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM travelers")
        total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM travelers WHERE passport_status = 'Active' OR passport_status IS NULL")
        active = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM batches WHERE status IN ('Open', 'Closing Soon')")
        open_batches = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM travelers WHERE DATE(created_at) = CURRENT_DATE")
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
