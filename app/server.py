from flask import Flask, send_from_directory, jsonify, request, session, make_response, redirect, abort
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

# ====== LOGGING CONFIGURATION ======
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====== ENVIRONMENT CONFIGURATION ======
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import database
from app.database import get_db, init_db, release_db

# Import route blueprints
from app.routes import auth, admin, batches, travelers, payments, company, uploads, reports, invoices, receipts, users, backup

# ====== FLASK APP INITIALIZATION ======
app = Flask(__name__)

# ====== 🛡️ SECURITY HEADERS ======
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com unpkg.com; "
        "style-src 'self' 'unsafe-inline' fonts.googleapis.com cdnjs.cloudflare.com; "
        "font-src 'self' fonts.gstatic.com cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https:;"
    )
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

# Global flags to track database initialization
_db_initialized = False
_db_init_lock = threading.Lock()
_db_init_started = False

# ====== APP CONFIGURATION ======
# Use environment variable with strong fallback for development only
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if os.getenv('RAILWAY_ENVIRONMENT') == 'production':
        # In production, require SECRET_KEY to be set
        raise ValueError("SECRET_KEY environment variable must be set in production")
    else:
        # Development fallback - generate from system randomness
        import secrets
        SECRET_KEY = secrets.token_hex(32)
        print(f"⚠️ WARNING: Using generated development SECRET_KEY. Set SECRET_KEY in production!")

app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ====== 🔐 SESSION CONFIGURATION ======
app.config['SESSION_COOKIE_NAME'] = 'alhudha_session'
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_SECURE'] = True  # ✅ FIXED: Set to True for HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# ====== 📁 DIRECTORY PATHS ======
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
ADMIN_DIR = os.path.join(PUBLIC_DIR, 'admin')
TRAVELER_DIR = os.path.join(PUBLIC_DIR, 'traveler')

# Print directory information for debugging
print(f"📁 Base directory: {BASE_DIR}")
print(f"📁 Public directory: {PUBLIC_DIR}")
print(f"📁 Admin directory: {ADMIN_DIR}")
print(f"📁 Traveler directory: {TRAVELER_DIR}")
print(f"📁 Uploads directory: {app.config['UPLOAD_FOLDER']}")
print(f"📁 Public exists: {os.path.exists(PUBLIC_DIR)}")
print(f"📁 Admin exists: {os.path.exists(ADMIN_DIR)}")
print(f"📁 Traveler exists: {os.path.exists(TRAVELER_DIR)}")

# List files for debugging
if os.path.exists(PUBLIC_DIR):
    print(f"📄 Files in public: {os.listdir(PUBLIC_DIR)}")
if os.path.exists(ADMIN_DIR):
    print(f"📄 Files in admin: {os.listdir(ADMIN_DIR)}")

# ====== 🌐 CORS CONFIGURATION ======
CORS(
    app,
    supports_credentials=True,
    origins=[
        'https://alhudhahajportal.up.railway.app',
        'http://localhost:8080',
        '*'
    ],
    allow_headers=[
        'Content-Type',
        'Authorization',
        'X-Requested-With'
    ],
    expose_headers=[
        'Set-Cookie',
        'Content-Type'
    ]
)

# ====== 📂 UPLOAD DIRECTORIES ======
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'passports'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'aadhaar'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'pan'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'vaccine'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'photos'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'backups'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'company'), exist_ok=True)
    print("✅ Upload directories created successfully")
except Exception as e:
    print(f"❌ Error creating upload directories: {e}")

# ====== 🔷 BLUEPRINT REGISTRATION ======
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
app.register_blueprint(users.bp)
app.register_blueprint(backup.bp)

# ====== 📝 SESSION DEBUGGING MIDDLEWARE ======
@app.after_request
def after_request(response):
    """Log session info after each request for debugging"""
    try:
        if request.path.startswith('/api/'):
            print(f"📝 Session after {request.path}:")
            print(f"  - User ID: {session.get('user_id')}")
            print(f"  - Session keys: {list(session.keys())}")
            print(f"  - Session permanent: {session.permanent}")
            print(f"  - Cookie in response: {'Set-Cookie' in response.headers}")
            if 'Set-Cookie' in response.headers:
                print(f"  - Cookie value: {response.headers['Set-Cookie'][:50]}...")
    except Exception as e:
        print(f"⚠️ Error in after_request: {e}")
    return response

# ====== 🏠 STATIC FILE ROUTES ======
@app.route('/')
def serve_index():
    """Serve the main index page"""
    try:
        index_path = os.path.join(PUBLIC_DIR, 'index.html')
        if os.path.exists(index_path):
            print(f"✅ Serving index.html from {index_path}")
            return send_from_directory(PUBLIC_DIR, 'index.html')
        else:
            print(f"❌ index.html not found at {index_path}")
            return jsonify({'success': False, 'error': 'Index page not found'}), 404
    except Exception as e:
        print(f"❌ Error serving index.html: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ====== 🔐 LOGIN PAGE ROUTES ======
@app.route('/admin.login.html')
def serve_admin_login_correct():
    """Serve admin login page"""
    try:
        login_path = os.path.join(PUBLIC_DIR, 'admin.login.html')
        if os.path.exists(login_path):
            return send_from_directory(PUBLIC_DIR, 'admin.login.html')
        return jsonify({'success': False, 'error': 'Login file not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/login.html')
@app.route('/admin/login')
def redirect_admin_login():
    """Redirect incorrect admin login URLs"""
    return redirect('/admin.login.html')

# ====== 📊 ADMIN STATIC ROUTES ======
@app.route('/admin/')
@app.route('/admin')
def serve_admin_index():
    """Serve admin dashboard"""
    try:
        dashboard_path = os.path.join(ADMIN_DIR, 'dashboard.html')
        if os.path.exists(dashboard_path):
            return send_from_directory(ADMIN_DIR, 'dashboard.html')
        return jsonify({'success': False, 'error': 'Dashboard not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/<path:filename>')
def serve_admin(filename):
    """Serve admin panel files"""
    try:
        if '..' in filename or filename.startswith('/'):
            return jsonify({'success': False, 'error': 'Invalid path'}), 400

        file_path = os.path.join(ADMIN_DIR, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(ADMIN_DIR, filename)

        if '.' not in filename:
            html_file = filename + '.html'
            html_path = os.path.join(ADMIN_DIR, html_file)
            if os.path.exists(html_path) and os.path.isfile(html_path):
                return send_from_directory(ADMIN_DIR, html_file)

        return jsonify({'success': False, 'error': 'Admin file not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ====== 👤 TRAVELER ROUTES ======
@app.route('/traveler/')
@app.route('/traveler')
def serve_traveler_index():
    """Serve traveler dashboard"""
    try:
        traveler_dashboard = os.path.join(PUBLIC_DIR, 'traveler_dashboard.html')
        if os.path.exists(traveler_dashboard):
            return send_from_directory(PUBLIC_DIR, 'traveler_dashboard.html')
        return jsonify({'success': False, 'error': 'Traveler dashboard not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/traveler/<path:filename>')
def serve_traveler(filename):
    """Serve traveler files"""
    try:
        if '..' in filename or filename.startswith('/'):
            return jsonify({'success': False, 'error': 'Invalid path'}), 400

        file_path = os.path.join(PUBLIC_DIR, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(PUBLIC_DIR, filename)

        html_path = os.path.join(PUBLIC_DIR, filename + '.html')
        if os.path.exists(html_path) and os.path.isfile(html_path):
            return send_from_directory(PUBLIC_DIR, filename + '.html')

        return jsonify({'success': False, 'error': 'Traveler file not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ====== 🚪 TRAVELER LOGIN ROUTES ======
@app.route('/traveler_login.html')
@app.route('/traveler/login')
def serve_traveler_login():
    """Serve traveler login page"""
    try:
        login_path = os.path.join(PUBLIC_DIR, 'traveler_login.html')
        if os.path.exists(login_path):
            return send_from_directory(PUBLIC_DIR, 'traveler_login.html')
        return jsonify({'success': False, 'error': 'Traveler login page not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ====== 📄 FRONTPAGE ROUTES ======
@app.route('/frontpage.html')
@app.route('/admin/frontpage.html')
def serve_frontpage():
    """Serve frontpage editor"""
    try:
        frontpage_path = os.path.join(ADMIN_DIR, 'frontpage.html')
        if os.path.exists(frontpage_path):
            return send_from_directory(ADMIN_DIR, 'frontpage.html')
        return jsonify({'success': False, 'error': 'Frontpage editor not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ====== 🎨 CSS ROUTES ======
@app.route('/style.css')
def serve_css():
    """Serve main CSS file"""
    try:
        css_path = os.path.join(PUBLIC_DIR, 'style.css')
        if os.path.exists(css_path):
            return send_from_directory(PUBLIC_DIR, 'style.css')
        return jsonify({'success': False, 'error': 'CSS file not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/admin-style.css')
def serve_admin_css():
    """Serve admin CSS file"""
    try:
        css_path = os.path.join(ADMIN_DIR, 'admin-style.css')
        if os.path.exists(css_path):
            return send_from_directory(ADMIN_DIR, 'admin-style.css')
        return jsonify({'success': False, 'error': 'Admin CSS file not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ====== 📜 JAVASCRIPT ROUTES ======
@app.route('/admin/js/<path:filename>')
def serve_admin_js(filename):
    """Serve admin JavaScript files"""
    try:
        js_dir = os.path.join(ADMIN_DIR, 'js')
        js_path = os.path.join(js_dir, filename)
        if os.path.exists(js_path) and os.path.isfile(js_path):
            return send_from_directory(js_dir, filename)
        return jsonify({'success': False, 'error': 'JS file not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ====== 📁 IMPROVED UPLOAD ROUTES ======
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files from any upload subdirectory"""
    try:
        if '..' in filename or filename.startswith('/'):
            return jsonify({'success': False, 'error': 'Invalid path'}), 400
        
        # List of all possible upload subdirectories
        upload_subdirs = ['passports', 'aadhaar', 'pan', 'vaccine', 'photos', 'documents', 'company', 'backups']
        
        # Try to find the file in any subdirectory
        for subdir in upload_subdirs:
            folder_path = os.path.join(app.config['UPLOAD_FOLDER'], subdir)
            file_path = os.path.join(folder_path, filename)
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                print(f"✅ Serving upload from {subdir}: {filename}")
                return send_file_upload(file_path, filename)
        
        # If not found in subdirectories, try the main upload folder
        main_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(main_path) and os.path.isfile(main_path):
            print(f"✅ Serving upload from main folder: {filename}")
            return send_file_upload(main_path, filename)
        
        # File not found
        print(f"❌ Upload file not found: {filename}")
        return jsonify({'success': False, 'error': 'File not found'}), 404
        
    except Exception as e:
        print(f"❌ Error serving upload {filename}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/uploads/<path:subdir>/<path:filename>')
def serve_upload_with_subdir(subdir, filename):
    """Serve uploaded files with explicit subdirectory"""
    try:
        if '..' in filename or '..' in subdir or filename.startswith('/') or subdir.startswith('/'):
            return jsonify({'success': False, 'error': 'Invalid path'}), 400
        
        # Validate subdir is allowed
        allowed_subdirs = ['passports', 'aadhaar', 'pan', 'vaccine', 'photos', 'documents', 'company', 'backups']
        if subdir not in allowed_subdirs:
            print(f"⚠️ Invalid subdirectory requested: {subdir}")
            return jsonify({'success': False, 'error': 'Invalid subdirectory'}), 400
        
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], subdir)
        file_path = os.path.join(folder_path, filename)
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            print(f"✅ Serving upload from {subdir}: {filename}")
            return send_file_upload(file_path, filename)
        else:
            print(f"❌ Upload file not found: {subdir}/{filename}")
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
    except Exception as e:
        print(f"❌ Error serving upload {subdir}/{filename}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Helper function to send file with proper mimetype
def send_file_upload(file_path, filename):
    """Send file with proper headers"""
    from flask import send_file
    import mimetypes
    
    # Get proper mimetype
    mimetype, encoding = mimetypes.guess_type(filename)
    if not mimetype:
        if filename.endswith('.pdf'):
            mimetype = 'application/pdf'
        elif filename.endswith(('.jpg', '.jpeg')):
            mimetype = 'image/jpeg'
        elif filename.endswith('.png'):
            mimetype = 'image/png'
        else:
            mimetype = 'application/octet-stream'
    
    return send_file(file_path, mimetype=mimetype, as_attachment=False, download_name=filename)

# Legacy upload routes for backward compatibility
@app.route('/uploads/company/<path:filename>')
def serve_company_upload(filename):
    """Serve company uploaded files (legacy)"""
    return serve_upload_with_subdir('company', filename)

@app.route('/uploads/passports/<path:filename>')
def serve_passport_upload(filename):
    """Serve passport files"""
    return serve_upload_with_subdir('passports', filename)

@app.route('/uploads/photos/<path:filename>')
def serve_photo_upload(filename):
    """Serve photo files"""
    return serve_upload_with_subdir('photos', filename)

@app.route('/uploads/aadhaar/<path:filename>')
def serve_aadhaar_upload(filename):
    """Serve aadhaar files"""
    return serve_upload_with_subdir('aadhaar', filename)

@app.route('/uploads/pan/<path:filename>')
def serve_pan_upload(filename):
    """Serve pan files"""
    return serve_upload_with_subdir('pan', filename)

@app.route('/uploads/vaccine/<path:filename>')
def serve_vaccine_upload(filename):
    """Serve vaccine files"""
    return serve_upload_with_subdir('vaccine', filename)

# ====== 🌍 CATCH-ALL STATIC ROUTE ======
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from public directory"""
    try:
        if '..' in filename or filename.startswith('/'):
            return jsonify({'success': False, 'error': 'Invalid path'}), 400

        file_path = os.path.join(PUBLIC_DIR, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(PUBLIC_DIR, filename)

        html_path = os.path.join(PUBLIC_DIR, filename + '.html')
        if os.path.exists(html_path) and os.path.isfile(html_path):
            return send_from_directory(PUBLIC_DIR, filename + '.html')

        return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        print(f"❌ Error serving static file {filename}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ====== 🏥 API HEALTH ENDPOINTS ======
@app.route('/api/health')
@app.route('/health')
def api_health():
    """API health check"""
    return jsonify({
        'success': True,
        'message': 'Alhudha Haj Travel API',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api')
def api_root():
    """API root information"""
    return jsonify({
        'success': True,
        'message': 'Alhudha Haj Travel API',
        'version': '2.0',
        'endpoints': [
            '/api/health',
            '/api/login',
            '/api/logout',
            '/api/check-session',
            '/api/admin/*',
            '/api/travelers/*',
            '/api/batches/*',
            '/api/payments/*'
        ],
        'timestamp': datetime.now().isoformat()
    }), 200

# ====== 💾 BACKGROUND DATABASE INITIALIZATION ======
def initialize_database():
    """Start database initialization in a background thread (non-blocking)."""
    global _db_initialized, _db_init_started

    with _db_init_lock:
        if _db_initialized or _db_init_started:
            return True
        _db_init_started = True

    print("🚀 Starting background database initialization...")

    def init_thread_func():
        global _db_initialized
        try:
            with app.app_context():
                init_db()
            print("✅ Database initialized successfully")
            with _db_init_lock:
                _db_initialized = True
        except Exception as e:
            print(f"❌ DB init error: {e}")

    init_thread = threading.Thread(target=init_thread_func, daemon=True)
    init_thread.start()
    return True

# Pre-initialize the database in the background
if os.getenv('DATABASE_URL'):
    initialize_database()

@app.before_request
def before_request():
    """Handle tasks before each request"""
    try:
        # Skip database init for static files and health checks
        if request.path in ['/', '/health', '/api/health', '/api', '/debug/paths', '/debug/test', '/style.css']:
            return
        if request.path.startswith('/uploads/'):
            return
        if request.path.startswith('/admin/js/'):
            return

        if not _db_initialized:
            initialize_database()

        # Refresh session if user is logged in
        if session.get('user_id'):
            session.modified = True
    except Exception as e:
        print(f"⚠️ Error in before_request: {e}")

# ====== 🐛 DEBUG ROUTES ======
@app.route('/debug/paths')
def debug_paths():
    """Debug endpoint to check file paths"""
    try:
        files_in_public = []
        files_in_admin = []
        files_in_admin_js = []
        upload_files = {}

        if os.path.exists(PUBLIC_DIR):
            files_in_public = os.listdir(PUBLIC_DIR)

        if os.path.exists(ADMIN_DIR):
            files_in_admin = os.listdir(ADMIN_DIR)

        js_dir = os.path.join(ADMIN_DIR, 'js')
        if os.path.exists(js_dir):
            files_in_admin_js = os.listdir(js_dir)

        # Check upload directories
        upload_subdirs = ['passports', 'aadhaar', 'pan', 'vaccine', 'photos', 'documents', 'company', 'backups']
        for subdir in upload_subdirs:
            folder = os.path.join(app.config['UPLOAD_FOLDER'], subdir)
            if os.path.exists(folder):
                upload_files[subdir] = os.listdir(folder)[:10]  # First 10 files
            else:
                upload_files[subdir] = []

        return jsonify({
            'base_dir': BASE_DIR,
            'public_dir': PUBLIC_DIR,
            'admin_dir': ADMIN_DIR,
            'upload_dir': app.config['UPLOAD_FOLDER'],
            'public_exists': os.path.exists(PUBLIC_DIR),
            'admin_exists': os.path.exists(ADMIN_DIR),
            'upload_exists': os.path.exists(app.config['UPLOAD_FOLDER']),
            'files_in_public': files_in_public,
            'files_in_admin': files_in_admin,
            'files_in_admin_js': files_in_admin_js,
            'upload_files': upload_files,
            'index_exists': os.path.exists(os.path.join(PUBLIC_DIR, 'index.html')),
            'login_page_exists': os.path.exists(os.path.join(PUBLIC_DIR, 'admin.login.html')),
            'dashboard_exists': os.path.exists(os.path.join(ADMIN_DIR, 'dashboard.html')),
            'session_manager_exists': os.path.exists(os.path.join(ADMIN_DIR, 'js', 'session-manager.js'))
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/debug/test')
def debug_test():
    return jsonify({'success': True, 'message': 'Debug route working!'})

@app.route('/debug/session')
def debug_session():
    try:
        return jsonify({
            'session': dict(session),
            'has_user': 'user_id' in session,
            'has_traveler': 'traveler_id' in session,
            'session_permanent': session.permanent,
            'cookie_in_request': request.cookies.get(app.config['SESSION_COOKIE_NAME']) is not None,
            'cookie_value': request.cookies.get(app.config['SESSION_COOKIE_NAME']),
            'session_expiry': (datetime.now() + app.config['PERMANENT_SESSION_LIFETIME']).isoformat() if session.permanent else None
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/debug/session-test')
def session_test():
    """Test if session is persisting"""
    try:
        return jsonify({
            'has_session': bool(session),
            'session_keys': list(session.keys()),
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'cookie_in_request': request.cookies.get(app.config['SESSION_COOKIE_NAME']) is not None,
            'cookie_name': app.config['SESSION_COOKIE_NAME']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/debug/routes')
def debug_routes():
    """List all registered routes"""
    try:
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'path': str(rule)
            })
        return jsonify(routes)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ====== ❌ ERROR HANDLERS ======
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    try:
        path = request.path
        if not path.startswith('/api/') and not path.startswith('/uploads/'):
            html_path = os.path.join(PUBLIC_DIR, path.lstrip('/') + '.html')
            if os.path.exists(html_path):
                return send_from_directory(PUBLIC_DIR, path.lstrip('/') + '.html')
        return jsonify({'success': False, 'error': 'Resource not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 internal server errors"""
    print(f"❌ Internal server error: {error}")
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# ====== 🔧 HELPER FUNCTIONS ======
def log_admin_action(user_id, action, description):
    """Log admin actions to database"""
    try:
        conn, cursor = get_db()
        try:
        cursor.execute("""
            INSERT INTO activity_log (user_id, action, module, description, ip_address, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, action, 'frontpage', description, request.remote_addr, datetime.now()))
        conn.commit()
        cursor.close()
        conn.close()
    finally:
        release_db(conn, cursor)
    except Exception as e:
        print(f"⚠️ Failed to log admin action: {e}")

def check_required_files():
    """Check if required files exist"""
    required_files = [
        os.path.join(PUBLIC_DIR, 'index.html'),
        os.path.join(PUBLIC_DIR, 'admin.login.html'),
        os.path.join(ADMIN_DIR, 'dashboard.html'),
    ]
    all_exist = True
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Required file missing: {file_path}")
            all_exist = False
    return all_exist

# ====== 🚀 APPLICATION ENTRY POINT ======
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    print("=" * 60)
    print("🚀 Alhudha Haj Travel System v2.0")
    print("=" * 60)
    print(f"📁 Server starting on port {port}")
    print(f"📁 Debug mode: {debug}")
    print(f"📁 Binding to: 0.0.0.0:{port}")
    print(f"📁 Session timeout: 30 minutes")
    print(f"📁 Session cookie name: {app.config['SESSION_COOKIE_NAME']}")
    print("=" * 60)
    print("🌐 ROOT URL: / → serves index.html")
    print("📡 API Health: /api/health")
    print("📡 API Info: /api")
    print("📡 Admin Login: /admin.login.html")
    print("📡 Admin Dashboard: /admin/")
    print("📡 Traveler Login: /traveler_login.html")
    print("📁 Upload URLs: /uploads/passports/filename.jpg, /uploads/photos/filename.jpg, etc.")
    print("=" * 60)

    try:
        app.run(host='0.0.0.0', port=port, debug=debug)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
