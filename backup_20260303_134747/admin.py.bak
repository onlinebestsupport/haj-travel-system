from flask import Blueprint, request, jsonify, session, send_file
from app.database import get_db
from datetime import datetime
import json
import os
from app.middleware import role_required, super_admin_required, log_critical_action, auto_backup, manual_backup
import psycopg2.extras

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ==================== USER MANAGEMENT ====================

@bp.route('/users', methods=['GET'])
def get_users():
    """Get all users with complete details"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    cursor.execute('''
        SELECT 
            id, username, full_name, email, phone, department,
            role, permissions, is_active, last_login, created_at
        FROM users 
        ORDER BY 
            CASE 
                WHEN role = 'super_admin' THEN 1
                WHEN role = 'admin' THEN 2
                WHEN role = 'manager' THEN 3
                WHEN role = 'staff' THEN 4
                ELSE 5
            END,
            username ASC
    ''')
    
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    result = []
    for user in users:
        user_dict = dict(user)
        if user_dict.get('permissions'):
            try:
                if isinstance(user_dict['permissions'], str):
                    user_dict['permissions'] = json.loads(user_dict['permissions'])
            except:
                user_dict['permissions'] = {}
        else:
            user_dict['permissions'] = {}
        result.append(user_dict)
    
    return jsonify({'success': True, 'users': result})

@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get single user with complete details"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    cursor.execute('''
        SELECT 
            id, username, full_name, email, phone, department,
            role, permissions, is_active, last_login, created_at, updated_at
        FROM users 
        WHERE id = %s
    ''', (user_id,))
    
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    user_dict = dict(user)
    if user_dict.get('permissions'):
        try:
            if isinstance(user_dict['permissions'], str):
                user_dict['permissions'] = json.loads(user_dict['permissions'])
        except:
            user_dict['permissions'] = {}
    else:
        user_dict['permissions'] = {}
    
    return jsonify({'success': True, 'user': user_dict})

# ==================== BACKUP & RESTORE ENDPOINTS ====================

@bp.route('/backups', methods=['GET'])
@role_required(['super_admin', 'admin'])
def get_backups():
    """Get backup history from PostgreSQL"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    # Get filter parameters
    backup_type = request.args.get('type', 'all')
    
    query = "SELECT * FROM backup_history"
    params = []
    
    if backup_type != 'all':
        if backup_type == 'restore':
            query += " WHERE is_restore_point = TRUE"
        else:
            query += " WHERE backup_type = %s"
            params.append(backup_type)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    backups = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify({
        'success': True,
        'backups': [dict(b) for b in backups]
    })

@bp.route('/backups/stats', methods=['GET'])
@role_required(['super_admin', 'admin'])
def get_backup_stats():
    """Get backup statistics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    # Get database size
    cursor.execute("SELECT pg_database_size(current_database()) as size")
    db_size_result = cursor.fetchone()
    db_size = db_size_result['size'] if db_size_result else 0
    
    # Get backup stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_backups,
            MAX(created_at) as last_backup,
            COUNT(CASE WHEN is_restore_point = TRUE THEN 1 END) as restore_points,
            COUNT(CASE WHEN backup_type = 'auto' THEN 1 END) as auto_backups,
            COUNT(CASE WHEN backup_type = 'manual' AND is_restore_point = FALSE THEN 1 END) as manual_backups
        FROM backup_history
    """)
    stats = cursor.fetchone()
    
    # Get total backup size
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', 'backups')
    total_size = 0
    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, file)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
    
    cursor.close()
    conn.close()
    
    # Format dates
    last_backup = stats['last_backup']
    if last_backup:
        last_backup = last_backup.strftime('%d %b, %H:%M')
    else:
        last_backup = 'Never'
    
    return jsonify({
        'success': True,
        'stats': {
            'dbSize': format_bytes(db_size),
            'totalBackups': stats['total_backups'] or 0,
            'lastBackup': last_backup,
            'storageUsed': format_bytes(total_size),
            'storageLimit': '1 GB',
            'storagePercent': min(round((total_size / (1024 * 1024 * 1024)) * 100, 1), 100),
            'restorePoints': stats['restore_points'] or 0,
            'autoBackups': stats['auto_backups'] or 0,
            'manualBackups': stats['manual_backups'] or 0
        }
    })

@bp.route('/backup/create', methods=['POST'])
@role_required(['super_admin', 'admin'])
def create_backup():
    """Create database backup"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json or {}
    backup_type = data.get('type', 'manual')
    description = data.get('description', '')
    is_restore_point = data.get('isRestorePoint', False)
    
    try:
        if is_restore_point:
            result = manual_backup(description, True)
            backup_type = 'restore_point'
        else:
            result = manual_backup()
        
        if result:
            # Log the action
            log_critical_action(
                session['user_id'],
                'CREATE_BACKUP',
                f'Created {backup_type} backup: {result["name"]}',
                request.remote_addr
            )
            
            return jsonify({
                'success': True,
                'backup': result,
                'message': f'{backup_type.replace("_", " ").title()} created successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Backup failed'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/backup/<int:backup_id>/download', methods=['GET'])
@role_required(['super_admin', 'admin'])
def download_backup(backup_id):
    """Download backup file"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM backup_history WHERE id = %s", (backup_id,))
    backup = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not backup:
        return jsonify({'success': False, 'error': 'Backup not found'}), 404
    
    backup_path = backup['location']
    if not os.path.exists(backup_path):
        return jsonify({'success': False, 'error': 'Backup file not found on server'}), 404
    
    return send_file(
        backup_path,
        as_attachment=True,
        download_name=backup['backup_name'],
        mimetype='application/octet-stream'
    )

@bp.route('/backup/<int:backup_id>', methods=['DELETE'])
@role_required(['super_admin', 'admin'])
def delete_backup(backup_id):
    """Delete backup"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    try:
        cursor.execute("SELECT * FROM backup_history WHERE id = %s", (backup_id,))
        backup = cursor.fetchone()
        
        if not backup:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Backup not found'}), 404
        
        # Delete file if exists
        backup_path = backup['location']
        if os.path.exists(backup_path):
            os.remove(backup_path)
        
        # Delete from database
        cursor.execute("DELETE FROM backup_history WHERE id = %s", (backup_id,))
        conn.commit()
        
        # Log the action
        log_critical_action(
            session['user_id'],
            'DELETE_BACKUP',
            f'Deleted backup: {backup["backup_name"]}',
            request.remote_addr
        )
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Backup deleted successfully'})
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/backup/settings', methods=['GET'])
@role_required(['super_admin', 'admin'])
def get_backup_settings():
    """Get backup settings"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM backup_settings WHERE id = 1")
    settings = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if settings:
        return jsonify({'success': True, 'settings': dict(settings)})
    else:
        return jsonify({
            'success': True,
            'settings': {
                'schedule': 'weekly',
                'retention_days': 30,
                'location': 'both',
                'compression': 'normal',
                'encryption': 'aes256'
            }
        })

@bp.route('/backup/settings', methods=['POST'])
@role_required(['super_admin', 'admin'])
def update_backup_settings():
    """Update backup settings"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    conn, cursor = get_db()
    
    try:
        cursor.execute("""
            UPDATE backup_settings SET
                schedule = %s,
                retention_days = %s,
                location = %s,
                compression = %s,
                encryption = %s,
                updated_at = %s,
                updated_by = %s
            WHERE id = 1
        """, (
            data.get('schedule', 'weekly'),
            data.get('retention_days', 30),
            data.get('location', 'both'),
            data.get('compression', 'normal'),
            data.get('encryption', 'aes256'),
            datetime.now(),
            session['user_id']
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Backup settings updated successfully'})
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/backup/restore/<int:backup_id>', methods=['POST'])
@super_admin_required
def restore_backup(backup_id):
    """Restore database from backup (Super Admin only)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    try:
        cursor.execute("SELECT * FROM backup_history WHERE id = %s", (backup_id,))
        backup = cursor.fetchone()
        
        if not backup:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Backup not found'}), 404
        
        backup_path = backup['location']
        if not os.path.exists(backup_path):
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Backup file not found on server'}), 404
        
        # Get database URL from environment
        import os
        import re
        import subprocess
        
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if not DATABASE_URL:
            return jsonify({'success': False, 'error': 'DATABASE_URL not found'}), 500
        
        # Parse database URL
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
        if not match:
            return jsonify({'success': False, 'error': 'Could not parse DATABASE_URL'}), 500
        
        user, password, host, port, database = match.groups()
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        # Run pg_restore
        cmd = [
            'pg_restore',
            '-h', host,
            '-p', str(port),
            '-U', user,
            '-d', database,
            '-c',  # Clean (drop) database objects before recreating
            '--if-exists',  # Use IF EXISTS when dropping objects
            backup_path
        ]
        
        print(f"🔄 Running pg_restore: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ pg_restore failed: {result.stderr}")
            return jsonify({'success': False, 'error': f'Restore failed: {result.stderr}'}), 500
        
        # Log the action
        log_critical_action(
            session['user_id'],
            'RESTORE_BACKUP',
            f'Restored database from backup: {backup["backup_name"]}',
            request.remote_addr
        )
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Database restored successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/backup/verify/<int:backup_id>', methods=['POST'])
@role_required(['super_admin', 'admin'])
def verify_backup(backup_id):
    """Verify backup integrity"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    try:
        cursor.execute("SELECT * FROM backup_history WHERE id = %s", (backup_id,))
        backup = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not backup:
            return jsonify({'success': False, 'error': 'Backup not found'}), 404
        
        backup_path = backup['location']
        if not os.path.exists(backup_path):
            return jsonify({'success': False, 'error': 'Backup file not found on server'}), 404
        
        # Simple verification - check if file exists and has size
        file_size = os.path.getsize(backup_path)
        
        if file_size > 0:
            return jsonify({
                'success': True,
                'message': 'Backup verified successfully',
                'fileSize': format_bytes(file_size),
                'fileName': backup['backup_name']
            })
        else:
            return jsonify({'success': False, 'error': 'Backup file is empty'}), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Helper function to format bytes
def format_bytes(bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"

# ==================== DASHBOARD STATS ====================

@bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    conn, cursor = get_db()
    
    try:
        cursor.execute('SELECT COUNT(*) as count FROM travelers')
        travelers_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM batches')
        batches_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM batches WHERE status = %s', ('Open',))
        active_batches = cursor.fetchone()['count']
        
        cursor.execute('''
            SELECT 
                COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as total_collected,
                COALESCE(SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END), 0) as pending_amount,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as paid_count,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count
            FROM payments
        ''')
        
        payment_stats = cursor.fetchone()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN is_active = true THEN 1 ELSE 0 END) as active_users
            FROM users
        ''')
        
        user_stats = cursor.fetchone()
        
        cursor.execute('''
            SELECT id, first_name, last_name, passport_no, created_at 
            FROM travelers 
            ORDER BY created_at DESC 
            LIMIT 5
        ''')
        recent_travelers = cursor.fetchall()
        
        cursor.execute('''
            SELECT 
                p.*, t.first_name, t.last_name, t.passport_no
            FROM payments p
            JOIN travelers t ON p.traveler_id = t.id
            ORDER BY p.created_at DESC 
            LIMIT 5
        ''')
        recent_payments = cursor.fetchall()
        
        cursor.execute('''
            SELECT id, batch_name, departure_date, booked_seats, total_seats
            FROM batches
            WHERE departure_date >= CURRENT_DATE
            ORDER BY departure_date ASC
            LIMIT 5
        ''')
        upcoming_batches = cursor.fetchall()
        
        cursor.execute('''
            SELECT 
                status,
                COUNT(*) as count,
                SUM(total_seats) as total_seats,
                SUM(booked_seats) as booked_seats
            FROM batches
            GROUP BY status
        ''')
        batch_distribution = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_travelers': travelers_count,
                'total_batches': batches_count,
                'active_batches': active_batches,
                'total_collected': float(payment_stats['total_collected']) if payment_stats['total_collected'] else 0,
                'pending_amount': float(payment_stats['pending_amount']) if payment_stats['pending_amount'] else 0,
                'paid_count': payment_stats['paid_count'] or 0,
                'pending_count': payment_stats['pending_count'] or 0,
                'total_users': user_stats['total_users'] or 0,
                'active_users': user_stats['active_users'] or 0
            },
            'recent_travelers': [dict(rt) for rt in recent_travelers],
            'recent_payments': [dict(rp) for rp in recent_payments],
            'upcoming_batches': [dict(ub) for ub in upcoming_batches],
            'batch_distribution': [dict(bd) for bd in batch_distribution]
        })
        
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== TABLE COUNTS HELPER ====================

@bp.route('/table-counts', methods=['GET'])
def get_table_counts():
    """Get count of records in all tables"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    try:
        tables = ['users', 'batches', 'travelers', 'payments', 'invoices', 'receipts']
        counts = {}
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            result = cursor.fetchone()
            counts[table] = result['count'] if result else 0
            
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'counts': counts
        })
        
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== HEALTH CHECK ====================

@bp.route('/health', methods=['GET'])
def system_health():
    """Get system health information"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    try:
        tables = ['travelers', 'batches', 'payments', 'users', 'invoices', 'receipts']
        counts = {}
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            counts[table] = cursor.fetchone()['count']
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'health': {
                'status': 'healthy',
                'record_counts': counts,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500
