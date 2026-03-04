from flask import Blueprint, request, jsonify, session, current_app
from app.database import get_db, release_db
from app.middleware import log_critical_action, get_client_ip
from datetime import datetime, timedelta
import json
import hashlib

bp = Blueprint('auth', __name__, url_prefix='/api')

def verify_password(plain_password, stored_password):
    """Verify plain password match (your current DB schema)"""
    return plain_password == stored_password

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
            release_db(conn, cursor)
    return wrapper

@bp.route('/login', methods=['POST'])
def login():
    """🔥 LOGIN with session persistence fix - Matches server.py"""
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    remember_me = data.get('remember_me', False)  # Default to False for 30 min sessions
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    def find_user(conn, cursor, uname):
        cursor.execute("""
            SELECT id, username, full_name, email, role, permissions, is_active, password,
                   last_login
            FROM users WHERE username = %s AND is_active = true
        """, (uname,))
        return cursor.fetchone()
    
    user = safe_db_operation(find_user)(username)
    
    if user and verify_password(password, user['password']):
        # 🔥 CRITICAL: Clear any existing session first
        session.clear()
        
        # Set session
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['name'] = user['full_name'] or user['username']
        session.permanent = True
        
        # Set session expiry based on remember_me
        if remember_me:
            # 7 days for remember me
            current_app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
        else:
            # 30 minutes for regular session
            current_app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
        
        # 🔥 FORCE SESSION TO SAVE - THIS IS CRITICAL
        session.modified = True
        
        # Update last login
        def update_last_login(conn, cursor, uid):
            cursor.execute(
                "UPDATE users SET last_login = %s WHERE id = %s",
                (datetime.now(), uid)
            )
        
        safe_db_operation(update_last_login)(user['id'])
        
        # Parse permissions
        permissions = {}
        if user['permissions']:
            try:
                permissions = json.loads(user['permissions']) if isinstance(user['permissions'], str) else user['permissions']
            except:
                permissions = {}
        
        log_critical_action(user['id'], 'LOGIN_SUCCESS', f'Admin login from {get_client_ip()}')
        
        # Calculate session expiry for frontend
        session_expiry = (datetime.now() + (timedelta(days=7) if remember_me else timedelta(minutes=30))).isoformat()
        
        return jsonify({
            'success': True,
            'authenticated': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'name': user['full_name'] or user['username'],
                'email': user['email'],
                'role': user['role'],
                'permissions': permissions,
                'last_login': user['last_login'].isoformat() if user['last_login'] else None
            },
            'session_expiry': session_expiry
        })
    
    log_critical_action(None, 'LOGIN_FAILED', f'Failed login attempt: {username} from {get_client_ip()}')
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@bp.route('/check-session', methods=['GET'])
def check_session():
    """🔥 Session validation with auto-refresh - Used by SessionManager"""
    response = {'success': True, 'authenticated': False}
    
    if session.get('user_id'):
        def validate_user(conn, cursor, uid):
            cursor.execute("""
                SELECT id, username, full_name as name, email, role, permissions, is_active
                FROM users WHERE id = %s AND is_active = true
            """, (uid,))
            return cursor.fetchone()
        
        user = safe_db_operation(validate_user)(session['user_id'])
        
        if user:
            # 🔥 Refresh session on every check
            session.modified = True
            
            # Parse permissions
            permissions = {}
            if user['permissions']:
                try:
                    permissions = json.loads(user['permissions']) if isinstance(user['permissions'], str) else user['permissions']
                except:
                    permissions = {}
            
            # Calculate session expiry
            expiry = None
            if session.permanent:
                # Get session expiry from cookie if available
                if hasattr(session, '_permanent_session_expiry'):
                    expiry = datetime.fromtimestamp(session._permanent_session_expiry).isoformat()
                else:
                    expiry = (datetime.now() + current_app.config['PERMANENT_SESSION_LIFETIME']).isoformat()
            
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'name': user['name'],
                    'email': user['email'],
                    'role': user['role'],
                    'permissions': permissions
                },
                'session_expiry': expiry
            })
        else:
            # User not found or inactive - clear session
            session.clear()
            return jsonify({'authenticated': False}), 401
    
    elif session.get('traveler_id'):
        # Traveler session
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session['traveler_id'],
                'name': session.get('traveler_name', 'Traveler'),
                'passport': session.get('traveler_passport', ''),
                'role': 'traveler'
            }
        })
    
    return jsonify({'authenticated': False}), 401

@bp.route('/logout', methods=['POST'])
def logout():
    """Clean logout with logging - Matches server.py"""
    user_id = session.get('user_id')
    
    if user_id:
        # Log logout action
        def log_logout(conn, cursor, uid):
            cursor.execute("""
                INSERT INTO activity_log (user_id, action, description, ip_address, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (uid, 'LOGOUT', f'User logged out', get_client_ip(), datetime.now()))
        
        safe_db_operation(log_logout)(user_id)
        log_critical_action(user_id, 'LOGOUT', f'User logged out from {get_client_ip()}')
    
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@bp.route('/session/status', methods=['GET'])
def session_status():
    """Get current session status (for debugging)"""
    if not session.get('user_id'):
        return jsonify({
            'authenticated': False,
            'message': 'No active session'
        })
    
    # Calculate session expiry
    expiry = None
    if session.permanent:
        if hasattr(session, '_permanent_session_expiry'):
            expiry = datetime.fromtimestamp(session._permanent_session_expiry).isoformat()
        else:
            expiry = (datetime.now() + current_app.config['PERMANENT_SESSION_LIFETIME']).isoformat()
    
    # Calculate time remaining
    remaining = None
    if expiry:
        try:
            expiry_dt = datetime.fromisoformat(expiry)
            remaining_seconds = (expiry_dt - datetime.now()).total_seconds()
            if remaining_seconds > 0:
                minutes = int(remaining_seconds // 60)
                seconds = int(remaining_seconds % 60)
                remaining = f"{minutes}m {seconds}s"
            else:
                remaining = "Expired"
        except:
            pass
    
    return jsonify({
        'authenticated': True,
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'name': session.get('name'),
        'role': session.get('role'),
        'session_permanent': session.permanent,
        'session_expiry': expiry,
        'time_remaining': remaining
    })

@bp.route('/change-password', methods=['POST'])
def change_password():
    """Change password for authenticated user"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.json or {}
    old_password = data.get('old_password', '').strip()
    new_password = data.get('new_password', '').strip()
    
    if not old_password or not new_password:
        return jsonify({'success': False, 'error': 'Old and new password required'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': 'New password must be at least 6 characters'}), 400
    
    def verify_and_change(conn, cursor, uid, old, new):
        # Get current password
        cursor.execute("SELECT password FROM users WHERE id = %s", (uid,))
        user = cursor.fetchone()
        
        if not user or not verify_password(old, user['password']):
            return {'error': 'Current password is incorrect'}
        
        # Update password
        cursor.execute(
            "UPDATE users SET password = %s, updated_at = %s WHERE id = %s",
            (new, datetime.now(), uid)
        )
        return {'success': True}
    
    result = safe_db_operation(verify_and_change)(session['user_id'], old_password, new_password)
    
    if result and 'error' in result:
        return jsonify({'success': False, 'error': result['error']}), 400
    
    log_critical_action(session['user_id'], 'PASSWORD_CHANGE', 'User changed password', get_client_ip())
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})

@bp.route('/refresh-session', methods=['POST'])
def refresh_session():
    """Manually refresh session - called by frontend on activity"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    # Refresh session
    session.modified = True
    
    # Calculate new expiry
    expiry = (datetime.now() + current_app.config['PERMANENT_SESSION_LIFETIME']).isoformat()
    
    return jsonify({
        'success': True,
        'message': 'Session refreshed',
        'session_expiry': expiry
    })
