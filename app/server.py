from flask import Flask, send_from_directory, jsonify, request, session
from flask_cors import CORS
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import database
from app.database import get_db, init_db

# Import route blueprints
from app.routes import auth, admin, batches, travelers, payments, company, uploads

# Initialize Flask app
app = Flask(__name__, 
            static_folder='../public',
            static_url_path='')

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'alhudha-haj-secret-key-2026')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Enable CORS
CORS(app, supports_credentials=True)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
try:
    init_db()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"❌ Database initialization error: {e}")

# Register blueprints
app.register_blueprint(auth.bp)
app.register_blueprint(admin.bp)
app.register_blueprint(batches.bp)
app.register_blueprint(travelers.bp)
app.register_blueprint(payments.bp)
app.register_blueprint(company.bp)
app.register_blueprint(uploads.bp)

# ==================== STATIC FILE ROUTES ====================

@app.route('/')
def serve_index():
    return send_from_directory('../public', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../public', path)

@app.route('/admin/<path:path>')
def serve_admin(path):
    return send_from_directory('../public/admin', path)

@app.route('/traveler/dashboard')
def serve_traveler_dashboard():
    return send_from_directory('../public', 'traveler_dashboard.html')

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# ==================== HEALTH CHECK ====================
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

# ==================== PRINT INFO ====================
print("=" * 60)
print("🚀 Alhudha Haj Travel System v2.0")
print("=" * 60)
print(f"📁 Public directory: {os.path.abspath('../public')}")
print(f"📁 Uploads directory: {app.config['UPLOAD_FOLDER']}")
print(f"📁 Database: SQLite")
print("=" * 60)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # Set debug=False for production