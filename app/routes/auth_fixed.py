from flask import Blueprint, request, jsonify, session
import psycopg2
import os
from dotenv import load_dotenv
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
        # Direct PostgreSQL connection
        load_dotenv()
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()
        
        # Simple query - no column aliases
        cursor.execute("SELECT id, username, password, name, role, is_active FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user:
            user_id, user_username, user_password, user_name, user_role, is_active = user
            
            if user_password == password and is_active:
                session.clear()
                session.permanent = True
                session['user_id'] = user_id
                session['username'] = user_username
                session['name'] = user_name
                session['role'] = user_role
                
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
                return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 401
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

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
    else:
        return jsonify({'authenticated': False}), 200