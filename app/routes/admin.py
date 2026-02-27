from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime
import json
from app.middleware import role_required, super_admin_required, log_critical_action, auto_backup

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ==================== USER MANAGEMENT ====================

@bp.route('/users', methods=['GET'])
def get_users():
    """Get all users with complete details"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
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
    db.close()
    
    result = []
    for user in users:
        user_dict = dict(user)
        if user_dict.get('permissions'):
            try:
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
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            id, username, full_name, email, phone, department,
            role, permissions, is_active, last_login, created_at, updated_at
        FROM users 
        WHERE id = ?
    ''', (user_id,))
    
    user = cursor.fetchone()
    db.close()
    
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    user_dict = dict(user)
    if user_dict.get('permissions'):
        try:
            user_dict['permissions'] = json.loads(user_dict['permissions'])
        except:
            user_dict['permissions'] = {}
    else:
        user_dict['permissions'] = {}
    
    return jsonify({'success': True, 'user': user_dict})

@bp.route('/users', methods=['POST'])
@role_required(['super_admin', 'admin'])
def create_user():
    """Create new user with permissions"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    required = ['username', 'password', 'email', 'role']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    if len(data['password']) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
    
    permissions = data.get('permissions', {})
    if isinstance(permissions, dict):
        permissions_json = json.dumps(permissions)
    else:
        permissions_json = permissions
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('SELECT id FROM users WHERE username = ?', (data['username'],))
        if cursor.fetchone():
            db.close()
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
        
        cursor.execute('SELECT id FROM users WHERE email = ?', (data['email'],))
        if cursor.fetchone():
            db.close()
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
        
        cursor.execute('''
            INSERT INTO users (
                username, password, full_name, email, phone, department,
                role, permissions, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['username'],
            data['password'],
            data.get('full_name'),
            data['email'],
            data.get('phone'),
            data.get('department'),
            data['role'],
            permissions_json,
            1,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        user_id = cursor.lastrowid
        
        log_critical_action(
            session['user_id'], 
            'CREATE_USER', 
            f'Created user: {data["username"]} (ID: {user_id})',
            request.remote_addr
        )
        
        db.commit()
        db.close()
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'User created successfully'
        })
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/users/<int:user_id>', methods=['PUT'])
@role_required(['super_admin', 'admin'])
def update_user(user_id):
    """Update user details and permissions"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('SELECT id, username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if not user:
            db.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        if data.get('email'):
            cursor.execute('SELECT id FROM users WHERE email = ? AND id != ?', (data['email'], user_id))
            if cursor.fetchone():
                db.close()
                return jsonify({'success': False, 'error': 'Email already in use'}), 400
        
        permissions = data.get('permissions', {})
        if isinstance(permissions, dict):
            permissions_json = json.dumps(permissions)
        else:
            permissions_json = permissions
        
        cursor.execute('''
            UPDATE users SET
                full_name = ?,
                email = ?,
                phone = ?,
                department = ?,
                role = ?,
                permissions = ?,
                is_active = ?,
                updated_at = ?
            WHERE id = ?
        ''', (
            data.get('full_name'),
            data.get('email'),
            data.get('phone'),
            data.get('department'),
            data.get('role'),
            permissions_json,
            data.get('is_active', 1),
            datetime.now().isoformat(),
            user_id
        ))
        
        log_critical_action(
            session['user_id'], 
            'UPDATE_USER', 
            f'Updated user: {user["username"]} (ID: {user_id})',
            request.remote_addr
        )
        
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'message': 'User updated successfully'})
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/users/<int:user_id>/password', methods=['POST'])
@role_required(['super_admin', 'admin'])
def change_user_password(user_id):
    """Change user password"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    new_password = data.get('new_password')
    
    if not new_password or len(new_password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            db.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        cursor.execute('''
            UPDATE users SET
                password = ?,
                updated_at = ?
            WHERE id = ?
        ''', (new_password, datetime.now().isoformat(), user_id))
        
        log_critical_action(
            session['user_id'], 
            'PASSWORD_CHANGE', 
            f'Changed password for user: {user["username"]} (ID: {user_id})',
            request.remote_addr
        )
        
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@role_required(['super_admin', 'admin'])
def toggle_user_status(user_id):
    """Toggle user active status"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('SELECT is_active, username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            db.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        new_status = 0 if user['is_active'] else 1
        
        cursor.execute('''
            UPDATE users SET
                is_active = ?,
                updated_at = ?
            WHERE id = ?
        ''', (new_status, datetime.now().isoformat(), user_id))
        
        status_text = 'activated' if new_status else 'deactivated'
        
        log_critical_action(
            session['user_id'], 
            'TOGGLE_STATUS', 
            f'{status_text} user: {user["username"]} (ID: {user_id})',
            request.remote_addr
        )
        
        db.commit()
        db.close()
        
        return jsonify({
            'success': True,
            'is_active': bool(new_status),
            'message': f'User {status_text} successfully'
        })
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/users/<int:user_id>', methods=['DELETE'])
@super_admin_required
def delete_user(user_id):
    """Delete user - SUPER ADMIN ONLY"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    if user_id == session['user_id']:
        return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
    
    backup_file = auto_backup()
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            db.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        log_critical_action(
            session['user_id'], 
            'DELETE_USER', 
            f'Deleted user: {user["username"]} (ID: {user_id})',
            request.remote_addr
        )
        
        db.commit()
        db.close()
        
        return jsonify({
            'success': True, 
            'message': 'User deleted successfully',
            'backup': backup_file
        })
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

# ==================== DASHBOARD STATS ====================

@bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT COUNT(*) as count FROM travelers')
    travelers_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM batches')
    batches_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM batches WHERE status = "Open"')
    active_batches = cursor.fetchone()['count']
    
    cursor.execute('''
        SELECT 
            COALESCE(SUM(CASE WHEN status = "completed" THEN amount ELSE 0 END), 0) as total_collected,
            COALESCE(SUM(CASE WHEN status = "pending" THEN amount ELSE 0 END), 0) as pending_amount,
            COUNT(CASE WHEN status = "completed" THEN 1 END) as paid_count,
            COUNT(CASE WHEN status = "pending" THEN 1 END) as pending_count
        FROM payments
    ''')
    
    payment_stats = cursor.fetchone()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_users,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_users
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
        WHERE departure_date >= date('now')
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
    
    db.close()
    
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

# ==================== ACTIVITY LOG ====================

@bp.route('/activity', methods=['GET'])
@role_required(['super_admin', 'admin'])
def get_activity_log():
    """Get recent activity log"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    limit = request.args.get('limit', 50, type=int)
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            a.*,
            u.username
        FROM activity_log a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC
        LIMIT ?
    ''', (limit,))
    
    activities = cursor.fetchall()
    db.close()
    
    return jsonify({
        'success': True,
        'activities': [dict(a) for a in activities]
    })

# ==================== CRITICAL LOGS ====================

@bp.route('/critical-logs', methods=['GET'])
@super_admin_required
def get_critical_logs():
    """Get critical action logs - SUPER ADMIN ONLY"""
    limit = request.args.get('limit', 100, type=int)
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            l.*,
            u.username
        FROM critical_logs l
        LEFT JOIN users u ON l.user_id = u.id
        ORDER BY l.timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    logs = cursor.fetchall()
    db.close()
    
    return jsonify({
        'success': True,
        'logs': [dict(l) for l in logs]
    })

# ==================== SYSTEM HEALTH ====================

@bp.route('/health', methods=['GET'])
def system_health():
    """Get system health information"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
    db_size = cursor.fetchone()
    
    tables = ['travelers', 'batches', 'payments', 'users', 'invoices', 'receipts']
    counts = {}
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
        counts[table] = cursor.fetchone()['count']
    
    db.close()
    
    return jsonify({
        'success': True,
        'health': {
            'status': 'healthy',
            'database_size': db_size['size'] if db_size else 0,
            'record_counts': counts,
            'timestamp': datetime.now().isoformat()
        }
    })

# ==================== DATABASE RESET (DEVELOPMENT ONLY) ====================

@bp.route('/reset-database', methods=['POST'])
@super_admin_required
def reset_database():
    """Reset database with sample data - SUPER ADMIN ONLY"""
    try:
        backup_file = auto_backup()
        
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        cursor.execute("DELETE FROM payments")
        cursor.execute("DELETE FROM receipts")
        cursor.execute("DELETE FROM invoices")
        cursor.execute("DELETE FROM travelers")
        cursor.execute("DELETE FROM batches")
        cursor.execute("DELETE FROM users WHERE username IN ('superadmin', 'admin1', 'manager1', 'staff1', 'viewer1')")
        cursor.execute("DELETE FROM activity_log")
        cursor.execute("DELETE FROM critical_logs")
        cursor.execute("DELETE FROM backup_history")
        
        cursor.execute("DELETE FROM sqlite_sequence")
        
        cursor.execute("PRAGMA foreign_keys = ON")
        
        users = [
            ('superadmin', 'admin123', 'Super Admin', 'super@alhudha.com', '9999999999', 'Management', 'super_admin', 
             json.dumps({'dashboard': True, 'batches': True, 'travelers': True, 'payments': True, 'invoices': True,
                        'receipts': True, 'reports': True, 'users': True, 'frontpage': True, 'whatsapp': True,
                        'email': True, 'backup': True})),
            ('admin1', 'admin123', 'Admin User', 'admin@alhudha.com', '8888888888', 'Operations', 'admin',
             json.dumps({'dashboard': True, 'batches': True, 'travelers': True, 'payments': True, 'invoices': True,
                        'receipts': True, 'reports': True, 'users': False, 'frontpage': False, 'whatsapp': True,
                        'email': True, 'backup': False})),
            ('manager1', 'admin123', 'Manager User', 'manager@alhudha.com', '7777777777', 'Sales', 'manager',
             json.dumps({'dashboard': True, 'batches': True, 'travelers': True, 'payments': True, 'invoices': True,
                        'receipts': True, 'reports': True, 'users': False, 'frontpage': False, 'whatsapp': False,
                        'email': False, 'backup': False})),
            ('staff1', 'admin123', 'Staff User', 'staff@alhudha.com', '6666666666', 'Customer Service', 'staff',
             json.dumps({'dashboard': True, 'batches': False, 'travelers': True, 'payments': True, 'invoices': False,
                        'receipts': True, 'reports': False, 'users': False, 'frontpage': False, 'whatsapp': False,
                        'email': False, 'backup': False})),
            ('viewer1', 'admin123', 'Viewer User', 'viewer@alhudha.com', '5555555555', 'Accounts', 'viewer',
             json.dumps({'dashboard': True, 'batches': True, 'travelers': True, 'payments': True, 'invoices': True,
                        'receipts': True, 'reports': True, 'users': False, 'frontpage': False, 'whatsapp': False,
                        'email': False, 'backup': False}))
        ]
        
        for user in users:
            cursor.execute('''
                INSERT INTO users (username, password, full_name, email, phone, department, role, permissions, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, datetime('now'), datetime('now'))
            ''', user)
        
        log_critical_action(
            session['user_id'], 
            'RESET_DATABASE', 
            f'Database reset with backup: {backup_file}',
            request.remote_addr
        )
        
        db.commit()
        db.close()
        
        return jsonify({
            'success': True, 
            'message': 'Database reset successfully',
            'backup': backup_file
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
