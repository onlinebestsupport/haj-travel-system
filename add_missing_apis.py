#!/usr/bin/env python3
"""
Add missing API endpoints
Run: python add_missing_apis_fixed.py
"""

import os

def add_to_admin_py():
    """Add backup API endpoints to admin.py"""
    admin_path = "app/routes/admin.py"
    
    backup_apis = """

# ==================== BACKUP API ENDPOINTS ====================

@bp.route('/backup/settings', methods=['GET'])
def get_backup_settings():
    \"\"\"Get backup settings\"\"\"
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT * FROM backup_settings LIMIT 1")
        settings = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'data': settings}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/backup/create', methods=['POST'])
def create_backup():
    \"\"\"Create a new backup\"\"\"
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        conn, cursor = get_db()
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cursor.execute(\"\"\"
            INSERT INTO backup_history (backup_name, status, created_at, created_by)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        \"\"\", (backup_name, 'completed', datetime.now(), session['user_id']))
        
        backup_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'backup_id': backup_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/backups/stats', methods=['GET'])
def get_backup_stats():
    \"\"\"Get backup statistics\"\"\"
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        conn, cursor = get_db()
        cursor.execute(\"\"\"
            SELECT 
                COUNT(*) as total_backups,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful,
                MAX(created_at) as last_backup
            FROM backup_history
        \"\"\")
        stats = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'data': stats}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
"""
    
    with open(admin_path, 'a') as f:
        f.write(backup_apis)
    print(f"✅ Added backup APIs to {admin_path}")

def add_to_payments_py():
    """Add payment stats endpoint"""
    payments_path = "app/routes/payments.py"
    
    stats_api = """

@bp.route('/stats', methods=['GET'])
def get_payment_stats():
    \"\"\"Get payment statistics\"\"\"
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        conn, cursor = get_db()
        cursor.execute(\"\"\"
            SELECT 
                COUNT(*) as total_payments,
                COALESCE(SUM(amount), 0) as total_amount,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count
            FROM payments
        \"\"\")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'stats': dict(result)}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
"""
    
    try:
        with open(payments_path, 'a') as f:
            f.write(stats_api)
        print(f"✅ Added payment stats to {payments_path}")
    except FileNotFoundError:
        print(f"⚠️ {payments_path} not found")

if __name__ == '__main__':
    print("🚀 Adding missing APIs...")
    add_to_admin_py()
    add_to_payments_py()
    print("✅ Done!")
