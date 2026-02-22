from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime
import json

bp = Blueprint('company', __name__, url_prefix='/api/company')

@bp.route('/settings', methods=['GET'])
def get_settings():
    """Get complete company settings (ALL 48 FIELDS)"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM company_settings WHERE id = 1')
    settings = cursor.fetchone()
    db.close()
    
    if settings:
        return jsonify({'success': True, 'settings': dict(settings)})
    else:
        # Return default empty structure if not found
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
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if settings exist
        cursor.execute('SELECT id FROM company_settings WHERE id = 1')
        exists = cursor.fetchone()
        
        now = datetime.now().isoformat()
        
        if exists:
            # Update existing settings
            cursor.execute('''
                UPDATE company_settings SET
                    -- Company Details
                    legal_name = ?,
                    display_name = ?,
                    
                    -- Address
                    address_line1 = ?,
                    address_line2 = ?,
                    city = ?,
                    state = ?,
                    country = ?,
                    pin_code = ?,
                    
                    -- Contact
                    phone = ?,
                    mobile = ?,
                    email = ?,
                    website = ?,
                    
                    -- Tax Information
                    gstin = ?,
                    pan = ?,
                    tan = ?,
                    tcs_no = ?,
                    tin = ?,
                    cin = ?,
                    iec = ?,
                    msme = ?,
                    
                    -- Bank Details
                    bank_name = ?,
                    bank_branch = ?,
                    account_name = ?,
                    account_no = ?,
                    ifsc_code = ?,
                    micr_code = ?,
                    upi_id = ?,
                    qr_code = ?,
                    
                    -- Logo
                    logo = ?,
                    
                    -- Metadata
                    updated_at = ?
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
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                now
            ))
        
        # Log activity
        log_activity(session['user_id'], 'update', 'company', 'Updated company settings')
        
        db.commit()
        db.close()
        
        return jsonify({
            'success': True, 
            'message': 'Company settings updated successfully'
        })
        
    except Exception as e:
        db.rollback()
        db.close()
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
    import os
    from werkzeug.utils import secure_filename
    
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    new_filename = f"logo_{timestamp}_{filename}"
    
    # Save file
    upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', 'company')
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, new_filename)
    file.save(file_path)
    
    # Update database with logo path
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        UPDATE company_settings 
        SET logo = ?, updated_at = ?
        WHERE id = 1
    ''', (f'/uploads/company/{new_filename}', datetime.now().isoformat()))
    db.commit()
    db.close()
    
    # Log activity
    log_activity(session['user_id'], 'upload', 'company', 'Uploaded company logo')
    
    return jsonify({
        'success': True,
        'logo_url': f'/uploads/company/{new_filename}',
        'message': 'Logo uploaded successfully'
    })

@bp.route('/details', methods=['GET'])
def get_company_details():
    """Get formatted company details for invoices/receipts"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM company_settings WHERE id = 1')
    settings = cursor.fetchone()
    db.close()
    
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
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT 
            bank_name, bank_branch, account_name, account_no,
            ifsc_code, micr_code, upi_id, qr_code
        FROM company_settings WHERE id = 1
    ''')
    bank = cursor.fetchone()
    db.close()
    
    return jsonify({
        'success': True,
        'bank_details': dict(bank) if bank else {}
    })

@bp.route('/tax-details', methods=['GET'])
def get_tax_details():
    """Get tax details only"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT 
            gstin, pan, tan, tcs_no, tin, cin, iec, msme
        FROM company_settings WHERE id = 1
    ''')
    tax = cursor.fetchone()
    db.close()
    
    return jsonify({
        'success': True,
        'tax_details': dict(tax) if tax else {}
    })

@bp.route('/contact-details', methods=['GET'])
def get_contact_details():
    """Get contact details only"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT 
            phone, mobile, email, website,
            address_line1, address_line2, city, state, country, pin_code
        FROM company_settings WHERE id = 1
    ''')
    contact = cursor.fetchone()
    db.close()
    
    return jsonify({
        'success': True,
        'contact_details': dict(contact) if contact else {}
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
