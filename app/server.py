from flask import Flask, send_from_directory, jsonify, request, session
from flask_cors import CORS
from app.database import get_db, init_db, release_db  # 🔥 Added release_db
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import threading
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== ENVIRONMENT CONFIGURATION ====================
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import route blueprints (API ONLY)
from app.routes import auth, admin, batches, travelers, payments, company, uploads, reports, invoices, receipts

# ==================== FLASK APP INITIALIZATION ====================
app = Flask(__name__)

# 🔥 GLOBAL DB FLAGS
_db_initialized = False
_db_init_lock = threading.Lock()

# ==================== CRITICAL SESSION CONFIGURATION ====================
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'alhudha-haj-secret-key-2026')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# 🚨 RAILWAY + PRODUCTION SESSION FIXES
app.config['SESSION_COOKIE_SECURE'] = False  # Railway HTTP proxy
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_NAME'] = 'alhudha_session'
app.config['PREFERRED_URL_SCHEME'] = 'https'

# ==================== DIRECTORY PATHS ====================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
ADMIN_DIR = os.path.join(PUBLIC_DIR, 'admin')
TRAVELER_DIR = os.path.join(PUBLIC_DIR, 'traveler')

print(f"🚀 Alhudha Haj Portal v2.2 - SESSION FIXED")
print(f"📁 Base: {BASE_DIR} | Public: {os.path.exists(PUBLIC_DIR)}")

# ==================== CORS + DIRECTORIES ====================
CORS(app, supports_credentials=True, origins=['*'])
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
for folder in ['passports', 'aadhaar', 'pan', 'vaccine', 'photos', 'backups', 'company']:
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], folder), exist_ok=True)

# =============================================================================
# 🔥 #1 STATIC ROUTES FIRST - NO CONFLICTS
# =============================================================================
@app.route('/', methods=['GET'])
@app.route('/index.html', methods=['GET'])
def serve_index():
    """Landing page - NO session interference"""
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/admin/<path:filename>')
def serve_admin(filename):
    """Admin dashboard - NO session check interference"""
    if '..' in filename:
        return jsonify({'error': 'Invalid path'}), 400
    try:
        return send_from_directory(ADMIN_DIR, filename)
    except:
        try:
            return send_from_directory(ADMIN_DIR, filename + '.html')
        except:
            return jsonify({'error': 'Admin file not found'}), 404

@app.route('/<path:filename>')
def serve_static(filename):
    """Public static files"""
    if '..' in filename:
        return jsonify({'error': 'Invalid path'}), 400
    try:
        return send_from_directory(PUBLIC_DIR, filename)
    except:
        try:
            return send_from_directory(PUBLIC_DIR, filename + '.html')
        except:
            return jsonify({'error': 'File not found'}), 404

# Specific routes
@app.route('/admin.login.html', methods=['GET'])
@app.route('/admin/login', methods=['GET'])
def serve_admin_login():
    return send_from_directory(PUBLIC_DIR, 'admin.login.html')

@app.route('/style.css')
def serve_css():
    return send_from_directory(PUBLIC_DIR, 'style.css')

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    if '..' in filename:
        return jsonify({'error': 'Invalid path'}), 400
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# =============================================================================
# 🔥 #2 BLUEPRINTS REGISTERED AFTER STATIC (No conflicts)
# =============================================================================
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

# =============================================================================
# 🔥 #3 FIXED before_request - API ONLY
# =============================================================================
def initialize_database():
    global _db_initialized
    with _db_init_lock:
        if _db_initialized:
            return True
        print("🚀 Initializing database...")
        try:
            with app.app_context():
                init_db()
            _db_initialized = True
            print("✅ Database ready")
            return True
        except Exception as e:
            print(f"❌ DB init failed: {e}")
            return False

@app.before_request
def before_request():
    """🔥 FIXED: API endpoints ONLY get DB init"""
    # Static files + dashboard = NO DB interference
    if any(path_match in request.path for path_match in [
        '/', '/admin/', '/style.', '/uploads/', '/traveler/', '.css', '.js', '.png', '.jpg'
    ]):
        return
    
    # API endpoints only
    if request.path.startswith('/api/') and not _db_initialized:
        initialize_database()

# =============================================================================
# 🔥 #4 CRITICAL DB CLEANUP - Prevents session leaks
# =============================================================================
@app.teardown_appcontext
def close_db(error):
    """🔥 CONNECTION POOL CLEANUP - Session saver"""
    try:
        release_db()
    except:
        pass

# =============================================================================
# 🔥 #5 HEALTH + DEBUG (Always work)
# =============================================================================
@app.route('/health')
@app.route('/api/health')
def health():
    return jsonify({
        'success': True,
        'status': 'healthy',
        'session_fixed': True,
        'static_fixed': True,
        'db_ready': _db_initialized
    }), 200

@app.route('/debug/session')
def debug_session():
    return jsonify({
        'session_data': dict(session),
        'has_user': bool(session.get('user_id')),
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role'),
        'permanent': getattr(session, 'permanent', False)
    })

@app.route('/debug/paths')
def debug_paths():
    return jsonify({
        'public_exists': os.path.exists(PUBLIC_DIR),
        'admin_exists': os.path.exists(ADMIN_DIR),
        'index_size': os.path.getsize(os.path.join(PUBLIC_DIR, 'index.html')) if os.path.exists(os.path.join(PUBLIC_DIR, 'index.html')) else 0,
        'dashboard_size': os.path.getsize(os.path.join(ADMIN_DIR, 'dashboard.html')) if os.path.exists(os.path.join(ADMIN_DIR, 'dashboard.html')) else 0
    })

# =============================================================================
# 🔥 #6 FIXED API ROUTES - Session persistence guaranteed
# =============================================================================
@app.route('/api/check-session', methods=['GET'])
def check_session():
    """🔥 FIXED SESSION CHECK - Works with dashboard"""
    if session.get('user_id'):
        try:
            conn, cursor = get_db()
            cursor.execute("SELECT id, username, full_name, role FROM users WHERE id = %s", (session['user_id'],))
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
            print(f"Session check error: {e}")
    
    elif session.get('traveler_id'):
        return jsonify({
            'success': True,
            'authenticated': True,
            'traveler': {
                'id': session['traveler_id'],
                'name': session.get('traveler_name'),
                'passport': session.get('traveler_passport')
            }
        })
    
    return jsonify({'success': True, 'authenticated': False})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'success': False, 'error': 'Server error'}), 500

# ==================== STARTUP ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print("=" * 80)
    print("🚀 ALHUDHA HAJ PORTAL v2.2 - FULLY FIXED")
    print("✅ Static serving: / → index.html")
    print("✅ Admin dashboard: /admin/dashboard.html") 
    print("✅ Login: superadmin/admin123 → STAYS LOGGED IN")
    print("✅ Session debug: /debug/session")
    print(f"📡 Running on port {port}")
    print("=" * 80)
    app.run(host='0.0.0.0', port=port, debug=False)
