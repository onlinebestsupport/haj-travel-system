from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory pattern - creates and configures the Flask app"""
    app = Flask(__name__, static_folder=None)
    
    # Load configuration from environment
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'alhudha-haj-dev-key-2026')
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_PATH', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Initialize CORS with proper settings
    CORS(app, resources={
        r"/api/*": {
            "origins": ["*"],
            "supports_credentials": True,
            "allow_headers": ["Content-Type", "Authorization"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        }
    })
    
    # Get paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(BASE_DIR)
    PUBLIC_DIR = os.path.join(ROOT_DIR, "public")
    UPLOAD_DIR = os.path.join(ROOT_DIR, "uploads")
    BACKUP_DIR = os.path.join(ROOT_DIR, "backups")
    
    # Create directories if they don't exist
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    logger.info(f"📁 Public folder: {PUBLIC_DIR}")
    logger.info(f"📁 Uploads folder: {UPLOAD_DIR}")
    
    # Add after-request handler for CORS
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    # Handle OPTIONS requests for CORS preflight
    @app.route('/api/<path:path>', methods=['OPTIONS'])
    def handle_options(path):
        return '', 200
    
    # ============ SIMPLE HEALTH CHECK (ALWAYS WORKS) ============
    @app.route('/api/health')
    def health_check():
        """Health check endpoint for Railway - must always return 200"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }), 200
    
    # ============ ROOT ROUTE ============
    @app.route('/')
    def serve_index():
        """Serve the main front page"""
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
    """Serve admin login page"""
    return send_from_directory(PUBLIC_DIR, 'admin.login.html')

@app.route('/admin/dashboard')
@login_required
def serve_admin_dashboard():
    """Serve admin dashboard"""
    return send_from_directory(PUBLIC_DIR, 'admin_dashboard.html')
    # ============ STATIC FILES ============
    @app.route('/<path:filename>')
    def serve_static(filename):
        """Serve static files from public directory"""
        # Security check - prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': 'Invalid path'}), 400
        
        # Try to serve the requested file
        try:
            return send_from_directory(PUBLIC_DIR, filename)
        except Exception as e:
            logger.warning(f"File not found: {filename}")
            # If file not found and it's not an API route, serve index.html for client-side routing
            if not filename.startswith('api/'):
                try:
                    return send_from_directory(PUBLIC_DIR, 'index.html')
                except:
                    pass
            return jsonify({'error': 'File not found'}), 404
    
    # ============ API ROOT ============
    @app.route('/api')
    def api_root():
        """API root endpoint with system info"""
        return jsonify({
            'name': 'Alhudha Haj Travel System',
            'version': '2.0',
            'status': 'operational',
            'endpoints': [
                '/api/health',
                '/api/travelers',
                '/api/uploads',
                '/api/batches',
                '/api/payments',
                '/api/company/profile'
            ],
            'total_fields': 33
        })
    
    # ============ BLUEPRINT REGISTRATION ============
    
    # Travelers blueprint
    try:
        from app.routes.travelers import travelers_bp
        app.register_blueprint(travelers_bp, url_prefix='/api/travelers')
        logger.info("✅ Travelers blueprint registered")
    except Exception as e:
        logger.error(f"❌ Failed to register travelers blueprint: {e}")
        @app.route('/api/travelers')
        def travelers_fallback():
            return jsonify({'success': True, 'travelers': []})
    
    # Uploads blueprint
    try:
        from app.routes.uploads import uploads_bp
        app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
        logger.info("✅ Uploads blueprint registered")
    except Exception as e:
        logger.error(f"❌ Failed to register uploads blueprint: {e}")
        @app.route('/api/uploads')
        def uploads_fallback():
            return jsonify({'success': True, 'message': 'Uploads API temporarily unavailable'})
    
    # Batches blueprint
    try:
        from app.routes.batches import batches_bp
        app.register_blueprint(batches_bp, url_prefix='/api/batches')
        logger.info("✅ Batches blueprint registered")
    except Exception as e:
        logger.error(f"❌ Failed to register batches blueprint: {e}")
        @app.route('/api/batches')
        def batches_fallback():
            return jsonify({'success': True, 'batches': []})
    
    # Payments blueprint
    try:
        from app.routes.payments import payments_bp
        app.register_blueprint(payments_bp, url_prefix='/api/payments')
        logger.info("✅ Payments blueprint registered")
    except Exception as e:
        logger.error(f"❌ Failed to register payments blueprint: {e}")
        @app.route('/api/payments')
        def payments_fallback():
            return jsonify({'success': True, 'payments': []})
    
    # Company blueprint
    try:
        from app.routes.company import company_bp
        app.register_blueprint(company_bp, url_prefix='/api/company')
        logger.info("✅ Company blueprint registered")
    except Exception as e:
        logger.error(f"❌ Failed to register company blueprint: {e}")
        @app.route('/api/company/profile')
        def company_fallback():
            return jsonify({
                'success': True,
                'name': 'Alhudha Haj Travel',
                'tagline': 'Your Trusted Partner',
                'badge': 'Est. 1998',
                'features': []
            })
    
    # Auth blueprint (optional)
    try:
        from app.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        logger.info("✅ Auth blueprint registered")
    except ImportError:
        logger.warning("⚠️ Auth blueprint not found")
    except Exception as e:
        logger.error(f"❌ Failed to register auth blueprint: {e}")
    
    # Admin blueprint (optional)
    try:
        from app.routes.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
        logger.info("✅ Admin blueprint registered")
    except ImportError:
        logger.warning("⚠️ Admin blueprint not found")
    except Exception as e:
        logger.error(f"❌ Failed to register admin blueprint: {e}")
    
    # ============ DATABASE INITIALIZATION (LAZY) ============
    def init_database():
        """Initialize database in background thread"""
        try:
            from app.database import init_db
            result = init_db()
            if result:
                logger.info("✅ Database initialized successfully")
            else:
                logger.warning("⚠️ Database initialization returned False")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
    
    # Run database init in background thread (doesn't block startup)
    import threading
    threading.Thread(target=init_database, daemon=True).start()
    
    # ============ ERROR HANDLERS ============
    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 errors"""
        if request.path.startswith('/api/'):
            return jsonify({'error': 'API endpoint not found'}), 404
        try:
            return send_from_directory(PUBLIC_DIR, 'index.html')
        except:
            return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        """Handle 500 errors"""
        logger.error(f"Server error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    
    # ============ STARTUP MESSAGE ============
    logger.info("=" * 60)
    logger.info("🚀 Alhudha Haj Travel System v2.0")
    logger.info("=" * 60)
    logger.info(f"📁 Public directory: {PUBLIC_DIR}")
    logger.info(f"📁 Uploads directory: {UPLOAD_DIR}")
    logger.info(f"🔑 Secret key: {'Set from environment' if os.environ.get('SECRET_KEY') else 'Using default (dev only)'}")
    logger.info("=" * 60)
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
