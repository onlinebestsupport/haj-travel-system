from flask import Blueprint, request, jsonify, current_app, send_file, session
import os
import uuid
from werkzeug.utils import secure_filename
import datetime
from functools import wraps
import mimetypes

uploads_bp = Blueprint('uploads', __name__)

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Document type mapping
DOCUMENT_TYPES = {
    'passport': {'name': 'Passport', 'icon': 'fa-passport', 'allowed': ALLOWED_EXTENSIONS},
    'aadhaar': {'name': 'Aadhaar Card', 'icon': 'fa-id-card', 'allowed': {'pdf', 'jpg', 'png'}},
    'pan': {'name': 'PAN Card', 'icon': 'fa-file-invoice', 'allowed': {'pdf', 'jpg', 'png'}},
    'vaccine': {'name': 'Vaccine Certificate', 'icon': 'fa-syringe', 'allowed': {'pdf', 'jpg', 'png'}},
    'photo': {'name': 'Photograph', 'icon': 'fa-camera', 'allowed': {'jpg', 'jpeg', 'png'}},
    'other': {'name': 'Other Document', 'icon': 'fa-file', 'allowed': ALLOWED_EXTENSIONS}
}

# ============ HELPER FUNCTIONS ============

def login_required(f):
    """Decorator to check if admin is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def traveler_login_required(f):
    """Decorator to check if traveler is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('traveler_id'):
            return jsonify({'success': False, 'error': 'Traveler authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename, doc_type='other'):
    """Check if file has allowed extension for document type"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    # Get allowed extensions for document type
    doc_config = DOCUMENT_TYPES.get(doc_type, DOCUMENT_TYPES['other'])
    allowed = doc_config['allowed']
    
    return ext in allowed

def get_upload_folder():
    """Get the upload folder path"""
    upload_folder = os.path.join(current_app.root_path, '..', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder

def get_file_metadata(filename):
    """Extract metadata from filename"""
    parts = filename.split('_')
    metadata = {
        'traveler_id': parts[0] if len(parts) > 0 else 'unknown',
        'document_type': parts[1] if len(parts) > 1 else 'other',
        'timestamp': parts[2] if len(parts) > 2 else 'unknown',
        'unique_id': parts[3].split('.')[0] if len(parts) > 3 else 'unknown'
    }
    return metadata

def update_traveler_document_record(traveler_id, doc_type, filename):
    """Update the traveler's document field in database"""
    try:
        from app.database import get_db
        
        conn = get_db()
        cur = conn.cursor()
        
        # Map document type to database field
        field_map = {
            'passport': 'passport_scan',
            'aadhaar': 'aadhaar_scan',
            'pan': 'pan_scan',
            'vaccine': 'vaccine_scan'
        }
        
        if doc_type in field_map:
            field = field_map[doc_type]
            cur.execute(f"""
                UPDATE travelers 
                SET {field} = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (filename, traveler_id))
            conn.commit()
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating traveler document: {e}")
        return False

def get_traveler_document_status(traveler_id):
    """Get document upload status for a traveler"""
    try:
        from app.database import get_db
        
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                passport_scan, aadhaar_scan, pan_scan, vaccine_scan
            FROM travelers 
            WHERE id = %s
        """, (traveler_id,))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            return {
                'passport': result[0] is not None,
                'aadhaar': result[1] is not None,
                'pan': result[2] is not None,
                'vaccine': result[3] is not None
            }
        return None
    except Exception as e:
        print(f"Error getting document status: {e}")
        return None

# ============ PUBLIC ROUTES ============

@uploads_bp.route('/', methods=['GET'])
def upload_status():
    """Check upload API status - Public"""
    return jsonify({
        'success': True,
        'message': 'Upload API is working',
        'allowed_extensions': list(ALLOWED_EXTENSIONS),
        'max_file_size': f"{MAX_FILE_SIZE / (1024*1024)}MB",
        'document_types': [
            {'id': k, 'name': v['name'], 'icon': v['icon']} 
            for k, v in DOCUMENT_TYPES.items()
        ],
        'endpoints': {
            'upload_file': '/api/uploads/upload (POST) - Login required',
            'upload_traveler': '/api/uploads/traveler/upload (POST) - Traveler login',
            'get_file_info': '/api/uploads/<filename> (GET)',
            'download_file': '/api/uploads/file/<filename> (GET)',
            'view_file': '/api/uploads/view/<filename> (GET)',
            'delete_file': '/api/uploads/<filename> (DELETE) - Admin only',
            'traveler_files': '/api/uploads/traveler/<traveler_id> (GET) - Login required',
            'document_types': '/api/uploads/document-types (GET)',
            'stats': '/api/uploads/stats (GET) - Admin only'
        }
    })

@uploads_bp.route('/document-types', methods=['GET'])
def get_document_types():
    """Get list of valid document types - Public"""
    return jsonify({
        'success': True,
        'document_types': [
            {
                'id': k, 
                'name': v['name'], 
                'icon': v['icon'],
                'allowed_extensions': list(v['allowed'])
            } 
            for k, v in DOCUMENT_TYPES.items()
        ]
    })

@uploads_bp.route('/file/<filename>', methods=['GET'])
def download_file(filename):
    """Download a file - Public (files are accessible via URL)"""
    try:
        # Sanitize filename to prevent path traversal
        safe_filename = secure_filename(filename)
        if '..' in filename or filename != safe_filename:
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400
        
        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, safe_filename)
        
        if os.path.exists(file_path):
            # Determine mimetype
            mimetype, _ = mimetypes.guess_type(file_path)
            return send_file(
                file_path, 
                as_attachment=True, 
                download_name=filename,
                mimetype=mimetype
            )
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@uploads_bp.route('/view/<filename>', methods=['GET'])
def view_file(filename):
    """View a file in browser (for images/PDFs) - Public"""
    try:
        # Sanitize filename to prevent path traversal
        safe_filename = secure_filename(filename)
        if '..' in filename or filename != safe_filename:
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400
        
        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, safe_filename)
        
        if os.path.exists(file_path):
            # Determine mimetype
            mimetype, _ = mimetypes.guess_type(file_path)
            return send_file(
                file_path, 
                as_attachment=False,
                mimetype=mimetype
            )
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@uploads_bp.route('/<filename>', methods=['GET'])
def get_file_info(filename):
    """Get file information without downloading - Public"""
    try:
        # Sanitize filename to prevent path traversal
        safe_filename = secure_filename(filename)
        if '..' in filename or filename != safe_filename:
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400
        
        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, safe_filename)
        
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            file_modified = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # Parse filename to extract metadata
            metadata = get_file_metadata(safe_filename)
            
            return jsonify({
                'success': True,
                'filename': safe_filename,
                'size': file_size,
                'size_mb': round(file_size / (1024 * 1024), 2),
                'modified': file_modified.isoformat(),
                'document_type': metadata['document_type'],
                'traveler_id': metadata['traveler_id'],
                'url': f'/api/uploads/file/{safe_filename}',
                'view_url': f'/api/uploads/view/{safe_filename}'
            })
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ TRAVELER ROUTES (Require Traveler Login) ============

@uploads_bp.route('/traveler/upload', methods=['POST'])
@traveler_login_required
def traveler_upload():
    """Upload a file for the logged-in traveler"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Get metadata from form
        traveler_id = session.get('traveler_id')
        document_type = request.form.get('document_type', 'other')
        
        # Validate document type
        if document_type not in DOCUMENT_TYPES:
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
        
        # Check file extension for document type
        if not allowed_file(file.filename, document_type):
            doc_config = DOCUMENT_TYPES.get(document_type, DOCUMENT_TYPES['other'])
            return jsonify({
                'success': False, 
                'error': f'File type not allowed for {doc_config["name"]}. Allowed: {", ".join(doc_config["allowed"])}'
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
        
        # Update traveler's document record in database
        update_traveler_document_record(traveler_id, document_type, new_filename)
        
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
            'document_name': DOCUMENT_TYPES[document_type]['name'],
            'traveler_id': traveler_id,
            'uploaded_at': datetime.datetime.now().isoformat(),
            'view_url': f'/api/uploads/view/{new_filename}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@uploads_bp.route('/traveler/my-files', methods=['GET'])
@traveler_login_required
def get_my_files():
    """Get all files for the logged-in traveler"""
    try:
        traveler_id = session.get('traveler_id')
        upload_folder = get_upload_folder()
        files = []
        
        # Get document status from database
        doc_status = get_traveler_document_status(traveler_id)
        
        # List all files in upload folder that belong to this traveler
        for filename in os.listdir(upload_folder):
            if filename.startswith(f"{traveler_id}_"):
                file_path = os.path.join(upload_folder, filename)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    file_modified = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    # Parse document type from filename
                    metadata = get_file_metadata(filename)
                    document_type = metadata['document_type']
                    
                    files.append({
                        'filename': filename,
                        'size': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'document_type': document_type,
                        'document_name': DOCUMENT_TYPES.get(document_type, {}).get('name', 'Other'),
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
            'count': len(files),
            'document_status': doc_status
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ ADMIN ROUTES (Require Admin Login) ============

@uploads_bp.route('/upload', methods=['POST'])
@login_required
def admin_upload_file():
    """Upload a file for any traveler - Admin only"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Get metadata from form
        traveler_id = request.form.get('traveler_id')
        if not traveler_id:
            return jsonify({'success': False, 'error': 'traveler_id is required'}), 400
            
        document_type = request.form.get('document_type', 'other')
        
        # Validate document type
        if document_type not in DOCUMENT_TYPES:
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
        
        # Check file extension for document type
        if not allowed_file(file.filename, document_type):
            doc_config = DOCUMENT_TYPES.get(document_type, DOCUMENT_TYPES['other'])
            return jsonify({
                'success': False, 
                'error': f'File type not allowed for {doc_config["name"]}. Allowed: {", ".join(doc_config["allowed"])}'
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
        
        # Update traveler's document record in database
        update_traveler_document_record(traveler_id, document_type, new_filename)
        
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
            'document_name': DOCUMENT_TYPES[document_type]['name'],
            'traveler_id': traveler_id,
            'uploaded_at': datetime.datetime.now().isoformat(),
            'uploaded_by': session.get('admin_username')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@uploads_bp.route('/traveler/<traveler_id>', methods=['GET'])
@login_required
def get_traveler_files(traveler_id):
    """Get all files for a specific traveler - Admin only"""
    try:
        upload_folder = get_upload_folder()
        files = []
        
        # Get document status from database
        doc_status = get_traveler_document_status(traveler_id)
        
        # List all files in upload folder that belong to this traveler
        for filename in os.listdir(upload_folder):
            if filename.startswith(f"{traveler_id}_"):
                file_path = os.path.join(upload_folder, filename)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    file_modified = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    # Parse document type from filename
                    metadata = get_file_metadata(filename)
                    document_type = metadata['document_type']
                    
                    files.append({
                        'filename': filename,
                        'size': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'document_type': document_type,
                        'document_name': DOCUMENT_TYPES.get(document_type, {}).get('name', 'Other'),
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
            'count': len(files),
            'document_status': doc_status
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@uploads_bp.route('/<filename>', methods=['DELETE'])
@login_required
def delete_file(filename):
    """Delete a file - Admin only"""
    try:
        # Sanitize filename to prevent path traversal
        safe_filename = secure_filename(filename)
        if '..' in filename or filename != safe_filename:
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400
        
        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, safe_filename)
        
        if os.path.exists(file_path):
            # Get metadata before deleting
            metadata = get_file_metadata(safe_filename)
            traveler_id = metadata['traveler_id']
            document_type = metadata['document_type']
            
            # Delete file
            os.remove(file_path)
            
            # Clear the document field in database if it's a primary document
            if document_type in ['passport', 'aadhaar', 'pan', 'vaccine']:
                from app.database import get_db
                conn = get_db()
                cur = conn.cursor()
                
                field_map = {
                    'passport': 'passport_scan',
                    'aadhaar': 'aadhaar_scan',
                    'pan': 'pan_scan',
                    'vaccine': 'vaccine_scan'
                }
                
                if document_type in field_map:
                    field = field_map[document_type]
                    cur.execute(f"""
                        UPDATE travelers 
                        SET {field} = NULL, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND {field} = %s
                    """, (traveler_id, safe_filename))
                    conn.commit()
                
                cur.close()
                conn.close()
            
            return jsonify({
                'success': True, 
                'message': 'File deleted successfully',
                'deleted_by': session.get('admin_username')
            })
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@uploads_bp.route('/cleanup', methods=['POST'])
@login_required
def cleanup_orphaned_files():
    """Delete files not referenced in database - Admin only"""
    try:
        from app.database import get_db
        
        upload_folder = get_upload_folder()
        orphaned_files = []
        deleted_count = 0
        
        # Get all valid filenames from database
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT passport_scan, aadhaar_scan, pan_scan, vaccine_scan 
            FROM travelers 
            WHERE passport_scan IS NOT NULL 
               OR aadhaar_scan IS NOT NULL 
               OR pan_scan IS NOT NULL 
               OR vaccine_scan IS NOT NULL
        """)
        
        db_files = set()
        for row in cur.fetchall():
            for filename in row:
                if filename:
                    db_files.add(filename)
        
        cur.close()
        conn.close()
        
        # Check all files in upload folder
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            if os.path.isfile(file_path) and filename not in db_files:
                orphaned_files.append(filename)
                os.remove(file_path)
                deleted_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Deleted {deleted_count} orphaned files',
            'orphaned_files': orphaned_files,
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@uploads_bp.route('/stats', methods=['GET'])
@login_required
def get_upload_stats():
    """Get upload statistics - Admin only"""
    try:
        upload_folder = get_upload_folder()
        total_files = 0
        total_size = 0
        files_by_type = {}
        files_by_date = {}
        files_by_traveler = {}
        
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            if os.path.isfile(file_path):
                total_files += 1
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                # Count by document type
                metadata = get_file_metadata(filename)
                doc_type = metadata['document_type']
                traveler_id = metadata['traveler_id']
                
                files_by_type[doc_type] = files_by_type.get(doc_type, 0) + 1
                files_by_traveler[traveler_id] = files_by_traveler.get(traveler_id, 0) + 1
                
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
                'files_by_date': files_by_date,
                'files_by_traveler_count': len(files_by_traveler)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ ERROR HANDLERS ============

@uploads_bp.errorhandler(413)
def file_too_large(e):
    return jsonify({
        'success': False, 
        'error': f'File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024)}MB'
    }), 413
