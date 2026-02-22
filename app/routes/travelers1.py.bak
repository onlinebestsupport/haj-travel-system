from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime
import json

bp = Blueprint('travelers', __name__, url_prefix='/api/travelers')

@bp.route('', methods=['GET'])
def get_travelers():
    """Get all travelers with complete details"""
    db = get_db()
    cursor = db.cursor()
    
    # Get all travelers with batch info and payment summary
    cursor.execute('''
        SELECT 
            t.*, 
            b.batch_name,
            b.price as batch_price,
            b.departure_date,
            b.return_date,
            (SELECT COUNT(*) FROM payments WHERE traveler_id = t.id AND status = 'completed') as payment_count,
            (SELECT SUM(amount) FROM payments WHERE traveler_id = t.id AND status = 'completed') as total_paid
        FROM travelers t
        LEFT JOIN batches b ON t.batch_id = b.id
        ORDER BY t.created_at DESC
    ''')
    
    travelers = cursor.fetchall()
    db.close()
    
    return jsonify({
        'success': True, 
        'travelers': [dict(t) for t in travelers]
    })

@bp.route('/<int:traveler_id>', methods=['GET'])
def get_traveler(traveler_id):
    """Get single traveler with complete details (ALL 33 FIELDS)"""
    db = get_db()
    cursor = db.cursor()
    
    # Get traveler details
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
        WHERE t.id = ?
    ''', (traveler_id,))
    
    traveler = cursor.fetchone()
    
    if not traveler:
        db.close()
        return jsonify({'success': False, 'error': 'Traveler not found'}), 404
    
    # Get payment history
    cursor.execute('''
        SELECT * FROM payments 
        WHERE traveler_id = ? 
        ORDER BY payment_date DESC
    ''', (traveler_id,))
    payments = cursor.fetchall()
    
    # Get payment summary
    cursor.execute('''
        SELECT 
            COUNT(*) as total_transactions,
            SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as total_paid,
            SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as pending_amount,
            MAX(payment_date) as last_payment_date,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count
        FROM payments 
        WHERE traveler_id = ?
    ''', (traveler_id,))
    payment_summary = cursor.fetchone()
    
    # Get invoices
    cursor.execute('''
        SELECT * FROM invoices 
        WHERE traveler_id = ? 
        ORDER BY created_at DESC
    ''', (traveler_id,))
    invoices = cursor.fetchall()
    
    # Get receipts
    cursor.execute('''
        SELECT * FROM receipts 
        WHERE traveler_id = ? 
        ORDER BY created_at DESC
    ''', (traveler_id,))
    receipts = cursor.fetchall()
    
    db.close()
    
    result = dict(traveler)
    result['payments'] = [dict(p) for p in payments]
    result['payment_summary'] = dict(payment_summary) if payment_summary else {}
    result['invoices'] = [dict(i) for i in invoices]
    result['receipts'] = [dict(r) for r in receipts]
    
    # Parse extra_fields if present
    if result.get('extra_fields'):
        try:
            result['extra_fields'] = json.loads(result['extra_fields'])
        except:
            result['extra_fields'] = {}
    
    return jsonify({'success': True, 'traveler': result})

@bp.route('/passport/<string:passport_no>', methods=['GET'])
def get_traveler_by_passport(passport_no):
    """Get traveler by passport number"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT t.*, b.batch_name, b.price as batch_price, 
               b.departure_date, b.return_date, b.status as batch_status
        FROM travelers t
        LEFT JOIN batches b ON t.batch_id = b.id
        WHERE t.passport_no = ?
    ''', (passport_no.upper(),))
    
    traveler = cursor.fetchone()
    
    if not traveler:
        db.close()
        return jsonify({'success': False, 'error': 'Traveler not found'}), 404
    
    # Get payment history
    cursor.execute('''
        SELECT * FROM payments 
        WHERE traveler_id = ? 
        ORDER BY payment_date DESC
    ''', (traveler['id'],))
    payments = cursor.fetchall()
    
    db.close()
    
    result = dict(traveler)
    result['payments'] = [dict(p) for p in payments]
    
    # Parse extra_fields if present
    if result.get('extra_fields'):
        try:
            result['extra_fields'] = json.loads(result['extra_fields'])
        except:
            result['extra_fields'] = {}
    
    return jsonify({'success': True, 'traveler': result})

@bp.route('', methods=['POST'])
def create_traveler():
    """Create new traveler with ALL 33 FIELDS"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    # Validate required fields
    required = ['first_name', 'last_name', 'passport_no', 'mobile', 'batch_id']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    # Auto-generate passport name if not provided
    passport_name = data.get('passport_name') or f"{data['first_name']} {data['last_name']}".strip()
    
    # Validate extra_fields if provided
    extra_fields = data.get('extra_fields', '{}')
    if isinstance(extra_fields, dict):
        extra_fields = json.dumps(extra_fields)
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if passport number already exists
        cursor.execute('SELECT id FROM travelers WHERE passport_no = ?', (data['passport_no'],))
        if cursor.fetchone():
            db.close()
            return jsonify({'success': False, 'error': 'Passport number already exists'}), 400
        
        cursor.execute('''
            INSERT INTO travelers (
                -- Personal Information (10 fields)
                first_name, last_name, passport_name, batch_id,
                passport_no, passport_issue_date, passport_expiry_date,
                passport_status, gender, dob,
                
                -- Contact Information (7 fields)
                mobile, email, aadhaar, pan, aadhaar_pan_linked,
                vaccine_status, wheelchair,
                
                -- Address & Family (7 fields)
                place_of_birth, place_of_issue, passport_address,
                father_name, mother_name, spouse_name,
                
                -- Document Uploads (5 fields)
                passport_scan, aadhaar_scan, pan_scan, vaccine_scan, photo,
                
                -- Additional Information (4 fields)
                pin, emergency_contact, emergency_phone, medical_notes,
                
                -- Extra fields
                extra_fields, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            # Personal Information
            data['first_name'], data['last_name'], passport_name, data['batch_id'],
            data['passport_no'].upper(), data.get('passport_issue_date'), data.get('passport_expiry_date'),
            data.get('passport_status', 'Active'), data.get('gender'), data.get('dob'),
            
            # Contact Information
            data['mobile'], data.get('email'), data.get('aadhaar'), data.get('pan'),
            data.get('aadhaar_pan_linked', 'No'), data.get('vaccine_status', 'Not Vaccinated'),
            data.get('wheelchair', 'No'),
            
            # Address & Family
            data.get('place_of_birth'), data.get('place_of_issue'), data.get('passport_address'),
            data.get('father_name'), data.get('mother_name'), data.get('spouse_name'),
            
            # Documents
            data.get('passport_scan'), data.get('aadhaar_scan'), data.get('pan_scan'),
            data.get('vaccine_scan'), data.get('photo'),
            
            # Additional Information
            data.get('pin', '0000'), data.get('emergency_contact'), data.get('emergency_phone'),
            data.get('medical_notes'),
            
            # Extra fields
            extra_fields,
            datetime.now().isoformat(), datetime.now().isoformat()
        ))
        
        traveler_id = cursor.lastrowid
        
        # Update batch booked seats
        cursor.execute('UPDATE batches SET booked_seats = booked_seats + 1 WHERE id = ?', (data['batch_id'],))
        
        # Log activity
        log_activity(session['user_id'], 'create', 'traveler', f'Created traveler: {data["first_name"]} {data["last_name"]}')
        
        db.commit()
        db.close()
        
        return jsonify({
            'success': True,
            'traveler_id': traveler_id,
            'message': 'Traveler created successfully with all 33 fields'
        })
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/<int:traveler_id>', methods=['PUT'])
def update_traveler(traveler_id):
    """Update traveler with ALL 33 FIELDS"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if traveler exists
        cursor.execute('SELECT id, batch_id FROM travelers WHERE id = ?', (traveler_id,))
        existing = cursor.fetchone()
        if not existing:
            db.close()
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
        
        # Handle batch change
        old_batch_id = existing['batch_id']
        new_batch_id = data.get('batch_id', old_batch_id)
        
        # Process extra_fields
        extra_fields = data.get('extra_fields', '{}')
        if isinstance(extra_fields, dict):
            extra_fields = json.dumps(extra_fields)
        
        cursor.execute('''
            UPDATE travelers SET
                -- Personal Information
                first_name = ?, last_name = ?, passport_name = ?,
                batch_id = ?, passport_no = ?, passport_issue_date = ?,
                passport_expiry_date = ?, passport_status = ?, gender = ?,
                dob = ?,
                
                -- Contact Information
                mobile = ?, email = ?, aadhaar = ?, pan = ?,
                aadhaar_pan_linked = ?, vaccine_status = ?, wheelchair = ?,
                
                -- Address & Family
                place_of_birth = ?, place_of_issue = ?, passport_address = ?,
                father_name = ?, mother_name = ?, spouse_name = ?,
                
                -- Documents (only update if new values provided)
                passport_scan = COALESCE(?, passport_scan),
                aadhaar_scan = COALESCE(?, aadhaar_scan),
                pan_scan = COALESCE(?, pan_scan),
                vaccine_scan = COALESCE(?, vaccine_scan),
                photo = COALESCE(?, photo),
                
                -- Additional Information
                pin = ?, emergency_contact = ?, emergency_phone = ?,
                medical_notes = ?,
                
                -- Extra fields
                extra_fields = ?,
                updated_at = ?
            WHERE id = ?
        ''', (
            # Personal Information
            data['first_name'], data['last_name'], data.get('passport_name'),
            new_batch_id, data['passport_no'].upper(), data.get('passport_issue_date'),
            data.get('passport_expiry_date'), data.get('passport_status', 'Active'),
            data.get('gender'), data.get('dob'),
            
            # Contact Information
            data['mobile'], data.get('email'), data.get('aadhaar'), data.get('pan'),
            data.get('aadhaar_pan_linked', 'No'), data.get('vaccine_status', 'Not Vaccinated'),
            data.get('wheelchair', 'No'),
            
            # Address & Family
            data.get('place_of_birth'), data.get('place_of_issue'), data.get('passport_address'),
            data.get('father_name'), data.get('mother_name'), data.get('spouse_name'),
            
            # Documents (using COALESCE to keep existing if null)
            data.get('passport_scan'), data.get('aadhaar_scan'), data.get('pan_scan'),
            data.get('vaccine_scan'), data.get('photo'),
            
            # Additional Information
            data.get('pin', '0000'), data.get('emergency_contact'), data.get('emergency_phone'),
            data.get('medical_notes'),
            
            # Extra fields
            extra_fields,
            datetime.now().isoformat(),
            traveler_id
        ))
        
        # Update batch counts if batch changed
        if old_batch_id != new_batch_id:
            cursor.execute('UPDATE batches SET booked_seats = booked_seats - 1 WHERE id = ?', (old_batch_id,))
            cursor.execute('UPDATE batches SET booked_seats = booked_seats + 1 WHERE id = ?', (new_batch_id,))
        
        # Log activity
        log_activity(session['user_id'], 'update', 'traveler', f'Updated traveler ID: {traveler_id}')
        
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'message': 'Traveler updated successfully'})
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/<int:traveler_id>', methods=['DELETE'])
def delete_traveler(traveler_id):
    """Delete traveler"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Get traveler details for logging and batch update
        cursor.execute('SELECT id, first_name, last_name, batch_id FROM travelers WHERE id = ?', (traveler_id,))
        traveler = cursor.fetchone()
        
        if not traveler:
            db.close()
            return jsonify({'success': False, 'error': 'Traveler not found'}), 404
        
        # Delete traveler (cascade will handle payments, invoices, receipts)
        cursor.execute('DELETE FROM travelers WHERE id = ?', (traveler_id,))
        
        # Update batch booked seats
        cursor.execute('UPDATE batches SET booked_seats = booked_seats - 1 WHERE id = ?', (traveler['batch_id'],))
        
        # Log activity
        log_activity(session['user_id'], 'delete', 'traveler', f'Deleted traveler: {traveler["first_name"]} {traveler["last_name"]}')
        
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'message': 'Traveler deleted successfully'})
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/<int:traveler_id>/payments', methods=['GET'])
def get_traveler_payments(traveler_id):
    """Get all payments for a traveler"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT * FROM payments 
        WHERE traveler_id = ? 
        ORDER BY payment_date DESC
    ''', (traveler_id,))
    
    payments = cursor.fetchall()
    
    # Get payment summary
    cursor.execute('''
        SELECT 
            COUNT(*) as total_count,
            SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as total_paid,
            SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as total_pending,
            MAX(payment_date) as last_payment
        FROM payments 
        WHERE traveler_id = ?
    ''', (traveler_id,))
    
    summary = cursor.fetchone()
    
    db.close()
    
    return jsonify({
        'success': True,
        'payments': [dict(p) for p in payments],
        'summary': dict(summary) if summary else {}
    })

@bp.route('/<int:traveler_id>/invoices', methods=['GET'])
def get_traveler_invoices(traveler_id):
    """Get all invoices for a traveler"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT * FROM invoices 
        WHERE traveler_id = ? 
        ORDER BY created_at DESC
    ''', (traveler_id,))
    
    invoices = cursor.fetchall()
    db.close()
    
    return jsonify({
        'success': True,
        'invoices': [dict(i) for i in invoices]
    })

@bp.route('/<int:traveler_id>/receipts', methods=['GET'])
def get_traveler_receipts(traveler_id):
    """Get all receipts for a traveler"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT * FROM receipts 
        WHERE traveler_id = ? 
        ORDER BY created_at DESC
    ''', (traveler_id,))
    
    receipts = cursor.fetchall()
    db.close()
    
    return jsonify({
        'success': True,
        'receipts': [dict(r) for r in receipts]
    })

@bp.route('/<int:traveler_id>/documents', methods=['GET'])
def get_traveler_documents(traveler_id):
    """Get document status for a traveler"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            passport_scan, aadhaar_scan, pan_scan, vaccine_scan, photo
        FROM travelers 
        WHERE id = ?
    ''', (traveler_id,))
    
    docs = cursor.fetchone()
    db.close()
    
    if not docs:
        return jsonify({'success': False, 'error': 'Traveler not found'}), 404
    
    result = {}
    for key in ['passport_scan', 'aadhaar_scan', 'pan_scan', 'vaccine_scan', 'photo']:
        result[key] = {
            'uploaded': bool(docs[key]),
            'filename': docs[key] if docs[key] else None
        }
    
    return jsonify({
        'success': True,
        'documents': result
    })

@bp.route('/summary', methods=['GET'])
def get_travelers_summary():
    """Get summary statistics for all travelers"""
    db = get_db()
    cursor = db.cursor()
    
    # Overall statistics
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
    
    # Gender distribution
    cursor.execute('''
        SELECT gender, COUNT(*) as count
        FROM travelers
        WHERE gender IS NOT NULL
        GROUP BY gender
    ''')
    
    gender_dist = cursor.fetchall()
    
    # Vaccine status distribution
    cursor.execute('''
        SELECT vaccine_status, COUNT(*) as count
        FROM travelers
        GROUP BY vaccine_status
    ''')
    
    vaccine_dist = cursor.fetchall()
    
    # Recent registrations
    cursor.execute('''
        SELECT id, first_name, last_name, passport_no, created_at
        FROM travelers
        ORDER BY created_at DESC
        LIMIT 10
    ''')
    
    recent = cursor.fetchall()
    
    db.close()
    
    return jsonify({
        'success': True,
        'summary': dict(stats) if stats else {},
        'gender_distribution': [dict(g) for g in gender_dist],
        'vaccine_distribution': [dict(v) for v in vaccine_dist],
        'recent_registrations': [dict(r) for r in recent]
    })

# Helper function to log activity
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
