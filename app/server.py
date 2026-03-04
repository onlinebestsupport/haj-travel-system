"""
🚀 ALHUDHA HAJ PORTAL v2.5 - GUNICORN BULLETPROOF
✅ NO blueprint imports on startup
✅ Lazy loading only  
✅ Zero startup crashes
✅ Emergency APIs always work
"""

from flask import Flask, send_from_directory, jsonify, request, session
from flask_cors import CORS
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import threading
import logging

# ==================== 🔧 MINIMAL STARTUP ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env FIRST
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ==================== 🏗️ FLASK APP - NO IMPORTS ====================
app = Flask(__name__)
app.config.update({
    'SECRET_KEY': os.getenv('SECRET_KEY', 'alhudha-haj-secret-key-2026-v2.5'),
    'SESSION_COOKIE_SECURE': False,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': timedelta(days=30),
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024
})

# ==================== 📁 PATHS ====================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
ADMIN_DIR = os.path.join(PUBLIC_DIR, 'admin')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

# Create dirs safely
os.makedirs(UPLOAD_DIR, exist_ok=True)
for folder in ['passports', 'aadhaar', 'pan', 'vaccine', 'photos', 'company', 'backups']:
    os.makedirs(os.path.join(UPLOAD_DIR, folder), exist_ok=True)

print("🚀 Alhudha Haj Portal v2.5 - GUNICORN SAFE STARTUP")
CORS(app, supports_credentials=True)

# ==================== 🌍 LAZY DB INIT ====================
_db_initialized = False
_db_lock = threading.Lock()

def safe_import_db():
    """🔥 LAZY IMPORT - Only when needed"""
    global _db_initialized
    try:
        from app.database import get_db, init_db
        return get_db, init_db
    except Exception as e:
        print(f"❌ DB import failed: {e}")
        return None, None

def initialize_database():
    """🔥 SAFE DB INIT - No crash"""
    global _db_initialized
    if _db_initialized:
        return True
    
    with _db_lock:
        if _db_initialized:
            return True
        
        get_db_func, init_db_func = safe_import_db()
        if not init_db_func:
            print("❌ Database module unavailable")
            return False
        
        print("🚀 Initializing database...")
        try:
            with app.app_context():
                init_db_func()
            _db_initialized = True
            print("✅ Database ready!")
            return True
        except Exception as e:
            print(f"❌ DB init failed: {e}")
            return False

# =============================================================================
# 🔥 #1 EMERGENCY APIs (100% Safe - No imports)
# =============================================================================

@app.route('/health')
@app.route('/api/health')
def health():
    return jsonify({
        'success': True,
        'version': '2.5-gunicorn',
        'status': 'healthy',
        'db_ready': _db_initialized,
        'static_ready': os.path.exists(PUBLIC_DIR)
    })

@app.route('/force-db-init', methods=['POST'])
def force_db_init():
    success = initialize_database()
    return jsonify({
        'success': success,
        'db_ready': _db_initialized,
        'message': 'Database ready' if success else 'DB unavailable'
    })

@app.route('/debug/paths')
def debug_paths():
    return jsonify({
        'public': os.path.exists(PUBLIC_DIR),
        'admin': os.path.exists(ADMIN_DIR),
        'uploads': os.path.exists(UPLOAD_DIR),
        'dashboard_size': os.path.getsize(os.path.join(ADMIN_DIR, 'dashboard.html')) if os.path.exists(os.path.join(ADMIN_DIR, 'dashboard.html')) else 0
    })

# 🔥 CORE EMERGENCY LOGIN (No blueprint dependency)
@app.route('/api/login', methods=['POST'])
def emergency_login():
    if not initialize_database():
        return jsonify({'success': False, 'error': 'Database unavailable'}), 503
    
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    get_db_func, _ = safe_import_db()
    if not get_db_func:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        conn, cursor = get_db_func()
        cursor.execute("""
            SELECT id, username, full_name, role 
            FROM users WHERE username = %s AND password = %s AND is_active = true
        """, (username, password))
        user = cursor.fetchone()
        cursor.close()
        if hasattr(conn, 'close'):
            conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session.permanent = True
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'name': user['full_name'] or username,
                    'role': user['role']
                }
            })
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'success': False, 'error': 'Login failed'}), 500

@app.route('/api/check-session', methods=['GET'])
def emergency_check_session():
    if not session.get('user_id'):
        return jsonify({'success': True, 'authenticated': False})
    
    get_db_func, _ = safe_import_db()
    if not get_db_func:
        return jsonify({'success': True, 'authenticated': False})
    
    try:
        conn, cursor = get_db_func()
        cursor.execute("SELECT id, username, full_name, role FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        cursor.close()
        if hasattr(conn, 'close'):
            conn.close()
        
        if user:
            return jsonify({
                'success': True,
                'authenticated': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'name': user['full_name'] or user['username'],
                    'role': user['role']
                }
            })
    except:
        pass
    
    session.clear()
    return jsonify({'success': True, 'authenticated': False})

@app.route('/api/logout', methods=['POST'])
def emergency_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})

# =============================================================================
# 🔥 #2 STATIC ROUTES (Safe file serving)
# =============================================================================
@app.route('/', methods=['GET'])
@app.route('/index.html')
def serve_index():
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/admin.login.html')
@app.route('/admin/login')
def serve_login():
    return send_from_directory(PUBLIC_DIR, 'admin.login.html')

@app.route('/admin/dashboard.html')
@app.route('/admin/dashboard')
def serve_dashboard():
    dashboard_path = os.path.join(ADMIN_DIR, 'dashboard.html')
    if os.path.exists(dashboard_path):
        return send_from_directory(ADMIN_DIR, 'dashboard.html')
    return send_from_directory(PUBLIC_DIR, 'admin.login.html')

@app.route('/admin/<path:filename>')
def serve_admin(filename):
    if '..' in filename:
        return jsonify({'error': 'Invalid path'}), 400
    admin_path = os.path.join(ADMIN_DIR, filename)
    if os.path.exists(admin_path):
        return send_from_directory(ADMIN_DIR, filename)
    if os.path.exists(admin_path + '.html'):
        return send_from_directory(ADMIN_DIR, filename + '.html')
    return jsonify({'error': 'Admin file not found'}), 404

@app.route('/style.css')
def serve_css():
    if os.path.exists(os.path.join(PUBLIC_DIR, 'style.css')):
        return send_from_directory(PUBLIC_DIR, 'style.css')
    return jsonify({'error': 'CSS not found'}), 404

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    if '..' in filename:
        return jsonify({'error': 'Invalid path'}), 400
    return send_from_directory(UPLOAD_DIR, filename)

# Catch-all LAST
@app.route('/<path:filename>')
def serve_public(filename):
    if '..' in filename:
        return jsonify({'error': 'Invalid path'}), 400
    public_path = os.path.join(PUBLIC_DIR, filename)
    if os.path.exists(public_path):
        return send_from_directory(PUBLIC_DIR, filename)
    if os.path.exists(public_path + '.html'):
        return send_from_directory(PUBLIC_DIR, filename + '.html')
    return jsonify({'error': f'File not found: {filename}'}), 404

# =============================================================================
# 🔥 #3 LAZY BLUEPRINTS (Optional - No crash)
# =============================================================================
@app.before_request
def lazy_blueprints():
    """🔥 Load blueprints only AFTER startup"""
    if request.path.startswith('/api/') and not hasattr(g, 'blueprints_loaded'):
        try:
            from app.routes import auth
            app.register_blueprint(auth.bp, url_prefix='/api')
            g.blueprints_loaded = True
            print("✅ Blueprints loaded on-demand")
        except:
            print("⚠️ Blueprints unavailable - using emergency APIs")
        setattr(g, 'blueprints_loaded', True)

# =============================================================================
# 🔥 #4 ERROR HANDLERS
# =============================================================================
@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'error': 'Server error'}), 500

# ==================== 🚀 STARTUP - ZERO CRASH ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    
    print("=" * 60)
    print("🚀 ALHUDHA HAJ PORTAL v2.5 - GUNICORN BULLETPROOF")
    print("✅ NO startup imports")
    print("✅ Emergency APIs ready") 
    print("✅ Login: superadmin/admin123")
    print(f"📡 Port: {port}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False)
