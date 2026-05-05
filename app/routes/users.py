from flask import Blueprint, request, jsonify, session
from app.database import get_db, release_db
from datetime import datetime
from werkzeug.security import generate_password_hash
import traceback
import sys

print("🔵 LOADING users.py BLUEPRINT...", file=sys.stderr)

bp = Blueprint('users', __name__, url_prefix='/api/users')

print(f"🔵 Blueprint 'users' created with url_prefix: /api/users", file=sys.stderr)

@bp.route('', methods=['GET'])
def get_users():
    """Get all users"""
    print("🔵 get_users() called", file=sys.stderr)
    print(f"🔵 Session: {dict(session)}", file=sys.stderr)
    
    try:
        if 'user_id' not in session:
            print("🔴 Unauthorized - no user_id in session", file=sys.stderr)
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401

        print(f"🔵 User authenticated: {session['user_id']}", file=sys.stderr)
        
        conn, cursor = get_db()
        try:
            print("🔵 Executing SQL query...", file=sys.stderr)
            # Use the correct column names from your database
            cursor.execute('''
                SELECT id, username, name, email, role, is_active, last_login, created_at 
                FROM users ORDER BY created_at DESC
            ''')
            users = cursor.fetchall()
            print(f"🔵 Found {len(users)} users", file=sys.stderr)
            
            # Convert rows to dictionaries
            user_list = []
            for user in users:
                user_dict = {
                    'id': user[0],
                    'username': user[1],
                    'full_name': user[2],  # 'name' column maps to 'full_name' in API
                    'email': user[3],
                    'role': user[4],
                    'is_active': user[5],
                    'last_login': user[6],
                    'created_at': user[7]
                }
                user_list.append(user_dict)
            
            result = {'success': True, 'users': user_list}
            print(f"🔵 Returning {len(user_list)} users", file=sys.stderr)
            return jsonify(result)
            
        except Exception as e:
            print(f"🔴 Database error: {str(e)}", file=sys.stderr)
            print(f"🔴 Traceback: {traceback.format_exc()}", file=sys.stderr)
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            release_db(conn, cursor)
            
    except Exception as e:
        print(f"🔴 Unexpected error: {str(e)}", file=sys.stderr)
        print(f"🔴 Traceback: {traceback.format_exc()}", file=sys.stderr)
        return jsonify({'success': False, 'error': str(e)}), 500

print("🔵 users.py blueprint loaded successfully!", file=sys.stderr)