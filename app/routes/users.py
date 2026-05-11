from flask import Blueprint, request, jsonify, session
from app.database import get_db, release_db
from datetime import datetime
from werkzeug.security import generate_password_hash
import traceback
import logging

# Setup logger - better than print statements
logger = logging.getLogger(__name__)

bp = Blueprint('users', __name__, url_prefix='/api/users')

@bp.route('', methods=['GET'])
def get_users():
    """Get all users - Admin only"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401

        conn, cursor = get_db()
        try:
            # Use the correct column names from your database
            cursor.execute('''
                SELECT id, username, name, email, role, is_active, last_login, created_at 
                FROM users ORDER BY created_at DESC
            ''')
            users = cursor.fetchall()
            
            # Convert rows to dictionaries
            user_list = []
            for user in users:
                user_dict = {
                    'id': user[0],
                    'username': user[1],
                    'full_name': user[2],
                    'email': user[3],
                    'role': user[4],
                    'is_active': user[5],
                    'last_login': user[6],
                    'created_at': str(user[7]) if user[7] else None
                }
                user_list.append(user_dict)
            
            result = {'success': True, 'users': user_list}
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            release_db(conn, cursor)
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': 'Server error'}), 500


@bp.route('', methods=['POST'])
def create_user():
    """Create a new user with hashed password"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    # Validate required fields
    required_fields = ['username', 'password', 'name', 'email', 'role']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    try:
        conn, cursor = get_db()
        
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE username = %s', (data['username'],))
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
        
        # Hash the password
        password_hash = generate_password_hash(data['password'])
        
        # Insert new user
        cursor.execute('''
            INSERT INTO users (username, password, name, email, role, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            data['username'],
            password_hash,
            data['name'],
            data['email'],
            data['role'],
            True,
            datetime.now()
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        logger.info(f"User {data['username']} created by {session.get('username')}")
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user_id': result[0] if result else None
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({'success': False, 'error': 'Error creating user'}), 500
    finally:
        release_db(conn, cursor)
