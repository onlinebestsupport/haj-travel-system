from flask import Flask, send_from_directory, jsonify, request, session
from flask_cors import CORS
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import hashlib
import uuid
import threading
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== ENVIRONMENT CONFIGURATION ====================
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import database
from app.database import get_db, init_db

# Import route blueprints
from app.routes import auth, admin, batches, travelers, payments, company, uploads, reports, invoices, receipts

# ==================== FLASK APP INITIALIZATION ====================
app = Flask(__name__)

# Global flag to track database initialization
_db_initialized = False
_db_init_lock = threading.Lock()

# ==================== APP CONFIGURATION ====================
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'alhudha-haj-secret-key-2026')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SESSION_COOKIE_NAME'] = 'alhudha_session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ==================== DIRECTORY PATHS ====================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
ADMIN_DIR = os.path.join(PUBLIC_DIR, 'admin')
TRAVELER_DIR = os.path.join(PUBLIC_DIR, 'traveler')

print(f"📁 Base directory: {BASE_DIR}")
print(f"📁 Public directory: {PUBLIC_DIR}")
print(f"📁 Admin directory: {ADMIN_DIR}")
print(f"📁 Traveler directory: {TRAVELER_DIR}")
print(f"📁 Uploads directory: {app.config['UPLOAD_FOLDER']}")

# Check if directories exist
print(f"📁 Public exists: {os.path.exists(PUBLIC_DIR)}")
print(f"📁 Admin exists: {os.path.exists(ADMIN_DIR)}")
print(f"📁 Traveler exists: {os.path.exists(TRAVELER_DIR)}")

# ==================== CORS CONFIGURATION ====================
CORS(app, supports_credentials=True, origins=['*'])

# ==================== UPLOAD DIRECTORIES ====================
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'passports'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'aadhaar'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'pan'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'vaccine'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'photos'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'backups'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'company'), exist_ok=True)

# ==================== BLUEPRINT REGISTRATION ====================
app.register_blueprint(auth.bp)
app.register_blueprint(admin.bp)
app.register_blueprint(batches.bp)
app.register_blueprint(travelers.bp)
app.register_blueprint(payments.bp)
app.register_blueprint(company.bp)
app.register_blueprint(uploads.bp)
app.register_blueprint(reports.bp)
app.register_blueprint(invoices.bp)	
app.register_blueprint(receipts.bp)

# ==================== HEALTH ENDPOINTS (Always work) ====================
@app.route('/')
def root():
    return jsonify({
        'success': True,
        'message': 'Alhudha Haj Travel API',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
@app.route('/api/health')
def simple_health():
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200

# ==================== LAZY DATABASE INITIALIZATION ====================
def initialize_database():
    global _db_initialized
    
    with _db_init_lock:
        if _db_initialized:
            return True
        
        print("🚀 Initializing database on first request...")
        try:
            with app.app_context():
                init_result = {'success': False}
                
                def init_thread_func():
                    try:
                        init_db()
                        init_result['success'] = True
                    except Exception as e:
                        print(f"❌ DB init error: {e}")
                
                init_thread = threading.Thread(target=init_thread_func)
                init_thread.daemon = True
                init_thread.start()
                init_thread.join(timeout=25)
                
                if init_thread.is_alive():
                    print("⚠️ DB init continuing in background")
                    _db_initialized = True
                    return True
                elif init_result['success']:
                    print("✅ Database initialized")
                    _db_initialized = True
                    return True
                else:
                    return False
        except Exception as e:
            print(f"⚠️ DB init error: {e}")
            return False

@app.before_request
def before_request():
    if request.path in ['/', '/health', '/api/health']:
        return
    if not _db_initialized:
        initialize_database()

# ==================== API ROUTES - AUTH ====================
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    try:
        initialize_database()
        conn, cursor = get_db()
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session.permanent = True
            
            cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s', (user['id'],))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'name': user['full_name'],
                    'role': user['role'],
                    'permissions': json.loads(user['permissions']) if user['permissions'] else {}
                }
            })
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/traveler/login', methods=['POST'])
def api_traveler_login():
    data = request.json
    passport_no = data.get('passport_no')
    pin = data.get('pin')
    
    if not passport_no or not pin:
        return jsonify({'success': False, 'error': 'Passport number and PIN required'}), 400
    
    try:
        initialize_database()
        conn, cursor = get_db()
        cursor.execute(
            'SELECT * FROM travelers WHERE passport_no = %s AND pin = %s',
            (passport_no.upper(), pin)
        )
        traveler = cursor.fetchone()
        
        if traveler:
            session['traveler_id'] = traveler['id']
            session['traveler_passport'] = traveler['passport_no']
            session['traveler_name'] = f"{traveler['first_name']} {traveler['last_name']}"
            session.permanent = True
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'traveler_id': traveler['id'],
                'name': f"{traveler['first_name']} {traveler['last_name']}",
                'passport': traveler['passport_no']
            })
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Invalid passport number or PIN'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/check-session', methods=['GET'])
def check_session():
    if session.get('user_id'):
        try:
            initialize_database()
            conn, cursor = get_db()
            cursor.execute(
                'SELECT id, username, full_name, role FROM users WHERE id = %s', 
                (session['user_id'],)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user:
                return jsonify({
                    'success': True,
                    'authenticated': True,
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'name': user['full_name'],
                        'role': user['role']
                    }
                })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    elif session.get('traveler_id'):
        return jsonify({
            'success': True,
            'authenticated': True,
            'traveler': {
                'id': session['traveler_id'],
                'name': session['traveler_name'],
                'passport': session['traveler_passport']
            }
        })
    
    return jsonify({'success': True, 'authenticated': False})

# ==================== API ROUTES - FRONTPAGE ====================
@app.route('/api/frontpage/config', methods=['GET'])
def get_frontpage_config():
    """Get complete frontpage configuration"""
    try:
        initialize_database()
        conn, cursor = get_db()
        cursor.execute('SELECT * FROM frontpage_settings WHERE id = 1')
        config = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if config:
            return jsonify({'success': True, **dict(config)})
        else:
            return jsonify({'success': False, 'error': 'Configuration not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/frontpage/config', methods=['POST'])
def update_frontpage_config():
    """Update frontpage configuration"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.json
    
    try:
        initialize_database()
        conn, cursor = get_db()
        cursor.execute("""
            UPDATE frontpage_settings SET
                hero_heading = %s, hero_subheading = %s, hero_button_text = %s,
                hero_button_link = %s, packages_title = %s, footer_text = %s,
                footer_phone = %s, footer_email = %s, facebook_url = %s,
                twitter_url = %s, instagram_url = %s, alert_enabled = %s,
                alert_message = %s, alert_link = %s, alert_color = %s,
                alert_style = %s, whatsapp_number = %s, whatsapp_message = %s,
                booking_email = %s, email_subject = %s, whatsapp_enabled = %s,
                email_enabled = %s, packages = %s, features = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (
            data.get('hero_heading'), data.get('hero_subheading'), data.get('hero_button_text'),
            data.get('hero_button_link'), data.get('packages_title'), data.get('footer_text'),
            data.get('footer_phone'), data.get('footer_email'), data.get('facebook_url'),
            data.get('twitter_url'), data.get('instagram_url'), data.get('alert_enabled', False),
            data.get('alert_message'), data.get('alert_link'), data.get('alert_color'),
            data.get('alert_style'), data.get('whatsapp_number'), data.get('whatsapp_message'),
            data.get('booking_email'), data.get('email_subject'), data.get('whatsapp_enabled', False),
            data.get('email_enabled', False), json.dumps(data.get('packages', [])),
            json.dumps(data.get('features', []))
        ))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/frontpage/publish', methods=['POST'])
def publish_frontpage():
    """Publish frontpage configuration with full company details"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    
    try:
        conn, cursor = get_db()
        
        # Update frontpage_settings
        cursor.execute("""
            UPDATE frontpage_settings SET
                hero_heading = %s,
                hero_subheading = %s,
                hero_button_text = %s,
                hero_button_link = %s,
                packages_title = %s,
                footer_text = %s,
                footer_phone = %s,
                footer_email = %s,
                facebook_url = %s,
                twitter_url = %s,
                instagram_url = %s,
                alert_enabled = %s,
                alert_message = %s,
                alert_link = %s,
                alert_color = %s,
                alert_style = %s,
                whatsapp_number = %s,
                whatsapp_message = %s,
                booking_email = %s,
                email_subject = %s,
                whatsapp_enabled = %s,
                email_enabled = %s,
                packages = %s,
                features = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (
            data['hero']['heading'],
            data['hero']['subheading'],
            data['hero']['button'],
            data['hero']['buttonLink'],
            data['packagesTitle'],
            data['footer']['text'],
            data['footer']['phone'],
            data['footer']['email'],
            data['contact']['facebook'],
            data['contact']['twitter'],
            data['contact']['instagram'],
            data['alert']['enabled'],
            data['alert']['message'],
            data['alert']['link'],
            data['alert']['color'],
            data['alert']['style'],
            data['contact']['whatsapp'],
            data['contact']['whatsappMessage'],
            data['contact']['email'],
            data['contact']['emailSubject'],
            data['whatsappEnabled'],
            data['emailEnabled'],
            json.dumps(data['packages']),
            json.dumps(data['features'])
        ))
        
        # Update company_settings with all 48 fields
        cursor.execute("""
            UPDATE company_settings SET
                legal_name = %s,
                display_name = %s,
                address_line1 = %s,
                address_line2 = %s,
                city = %s,
                state = %s,
                country = %s,
                pin_code = %s,
                phone = %s,
                mobile = %s,
                email = %s,
                website = %s,
                gstin = %s,
                pan = %s,
                tan = %s,
                tcs_no = %s,
                tin = %s,
                cin = %s,
                iec = %s,
                msme = %s,
                bank_name = %s,
                bank_branch = %s,
                account_name = %s,
                account_no = %s,
                ifsc_code = %s,
                micr_code = %s,
                upi_id = %s,
                qr_code = %s,
                logo = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (
            data['company']['legalName'],
            data['company']['displayName'],
            data['company']['address1'],
            data['company']['address2'],
            data['company']['city'],
            data['company']['state'],
            data['company']['country'],
            data['company']['pin'],
            data['company']['phone'],
            data['company']['mobile'],
            data['company']['email'],
            data['company']['website'],
            data['company']['gstin'],
            data['company']['pan'],
            data['company']['tan'],
            data['company']['tcs'],
            data['company']['tin'],
            data['company']['cin'],
            data['company']['iec'],
            data['company']['msme'],
            data['company']['bankName'],
            data['company']['bankBranch'],
            data['company']['accountName'],
            data['company']['accountNo'],
            data['company']['ifsc'],
            data['company']['micr'],
            data['company']['upi'],
            data['company']['qr'],
            data.get('logo', '')
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log the publish action
        log_admin_action(session['user_id'], 'publish_frontpage', 'Published website frontpage')
        
        return jsonify({'success': True, 'message': 'Frontpage published successfully'})
        
    except Exception as e:
        print(f"❌ Publish error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/frontpage/whatsapp', methods=['GET'])
def get_whatsapp_config():
    """Get WhatsApp configuration"""
    try:
        initialize_database()
        conn, cursor = get_db()
        cursor.execute('SELECT number, message_template FROM whatsapp_settings WHERE id = 1')
        config = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if config:
            return jsonify({'success': True, **dict(config)})
        else:
            return jsonify({'success': False, 'error': 'WhatsApp config not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/frontpage/email', methods=['GET'])
def get_email_config():
    """Get email configuration"""
    try:
        initialize_database()
        conn, cursor = get_db()
        cursor.execute('SELECT from_email, reply_to, subject_prefix FROM email_settings WHERE id = 1')
        config = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if config:
            return jsonify({'success': True, **dict(config)})
        else:
            return jsonify({'success': False, 'error': 'Email config not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API ROUTES - DATABASE INIT ====================
@app.route('/api/admin/init-db', methods=['POST'])
def init_database_route():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        with app.app_context():
            success = initialize_database()
            if success:
                return jsonify({'success': True, 'message': 'Database initialized'})
            else:
                return jsonify({'success': False, 'error': 'Database init failed'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API ROUTES - MIGRATIONS ====================
@app.route('/api/admin/migrate-receipts', methods=['POST'])
def migrate_receipts():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app.database import migrate_receipts_table
        migrate_receipts_table()
        return jsonify({'success': True, 'message': 'Receipts table migrated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== STATIC FILE ROUTES ====================
@app.route('/')
def serve_index():
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    if '..' in filename or filename.startswith('/'):
        return jsonify({'success': False, 'error': 'Invalid path'}), 400
    
    if '.' in filename:
        try:
            return send_from_directory(PUBLIC_DIR, filename)
        except:
            pass
    
    try:
        return send_from_directory(PUBLIC_DIR, filename + '.html')
    except:
        return jsonify({'success': False, 'error': 'File not found'}), 404

@app.route('/admin/<path:filename>')
def serve_admin(filename):
    if '..' in filename or filename.startswith('/'):
        return jsonify({'success': False, 'error': 'Invalid path'}), 400

    file_path = os.path.join(ADMIN_DIR, filename)

    if os.path.exists(file_path):
        return send_from_directory(ADMIN_DIR, filename)

    if '.' not in filename:
        html_file = filename + '.html'
        html_path = os.path.join(ADMIN_DIR, html_file)

        if os.path.exists(html_path):
            return send_from_directory(ADMIN_DIR, html_file)

    return jsonify({'success': False, 'error': 'Admin file not found'}), 404

@app.route('/traveler/')
@app.route('/traveler')
def serve_traveler_index():
    return send_from_directory(PUBLIC_DIR, 'traveler_dashboard.html')

@app.route('/traveler/<path:filename>')
def serve_traveler(filename):
    if '..' in filename or filename.startswith('/'):
        return jsonify({'success': False, 'error': 'Invalid path'}), 400
    
    try:
        return send_from_directory(PUBLIC_DIR, filename)
    except:
        try:
            return send_from_directory(PUBLIC_DIR, filename + '.html')
        except:
            return jsonify({'success': False, 'error': 'Traveler file not found'}), 404

@app.route('/admin.login.html')
@app.route('/admin/login')
def serve_admin_login():
    return send_from_directory(PUBLIC_DIR, 'admin.login.html')

@app.route('/traveler_login.html')
@app.route('/traveler/login')
def serve_traveler_login():
    return send_from_directory(PUBLIC_DIR, 'traveler_login.html')

@app.route('/frontpage.html')
@app.route('/admin/frontpage.html')
def serve_frontpage():
    return send_from_directory(ADMIN_DIR, 'frontpage.html')

@app.route('/style.css')
def serve_css():
    return send_from_directory(PUBLIC_DIR, 'style.css')

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    if '..' in filename or filename.startswith('/'):
        return jsonify({'success': False, 'error': 'Invalid path'}), 400
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/uploads/company/<path:filename>')
def serve_company_upload(filename):
    if '..' in filename or filename.startswith('/'):
        return jsonify({'success': False, 'error': 'Invalid path'}), 400
    company_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'company')
    return send_from_directory(company_folder, filename)

# ==================== DEBUG ROUTES ====================
@app.route('/debug/paths')
def debug_paths():
    files_in_public = []
    files_in_admin = []
    
    try:
        files_in_public = os.listdir(PUBLIC_DIR) if os.path.exists(PUBLIC_DIR) else []
    except:
        pass
    
    try:
        files_in_admin = os.listdir(ADMIN_DIR) if os.path.exists(ADMIN_DIR) else []
    except:
        pass
    
    return jsonify({
        'base_dir': BASE_DIR,
        'public_dir': PUBLIC_DIR,
        'admin_dir': ADMIN_DIR,
        'public_exists': os.path.exists(PUBLIC_DIR),
        'admin_exists': os.path.exists(ADMIN_DIR),
        'files_in_public': files_in_public,
        'files_in_admin': files_in_admin,
        'dashboard_exists': os.path.exists(os.path.join(ADMIN_DIR, 'dashboard.html')),
        'dashboard_size': os.path.getsize(os.path.join(ADMIN_DIR, 'dashboard.html')) if os.path.exists(os.path.join(ADMIN_DIR, 'dashboard.html')) else 0,
        'frontpage_exists': os.path.exists(os.path.join(ADMIN_DIR, 'frontpage.html'))
    })

@app.route('/debug/test')
def debug_test():
    return jsonify({'success': True, 'message': 'Debug route working!'})

@app.route('/debug/session')
def debug_session():
    return jsonify({
        'session': dict(session),
        'has_user': 'user_id' in session,
        'has_traveler': 'traveler_id' in session
    })

@app.route('/debug/routes')
def debug_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': str(rule)
        })
    return jsonify(routes)

# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# ==================== HELPER FUNCTIONS ====================
def log_admin_action(user_id, action, description):
    """Log admin actions to database"""
    try:
        conn, cursor = get_db()
        cursor.execute("""
            INSERT INTO activity_log (user_id, action, module, description, ip_address, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, action, 'frontpage', description, request.remote_addr, datetime.now()))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Failed to log admin action: {e}")

# ==================== APPLICATION ENTRY POINT ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("=" * 60)
    print("🚀 Alhudha Haj Travel System v2.0")
    print("=" * 60)
    print(f"📁 Server starting on port {port}")
    print(f"📁 Debug mode: {debug}")
    print(f"📁 Binding to: 0.0.0.0:{port}")
    print("=" * 60)
    print("📡 Health check: /health")
    print("📡 API Endpoints ready (lazy DB init)")
    print("📡 Frontpage Editor: /admin/frontpage.html")
    print("📡 Frontpage API: /api/frontpage/config")
    print("📡 Publish API: /api/frontpage/publish")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
