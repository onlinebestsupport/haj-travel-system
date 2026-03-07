from flask import Flask, send_from_directory, jsonify, request, session, make_response, redirect
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

# ==================== LOGGING CONFIGURATION ====================
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

# ==================== 🛡️ SECURITY HEADERS ====================
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


# Global flag to track database initialization
_db_initialized = False
_db_init_lock = threading.Lock()

# ==================== APP CONFIGURATION ====================
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'alhudha-haj-secret-key-2026')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ==================== 🔐 SESSION CONFIGURATION ====================
app.config['SESSION_COOKIE_NAME'] = 'alhudha_session'
app.config['SESSION_COOKIE_DOMAIN'] = None  # Allow all domains
app.config['SESSION_COOKIE_PATH'] = '/'  # Cookie valid for entire site
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True only with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Changed from 'Strict' to 'Lax'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # 30 minutes default
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_COOKIE_PERSISTENT'] = True  # Keep cookie after browser close

# ==================== 📁 DIRECTORY PATHS ====================
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

# ==================== 🌐 CORS CONFIGURATION ====================
# ==================== CORS CONFIGURATION ====================
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

# ==================== 📂 UPLOAD DIRECTORIES ====================
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

# ==================== 🔷 BLUEPRINT REGISTRATION ====================
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

# ==================== 📝 SESSION DEBUGGING MIDDLEWARE ====================
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

# ==================== 🏠 STATIC FILE ROUTES ====================
# These routes MUST come before API routes

@app.route('/')
def serve_index():
    """Serve the main index page - THIS IS THE ROOT URL"""
    try:
        index_path = os.path.join(PUBLIC_DIR, 'index.html')
        if os.path.exists(index_path):
            print(f"✅ Serving index.html from {index_path}")
            return send_from_directory(PUBLIC_DIR, 'index.html')
        else:
            print(f"❌ index.html not found at {index_path}")
            print(f"📁 Files in {PUBLIC_DIR}: {os.listdir(PUBLIC_DIR) if os.path.exists(PUBLIC_DIR) else 'Directory does not exist'}")
            return jsonify({'success': False, 'error': 'Index page not found'}), 404
    except Exception as e:
        print(f"❌ Error serving index.html: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 🔐 LOGIN PAGE ROUTES (FIXED) ====================
@app.route('/admin.login.html')
def serve_admin_login_correct():
    """Serve admin login page from public directory - CORRECT URL"""
    try:
        login_path = os.path.join(PUBLIC_DIR, 'admin.login.html')
        print(f"🔍 Serving login from: {login_path}")
        if os.path.exists(login_path):
            return send_from_directory(PUBLIC_DIR, 'admin.login.html')
        else:
            return jsonify({'success': False, 'error': 'Login file not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/login.html')
@app.route('/admin/login')
def redirect_admin_login():
    """Redirect incorrect admin login URLs to correct one"""
    print(f"🔄 Redirecting {request.path} to /admin.login.html")
    return redirect('/admin.login.html')

# ==================== 📊 ADMIN STATIC ROUTES ====================
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
    """Serve admin panel files from admin directory"""
    try:
        # Security check
        if '..' in filename or filename.startswith('/'):
            return jsonify({'success': False, 'error': 'Invalid path'}), 400

        # Try exact file match
        file_path = os.path.join(ADMIN_DIR, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(ADMIN_DIR, filename)

        # Try with .html extension
        if '.' not in filename:
            html_file = filename + '.html'
            html_path = os.path.join(ADMIN_DIR, html_file)
            if os.path.exists(html_path) and os.path.isfile(html_path):
                return send_from_directory(ADMIN_DIR, html_file)

        return jsonify({'success': False, 'error': 'Admin file not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 👤 TRAVELER ROUTES ====================
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
        # Security check
        if '..' in filename or filename.startswith('/'):
            return jsonify({'success': False, 'error': 'Invalid path'}), 400
        
        # Try exact file match
        file_path = os.path.join(PUBLIC_DIR, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(PUBLIC_DIR, filename)
        
        # Try with .html extension
        html_path = os.path.join(PUBLIC_DIR, filename + '.html')
        if os.path.exists(html_path) and os.path.isfile(html_path):
            return send_from_directory(PUBLIC_DIR, filename + '.html')
        
        return jsonify({'success': False, 'error': 'Traveler file not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 🚪 TRAVELER LOGIN ROUTES ====================
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

# ==================== 📄 FRONTPAGE ROUTES ====================
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

# ==================== 🎨 CSS ROUTES ====================
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
# ==================== 📜 JAVASCRIPT ROUTES ====================
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

# ==================== 📁 UPLOAD ROUTES ====================
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files"""
    try:
        if '..' in filename or filename.startswith('/'):
            return jsonify({'success': False, 'error': 'Invalid path'}), 400
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/uploads/company/<path:filename>')
def serve_company_upload(filename):
    """Serve company uploaded files"""
    try:
        if '..' in filename or filename.startswith('/'):
            return jsonify({'success': False, 'error': 'Invalid path'}), 400
        company_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'company')
        return send_from_directory(company_folder, filename)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 🌍 CATCH-ALL STATIC ROUTE ====================
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from public directory (catch-all)"""
    try:
        # Security check
        if '..' in filename or filename.startswith('/'):
            return jsonify({'success': False, 'error': 'Invalid path'}), 400
        
        # Try exact file match
        file_path = os.path.join(PUBLIC_DIR, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(PUBLIC_DIR, filename)
        
        # Try with .html extension
        html_path = os.path.join(PUBLIC_DIR, filename + '.html')
        if os.path.exists(html_path) and os.path.isfile(html_path):
            return send_from_directory(PUBLIC_DIR, filename + '.html')
        
        return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        print(f"❌ Error serving static file {filename}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 🏥 API HEALTH ENDPOINTS ====================
@app.route('/api/health')
@app.route('/health')
def api_health():
    """API health check - accessible at /api/health or /health"""
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

# ==================== 💾 LAZY DATABASE INITIALIZATION ====================
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

# ==================== 🐛 DEBUG ROUTES ====================
@app.route('/debug/paths')
def debug_paths():
    """Debug endpoint to check file paths"""
    try:
        files_in_public = []
        files_in_admin = []
        files_in_admin_js = []
        
        if os.path.exists(PUBLIC_DIR):
            files_in_public = os.listdir(PUBLIC_DIR)
        
        if os.path.exists(ADMIN_DIR):
            files_in_admin = os.listdir(ADMIN_DIR)
        
        js_dir = os.path.join(ADMIN_DIR, 'js')
        if os.path.exists(js_dir):
            files_in_admin_js = os.listdir(js_dir)
        
        return jsonify({
            'base_dir': BASE_DIR,
            'public_dir': PUBLIC_DIR,
            'admin_dir': ADMIN_DIR,
            'public_exists': os.path.exists(PUBLIC_DIR),
            'admin_exists': os.path.exists(ADMIN_DIR),
            'files_in_public': files_in_public,
            'files_in_admin': files_in_admin,
            'files_in_admin_js': files_in_admin_js,
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

# ==================== ❌ ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors - try to serve HTML file if possible"""
    try:
        path = request.path
        if not path.startswith('/api/') and not path.startswith('/uploads/'):
            # Try to serve HTML file
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

# ==================== 🔧 HELPER FUNCTIONS ====================
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

# ==================== 🚀 APPLICATION ENTRY POINT ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Check required files before starting
    files_ok = check_required_files()
    
    print("=" * 60)
    print("🚀 Alhudha Haj Travel System v2.0")
    print("=" * 60)
    print(f"📁 Server starting on port {port}")
    print(f"📁 Debug mode: {debug}")
    print(f"📁 Binding to: 0.0.0.0:{port}")
    print(f"📁 Session timeout: 30 minutes (7 days with remember me)")
    print(f"📁 Session cookie name: {app.config['SESSION_COOKIE_NAME']}")
    print("=" * 60)
    print("🌐 ROOT URL: / → serves index.html")
    print("📡 API Health: /api/health")
    print("📡 API Info: /api")
    print("📡 Debug paths: /debug/paths")
    print("📡 Debug session: /debug/session")
    print("📡 Session test: /debug/session-test")
    print("📡 Admin Login (correct): /admin.login.html")
    print("📡 Admin Login (redirect): /admin/login.html → /admin.login.html")
    print("📡 Admin Dashboard: /admin/")
    print("📡 Traveler Login: /traveler_login.html")
    print("📡 Frontpage Editor: /admin/frontpage.html")
    print("=" * 60)
    
    try:
        app.run(host='0.0.0.0', port=port, debug=debug)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
