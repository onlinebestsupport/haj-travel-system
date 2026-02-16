from flask import Blueprint, jsonify

batches_bp = Blueprint('batches', __name__)

@batches_bp.route('/', methods=['GET'])
def get_batches():
    return jsonify({
        'success': True,
        'message': 'Batches API - Coming soon',
        'batches': []
    })
