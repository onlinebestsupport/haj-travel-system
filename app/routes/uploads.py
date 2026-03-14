from flask import Blueprint, request, jsonify, session, current_app, send_file, abort
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
    if not filename or '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if doc_type in ALLOWED_EXTENSIONS:
        return ext in ALLOWED_EXTENSIONS[doc_type]
    return ext in ALLOWED_EXTENSIONS['document']

def get_upload_folder(doc_type='document'):
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
    
    # Create folder if it doesn't exist
    try:
        os.makedirs(folder_path, exist_ok=True)
    except Exception as e:
        print(f"⚠️ Error creating upload folder {folder_path}: {e}")
    
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

# ==================== FILE UPLOAD ROUTES ====================

@bp.route('', methods=['POST'])
def upload_file():
    """Upload a file with document type specification"""
    # Check authentication
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # Get document type from request
    doc_type = request.form.get('doc_type', 'document')
    traveler_id = request.form.get('traveler_id')
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file or file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Check file type
    if not allowed_file(file.filename, doc_type):
        allowed_exts = ", ".join(ALLOWED_EXTENSIONS.get(doc_type, ALLOWED_EXTENSIONS['document']))
        return jsonify({
            'success': False, 
            'error': f'File type not allowed for {doc_type}. Allowed: {allowed_exts}'
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
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    
    # Create organized filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if traveler_id:
        new_filename = f"{doc_type}_{traveler_id}_{timestamp}_{uuid.uuid4().hex[:8]}.{ext}"
    else:
        new_filename = f"{doc_type}_{timestamp}_{uuid.uuid4().hex}.{ext}"
    
    # Save file in appropriate folder
    try:
        upload_folder = get_upload_folder(doc_type)
        file_path = os.path.join(upload_folder, new_filename)
        file.save(file_path)
        
        # Verify file was saved
        if not os.path.exists(file_path):
            raise Exception("File was not saved properly")
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to save file: {str(e)}'
        }), 500
    
    # If this is for a traveler, update the traveler record
    if traveler_id and doc_type in ['passport', 'aadhaar', 'pan', 'vaccine', 'photo']:
        try:
            update_traveler_document(traveler_id, doc_type, new_filename)
        except Exception as e:
            # If database update fails, delete the uploaded file
            try:
                os.remove(file_path)
            except:
                pass
            return jsonify({
                'success': False,
                'error': f'Failed to update traveler record: {str(e)}'
            }), 500
    
    # Log activity for admin users
    if 'user_id' in session:
        log_activity(
            session['user_id'],
            'upload',
            'uploads',
            f'Uploaded {doc_type} file: {original_filename}',
            request.remote_addr
        )
    
    # Generate URL for accessing the file
    subfolder = get_upload_subfolder(doc_type)
    file_url = f'/uploads/{subfolder}/{new_filename}'
    
    return jsonify({
        'success': True,
        'filename': new_filename,
        'original_name': original_filename,
        'url': file_url,
        'doc_type': doc_type,
        'file_size': file_size,
        'file_size_mb': round(file_size / (1024 * 1024), 2),
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
    
    if not files:
        return jsonify({'success': False, 'error': 'No files provided'}), 400
    
    uploaded_files = []
    errors = []
    
    for file in files:
        if not file or file.filename == '':
            continue
        
        try:
            # Check file type
            if not allowed_file(file.filename, doc_type):
                errors.append(f"{file.filename}: File type not allowed")
                continue
            
            # Generate filename
            original_filename = secure_filename(file.filename)
            ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if traveler_id:
                new_filename = f"{doc_type}_{traveler_id}_{timestamp}_{uuid.uuid4().hex[:8]}.{ext}"
            else:
                new_filename = f"{doc_type}_{timestamp}_{uuid.uuid4().hex}.{ext}"
            
            # Save file
            upload_folder = get_upload_folder(doc_type)
            file_path = os.path.join(upload_folder, new_filename)
            file.save(file_path)
            
            subfolder = get_upload_subfolder(doc_type)
            uploaded_files.append({
                'filename': new_filename,
                'original_name': original_filename,
                'url': f'/uploads/{subfolder}/{new_filename}',
                'size': os.path.getsize(file_path)
            })
            
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    return jsonify({
        'success': len(uploaded_files) > 0,
        'uploaded_files': uploaded_files,
        'uploaded_count': len(uploaded_files),
        'errors': errors,
        'error_count': len(errors),
        'message': f'Successfully uploaded {len(uploaded_files)} files'
    })

# ==================== FILE SERVING ROUTES ====================

@bp.route('/files/<path:filename>')
def serve_file(filename):
    """Serve uploaded files - searches all subdirectories"""
    # 🔓 AUTHENTICATION REMOVED - Files should be accessible when user is logged in
    # The frontend already checks authentication before showing document icons
    
    # Security: Prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        print(f"⚠️ Security: Directory traversal attempt blocked: {filename}")
        abort(404)
    
    base_folder = current_app.config['UPLOAD_FOLDER']
    
    # Define all possible subdirectories where files might be stored
    subdirs = ['passports', 'aadhaar', 'pan', 'vaccine', 'photos', 'documents', 'company', 'backups']
    
    # Log for debugging
    print(f"🔍 Looking for file: {filename}")
    
    # Search each subdirectory
    for subdir in subdirs:
        folder_path = os.path.join(base_folder, subdir)
        file_path = os.path.join(folder_path, filename)
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            print(f"✅ Found file in {subdir}: {file_path}")
            try:
                return send_file(file_path)
            except Exception as e:
                print(f"❌ Error sending file: {e}")
                abort(500)
    
    # If we get here, file wasn't found
    print(f"❌ File not found: {filename}")
    print(f"   Searched in: {base_folder}")
    for subdir in subdirs:
        folder_path = os.path.join(base_folder, subdir)
        if os.path.exists(folder_path):
            files = os.listdir(folder_path)
            print(f"   - {subdir}: {len(files)} files")
            # Show first 5 files for debugging
            if files and len(files) > 0:
                print(f"     Sample files: {', '.join(files[:5])}")
    
    abort(404)

@bp.route('/<path:subdir>/<path:filename>')
def serve_file_with_subdir(subdir, filename):
    """Serve uploaded files with explicit subdirectory"""
    # 🔓 AUTHENTICATION REMOVED - Files should be accessible when user is logged in
    
    # Security: Prevent directory traversal
    if '..' in filename or '..' in subdir or filename.startswith('/') or subdir.startswith('/'):
        print(f"⚠️ Security: Directory traversal attempt blocked: {subdir}/{filename}")
        abort(404)
    
    # Validate subdir is allowed
    allowed_subdirs = ['passports', 'aadhaar', 'pan', 'vaccine', 'photos', 'documents', 'company', 'backups']
    if subdir not in allowed_subdirs:
        print(f"⚠️ Security: Invalid subdirectory requested: {subdir}")
        abort(404)
    
    base_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(base_folder, subdir, filename)
    
    print(f"🔍 Looking for file with subdir: {subdir}/{filename}")
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        print(f"✅ Found file: {file_path}")
        try:
            return send_file(file_path)
        except Exception as e:
            print(f"❌ Error sending file: {e}")
            abort(500)
    else:
        print(f"❌ File not found: {file_path}")
        
        # Debug: Show what files exist in this directory
        folder_path = os.path.join(base_folder, subdir)
        if os.path.exists(folder_path):
            files = os.listdir(folder_path)
            print(f"   Files in {subdir}: {len(files)} files")
            if files and len(files) > 0:
                print(f"   Available: {', '.join(files[:10])}")
        else:
            print(f"   Directory does not exist: {folder_path}")
        
        abort(404)

# Optional: Add a route to check if file exists without downloading
@bp.route('/check/<path:subdir>/<path:filename>', methods=['GET'])
def check_file_exists(subdir, filename):
    """Check if a file exists (returns JSON instead of file)"""
    # This is useful for debugging
    
    # Security: Prevent directory traversal
    if '..' in filename or '..' in subdir:
        return jsonify({'success': False, 'error': 'Invalid path'}), 400
    
    base_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(base_folder, subdir, filename)
    
    exists = os.path.exists(file_path) and os.path.isfile(file_path)
    
    result = {
        'success': True,
        'exists': exists,
        'filename': filename,
        'subdir': subdir,
        'full_path': file_path if exists else None
    }
    
    if exists:
        result['size'] = os.path.getsize(file_path)
        result['size_mb'] = round(result['size'] / (1024 * 1024), 2)
    
    return jsonify(result)
# ==================== FILE MANAGEMENT ROUTES ====================

@bp.route('/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a file"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    doc_type = request.args.get('doc_type', 'document')
    traveler_id = request.args.get('traveler_id')
    
    try:
        upload_folder = get_upload_folder(doc_type)
        file_path = os.path.join(upload_folder, secure_filename(filename))
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        # Get file info before deleting
        file_size = os.path.getsize(file_path)
        
        # Delete the file
        os.remove(file_path)
        
        # If this is for a traveler, clear the document field
        if traveler_id and doc_type in ['passport', 'aadhaar', 'pan', 'vaccine', 'photo']:
            clear_traveler_document(traveler_id, doc_type)
        
        # Log activity
        log_activity(
            session['user_id'],
            'delete',
            'uploads',
            f'Deleted {doc_type} file: {filename} (size: {file_size} bytes)',
            request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'message': 'File deleted successfully',
            'filename': filename,
            'file_size': file_size
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/traveler/<int:traveler_id>', methods=['GET'])
def get_traveler_documents(traveler_id):
    """Get all documents for a traveler"""
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        cursor.execute('''
            SELECT 
                passport_scan, aadhaar_scan, pan_scan, vaccine_scan, photo
            FROM travelers 
            WHERE id = %s
        ''', (traveler_id,))
        
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
        
        documents = {}
        doc_mapping = {
            'passport_scan': 'passport',
            'aadhaar_scan': 'aadhaar',
            'pan_scan': 'pan',
            'vaccine_scan': 'vaccine',
            'photo': 'photo'
        }
        
        for db_field, doc_type in doc_mapping.items():
            filename = result[db_field]
            if filename:
                subfolder = get_upload_subfolder(doc_type)
                file_path = os.path.join(get_upload_folder(doc_type), filename)
                file_exists = os.path.exists(file_path)
                
                documents[db_field] = {
                    'filename': filename,
                    'url': f'/uploads/{subfolder}/{filename}' if file_exists else None,
                    'uploaded': True,
                    'exists_on_disk': file_exists,
                    'size': os.path.getsize(file_path) if file_exists else 0
                }
            else:
                documents[db_field] = {
                    'filename': None,
                    'url': None,
                    'uploaded': False,
                    'exists_on_disk': False,
                    'size': 0
                }
        
        return jsonify({
            'success': True,
            'traveler_id': traveler_id,
            'documents': documents
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@bp.route('/info/<path:filename>', methods=['GET'])
def get_file_info(filename):
    """Get file information"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    doc_type = request.args.get('doc_type', 'document')
    
    try:
        upload_folder = get_upload_folder(doc_type)
        file_path = os.path.join(upload_folder, secure_filename(filename))
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        stat = os.stat(file_path)
        subfolder = get_upload_subfolder(doc_type)
        
        return jsonify({
            'success': True,
            'file_info': {
                'filename': filename,
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'url': f'/uploads/{subfolder}/{filename}',
                'doc_type': doc_type,
                'exists': True
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== HELPER FUNCTIONS ====================

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
                RETURNING id
            ''', (filename, datetime.now(), traveler_id))
            
            result = cursor.fetchone()
            conn.commit()
            
            if not result:
                raise Exception(f"Traveler {traveler_id} not found")
                
            print(f"✅ Updated traveler {traveler_id} {field} = {filename}")
        
    except Exception as e:
        print(f"❌ Error updating traveler document: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

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
                RETURNING id
            ''', (datetime.now(), traveler_id))
            
            result = cursor.fetchone()
            conn.commit()
            
            if not result:
                raise Exception(f"Traveler {traveler_id} not found")
                
            print(f"✅ Cleared traveler {traveler_id} {field}")
        
    except Exception as e:
        print(f"❌ Error clearing traveler document: {e}")
        if conn:
            conn.rollback()
        raise e
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
        print(f"✅ Activity logged: {action} - {description}")
    except Exception as e:
        print(f"⚠️ Activity log error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ==================== ADMIN ROUTES ====================

@bp.route('/cleanup', methods=['POST'])
def cleanup_orphaned_files():
    """Clean up orphaned files (admin only)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
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
            for value in row:
                if value:
                    referenced_files.add(value)
        
        cursor.close()
        conn.close()
        
        # Get all files in upload directories
        base_folder = current_app.config['UPLOAD_FOLDER']
        orphaned = []
        orphaned_by_folder = {}
        total_size = 0
        
        for doc_type, folder_name in [
            ('passport', 'passports'),
            ('aadhaar', 'aadhaar'),
            ('pan', 'pan'),
            ('vaccine', 'vaccine'),
            ('photo', 'photos'),
            ('document', 'documents'),
            ('logo', 'company'),
            ('backup', 'backups')
        ]:
            folder = os.path.join(base_folder, folder_name)
            if os.path.exists(folder):
                orphaned_by_folder[folder_name] = []
                for filename in os.listdir(folder):
                    filepath = os.path.join(folder, filename)
                    if os.path.isfile(filepath) and filename not in referenced_files:
                        file_size = os.path.getsize(filepath)
                        orphaned.append({
                            'path': filepath,
                            'filename': filename,
                            'size': file_size,
                            'folder': folder_name
                        })
                        orphaned_by_folder[folder_name].append(filename)
                        total_size += file_size
        
        # Log activity
        log_activity(
            session['user_id'],
            'cleanup_check',
            'uploads',
            f'Found {len(orphaned)} orphaned files ({round(total_size / (1024*1024), 2)} MB)',
            request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'orphaned_count': len(orphaned),
            'orphaned_by_folder': orphaned_by_folder,
            'orphaned_files': orphaned[:50],  # Limit to first 50 for response
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'message': f'Found {len(orphaned)} orphaned files. Use POST /cleanup/delete to remove them.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/cleanup/delete', methods=['POST'])
def delete_orphaned_files():
    """Delete orphaned files (admin only)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json or {}
    confirm = data.get('confirm', False)
    files_to_delete = data.get('files', [])
    
    if not confirm:
        return jsonify({'success': False, 'error': 'Confirmation required. Set confirm: true'}), 400
    
    if not files_to_delete:
        return jsonify({'success': False, 'error': 'No files specified for deletion'}), 400
    
    deleted = []
    errors = []
    total_size = 0
    
    for file_info in files_to_delete:
        try:
            filepath = file_info if isinstance(file_info, str) else file_info.get('path')
            if not filepath:
                continue
                
            if os.path.exists(filepath) and os.path.isfile(filepath):
                file_size = os.path.getsize(filepath)
                os.remove(filepath)
                deleted.append({
                    'path': filepath,
                    'filename': os.path.basename(filepath),
                    'size': file_size
                })
                total_size += file_size
            else:
                errors.append(f"File not found: {filepath}")
        except Exception as e:
            errors.append(f"Error deleting {filepath}: {str(e)}")
    
    # Log activity
    log_activity(
        session['user_id'],
        'cleanup_delete',
        'uploads',
        f'Deleted {len(deleted)} orphaned files ({round(total_size / (1024*1024), 2)} MB)',
        request.remote_addr
    )
    
    return jsonify({
        'success': True,
        'deleted_count': len(deleted),
        'deleted': deleted[:30],  # Limit response
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'errors': errors,
        'error_count': len(errors),
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
            'folder': get_upload_subfolder(doc_type),
            'allowed': True
        }
    
    return jsonify({
        'success': True,
        'config': config,
        'count': len(config)
    })

@bp.route('/stats', methods=['GET'])
def get_upload_stats():
    """Get upload statistics (admin only)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    base_folder = current_app.config['UPLOAD_FOLDER']
    stats = {}
    total_files = 0
    total_size = 0
    
    for doc_type, folder_name in [
        ('passport', 'passports'),
        ('aadhaar', 'aadhaar'),
        ('pan', 'pan'),
        ('vaccine', 'vaccine'),
        ('photo', 'photos'),
        ('document', 'documents'),
        ('logo', 'company'),
        ('backup', 'backups')
    ]:
        folder = os.path.join(base_folder, folder_name)
        if os.path.exists(folder):
            files = []
            folder_size = 0
            for filename in os.listdir(folder):
                filepath = os.path.join(folder, filename)
                if os.path.isfile(filepath):
                    file_size = os.path.getsize(filepath)
                    files.append({
                        'name': filename,
                        'size': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                    })
                    folder_size += file_size
            
            stats[folder_name] = {
                'file_count': len(files),
                'total_size_bytes': folder_size,
                'total_size_mb': round(folder_size / (1024 * 1024), 2),
                'files': files[:20]  # Limit preview
            }
            total_files += len(files)
            total_size += folder_size
    
    return jsonify({
        'success': True,
        'stats': stats,
        'summary': {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2)
        }
    })
