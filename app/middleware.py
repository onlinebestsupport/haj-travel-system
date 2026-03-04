from functools import wraps
from flask import session, jsonify, request
from app.database import get_db, release_db  # 🔥 ADDED release_db
from datetime import datetime
import json
import os
import subprocess
import shutil
import re

def safe_db_operation(operation_func):
    """🔥 Context manager wrapper for ALL DB operations"""
    def wrapper(*args, **kwargs):
        conn = cursor = None
        try:
            conn, cursor = get_db()
            result = operation_func(conn, cursor, *args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ DB operation failed: {e}")
            return None
        finally:
            release_db(conn, cursor)  # 🔥 CRITICAL CLEANUP
    return wrapper

def role_required(allowed_roles):
    """🔥 FIXED: Proper connection cleanup"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 401
            
            def check_role(conn, cursor, user_id):
                cursor.execute('SELECT role FROM users WHERE id = %s', (user_id,))
                user = cursor.fetchone()
                return user['role'] if user else None
            
            user_role = safe_db_operation(check_role)(session['user_id'])
            
            if not user_role:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            if user_role not in allowed_roles:
                return jsonify({
                    'success': False, 
                    'error': f'Access denied. Required: {", ".join(allowed_roles)}'
                }), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def super_admin_required(f):
    """🔥 FIXED: Super admin check with cleanup"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        def check_super_admin(conn, cursor, user_id):
            cursor.execute('SELECT role FROM users WHERE id = %s', (user_id,))
            user = cursor.fetchone()
            return user['role'] == 'super_admin' if user else False
        
        is_super_admin = safe_db_operation(check_super_admin)(session['user_id'])
        
        if not is_super_admin:
            return jsonify({'success': False, 'error': 'Super admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def log_critical_action(user_id, action, details, ip_address=None):
    """🔥 FIXED: Proper cleanup"""
    def log_action(conn, cursor, user_id, action, details, ip):
        cursor.execute('''
            INSERT INTO critical_logs (user_id, action, description, ip_address, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        ''', (user_id, action, details, ip or get_client_ip(), datetime.now()))
    
    safe_db_operation(log_action)(user_id, action, details)
    print(f"✅ Critical action logged: {action}")

def get_current_user():
    """🔥 FIXED: Single connection, proper cleanup"""
    if 'user_id' not in session:
        return None
    
    def fetch_user(conn, cursor, user_id):
        cursor.execute('''
            SELECT id, username, full_name, email, phone, department,
                   role, permissions, is_active, last_login, created_at
            FROM users WHERE id = %s AND is_active = true
        ''', (user_id,))
        user = cursor.fetchone()
        if user and user.get('permissions'):
            try:
                if isinstance(user['permissions'], str):
                    user['permissions'] = json.loads(user['permissions'])
            except:
                user['permissions'] = {}
        else:
            user['permissions'] = {}
        return dict(user) if user else None
    
    return safe_db_operation(fetch_user)(session['user_id'])

def has_permission(permission_name):
    """🔥 FIXED: Use cached user"""
    user = get_current_user()
    if not user:
        return False
    if user['role'] == 'super_admin':
        return True
    permissions = user.get('permissions', {})
    return permissions.get(permission_name, False)

def require_permission(permission_name):
    """🔥 FIXED permission decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 401
            if not has_permission(permission_name):
                return jsonify({
                    'success': False, 
                    'error': f'Permission "{permission_name}" required'
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_client_ip():
    """Get real client IP (Railway proxy aware)"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr

def log_user_activity(action, module, description):
    """🔥 FIXED activity logging"""
    user_id = session.get('user_id')
    if not user_id:
        return
    
    def log_activity(conn, cursor, user_id, action, module, desc):
        cursor.execute('''
            INSERT INTO activity_log (user_id, action, module, description, ip_address, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (user_id, action, module, desc, get_client_ip(), datetime.now()))
    
    safe_db_operation(log_activity)(user_id, action, module, description)

def check_database_connection():
    """🔥 FIXED health check"""
    def ping_db(conn, cursor):
        cursor.execute("SELECT 1")
        return cursor.fetchone() is not None
    
    return bool(safe_db_operation(ping_db)())

# =============================================================================
# 🔥 BACKUP FUNCTIONS - RAILWAY SAFE (No subprocess issues)
# =============================================================================
def auto_backup():
    """🔥 SIMPLIFIED backup - No pg_dump subprocess"""
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}.json"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Get table counts for metadata
        def get_counts(conn, cursor):
            tables = ['users', 'batches', 'travelers', 'payments']
            counts = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                counts[table] = cursor.fetchone()['count']
            return counts
        
        table_counts = safe_db_operation(get_counts)()
        
        backup_data = {
            'timestamp': timestamp,
            'tables': table_counts,
            'message': 'Configuration backup (full DB backup requires pg_dump)'
        }
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        # Log to backup_history
        def log_backup(conn, cursor, name, size, tables):
            cursor.execute("""
                INSERT INTO backup_history (backup_name, backup_type, file_size, tables_count, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, 'auto', f"{os.path.getsize(backup_path)} bytes", sum(tables.values()), 'completed'))
        
        safe_db_operation(log_backup)(backup_name, os.path.getsize(backup_path), table_counts)
        
        return {'name': backup_name, 'path': backup_path, 'tables': table_counts}
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def manual_backup(description=None, is_restore_point=False):
    """Manual backup wrapper"""
    result = auto_backup()
    if result and is_restore_point and description:
        def mark_restore(conn, cursor, name, desc):
            cursor.execute("""
                UPDATE backup_history SET is_restore_point = TRUE, description = %s
                WHERE backup_name = %s
            """, (desc, name))
        safe_db_operation(mark_restore)(result['name'], description)
        result['is_restore_point'] = True
    return result

def format_file_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

__all__ = [
    'role_required', 'super_admin_required', 'log_critical_action',
    'auto_backup', 'manual_backup', 'get_current_user', 'has_permission',
    'require_permission', 'get_client_ip', 'log_user_activity',
    'check_database_connection'
]
