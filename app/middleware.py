from functools import wraps
from flask import session, jsonify, request, g
from app.database import get_db, release_db  # ✅ Pool compatible
from datetime import datetime
import json
import os

# ==================== 🔥 SAFE DB WRAPPER ====================
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

# ==================== 🔐 AUTH DECORATORS ====================
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
            if role not in allowed_roles:
                return jsonify({'success': False, 'error': f'Requires: {allowed_roles}'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def get_current_user():
    """🔥 Single pooled query"""
    if 'user_id' not in session: return None
    
    def fetch_user(conn, cursor, user_id):
        cursor.execute('SELECT * FROM users WHERE id = %s AND is_active = true', (user_id,))
        user = cursor.fetchone()
        return dict(user) if user else None
    
    return safe_db_operation(fetch_user)(session['user_id'])

# ==================== 📊 LOGGING ====================
def log_critical_action(user_id, action, details):
    """🔥 Pool-safe logging"""
    def log_action(conn, cursor, uid, act, det):
        cursor.execute('INSERT INTO critical_logs (user_id, action, description, ip_address, timestamp) VALUES (%s,%s,%s,%s,%s)', 
                      (uid, act, det, request.remote_addr, datetime.now()))
    safe_db_operation(log_action)(user_id, action, details)

def get_client_ip():
    """Railway proxy aware"""
    return request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

__all__ = ['role_required', 'get_current_user', 'log_critical_action', 'safe_db_operation', 'get_client_ip']
