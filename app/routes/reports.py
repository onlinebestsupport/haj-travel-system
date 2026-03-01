from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime
import json

bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@bp.route('/generate', methods=['POST'])
def generate_report():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    report_type = data.get('type')
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    batch_id = data.get('batchId')
    status = data.get('status')
    
    conn, cursor = get_db()
    
    try:
        if report_type == 'traveler':
            query = """
                SELECT t.*, b.batch_name
                FROM travelers t
                LEFT JOIN batches b ON t.batch_id = b.id
                WHERE 1=1
            """
            params = []
            
            if start_date and end_date:
                query += " AND t.created_at BETWEEN %s AND %s"
                params.extend([start_date, end_date])
            
            if batch_id and batch_id != 'all':
                query += " AND t.batch_id = %s"
                params.append(batch_id)
            
            if status and status != 'all':
                query += " AND t.passport_status = %s"
                params.append(status)
            
            cursor.execute(query, params)
            travelers = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'report': {
                    'travelers': travelers,
                    'summary': {
                        'total': len(travelers)
                    }
                }
            })
        
        # Add other report types similarly...
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
