from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime, timedelta
import json
import hashlib
import secrets

bp = Blueprint('auth', __name__, url_prefix='/api')

# In production, use proper password hashing
# For demo, we'll keep simple but with a note

def hash_password(password):
    """Simple password hashing (replace with bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password, hashed_password):
    """Verify password (replace with bcrypt in production)"""
    return hash_password(plain_password) == hashed_password

@bp.route('/login', methods=['POST'])
def login():
    """Admin login with enhanced security"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    remember_me = data.get('remember_me', False)
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    # Get user with active status
    cursor.execute('''
        SELECT * FROM users 
        WHERE username = ? AND is_active = 1
    ''', (username,))
    
    user = cursor.fetchone()
    
    # Demo mode - simple password check
    # In production, use proper password verification
    if user and user['password'] == password:
        # Set session
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session.permanent = remember_me
        if remember_me:
            session.permanent_session_lifetime = timedelta(days=30)
        
        # Update last login
        cursor.execute('''
            UPDATE users 
            SET last_login = ? 
            WHERE id = ?
        ''', (datetime.now().isoformat(), user['id']))
        
        # Parse permissions
        permissions = {}
        if user['permissions']:
            try:
                permissions = json.loads(user['permissions'])
            except:
                permissions = {}
        
        # Log activity
        log_activity(user['id'], 'login', 'auth', f'User logged in from {request.remote_addr}', request.remote_addr)
        
        db.commit()
        db.close()
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'name': user['full_name'] or user['username'],
                'email': user['email'],
                'role': user['role'],
                'permissions': permissions
            },
            'redirect': '/admin/dashboard.html'
        })
    
    db.close()
    
    # Failed login - log attempt (optional)
    log_activity(None, 'failed_login', 'auth', f'Failed login attempt for username: {username}', request.remote_addr)
    
    return jsonify({'success': False, 'error': 'Invalid credentials or inactive account'}), 401

@bp.route('/traveler/login', methods=['POST'])
def traveler_login():
    """Traveler login using passport number and PIN with enhanced security"""
    data = request.json
    passport_no = data.get('passport_no', '').strip().upper()
    pin = data.get('pin', '').strip()
    
    if not passport_no or not pin:
        return jsonify({'success': False, 'error': 'Passport number and PIN required'}), 400
    
    if len(pin) != 4 or not pin.isdigit():
        return jsonify({'success': False, 'error': 'PIN must be exactly 4 digits'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT t.*, b.batch_name, b.departure_date, b.return_date, b.status as batch_status
        FROM travelers t
        LEFT JOIN batches b ON t.batch_id = b.id
        WHERE t.passport_no = ? AND t.pin = ?
    ''', (passport_no, pin))
    
    traveler = cursor.fetchone()
    
    if traveler:
        # Set traveler session
        session['traveler_id'] = traveler['id']
        session['traveler_name'] = f"{traveler['first_name']} {traveler['last_name']}"
        session['traveler_passport'] = traveler['passport_no']
        session.permanent = True
        session.permanent_session_lifetime = timedelta(hours=2)  # Short session for travelers
        
        # Get payment summary
        cursor.execute('''
            SELECT 
                COUNT(*) as payment_count,
                SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as total_paid,
                SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as total_pending
            FROM payments
            WHERE traveler_id = ?
        ''', (traveler['id'],))
        
        payment_summary = cursor.fetchone()
        
        # Log activity
        log_activity(None, 'traveler_login', 'auth', f'Traveler logged in: {traveler["first_name"]} {traveler["last_name"]}', request.remote_addr)
        
        db.close()
        
        return jsonify({
            'success': True,
            'traveler_id': traveler['id'],
            'name': f"{traveler['first_name']} {traveler['last_name']}",
            'passport': traveler['passport_no'],
            'batch_name': traveler['batch_name'],
            'payment_summary': {
                'total_paid': float(payment_summary['total_paid']) if payment_summary['total_paid'] else 0,
                'total_pending': float(payment_summary['total_pending']) if payment_summary['total_pending'] else 0,
                'payment_count': payment_summary['payment_count'] or 0
            },
            'message': 'Login successful'
        })
    
    db.close()
    
    # Failed login - log attempt
    log_activity(None, 'failed_traveler_login', 'auth', f'Failed traveler login attempt for passport: {passport_no}', request.remote_addr)
    
    return jsonify({'success': False, 'error': 'Invalid passport number or PIN'}), 401

@bp.route('/logout', methods=['POST'])
def logout():
    """User logout with cleanup"""
    user_id = session.get('user_id')
    traveler_id = session.get('traveler_id')
    
    if user_id:
        log_activity(user_id, 'logout', 'auth', 'User logged out', request.remote_addr)
    elif traveler_id:
        log_activity(None, 'traveler_logout', 'auth', f'Traveler ID {traveler_id} logged out', request.remote_addr)
    
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@bp.route('/check-session', methods=['GET'])
def check_session():
    """Check current session status"""
    response = {
        'success': True,
        'authenticated': False
    }
    
    if 'user_id' in session:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT id, username, full_name, email, role, permissions
            FROM users WHERE id = ? AND is_active = 1
        ''', (session['user_id'],))
        
        user = cursor.fetchone()
        db.close()
        
        if user:
            # Parse permissions
            permissions = {}
            if user['permissions']:
                try:
                    permissions = json.loads(user['permissions'])
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
            # User not found or inactive, clear session
            session.clear()
    
    elif 'traveler_id' in session:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT id, first_name, last_name, passport_no, batch_id
            FROM travelers WHERE id = ?
        ''', (session['traveler_id'],))
        
        traveler = cursor.fetchone()
        db.close()
        
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
        else:
            # Traveler not found, clear session
            session.clear()
    
    return jsonify(response)

@bp.route('/change-password', methods=['POST'])
def change_password():
    """Change password for logged in user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'success': False, 'error': 'Old and new password required'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': 'New password must be at least 6 characters'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT password FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    if not user or user['password'] != old_password:  # Simple check for demo
        db.close()
        return jsonify({'success': False, 'error': 'Current password is incorrect'}), 401
    
    cursor.execute('''
        UPDATE users 
        SET password = ?, updated_at = ?
        WHERE id = ?
    ''', (new_password, datetime.now().isoformat(), session['user_id']))
    
    log_activity(session['user_id'], 'password_change', 'auth', 'User changed password', request.remote_addr)
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})

@bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Handle forgot password request"""
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'error': 'Email required'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT id, username FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    db.close()
    
    if user:
        # In production, send email with reset link
        # For demo, just return success
        log_activity(user['id'], 'forgot_password', 'auth', 'Password reset requested', request.remote_addr)
    
    # Always return success to prevent email enumeration
    return jsonify({
        'success': True, 
        'message': 'If your email exists in our system, you will receive password reset instructions.'
    })

# Helper function to log activity
def log_activity(user_id, action, module, description, ip_address=None):
    """Log user activity"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO activity_log (user_id, action, module, description, ip_address) VALUES (?, ?, ?, ?, ?)',
            (user_id, action, module, description, ip_address)
        )
        db.commit()
        db.close()
    except:
        pass  # Fail silently

# Token generation for API (optional)
def generate_token(user_id):
    """Generate simple token for API authentication"""
    import secrets
    token = secrets.token_hex(32)
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO api_tokens (user_id, token, created_at)
        VALUES (?, ?, ?)
    ''', (user_id, token, datetime.now().isoformat()))
    db.commit()
    db.close()
    
    return token
