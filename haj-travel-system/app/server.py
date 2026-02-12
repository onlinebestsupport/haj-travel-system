from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from app.database import init_db
import os

app = Flask(__name__, 
            static_folder='../public',
            template_folder='../public')
CORS(app)

# ============ ROUTES FOR HTML PAGES ============

@app.route('/')
def serve_index():
    """Serve the main 33-field form"""
    return send_from_directory('../public', 'index.html')

@app.route('/admin')
def serve_admin():
    """Serve the admin panel"""
    return send_from_directory('../public', 'admin.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve all static files (CSS, JS, images)"""
    return send_from_directory('../public', path)

# ============ API ROUTES ============

@app.route('/api')
def api():
    """API status endpoint"""
    return jsonify({
        "name": "Haj Travel System",
        "status": "active",
        "fields": 33,
        "message": "API is working!"
    })

@app.route('/api/health')
def health():
    """Healthcheck endpoint for Railway"""
    return jsonify({"status": "healthy"}), 200

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return jsonify({"error": "Server error"}), 500

# ============ STARTUP ============

if __name__ == '__main__':
    # Initialize database
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    # Get port from environment
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Starting server on port {port}")
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=False)
