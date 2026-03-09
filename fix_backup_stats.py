#!/usr/bin/env python3
import re

with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the get_backup_stats function and replace it
pattern = r'@bp\.route\(\'/backups/stats\'.*?def get_backup_stats\(.*?return jsonify\(.*?\)'
replacement = '''@bp.route('/backups/stats', methods=['GET'])
def get_backup_stats():
    """Get backup statistics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    cursor.execute("""
        SELECT 
            COUNT(*) as total_backups,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful,
            COUNT(CASE WHEN created_at > NOW() - INTERVAL '30 days' THEN 1 END) as last_30_days
        FROM backup_history
    """)
    stats = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'data': stats}), 200'''

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Fixed get_backup_stats function")