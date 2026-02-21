from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@bp.route('/users', methods=['GET'])
def get_users():
    """Get all users (admin only)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, username, name, email, role, is_active, created_at
        FROM users ORDER BY id
    ''')
    users = cursor.fetchall()
    db.close()
    
    return jsonify({'success': True, 'users': [dict(u) for u in users]})

@bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT COUNT(*) as count FROM travelers')
    travelers_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM batches WHERE status = "Open"')
    active_batches = cursor.fetchone()['count']
    
    cursor.execute('SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE status = "completed"')
    total_collected = cursor.fetchone()['total']
    
    cursor.execute('SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE status = "pending"')
    pending_amount = cursor.fetchone()['total']
    
    # Get recent activity
    cursor.execute('''
        SELECT "traveler" as type, first_name || " " || last_name as name, created_at 
        FROM travelers 
        ORDER BY created_at DESC 
        LIMIT 3
    ''')
    recent = cursor.fetchall()
    
    db.close()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_travelers': travelers_count,
            'active_batches': active_batches,
            'total_collected': float(total_collected) if total_collected else 0,
            'pending_amount': float(pending_amount) if pending_amount else 0
        },
        'recent_activity': [dict(r) for r in recent]
    })