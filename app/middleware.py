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
            
            db = get_db()
            cursor = db.cursor()
            cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
            user = cursor.fetchone()
            db.close()
            
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
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        db.close()
        
        if not user or user['role'] != 'super_admin':
            return jsonify({'success': False, 'error': 'Super admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def log_critical_action(user_id, action, details, ip_address=None):
    """Log all critical actions to database"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Create critical_logs table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS critical_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                timestamp TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            INSERT INTO critical_logs (user_id, action, details, ip_address, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, action, details, ip_address, datetime.now().isoformat()))
        
        db.commit()
        db.close()
    except Exception as e:
        print(f"Logging error: {e}")

def auto_backup():
    """Auto backup before critical operations"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Create backups directory if not exists
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
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
        
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'users': [dict(u) for u in users],
            'travelers': [dict(t) for t in travelers],
            'batches': [dict(b) for b in batches],
            'payments': [dict(p) for p in payments]
        }
        
        with open(f'{backup_dir}/{backup_name}', 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        db.close()
        return backup_name
    except Exception as e:
        print(f"Backup error: {e}")
        return None
