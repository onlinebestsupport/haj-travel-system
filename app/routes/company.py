from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime

bp = Blueprint('company', __name__, url_prefix='/api/company')

@bp.route('/settings', methods=['GET'])
def get_settings():
    """Get company settings"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM company_settings WHERE id = 1')
    settings = cursor.fetchone()
    db.close()
    
    return jsonify({'success': True, 'settings': dict(settings) if settings else {}})

@bp.route('/settings', methods=['PUT'])
def update_settings():
    """Update company settings"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('''
            UPDATE company_settings SET
                company_name = ?, address = ?, phone = ?,
                email = ?, website = ?, gst_no = ?,
                pan_no = ?, logo = ?, updated_at = ?
            WHERE id = 1
        ''', (
            data.get('company_name'),
            data.get('address'),
            data.get('phone'),
            data.get('email'),
            data.get('website'),
            data.get('gst_no'),
            data.get('pan_no'),
            data.get('logo'),
            datetime.now().isoformat()
        ))
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'message': 'Settings updated successfully'})
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400