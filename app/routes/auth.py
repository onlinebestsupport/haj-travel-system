from flask import Blueprint, request, jsonify, session, current_app
from app.database import get_db, release_db
from datetime import datetime, timedelta
import hashlib
import uuid
import hmac
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint('auth', __name__, url_prefix='/api')

# ====== PASSWORD HASHING ======
def hash_password(password):
    """Hash a password using werkzeug security"""
    return generate_password_hash(password)

ddef verify_password(password, password_hash):
    """Verify a password against its hash"""
    if not password_hash:
        return False
    
    # Check if it's a werkzeug hash (starts with pbkdf2:sha256)
    if password_hash.startswith('pbkdf2:sha256'):
        return check_password_hash(password_hash, password)
    # Check if it's a bcrypt hash (starts with $2)
    elif password_hash.startswith('$2'):
        return check_password_hash(password_hash, password)
    else:
        # Legacy plain text comparison
        return password == password_hash

def migrate_password_to_hash(conn, cursor, user_id, plain_password):
    """Migrate a user from plain text to hashed password"""
    password_hash = hash_password(plain_password)
    cursor.execute(
        "UPDATE users SET password_hash = %s, password_updated_at = %s WHERE id = %s",
        (password_hash, datetime.now(), user_id)
    )
    conn.commit()
    print(f"✅ Migrated user {user_id} to hashed password")

@bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and create session"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    conn, cursor = get_db()
    try:
        # Check users table (admin/staff)
        cursor.execute('''
            SELECT id, username, password_hash, password, role, name, email, is_active 
            FROM users WHERE username = %s AND is_active = true
        ''', (username,))
        user = cursor.fetchone()
        
        if user:
            # Check password (handle both hashed and legacy plain text)
            password_valid = False
            password_hash = user.get('password_hash')
            
            if password_hash:
                # Hashed password exists
                password_valid = verify_password(password, password_hash)
            else:
                # Legacy plain text password - verify and migrate
                plain_password = user.get('password')
                if plain_password and password == plain_password:
                    password_valid = True
                    # Migrate to hashed password
                    migrate_password_to_hash(conn, cursor, user['id'], password)
            
            if password_valid:
                # Create session
                session.permanent = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                session['name'] = user.get('name', username)
                session['login_time'] = datetime.now().isoformat()
                
                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = %s WHERE id = %s",
                    (datetime.now(), user['id'])
                )
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'authenticated': True,
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'name': user.get('name', username),
                        'email': user.get('email'),
                        'role': user['role']
                    },
                    'session_expiry': (datetime.now() + current_app.permanent_session_lifetime).isoformat()
                })
        
        # Check travelers table (pilgrims)
        cursor.execute('''
            SELECT id, first_name, last_name, passport_no, email, mobile 
            FROM travelers WHERE passport_no = %s
        ''', (username,))
        traveler = cursor.fetchone()
        
        if traveler:
            # Travelers use passport number as username and don't have passwords
            # For demo, they can login with any password
            session.permanent = True
            session['traveler_id'] = traveler['id']
            session['traveler_name'] = f"{traveler['first_name']} {traveler['last_name']}"
            session['traveler_passport'] = traveler['passport_no']
            
            return jsonify({
                'success': True,
                'authenticated': True,
                'traveler': {
                    'id': traveler['id'],
                    'name': f"{traveler['first_name']} {traveler['last_name']}",
                    'passport': traveler['passport_no'],
                    'email': traveler.get('email'),
                    'mobile': traveler.get('mobile')
                },
                'session_expiry': (datetime.now() + current_app.permanent_session_lifetime).isoformat()
            })
        
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)

@bp.route('/logout', methods=['POST'])
def logout():
    """Clear user session"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@bp.route('/check-session', methods=['GET'])
def check_session():
    """Check if user is authenticated"""
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user_id': session['user_id'],
            'username': session.get('username'),
            'name': session.get('name'),
            'role': session.get('role'),
            'type': 'admin'
        })
    elif 'traveler_id' in session:
        return jsonify({
            'authenticated': True,
            'traveler_id': session['traveler_id'],
            'traveler_name': session.get('traveler_name'),
            'type': 'traveler'
        })
    else:
        return jsonify({'authenticated': False}), 200

@bp.route('/change-password', methods=['POST'])
def change_password():
    """Change user password (authenticated users only)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'error': 'Current and new password required'}), 400
    
    conn, cursor = get_db()
    try:
        cursor.execute(
            'SELECT password_hash, password FROM users WHERE id = %s',
            (session['user_id'],)
        )
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Verify current password
        password_valid = False
        password_hash = user.get('password_hash')
        
        if password_hash:
            password_valid = verify_password(current_password, password_hash)
        else:
            # Legacy plain text
            password_valid = (user.get('password') == current_password)
        
        if not password_valid:
            return jsonify({'success': False, 'error': 'Current password is incorrect'}), 401
        
        # Update to new hashed password
        new_password_hash = hash_password(new_password)
        cursor.execute(
            'UPDATE users SET password_hash = %s, password_updated_at = %s WHERE id = %s',
            (new_password_hash, datetime.now(), session['user_id'])
        )
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)

# ====== PASSWORD RESET TOKENS ======
@bp.route('/reset-password-request', methods=['POST'])
def reset_password_request():
    """Request password reset (generates token)"""
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'error': 'Email required'}), 400
    
    conn, cursor = get_db()
    try:
        cursor.execute('SELECT id, username FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        
        if not user:
            # Don't reveal that email doesn't exist
            return jsonify({'success': True, 'message': 'If email exists, reset link will be sent'})
        
        # Generate reset token
        token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(hours=24)
        
        cursor.execute(
            'UPDATE users SET reset_token = %s, reset_token_expires = %s WHERE id = %s',
            (token, expires, user['id'])
        )
        conn.commit()
        
        # TODO: Send email with reset link
        print(f"🔐 Password reset token for {email}: {token}")
        
        return jsonify({'success': True, 'message': 'Reset link sent to email'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)

@bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using token"""
    data = request.json
    token = data.get('token')
    new_password = data.get('new_password')
    
    if not token or not new_password:
        return jsonify({'success': False, 'error': 'Token and new password required'}), 400
    
    conn, cursor = get_db()
    try:
        cursor.execute(
            'SELECT id FROM users WHERE reset_token = %s AND reset_token_expires > %s',
            (token, datetime.now())
        )
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 400
        
        # Update password
        new_password_hash = hash_password(new_password)
        cursor.execute(
            'UPDATE users SET password_hash = %s, reset_token = NULL, reset_token_expires = NULL, password_updated_at = %s WHERE id = %s',
            (new_password_hash, datetime.now(), user['id'])
        )
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Password reset successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)
