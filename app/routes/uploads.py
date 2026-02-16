from flask import Blueprint, request, jsonify, current_app
import os
import uuid
from werkzeug.utils import secure_filename

uploads_bp = Blueprint('uploads', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@uploads_bp.route('/', methods=['GET'])
def upload_status():
    """Check upload API status"""
    return jsonify({
        'success': True,
        'message': 'Upload API is working',
        'endpoints': {
            'upload_file': '/api/uploads/upload (POST)',
            'get_file': '/api/uploads/<filename> (GET)'
        }
    })

@uploads_bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload a file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        traveler_id = request.form.get('traveler_id', 'unknown')
        document_type = request.form.get('document_type', 'other')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            file_ext = original_filename.rsplit('.', 1)[1].lower()
            new_filename = f"{traveler_id}_{document_type}_{uuid.uuid4().hex[:8]}.{file_ext}"
            
            # Save file
            upload_folder = os.path.join(current_app.root_path, '..', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, new_filename)
            file.save(file_path)
            
            return jsonify({
                'success': True,
                'message': 'File uploaded successfully',
                'filename': new_filename,
                'original_name': original_filename,
                'size': os.path.getsize(file_path)
            })
        else:
            return jsonify({
                'success': False, 
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@uploads_bp.route('/<filename>', methods=['GET'])
def get_file(filename):
    """Get file information"""
    try:
        upload_folder = os.path.join(current_app.root_path, '..', 'uploads')
        file_path = os.path.join(upload_folder, secure_filename(filename))
        
        if os.path.exists(file_path):
            return jsonify({
                'success': True,
                'filename': filename,
                'size': os.path.getsize(file_path),
                'url': f'/api/uploads/file/{filename}'
            })
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@uploads_bp.route('/file/<filename>', methods=['GET'])
def download_file(filename):
    """Download a file"""
    from flask import send_file
    try:
        upload_folder = os.path.join(current_app.root_path, '..', 'uploads')
        file_path = os.path.join(upload_folder, secure_filename(filename))
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
