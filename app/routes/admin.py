from flask import Blueprint, jsonify

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/status', methods=['GET'])
def status():
    return jsonify({
        'success': True,
        'message': 'Admin blueprint loaded',
        'status': 'active'
    })
