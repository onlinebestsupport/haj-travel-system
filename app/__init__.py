from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import os
import datetime

def create_app():
    """Application factory pattern - creates and configures the Flask app"""
    app = Flask(__name__, static_folder=None)
    
    # Load configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'alhudha-haj-dev-key-2026')
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_PATH', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    
    # Initialize CORS
    CORS(app, resources={r"/api/*": {"origins": "*", "supports_credentials": True}})
    
    # Create required directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    public_dir = os.path.join(base_dir, 'public')
    upload_dir = os.path.join(base_dir, 'uploads')
    backup_dir = os.path.join(base_dir, 'backups')
    
    os.makedirs(public_dir, exist_ok=True)
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(backup_dir, exist_ok=True)
    
    # Import and initialize database LATER (not at top level)
    def init_db_if_needed():
        try:
            from app.database import init_db, check_database
            init_db()
            check_database()
            print("✅ Database initialized")
        except Exception as e:
            print(f"⚠️ Database init skipped: {e}")
    
    # Run DB init in a try block
    try:
        init_db_if_needed()
    except:
        print("⚠️ Will initialize database on first request")
    
    # ============ BLUEPRINTS ============
    
    # Import blueprints inside function to avoid circular imports
    from app.routes.travelers import travelers_bp
    from app.routes.uploads import uploads_bp
    
    # Register blueprints
    app.register_blueprint(travelers_bp, url_prefix='/api/travelers')
    app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
    
    # ============ ROOT ROUTES ============
    
    @app.route('/')
    def index():
        """Serve the main front page"""
        return send_from_directory(public_dir, 'index.html')
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        """Serve static files"""
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': 'Invalid path'}), 400
        try:
            return send_from_directory(public_dir, filename)
        except:
            if not filename.startswith('api/'):
                return send_from_directory(public_dir, 'index.html')
            return jsonify({'error': 'File not found'}), 404
    
    @app.route('/api')
    def api_root():
        return jsonify({
            'name': 'Alhudha Haj Travel System',
            'version': '2.0',
            'status': 'operational',
            'total_fields': 33
        })
    
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.datetime.now().isoformat()
        }), 200
    
    # ============ ERROR HANDLERS ============
    
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'API endpoint not found'}), 404
        return send_from_directory(public_dir, 'index.html')
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error'}), 500
    
    print("=" * 60)
    print("🚀 Alhudha Haj Travel System v2.0")
    print("=" * 60)
    print(f"📁 Public: {public_dir}")
    print(f"📁 Uploads: {upload_dir}")
    print("=" * 60)
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
