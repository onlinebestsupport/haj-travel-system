from flask import Blueprint, request, jsonify, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import psycopg2
import os
from dotenv import load_dotenv
import traceback
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# Setup logger instead of print statements
logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__, url_prefix='/api')
limiter = Limiter(key_func=get_remote_address)

@bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limit: 5 attempts per minute
def login():
    """Authenticate user with username and password (hashed)"""
    data = request.json
    username = data.get('username', '').strip() if data else ''
    password = data.get('password', '') if data else ''
    
    if not username or not password:
        logger.warning(f"Login attempt with missing credentials from {get_remote_address()}")
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    try:
        # Direct PostgreSQL connection
        load_dotenv()
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()
        
        # Query user with hashed password
        cursor.execute(
            "SELECT id, username, password, name, role, is_active FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user:
            user_id, user_username, user_password_hash, user_name, user_role, is_active = user
            
            # Verify password using hashing
            if check_password_hash(user_password_hash, password) and is_active:
                session.clear()
                session.permanent = True
                session['user_id'] = user_id
                session['username'] = user_username
                session['name'] = user_name
                session['role'] = user_role
                
                logger.info(f"User {user_username} logged in successfully")
                
                return jsonify({
                    'success': True,
                    'authenticated': True,
                    'user': {
                        'id': user_id,
                        'username': user_username,
                        'name': user_name,
                        'role': user_role
                    }
                })
            else:
                logger.warning(f"Failed login attempt for user {username} from {get_remote_address()}")
                return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        else:
            logger.warning(f"Login attempt with non-existent user {username} from {get_remote_address()}")
            return jsonify({'success': False, 'error': 'User not found'}), 401
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': 'An error occurred during login'}), 500

@bp.route('/logout', methods=['POST'])
def logout():
    """Clear user session and log out"""
    try:
        username = session.get('username', 'Unknown')
        session.clear()
        logger.info(f"User {username} logged out")
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/check-session', methods=['GET'])
def check_session():
    """Check if user has an active session"""
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user_id': session['user_id'],
            'username': session.get('username'),
            'name': session.get('name'),
            'role': session.get('role')
        })
    else:
        return jsonify({'authenticated': False}), 200
