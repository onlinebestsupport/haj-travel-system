from functools import wraps
from flask import session, jsonify, request
from app.database import get_db
from datetime import datetime
import json
import os

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
        
        # Create critical_logs table if not exists (using PostgreSQL syntax)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS critical_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO critical_logs (user_id, action, details, ip_address, timestamp)
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
    """Auto backup before critical operations"""
    try:
        conn, cursor = get_db()
        
        # Create backups directory if not exists
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            print(f"📁 Created backup directory: {backup_dir}")
        
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Backup users table
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        # Backup travelers table
        cursor.execute("SELECT * FROM travelers")
        travelers = cursor.fetchall()
        
        # Backup batches table
        cursor.execute("SELECT * FROM batches")
        batches = cursor.fetchall()
        
        # Backup payments table
        cursor.execute("SELECT * FROM payments")
        payments = cursor.fetchall()
        
        # Backup invoices table
        cursor.execute("SELECT * FROM invoices")
        invoices = cursor.fetchall()
        
        # Backup receipts table
        cursor.execute("SELECT * FROM receipts")
        receipts = cursor.fetchall()
        
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'users': [dict(u) for u in users],
            'travelers': [dict(t) for t in travelers],
            'batches': [dict(b) for b in batches],
            'payments': [dict(p) for p in payments],
            'invoices': [dict(i) for i in invoices],
            'receipts': [dict(r) for r in receipts]
        }
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        cursor.close()
        conn.close()
        
        # Log the backup
        log_critical_action(
            session.get('user_id'), 
            'AUTO_BACKUP', 
            f'Created backup: {backup_name}',
            request.remote_addr if request else None
        )
        
        print(f"✅ Backup created: {backup_name}")
        return backup_name
        
    except Exception as e:
        print(f"❌ Backup error: {e}")
        return None

def get_current_user():
    """Helper function to get current user details"""
    if 'user_id' not in session:
        return None
    
    try:
        conn, cursor = get_db()
        cursor.execute('''
            SELECT id, username, full_name, role, permissions 
            FROM users WHERE id = %s
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
                except:
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

__all__ = [
    'role_required', 
    'super_admin_required', 
    'log_critical_action', 
    'auto_backup',
    'get_current_user',
    'has_permission'
]
