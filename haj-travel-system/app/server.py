from flask import Flask, send_from_directory, jsonify, request, redirect, url_for, session
from flask_cors import CORS
from app.database import init_db
import os
from functools import wraps

app = Flask(__name__)
CORS(app)

# Secret key for sessions - CHANGE THIS IN PRODUCTION!
app.secret_key = 'alhudha-haj-secret-key-2026'

# Public folder path - using 'puplic' as per your GitHub
PUBLIC_DIR = '/app/puplic'

print(f"📁 Public folder: {PUBLIC_DIR}")
print(f"📁 Files: {os.listdir(PUBLIC_DIR) if os.path.exists(PUBLIC_DIR) else 'NOT FOUND'}")

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
    
    # Simple authentication - CHANGE THESE IN PRODUCTION!
    if username == 'admin' and password == 'admin123':
        session['admin_logged_in'] = True
        return jsonify({'success': True, 'message': 'Login successful'})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

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
    """Public main form - no login required"""
    return send_from_directory(PUBLIC_DIR, 'index.html')

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
    # ============ TRAVELER PORTAL ROUTES ============

@app.route('/traveler-login')
def traveler_login_page():
    """Serve traveler login page"""
    return send_from_directory(PUBLIC_DIR, 'traveler_login.html')

@app.route('/traveler/dashboard')
def traveler_dashboard():
    """Serve traveler dashboard"""
    return send_from_directory(PUBLIC_DIR, 'traveler_dashboard.html')

@app.route('/api/traveler/login', methods=['POST'])
def traveler_login():
    """API endpoint for traveler login using passport + PIN"""
    data = request.json
    passport_no = data.get('passport_no')
    pin = data.get('pin')
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Check if traveler exists and PIN matches
        # Note: You need to add a 'pin' column to travelers table
        cur.execute("""
            SELECT id, first_name, last_name 
            FROM travelers 
            WHERE passport_no = %s AND pin = %s
        """, (passport_no, pin))
        
        traveler = cur.fetchone()
        cur.close()
        conn.close()
        
        if traveler:
            return jsonify({
                'success': True,
                'traveler_id': traveler[0],
                'name': f"{traveler[1]} {traveler[2]}"
            })
        else:
            return jsonify({'success': False}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/traveler/<passport_no>')
def get_traveler_by_passport(passport_no):
    """Get traveler details by passport number"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT t.*, b.batch_name, b.departure_date, b.return_date, b.status as batch_status
            FROM travelers t
            LEFT JOIN batches b ON t.batch_id = b.id
            WHERE t.passport_no = %s
        """, (passport_no,))
        
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
                'vaccine_status': row[16],
                'wheelchair': row[17],
                'father_name': row[21],
                'mother_name': row[22],
                'spouse_name': row[23],
                'batch_name': row[31],
                'departure_date': row[32],
                'return_date': row[33],
                'batch_status': row[34]
            }
            return jsonify({'success': True, 'traveler': traveler})
        else:
            return jsonify({'success': False}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ PAYMENT ROUTES ============

@app.route('/api/payments/<int:traveler_id>')
def get_payments(traveler_id):
    """Get payment schedule for traveler"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Create payments table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                traveler_id INTEGER REFERENCES travelers(id),
                installment TEXT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                due_date DATE,
                status TEXT DEFAULT 'Pending',
                payment_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("""
            SELECT * FROM payments 
            WHERE traveler_id = %s 
            ORDER BY due_date
        """, (traveler_id,))
        
        payments = []
        for row in cur.fetchall():
            payments.append({
                'id': row[0],
                'installment': row[2],
                'amount': row[3],
                'due_date': row[4],
                'status': row[5],
                'payment_date': row[6]
            })
        
        cur.close()
        conn.close()
        return jsonify({'success': True, 'payments': payments})
    except Exception as e:
        return jsonify({'success': True, 'payments': []})  # Return empty if table doesn't exist

