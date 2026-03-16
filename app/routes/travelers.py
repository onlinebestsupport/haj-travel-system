from flask import Blueprint, request, jsonify, session, send_file, current_app
from app.database import get_db, release_db
from datetime import datetime
import json
import os
import uuid
from werkzeug.utils import secure_filename
import io
import base64
import csv

bp = Blueprint('travelers', __name__, url_prefix='/api/travelers')

# Configuration for file uploads - using app config
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_folder():
    """Get upload folder path from app config"""
    return os.path.join(current_app.config['UPLOAD_FOLDER'], 'travelers')

def save_uploaded_file(file, traveler_id, doc_type):
    """Save uploaded file and return filename"""
    if not file or not file.filename or not allowed_file(file.filename):
        return None
    
    # Create traveler-specific directory
    upload_folder = get_upload_folder()
    traveler_dir = os.path.join(upload_folder, str(traveler_id))
    os.makedirs(traveler_dir, exist_ok=True)
    
    # Secure filename and generate unique name
    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    filename = f"{doc_type}_{uuid.uuid4().hex[:8]}.{ext}" if ext else f"{doc_type}_{uuid.uuid4().hex[:8]}"
    filepath = os.path.join(traveler_dir, filename)
    
    # Save file
    file.save(filepath)
    
    return filename

def log_activity(user_id, action, module, description, ip_address=None):
    """Log user activity with proper connection handling"""
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
        print(f"⚠️ Error logging activity: {e}")
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('', methods=['GET'])
def get_travelers():
    """Get all travelers"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute('''
            SELECT 
                t.*, 
                b.batch_name,
                b.price as batch_price,
                b.departure_date,
                b.return_date,
                (SELECT COUNT(*) FROM payments WHERE traveler_id = t.id AND status = 'completed') as payment_count,
                (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE traveler_id = t.id AND status = 'completed') as total_paid,
                (SELECT COUNT(*) FROM payments WHERE traveler_id = t.id AND status = 'pending') as pending_count,
                (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE traveler_id = t.id AND status = 'pending') as pending_amount
            FROM travelers t
            LEFT JOIN batches b ON t.batch_id = b.id
            ORDER BY t.created_at DESC
        ''')
        
        travelers = cursor.fetchall()
        
        # Convert to list of dicts and parse extra_fields
        result = []
        for t in travelers:
            t_dict = dict(t)
            if t_dict.get('extra_fields'):
                try:
                    if isinstance(t_dict['extra_fields'], str):
                        t_dict['extra_fields'] = json.loads(t_dict['extra_fields'])
                except:
                    t_dict['extra_fields'] = {}
            result.append(t_dict)
        
        return jsonify({
            'success': True, 
            'travelers': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:traveler_id>', methods=['GET'])
def get_traveler(traveler_id):
    """Get single traveler with complete details"""
    # Check authentication
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # If traveler is accessing, ensure they can only access their own data
    if 'traveler_id' in session and session['traveler_id'] != traveler_id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        cursor.execute('''
            SELECT 
                t.*, 
                b.batch_name,
                b.price as batch_price,
                b.departure_date,
                b.return_date,
                b.status as batch_status,
                b.total_seats,
                b.booked_seats,
                b.description as batch_description
            FROM travelers t
            LEFT JOIN batches b ON t.batch_id = b.id
            WHERE t.id = %s
        ''', (traveler_id,))
        
        traveler = cursor.fetchone()
        
        if not traveler:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
        
        # Get payments
        cursor.execute('''
            SELECT * FROM payments 
            WHERE traveler_id = %s 
            ORDER BY payment_date DESC
        ''', (traveler_id,))
        payments = cursor.fetchall()
        
        # Get payment summary
        cursor.execute('''
            SELECT 
                COUNT(*) as total_transactions,
                COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as total_paid,
                COALESCE(SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END), 0) as pending_amount,
                MAX(payment_date) as last_payment_date,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count
            FROM payments 
            WHERE traveler_id = %s
        ''', (traveler_id,))
        payment_summary = cursor.fetchone()
        
        # Get invoices
        cursor.execute('''
            SELECT * FROM invoices 
            WHERE traveler_id = %s 
            ORDER BY created_at DESC
        ''', (traveler_id,))
        invoices = cursor.fetchall()
        
        # Get receipts
        cursor.execute('''
            SELECT * FROM receipts 
            WHERE traveler_id = %s 
            ORDER BY created_at DESC
        ''', (traveler_id,))
        receipts = cursor.fetchall()
        
        result = dict(traveler)
        result['payments'] = [dict(p) for p in payments]
        result['payment_summary'] = dict(payment_summary) if payment_summary else {}
        result['invoices'] = [dict(i) for i in invoices]
        result['receipts'] = [dict(r) for r in receipts]
        
        if result.get('extra_fields'):
            try:
                if isinstance(result['extra_fields'], str):
                    result['extra_fields'] = json.loads(result['extra_fields'])
            except:
                result['extra_fields'] = {}
        
        return jsonify({'success': True, 'traveler': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/passport/<string:passport_no>', methods=['GET'])
def get_traveler_by_passport(passport_no):
    """Get traveler by passport number"""
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        cursor.execute('''
            SELECT t.*, b.batch_name, b.price as batch_price, 
                   b.departure_date, b.return_date, b.status as batch_status
            FROM travelers t
            LEFT JOIN batches b ON t.batch_id = b.id
            WHERE t.passport_no = %s
        ''', (passport_no.upper(),))
        
        traveler = cursor.fetchone()
        
        if not traveler:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
        
        cursor.execute('''
            SELECT * FROM payments 
            WHERE traveler_id = %s 
            ORDER BY payment_date DESC
        ''', (traveler['id'],))
        payments = cursor.fetchall()
        
        result = dict(traveler)
        result['payments'] = [dict(p) for p in payments]
        
        if result.get('extra_fields'):
            try:
                if isinstance(result['extra_fields'], str):
                    result['extra_fields'] = json.loads(result['extra_fields'])
            except:
                result['extra_fields'] = {}
        
        return jsonify({'success': True, 'traveler': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('', methods=['POST'])
def create_traveler():
    """Create new traveler"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # Handle multipart/form-data for file uploads
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form.to_dict()
        files = request.files
    else:
        data = request.json
        files = {}
    
    # Validate required fields
    required = ['first_name', 'last_name', 'passport_no', 'mobile', 'batch_id']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    # Validate batch_id is integer
    try:
        batch_id = int(data['batch_id'])
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid batch_id'}), 400
    
    passport_name = data.get('passport_name') or f"{data['first_name']} {data['last_name']}".strip()
    
    extra_fields = data.get('extra_fields', '{}')
    if isinstance(extra_fields, dict):
        extra_fields = json.dumps(extra_fields)
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        # Check for duplicate passport
        cursor.execute('SELECT id FROM travelers WHERE passport_no = %s', (data['passport_no'].upper(),))
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'Passport number already exists'}), 400
        
        # Insert traveler first to get ID
        cursor.execute('''
            INSERT INTO travelers (
                first_name, last_name, passport_name, batch_id,
                passport_no, passport_issue_date, passport_expiry_date,
                passport_status, gender, dob,
                mobile, email, aadhaar, pan, aadhaar_pan_linked,
                vaccine_status, wheelchair,
                place_of_birth, place_of_issue, passport_address,
                father_name, mother_name, spouse_name,
                pin, emergency_contact, emergency_phone, medical_notes,
                extra_fields, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            data['first_name'],
            data['last_name'],
            passport_name,
            batch_id,
            data['passport_no'].upper(),
            data.get('passport_issue_date'),
            data.get('passport_expiry_date'),
            data.get('passport_status', 'Active'),
            data.get('gender'),
            data.get('dob'),
            data['mobile'],
            data.get('email'),
            data.get('aadhaar'),
            data.get('pan'),
            data.get('aadhaar_pan_linked', 'No'),
            data.get('vaccine_status', 'Not Vaccinated'),
            data.get('wheelchair', 'No'),
            data.get('place_of_birth'),
            data.get('place_of_issue'),
            data.get('passport_address'),
            data.get('father_name'),
            data.get('mother_name'),
            data.get('spouse_name'),
            data.get('pin', '0000'),
            data.get('emergency_contact'),
            data.get('emergency_phone'),
            data.get('medical_notes'),
            extra_fields,
            datetime.now(),
            datetime.now()
        ))
        
        result = cursor.fetchone()
        traveler_id = result['id'] if result else None
        
        # Handle document fields
        document_fields = ['passport_scan', 'aadhaar_scan', 'pan_scan', 'vaccine_scan', 'photo']
        document_updates = []
        document_values = []
        
        for doc_field in document_fields:
            # Case 1: File upload
            if doc_field in files and files[doc_field]:
                file = files[doc_field]
                if file and file.filename:
                    filename = save_uploaded_file(file, traveler_id, doc_field)
                    if filename:
                        document_updates.append(f"{doc_field} = %s")
                        document_values.append(filename)
            # Case 2: JSON data with document content
            elif doc_field in data and data[doc_field] is not None and data[doc_field]:
                document_updates.append(f"{doc_field} = %s")
                document_values.append(data[doc_field])
        
        if document_updates:
            update_query = f"UPDATE travelers SET {', '.join(document_updates)} WHERE id = %s"
            document_values.append(traveler_id)
            cursor.execute(update_query, document_values)
        
        # Update batch booked seats
        cursor.execute('UPDATE batches SET booked_seats = booked_seats + 1 WHERE id = %s', (batch_id,))
        
        # Log activity
        log_activity(session['user_id'], 'create', 'traveler', f'Created traveler: {data["first_name"]} {data["last_name"]}', request.remote_addr)
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'traveler_id': traveler_id,
            'message': 'Traveler created successfully'
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:traveler_id>', methods=['PUT'])
def update_traveler(traveler_id):
    """Update traveler"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # Handle multipart/form-data for file uploads
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form.to_dict()
        files = request.files
    else:
        data = request.json
        files = {}
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        cursor.execute('SELECT id, batch_id, first_name, last_name FROM travelers WHERE id = %s', (traveler_id,))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
        
        old_batch_id = existing['batch_id']
        new_batch_id = int(data.get('batch_id', old_batch_id)) if data.get('batch_id') else old_batch_id
        
        extra_fields = data.get('extra_fields', '{}')
        if isinstance(extra_fields, dict):
            extra_fields = json.dumps(extra_fields)
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        # Text fields that can be updated
        text_fields = [
            'first_name', 'last_name', 'passport_name', 'passport_no',
            'passport_issue_date', 'passport_expiry_date', 'passport_status',
            'gender', 'dob', 'mobile', 'email', 'aadhaar', 'pan',
            'aadhaar_pan_linked', 'vaccine_status', 'wheelchair',
            'place_of_birth', 'place_of_issue', 'passport_address',
            'father_name', 'mother_name', 'spouse_name', 'pin',
            'emergency_contact', 'emergency_phone', 'medical_notes'
        ]
        
        for field in text_fields:
            if field in data and data[field] is not None:
                update_fields.append(f"{field} = %s")
                if field == 'passport_no':
                    values.append(data[field].upper())
                else:
                    values.append(data[field])
        
        # Handle document fields
        document_fields = ['passport_scan', 'aadhaar_scan', 'pan_scan', 'vaccine_scan', 'photo']
        
        # Case 1: Document fields as file uploads
        for doc_field in document_fields:
            if doc_field in files and files[doc_field]:
                file = files[doc_field]
                if file and file.filename:
                    filename = save_uploaded_file(file, traveler_id, doc_field)
                    if filename:
                        update_fields.append(f"{doc_field} = %s")
                        values.append(filename)
        
        # Case 2: Document fields as JSON data
        for doc_field in document_fields:
            if doc_field in data and data[doc_field] is not None and data[doc_field]:
                update_fields.append(f"{doc_field} = %s")
                values.append(data[doc_field])
        
        # Add batch_id if changed
        if 'batch_id' in data and data['batch_id']:
            update_fields.append("batch_id = %s")
            values.append(new_batch_id)
        
        # Add extra_fields
        if 'extra_fields' in data:
            update_fields.append("extra_fields = %s")
            values.append(extra_fields)
        
        # Add updated_at
        update_fields.append("updated_at = %s")
        values.append(datetime.now())
        
        if update_fields:
            query = f"UPDATE travelers SET {', '.join(update_fields)} WHERE id = %s"
            values.append(traveler_id)
            cursor.execute(query, values)
        
        # Update batch seats if batch changed
        if old_batch_id != new_batch_id:
            cursor.execute('UPDATE batches SET booked_seats = booked_seats - 1 WHERE id = %s', (old_batch_id,))
            cursor.execute('UPDATE batches SET booked_seats = booked_seats + 1 WHERE id = %s', (new_batch_id,))
        
        # Log activity
        log_activity(session['user_id'], 'update', 'traveler', f'Updated traveler ID: {traveler_id}', request.remote_addr)
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Traveler updated successfully'})
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:traveler_id>', methods=['DELETE'])
def delete_traveler(traveler_id):
    """Delete traveler"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        cursor.execute('SELECT id, first_name, last_name, batch_id FROM travelers WHERE id = %s', (traveler_id,))
        traveler = cursor.fetchone()
        
        if not traveler:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
        
        # Delete associated files
        upload_folder = get_upload_folder()
        traveler_dir = os.path.join(upload_folder, str(traveler_id))
        if os.path.exists(traveler_dir):
            import shutil
            shutil.rmtree(traveler_dir)
        
        # Delete traveler record
        cursor.execute('DELETE FROM travelers WHERE id = %s', (traveler_id,))
        
        # Update batch booked seats
        cursor.execute('UPDATE batches SET booked_seats = booked_seats - 1 WHERE id = %s', (traveler['batch_id'],))
        
        # Log activity
        log_activity(session['user_id'], 'delete', 'traveler', f'Deleted traveler: {traveler["first_name"]} {traveler["last_name"]}', request.remote_addr)
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Traveler deleted successfully'})
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:traveler_id>/payments', methods=['GET'])
def get_traveler_payments(traveler_id):
    """Get all payments for a traveler"""
    # Check authentication
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # If traveler is accessing, ensure they can only access their own data
    if 'traveler_id' in session and session['traveler_id'] != traveler_id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        cursor.execute('''
            SELECT * FROM payments 
            WHERE traveler_id = %s 
            ORDER BY payment_date DESC
        ''', (traveler_id,))
        
        payments = cursor.fetchall()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_count,
                COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as total_paid,
                COALESCE(SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END), 0) as total_pending,
                MAX(payment_date) as last_payment
            FROM payments 
            WHERE traveler_id = %s
        ''', (traveler_id,))
        
        summary = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'payments': [dict(p) for p in payments],
            'summary': dict(summary) if summary else {}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:traveler_id>/invoices', methods=['GET'])
def get_traveler_invoices(traveler_id):
    """Get all invoices for a traveler"""
    # Check authentication
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # If traveler is accessing, ensure they can only access their own data
    if 'traveler_id' in session and session['traveler_id'] != traveler_id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        cursor.execute('''
            SELECT * FROM invoices 
            WHERE traveler_id = %s 
            ORDER BY created_at DESC
        ''', (traveler_id,))
        
        invoices = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'invoices': [dict(i) for i in invoices]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:traveler_id>/receipts', methods=['GET'])
def get_traveler_receipts(traveler_id):
    """Get all receipts for a traveler"""
    # Check authentication
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # If traveler is accessing, ensure they can only access their own data
    if 'traveler_id' in session and session['traveler_id'] != traveler_id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        cursor.execute('''
            SELECT * FROM receipts 
            WHERE traveler_id = %s 
            ORDER BY created_at DESC
        ''', (traveler_id,))
        
        receipts = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'receipts': [dict(r) for r in receipts]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:traveler_id>/documents', methods=['GET'])
def get_traveler_documents(traveler_id):
    """Get document status and download links for a traveler"""
    # Check authentication
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # If traveler is accessing, ensure they can only access their own data
    if 'traveler_id' in session and session['traveler_id'] != traveler_id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
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
        
        docs = cursor.fetchone()
        
        if not docs:
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
        
        upload_folder = get_upload_folder()
        result = {}
        for key in ['passport_scan', 'aadhaar_scan', 'pan_scan', 'vaccine_scan', 'photo']:
            filename = docs[key]
            if filename:
                filepath = os.path.join(upload_folder, str(traveler_id), filename)
                result[key] = {
                    'uploaded': True,
                    'filename': filename,
                    'url': f'/api/travelers/{traveler_id}/documents/{key}',
                    'exists': os.path.exists(filepath),
                    'size': os.path.getsize(filepath) if os.path.exists(filepath) else 0
                }
            else:
                result[key] = {
                    'uploaded': False,
                    'filename': None
                }
        
        return jsonify({
            'success': True,
            'documents': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:traveler_id>/documents/<string:doc_type>', methods=['GET'])
def download_document(traveler_id, doc_type):
    """Download a specific document for a traveler"""
    # Check authentication
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # If traveler is accessing, ensure they can only access their own data
    if 'traveler_id' in session and session['traveler_id'] != traveler_id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    valid_doc_types = ['passport_scan', 'aadhaar_scan', 'pan_scan', 'vaccine_scan', 'photo']
    if doc_type not in valid_doc_types:
        return jsonify({'success': False, 'error': 'Invalid document type'}), 400
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        cursor.execute(f'SELECT {doc_type} FROM travelers WHERE id = %s', (traveler_id,))
        result = cursor.fetchone()
        
        if not result or not result[doc_type]:
            return jsonify({'success': False, 'error': 'Document not found'}), 404
        
        filename = result[doc_type]
        upload_folder = get_upload_folder()
        filepath = os.path.join(upload_folder, str(traveler_id), filename)
        
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File not found on server'}), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/summary', methods=['GET'])
def get_travelers_summary():
    """Get summary statistics for all travelers"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_travelers,
                SUM(CASE WHEN passport_status = 'Active' THEN 1 ELSE 0 END) as active_passports,
                SUM(CASE WHEN vaccine_status = 'Fully Vaccinated' THEN 1 ELSE 0 END) as fully_vaccinated,
                SUM(CASE WHEN wheelchair = 'Yes' THEN 1 ELSE 0 END) as wheelchair_required,
                COUNT(DISTINCT batch_id) as batches_with_travelers
            FROM travelers
        ''')
        
        stats = cursor.fetchone()
        
        cursor.execute('''
            SELECT gender, COUNT(*) as count
            FROM travelers
            WHERE gender IS NOT NULL
            GROUP BY gender
        ''')
        
        gender_dist = cursor.fetchall()
        
        cursor.execute('''
            SELECT vaccine_status, COUNT(*) as count
            FROM travelers
            GROUP BY vaccine_status
        ''')
        
        vaccine_dist = cursor.fetchall()
        
        cursor.execute('''
            SELECT id, first_name, last_name, passport_no, created_at
            FROM travelers
            ORDER BY created_at DESC
            LIMIT 10
        ''')
        
        recent = cursor.fetchall()
        
        cursor.execute('''
            SELECT 
                b.id, b.batch_name,
                COUNT(t.id) as traveler_count
            FROM batches b
            LEFT JOIN travelers t ON b.id = t.batch_id
            GROUP BY b.id, b.batch_name
        ''')
        
        batch_dist = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'summary': dict(stats) if stats else {},
            'gender_distribution': [dict(g) for g in gender_dist],
            'vaccine_distribution': [dict(v) for v in vaccine_dist],
            'batch_distribution': [dict(b) for b in batch_dist],
            'recent_registrations': [dict(r) for r in recent]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/search', methods=['GET'])
def search_travelers():
    """Search travelers by various criteria"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify({'success': False, 'error': 'Search query too short'}), 400
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        search_term = f'%{query}%'
        cursor.execute('''
            SELECT 
                t.id, t.first_name, t.last_name, t.passport_no, 
                t.mobile, t.email, t.passport_status,
                b.batch_name
            FROM travelers t
            LEFT JOIN batches b ON t.batch_id = b.id
            WHERE 
                t.first_name ILIKE %s OR 
                t.last_name ILIKE %s OR 
                t.passport_no ILIKE %s OR 
                t.mobile ILIKE %s OR 
                t.email ILIKE %s OR
                t.passport_name ILIKE %s
            ORDER BY t.created_at DESC
            LIMIT 50
        ''', [search_term] * 6)
        
        results = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'results': [dict(r) for r in results],
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/export', methods=['POST'])
def export_travelers():
    """Export travelers data in various formats"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    format_type = data.get('format', 'csv')
    fields = data.get('fields', [])
    batch_id = data.get('batch_id')
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        query = '''
            SELECT 
                t.*, b.batch_name
            FROM travelers t
            LEFT JOIN batches b ON t.batch_id = b.id
            WHERE 1=1
        '''
        params = []
        
        if batch_id:
            query += " AND t.batch_id = %s"
            params.append(batch_id)
        
        query += " ORDER BY t.created_at DESC"
        
        cursor.execute(query, params)
        travelers = cursor.fetchall()
        
        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            if fields:
                writer.writerow(fields)
            else:
                writer.writerow(['ID', 'First Name', 'Last Name', 'Passport Name', 'Batch', 
                               'Passport No', 'Mobile', 'Email', 'Status', 'Created At'])
            
            # Write data
            for t in travelers:
                if fields:
                    row = [t.get(f, '') for f in fields]
                else:
                    row = [
                        t['id'], t['first_name'], t['last_name'], t['passport_name'],
                        t['batch_name'], t['passport_no'], t['mobile'], t['email'],
                        t['passport_status'], t['created_at']
                    ]
                writer.writerow(row)
            
            output.seek(0)
            
            # Log activity
            log_activity(session['user_id'], 'export', 'traveler', f'Exported travelers data as CSV', request.remote_addr)
            
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8-sig')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'travelers_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
        
        elif format_type == 'json':
            return jsonify({
                'success': True,
                'data': [dict(t) for t in travelers],
                'count': len(travelers)
            })
        
        else:
            return jsonify({'success': False, 'error': 'Unsupported format'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/stats/monthly', methods=['GET'])
def get_monthly_stats():
    """Get monthly registration and payment statistics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    year = request.args.get('year', datetime.now().year, type=int)
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        # Monthly registrations
        cursor.execute('''
            SELECT 
                TO_CHAR(created_at, 'MM') as month,
                COUNT(*) as count
            FROM travelers
            WHERE EXTRACT(YEAR FROM created_at) = %s
            GROUP BY TO_CHAR(created_at, 'MM')
            ORDER BY month
        ''', (year,))
        
        registrations = cursor.fetchall()
        
        # Monthly payments
        cursor.execute('''
            SELECT 
                TO_CHAR(payment_date, 'MM') as month,
                COALESCE(SUM(amount), 0) as total,
                COUNT(*) as count
            FROM payments
            WHERE EXTRACT(YEAR FROM payment_date) = %s AND status = 'completed'
            GROUP BY TO_CHAR(payment_date, 'MM')
            ORDER BY month
        ''', (year,))
        
        payments = cursor.fetchall()
        
        # Initialize all months with zero
        months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Convert to dictionaries for easier lookup
        reg_dict = {r['month']: r for r in registrations}
        pay_dict = {p['month']: p for p in payments}
        
        registration_data = []
        payment_data = []
        
        for i, month in enumerate(months):
            reg = reg_dict.get(month)
            registration_data.append({
                'month': month_names[i],
                'count': reg['count'] if reg else 0
            })
            
            pay = pay_dict.get(month)
            payment_data.append({
                'month': month_names[i],
                'total': float(pay['total']) if pay else 0,
                'count': pay['count'] if pay else 0
            })
        
        return jsonify({
            'success': True,
            'year': year,
            'registrations': registration_data,
            'payments': payment_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)