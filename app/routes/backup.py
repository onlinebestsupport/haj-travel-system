from flask import Blueprint, jsonify, session
from app.database import get_db, release_db
import traceback
import datetime
import logging

# Setup logger instead of print statements
logger = logging.getLogger(__name__)

bp = Blueprint('backup', __name__, url_prefix='/api/backup')

@bp.route('', methods=['GET'])
def get_backups():
    """Get all backups - Admin only"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401

        conn, cursor = get_db()
        try:
            cursor.execute('SELECT * FROM backup_history ORDER BY created_at DESC')
            backups = cursor.fetchall()
            return jsonify({'success': True, 'backups': [dict(b) for b in backups]})
        except Exception as e:
            logger.error(f"Backup query error: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            release_db(conn, cursor)
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'success': False, 'error': 'Server error'}), 500


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
        
        logger.info(f"Backup {filename} created by user {session.get('user_id')}")
        
        return jsonify({
            'success': True,
            'message': 'Backup created successfully',
            'backup_id': row['id'] if row else None
        })
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Create backup error: {str(e)}")
        return jsonify({'success': False, 'error': 'Error creating backup'}), 500
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
        
        # Check if backup exists
        cursor.execute('SELECT id FROM backup_history WHERE id = %s', (backup_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Backup not found'}), 404
        
        # Delete the backup
        cursor.execute('DELETE FROM backup_history WHERE id = %s', (backup_id,))
        conn.commit()
        
        logger.info(f"Backup {backup_id} deleted by user {session.get('user_id')}")
        
        return jsonify({'success': True, 'message': 'Backup deleted successfully'})
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Delete backup error: {str(e)}")
        return jsonify({'success': False, 'error': 'Error deleting backup'}), 500
    finally:
        release_db(conn, cursor)
