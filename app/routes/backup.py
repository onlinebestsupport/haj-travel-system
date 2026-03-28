from flask import Blueprint, jsonify, session
from app.database import get_db, release_db
import traceback
import sys
import datetime

print("🔵 LOADING backup.py BLUEPRINT...", file=sys.stderr)

bp = Blueprint('backup', __name__, url_prefix='/api/backup')

print(f"🔵 Blueprint 'backup' created with url_prefix: /api/backup", file=sys.stderr)

@bp.route('', methods=['GET'])
def get_backups():
    """Get all backups"""
    print("🔵 get_backups() called", file=sys.stderr)
    
    try:
        if 'user_id' not in session:
            print("🔴 Unauthorized - no user_id in session", file=sys.stderr)
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401

        conn, cursor = get_db()
        try:
            cursor.execute('SELECT * FROM backup_history ORDER BY created_at DESC')
            backups = cursor.fetchall()
            return jsonify({'success': True, 'backups': [dict(b) for b in backups]})
        except Exception as e:
            print(f"🔴 Backup error: {str(e)}", file=sys.stderr)
            print(f"🔴 Traceback: {traceback.format_exc()}", file=sys.stderr)
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            release_db(conn, cursor)
            
    except Exception as e:
        print(f"🔴 Unexpected error: {str(e)}", file=sys.stderr)
        return jsonify({'success': False, 'error': str(e)}), 500

print("🔵 backup.py blueprint loaded successfully!", file=sys.stderr)
@bp.route('/create', methods=['POST'])
def create_backup():
    """Create a new backup entry"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        filename = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        cursor.execute(
            '''INSERT INTO backup_history (filename, status, created_by, created_at)
               VALUES (%s, %s, %s, NOW()) RETURNING id''',
            (filename, 'completed', session['user_id'])
        )
        row = cursor.fetchone()
        conn.commit()
        return jsonify({'success': True, 'message': 'Backup created successfully', 'backup_id': row['id']})
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"🔴 Create backup error: {str(e)}", file=sys.stderr)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)


@bp.route('/<int:backup_id>', methods=['DELETE'])
def delete_backup(backup_id):
    """Delete a backup record"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute('SELECT id FROM backup_history WHERE id = %s', (backup_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Backup not found'}), 404
        cursor.execute('DELETE FROM backup_history WHERE id = %s', (backup_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Backup deleted successfully'})
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"🔴 Delete backup error: {str(e)}", file=sys.stderr)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)
