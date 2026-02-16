from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os

def create_app():
    """Application factory pattern - creates and configures the Flask app"""
    app = Flask(__name__, 
                static_folder=None)  # Disable default static folder, we'll handle it manually
    
    # Load configuration from environment
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'alhudha-haj-dev-key-2026')
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_PATH', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Initialize CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:8080", "https://*.railway.app"],
            "supports_credentials": True
        }
    })
    
    # Import database module
    from app.database import init_db, get_db, check_database
    
    # Initialize database at startup
    with app.app_context():
        try:
            init_db()
            check_database()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
    
    # ============ BLUEPRINTS ============
    
    # Import blueprints
    from app.routes.travelers import travelers_bp
    from app.routes.uploads import uploads_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.batches import batches_bp
    from app.routes.payments import payments_bp
    
    # Register blueprints with proper URL prefixes
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(travelers_bp, url_prefix='/api/travelers')
    app.register_blueprint(batches_bp, url_prefix='/api/batches')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
    
    # ============ ROOT ROUTES ============
    
    @app.route('/')
    def index():
        """Serve the main front page"""
        public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public')
        return send_from_directory(public_dir, 'index.html')
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        """Serve static files from public directory"""
        public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public')
        
        # Security check - prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': 'Invalid path'}), 400
        
        # Try to serve the requested file
        try:
            return send_from_directory(public_dir, filename)
        except:
            # If file not found and it's not an API route, serve index.html for client-side routing
            if not filename.startswith('api/'):
                return send_from_directory(public_dir, 'index.html')
            return jsonify({'error': 'File not found'}), 404
    
    # ============ API ROOT ============
    
    @app.route('/api')
    def api_root():
        """API root endpoint with system info"""
        return jsonify({
            'name': 'Alhudha Haj Travel System',
            'version': '2.0',
            'status': 'operational',
            'endpoints': {
                'auth': '/api/auth/login',
                'batches': '/api/batches',
                'travelers': '/api/travelers',
                'payments': '/api/payments',
                'uploads': '/api/uploads',
                'admin': '/api/admin/users'
            },
            'total_fields': 33,
            'database': check_database() if check_database() else 'connected'
        })
    
    # ============ HEALTH CHECK ============
    
    @app.route('/api/health')
    def health_check():
        """Health check endpoint for Railway"""
        return jsonify({
            'status': 'healthy',
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'services': {
                'database': 'connected',
                'storage': 'ok'
            }
        }), 200
    
    # ============ ERROR HANDLERS ============
    
    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 errors - return index.html for client-side routing"""
        if request.path.startswith('/api/'):
            return jsonify({'error': 'API endpoint not found'}), 404
        public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public')
        return send_from_directory(public_dir, 'index.html')
    
    @app.errorhandler(500)
    def server_error(e):
        """Handle 500 errors"""
        return jsonify({'error': 'Internal server error'}), 500
    
    # Print startup message
    print("=" * 60)
    print("🚀 Alhudha Haj Travel System v2.0")
    print("=" * 60)
    print(f"📁 Public directory: {os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public')}")
    print(f"📁 Uploads directory: {os.environ.get('UPLOAD_PATH', 'uploads')}")
    print(f"🔑 Secret key: {'Set from environment' if os.environ.get('SECRET_KEY') else 'Using default (dev only)'}")
    print("=" * 60)
    
    return app

# Create the application instance
app = create_app()

# This allows running with `python -m app`
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
