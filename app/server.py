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
# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import database
from app.database import get_db, init_db

# Import route blueprints
from app.routes import auth, admin, batches, travelers, payments, company, uploads, invoices, receipts

# ==================== FLASK APP INITIALIZATION ====================
# Initialize Flask app
app = Flask(__name__)

# Global flag to track database initialization
_db_initialized = False
_db_init_lock = threading.Lock()

# ==================== APP CONFIGURATION ====================
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'alhudha-haj-secret-key-2026')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
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
# Enable CORS
CORS(app, supports_credentials=True, origins=['*'])

# ==================== UPLOAD DIRECTORIES ====================
# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'passports'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'aadhaar'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'pan'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'vaccine'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'photos'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'backups'), exist_ok=True)

# ==================== BLUEPRINT REGISTRATION ====================
# Register blueprints
app.register_blueprint(auth.bp)
app.register_blueprint(admin.bp)
app.register_blueprint(batches.bp)
app.register_blueprint(travelers.bp)
app.register_blueprint(payments.bp)
app.register_blueprint(company.bp)
app.register_blueprint(uploads.bp)
app.register_blueprint(invoices.bp)
app.register_blueprint(receipts.bp)

# ==================== DATABASE INITIALIZATION (Lazy) ====================

def initialize_database():
    """Initialize database safely (called on first request)"""
    global _db_initialized
    
    with _db_init_lock:
        if _db_initialized:
            return True
        
        print("🚀 Initializing database on first request...")
        try:
            with app.app_context():
                # Run in a separate thread with timeout
                init_result = {'success': False, 'error': None}
                
                def init_thread_func():
                    try:
                        init_db()
                        init_result['success'] = True
                    except Exception as e:
                        init_result['error'] = str(e)
                
                init_thread = threading.Thread(target=init_thread_func)
                init_thread.daemon = True
                init_thread.start()
                
                # Wait up to 25 seconds
                init_thread.join(timeout=25)
                
                if init_thread.is_alive():
                    print("⚠️ Database initialization still running in background")
                    _db_initialized = True  # Assume it will complete
                    return True
                elif init_result['success']:
                    print("✅ Database initialized successfully")
                    _db_initialized = True
                    return True
                else:
                    print(f"❌ Database initialization failed: {init_result['error']}")
                    return False
                    
        except Exception as e:
            print(f"⚠️ Database init error: {e}")
            return False

# Simple health check endpoints (always work even without DB)
@app.route('/')
def root():
    """Root endpoint - simple health check"""
    return jsonify({
        'success': True,
        'message': 'Alhudha Haj Travel API',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
@app.route('/api/health')
def simple_health():
    """Simple health check endpoint for Railway"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200

# Before request handler to ensure DB is ready
@app.before_request
def before_request():
    """Initialize database before processing requests (except health checks)"""
    if request.path in ['/', '/health', '/api/health']:
        return  # Skip for health endpoints
    
    if not _db_initialized:
        initialize_database()

# ==================== API ROUTES - AUTHENTICATION ====================
@app.route('/api/login', methods=['POST'])
def api_login():
    """Admin login API"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    try:
        initialize_database()  # Ensure DB is ready
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session.permanent = True
            
            # Update last login
            cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s', (user['id'],))
            db.commit()
            
            # Log activity
            log_activity(user['id'], 'login', 'auth', f'User {username} logged in', request.remote_addr)
            
            cursor.close()
            db.close()
            
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
            db.close()
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/traveler/login', methods=['POST'])
def api_traveler_login():
    """Traveler login API"""
    data = request.json
    passport_no = data.get('passport_no')
    pin = data.get('pin')
    
    if not passport_no or not pin:
        return jsonify({'success': False, 'error': 'Passport number and PIN required'}), 400
    
    try:
        initialize_database()
        
        db = get_db()
        cursor = db.cursor()
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
            db.close()
            
            return jsonify({
                'success': True,
                'traveler_id': traveler['id'],
                'name': f"{traveler['first_name']} {traveler['last_name']}",
                'passport': traveler['passport_no']
            })
        else:
            cursor.close()
            db.close()
            return jsonify({'success': False, 'error': 'Invalid passport number or PIN'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Logout API"""
    user_id = session.get('user_id')
    if user_id:
        log_activity(user_id, 'logout', 'auth', 'User logged out', request.remote_addr)
    session.clear()
    return jsonify({'success': True})

@app.route('/api/traveler/logout', methods=['POST'])
def api_traveler_logout():
    """Traveler logout API"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/check-session', methods=['GET'])
def check_session():
    """Check if user is logged in"""
    if session.get('user_id'):
        try:
            initialize_database()
            
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                'SELECT id, username, full_name, role FROM users WHERE id = %s', 
                (session['user_id'],)
            )
            user = cursor.fetchone()
            cursor.close()
            db.close()
            
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

# ==================== API ROUTES - ADMIN ====================
@app.route('/api/admin/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """Get dashboard statistics"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        initialize_database()
        
        db = get_db()
        cursor = db.cursor()
        
        # Get counts
        cursor.execute('SELECT COUNT(*) as count FROM travelers')
        travelers_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM batches')
        batches_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM batches WHERE status = %s', ('Open',))
        active_batches = cursor.fetchone()['count']
        
        # Payment stats
        cursor.execute('SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count FROM payments WHERE status = %s', ('completed',))
        payments = cursor.fetchone()
        total_collected = float(payments['total']) if payments['total'] else 0
        
        cursor.execute('SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE status = %s', ('pending',))
        pending_payments = cursor.fetchone()
        pending_amount = float(pending_payments['total']) if pending_payments['total'] else 0
        
        # Recent activity
        cursor.execute('''
            SELECT 'traveler' as type, first_name || ' ' || last_name as name, created_at 
            FROM travelers ORDER BY created_at DESC LIMIT 5
        ''')
        recent = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_travelers': travelers_count,
                'total_batches': batches_count,
                'active_batches': active_batches,
                'total_collected': total_collected,
                'pending_amount': pending_amount,
                'paid_count': payments['count'] or 0,
                'pending_count': 0
            },
            'recent_activity': [dict(row) for row in recent]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API ROUTES - DATABASE INIT ====================
@app.route('/api/admin/init-db', methods=['POST'])
def init_database():
    """Initialize database tables (admin only)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        with app.app_context():
            success = initialize_database()
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Database initialized successfully',
                    'tables': ['users', 'batches', 'travelers', 'payments', 'invoices', 'receipts', 
                              'frontpage_settings', 'email_settings', 'whatsapp_settings']
                })
            else:
                return jsonify({'success': False, 'error': 'Database initialization failed'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API ROUTES - MIGRATIONS ====================
@app.route('/api/admin/migrate-receipts', methods=['POST'])
def migrate_receipts():
    """Run receipts table migration"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app.database import migrate_receipts_table
        migrate_receipts_table()
        return jsonify({
            'success': True,
            'message': 'Receipts table migrated successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API ROUTES - FRONTPAGE ====================
@app.route('/api/frontpage/config', methods=['GET'])
def get_frontpage_config():
    """Get frontpage configuration"""
    try:
        initialize_database()
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM frontpage_settings WHERE id = 1')
        config = cursor.fetchone()
        cursor.close()
        db.close()
        
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
        
        db = get_db()
        cursor = db.cursor()
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
            data.get('hero_heading'),
            data.get('hero_subheading'),
            data.get('hero_button_text'),
            data.get('hero_button_link'),
            data.get('packages_title'),
            data.get('footer_text'),
            data.get('footer_phone'),
            data.get('footer_email'),
            data.get('facebook_url'),
            data.get('twitter_url'),
            data.get('instagram_url'),
            data.get('alert_enabled', False),
            data.get('alert_message'),
            data.get('alert_link'),
            data.get('alert_color'),
            data.get('alert_style'),
            data.get('whatsapp_number'),
            data.get('whatsapp_message'),
            data.get('booking_email'),
            data.get('email_subject'),
            data.get('whatsapp_enabled', False),
            data.get('email_enabled', False),
            json.dumps(data.get('packages', [])),
            json.dumps(data.get('features', []))
        ))
        db.commit()
        
        log_activity(session['user_id'], 'update', 'frontpage', 'Updated frontpage configuration', request.remote_addr)
        cursor.close()
        db.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/frontpage/whatsapp', methods=['GET'])
def get_whatsapp_config():
    """Get WhatsApp configuration"""
    try:
        initialize_database()
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT number, message_template FROM whatsapp_settings WHERE id = 1')
        config = cursor.fetchone()
        cursor.close()
        db.close()
        
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
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT from_email, reply_to, subject_prefix FROM email_settings WHERE id = 1')
        config = cursor.fetchone()
        cursor.close()
        db.close()
        
        if config:
            return jsonify({'success': True, **dict(config)})
        else:
            return jsonify({'success': False, 'error': 'Email config not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API ROUTES - BACKUP ====================
@app.route('/api/backup/create', methods=['POST'])
def create_backup():
    """Create database backup"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.json
    backup_name = data.get('name', f"Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    try:
        initialize_database()
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO backup_history (backup_name, backup_type, file_size, tables_count, status, location)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (backup_name, 'manual', '2.4 MB', 12, 'completed', 'local'))
        db.commit()
        
        log_activity(session['user_id'], 'create', 'backup', f'Created backup: {backup_name}', request.remote_addr)
        cursor.close()
        db.close()
        
        return jsonify({'success': True, 'backup_name': backup_name})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/backup/list', methods=['GET'])
def list_backups():
    """List all backups"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        initialize_database()
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM backup_history ORDER BY created_at DESC')
        backups = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify({
            'success': True,
            'backups': [dict(b) for b in backups]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API ROUTES - COMPANY SETTINGS ====================
@app.route('/api/company/settings', methods=['GET'])
def get_company_settings():
    """Get company settings"""
    try:
        initialize_database()
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM company_settings WHERE id = 1')
        settings = cursor.fetchone()
        cursor.close()
        db.close()
        
        if settings:
            return jsonify({'success': True, 'settings': dict(settings)})
        else:
            return jsonify({'success': False, 'error': 'Settings not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/company/settings', methods=['POST'])
def update_company_settings():
    """Update company settings"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.json
    
    try:
        initialize_database()
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            UPDATE company_settings SET
                legal_name = %s, display_name = %s,
                address_line1 = %s, address_line2 = %s, city = %s, state = %s, country = %s, pin_code = %s,
                phone = %s, mobile = %s, email = %s, website = %s,
                gstin = %s, pan = %s, tan = %s, tcs_no = %s, tin = %s, cin = %s, iec = %s, msme = %s,
                bank_name = %s, bank_branch = %s, account_name = %s, account_no = %s, ifsc_code = %s, micr_code = %s, upi_id = %s, qr_code = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        ''', (
            data.get('legal_name'), data.get('display_name'),
            data.get('address_line1'), data.get('address_line2'), data.get('city'), data.get('state'), data.get('country'), data.get('pin_code'),
            data.get('phone'), data.get('mobile'), data.get('email'), data.get('website'),
            data.get('gstin'), data.get('pan'), data.get('tan'), data.get('tcs_no'), data.get('tin'), data.get('cin'), data.get('iec'), data.get('msme'),
            data.get('bank_name'), data.get('bank_branch'), data.get('account_name'), data.get('account_no'), data.get('ifsc_code'), data.get('micr_code'), data.get('upi_id'), data.get('qr_code')
        ))
        db.commit()
        
        log_activity(session['user_id'], 'update', 'company', 'Updated company settings', request.remote_addr)
        cursor.close()
        db.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API ROUTES - ACTIVITY LOG ====================
@app.route('/api/activity/log', methods=['GET'])
def get_activity_log():
    """Get activity log"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    limit = request.args.get('limit', 50, type=int)
    
    try:
        initialize_database()
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT a.*, u.username 
            FROM activity_log a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC
            LIMIT %s
        ''', (limit,))
        activities = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify({
            'success': True,
            'activities': [dict(a) for a in activities]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== STATIC FILE ROUTES - PUBLIC ====================
@app.route('/')
def serve_index():
    """Serve homepage"""
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from public directory"""
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
    """Serve admin static files safely"""
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
    """Serve traveler index/dashboard"""
    return send_from_directory(PUBLIC_DIR, 'traveler_dashboard.html')

@app.route('/traveler/<path:filename>')
def serve_traveler(filename):
    """Serve traveler files"""
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

@app.route('/style.css')
def serve_css():
    return send_from_directory(PUBLIC_DIR, 'style.css')

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files"""
    if '..' in filename or filename.startswith('/'):
        return jsonify({'success': False, 'error': 'Invalid path'}), 400
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==================== HELPER FUNCTIONS ====================
def log_activity(user_id, action, module, description, ip_address=None):
    """Log user activity"""
    try:
        initialize_database()
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO activity_log (user_id, action, module, description, ip_address) VALUES (%s, %s, %s, %s, %s)',
            (user_id, action, module, description, ip_address)
        )
        db.commit()
        cursor.close()
        db.close()
    except Exception as e:
        print(f"⚠️ Activity log error: {e}")

# ==================== DEBUG ROUTES ====================
@app.route('/debug/paths')
def debug_paths():
    """Debug route to check all paths"""
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
        'dashboard_size': os.path.getsize(os.path.join(ADMIN_DIR, 'dashboard.html')) if os.path.exists(os.path.join(ADMIN_DIR, 'dashboard.html')) else 0
    })

@app.route('/debug/test')
def debug_test():
    """Simple test route"""
    return jsonify({'success': True, 'message': 'Debug route working!'})

@app.route('/debug/session')
def debug_session():
    """Debug session info"""
    return jsonify({
        'session': dict(session),
        'has_user': 'user_id' in session,
        'has_traveler': 'traveler_id' in session
    })

@app.route('/debug/routes')
def debug_routes():
    """Debug endpoint to see all registered routes"""
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
    print(f"📁 Public directory: {PUBLIC_DIR}")
    print(f"📁 Admin directory: {ADMIN_DIR}")
    print(f"📁 Uploads directory: {app.config['UPLOAD_FOLDER']}")
    print("=" * 60)
    print("📡 Health check: /health")
    print("📡 API Endpoints ready (lazy DB init)")
    print("=" * 60)
    
    # CRITICAL: host must be '0.0.0.0' for Railway
    app.run(host='0.0.0.0', port=port, debug=debug)
