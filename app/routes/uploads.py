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
            f'Uploaded {doc_type} file: {original_filename}'
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
            file.save(os.path.join(upload_folder, new_filename))
            
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
                f'Deleted {doc_type} file: {filename}'
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
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            passport_scan, aadhaar_scan, pan_scan, vaccine_scan, photo
        FROM travelers 
        WHERE id = ?
    ''', (traveler_id,))
    
    traveler = cursor.fetchone()
    db.close()
    
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
                'uploaded': True
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

# Helper function to update traveler document
def update_traveler_document(traveler_id, doc_type, filename):
    """Update traveler record with document filename"""
    try:
        db = get_db()
        cursor = db.cursor()
        
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
                SET {field} = ?, updated_at = ?
                WHERE id = ?
            ''', (filename, datetime.now().isoformat(), traveler_id))
            db.commit()
        
        db.close()
    except Exception as e:
        print(f"Error updating traveler document: {e}")

# Helper function to clear traveler document
def clear_traveler_document(traveler_id, doc_type):
    """Clear traveler document field"""
    try:
        db = get_db()
        cursor = db.cursor()
        
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
                SET {field} = NULL, updated_at = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), traveler_id))
            db.commit()
        
        db.close()
    except Exception as e:
        print(f"Error clearing traveler document: {e}")

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

def log_activity(user_id, action, module, description):
    """Log user activity"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO activity_log (user_id, action, module, description, ip_address) VALUES (?, ?, ?, ?, ?)',
            (user_id, action, module, description, request.remote_addr)
        )
        db.commit()
        db.close()
    except:
        pass  # Fail silently

@bp.route('/cleanup', methods=['POST'])
def cleanup_orphaned_files():
    """Clean up orphaned files (admin only)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # This would require admin privileges
    db = get_db()
    cursor = db.cursor()
    
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
    
    referenced_files = set(row[0] for row in cursor.fetchall())
    
    # Get all files in upload directories
    base_folder = current_app.config['UPLOAD_FOLDER']
    orphaned = []
    
    for doc_type in ['passports', 'aadhaar', 'pan', 'vaccine', 'photos']:
        folder = os.path.join(base_folder, doc_type)
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                if filename not in referenced_files:
                    orphaned.append(os.path.join(folder, filename))
    
    db.close()
    
    return jsonify({
        'success': True,
        'orphaned_count': len(orphaned),
        'orphaned_files': orphaned
    })
