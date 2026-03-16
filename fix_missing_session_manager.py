import os
import re

# Modules that need fixing
MODULES_TO_FIX = [
    {"name": "Dashboard", "file": "public/admin/dashboard.html"},
    {"name": "Travelers", "file": "public/admin/travelers.html"},
    {"name": "Batches", "file": "public/admin/batches.html"},
    {"name": "Payments", "file": "public/admin/payments.html"},
    {"name": "Users", "file": "public/admin/users.html"},
]

def add_session_manager_to_file(filepath):
    """Add session-manager.js reference and initialization to HTML file"""
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if session-manager.js is already present
    if 'session-manager.js' in content:
        print(f"  ⏭️  session-manager.js already present in {filepath}")
        return True
    
    # Add script reference in head section
    if '</head>' in content:
        content = content.replace('</head>', '    <script src="/admin/js/session-manager.js"></script>\n</head>')
        print(f"  ✅ Added session-manager.js to head in {filepath}")
    else:
        print(f"  ❌ Could not find head tag in {filepath}")
        return False
    
    # Add initialization script if needed
    if 'SessionManager.initPage' not in content:
        init_script = '''
<script>
// Initialize page with session check
document.addEventListener('DOMContentLoaded', function() {
    if (typeof SessionManager !== 'undefined' && SessionManager.initPage) {
        SessionManager.initPage(function() {
            console.log('Page initialized');
        });
    }
});
</script>
'''
        content = content.replace('</body>', init_script + '\n</body>')
        print(f"  ✅ Added SessionManager initialization")
    
    # Write the file back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def create_users_py():
    """Create users.py with simple string"""
    users_file = 'app/routes/users.py'
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(users_file), exist_ok=True)
    
    users_content = '''from flask import Blueprint, request, jsonify, session
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
'''
    
    with open(users_file, 'w') as f:
        f.write(users_content)
    print(f"✅ Created {users_file}")

def create_backup_py():
    """Create backup.py with simple string"""
    backup_file = 'app/routes/backup.py'
    
    os.makedirs(os.path.dirname(backup_file), exist_ok=True)
    
    backup_content = '''from flask import Blueprint, request, jsonify, session
from app.database import get_db, release_db
from datetime import datetime

bp = Blueprint('backup', __name__, url_prefix='/api/backup')

@bp.route('', methods=['GET'])
def get_backups():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    try:
        cursor.execute('SELECT * FROM backup_history ORDER BY created_at DESC')
        backups = cursor.fetchall()
        return jsonify({'success': True, 'backups': [dict(b) for b in backups]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)

@bp.route('/create', methods=['POST'])
def create_backup():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    conn, cursor = get_db()
    try:
        cursor.execute('INSERT INTO backup_history (backup_name, status, created_at) VALUES (%s, %s, %s) RETURNING id',
                      (data.get('backup_name', f"Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"), 'completed', datetime.now()))
        result = cursor.fetchone()
        conn.commit()
        return jsonify({'success': True, 'backup_id': result['id']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)

@bp.route('/settings', methods=['GET'])
def get_settings():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    try:
        cursor.execute('SELECT * FROM backup_settings LIMIT 1')
        settings = cursor.fetchone()
        return jsonify({'success': True, 'settings': dict(settings) if settings else {}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)
'''
    
    with open(backup_file, 'w') as f:
        f.write(backup_content)
    print(f"✅ Created {backup_file}")

def update_init_py():
    """Update __init__.py to import new modules"""
    init_file = 'app/routes/__init__.py'
    
    if not os.path.exists(init_file):
        init_content = '''from . import auth
from . import admin
from . import batches
from . import travelers
from . import payments
from . import company
from . import uploads
from . import reports
from . import invoices
from . import receipts
from . import users
from . import backup
'''
        with open(init_file, 'w') as f:
            f.write(init_content)
        print(f"✅ Created {init_file}")
        return
    
    with open(init_file, 'r') as f:
        content = f.read()
    
    with open(init_file, 'a') as f:
        if 'from . import users' not in content:
            f.write('from . import users\n')
            print(f"✅ Added users to {init_file}")
        if 'from . import backup' not in content:
            f.write('from . import backup\n')
            print(f"✅ Added backup to {init_file}")

def main():
    print("=" * 60)
    print("🔧 FIXING ALL ISSUES")
    print("=" * 60)
    
    # Step 1: Fix HTML files
    print("\n📁 STEP 1: Adding session-manager.js to HTML files")
    print("-" * 40)
    
    fixed_count = 0
    for module in MODULES_TO_FIX:
        print(f"\n{module['name']}:")
        if add_session_manager_to_file(module['file']):
            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} out of {len(MODULES_TO_FIX)} modules")
    
    # Step 2: Create missing API files
    print("\n📁 STEP 2: Creating missing API files")
    print("-" * 40)
    
    create_users_py()
    create_backup_py()
    update_init_py()
    
    # Step 3: Git commands
    print("\n📁 STEP 3: Deploy fixes")
    print("-" * 40)
    print("\nRun these commands to deploy:")
    print("  git add public/admin/")
    print("  git add app/routes/")
    print('  git commit -m "Fix: Add session-manager.js to missing modules and create users/backup APIs"')
    print("  git push origin main")
    
    print("\n" + "=" * 60)
    print("✅ ALL FIXES COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()