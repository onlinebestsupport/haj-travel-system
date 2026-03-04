from flask import Blueprint, request, jsonify, session
from app.database import get_db, release_db  # ✅ POOL SAFE
from app.middleware import role_required, log_critical_action, get_client_ip  # ✅ MIDDLEWARE
from datetime import datetime, timedelta
import json
import hashlib
import secrets

bp = Blueprint('auth', __name__, url_prefix='/api')

# ==================== 🔐 PASSWORD HELPERS (KEEP PLAIN FOR YOUR DEMO) ====================
def hash_password(password):
    """Simple SHA256 - KEEP for demo (use bcrypt in prod)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password, stored_password):
    """Verify plain password match (your current DB schema)"""
    return plain_password == stored_password  # ✅ Your DB stores plain text

# ==================== 🔥 SAFE DB WRAPPER (Zero Leaks) ====================
def safe_db_operation(operation_func):
    """🔥 POOL SAFE - Auto release_db()"""
    def wrapper(*args, **kwargs):
        conn = cursor = None
        try:
            conn, cursor = get_db()
            result = operation_func(conn, cursor, *args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            if conn: conn.rollback()
            print(f"❌ Auth DB error: {e}")
            return None
        finally:
            release_db(conn, cursor)  # 🔥 CRITICAL
    return wrapper

# ==================== 👤 ADMIN LOGIN ====================
@bp.route('/login', methods=['POST'])
def login():
    """🔥 CLEAN LOGIN - Single flow, pool safe"""
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    remember_me = data.get('remember_me', False)
    
    # Validate input
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    # 🔥 POOL SAFE USER LOOKUP - FIXED: Added password to SELECT
    def find_user(conn, cursor, uname):
        cursor.execute("""
            SELECT id, username, full_name, email, role, permissions, is_active, password 
            FROM users WHERE username = %s AND is_active = true
        """, (uname,))
        return cursor.fetchone()
    
    user = safe_db_operation(find_user)(username)
    
    # Verify credentials
    if user and verify_password(password, user['password']):  # ✅ Now user['password'] exists
        # 🔥 CRITICAL: Clear any existing session first
        session.clear()
        
        # Set session
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        if remember_me:
            session.permanent = True
            session.permanent_session_lifetime = timedelta(days=30)
        
        # 🔥 FORCE SESSION TO SAVE
        session.modified = True
        
        # Parse permissions
        permissions = {}
        if user['permissions']:
            try:
                permissions = json.loads(user['permissions']) if isinstance(user['permissions'], str) else user['permissions']
            except:
                permissions = {}
        
        # Log success
        log_critical_action(
            user['id'], 
            'LOGIN_SUCCESS', 
            f'Admin login from {get_client_ip()}',
            get_client_ip()
        )
        
        return jsonify({
            'success': True,
            'authenticated': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'name': user['full_name'] or user['username'],
                'email': user['email'],
                'role': user['role'],
                'permissions': permissions
            }
        })
    
    # Log failed attempt
    log_critical_action(
        None, 
        'LOGIN_FAILED', 
        f'Failed login attempt: {username} from {get_client_ip()}',
        get_client_ip()
    )
    
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

# ==================== 🧳 TRAVELER LOGIN ====================
@bp.route('/traveler/login', methods=['POST'])
def traveler_login():
    """Traveler login by passport + PIN"""
    data = request.json or {}
    passport_no = data.get('passport_no', '').strip().upper()
    pin = data.get('pin', '').strip()
    
    if not passport_no or not pin:
        return jsonify({'success': False, 'error': 'Passport and PIN required'}), 400
    
    if len(pin) != 4 or not pin.isdigit():
        return jsonify({'success': False, 'error': 'PIN must be 4 digits'}), 400
    
    def find_traveler(conn, cursor, passport, pin_code):
        cursor.execute("""
            SELECT t.*, b.batch_name, b.departure_date, b.status as batch_status
            FROM travelers t
            LEFT JOIN batches b ON t.batch_id = b.id
            WHERE t.passport_no = %s AND t.pin = %s
        """, (passport, pin_code))
        return cursor.fetchone()
    
    traveler = safe_db_operation(find_traveler)(passport_no, pin)
    
    if traveler:
        # Set traveler session (short lived)
        session['traveler_id'] = traveler['id']
        session['traveler_name'] = f"{traveler['first_name']} {traveler['last_name']}"
        session['traveler_passport'] = traveler['passport_no']
        session.permanent = True
        session.permanent_session_lifetime = timedelta(hours=2)
        session.modified = True
        
        # Payment summary
        def get_payment_summary(conn, cursor, tid):
            cursor.execute("""
                SELECT 
                    COUNT(*) as payment_count,
                    COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as total_paid,
                    COALESCE(SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END), 0) as total_pending
                FROM payments WHERE traveler_id = %s
            """, (tid,))
            return cursor.fetchone()
        
        payments = safe_db_operation(get_payment_summary)(traveler['id'])
        
        log_critical_action(
            None,
            'TRAVELER_LOGIN',
            f'{traveler["first_name"]} {traveler["last_name"]} logged in',
            get_client_ip()
        )
        
        return jsonify({
            'success': True,
            'traveler_id': traveler['id'],
            'name': f"{traveler['first_name']} {traveler['last_name']}",
            'passport': traveler['passport_no'],
            'batch_name': traveler.get('batch_name', 'N/A'),
            'payment_summary': {
                'total_paid': float(payments['total_paid']) if payments else 0,
                'total_pending': float(payments['total_pending']) if payments else 0,
                'payment_count': payments['payment_count'] if payments else 0
            }
        })
    
    log_critical_action(
        None,
        'TRAVELER_LOGIN_FAILED',
        f'Passport {passport_no} failed login',
        get_client_ip()
    )
    
    return jsonify({'success': False, 'error': 'Invalid passport or PIN'}), 401

# ==================== 🚪 LOGOUT ====================
@bp.route('/logout', methods=['POST'])
def logout():
    """Clean logout with logging"""
    user_id = session.pop('user_id', None)
    traveler_id = session.pop('traveler_id', None)
    
    if user_id:
        log_critical_action(user_id, 'LOGOUT', 'User logged out', get_client_ip())
    elif traveler_id:
        log_critical_action(None, 'TRAVELER_LOGOUT', f'Traveler {traveler_id} logged out', get_client_ip())
    
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})

# ==================== 🔍 SESSION CHECK ====================
@bp.route('/check-session', methods=['GET'])
def check_session():
    """🔥 Validate + refresh session"""
    response = {'success': True, 'authenticated': False}
    
    # Check admin session
    if session.get('user_id'):
        def validate_user(conn, cursor, uid):
            cursor.execute("""
                SELECT id, username, full_name, email, role, permissions
                FROM users WHERE id = %s AND is_active = true
            """, (uid,))
            return cursor.fetchone()
        
        user = safe_db_operation(validate_user)(session['user_id'])
        
        if user:
            permissions = {}
            if user['permissions']:
                try:
                    permissions = json.loads(user['permissions']) if isinstance(user['permissions'], str) else user['permissions']
                except:
                    permissions = {}
            
            response.update({
                'authenticated': True,
                'user_type': 'admin',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'name': user['full_name'] or user['username'],
                    'email': user['email'],
                    'role': user['role'],
                    'permissions': permissions
                }
            })
            return jsonify(response)
        # Invalid user → clear session
        session.clear()
    
    # Check traveler session
    elif session.get('traveler_id'):
        def validate_traveler(conn, cursor, tid):
            cursor.execute("""
                SELECT id, first_name, last_name, passport_no, batch_id
                FROM travelers WHERE id = %s
            """, (tid,))
            return cursor.fetchone()
        
        traveler = safe_db_operation(validate_traveler)(session['traveler_id'])
        
        if traveler:
            response.update({
                'authenticated': True,
                'user_type': 'traveler',
                'traveler': {
                    'id': traveler['id'],
                    'name': f"{traveler['first_name']} {traveler['last_name']}",
                    'passport': traveler['passport_no'],
                    'batch_id': traveler['batch_id']
                }
            })
            return jsonify(response)
        # Invalid traveler → clear session
        session.clear()
    
    return jsonify(response)

# ==================== 🔑 PASSWORD MANAGEMENT ====================
@bp.route('/change-password', methods=['POST'])
def change_password():
    """Change password for authenticated user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.json or {}
    old_password = data.get('old_password', '').strip()
    new_password = data.get('new_password', '').strip()
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': 'Password must be 6+ characters'}), 400
    
    def verify_and_update(conn, cursor, uid):
        # Verify old password
        cursor.execute('SELECT password FROM users WHERE id = %s', (uid,))
        user = cursor.fetchone()
        if not user or user['password'] != old_password:
            return False
        
        # Update password
        cursor.execute("""
            UPDATE users SET password = %s, updated_at = %s 
            WHERE id = %s
        """, (new_password, datetime.now(), uid))
        return True
    
    success = safe_db_operation(verify_and_update)(session['user_id'])
    
    if success:
        log_critical_action(
            session['user_id'], 
            'PASSWORD_CHANGE', 
            'Password updated successfully',
            get_client_ip()
        )
        return jsonify({'success': True, 'message': 'Password changed'})
    
    return jsonify({'success': False, 'error': 'Current password incorrect'}), 401

@bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Demo forgot password (logs request only)"""
    data = request.json or {}
    email = data.get('email', '').strip()
    
    if not email:
        return jsonify({'success': False, 'error': 'Email required'}), 400
    
    def find_user_by_email(conn, cursor, email_addr):
        cursor.execute('SELECT id FROM users WHERE email = %s', (email_addr,))
        return cursor.fetchone()
    
    user = safe_db_operation(find_user_by_email)(email)
    
    if user:
        log_critical_action(
            None,
            'FORGOT_PASSWORD',
            f'Password reset requested for {email}',
            get_client_ip()
        )
    
    # Always return success (security)
    return jsonify({
        'success': True,
        'message': 'If email exists, reset instructions sent (demo mode)'
    })

# ==================== 🔐 API TOKENS (Optional) ====================
@bp.route('/api-token', methods=['POST'])
def create_api_token():
    """Generate API token for integrations"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    token = secrets.token_hex(32)
    
    def create_token_record(conn, cursor, uid, tkn):
        # Create table with proper unique constraint
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_tokens (
                id SERIAL PRIMARY KEY, 
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                token TEXT UNIQUE NOT NULL, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP + INTERVAL '30 days'
            )
        """)
        cursor.execute("""
            INSERT INTO api_tokens (user_id, token) VALUES (%s, %s)
        """, (uid, tkn))
        return True
    
    success = safe_db_operation(create_token_record)(session['user_id'], token)
    
    if success:
        log_critical_action(
            session['user_id'], 
            'API_TOKEN_CREATED', 
            f'Token: {token[:16]}...', 
            get_client_ip()
        )
        return jsonify({'success': True, 'token': token, 'expires': '30 days'})
    
    return jsonify({'success': False, 'error': 'Token creation failed'}), 500
