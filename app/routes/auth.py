from flask import Blueprint, request, jsonify, session
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle admin login"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        # Demo credentials - in production, check against database
        valid_users = {
            'superadmin': 'admin123',
            'admin1': 'admin123',
            'manager1': 'admin123'
        }
        
        if username in valid_users and valid_users[username] == password:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['admin_name'] = username
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'redirect': '/admin/dashboard',
                'user': {
                    'name': username,
                    'roles': ['admin']
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Handle logout"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})
