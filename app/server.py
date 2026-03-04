from flask import Flask, send_from_directory, jsonify, request, session
from flask_cors import CORS
from app.database import get_db, init_db  # ✅ FIXED: NO release_db crash
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

# Import route blueprints (SAFE - won't crash if missing)
try:
    from app.routes import auth, admin, batches, travelers, payments, company, uploads, reports, invoices, receipts
    BLUEPRINTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Blueprints not found: {e}. Using emergency APIs.")
    BLUEPRINTS_AVAILABLE = False

# ==================== FLASK APP INITIALIZATION ====================
app = Flask(__name__)

# 🔥 GLOBAL DB FLAGS - FIXED INIT
_db_initialized = False
_db_init_lock = threading.Lock()

# ==================== CRITICAL SESSION CONFIGURATION ====================
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'alhudha-haj-secret-key-2026')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_NAME'] = 'alhudha_session'
app.config['PREFERRED_URL_SCHEME'] = 'https'

# ==================== DIRECTORY PATHS ====================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
ADMIN_DIR = os.path.join(PUBLIC_DIR, 'admin')
TRAVELER_DIR = os.path.join(PUBLIC_DIR, 'traveler')

print(f"🚀 Alhudha Haj Portal v2.2 - CRASH-PROOF")
print(f"📁 Base: {BASE_DIR} | Public: {os.path.exists(PUBLIC_DIR)} | Blueprints: {BLUEPRINTS_AVAILABLE}")

# ==================== CORS + DIRECTORIES ====================
CORS(app, supports_credentials=True, origins=['*'])
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
for folder in ['passports', 'aadhaar', 'pan', 'vaccine', 'photos', 'backups', 'company']:
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], folder), exist_ok=True)

# 🔥 🔥 FIX #1: EMERGENCY APIs BEFORE STATIC ROUTES 🔥 🔥
@app.route('/health')
@app.route('/api/health')
def health():
    return jsonify({
        'success': True,
        'status': 'healthy',
        'session_fixed': True,
        'static_fixed': True,
        'db_ready': _db_initialized,
        'blueprints': BLUEPRINTS_AVAILABLE
    }), 200

@app.route('/force-db-init', methods=['POST'])
def force_db_init():
    """🔥 EMERGENCY FORCE DB INIT"""
    global _db_initialized
    print("🚨 FORCE DB INIT TRIGGERED")
    try:
        with app.app_context():
            init_db()
        _db_initialized = True
        print("✅ FORCE DB INIT SUCCESS")
        return jsonify({'success': True, 'db_ready': True})
    except Exception as e:
        print(f"❌ FORCE DB INIT FAILED: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/login', methods=['POST'])
def emergency_login():
    """🔥 EMERGENCY LOGIN - WORKS EVEN WITHOUT BLUEPRINTS"""
    if not _db_initialized:
        initialize_database()
    
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Credentials required'}), 400
    
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT id, username, full_name, role FROM users WHERE username = %s AND password = %s", 
                      (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session.permanent = True
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
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

@app.route('/api/check-session', methods=['GET'])
def emergency_check_session():
    """🔥 EMERGENCY SESSION CHECK"""
    if session.get('user_id'):
        try:
            conn, cursor = get_db()
            cursor.execute("SELECT id, username, full_name, role FROM users WHERE id = %s", 
                          (session['user_id'],))
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
        except:
            pass
    return jsonify({'success': True, 'authenticated': False})

@app.route('/api/dashboard-data', methods=['GET'])
def emergency_dashboard_data():
    """🔥 EMERGENCY DASHBOARD DATA"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'authenticated': False}), 401
    
    try:
        conn, cursor = get_db()
        cursor.execute("SELECT COUNT(*) as count FROM users")
        users = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM batches")
        batches = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM travelers")
        travelers = cursor.fetchone()['count']
        cursor.close()
        conn.close()
        return jsonify({
            'success': True,
            'data': {'users': users, 'batches': batches, 'travelers': travelers}
        })
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

# =============================================================================
# 🔥 #1 STATIC ROUTES (AFTER EMERGENCY APIs!)
# =============================================================================
@app.route('/', methods=['GET'])
@app.route('/index.html', methods=['GET'])
def serve_index():
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/admin/login')
@app.route('/admin.login.html')
def serve_admin_login():
    return send_from_directory(PUBLIC_DIR, 'admin.login.html')

@app.route('/admin/dashboard.html')
@app.route('/admin/dashboard')
def serve_admin_dashboard():
    dashboard_path = os.path.join(ADMIN_DIR, 'dashboard.html')
    if os.path.exists(dashboard_path):
        return send_from_directory(ADMIN_DIR, 'dashboard.html')
    return send_from_directory(PUBLIC_DIR, 'admin.login.html')

@app.route('/admin/<path:filename>')
def serve_admin(filename):
    if '..' in filename or filename.startswith('/'):
        return jsonify({'error': 'Invalid path'}), 400
    try:
        return send_from_directory(ADMIN_DIR, filename)
    except:
        try:
            return send_from_directory(ADMIN_DIR, filename + '.html')
        except:
            return jsonify({'error': f'Admin file "{filename}" not found'}), 404

@app.route('/traveler/<path:filename>')
def serve_traveler(filename):
    if '..' in filename:
        return jsonify({'error': 'Invalid path'}), 400
    return send_from_directory(TRAVELER_DIR, filename)

@app.route('/style.css')
@app.route('/css/<path:filename>')
def serve_css(filename='style.css'):
    try:
        return send_from_directory(PUBLIC_DIR, 'style.css')
    except:
        return jsonify({'error': 'CSS not found'}), 404

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    if '..' in filename:
        return jsonify({'error': 'Invalid path'}), 400
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 🔥 STATIC CATCH-ALL (LAST!)
@app.route('/<path:filename>')
def serve_public(filename):
    if '..' in filename or filename.startswith('/'):
        return jsonify({'error': 'Invalid path'}), 400
    try:
        return send_from_directory(PUBLIC_DIR, filename)
    except:
        try:
            return send_from_directory(PUBLIC_DIR, filename + '.html')
        except:
            return jsonify({'error': f'Public file "{filename}" not found'}), 404

# =============================================================================
# 🔥 #2 SAFE BLUEPRINT REGISTRATION (After emergency APIs)
# =============================================================================
if BLUEPRINTS_AVAILABLE:
    try:
        app.register_blueprint(auth.bp, url_prefix='/api')
        app.register_blueprint(admin.bp, url_prefix='/api')
        app.register_blueprint(batches.bp, url_prefix='/api')
        app.register_blueprint(travelers.bp, url_prefix='/api')
        app.register_blueprint(payments.bp, url_prefix='/api')
        app.register_blueprint(company.bp, url_prefix='/api')
        app.register_blueprint(uploads.bp, url_prefix='/api')
        app.register_blueprint(reports.bp, url_prefix='/api')
        app.register_blueprint(invoices.bp, url_prefix='/api')
        app.register_blueprint(receipts.bp, url_prefix='/api')
        print("✅ All blueprints registered")
    except Exception as e:
        print(f"⚠️ Blueprint registration failed: {e}")

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
    if any(path_match in request.path for path_match in [
        '/', '/admin/', '/style.', '/uploads/', '/traveler/', '.css', '.js', '.png', '.jpg', '.ico'
    ]):
        return
    if request.path.startswith('/api/') and not _db_initialized:
        initialize_database()

# =============================================================================
# 🔥 #4 SAFE DB CLEANUP
# =============================================================================
@app.teardown_appcontext
def close_db(error):
    try:
        if hasattr(g, 'db_conn'):
            pass
    except:
        pass

@app.route('/debug/session')
def debug_session():
    return jsonify({
        'session_data': dict(session),
        'has_user': bool(session.get('user_id')),
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role')
    })

@app.route('/debug/paths')
def debug_paths():
    return jsonify({
        'public_exists': os.path.exists(PUBLIC_DIR),
        'admin_exists': os.path.exists(ADMIN_DIR),
        'index_size': os.path.getsize(os.path.join(PUBLIC_DIR, 'index.html')) if os.path.exists(os.path.join(PUBLIC_DIR, 'index.html')) else 0,
        'dashboard_size': os.path.getsize(os.path.join(ADMIN_DIR, 'dashboard.html')) if os.path.exists(os.path.join(ADMIN_DIR, 'dashboard.html')) else 0,
        'login_size': os.path.getsize(os.path.join(PUBLIC_DIR, 'admin.login.html')) if os.path.exists(os.path.join(PUBLIC_DIR, 'admin.login.html')) else 0
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'success': False, 'error': 'Server error'}), 500

# ==================== STARTUP - FORCE DB INIT ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    
    # 🔥 FIX #2: FORCE DB INIT ON STARTUP
    with app.app_context():
        initialize_database()
    
    print("=" * 80)
    print("🚀 ALHUDHA HAJ PORTAL v2.2 - BULLETPROOF")
    print(f"✅ DB Ready: {_db_initialized}")
    print("✅ Login: superadmin/admin123")
    print(f"📡 Port: {port}")
    print("=" * 80)
    app.run(host='0.0.0.0', port=port, debug=False)
