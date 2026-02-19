from flask import Flask, send_from_directory, jsonify, request, redirect, session
from flask_cors import CORS
import os
import logging
from datetime import datetime
from functools import wraps
import hashlib
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_password_hash(password):
    salt = "alhudha-salt-2026"
    hash_obj = hashlib.sha256((password + salt).encode())
    return base64.b64encode(hash_obj.digest()).decode()

def check_password_hash(stored_hash, password):
    return generate_password_hash(password) == stored_hash

def get_db():
    from app.database import get_db as db_get
    return db_get()

def create_app():
    app = Flask(__name__, static_folder=None)
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'alhudha-haj-dev-key-2026')
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_PATH', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    CORS(app, resources={
        r"/api/*": {
            "origins": ["*"],
            "supports_credentials": True,
            "allow_headers": ["Content-Type", "Authorization"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        }
    })
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(BASE_DIR)
    PUBLIC_DIR = os.path.join(ROOT_DIR, "public")
    UPLOAD_DIR = os.path.join(ROOT_DIR, "uploads")
    BACKUP_DIR = os.path.join(ROOT_DIR, "backups")
    
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    logger.info(f"📁 Public folder: {PUBLIC_DIR}")
    logger.info(f"📁 Uploads folder: {UPLOAD_DIR}")
    
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    @app.route('/api/<path:path>', methods=['OPTIONS'])
    def handle_options(path):
        return '', 200
    
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }), 200
    
    @app.route('/')
    def serve_index():
        try:
            return send_from_directory(PUBLIC_DIR, 'index.html')
        except Exception as e:
            logger.error(f"Error serving index: {e}")
            return jsonify({
                'name': 'Alhudha Haj Travel System',
                'status': 'running',
                'message': 'Frontend files not found but API is working'
            })
    
    @app.route('/admin.login.html')
    def serve_admin_login():
        return send_from_directory(PUBLIC_DIR, 'admin.login.html')
    
    @app.route('/admin.html')
    def redirect_admin_to_login():
        return redirect('/admin.login.html', 301)
    
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('admin_logged_in'):
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/admin/dashboard')
    @login_required
    def redirect_old_dashboard():
        return redirect('/admin/index.html', 301)
    
    @app.route('/admin/')
    @app.route('/admin/index.html')
    @login_required
    def serve_admin_index():
        try:
            return send_from_directory(os.path.join(PUBLIC_DIR, 'admin'), 'index.html')
        except Exception as e:
            logger.error(f"Error serving admin index: {e}")
            return jsonify({'error': 'Admin dashboard not found'}), 404
    
    @app.route('/admin/<path:filename>')
    @login_required
    def serve_admin_files(filename):
        try:
            return send_from_directory(os.path.join(PUBLIC_DIR, 'admin'), filename)
        except Exception as e:
            logger.error(f"Error serving admin file {filename}: {e}")
            return jsonify({'error': 'File not found'}), 404
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': 'Invalid path'}), 400
        
        try:
            return send_from_directory(PUBLIC_DIR, filename)
        except Exception as e:
            logger.warning(f"File not found: {filename}")
            if not filename.startswith('api/'):
                try:
                    return send_from_directory(PUBLIC_DIR, 'index.html')
                except:
                    pass
            return jsonify({'error': 'File not found'}), 404
    
    @app.route('/api')
    def api_root():
        return jsonify({
            'name': 'Alhudha Haj Travel System',
            'version': '2.0',
            'status': 'operational',
            'endpoints': [
                '/api/health',
                '/api/login',
                '/api/travelers',
                '/api/uploads',
                '/api/batches',
                '/api/payments',
                '/api/company/profile',
                '/api/admin/users'
            ],
            'total_fields': 33
        })
    
    @app.route('/api/login', methods=['POST'])
    def api_login():
        try:
            data = request.json
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({'success': False, 'message': 'Username and password required'}), 400
            
            conn = get_db()
            if not conn:
                logger.error("Database connection failed")
                return jsonify({'success': False, 'message': 'Database not available'}), 503
            
            cur = conn.cursor()
            cur.execute("""
                SELECT id, username, password_hash, full_name, is_active 
                FROM admin_users 
                WHERE username = %s AND is_active = true
            """, (username,))
            
            user = cur.fetchone()
            cur.close()
            conn.close()
            
            if user and check_password_hash(user[2], password):
                session['admin_logged_in'] = True
                session['admin_user_id'] = user[0]
                session['admin_username'] = user[1]
                session['admin_name'] = user[3] or user[1]
                
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'redirect': '/admin/index.html',
                    'user': {
                        'id': user[0],
                        'name': user[3] or user[1],
                        'username': user[1],
                        'roles': ['admin']
                    }
                })
            else:
                logger.warning(f"Failed login attempt for username: {username}")
                return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return jsonify({'success': False, 'message': 'Server error'}), 500
    
    # Blueprint registrations
    try:
        from app.routes.travelers import travelers_bp
        app.register_blueprint(travelers_bp, url_prefix='/api/travelers')
        logger.info("✅ Travelers blueprint registered")
    except Exception as e:
        logger.error(f"❌ Failed to register travelers blueprint: {e}")
    
    try:
        from app.routes.uploads import uploads_bp
        app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
        logger.info("✅ Uploads blueprint registered")
    except Exception as e:
        logger.error(f"❌ Failed to register uploads blueprint: {e}")
    
    try:
        from app.routes.batches import batches_bp
        app.register_blueprint(batches_bp, url_prefix='/api/batches')
        logger.info("✅ Batches blueprint registered")
    except Exception as e:
        logger.error(f"❌ Failed to register batches blueprint: {e}")
    
    try:
        from app.routes.payments import payments_bp
        app.register_blueprint(payments_bp, url_prefix='/api/payments')
        logger.info("✅ Payments blueprint registered")
    except Exception as e:
        logger.error(f"❌ Failed to register payments blueprint: {e}")
    
    try:
        from app.routes.company import company_bp
        app.register_blueprint(company_bp, url_prefix='/api/company')
        logger.info("✅ Company blueprint registered")
    except Exception as e:
        logger.error(f"❌ Failed to register company blueprint: {e}")
    
    try:
        from app.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        logger.info("✅ Auth blueprint registered")
    except Exception as e:
        logger.error(f"❌ Failed to register auth blueprint: {e}")
    
    try:
        from app.routes.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
        logger.info("✅ Admin blueprint registered")
    except Exception as e:
        logger.error(f"❌ Failed to register admin blueprint: {e}")
    
    def init_database():
        try:
            from app.database import init_db
            result = init_db()
            if result:
                logger.info("✅ Database initialized successfully")
            else:
                logger.warning("⚠️ Database initialization returned False")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
    
    import threading
    threading.Thread(target=init_database, daemon=True).start()
    
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'API endpoint not found'}), 404
        try:
            return send_from_directory(PUBLIC_DIR, 'index.html')
        except:
            return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    
    logger.info("=" * 60)
    logger.info("🚀 Alhudha Haj Travel System v2.0")
    logger.info("=" * 60)
    logger.info(f"📁 Public directory: {PUBLIC_DIR}")
    logger.info(f"📁 Uploads directory: {UPLOAD_DIR}")
    logger.info(f"📁 Admin directory: {os.path.join(PUBLIC_DIR, 'admin')}")
    logger.info("=" * 60)
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
