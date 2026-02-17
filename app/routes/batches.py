from flask import Blueprint, jsonify
from app.database import get_db
import psycopg2.extras

batches_bp = Blueprint('batches', __name__)

@batches_bp.route('/', methods=['GET'])
def get_batches():
    """Get all batches/packages"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': True, 'batches': []})
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM batches ORDER BY departure_date")
        batches = cur.fetchall()
        cur.close()
        conn.close()
        
        # Convert decimal to float for JSON serialization
        for batch in batches:
            if 'price' in batch and batch['price']:
                batch['price'] = float(batch['price'])
        
        return jsonify({'success': True, 'batches': batches})
    except Exception as e:
        print(f"Error in batches: {e}")
        return jsonify({'success': True, 'batches': []})
