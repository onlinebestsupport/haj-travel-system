from flask import Blueprint, request, jsonify
from app.database import get_db
import psycopg2
import psycopg2.extras

travelers_bp = Blueprint('travelers', __name__)

@travelers_bp.route('/', methods=['GET'])
def get_all_travelers():
    """Get all travelers"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM travelers ORDER BY created_at DESC")
        travelers = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'travelers': travelers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/<int:traveler_id>', methods=['GET'])
def get_traveler(traveler_id):
    """Get a single traveler"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM travelers WHERE id = %s", (traveler_id,))
        traveler = cur.fetchone()
        cur.close()
        conn.close()
        
        if traveler:
            return jsonify({'success': True, 'traveler': traveler})
        return jsonify({'success': False, 'error': 'Not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/', methods=['POST'])
def create_traveler():
    """Create a traveler"""
    try:
        data = request.json
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO travelers (first_name, last_name, passport_no, mobile, email, pin)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get('first_name'),
            data.get('last_name'),
            data.get('passport_no'),
            data.get('mobile'),
            data.get('email'),
            data.get('pin', '0000')
        ))
        traveler_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'traveler_id': traveler_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@travelers_bp.route('/passport/<passport_no>', methods=['GET'])
def get_traveler_by_passport(passport_no):
    """Get traveler by passport number"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM travelers WHERE passport_no = %s", (passport_no,))
        traveler = cur.fetchone()
        cur.close()
        conn.close()
        
        if traveler:
            return jsonify({'success': True, 'traveler': traveler})
        return jsonify({'success': False}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
