from flask import Blueprint, request, jsonify, session, send_file
from app.database import get_db, release_db  # ✅ POOL COMPATIBLE
from app.middleware import role_required, safe_db_operation, log_critical_action, get_client_ip  # ✅ FIXED IMPORTS
from datetime import datetime
import json
import os

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ==================== 🔥 SAFE DB HELPER ====================
def safe_db_operation(operation_func):
    """🔥 ZERO LEAKS - Pool safe wrapper"""
    def wrapper(*args, **kwargs):
        conn = cursor = None
        try:
            conn, cursor = get_db()
            result = operation_func(conn, cursor, *args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            if conn: conn.rollback()
            print(f"❌ Admin DB error: {e}")
            return None
        finally:
            release_db(conn, cursor)  # 🔥 CRITICAL
    return wrapper

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
    if not users:
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
            SELECT COUNT(*) as total, MAX(created_at) as last_backup,
                   COUNT(CASE WHEN is_restore_point THEN 1 END) as restore_points
            FROM backup_history
        """)
        return cursor.fetchone()
    
    stats = safe_db_operation(fetch_stats)()
    
    # File system stats (safe)
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', 'backups')
    total_size = sum(os.path.getsize(os.path.join(backup_dir, f)) 
                    for f in os.listdir(backup_dir) if os.path.isfile(os.path.join(backup_dir, f))
                    ) if os.path.exists(backup_dir) else 0
    
    return jsonify({
        'success': True,
        'stats': {
            'totalBackups': stats['total'] if stats else 0,
            'restorePoints': stats['restore_points'] if stats else 0,
            'lastBackup': stats['last_backup'].strftime('%d %b %H:%M') if stats and stats['last_backup'] else 'Never',
            'storageUsed': format_bytes(total_size),
            'storagePercent': min((total_size / (1024**3)) * 100, 100)
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
        tables = ['users', 'batches', 'travelers', 'payments']
        backup_data = {'timestamp': timestamp, 'tables': {}}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            backup_data['tables'][table] = cursor.fetchone()['count']
        return backup_data
    
    data = safe_db_operation(create_json_backup)()
    
    # Write JSON backup
    with open(backup_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Log to database
    def log_backup(conn, cursor, name):
        cursor.execute("""
            INSERT INTO backup_history (backup_name, backup_type, file_size, tables_count, status, location)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, 'manual', format_bytes(os.path.getsize(backup_path)), 
              sum(data['tables'].values()), 'completed', backup_path))
    
    safe_db_operation(log_backup)(backup_name)
    
    log_critical_action(session['user_id'], 'CREATE_BACKUP', f'Created: {backup_name}', get_client_ip())
    
    return jsonify({
        'success': True,
        'backup': {'name': backup_name, 'size': format_bytes(os.path.getsize(backup_path))}
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
        return True
    
    success = safe_db_operation(get_delete_info)(backup_id)
    if success:
        log_critical_action(session['user_id'], 'DELETE_BACKUP', f'Backup ID: {backup_id}')
        return jsonify({'success': True, 'message': 'Deleted'})
    return jsonify({'success': False, 'error': 'Not found'}), 404

# ==================== 📊 DASHBOARD STATS ====================
@bp.route('/dashboard/stats', methods=['GET'])
@role_required(['super_admin', 'admin', 'manager'])
def get_dashboard_stats():
    """🔥 FIXED - Single pooled query"""
    def fetch_stats(conn, cursor):
        stats = {}
        cursor.execute('SELECT COUNT(*) as count FROM travelers'); stats['travelers'] = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM batches'); stats['batches'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM batches WHERE status = 'Open'"); stats['active'] = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM users'); stats['users'] = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM invoices'); stats['invoices'] = cursor.fetchone()['count']
        return stats
    
    stats = safe_db_operation(fetch_stats)()
    return jsonify({'success': True, 'stats': stats or {}})

@bp.route('/table-counts', methods=['GET'])
@role_required(['super_admin', 'admin'])
def get_table_counts():
    """Quick table counts"""
    def count_tables(conn, cursor):
        tables = ['users', 'batches', 'travelers', 'payments', 'invoices', 'receipts']
        counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            counts[table] = cursor.fetchone()['count']
        return counts
    
    counts = safe_db_operation(count_tables)()
    return jsonify({'success': True, 'counts': counts or {}})

# ==================== 🩺 HEALTH CHECK ====================
@bp.route('/health', methods=['GET'])
@role_required(['super_admin', 'admin'])
def system_health():
    """Admin health check"""
    def health_check(conn, cursor):
        tables = ['travelers', 'batches', 'payments']
        counts = {t: cursor.execute(f"SELECT COUNT(*) as count FROM {t}") or cursor.fetchone()['count'] for t in tables}
        return {'status': 'healthy', 'counts': counts}
    
    health = safe_db_operation(health_check)()
    return jsonify({'success': True, 'health': health or {'status': 'error'}})

# ==================== 🔧 UTILITY ====================
def format_bytes(size_bytes):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"
