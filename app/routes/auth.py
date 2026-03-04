from flask import Blueprint, request, jsonify, session
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
    """🔥 LOGIN with session persistence fix"""
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    remember_me = data.get('remember_me', True)
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    def find_user(conn, cursor, uname):
        cursor.execute("""
            SELECT id, username, full_name, email, role, permissions, is_active, password 
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
        session.permanent = remember_me
        
        # 🔥 FORCE SESSION TO SAVE - THIS IS CRITICAL
        session.modified = True
        
        # Parse permissions
        permissions = {}
        if user['permissions']:
            try:
                permissions = json.loads(user['permissions']) if isinstance(user['permissions'], str) else user['permissions']
            except:
                permissions = {}
        
        log_critical_action(user['id'], 'LOGIN_SUCCESS', f'Admin login from {get_client_ip()}')
        
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
    
    log_critical_action(None, 'LOGIN_FAILED', f'Failed login attempt: {username}')
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@bp.route('/check-session', methods=['GET'])
def check_session():
    """🔥 Session validation with auto-refresh"""
    response = {'success': True, 'authenticated': False}
    
    if session.get('user_id'):
        def validate_user(conn, cursor, uid):
            cursor.execute("""
                SELECT id, username, full_name, email, role, permissions
                FROM users WHERE id = %s AND is_active = true
            """, (uid,))
            return cursor.fetchone()
        
        user = safe_db_operation(validate_user)(session['user_id'])
        
        if user:
            # 🔥 Refresh session on every check
            session.modified = True
            session.permanent = True
            
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
        else:
            session.clear()
    
    return jsonify(response)

@bp.route('/logout', methods=['POST'])
def logout():
    """Clean logout"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})
