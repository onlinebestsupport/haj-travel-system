from flask import Blueprint, request, jsonify, session, current_app
from app.database import get_db, release_db
from datetime import datetime
import json
import os

bp = Blueprint('company', __name__, url_prefix='/api/company')

# Default company settings
DEFAULT_SETTINGS = {
    'company_name': 'Alhudha Haj Travel',
    'address': '',
    'phone': '',
    'email': '',
    'website': '',
    'gst': '',
    'pan': '',
    'logo': None,
    'bank_name': '',
    'bank_account': '',
    'bank_ifsc': '',
    'bank_branch': '',
    'terms_conditions': '',
    'invoice_prefix': 'INV',
    'receipt_prefix': 'REC',
    'footer_text': 'Thank you for your business!'
}

@bp.route('/settings', methods=['GET'])
def get_settings():
    """Get company settings"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT * FROM company_settings LIMIT 1")
        settings = cursor.fetchone()
        
        if not settings:
            # Return default settings if none exist
            return jsonify({'success': True, 'settings': DEFAULT_SETTINGS})
        
        # Parse JSON fields
        settings_dict = dict(settings)
        
        return jsonify({'success': True, 'settings': settings_dict})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/settings', methods=['POST'])
def update_settings():
    """Update company settings"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        # Check if settings exist
        cursor.execute("SELECT id FROM company_settings LIMIT 1")
        existing = cursor.fetchone()
        
        if existing:
            # Update existing settings
            query = "UPDATE company_settings SET "
            fields = []
            values = []
            
            updatable_fields = [
                'company_name', 'address', 'phone', 'email', 'website',
                'gst', 'pan', 'logo', 'bank_name', 'bank_account',
                'bank_ifsc', 'bank_branch', 'terms_conditions',
                'invoice_prefix', 'receipt_prefix', 'footer_text'
            ]
            
            for field in updatable_fields:
                if field in data:
                    fields.append(f"{field} = %s")
                    values.append(data[field])
            
            if fields:
                fields.append("updated_at = %s")
                values.append(datetime.now())
                values.append(existing['id'])
                
                query += ", ".join(fields) + " WHERE id = %s"
                cursor.execute(query, values)
        else:
            # Insert new settings
            fields = []
            placeholders = []
            values = []
            
            for field in DEFAULT_SETTINGS.keys():
                fields.append(field)
                placeholders.append("%s")
                values.append(data.get(field, DEFAULT_SETTINGS[field]))
            
            values.append(datetime.now())
            values.append(datetime.now())
            
            query = f"INSERT INTO company_settings ({', '.join(fields)}, created_at, updated_at) VALUES ({', '.join(placeholders)}, %s, %s)"
            cursor.execute(query, values)
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Settings updated successfully'})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

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
    allowed_extensions = {'png', 'jpg', 'jpeg', 'svg', 'gif'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({'success': False, 'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, SVG, GIF'}), 400
    
    # Generate unique filename
    import uuid
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"logo_{uuid.uuid4().hex}.{ext}"
    
    # Save file
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'company')
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    # Update database with logo path
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        # Check if settings exist
        cursor.execute("SELECT id FROM company_settings LIMIT 1")
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("UPDATE company_settings SET logo = %s, updated_at = %s WHERE id = %s",
                          (filename, datetime.now(), existing['id']))
        else:
            # Create settings with logo
            fields = ['logo', 'created_at', 'updated_at']
            placeholders = ['%s', '%s', '%s']
            values = [filename, datetime.now(), datetime.now()]
            
            query = f"INSERT INTO company_settings ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(query, values)
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'logo_url': f'/uploads/company/{filename}',
            'message': 'Logo uploaded successfully'
        })
    except Exception as e:
        if conn:
            conn.rollback()
        # Delete uploaded file if database update fails
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/details', methods=['GET'])
def get_company_details():
    """Get company details for public display"""
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT company_name, address, phone, email, website, logo FROM company_settings LIMIT 1")
        details = cursor.fetchone()
        
        if not details:
            return jsonify({'success': True, 'details': {
                'company_name': DEFAULT_SETTINGS['company_name'],
                'address': '',
                'phone': '',
                'email': '',
                'website': '',
                'logo': None
            }})
        
        details_dict = dict(details)
        if details_dict.get('logo'):
            details_dict['logo_url'] = f'/uploads/company/{details_dict["logo"]}'
        
        return jsonify({'success': True, 'details': details_dict})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/bank-details', methods=['GET'])
def get_bank_details():
    """Get bank details"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT bank_name, bank_account, bank_ifsc, bank_branch FROM company_settings LIMIT 1")
        details = cursor.fetchone()
        
        if not details:
            return jsonify({'success': True, 'details': {
                'bank_name': '',
                'bank_account': '',
                'bank_ifsc': '',
                'bank_branch': ''
            }})
        
        return jsonify({'success': True, 'details': dict(details)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/tax-details', methods=['GET'])
def get_tax_details():
    """Get tax details"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT gst, pan FROM company_settings LIMIT 1")
        details = cursor.fetchone()
        
        if not details:
            return jsonify({'success': True, 'details': {
                'gst': '',
                'pan': ''
            }})
        
        return jsonify({'success': True, 'details': dict(details)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/contact-details', methods=['GET'])
def get_contact_details():
    """Get contact details"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT phone, email, address FROM company_settings LIMIT 1")
        details = cursor.fetchone()
        
        if not details:
            return jsonify({'success': True, 'details': {
                'phone': '',
                'email': '',
                'address': ''
            }})
        
        return jsonify({'success': True, 'details': dict(details)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/initialize', methods=['POST'])
def initialize_settings():
    """Initialize company settings with defaults"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        # Check if settings already exist
        cursor.execute("SELECT id FROM company_settings LIMIT 1")
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'Settings already exist'}), 400
        
        # Insert default settings
        fields = []
        placeholders = []
        values = []
        
        for field, value in DEFAULT_SETTINGS.items():
            fields.append(field)
            placeholders.append("%s")
            values.append(value)
        
        values.append(datetime.now())
        values.append(datetime.now())
        
        query = f"INSERT INTO company_settings ({', '.join(fields)}, created_at, updated_at) VALUES ({', '.join(placeholders)}, %s, %s)"
        cursor.execute(query, values)
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Company settings initialized successfully'})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)