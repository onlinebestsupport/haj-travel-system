from flask import Blueprint, request, jsonify, current_app, send_file
import os
import uuid
from werkzeug.utils import secure_filename
import datetime

uploads_bp = Blueprint('uploads', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_folder():
    upload_folder = os.path.join(current_app.root_path, '..', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder

@uploads_bp.route('/', methods=['GET'])
def status():
    return jsonify({'success': True, 'message': 'Upload API working'})

@uploads_bp.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        new_filename = f"{timestamp}_{unique_id}_{filename}"
        
        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, new_filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'filename': new_filename,
            'size': os.path.getsize(file_path)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@uploads_bp.route('/file/<filename>', methods=['GET'])
def get_file(filename):
    try:
        safe_filename = secure_filename(filename)
        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, safe_filename)
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        return jsonify({'success': False, 'error': 'Not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
