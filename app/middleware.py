from functools import wraps
from flask import session, jsonify, request
from app.database import get_db
from datetime import datetime
import json
import os
import subprocess
import shutil

def role_required(allowed_roles):
    """
    Decorator to check if user has required role
    Usage: @role_required(['super_admin', 'admin'])
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 401
            
            conn, cursor = get_db()
            cursor.execute('SELECT role FROM users WHERE id = %s', (session['user_id'],))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            if user['role'] not in allowed_roles:
                return jsonify({
                    'success': False, 
                    'error': f'Access denied. Required role: {", ".join(allowed_roles)}'
                }), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def super_admin_required(f):
    """Decorator for super_admin only access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        conn, cursor = get_db()
        cursor.execute('SELECT role FROM users WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user or user['role'] != 'super_admin':
            return jsonify({'success': False, 'error': 'Super admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def log_critical_action(user_id, action, details, ip_address=None):
    """Log all critical actions to database"""
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        cursor.execute('''
            INSERT INTO critical_logs (user_id, action, description, ip_address, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        ''', (user_id, action, details, ip_address, datetime.now()))
        
        conn.commit()
        print(f"✅ Critical action logged: {action}")
        
    except Exception as e:
        print(f"❌ Logging error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def auto_backup():
    """Create automatic database backup with PostgreSQL pg_dump"""
    try:
        from flask import current_app
        
        # Get database URL from environment
        import os
        DATABASE_URL = os.environ.get('DATABASE_URL')
        
        if not DATABASE_URL:
            print("❌ DATABASE_URL not found")
            return None
        
        # Parse database URL
        # Format: postgresql://user:password@host:port/database
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
        if not match:
            print("❌ Could not parse DATABASE_URL")
            return None
        
        user, password, host, port, database = match.groups()
        
        # Create backups directory
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            print(f"📁 Created backup directory: {backup_dir}")
        
        # Generate backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}.sql"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Set PGPASSWORD environment variable for password
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        # Run pg_dump command
        cmd = [
            'pg_dump',
            '-h', host,
            '-p', str(port),
            '-U', user,
            '-d', database,
            '-F', 'c',  # Custom format (compressed)
            '-f', backup_path
        ]
        
        print(f"🔄 Running pg_dump: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ pg_dump failed: {result.stderr}")
            return None
        
        # Get file size
        file_size = os.path.getsize(backup_path)
        size_str = format_file_size(file_size)
        
        print(f"✅ Backup created: {backup_name} ({size_str})")
        
        # Get table count
        conn, cursor = get_db()
        cursor.execute("""
            SELECT COUNT(*) as count FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables_count = cursor.fetchone()['count']
        cursor.close()
        conn.close()
        
        # Save to backup_history table
        conn, cursor = get_db()
        cursor.execute("""
            INSERT INTO backup_history (
                backup_name, backup_type, file_size, tables_count, 
                status, location, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            backup_name,
            'auto',
            size_str,
            tables_count,
            'completed',
            backup_path,
            datetime.now()
        ))
        backup_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'id': backup_id,
            'name': backup_name,
            'path': backup_path,
            'size': size_str,
            'tables': tables_count
        }
        
    except Exception as e:
        print(f"❌ Backup error: {e}")
        return None

def manual_backup(description=None, is_restore_point=False):
    """Create manual backup or restore point"""
    try:
        result = auto_backup()  # Reuse auto_backup logic
        
        if result and is_restore_point:
            # Update as restore point
            conn, cursor = get_db()
            cursor.execute("""
                UPDATE backup_history 
                SET is_restore_point = TRUE, description = %s
                WHERE id = %s
            """, (description, result['id']))
            conn.commit()
            cursor.close()
            conn.close()
            result['is_restore_point'] = True
            result['description'] = description
        
        return result
        
    except Exception as e:
        print(f"❌ Manual backup error: {e}")
        return None

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def get_current_user():
    """Helper function to get current user details"""
    if 'user_id' not in session:
        return None
    
    try:
        conn, cursor = get_db()
        cursor.execute('''
            SELECT id, username, full_name, email, phone, department,
                   role, permissions, is_active, last_login, created_at
            FROM users 
            WHERE id = %s AND is_active = true
        ''', (session['user_id'],))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            user_dict = dict(user)
            if user_dict.get('permissions'):
                try:
                    if isinstance(user_dict['permissions'], str):
                        user_dict['permissions'] = json.loads(user_dict['permissions'])
                except Exception as e:
                    print(f"⚠️ Error parsing permissions: {e}")
                    user_dict['permissions'] = {}
            else:
                user_dict['permissions'] = {}
            return user_dict
        return None
    except Exception as e:
        print(f"❌ Error getting current user: {e}")
        return None

def has_permission(permission_name):
    """Check if current user has specific permission"""
    user = get_current_user()
    if not user:
        return False
    
    if user['role'] == 'super_admin':
        return True
    
    permissions = user.get('permissions', {})
    return permissions.get(permission_name, False)

def require_permission(permission_name):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 401
            
            if not has_permission(permission_name):
                return jsonify({
                    'success': False, 
                    'error': f'Permission denied. Required: {permission_name}'
                }), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_client_ip():
    """Get client IP address from request"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr

def log_user_activity(action, module, description):
    """Log general user activity"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return
        
        conn, cursor = get_db()
        cursor.execute('''
            INSERT INTO activity_log (user_id, action, module, description, ip_address, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (user_id, action, module, description, get_client_ip(), datetime.now()))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Activity log error: {e}")

def check_database_connection():
    """Check if database connection is healthy"""
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection check failed: {e}")
        return False

__all__ = [
    'role_required', 
    'super_admin_required', 
    'log_critical_action', 
    'auto_backup',
    'manual_backup',
    'get_current_user',
    'has_permission',
    'require_permission',
    'get_client_ip',
    'log_user_activity',
    'check_database_connection'
]
