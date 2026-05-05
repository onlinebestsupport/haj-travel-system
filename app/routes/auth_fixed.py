from flask import Blueprint, request, jsonify, session
from app.database import get_db, release_db

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
        cursor.execute("SELECT id, username, password, role, name, email, is_active FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        release_db(conn, cursor)
        
        if user:
            # Convert to dictionary
            user_dict = {
                'id': user[0],
                'username': user[1],
                'password': user[2],
                'role': user[3],
                'name': user[4],
                'email': user[5],
                'is_active': user[6]
            }
            
            if user_dict['password'] == password and user_dict['is_active']:
                session.clear()
                session.permanent = True
                session['user_id'] = user_dict['id']
                session['username'] = user_dict['username']
                session['role'] = user_dict['role']
                session['name'] = user_dict['name']
                return jsonify({
                    'success': True,
                    'authenticated': True,
                    'user': {
                        'id': user_dict['id'],
                        'username': user_dict['username'],
                        'name': user_dict['name'],
                        'email': user_dict['email'],
                        'role': user_dict['role']
                    }
                })
        
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
    else:
        return jsonify({'authenticated': False}), 200