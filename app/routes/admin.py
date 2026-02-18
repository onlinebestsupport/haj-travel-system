from flask import Blueprint, request, jsonify, session
from app.database import get_db
import psycopg2
import psycopg2.extras
from functools import wraps
import hashlib
import base64

admin_bp = Blueprint('admin', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def generate_password_hash(password):
    """Simple password hashing"""
    salt = "alhudha-salt-2026"
    hash_obj = hashlib.sha256((password + salt).encode())
    return base64.b64encode(hash_obj.digest()).decode()

@admin_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    """Get all admin users"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("""
            SELECT u.id, u.username, u.email, u.full_name, u.is_active, 
                   u.created_at, u.last_login,
                   COALESCE(array_agg(DISTINCT r.name) FILTER (WHERE r.name IS NOT NULL), '{}') as roles
            FROM admin_users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            GROUP BY u.id
            ORDER BY u.created_at DESC
        """)
        
        users = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/users', methods=['POST'])
@login_required
def create_user():
    """Create a new admin user"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['username', 'password', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        cur = conn.cursor()
        
        # Check if username exists
        cur.execute("SELECT id FROM admin_users WHERE username = %s", (data['username'],))
        if cur.fetchone():
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
        
        # Check if email exists
        cur.execute("SELECT id FROM admin_users WHERE email = %s", (data['email'],))
        if cur.fetchone():
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
        
        # Hash password
        password_hash = generate_password_hash(data['password'])
        
        # Insert user
        cur.execute("""
            INSERT INTO admin_users (username, password_hash, email, full_name, created_by)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data['username'],
            password_hash,
            data['email'],
            data.get('full_name', ''),
            session.get('admin_user_id')
        ))
        
        user_id = cur.fetchone()[0]
        
        # Assign role (default to 'viewer' if not specified)
        role_name = data.get('roles', ['viewer'])[0]
        cur.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
        role = cur.fetchone()
        
        if role:
            cur.execute("""
                INSERT INTO user_roles (user_id, role_id, assigned_by)
                VALUES (%s, %s, %s)
            """, (user_id, role[0], session.get('admin_user_id')))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user_id': user_id
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
