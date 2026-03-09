from functools import wraps
from flask import session, jsonify, request, g
from app.database import get_db, release_db  # ✅ Pool compatible
from datetime import datetime
import json
import os

# ====== 🔥 SAFE DB WRAPPER ======
def safe_db_operation(operation_func):
    """🔥 ZERO LEAKS - Pool safe wrapper for ALL middleware DB calls"""
    def wrapper(*args, **kwargs):
        conn = cursor = None
        try:
            conn, cursor = get_db()
            result = operation_func(conn, cursor, *args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            if conn: conn.rollback()
            print(f"❌ Middleware DB error: {e}")
            return None
        finally:
            release_db(conn, cursor)  # 🔥 CRITICAL
    return wrapper

# ====== 🔐 AUTH DECORATORS ======
def role_required(allowed_roles):
    """🔥 Pool-safe role check"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 401
            
            def check_role(conn, cursor, user_id):
                cursor.execute('SELECT role FROM users WHERE id = %s', (user_id,))
                user = cursor.fetchone()
                return user['role'] if user else None
            
            role = safe_db_operation(check_role)(session['user_id'])
            if not role:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            if role not in allowed_roles:
                return jsonify({'success': False, 'error': f'Requires: {allowed_roles}'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def super_admin_required(f):
    """🔥 Super admin only decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        def check_role(conn, cursor, user_id):
            cursor.execute('SELECT role FROM users WHERE id = %s', (user_id,))
            user = cursor.fetchone()
            return user['role'] if user else None
        
        role = safe_db_operation(check_role)(session['user_id'])
        if not role or role != 'super_admin':
            return jsonify({'success': False, 'error': 'Super admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    """🔥 Single pooled query to get full user details"""
    if 'user_id' not in session: 
        return None
    
    def fetch_user(conn, cursor, user_id):
        cursor.execute('''
            SELECT id, username, full_name, email, phone, department,
                   role, permissions, is_active, last_login, created_at
            FROM users 
            WHERE id = %s AND is_active = true
        ''', (user_id,))
        user = cursor.fetchone()
        
        if user:
            user_dict = dict(user)
            if user_dict.get('permissions'):
                try:
                    if isinstance(user_dict['permissions'], str):
                        user_dict['permissions'] = json.loads(user_dict['permissions'])
                except:
                    user_dict['permissions'] = {}
            return user_dict
        return None
    
    return safe_db_operation(fetch_user)(session['user_id'])

def has_permission(permission_name):
    """🔥 Check if current user has specific permission"""
    user = get_current_user()
    if not user:
        return False
    if user['role'] == 'super_admin':
        return True
    permissions = user.get('permissions', {})
    return permissions.get(permission_name, False)

def require_permission(permission_name):
    """🔥 Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 401
            if not has_permission(permission_name):
                return jsonify({
                    'success': False, 
                    'error': f'Permission denied. Required: {permission_name}'
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

# ====== 📊 LOGGING ======
def log_critical_action(user_id, action, details, ip_address=None):
    """🔥 Pool-safe critical action logging"""
    def log_action(conn, cursor, uid, act, det, ip):
        cursor.execute('''
            INSERT INTO critical_logs (user_id, action, description, ip_address, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        ''', (uid, act, det, ip or get_client_ip(), datetime.now()))
    
    safe_db_operation(log_action)(user_id, action, details, ip_address)

def log_user_activity(action, module, description):
    """🔥 Log general user activity"""
    user_id = session.get('user_id')
    if not user_id:
        return
    
    def log_activity(conn, cursor, uid, act, mod, desc, ip):
        cursor.execute('''
            INSERT INTO activity_log (user_id, action, module, description, ip_address, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (uid, act, mod, desc, ip, datetime.now()))
    
    safe_db_operation(log_activity)(user_id, action, module, description, get_client_ip())

# ====== 🌍 IP HELPERS ======
def get_client_ip():
    """🔥 Railway proxy aware IP detection"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr

# ====== 🩺 HEALTH CHECK ======
def check_database_connection():
    """🔥 Quick database health check"""
    def ping_db(conn, cursor):
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return True
    
    return safe_db_operation(ping_db)() is not False

# ====== 📦 EXPORTS ======
__all__ = [
    'role_required',
    'super_admin_required',
    'get_current_user',
    'has_permission',
    'require_permission',
    'log_critical_action',
    'log_user_activity',
    'get_client_ip',
    'safe_db_operation',
    'check_database_connection'
]
