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
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'alhudha-haj-secret-key-2026')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
ADMIN_DIR = os.path.join(PUBLIC_DIR, 'admin')

print(f"📁 Base directory: {BASE_DIR}")
print(f"📁 Public directory: {PUBLIC_DIR}")
print(f"📁 Admin directory: {ADMIN_DIR}")
print(f"📁 Uploads directory: {app.config['UPLOAD_FOLDER']}")

# Check if directories exist
print(f"📁 Public exists: {os.path.exists(PUBLIC_DIR)}")
print(f"📁 Admin exists: {os.path.exists(ADMIN_DIR)}")

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
    """Serve homepage"""
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from public directory"""
    try:
        return send_from_directory(PUBLIC_DIR, filename)
    except:
        return jsonify({'success': False, 'error': 'File not found'}), 404

@app.route('/admin/<path:filename>')
def serve_admin(filename):
    """Serve admin files - handles both with and without .html"""
    try:
        # Try with the filename as-is
        return send_from_directory(ADMIN_DIR, filename)
    except:
        try:
            # Try adding .html extension
            return send_from_directory(ADMIN_DIR, filename + '.html')
        except:
            return jsonify({'success': False, 'error': 'Admin file not found'}), 404

# Specific routes for admin pages (for better reliability)
@app.route('/admin/dashboard')
@app.route('/admin/dashboard.html')
def serve_admin_dashboard():
    return send_from_directory(ADMIN_DIR, 'dashboard.html')

@app.route('/admin/batches')
@app.route('/admin/batches.html')
def serve_admin_batches():
    return send_from_directory(ADMIN_DIR, 'batches.html')

@app.route('/admin/travelers')
@app.route('/admin/travelers.html')
def serve_admin_travelers():
    return send_from_directory(ADMIN_DIR, 'travelers.html')

@app.route('/admin/payments')
@app.route('/admin/payments.html')
def serve_admin_payments():
    return send_from_directory(ADMIN_DIR, 'payments.html')

@app.route('/admin/users')
@app.route('/admin/users.html')
def serve_admin_users():
    return send_from_directory(ADMIN_DIR, 'users.html')

@app.route('/admin/reports')
@app.route('/admin/reports.html')
def serve_admin_reports():
    return send_from_directory(ADMIN_DIR, 'reports.html')

@app.route('/admin/invoices')
@app.route('/admin/invoices.html')
def serve_admin_invoices():
    return send_from_directory(ADMIN_DIR, 'invoices.html')

@app.route('/admin/receipts')
@app.route('/admin/receipts.html')
def serve_admin_receipts():
    return send_from_directory(ADMIN_DIR, 'receipts.html')

@app.route('/admin/backup')
@app.route('/admin/backup.html')
def serve_admin_backup():
    return send_from_directory(ADMIN_DIR, 'backup.html')

@app.route('/admin/whatsapp')
@app.route('/admin/whatsapp.html')
def serve_admin_whatsapp():
    return send_from_directory(ADMIN_DIR, 'whatsapp.html')

@app.route('/admin/email')
@app.route('/admin/email.html')
def serve_admin_email():
    return send_from_directory(ADMIN_DIR, 'email.html')

@app.route('/admin/frontpage')
@app.route('/admin/frontpage.html')
def serve_admin_frontpage():
    return send_from_directory(ADMIN_DIR, 'frontpage.html')

@app.route('/admin/index')
@app.route('/admin/index.html')
def serve_admin_index():
    return send_from_directory(ADMIN_DIR, 'index.html')

@app.route('/admin/style.css')
def serve_admin_css():
    return send_from_directory(ADMIN_DIR, 'style.css')

@app.route('/traveler/dashboard')
def serve_traveler_dashboard():
    return send_from_directory(PUBLIC_DIR, 'traveler_dashboard.html')

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==================== DEBUG ROUTES ====================

@app.route('/debug/paths')
def debug_paths():
    """Debug route to check all paths"""
    import os
    return {
        'base_dir': BASE_DIR,
        'public_dir': PUBLIC_DIR,
        'admin_dir': ADMIN_DIR,
        'public_exists': os.path.exists(PUBLIC_DIR),
        'admin_exists': os.path.exists(ADMIN_DIR),
        'files_in_public': os.listdir(PUBLIC_DIR) if os.path.exists(PUBLIC_DIR) else [],
        'files_in_admin': os.listdir(ADMIN_DIR) if os.path.exists(ADMIN_DIR) else [],
        'dashboard_exists': os.path.exists(os.path.join(ADMIN_DIR, 'dashboard.html')),
        'dashboard_size': os.path.getsize(os.path.join(ADMIN_DIR, 'dashboard.html')) if os.path.exists(os.path.join(ADMIN_DIR, 'dashboard.html')) else 0
    }

@app.route('/debug/test')
def debug_test():
    """Simple test route"""
    return jsonify({'success': True, 'message': 'Debug route working!'})

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print("🚀 Alhudha Haj Travel System v2.0")
    print("=" * 60)
    print(f"📁 Server starting on port {port}")
    print(f"📁 Public directory: {PUBLIC_DIR}")
    print(f"📁 Admin directory: {ADMIN_DIR}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=True)