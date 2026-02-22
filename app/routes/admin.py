from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime
import json

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
    
    # Parse permissions JSON for each user
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
def create_user():
    """Create new user with permissions"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    # Validate required fields
    required = ['username', 'password', 'email', 'role']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    # Validate password length
    if len(data['password']) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
    
    # Process permissions
    permissions = data.get('permissions', {})
    if isinstance(permissions, dict):
        permissions_json = json.dumps(permissions)
    else:
        permissions_json = permissions
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if username exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (data['username'],))
        if cursor.fetchone():
            db.close()
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
        
        # Check if email exists
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
            data['password'],  # In production, hash this!
            data.get('full_name'),
            data['email'],
            data.get('phone'),
            data.get('department'),
            data['role'],
            permissions_json,
            1,  # is_active = true by default
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        user_id = cursor.lastrowid
        
        # Log activity
        log_activity(session['user_id'], 'create', 'user', f'Created user: {data["username"]}')
        
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
def update_user(user_id):
    """Update user details and permissions"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if user exists
        cursor.execute('SELECT id, username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if not user:
            db.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Check if email is taken by another user
        if data.get('email'):
            cursor.execute('SELECT id FROM users WHERE email = ? AND id != ?', (data['email'], user_id))
            if cursor.fetchone():
                db.close()
                return jsonify({'success': False, 'error': 'Email already in use by another user'}), 400
        
        # Process permissions
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
        
        # Log activity
        log_activity(session['user_id'], 'update', 'user', f'Updated user: {user["username"]}')
        
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'message': 'User updated successfully'})
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/users/<int:user_id>/password', methods=['POST'])
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
        
        # Log activity
        log_activity(session['user_id'], 'password', 'user', f'Changed password for user: {user["username"]}')
        
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/users/<int:user_id>/toggle', methods=['POST'])
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
        
        # Log activity
        status_text = 'activated' if new_status else 'deactivated'
        log_activity(session['user_id'], 'toggle', 'user', f'{status_text} user: {user["username"]}')
        
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
def delete_user(user_id):
    """Delete user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # Prevent deleting yourself
    if user_id == session['user_id']:
        return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            db.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        # Log activity
        log_activity(session['user_id'], 'delete', 'user', f'Deleted user: {user["username"]}')
        
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'message': 'User deleted successfully'})
        
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
    
    # Basic counts
    cursor.execute('SELECT COUNT(*) as count FROM travelers')
    travelers_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM batches')
    batches_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM batches WHERE status = "Open"')
    active_batches = cursor.fetchone()['count']
    
    # Payment stats
    cursor.execute('''
        SELECT 
            COALESCE(SUM(CASE WHEN status = "completed" THEN amount ELSE 0 END), 0) as total_collected,
            COALESCE(SUM(CASE WHEN status = "pending" THEN amount ELSE 0 END), 0) as pending_amount,
            COUNT(CASE WHEN status = "completed" THEN 1 END) as paid_count,
            COUNT(CASE WHEN status = "pending" THEN 1 END) as pending_count
        FROM payments
    ''')
    
    payment_stats = cursor.fetchone()
    
    # User stats
    cursor.execute('''
        SELECT 
            COUNT(*) as total_users,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_users
        FROM users
    ''')
    
    user_stats = cursor.fetchone()
    
    # Recent travelers
    cursor.execute('''
        SELECT id, first_name, last_name, passport_no, created_at 
        FROM travelers 
        ORDER BY created_at DESC 
        LIMIT 5
    ''')
    recent_travelers = cursor.fetchall()
    
    # Recent payments
    cursor.execute('''
        SELECT 
            p.*, t.first_name, t.last_name, t.passport_no
        FROM payments p
        JOIN travelers t ON p.traveler_id = t.id
        ORDER BY p.created_at DESC 
        LIMIT 5
    ''')
    recent_payments = cursor.fetchall()
    
    # Upcoming batches
    cursor.execute('''
        SELECT id, batch_name, departure_date, booked_seats, total_seats
        FROM batches
        WHERE departure_date >= date('now')
        ORDER BY departure_date ASC
        LIMIT 5
    ''')
    upcoming_batches = cursor.fetchall()
    
    # Batch distribution
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

# ==================== SYSTEM HEALTH ====================

@bp.route('/health', methods=['GET'])
def system_health():
    """Get system health information"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    # Get database size
    cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
    db_size = cursor.fetchone()
    
    # Get table counts
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
def reset_database():
    """Reset database with sample data (DEVELOPMENT ONLY)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # Only allow super_admin
    if session.get('role') != 'super_admin':
        return jsonify({'success': False, 'error': 'Super admin only'}), 403
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Disable foreign keys temporarily
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Delete all data from tables
        cursor.execute("DELETE FROM payments")
        cursor.execute("DELETE FROM receipts")
        cursor.execute("DELETE FROM invoices")
        cursor.execute("DELETE FROM travelers")
        cursor.execute("DELETE FROM batches")
        cursor.execute("DELETE FROM users WHERE username IN ('superadmin', 'admin1', 'manager1', 'staff1', 'viewer1')")
        cursor.execute("DELETE FROM activity_log")
        cursor.execute("DELETE FROM backup_history")
        
        # Reset auto-increment counters
        cursor.execute("DELETE FROM sqlite_sequence")
        
        # Re-enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Insert default users
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
        
        # Insert batches
        batches = [
            ('Haj Platinum 2026', 50, 850000, '2026-06-14', '2026-07-31', 'Open', 
             'Premium Haj package with 5-star accommodation near Haram',
             'Day 1: Arrival Jeddah, Day 2-7: Makkah, Day 8-13: Mina/Arafat/Muzdalifah, Day 14-20: Madinah',
             '5-star hotel, VIP transport, expert guide, meals, visa processing',
             'Airfare not included, personal expenses',
             'Pullman ZamZam Makkah (5-star)',
             'Private AC buses',
             'Full board (breakfast, lunch, dinner)'),
            
            ('Haj Gold 2026', 100, 550000, '2026-06-15', '2026-07-30', 'Open',
             'Standard Haj package with 4-star accommodation',
             'Day 1-20: Standard Haj itinerary',
             '4-star hotel, transport, guide, meals',
             'Airfare, personal expenses',
             'Makkah Hotel (4-star)',
             'Shared AC buses',
             'Half board (breakfast & dinner)'),
            
            ('Umrah Ramadhan Special', 200, 125000, '2026-03-01', '2026-03-20', 'Closing Soon',
             'Special Umrah package for the last 10 days of Ramadhan',
             'Day 1-20: Umrah itinerary with focus on Ramadhan',
             '3-star hotel, transport, guide',
             'Airfare, meals',
             'Dar Al Tawhid (3-star)',
             'Shared buses',
             'Breakfast only'),
            
            ('Haj Silver 2026', 150, 350000, '2026-06-20', '2026-07-28', 'Open',
             'Economy Haj package for budget-conscious pilgrims',
             'Day 1-20: Standard Haj itinerary',
             '3-star hotel, transport, basic guidance',
             'Airfare, meals, extras',
             'Al Safwah Hotel (3-star)',
             'Economy buses',
             'No meals included')
        ]
        
        for batch in batches:
            cursor.execute('''
                INSERT INTO batches (
                    batch_name, total_seats, price, departure_date, return_date, status, description,
                    itinerary, inclusions, exclusions, hotel_details, transport_details, meal_plan,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            ''', batch)
        
        # Insert travelers
        travelers = [
            ('Ahmed', 'Khan', 'Ahmed Khan', 1, 'A1234567', '2020-01-15', '2030-01-14', 'Active', 'Male', '1985-06-15',
             '9876543210', 'ahmed@email.com', '123456789012', 'ABCDE1234F', 'Yes', 'Fully Vaccinated', 'No',
             'Mumbai', 'Mumbai', '123, Green Street, Andheri East, Mumbai - 400093',
             'Abdullah Khan', 'Amina Khan', '', '1234', 'Brother', '9876543211', 'No known allergies',
             '{"blood_group":"O+","allergies":"None"}'),
            
            ('Fatima', 'Begum', 'Fatima Begum', 2, 'B7654321', '2019-08-20', '2029-08-19', 'Active', 'Female', '1990-11-22',
             '8765432109', 'fatima@email.com', '234567890123', 'FGHIJ5678K', 'Pending', 'Partially Vaccinated', 'No',
             'Delhi', 'Delhi', '456, Lotus Apartments, Saket, New Delhi - 110017',
             'Mohammed Ali', 'Zainab Ali', 'Hasan Raza', '5678', 'Husband', '8765432100', 'Diabetic',
             '{"blood_group":"B+","allergies":"None"}'),
            
            ('Mohammed', 'Rafiq', 'Mohammed Rafiq', 3, 'C9876543', '2021-03-10', '2031-03-09', 'Processing', 'Male', '1978-03-08',
             '7654321098', 'rafiq@email.com', '345678901234', 'KLMNO9012P', 'No', 'Not Vaccinated', 'Yes',
             'Hyderabad', 'Hyderabad', '789, Old City, Hyderabad - 500002',
             'Abdul Rafiq', 'Razia Sultana', '', '9012', 'Son', '7654321000', 'Requires wheelchair assistance',
             '{"blood_group":"A+","allergies":"Dust"}')
        ]
        
        for traveler in travelers:
            cursor.execute('''
                INSERT INTO travelers (
                    first_name, last_name, passport_name, batch_id, passport_no,
                    passport_issue_date, passport_expiry_date, passport_status, gender, dob,
                    mobile, email, aadhaar, pan, aadhaar_pan_linked, vaccine_status, wheelchair,
                    place_of_birth, place_of_issue, passport_address, father_name, mother_name, spouse_name,
                    pin, emergency_contact, emergency_phone, medical_notes, extra_fields,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            ''', traveler)
        
        # Update batch booked seats
        cursor.execute("UPDATE batches SET booked_seats = (SELECT COUNT(*) FROM travelers WHERE batch_id = 1) WHERE id = 1")
        cursor.execute("UPDATE batches SET booked_seats = (SELECT COUNT(*) FROM travelers WHERE batch_id = 2) WHERE id = 2")
        cursor.execute("UPDATE batches SET booked_seats = (SELECT COUNT(*) FROM travelers WHERE batch_id = 3) WHERE id = 3")
        
        # Insert payments
        payments = [
            (1, 1, 85000, '2026-01-15', 'Bank Transfer', 'TXN123456', 'Booking Amount', 'completed', 'Booking payment received'),
            (1, 1, 85000, '2026-02-15', 'Bank Transfer', 'TXN123457', '1st Installment', 'completed', 'First installment'),
            (2, 2, 550000, '2026-01-20', 'UPI', 'UPI123456', 'Full Payment', 'completed', 'Full payment received'),
            (3, 3, 25000, '2026-02-01', 'Cash', 'CASH001', 'Booking Amount', 'pending', 'Booking amount pending')
        ]
        
        for payment in payments:
            cursor.execute('''
                INSERT INTO payments (traveler_id, batch_id, amount, payment_date, payment_method, transaction_id, installment, status, remarks, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ''', payment)
        
        db.commit()
        
        # Log activity
        log_activity(session['user_id'], 'reset', 'database', 'Database reset with sample data')
        
        db.close()
        
        return jsonify({
            'success': True, 
            'message': 'Database reset successfully with sample data'
        })
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== HELPER FUNCTIONS ====================

def log_activity(user_id, action, module, description):
    """Log user activity"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO activity_log (user_id, action, module, description, ip_address) VALUES (?, ?, ?, ?, ?)',
            (user_id, action, module, description, request.remote_addr)
        )
        db.commit()
        db.close()
    except:
        pass  # Fail silently
