from flask import Blueprint, request, jsonify, session
from app.database import get_db, release_db
from datetime import datetime
from werkzeug.security import generate_password_hash

bp = Blueprint('users', __name__, url_prefix='/api/users')

@bp.route('', methods=['GET'])
def get_users():
    """Get all users"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    try:
        cursor.execute('SELECT id, username, name, email, role, is_active, last_login, created_at FROM users ORDER BY created_at DESC')
        users = cursor.fetchall()
        return jsonify({'success': True, 'users': [dict(u) for u in users]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)

@bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    try:
        cursor.execute('SELECT id, username, name, email, role, is_active, last_login, created_at FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        return jsonify({'success': True, 'user': dict(user)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)

@bp.route('', methods=['POST'])
def create_user():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    if not data.get('username') or not data.get('password'):
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    password_hash = generate_password_hash(data['password'])
    conn, cursor = get_db()
    try:
        cursor.execute('INSERT INTO users (username, password_hash, name, email, role, created_at) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id',
                      (data['username'], password_hash, data.get('name'), data.get('email'), data.get('role', 'staff'), datetime.now()))
        result = cursor.fetchone()
        conn.commit()
        return jsonify({'success': True, 'user_id': result['id']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)

@bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    conn, cursor = get_db()
    try:
        updates = []
        values = []
        for field in ['name', 'email', 'role', 'is_active']:
            if field in data:
                updates.append(f"{field} = %s")
                values.append(data[field])
        if 'password' in data:
            updates.append("password_hash = %s")
            values.append(generate_password_hash(data['password']))
        
        if updates:
            values.append(user_id)
            cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = %s", values)
            conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)

@bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    if user_id == session['user_id']:
        return jsonify({'success': False, 'error': 'Cannot delete yourself'}), 400
    
    conn, cursor = get_db()
    try:
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)
