from flask import Blueprint, request, jsonify, session
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
