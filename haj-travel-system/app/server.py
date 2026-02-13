from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from app.database import init_db
import os
import sys

app = Flask(__name__)
CORS(app)

# ============ FIXED PATHS FOR RAILWAY ============
# The public folder is at /app/public in Railway
PUBLIC_DIR = '/app/puplic'

print(f"📁 Looking for public folder at: {PUBLIC_DIR}")
print(f"📁 Does public folder exist? {os.path.exists(PUBLIC_DIR)}")

if os.path.exists(PUBLIC_DIR):
    print(f"📁 Files in public folder: {os.listdir(PUBLIC_DIR)}")
else:
    print(f"❌ PUBLIC FOLDER NOT FOUND! Current directory: {os.getcwd()}")
    print(f"❌ Files in /app: {os.listdir('/app') if os.path.exists('/app') else 'NO /app'}")

# ============ ROUTES ============

@app.route('/')
def serve_index():
    """Serve the main 33-field form"""
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/admin')
def serve_admin():
    """Serve the admin panel"""
    return send_from_directory(PUBLIC_DIR, 'admin.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve all static files (CSS, JS, images)"""
    return send_from_directory(PUBLIC_DIR, path)

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

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({"error": "Not found"}), 404

# ============ STARTUP ============

if __name__ == '__main__':
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

