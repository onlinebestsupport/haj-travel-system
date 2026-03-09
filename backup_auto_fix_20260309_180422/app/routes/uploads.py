from flask import Blueprint, request, jsonify, session, current_app
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from app.database import get_db

bp = Blueprint('uploads', __name__, url_prefix='/api/uploads')

# Allowed file extensions for different document types
ALLOWED_EXTENSIONS = {
    'passport': {'png', 'jpg', 'jpeg', 'pdf'},
    'aadhaar': {'png', 'jpg', 'jpeg', 'pdf'},
    'pan': {'png', 'jpg', 'jpeg', 'pdf'},
    'vaccine': {'png', 'jpg', 'jpeg', 'pdf'},
    'photo': {'png', 'jpg', 'jpeg'},
    'document': {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'},
    'logo': {'png', 'jpg', 'jpeg', 'svg', 'gif'}
}

# Max file sizes (in MB)
MAX_FILE_SIZES = {
    'passport': 5,
    'aadhaar': 5,
    'pan': 5,
    'vaccine': 5,
    'photo': 2,
    'document': 10,
    'logo': 2
}

def allowed_file(filename, doc_type='document'):
    """Check if file type is allowed for specific document type"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if doc_type in ALLOWED_EXTENSIONS:
        return ext in ALLOWED_EXTENSIONS[doc_type]
    return ext in ALLOWED_EXTENSIONS['document']

def get_upload_folder(doc_type='documents'):
    """Get upload folder for specific document type"""
    base_folder = current_app.config['UPLOAD_FOLDER']
    
    folders = {
        'passport': 'passports',
        'aadhaar': 'aadhaar',
        'pan': 'pan',
        'vaccine': 'vaccine',
        'photo': 'photos',
        'logo': 'company',
        'backup': 'backups',
        'document': 'documents'
    }
    
    subfolder = folders.get(doc_type, 'documents')
    folder_path = os.path.join(base_folder, subfolder)
    os.makedirs(folder_path, exist_ok=True)
    
    return folder_path

def get_upload_subfolder(doc_type):
    """Get upload subfolder name for URL generation"""
    folders = {
        'passport': 'passports',
        'aadhaar': 'aadhaar',
        'pan': 'pan',
        'vaccine': 'vaccine',
        'photo': 'photos',
        'logo': 'company',
        'backup': 'backups',
        'document': 'documents'
    }
    return folders.get(doc_type, 'documents')

@bp.route('', methods=['POST'])
def upload_file():
    """Upload a file with document type specification"""
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # Get document type from request
    doc_type = request.form.get('doc_type', 'document')
    traveler_id = request.form.get('traveler_id')
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Check file type
    if not allowed_file(file.filename, doc_type):
        return jsonify({
            'success': False, 
            'error': f'File type not allowed for {doc_type}. Allowed: {", ".join(ALLOWED_EXTENSIONS.get(doc_type, ALLOWED_EXTENSIONS["document"]))}'
        }), 400
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    max_size = MAX_FILE_SIZES.get(doc_type, 5) * 1024 * 1024  # Convert MB to bytes
    if file_size > max_size:
        max_size_mb = MAX_FILE_SIZES.get(doc_type, 5)
        return jsonify({
            'success': False,
            'error': f'File too large. Maximum size for {doc_type} is {max_size_mb}MB'
        }), 400
    
    # Generate unique filename
    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[1].lower()
    
    # Create organized filename
    if traveler_id:
        new_filename = f"{doc_type}_{traveler_id}_{uuid.uuid4().hex[:8]}.{ext}"
    else:
        new_filename = f"{doc_type}_{uuid.uuid4().hex}.{ext}"
    
    # Save file in appropriate folder
    upload_folder = get_upload_folder(doc_type)
    file_path = os.path.join(upload_folder, new_filename)
    file.save(file_path)
    
    # If this is for a traveler, update the traveler record
    if traveler_id and doc_type in ['passport', 'aadhaar', 'pan', 'vaccine', 'photo']:
        update_traveler_document(traveler_id, doc_type, new_filename)
    
    # Log activity for admin users
    if 'user_id' in session:
        log_activity(
            session['user_id'],
            'upload',
            'uploads',
            f'Uploaded {doc_type} file: {original_filename}',
            request.remote_addr
        )
    
    return jsonify({
        'success': True,
        'filename': new_filename,
        'original_name': original_filename,
        'url': f'/uploads/{get_upload_subfolder(doc_type)}/{new_filename}',
        'doc_type': doc_type,
        'file_size': file_size,
        'message': f'{doc_type.capitalize()} uploaded successfully'
    })

@bp.route('/multiple', methods=['POST'])
def upload_multiple_files():
    """Upload multiple files at once"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    if 'files' not in request.files:
        return jsonify({'success': False, 'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    doc_type = request.form.get('doc_type', 'document')
    traveler_id = request.form.get('traveler_id')
    
    uploaded_files = []
    errors = []
    
    for file in files:
        if file.filename == '':
            continue
        
        try:
            # Check file type
            if not allowed_file(file.filename, doc_type):
                errors.append(f"{file.filename}: File type not allowed")
                continue
            
            # Generate filename
            original_filename = secure_filename(file.filename)
            ext = original_filename.rsplit('.', 1)[1].lower()
            
            if traveler_id:
                new_filename = f"{doc_type}_{traveler_id}_{uuid.uuid4().hex[:8]}.{ext}"
            else:
                new_filename = f"{doc_type}_{uuid.uuid4().hex}.{ext}"
            
            # Save file
            upload_folder = get_upload_folder(doc_type)
            file_path = os.path.join(upload_folder, new_filename)
            file.save(file_path)
            
            uploaded_files.append({
                'filename': new_filename,
                'original_name': original_filename,
                'url': f'/uploads/{get_upload_subfolder(doc_type)}/{new_filename}'
            })
            
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    return jsonify({
        'success': len(uploaded_files) > 0,
        'uploaded_files': uploaded_files,
        'errors': errors,
        'message': f'Successfully uploaded {len(uploaded_files)} files'
    })

@bp.route('/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a file"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    doc_type = request.args.get('doc_type', 'document')
    traveler_id = request.args.get('traveler_id')
    
    try:
        upload_folder = get_upload_folder(doc_type)
        file_path = os.path.join(upload_folder, filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
            # If this is for a traveler, clear the document field
            if traveler_id and doc_type in ['passport', 'aadhaar', 'pan', 'vaccine', 'photo']:
                clear_traveler_document(traveler_id, doc_type)
            
            # Log activity
            log_activity(
                session['user_id'],
                'delete',
                'uploads',
                f'Deleted {doc_type} file: {filename}',
                request.remote_addr
            )
            
            return jsonify({'success': True, 'message': 'File deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/traveler/<int:traveler_id>', methods=['GET'])
def get_traveler_documents(traveler_id):
    """Get all documents for a traveler"""
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    cursor.execute('''
        SELECT 
            passport_scan, aadhaar_scan, pan_scan, vaccine_scan, photo
        FROM travelers 
        WHERE id = %s
    ''', (traveler_id,))
    
    traveler = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not traveler:
        return jsonify({'success': False, 'error': 'Traveler not found'}), 404
    
    documents = {}
    for doc_type in ['passport_scan', 'aadhaar_scan', 'pan_scan', 'vaccine_scan', 'photo']:
        filename = traveler[doc_type]
        if filename:
            clean_type = doc_type.replace('_scan', '').replace('_', '')
            documents[doc_type] = {
                'filename': filename,
                'url': f'/uploads/{get_upload_subfolder(clean_type)}/{filename}',
                'uploaded': True,
                'exists': os.path.exists(os.path.join(get_upload_folder(clean_type), filename))
            }
        else:
            documents[doc_type] = {
                'filename': None,
                'url': None,
                'uploaded': False
            }
    
    return jsonify({
        'success': True,
        'documents': documents
    })

@bp.route('/info/<path:filename>', methods=['GET'])
def get_file_info(filename):
    """Get file information"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    doc_type = request.args.get('doc_type', 'document')
    
    try:
        upload_folder = get_upload_folder(doc_type)
        file_path = os.path.join(upload_folder, filename)
        
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            return jsonify({
                'success': True,
                'file_info': {
                    'filename': filename,
                    'size': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'url': f'/uploads/{get_upload_subfolder(doc_type)}/{filename}'
                }
            })
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Helper function to update traveler document
def update_traveler_document(traveler_id, doc_type, filename):
    """Update traveler record with document filename"""
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        field_map = {
            'passport': 'passport_scan',
            'aadhaar': 'aadhaar_scan',
            'pan': 'pan_scan',
            'vaccine': 'vaccine_scan',
            'photo': 'photo'
        }
        
        field = field_map.get(doc_type)
        if field:
            cursor.execute(f'''
                UPDATE travelers 
                SET {field} = %s, updated_at = %s
                WHERE id = %s
            ''', (filename, datetime.now(), traveler_id))
            conn.commit()
        
    except Exception as e:
        print(f"❌ Error updating traveler document: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Helper function to clear traveler document
def clear_traveler_document(traveler_id, doc_type):
    """Clear traveler document field"""
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        field_map = {
            'passport': 'passport_scan',
            'aadhaar': 'aadhaar_scan',
            'pan': 'pan_scan',
            'vaccine': 'vaccine_scan',
            'photo': 'photo'
        }
        
        field = field_map.get(doc_type)
        if field:
            cursor.execute(f'''
                UPDATE travelers 
                SET {field} = NULL, updated_at = %s
                WHERE id = %s
            ''', (datetime.now(), traveler_id))
            conn.commit()
        
    except Exception as e:
        print(f"❌ Error clearing traveler document: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def log_activity(user_id, action, module, description, ip_address=None):
    """Log user activity"""
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute(
            'INSERT INTO activity_log (user_id, action, module, description, ip_address, created_at) VALUES (%s, %s, %s, %s, %s, %s)',
            (user_id, action, module, description, ip_address, datetime.now())
        )
        conn.commit()
    except Exception as e:
        print(f"⚠️ Activity log error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@bp.route('/cleanup', methods=['POST'])
def cleanup_orphaned_files():
    """Clean up orphaned files (admin only)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    # Get all referenced files from database
    cursor.execute('''
        SELECT passport_scan FROM travelers WHERE passport_scan IS NOT NULL
        UNION ALL
        SELECT aadhaar_scan FROM travelers WHERE aadhaar_scan IS NOT NULL
        UNION ALL
        SELECT pan_scan FROM travelers WHERE pan_scan IS NOT NULL
        UNION ALL
        SELECT vaccine_scan FROM travelers WHERE vaccine_scan IS NOT NULL
        UNION ALL
        SELECT photo FROM travelers WHERE photo IS NOT NULL
    ''')
    
    rows = cursor.fetchall()
    referenced_files = set()
    for row in rows:
        for key, value in row.items():
            if value:
                referenced_files.add(value)
    
    cursor.close()
    conn.close()
    
    # Get all files in upload directories
    base_folder = current_app.config['UPLOAD_FOLDER']
    orphaned = []
    orphaned_by_folder = {}
    
    for doc_type, folder_name in [
        ('passports', 'passport'),
        ('aadhaar', 'aadhaar'),
        ('pan', 'pan'),
        ('vaccine', 'vaccine'),
        ('photos', 'photo'),
        ('documents', 'document'),
        ('company', 'logo'),
        ('backups', 'backup')
    ]:
        folder = os.path.join(base_folder, folder_name)
        if os.path.exists(folder):
            orphaned_by_folder[folder_name] = []
            for filename in os.listdir(folder):
                filepath = os.path.join(folder, filename)
                if os.path.isfile(filepath) and filename not in referenced_files:
                    orphaned.append(filepath)
                    orphaned_by_folder[folder_name].append(filename)
    
    return jsonify({
        'success': True,
        'orphaned_count': len(orphaned),
        'orphaned_by_folder': orphaned_by_folder,
        'orphaned_files': orphaned[:100],  # Limit to first 100 for response
        'message': f'Found {len(orphaned)} orphaned files. Use POST /cleanup/delete to remove them.'
    })

@bp.route('/cleanup/delete', methods=['POST'])
def delete_orphaned_files():
    """Delete orphaned files (admin only)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    confirm = data.get('confirm', False)
    files_to_delete = data.get('files', [])
    
    if not confirm:
        return jsonify({'success': False, 'error': 'Confirmation required'}), 400
    
    deleted = []
    errors = []
    
    for filepath in files_to_delete:
        try:
            if os.path.exists(filepath) and os.path.isfile(filepath):
                os.remove(filepath)
                deleted.append(filepath)
            else:
                errors.append(f"File not found: {filepath}")
        except Exception as e:
            errors.append(f"Error deleting {filepath}: {str(e)}")
    
    # Log activity
    log_activity(
        session['user_id'],
        'cleanup',
        'uploads',
        f'Deleted {len(deleted)} orphaned files',
        request.remote_addr
    )
    
    return jsonify({
        'success': True,
        'deleted_count': len(deleted),
        'deleted': deleted[:50],  # Limit response
        'errors': errors,
        'message': f'Successfully deleted {len(deleted)} files'
    })

@bp.route('/types', methods=['GET'])
def get_upload_types():
    """Get allowed upload types and their configurations"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    config = {}
    for doc_type in ALLOWED_EXTENSIONS:
        config[doc_type] = {
            'extensions': list(ALLOWED_EXTENSIONS[doc_type]),
            'max_size_mb': MAX_FILE_SIZES.get(doc_type, 5),
            'folder': get_upload_subfolder(doc_type)
        }
    
    return jsonify({
        'success': True,
        'config': config
    })
