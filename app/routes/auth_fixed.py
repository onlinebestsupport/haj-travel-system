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
        cursor.execute("SELECT id, username, password, role, name, email FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        release_db(conn, cursor)
        
        if user:
            # Convert tuple to dict using column names
            user_dict = {
                'id': user[0],
                'username': user[1],
                'password': user[2],
                'role': user[3],
                'name': user[4],
                'email': user[5]
            }
            
            if user_dict['password'] == password:
                session.clear()
                session['user_id'] = user_dict['id']
                session['username'] = user_dict['username']
                session['role'] = user_dict['role']
                session['name'] = user_dict['name']
                return jsonify({'success': True, 'user': user_dict})
        
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500