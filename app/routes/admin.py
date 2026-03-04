from flask import Blueprint, request, jsonify, session, send_file
from app.database import get_db, release_db  # ✅ POOL COMPATIBLE
from app.middleware import role_required, safe_db_operation, log_critical_action, get_client_ip  # ✅ FIXED IMPORTS
from datetime import datetime, timedelta
import json
import os
import hashlib

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ==================== 🔐 SESSION MANAGEMENT ====================
@bp.route('/check-session', methods=['GET'])
def check_session():
    """Check if user is authenticated - Used by SessionManager"""
    if 'user_id' not in session:
        return jsonify({'authenticated': False}), 401
    
    def get_user_info(conn, cursor):
        cursor.execute('''
            SELECT id, username, full_name as name, email, role, last_login 
            FROM users WHERE id = %s AND is_active = true
        ''', (session['user_id'],))
        return cursor.fetchone()
    
    user = safe_db_operation(get_user_info)()
    if not user:
        session.clear()
        return jsonify({'authenticated': False}), 401
    
    # Update last activity timestamp
    session['last_activity'] = datetime.now().isoformat()
    
    return jsonify({
        'authenticated': True,
        'user': dict(user),
        'session_expiry': (datetime.now() + timedelta(minutes=30)).isoformat()
    })

@bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    user_id = session.get('user_id')
    if user_id:
        log_critical_action(user_id, 'LOGOUT', 'User logged out', get_client_ip())
    
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

# ==================== 👥 USER MANAGEMENT ====================
@bp.route('/users', methods=['GET'])
@role_required(['super_admin', 'admin', 'manager'])
def get_users():
    """Get all users - POOL SAFE"""
    def fetch_users(conn, cursor):
        cursor.execute('''
            SELECT id, username, full_name, email, phone, department,
                   role, permissions, is_active, last_login, created_at
            FROM users ORDER BY username
        ''')
        return cursor.fetchall()
    
    users = safe_db_operation(fetch_users)()
    if users is None:
        return jsonify({'success': False, 'error': 'Failed to fetch users'}), 500
    
    # Parse permissions
    result = []
    for user in users:
        user_dict = dict(user)
        perms = user_dict.get('permissions', '{}')
        try:
            user_dict['permissions'] = json.loads(perms) if isinstance(perms, str) else perms
        except:
            user_dict['permissions'] = {}
        result.append(user_dict)
    
    return jsonify({'success': True, 'users': result})

@bp.route('/users/<int:user_id>', methods=['GET'])
@role_required(['super_admin', 'admin'])
def get_user(user_id):
    """Get single user"""
    def fetch_user(conn, cursor, uid):
        cursor.execute('SELECT * FROM users WHERE id = %s', (uid,))
        return cursor.fetchone()
    
    user = safe_db_operation(fetch_user)(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    user_dict = dict(user)
    perms = user_dict.get('permissions', '{}')
    try:
        user_dict['permissions'] = json.loads(perms) if isinstance(perms, str) else perms
    except:
        user_dict['permissions'] = {}
    
    return jsonify({'success': True, 'user': user_dict})

@bp.route('/users', methods=['POST'])
@role_required(['super_admin', 'admin'])
def create_user():
    """Create new user"""
    data = request.json
    
    required = ['username', 'password', 'email', 'role']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} required'}), 400
    
    # Hash password (in production, use proper password hashing)
    password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
    permissions = json.dumps(data.get('permissions', {}))
    
    def create(conn, cursor):
        # Check duplicates
        cursor.execute('SELECT id FROM users WHERE username = %s', (data['username'],))
        if cursor.fetchone():
            return {'error': 'Username exists'}
        
        cursor.execute('SELECT id FROM users WHERE email = %s', (data['email'],))
        if cursor.fetchone():
            return {'error': 'Email exists'}
        
        cursor.execute('''
            INSERT INTO users (username, password, full_name, email, phone, department,
                             role, permissions, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (data['username'], password_hash, data.get('full_name'), data['email'],
              data.get('phone'), data.get('department'), data['role'], permissions,
              True, datetime.now(), datetime.now()))
        
        return {'id': cursor.fetchone()['id']}
    
    result = safe_db_operation(create)()
    if result and 'error' in result:
        return jsonify({'success': False, 'error': result['error']}), 400
    
    log_critical_action(session['user_id'], 'CREATE_USER', 
                       f'Created user: {data["username"]}', get_client_ip())
    
    return jsonify({'success': True, 'user_id': result['id']})

@bp.route('/users/<int:user_id>', methods=['PUT'])
@role_required(['super_admin', 'admin'])
def update_user(user_id):
    """Update user"""
    data = request.json
    
    def update(conn, cursor, uid):
        cursor.execute('SELECT username FROM users WHERE id = %s', (uid,))
        user = cursor.fetchone()
        if not user:
            return None
        
        permissions = json.dumps(data.get('permissions', {}))
        cursor.execute('''
            UPDATE users SET full_name = %s, email = %s, phone = %s,
                department = %s, role = %s, permissions = %s, updated_at = %s
            WHERE id = %s
        ''', (data.get('full_name'), data['email'], data.get('phone'),
              data.get('department'), data['role'], permissions, datetime.now(), uid))
        return user['username']
    
    username = safe_db_operation(update)(user_id)
    if username is None:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    log_critical_action(session['user_id'], 'UPDATE_USER', 
                       f'Updated user: {username}', get_client_ip())
    
    return jsonify({'success': True})

@bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@role_required(['super_admin', 'admin'])
def toggle_user_status(user_id):
    """Toggle user active status"""
    def toggle(conn, cursor, uid):
        cursor.execute('SELECT is_active, username FROM users WHERE id = %s', (uid,))
        user = cursor.fetchone()
        if not user:
            return None
        new_status = not user['is_active']
        cursor.execute('UPDATE users SET is_active = %s, updated_at = %s WHERE id = %s', 
                      (new_status, datetime.now(), uid))
        return {'username': user['username'], 'new_status': new_status}
    
    result = safe_db_operation(toggle)(user_id)
    if not result:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    status_text = 'activated' if result['new_status'] else 'deactivated'
    log_critical_action(session['user_id'], f'{status_text.upper()}_USER', 
                       f'{status_text} user: {result["username"]}', get_client_ip())
    
    return jsonify({'success': True, 'is_active': result['new_status']})

@bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@role_required(['super_admin', 'admin'])
def reset_password(user_id):
    """Reset user password"""
    data = request.json
    new_password = data.get('password')
    
    if not new_password or len(new_password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
    
    password_hash = hashlib.sha256(new_password.encode()).hexdigest()
    
    def reset(conn, cursor, uid):
        cursor.execute('SELECT username FROM users WHERE id = %s', (uid,))
        user = cursor.fetchone()
        if not user:
            return None
        cursor.execute('UPDATE users SET password = %s, updated_at = %s WHERE id = %s',
                      (password_hash, datetime.now(), uid))
        return user['username']
    
    username = safe_db_operation(reset)(user_id)
    if not username:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    log_critical_action(session['user_id'], 'RESET_PASSWORD', 
                       f'Reset password for: {username}', get_client_ip())
    
    return jsonify({'success': True})

# ==================== 📊 DASHBOARD STATS ====================
@bp.route('/dashboard/stats', methods=['GET'])
@role_required(['super_admin', 'admin', 'manager'])
def get_dashboard_stats():
    """🔥 FIXED - Single pooled query with recent activity"""
    def fetch_stats(conn, cursor):
        stats = {}
        
        # Basic counts
        cursor.execute('SELECT COUNT(*) as count FROM travelers')
        stats['total_travelers'] = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM batches')
        stats['total_batches'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM batches WHERE status = 'Open'")
        stats['active_batches'] = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM users')
        stats['total_users'] = cursor.fetchone()['count']
        
        # Payment stats
        cursor.execute('SELECT COUNT(*) as count FROM payments WHERE status = \'completed\'')
        stats['paid_count'] = cursor.fetchone()['count']
        
        cursor.execute('SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE status = \'completed\'')
        stats['total_collected'] = float(cursor.fetchone()['total'])
        
        cursor.execute('SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE status = \'pending\'')
        stats['pending_amount'] = float(cursor.fetchone()['total'])
        
        # Recent travelers (last 5)
        cursor.execute('''
            SELECT id, first_name, last_name, passport_no, created_at 
            FROM travelers ORDER BY created_at DESC LIMIT 5
        ''')
        stats['recent_travelers'] = [dict(row) for row in cursor.fetchall()]
        
        # Recent payments (last 5)
        cursor.execute('''
            SELECT p.id, p.amount, p.payment_date, t.first_name, t.last_name
            FROM payments p
            JOIN travelers t ON p.traveler_id = t.id
            ORDER BY p.payment_date DESC LIMIT 5
        ''')
        stats['recent_payments'] = [dict(row) for row in cursor.fetchall()]
        
        # Upcoming batches (next 3)
        cursor.execute('''
            SELECT id, batch_name, departure_date, total_seats, booked_seats
            FROM batches WHERE departure_date > NOW()
            ORDER BY departure_date ASC LIMIT 3
        ''')
        stats['upcoming_batches'] = [dict(row) for row in cursor.fetchall()]
        
        return stats
    
    stats = safe_db_operation(fetch_stats)()
    if stats is None:
        return jsonify({'success': False, 'error': 'Failed to fetch stats'}), 500
    
    return jsonify({'success': True, 'stats': stats})

@bp.route('/table-counts', methods=['GET'])
@role_required(['super_admin', 'admin'])
def get_table_counts():
    """Quick table counts"""
    def count_tables(conn, cursor):
        tables = ['users', 'batches', 'travelers', 'payments', 'invoices', 'receipts']
        counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            result = cursor.fetchone()
            counts[table] = result['count'] if result else 0
        return counts
    
    counts = safe_db_operation(count_tables)() or {}
    return jsonify({'success': True, 'counts': counts})

# ==================== 💾 BACKUP MANAGEMENT ====================
@bp.route('/backups', methods=['GET'])
@role_required(['super_admin', 'admin'])
def get_backups():
    """Get backup history"""
    def fetch_backups(conn, cursor):
        cursor.execute("SELECT * FROM backup_history ORDER BY created_at DESC")
        return cursor.fetchall()
    
    backups = safe_db_operation(fetch_backups)()
    return jsonify({'success': True, 'backups': [dict(b) for b in backups or []]})

@bp.route('/backups/stats', methods=['GET'])
@role_required(['super_admin', 'admin'])
def get_backup_stats():
    """Get backup statistics - NO SUBPROCESS"""
    def fetch_stats(conn, cursor):
        cursor.execute("""
            SELECT COUNT(*) as total, 
                   MAX(created_at) as last_backup,
                   COUNT(CASE WHEN is_restore_point = true THEN 1 END) as restore_points
            FROM backup_history
        """)
        return cursor.fetchone()
    
    stats = safe_db_operation(fetch_stats)()
    
    # File system stats with error handling
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', 'backups')
    total_size = 0
    if os.path.exists(backup_dir):
        try:
            total_size = sum(os.path.getsize(os.path.join(backup_dir, f)) 
                            for f in os.listdir(backup_dir) 
                            if os.path.isfile(os.path.join(backup_dir, f)))
        except Exception as e:
            print(f"⚠️ Backup size calculation error: {e}")
    
    # Safe date formatting
    last_backup_str = 'Never'
    if stats and stats.get('last_backup'):
        try:
            last_backup_str = stats['last_backup'].strftime('%d %b %H:%M')
        except:
            last_backup_str = str(stats['last_backup'])
    
    return jsonify({
        'success': True,
        'stats': {
            'totalBackups': stats['total'] if stats else 0,
            'restorePoints': stats['restore_points'] if stats else 0,
            'lastBackup': last_backup_str,
            'storageUsed': format_bytes(total_size),
            'storagePercent': min((total_size / (1024**3)) * 100, 100) if total_size > 0 else 0
        }
    })

@bp.route('/backup/create', methods=['POST'])
@role_required(['super_admin', 'admin'])
def create_backup():
    """🔥 JSON Backup (Railway safe - NO pg_dump)"""
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"backup_{timestamp}.json"
    backup_path = os.path.join(backup_dir, backup_name)
    
    def create_json_backup(conn, cursor):
        tables = ['users', 'batches', 'travelers', 'payments', 'invoices', 'receipts']
        backup_data = {
            'timestamp': timestamp,
            'version': '2.0',
            'tables': {}
        }
        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            backup_data['tables'][table] = [dict(row) for row in rows]
        return backup_data
    
    data = safe_db_operation(create_json_backup)()
    if data is None:
        return jsonify({'success': False, 'error': 'Failed to create backup'}), 500
    
    # Write JSON backup
    with open(backup_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    file_size = os.path.getsize(backup_path)
    
    # Log to database
    def log_backup(conn, cursor):
        cursor.execute("""
            INSERT INTO backup_history (backup_name, backup_type, file_size, tables_count, status, location, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (backup_name, 'manual', file_size, len(data['tables']), 'completed', backup_path, datetime.now()))
    
    safe_db_operation(log_backup)()
    
    log_critical_action(session['user_id'], 'CREATE_BACKUP', f'Created: {backup_name}', get_client_ip())
    
    return jsonify({
        'success': True,
        'backup': {'name': backup_name, 'size': format_bytes(file_size)}
    })

@bp.route('/backup/<int:backup_id>/download', methods=['GET'])
@role_required(['super_admin', 'admin'])
def download_backup(backup_id):
    """Download backup file"""
    def get_backup_path(conn, cursor, bid):
        cursor.execute("SELECT location, backup_name FROM backup_history WHERE id = %s", (bid,))
        return cursor.fetchone()
    
    backup = safe_db_operation(get_backup_path)(backup_id)
    if not backup:
        return jsonify({'success': False, 'error': 'Backup not found'}), 404
    
    backup_path = backup['location']
    if not os.path.exists(backup_path):
        return jsonify({'success': False, 'error': 'File missing'}), 404
    
    return send_file(backup_path, as_attachment=True, download_name=backup['backup_name'])

@bp.route('/backup/<int:backup_id>', methods=['DELETE'])
@role_required(['super_admin', 'admin'])
def delete_backup(backup_id):
    """Delete backup"""
    def get_delete_info(conn, cursor, bid):
        cursor.execute("SELECT location, backup_name FROM backup_history WHERE id = %s", (bid,))
        backup = cursor.fetchone()
        if backup and os.path.exists(backup['location']):
            os.remove(backup['location'])
        cursor.execute("DELETE FROM backup_history WHERE id = %s", (bid,))
        return backup
    
    backup = safe_db_operation(get_delete_info)(backup_id)
    if backup:
        log_critical_action(session['user_id'], 'DELETE_BACKUP', 
                           f'Deleted: {backup["backup_name"]}', get_client_ip())
        return jsonify({'success': True, 'message': 'Deleted'})
    return jsonify({'success': False, 'error': 'Not found'}), 404

# ==================== 🩺 HEALTH CHECK ====================
@bp.route('/health', methods=['GET'])
@role_required(['super_admin', 'admin'])
def system_health():
    """Admin health check"""
    def health_check(conn, cursor):
        tables = ['travelers', 'batches', 'payments', 'users']
        counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            result = cursor.fetchone()
            counts[table] = result['count'] if result else 0
        
        # Check connection pool
        cursor.execute('SELECT 1 as healthy')
        db_healthy = cursor.fetchone()['healthy'] == 1
        
        return {
            'status': 'healthy' if db_healthy else 'degraded',
            'timestamp': datetime.now().isoformat(),
            'counts': counts,
            'session_active': bool(session.get('user_id'))
        }
    
    health = safe_db_operation(health_check)()
    if health is None:
        return jsonify({'success': False, 'error': 'Health check failed'}), 500
    
    return jsonify({'success': True, 'health': health})

# ==================== 🔧 UTILITY ====================
def format_bytes(size_bytes):
    """Format bytes to human readable"""
    if size_bytes == 0:
        return "0B"
    units = ['B', 'KB', 'MB', 'GB']
    for unit in units:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"
