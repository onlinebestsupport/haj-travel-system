from flask import Flask, send_from_directory, jsonify, request, redirect, url_for, session, send_file
from flask_cors import CORS
from app.database import init_db, get_db
import os
from functools import wraps
import psycopg2
import psycopg2.extras
import datetime
import json
import shutil
import zipfile
from io import BytesIO
import subprocess

app = Flask(__name__)
CORS(app)

# Secret key for sessions - CHANGE THIS IN PRODUCTION!
app.secret_key = 'alhudha-haj-secret-key-2026'

# Public folder path - USING 'public' as per your GitHub
PUBLIC_DIR = '/app/public'
BACKUP_DIR = '/app/backups'
UPLOAD_DIR = '/app/uploads'

# Create backup directory if not exists
os.makedirs(BACKUP_DIR, exist_ok=True)

print(f"📁 Public folder: {PUBLIC_DIR}")
print(f"📁 Files: {os.listdir(PUBLIC_DIR) if os.path.exists(PUBLIC_DIR) else 'NOT FOUND'}")
print(f"📁 Backup folder: {BACKUP_DIR}")

# ============ CREATE LOGIN LOGS TABLE ============
def create_login_logs_table():
    """Create table to track all logins"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS login_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES admin_users(id),
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(45),
                user_agent TEXT,
                logout_time TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Login logs table ready")
    except Exception as e:
        print(f"❌ Error creating login_logs table: {e}")

# Call this at startup
create_login_logs_table()

# ============ ROLE-BASED ACCESS CONTROL ============

def has_permission(permission_name):
    """Check if logged-in user has specific permission"""
    if not session.get('admin_logged_in'):
        return False
    
    # Super admin has all permissions
    if 'super_admin' in session.get('admin_roles', []):
        return True
    
    permissions = session.get('admin_permissions', [])
    return permission_name in permissions

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

# ============ LOGIN WITH ROLE & TIME TRACKING ============
@app.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for login with role and time tracking"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Get user details with roles
        cur.execute("""
            SELECT u.id, u.username, u.full_name, 
                   array_agg(r.name) as roles
            FROM admin_users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            WHERE u.username = %s AND u.is_active = true
            GROUP BY u.id
        """, (username,))
        
        user = cur.fetchone()
        
        if user and password == 'admin123':  # In production, use proper password hashing
            user_id = user[0]
            roles = user[3] if user[3] else ['viewer']
            
            # Get all permissions for this user
            cur.execute("""
                SELECT DISTINCT p.name
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN user_roles ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = %s
            """, (user_id,))
            
            permissions = [row[0] for row in cur.fetchall()]
            
            # Log the login
            cur.execute("""
                INSERT INTO login_logs (user_id, login_time, ip_address, user_agent)
                VALUES (%s, NOW(), %s, %s)
            """, (user_id, request.remote_addr, request.headers.get('User-Agent')))
            
            conn.commit()
            
            session['admin_logged_in'] = True
            session['admin_user_id'] = user_id
            session['admin_username'] = user[1]
            session['admin_name'] = user[2] or user[1]
            session['admin_roles'] = roles
            session['admin_permissions'] = permissions
            
            return jsonify({
                'success': True, 
                'message': 'Login successful',
                'user': {
                    'id': user_id,
                    'name': user[2] or user[1],
                    'roles': roles,
                    'permissions': permissions
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ LOGOUT WITH TIME TRACKING ============
@app.route('/api/logout', methods=['POST'])
def api_logout():
    """API endpoint for logout with time tracking"""
    if session.get('admin_user_id'):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                UPDATE login_logs 
                SET logout_time = NOW() 
                WHERE user_id = %s AND logout_time IS NULL
                ORDER BY login_time DESC LIMIT 1
            """, (session['admin_user_id'],))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Logout logging error: {e}")
    
    session.clear()
    return jsonify({'success': True, 'message': 'Logout successful'})

# ============ GET USER PERMISSIONS ============
@app.route('/api/user/permissions', methods=['GET'])
@login_required
def get_user_permissions():
    """Get current user's permissions"""
    return jsonify({
        'success': True,
        'user_id': session.get('admin_user_id'),
        'username': session.get('admin_username'),
        'roles': session.get('admin_roles', []),
        'permissions': session.get('admin_permissions', [])
    })

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

# ============ GET ALL ROLES ============
@app.route('/api/roles', methods=['GET'])
@login_required
def get_all_roles():
    """Get all available roles with permissions"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT r.*, array_agg(p.name) as permissions
            FROM roles r
            LEFT JOIN role_permissions rp ON r.id = rp.role_id
            LEFT JOIN permissions p ON rp.permission_id = p.id
            GROUP BY r.id
            ORDER BY r.id
        """)
        
        roles = []
        for row in cur.fetchall():
            roles.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'permissions': [p for p in row[4] if p]  # Filter out None
            })
        
        cur.close()
        conn.close()
        return jsonify({'success': True, 'roles': roles})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ SUPER ADMIN: GET ALL USERS ============
@app.route('/api/admin/users', methods=['GET'])
@login_required
@permission_required('manage_users')
def get_all_users():
    """Get all users with their roles and permissions"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                u.id, u.username, u.full_name, u.email, u.is_active,
                COALESCE(array_agg(DISTINCT r.name), '{}') as roles,
                COALESCE(array_agg(DISTINCT p.name), '{}') as permissions,
                u.created_at
            FROM admin_users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            LEFT JOIN role_permissions rp ON r.id = rp.role_id
            LEFT JOIN permissions p ON rp.permission_id = p.id
            GROUP BY u.id
            ORDER BY u.created_at DESC
        """)
        
        users = []
        for row in cur.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'full_name': row[2],
                'email': row[3],
                'is_active': row[4],
                'roles': [r for r in row[5] if r],
                'permissions': list(set([p for p in row[6] if p])),
                'created_at': row[7].isoformat() if row[7] else None
            })
        
        cur.close()
        conn.close()
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ SUPER ADMIN: GET LOGIN LOGS ============
@app.route('/api/admin/login-logs', methods=['GET'])
@login_required
@permission_required('view_logs')
def get_login_logs():
    """Get login logs for last 30 days"""
    try:
        days = request.args.get('days', 30)
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                l.id, u.username, u.full_name, 
                l.login_time, l.logout_time, l.ip_address, l.user_agent
            FROM login_logs l
            JOIN admin_users u ON l.user_id = u.id
            WHERE l.login_time > NOW() - INTERVAL '%s days'
            ORDER BY l.login_time DESC
        """, (days,))
        
        logs = []
        for row in cur.fetchall():
            duration = None
            if row[4]:  # logout_time exists
                duration = (row[4] - row[3]).total_seconds() / 60  # minutes
            
            logs.append({
                'id': row[0],
                'username': row[1],
                'full_name': row[2],
                'login_time': row[3].isoformat(),
                'logout_time': row[4].isoformat() if row[4] else None,
                'duration_minutes': round(duration, 2) if duration else None,
                'ip_address': row[5],
                'user_agent': row[6]
            })
        
        cur.close()
        conn.close()
        return jsonify({'success': True, 'logs': logs})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ SUPER ADMIN: UPDATE USER PERMISSIONS ============
@app.route('/api/admin/users/<int:user_id>/permissions', methods=['PUT'])
@login_required
@permission_required('manage_users')
def update_user_permissions(user_id):
    """Update user's roles and permissions"""
    try:
        data = request.json
        role_names = data.get('roles', [])
        
        conn = get_db()
        cur = conn.cursor()
        
        # Clear existing roles
        cur.execute("DELETE FROM user_roles WHERE user_id = %s", (user_id,))
        
        # Add new roles
        for role_name in role_names:
            cur.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
            role = cur.fetchone()
            if role:
                cur.execute("""
                    INSERT INTO user_roles (user_id, role_id, assigned_by)
                    VALUES (%s, %s, %s)
                """, (user_id, role[0], session['admin_user_id']))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Permissions updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ SUPER ADMIN: TOGGLE USER STATUS ============
@app.route('/api/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@permission_required('manage_users')
def toggle_user_status(user_id):
    """Activate or deactivate a user"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE admin_users 
            SET is_active = NOT is_active 
            WHERE id = %s
            RETURNING is_active
        """, (user_id,))
        
        new_status = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'User {"activated" if new_status else "deactivated"}',
            'is_active': new_status
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
            # Log the entire row to see structure (temporary debug)
            print(f"Row has {len(b)} columns")
            
            # CORRECT COLUMN INDEXES based on your schema:
            # 0:id, 1:batch_name, 2:departure_date, 3:return_date, 
            # 4:total_seats, 5:booked_seats, 6:status, 7:created_at, 8:price, 9:description
            
            # Convert date objects to strings safely
            departure_date = b[2].isoformat() if b[2] else None
            return_date = b[3].isoformat() if b[3] else None
            
            # PRICE IS AT INDEX 8, NOT 7!
            price = None
            if len(b) > 8 and b[8] is not None:
                try:
                    price = float(b[8])
                    print(f"✅ Price found: {price} for {b[1]}")
                except (TypeError, ValueError) as e:
                    print(f"❌ Price conversion error for {b[1]}: {e}")
                    price = None
            else:
                print(f"⚠️ No price for {b[1]}")
            
            result.append({
                'id': b[0],
                'batch_name': b[1],
                'departure_date': departure_date,
                'return_date': return_date,
                'total_seats': b[4],
                'booked_seats': b[5],
                'status': b[6],
                'price': price,
                'description': b[9] if len(b) > 9 else None
            })
        cur.close()
        conn.close()
        print(f"✅ Returning {len(result)} batches with prices")
        return jsonify({'success': True, 'batches': result})
    except Exception as e:
        print(f"❌ Batches API error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/batches', methods=['POST'])
@login_required
@permission_required('create_batch')
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
@login_required
@permission_required('create_traveler')
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

# ============ TRAVELER LOGIN API ============
@app.route('/api/traveler/login', methods=['POST'])
def traveler_login():
    """API endpoint for traveler login using passport + PIN"""
    try:
        data = request.json
        passport_no = data.get('passport_no')
        pin = data.get('pin')
        
        conn = get_db()
        cur = conn.cursor()
        
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
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/traveler/<passport_no>', methods=['GET'])
def get_traveler_by_passport_api(passport_no):
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
                'batch_name': row[32] if len(row) > 32 else None,
                'departure_date': row[33].isoformat() if len(row) > 33 and row[33] else None,
                'return_date': row[34].isoformat() if len(row) > 34 and row[34] else None,
                'batch_status': row[35] if len(row) > 35 else None
            }
            return jsonify({'success': True, 'traveler': traveler})
        else:
            return jsonify({'success': False}), 404
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
                    WHEN p.status = 'Reversed' THEN 3
                    ELSE 4 
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
        
        # Reversed amount
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'Reversed'")
        reversed_amount = cur.fetchone()[0]
        
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
                'reversed_amount': float(reversed_amount),
                'status_counts': status_counts
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/payments', methods=['POST'])
@login_required
@permission_required('create_payment')
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

# ============ STEP 12: PAYMENT REVERSAL API ============

@app.route('/api/payments/reverse/<int:payment_id>', methods=['POST'])
@login_required
@permission_required('reverse_payment')
def reverse_payment(payment_id):
    """Reverse a payment (admin only) - Step 12"""
    try:
        data = request.json
        reason = data.get('reason')
        reversal_amount = data.get('amount')  # For partial reversal
        is_full_reversal = data.get('full_reversal', True)
        
        if not reason:
            return jsonify({'success': False, 'error': 'Reason is required for reversal'}), 400
        
        conn = get_db()
        cur = conn.cursor()
        
        # Get original payment
        cur.execute("SELECT * FROM payments WHERE id = %s", (payment_id,))
        payment = cur.fetchone()
        
        if not payment:
            return jsonify({'success': False, 'error': 'Payment not found'}), 404
        
        if payment[6] == 'Reversed':  # status column
            return jsonify({'success': False, 'error': 'Payment already reversed'}), 400
        
        # Calculate reversal amount
        reversal_amt = payment[3] if is_full_reversal else reversal_amount  # amount column
        
        # Create payment_reversals table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payment_reversals (
                id SERIAL PRIMARY KEY,
                original_payment_id INTEGER REFERENCES payments(id),
                amount DECIMAL(10,2) NOT NULL,
                reason TEXT NOT NULL,
                reversed_by INTEGER REFERENCES admin_users(id),
                reversed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_full_reversal BOOLEAN DEFAULT true
            )
        """)
        
        # Create reversal record
        cur.execute("""
            INSERT INTO payment_reversals (
                original_payment_id, amount, reason, reversed_by, is_full_reversal
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (payment_id, reversal_amt, reason, session['admin_user_id'], is_full_reversal))
        
        reversal_id = cur.fetchone()[0]
        
        if is_full_reversal:
            # Update original payment status
            cur.execute("UPDATE payments SET status = 'Reversed' WHERE id = %s", (payment_id,))
        else:
            # For partial reversal, keep original but reduce amount? 
            # This depends on your business logic
            # Option: Create a new negative payment
            cur.execute("""
                INSERT INTO payments (
                    traveler_id, installment, amount, payment_date, 
                    payment_method, remarks, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                payment[1],  # traveler_id
                f"Reversal of {payment[2]}",  # installment
                -reversal_amt,  # negative amount
                datetime.date.today().isoformat(),
                'Reversal',
                f"Partial reversal of payment {payment_id}: {reason}",
                'Reversed'
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Payment reversed successfully',
            'reversal_id': reversal_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/payments/reversals', methods=['GET'])
@login_required
@permission_required('view_payments')
def get_payment_reversals():
    """Get all payment reversals"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT pr.*, p.id as payment_id, p.amount as original_amount,
                   t.first_name || ' ' || t.last_name as traveler_name,
                   a.username as reversed_by_username
            FROM payment_reversals pr
            JOIN payments p ON pr.original_payment_id = p.id
            JOIN travelers t ON p.traveler_id = t.id
            LEFT JOIN admin_users a ON pr.reversed_by = a.id
            ORDER BY pr.reversed_at DESC
        """)
        
        reversals = []
        for row in cur.fetchall():
            reversals.append({
                'id': row[0],
                'original_payment_id': row[1],
                'amount': float(row[2]),
                'reason': row[3],
                'reversed_at': row[5].isoformat() if row[5] else None,
                'is_full_reversal': row[6],
                'original_amount': float(row[8]),
                'traveler_name': row[9],
                'reversed_by': row[10]
            })
        
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'reversals': reversals})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ STEP 13: GST/TCS INVOICE MODULE ============

@app.route('/api/invoice/generate/<int:traveler_id>', methods=['GET'])
@login_required
@permission_required('view_reports')
def generate_invoice(traveler_id):
    """Generate GST/TCS invoice for traveler"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Get traveler details with batch and payments
        cur.execute("""
            SELECT 
                t.*, 
                b.batch_name, b.price as batch_price,
                COALESCE(SUM(p.amount) FILTER (WHERE p.status = 'Paid'), 0) as total_paid
            FROM travelers t
            LEFT JOIN batches b ON t.batch_id = b.id
            LEFT JOIN payments p ON t.id = p.traveler_id
            WHERE t.id = %s
            GROUP BY t.id, b.id
        """, (traveler_id,))
        
        traveler = cur.fetchone()
        
        if not traveler:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
        
        # Calculate GST and TCS
        base_amount = float(traveler[39]) if traveler[39] else 0  # batch_price
        total_paid = float(traveler[40]) if traveler[40] else 0
        
        # GST calculation (5% on base amount)
        gst_rate = 5
        gst_amount = (base_amount * gst_rate) / 100
        
        # TCS calculation (0.5% on GST-inclusive amount)
        tcs_rate = 0.5
        amount_with_gst = base_amount + gst_amount
        tcs_amount = (amount_with_gst * tcs_rate) / 100
        
        total_invoice = amount_with_gst + tcs_amount
        balance_due = total_invoice - total_paid
        
        # Create invoices table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id SERIAL PRIMARY KEY,
                traveler_id INTEGER REFERENCES travelers(id),
                invoice_number VARCHAR(50) UNIQUE,
                base_amount DECIMAL(10,2),
                gst_rate DECIMAL(5,2),
                gst_amount DECIMAL(10,2),
                tcs_rate DECIMAL(5,2),
                tcs_amount DECIMAL(10,2),
                total_amount DECIMAL(10,2),
                total_paid DECIMAL(10,2),
                balance_due DECIMAL(10,2),
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                generated_by INTEGER REFERENCES admin_users(id),
                pdf_path TEXT
            )
        """)
        
        # Generate invoice number
        invoice_number = f"INV-{datetime.datetime.now().strftime('%Y%m')}-{traveler_id:04d}"
        
        # Store invoice in database
        cur.execute("""
            INSERT INTO invoices (
                traveler_id, invoice_number, base_amount, gst_rate, gst_amount,
                tcs_rate, tcs_amount, total_amount, total_paid, balance_due, generated_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            traveler_id, invoice_number, base_amount, gst_rate, gst_amount,
            tcs_rate, tcs_amount, total_invoice, total_paid, balance_due,
            session['admin_user_id']
        ))
        
        invoice_id = cur.fetchone()[0]
        conn.commit()
        
        # Get all payments for this traveler
        cur.execute("""
            SELECT installment, amount, payment_date, status
            FROM payments
            WHERE traveler_id = %s AND status IN ('Paid', 'Pending')
            ORDER BY payment_date
        """, (traveler_id,))
        
        payments = []
        for row in cur.fetchall():
            payments.append({
                'installment': row[0],
                'amount': float(row[1]),
                'payment_date': row[2].isoformat() if row[2] else None,
                'status': row[3]
            })
        
        cur.close()
        conn.close()
        
        invoice_data = {
            'invoice_id': invoice_id,
            'invoice_number': invoice_number,
            'traveler': {
                'id': traveler[0],
                'name': f"{traveler[1]} {traveler[2]}",
                'passport': traveler[5],
                'mobile': traveler[11],
                'email': traveler[12]
            },
            'batch': {
                'name': traveler[38],
                'price': base_amount
            },
            'calculations': {
                'base_amount': base_amount,
                'gst_rate': gst_rate,
                'gst_amount': gst_amount,
                'tcs_rate': tcs_rate,
                'tcs_amount': tcs_amount,
                'total_invoice': total_invoice,
                'total_paid': total_paid,
                'balance_due': balance_due
            },
            'payments': payments,
            'generated_at': datetime.datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'invoice': invoice_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invoice/<int:invoice_id>', methods=['GET'])
@login_required
@permission_required('view_reports')
def get_invoice(invoice_id):
    """Get invoice details"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT i.*, t.first_name, t.last_name, t.passport_no, b.batch_name
            FROM invoices i
            JOIN travelers t ON i.traveler_id = t.id
            LEFT JOIN batches b ON t.batch_id = b.id
            WHERE i.id = %s
        """, (invoice_id,))
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            invoice = {
                'id': row[0],
                'traveler_id': row[1],
                'invoice_number': row[2],
                'base_amount': float(row[3]),
                'gst_rate': float(row[4]),
                'gst_amount': float(row[5]),
                'tcs_rate': float(row[6]),
                'tcs_amount': float(row[7]),
                'total_amount': float(row[8]),
                'total_paid': float(row[9]),
                'balance_due': float(row[10]),
                'generated_at': row[11].isoformat() if row[11] else None,
                'traveler_name': f"{row[14]} {row[15]}",
                'passport': row[16],
                'batch_name': row[17]
            }
            return jsonify({'success': True, 'invoice': invoice})
        else:
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ STEP 16: DAILY AUTO BACKUP ============

@app.route('/api/backup/create', methods=['POST'])
@login_required
@permission_required('create_backup')
def create_manual_backup():
    """Create manual backup"""
    return create_backup_function()

@app.route('/api/backup/auto', methods=['POST'])
def auto_backup():
    """Automated backup (called by cron job)"""
    # This endpoint should be protected by a secret key
    auth_key = request.headers.get('X-Backup-Key')
    if auth_key != os.environ.get('BACKUP_SECRET_KEY', 'alhudha-backup-key-2026'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    return create_backup_function()

def create_backup_function():
    """Core backup function"""
    try:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{timestamp}.zip"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # Create a temporary directory for backup files
        temp_dir = f"/tmp/backup_{timestamp}"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 1. Backup database
        db_backup_file = os.path.join(temp_dir, "database.sql")
        
        # Get database URL from environment
        db_url = os.environ.get('DATABASE_URL')
        
        # Use pg_dump to backup database
        if db_url:
            cmd = f"pg_dump {db_url} > {db_backup_file}"
            subprocess.run(cmd, shell=True, check=True)
        
        # 2. Backup uploads folder
        uploads_backup = os.path.join(temp_dir, "uploads")
        if os.path.exists(UPLOAD_DIR):
            shutil.copytree(UPLOAD_DIR, uploads_backup)
        
        # 3. Create backup log
        conn = get_db()
        cur = conn.cursor()
        
        # Get backup stats
        cur.execute("SELECT COUNT(*) FROM travelers")
        traveler_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM batches")
        batch_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM payments")
        payment_count = cur.fetchone()[0]
        
        # Create backup record
        cur.execute("""
            CREATE TABLE IF NOT EXISTS backups (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255),
                size_bytes BIGINT,
                traveler_count INTEGER,
                batch_count INTEGER,
                payment_count INTEGER,
                status VARCHAR(50),
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 4. Zip everything
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        # Get file size
        backup_size = os.path.getsize(backup_path)
        
        # 5. Cleanup old backups (keep last 30 days)
        cleanup_old_backups(30)
        
        # 6. Record backup in database
        cur.execute("""
            INSERT INTO backups (filename, size_bytes, traveler_count, batch_count, payment_count, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (backup_filename, backup_size, traveler_count, batch_count, payment_count, 'Success'))
        
        conn.commit()
        cur.close()
        conn.close()
        
        # 7. Cleanup temp directory
        shutil.rmtree(temp_dir)
        
        return jsonify({
            'success': True, 
            'message': 'Backup created successfully',
            'filename': backup_filename,
            'size': backup_size,
            'stats': {
                'travelers': traveler_count,
                'batches': batch_count,
                'payments': payment_count
            }
        })
    except Exception as e:
        # Record failure
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO backups (filename, status, error_message)
                VALUES (%s, %s, %s)
            """, ('failed_' + timestamp, 'Failed', str(e)))
            conn.commit()
            cur.close()
            conn.close()
        except:
            pass
        
        return jsonify({'success': False, 'error': str(e)}), 500

def cleanup_old_backups(days_to_keep):
    """Delete backups older than specified days"""
    try:
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
        
        for filename in os.listdir(BACKUP_DIR):
            filepath = os.path.join(BACKUP_DIR, filename)
            if os.path.isfile(filepath):
                file_time = datetime.datetime.fromtimestamp(os.path.getctime(filepath))
                if file_time < cutoff:
                    os.remove(filepath)
    except Exception as e:
        print(f"Backup cleanup error: {e}")

@app.route('/api/backups', methods=['GET'])
@login_required
@permission_required('view_reports')
def get_backups():
    """Get list of all backups"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT * FROM backups 
            ORDER BY created_at DESC 
            LIMIT 50
        """)
        
        backups = []
        for row in cur.fetchall():
            backups.append({
                'id': row[0],
                'filename': row[1],
                'size_bytes': row[2],
                'traveler_count': row[3],
                'batch_count': row[4],
                'payment_count': row[5],
                'status': row[6],
                'error_message': row[7],
                'created_at': row[8].isoformat() if row[8] else None
            })
        
        cur.close()
        conn.close()
        return jsonify({'success': True, 'backups': backups})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/backup/download/<filename>', methods=['GET'])
@login_required
@permission_required('export_data')
def download_backup(filename):
    """Download a backup file"""
    try:
        filepath = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'Backup not found'}), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/backup/restore/<filename>', methods=['POST'])
@login_required
@permission_required('restore_backup')
def restore_backup(filename):
    """Restore from a backup (admin only)"""
    try:
        filepath = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'Backup not found'}), 404
        
        # Extract to temp directory
        temp_restore = f"/tmp/restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(temp_restore, exist_ok=True)
        
        with zipfile.ZipFile(filepath, 'r') as zipf:
            zipf.extractall(temp_restore)
        
        # Restore database
        db_backup = os.path.join(temp_restore, "database.sql")
        if os.path.exists(db_backup):
            db_url = os.environ.get('DATABASE_URL')
            cmd = f"psql {db_url} < {db_backup}"
            subprocess.run(cmd, shell=True, check=True)
        
        # Restore uploads
        uploads_restore = os.path.join(temp_restore, "uploads")
        if os.path.exists(uploads_restore):
            if os.path.exists(UPLOAD_DIR):
                shutil.rmtree(UPLOAD_DIR)
            shutil.copytree(uploads_restore, UPLOAD_DIR)
        
        # Cleanup
        shutil.rmtree(temp_restore)
        
        return jsonify({'success': True, 'message': 'Backup restored successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ STEP 18: MORNING HEALTH CHECK ============

@app.route('/api/health/check', methods=['GET'])
@login_required
def morning_health_check():
    """Morning health check for admin"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Check database connection
        cur.execute("SELECT 1")
        db_ok = True
        
        # Check last backup
        cur.execute("SELECT created_at, status FROM backups ORDER BY created_at DESC LIMIT 1")
        last_backup = cur.fetchone()
        
        # Check recent errors
        cur.execute("SELECT COUNT(*) FROM backups WHERE status = 'Failed' AND created_at > NOW() - INTERVAL '1 day'")
        failed_backups = cur.fetchone()[0]
        
        # Get system stats
        cur.execute("SELECT COUNT(*) FROM travelers")
        travelers = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM batches")
        batches = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM payments WHERE status = 'Pending'")
        pending_payments = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        # Calculate health status
        health_status = 'GREEN'
        issues = []
        
        if not db_ok:
            health_status = 'RED'
            issues.append('Database connection failed')
        elif not last_backup:
            health_status = 'YELLOW'
            issues.append('No backup found')
        elif last_backup[1] == 'Failed':
            health_status = 'YELLOW'
            issues.append('Last backup failed')
        elif (datetime.datetime.now() - last_backup[0]).days > 1:
            health_status = 'YELLOW'
            issues.append('Backup older than 1 day')
        
        if failed_backups > 0:
            if health_status != 'RED':
                health_status = 'YELLOW'
            issues.append(f'{failed_backups} failed backups in last 24h')
        
        return jsonify({
            'success': True,
            'health_check': {
                'status': health_status,
                'timestamp': datetime.datetime.now().isoformat(),
                'database': 'Connected' if db_ok else 'Failed',
                'last_backup': last_backup[0].isoformat() if last_backup else None,
                'last_backup_status': last_backup[1] if last_backup else None,
                'stats': {
                    'travelers': travelers,
                    'batches': batches,
                    'pending_payments': pending_payments
                },
                'issues': issues,
                'message': get_health_message(health_status)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_health_message(status):
    """Get user-friendly health message"""
    if status == 'GREEN':
        return '✅ System is healthy. All systems operational.'
    elif status == 'YELLOW':
        return '⚠️ System has minor issues. Check backup status.'
    else:
        return '❌ System has critical issues. Immediate attention required.'

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
        create_login_logs_table()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Server starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

@app.route('/api/payments/traveler/<int:traveler_id>', methods=['GET'])
def get_traveler_payments(traveler_id):
    """Get payments for a specific traveler"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                p.id,
                p.installment,
                p.amount,
                TO_CHAR(p.due_date, 'DD-MM-YYYY') as due_date,
                TO_CHAR(p.payment_date, 'DD-MM-YYYY') as payment_date,
                p.status,
                p.payment_method
            FROM payments p
            WHERE p.traveler_id = %s
            ORDER BY p.due_date
        """, (traveler_id,))
        
        payments = []
        for row in cur.fetchall():
            payments.append({
                'id': row[0],
                'installment': row[1],
                'amount': float(row[2]),
                'due_date': row[3],
                'payment_date': row[4],
                'status': row[5],
                'payment_method': row[6]
            })
        
        cur.close()
        conn.close()
        return jsonify({'success': True, 'payments': payments})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ SUPER ADMIN: DELETE USER ============
@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@permission_required('manage_users')
def delete_user(user_id):
    """Delete a user (super admin only)"""
    try:
        # Prevent deleting yourself
        if user_id == session.get('admin_user_id'):
            return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
        
        conn = get_db()
        cur = conn.cursor()
        
        # Delete user roles first (cascade should handle this, but let's be explicit)
        cur.execute("DELETE FROM user_roles WHERE user_id = %s", (user_id,))
        
        # Delete the user
        cur.execute("DELETE FROM admin_users WHERE id = %s RETURNING id", (user_id,))
        deleted = cur.fetchone()
        
        conn.commit()
        cur.close()
        conn.close()
        
        if deleted:
            return jsonify({'success': True, 'message': 'User deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

