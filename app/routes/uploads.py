from flask import Blueprint, request, jsonify, current_app, send_file
import os
import uuid
from werkzeug.utils import secure_filename
import datetime

uploads_bp = Blueprint('uploads', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_folder():
    """Get the upload folder path"""
    upload_folder = os.path.join(current_app.root_path, '..', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder

@uploads_bp.route('/', methods=['GET'])
def upload_status():
    """Check upload API status"""
    return jsonify({
        'success': True,
        'message': 'Upload API is working',
        'allowed_extensions': list(ALLOWED_EXTENSIONS),
        'max_file_size': f"{MAX_FILE_SIZE / (1024*1024)}MB",
        'endpoints': {
            'upload_file': '/api/uploads/upload (POST)',
            'get_file_info': '/api/uploads/<filename> (GET)',
            'download_file': '/api/uploads/file/<filename> (GET)',
            'delete_file': '/api/uploads/<filename> (DELETE)',
            'traveler_files': '/api/uploads/traveler/<traveler_id> (GET)'
        }
    })

@uploads_bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload a file for a traveler"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Get metadata from form
        traveler_id = request.form.get('traveler_id', 'unknown')
        document_type = request.form.get('document_type', 'other')
        
        # Validate document type
        valid_document_types = ['passport', 'aadhaar', 'pan', 'vaccine', 'other']
        if document_type not in valid_document_types:
            document_type = 'other'
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False, 
                'error': f'File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024)}MB'
            }), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        
        new_filename = f"{traveler_id}_{document_type}_{timestamp}_{unique_id}.{file_ext}"
        
        # Save file
        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, new_filename)
        file.save(file_path)
        
        # Get file size after save
        saved_size = os.path.getsize(file_path)
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'filename': new_filename,
            'original_name': original_filename,
            'size': saved_size,
            'size_mb': round(saved_size / (1024 * 1024), 2),
            'document_type': document_type,
            'traveler_id': traveler_id,
            'uploaded_at': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@uploads_bp.route('/<filename>', methods=['GET'])
def get_file_info(filename):
    """Get file information without downloading"""
    try:
        # Sanitize filename to prevent path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400
        
        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, secure_filename(filename))
        
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            file_modified = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # Parse filename to extract metadata
            parts = filename.split('_')
            traveler_id = parts[0] if len(parts) > 0 else 'unknown'
            document_type = parts[1] if len(parts) > 1 else 'other'
            
            return jsonify({
                'success': True,
                'filename': filename,
                'size': file_size,
                'size_mb': round(file_size / (1024 * 1024), 2),
                'modified': file_modified.isoformat(),
                'document_type': document_type,
                'traveler_id': traveler_id,
                'url': f'/api/uploads/file/{filename}'
            })
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@uploads_bp.route('/file/<filename>', methods=['GET'])
def download_file(filename):
    """Download a file"""
    try:
        # Sanitize filename to prevent path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400
        
        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, secure_filename(filename))
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@uploads_bp.route('/view/<filename>', methods=['GET'])
def view_file(filename):
    """View a file in browser (for images/PDFs)"""
    try:
        # Sanitize filename to prevent path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400
        
        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, secure_filename(filename))
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=False)
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@uploads_bp.route('/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a file"""
    try:
        # Sanitize filename to prevent path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400
        
        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, secure_filename(filename))
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True, 'message': 'File deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@uploads_bp.route('/traveler/<traveler_id>', methods=['GET'])
def get_traveler_files(traveler_id):
    """Get all files for a specific traveler"""
    try:
        upload_folder = get_upload_folder()
        files = []
        
        # List all files in upload folder
        for filename in os.listdir(upload_folder):
            # Check if filename starts with traveler_id
            if filename.startswith(f"{traveler_id}_"):
                file_path = os.path.join(upload_folder, filename)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    file_modified = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    # Parse document type from filename
                    parts = filename.split('_')
                    document_type = parts[1] if len(parts) > 1 else 'other'
                    
                    files.append({
                        'filename': filename,
                        'size': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'document_type': document_type,
                        'modified': file_modified.isoformat(),
                        'url': f'/api/uploads/file/{filename}',
                        'view_url': f'/api/uploads/view/{filename}'
                    })
        
        # Sort by modified date (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'traveler_id': traveler_id,
            'files': files,
            'count': len(files)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@uploads_bp.route('/document-types', methods=['GET'])
def get_document_types():
    """Get list of valid document types"""
    return jsonify({
        'success': True,
        'document_types': [
            {'id': 'passport', 'name': 'Passport', 'icon': 'fa-passport'},
            {'id': 'aadhaar', 'name': 'Aadhaar Card', 'icon': 'fa-id-card'},
            {'id': 'pan', 'name': 'PAN Card', 'icon': 'fa-file-invoice'},
            {'id': 'vaccine', 'name': 'Vaccine Certificate', 'icon': 'fa-syringe'},
            {'id': 'photo', 'name': 'Photograph', 'icon': 'fa-camera'},
            {'id': 'other', 'name': 'Other Document', 'icon': 'fa-file'}
        ]
    })

@uploads_bp.route('/cleanup', methods=['POST'])
def cleanup_orphaned_files():
    """Delete files not referenced in database (admin only)"""
    # This endpoint should be protected by admin authentication
    # For now, returning not implemented
    return jsonify({'success': False, 'error': 'Not implemented'}), 501

@uploads_bp.route('/stats', methods=['GET'])
def get_upload_stats():
    """Get upload statistics"""
    try:
        upload_folder = get_upload_folder()
        total_files = 0
        total_size = 0
        files_by_type = {}
        files_by_date = {}
        
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            if os.path.isfile(file_path):
                total_files += 1
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                # Count by document type
                parts = filename.split('_')
                doc_type = parts[1] if len(parts) > 1 else 'other'
                files_by_type[doc_type] = files_by_type.get(doc_type, 0) + 1
                
                # Count by date
                modified = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                date_str = modified.strftime('%Y-%m-%d')
                files_by_date[date_str] = files_by_date.get(date_str, 0) + 1
        
        return jsonify({
            'success': True,
            'stats': {
                'total_files': total_files,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'files_by_type': files_by_type,
                'files_by_date': files_by_date
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Error handler for file too large
@uploads_bp.errorhandler(413)
def file_too_large(e):
    return jsonify({'success': False, 'error': 'File too large'}), 413
