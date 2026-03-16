from flask import Blueprint, request, jsonify, session, current_app
from app.database import release_db, get_db
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename

bp = Blueprint('company', __name__, url_prefix='/api/company')

# ====== COMPANY SETTINGS MANAGEMENT ======

@bp.route('/settings', methods=['GET'])
def get_settings():
    """Get company settings"""
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT * FROM company_settings LIMIT 1")
        settings = cursor.fetchone()
        return jsonify({'success': True, 'settings': dict(settings) if settings else {}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

        return jsonify({
            'success': True, 
            'settings': {
                # Company Details
                'legal_name': 'Alhudha Haj Service P Ltd.',
                'display_name': 'Alhudha Haj Travel',
                
                # Address
                'address_line1': '2/117, Second Floor, Armenian Street',
                'address_line2': 'Mannady',
                'city': 'Chennai',
                'state': 'Tamil Nadu',
                'country': 'India',
                'pin_code': '600001',
                
                # Contact
                'phone': '+91 44 1234 5678',
                'mobile': '+91 98765 43210',
                'email': 'info@alhudha.com',
                'website': 'www.alhudha.com',
                
                # Tax Information
                'gstin': '',
                'pan': '',
                'tan': '',
                'tcs_no': '',
                'tin': '',
                'cin': '',
                'iec': '',
                'msme': '',
                
                # Bank Details
                'bank_name': '',
                'bank_branch': '',
                'account_name': '',
                'account_no': '',
                'ifsc_code': '',
                'micr_code': '',
                'upi_id': '',
                'qr_code': '',
                
                # Logo
                'logo': ''
            }
        })

@bp.route('/settings', methods=['POST'])
def update_settings():
    """Update complete company settings (ALL 48 FIELDS)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    conn, cursor = get_db()
    
    try:
        # Check if settings exist
        try:
        cursor.execute('SELECT id FROM company_settings WHERE id = 1')
        exists = cursor.fetchone()
        
        now = datetime.now()
        
        if exists:
            # Update existing settings
            cursor.execute('''
                UPDATE company_settings SET
                    -- Company Details
                    legal_name = %s,
                    display_name = %s,
                    
                    -- Address
                    address_line1 = %s,
                    address_line2 = %s,
                    city = %s,
                    state = %s,
                    country = %s,
                    pin_code = %s,
                    
                    -- Contact
                    phone = %s,
                    mobile = %s,
                    email = %s,
                    website = %s,
                    
                    -- Tax Information
                    gstin = %s,
                    pan = %s,
                    tan = %s,
                    tcs_no = %s,
                    tin = %s,
                    cin = %s,
                    iec = %s,
                    msme = %s,
                    
                    -- Bank Details
                    bank_name = %s,
                    bank_branch = %s,
                    account_name = %s,
                    account_no = %s,
                    ifsc_code = %s,
                    micr_code = %s,
                    upi_id = %s,
                    qr_code = %s,
                    
                    -- Logo
                    logo = %s,
                    
                    -- Metadata
                    updated_at = %s
                WHERE id = 1
            ''', (
                # Company Details
                data.get('legal_name'),
                data.get('display_name'),
                
                # Address
                data.get('address_line1'),
                data.get('address_line2'),
                data.get('city'),
                data.get('state'),
                data.get('country', 'India'),
                data.get('pin_code'),
                
                # Contact
                data.get('phone'),
                data.get('mobile'),
                data.get('email'),
                data.get('website'),
                
                # Tax Information
                data.get('gstin'),
                data.get('pan'),
                data.get('tan'),
                data.get('tcs_no'),
                data.get('tin'),
                data.get('cin'),
                data.get('iec'),
                data.get('msme'),
                
                # Bank Details
                data.get('bank_name'),
                data.get('bank_branch'),
                data.get('account_name'),
                data.get('account_no'),
                data.get('ifsc_code'),
                data.get('micr_code'),
                data.get('upi_id'),
                data.get('qr_code'),
                
                # Logo
                data.get('logo'),
                
                # Metadata
                now
            ))
        else:
            # Insert new settings
            cursor.execute('''
                INSERT INTO company_settings (
                    -- Company Details
                    legal_name, display_name,
                    
                    -- Address
                    address_line1, address_line2, city, state, country, pin_code,
                    
                    -- Contact
                    phone, mobile, email, website,
                    
                    -- Tax Information
                    gstin, pan, tan, tcs_no, tin, cin, iec, msme,
                    
                    -- Bank Details
                    bank_name, bank_branch, account_name, account_no, ifsc_code, micr_code, upi_id, qr_code,
                    
                    -- Logo
                    logo,
                    
                    -- Metadata
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                # Company Details
                data.get('legal_name', 'Alhudha Haj Service P Ltd.'),
                data.get('display_name', 'Alhudha Haj Travel'),
                
                # Address
                data.get('address_line1'),
                data.get('address_line2'),
                data.get('city'),
                data.get('state'),
                data.get('country', 'India'),
                data.get('pin_code'),
                
                # Contact
                data.get('phone'),
                data.get('mobile'),
                data.get('email'),
                data.get('website'),
                
                # Tax Information
                data.get('gstin'),
                data.get('pan'),
                data.get('tan'),
                data.get('tcs_no'),
                data.get('tin'),
                data.get('cin'),
                data.get('iec'),
                data.get('msme'),
                
                # Bank Details
                data.get('bank_name'),
                data.get('bank_branch'),
                data.get('account_name'),
                data.get('account_no'),
                data.get('ifsc_code'),
                data.get('micr_code'),
                data.get('upi_id'),
                data.get('qr_code'),
                
                # Logo
                data.get('logo'),
                
                # Metadata
                now,
                now
            ))
        
        # Log activity
        log_activity(session['user_id'], 'update', 'company', 'Updated company settings', request.remote_addr)
        
        conn.commit()
        cursor.close()
        conn.close()
    finally:
        release_db(conn, cursor)
        
        return jsonify({
            'success': True, 
            'message': 'Company settings updated successfully'
        })
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/logo', methods=['POST'])
def upload_logo():
    """Upload company logo"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    if 'logo' not in request.files:
        return jsonify({'success': False, 'error': 'No logo file provided'}), 400
    
    file = request.files['logo']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({'success': False, 'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, svg'}), 400
    
    # Generate unique filename
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    ext = filename.rsplit('.', 1)[1].lower()
    new_filename = f"logo_{timestamp}.{ext}"
    
    # Save file
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'company')
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, new_filename)
    file.save(file_path)
    
    # Update database with logo path
    conn, cursor = get_db()
    try:
        cursor.execute('''
        UPDATE company_settings 
        SET logo = %s, updated_at = %s
        WHERE id = 1
    ''', (f'/uploads/company/{new_filename}', datetime.now()))
    conn.commit()
    cursor.close()
    conn.close()
    finally:
        release_db(conn, cursor)
    
    # Log activity
    log_activity(session['user_id'], 'upload', 'company', 'Uploaded company logo', request.remote_addr)
    
    return jsonify({
        'success': True,
        'logo_url': f'/uploads/company/{new_filename}',
        'message': 'Logo uploaded successfully'
    })

@bp.route('/details', methods=['GET'])
def get_company_details():
    """Get formatted company details for invoices/receipts"""
    conn, cursor = get_db()
    try:
        cursor.execute('SELECT * FROM company_settings WHERE id = 1')
    settings = cursor.fetchone()
        conn.commit()
    except Exception as e:
        return jsonify({\'success\': False, \'error\': str(e)}), 500
    finally:
        release_db(conn, cursor)
        conn.commit()
    except Exception as e:
        return jsonify({\'success\': False, \'error\': str(e)}), 500
    finally:
        release_db(conn, cursor)    cursor.close()
    conn.close()
    finally:
        release_db(conn, cursor)
    
    if not settings:
        return jsonify({'success': False, 'error': 'Company settings not found'}), 404
    
    settings = dict(settings)
    
    # Format full address
    address_parts = []
    if settings.get('address_line1'):
        address_parts.append(settings['address_line1'])
    if settings.get('address_line2'):
        address_parts.append(settings['address_line2'])
    if settings.get('city'):
        address_parts.append(settings['city'])
    if settings.get('state'):
        address_parts.append(settings['state'])
    if settings.get('pin_code'):
        address_parts.append(settings['pin_code'])
    if settings.get('country'):
        address_parts.append(settings['country'])
    
    full_address = ', '.join(address_parts) if address_parts else ''
    
    return jsonify({
        'success': True,
        'company': {
            'name': settings.get('display_name') or settings.get('legal_name'),
            'legal_name': settings.get('legal_name'),
            'address': full_address,
            'address_line1': settings.get('address_line1'),
            'address_line2': settings.get('address_line2'),
            'city': settings.get('city'),
            'state': settings.get('state'),
            'country': settings.get('country'),
            'pin_code': settings.get('pin_code'),
            'phone': settings.get('phone'),
            'mobile': settings.get('mobile'),
            'email': settings.get('email'),
            'website': settings.get('website'),
            'gstin': settings.get('gstin'),
            'pan': settings.get('pan'),
            'tan': settings.get('tan'),
            'tcs_no': settings.get('tcs_no'),
            'tin': settings.get('tin'),
            'cin': settings.get('cin'),
            'iec': settings.get('iec'),
            'msme': settings.get('msme'),
            'bank_name': settings.get('bank_name'),
            'bank_branch': settings.get('bank_branch'),
            'account_name': settings.get('account_name'),
            'account_no': settings.get('account_no'),
            'ifsc_code': settings.get('ifsc_code'),
            'micr_code': settings.get('micr_code'),
            'upi_id': settings.get('upi_id'),
            'qr_code': settings.get('qr_code'),
            'logo': settings.get('logo')
        }
    })

@bp.route('/bank-details', methods=['GET'])
def get_bank_details():
    """Get bank details only"""
    conn, cursor = get_db()
    try:
        cursor.execute('''
        SELECT 
            bank_name, bank_branch, account_name, account_no,
            ifsc_code, micr_code, upi_id, qr_code
        FROM company_settings WHERE id = 1
    ''')
    bank = cursor.fetchone()
    cursor.close()
    conn.close()
    finally:
        release_db(conn, cursor)
    
    return jsonify({
        'success': True,
        'bank_details': dict(bank) if bank else {}
    })

@bp.route('/tax-details', methods=['GET'])
def get_tax_details():
    """Get tax details only"""
    conn, cursor = get_db()
    try:
        cursor.execute('''
        SELECT 
            gstin, pan, tan, tcs_no, tin, cin, iec, msme
        FROM company_settings WHERE id = 1
    ''')
    tax = cursor.fetchone()
    cursor.close()
    conn.close()
    finally:
        release_db(conn, cursor)
    
    return jsonify({
        'success': True,
        'tax_details': dict(tax) if tax else {}
    })

@bp.route('/contact-details', methods=['GET'])
def get_contact_details():
    """Get contact details only"""
    conn, cursor = get_db()
    try:
        cursor.execute('''
        SELECT 
            phone, mobile, email, website,
            address_line1, address_line2, city, state, country, pin_code
        FROM company_settings WHERE id = 1
    ''')
    contact = cursor.fetchone()
    cursor.close()
    conn.close()
    finally:
        release_db(conn, cursor)
    
    return jsonify({
        'success': True,
        'contact_details': dict(contact) if contact else {}
    })

@bp.route('/initialize', methods=['POST'])
def initialize_settings():
    """Initialize company settings with default values"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    
    try:
        # Check if settings already exist
        try:
        cursor.execute('SELECT id FROM company_settings WHERE id = 1')
        exists = cursor.fetchone()
        
        if not exists:
            now = datetime.now()
            cursor.execute('''
                INSERT INTO company_settings (
                    id, legal_name, display_name, country, created_at, updated_at
                ) VALUES (1, %s, %s, %s, %s, %s)
            ''', (
                'Alhudha Haj Service P Ltd.',
                'Alhudha Haj Travel',
                'India',
                now,
                now
            ))
            conn.commit()
            message = 'Company settings initialized with defaults'
        else:
            message = 'Company settings already exist'
        
        cursor.close()
        conn.close()
    finally:
        release_db(conn, cursor)
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 400

# Helper function to log activity
def log_activity(user_id, action, module, description, ip_address=None):
    """Log user activity"""
    try:
        conn, cursor = get_db()
        try:
        cursor.execute(
            'INSERT INTO activity_log (user_id, action, module, description, ip_address, created_at) VALUES (%s, %s, %s, %s, %s, %s)',
            (user_id, action, module, description, ip_address or request.remote_addr, datetime.now())
        )
        conn.commit()
        cursor.close()
        conn.close()
    finally:
        release_db(conn, cursor)
    except Exception as e:
        print(f"⚠️ Activity log error: {e}")
