from flask import Blueprint, request, jsonify, session, current_app
from app.database import get_db, release_db
from datetime import datetime
import secrets
import traceback

bp = Blueprint('auth', __name__, url_prefix='/api')

@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    try:
        conn, cursor = get_db()
        
        # Use the 'name' column (not full_name)
        cursor.execute('''
            SELECT id, username, password, role, name, email, is_active 
            FROM users WHERE username = %s AND is_active = true
        ''', (username,))
        user = cursor.fetchone()
        
        if user:
            stored_password = user['password']
            if stored_password == password:
                session.clear()
                session.permanent = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                session['name'] = user['name']
                session['login_time'] = datetime.now().isoformat()
                
                return jsonify({
                    'success': True,
                    'authenticated': True,
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'name': user['name'],
                        'email': user['email'],
                        'role': user['role']
                    }
                })
        
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)

@bp.route('/logout', methods=['POST'])
def logout():
    try:
        session.clear()
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/check-session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user_id': session['user_id'],
            'username': session.get('username'),
            'name': session.get('name'),
            'role': session.get('role')
        })
    elif 'traveler_id' in session:
        return jsonify({
            'authenticated': True,
            'traveler_id': session['traveler_id'],
            'traveler_name': session.get('traveler_name')
        })
    else:
        return jsonify({'authenticated': False}), 200