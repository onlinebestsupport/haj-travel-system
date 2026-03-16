from flask import Blueprint, jsonify, session
from app.database import get_db, release_db
import traceback
import sys

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