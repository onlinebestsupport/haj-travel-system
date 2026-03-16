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
            cursor.execute('SELECT id, username, name, email, role, is_active, last_login, created_at FROM users ORDER BY created_at DESC')
            users = cursor.fetchall()
            print(f"🔵 Found {len(users)} users", file=sys.stderr)
            
            result = {'success': True, 'users': [dict(u) for u in users]}
            print(f"🔵 Returning result: {result}", file=sys.stderr)
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