from flask import Flask, send_from_directory, jsonify, request, session
from flask_cors import CORS
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import hashlib
import uuid

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
app.config['SESSION_COOKIE_NAME'] = 'alhudha_session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
ADMIN_DIR = os.path.join(PUBLIC_DIR, 'admin')
TRAVELER_DIR = os.path.join(PUBLIC_DIR, 'traveler')

print(f"📁 Base directory: {BASE_DIR}")
print(f"📁 Public directory: {PUBLIC_DIR}")
print(f"📁 Admin directory: {ADMIN_DIR}")
print(f"📁 Traveler directory: {TRAVELER_DIR}")
print(f"📁 Uploads directory: {app.config['UPLOAD_FOLDER']}")

# Check if directories exist
print(f"📁 Public exists: {os.path.exists(PUBLIC_DIR)}")
print(f"📁 Admin exists: {os.path.exists(ADMIN_DIR)}")
print(f"📁 Traveler exists: {os.path.exists(TRAVELER_DIR)}")

# Enable CORS
CORS(app, supports_credentials=True, origins=['*'])

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'passports'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'aadhaar'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'pan'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'vaccine'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'photos'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'backups'), exist_ok=True)

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
    # Prevent directory traversal attacks
    if '..' in filename or filename.startswith('/'):
        return jsonify({'success': False, 'error': 'Invalid path'}), 400
    
    # Check if it's a file with extension
    if '.' in filename:
        try:
            return send_from_directory(PUBLIC_DIR, filename)
        except:
            pass
    
    # If no extension, try with .html
    try:
        return send_from_directory(PUBLIC_DIR, filename + '.html')
    except:
        return jsonify({'success': False, 'error': 'File not found'}), 404

# Admin routes
@app.route('/admin/')
@app.route('/admin')
def serve_admin_index():
    """Serve admin index/dashboard"""
    return send_from_directory(ADMIN_DIR, 'dashboard.html')

@app.route('/admin/<path:filename>')
def serve_admin(filename):
    """Serve admin files"""
    # Prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return jsonify({'success': False, 'error': 'Invalid path'}), 400
    
    # If it's a CSS/JS file, serve directly
    if filename.endswith('.css') or filename.endswith('.js') or filename.endswith('.png') or filename.endswith('.jpg'):
        try:
            return send_from_directory(ADMIN_DIR, filename)
        except:
            pass
    
    # Try with .html extension
    try:
        return send_from_directory(ADMIN_DIR, filename + '.html')
    except:
        try:
            # Try without .html
            return send_from_directory(ADMIN_DIR, filename)
        except:
            return jsonify({'success': False, 'error': 'Admin file not found'}), 404

# Traveler routes
@app.route('/traveler/')
@app.route('/traveler')
def serve_traveler_index():
    """Serve traveler index/dashboard"""
    return send_from_directory(PUBLIC_DIR, 'traveler_dashboard.html')

@app.route('/traveler/<path:filename>')
def serve_traveler(filename):
    """Serve traveler files"""
    if '..' in filename or filename.startswith('/'):
        return jsonify({'success': False, 'error': 'Invalid path'}), 400
    
    try:
        return send_from_directory(PUBLIC_DIR, filename)
    except:
        try:
            return send_from_directory(PUBLIC_DIR, filename + '.html')
        except:
            return jsonify({'success': False, 'error': 'Traveler file not found'}), 404

# Login pages
@app.route('/admin.login.html')
@app.route('/admin/login')
def serve_admin_login():
    return send_from_directory(PUBLIC_DIR, 'admin.login.html')

@app.route('/traveler_login.html')
@app.route('/traveler/login')
def serve_traveler_login():
    return send_from_directory(PUBLIC_DIR, 'traveler_login.html')

# CSS
@app.route('/style.css')
def serve_css():
    return send_from_directory(PUBLIC_DIR, 'style.css')

# Uploads
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files"""
    if '..' in filename or filename.startswith('/'):
        return jsonify({'success': False, 'error': 'Invalid path'}), 400
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==================== API ROUTES ====================

# ==================== AUTHENTICATION API ====================

@app.route('/api/login', methods=['POST'])
def api_login():
    """Admin login API"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session.permanent = True
        
        # Update last login
        db.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
        db.commit()
        
        # Log activity
        log_activity(user['id'], 'login', 'auth', f'User {username} logged in', request.remote_addr)
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'name': user['full_name'],
                'role': user['role'],
                'permissions': json.loads(user['permissions']) if user['permissions'] else {}
            }
        })
    else:
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/api/traveler/login', methods=['POST'])
def api_traveler_login():
    """Traveler login API"""
    data = request.json
    passport_no = data.get('passport_no')
    pin = data.get('pin')
    
    if not passport_no or not pin:
        return jsonify({'success': False, 'error': 'Passport number and PIN required'}), 400
    
    db = get_db()
    traveler = db.execute(
        'SELECT * FROM travelers WHERE passport_no = ? AND pin = ?',
        (passport_no.upper(), pin)
    ).fetchone()
    
    if traveler:
        session['traveler_id'] = traveler['id']
        session['traveler_passport'] = traveler['passport_no']
        session['traveler_name'] = f"{traveler['first_name']} {traveler['last_name']}"
        session.permanent = True
        
        return jsonify({
            'success': True,
            'traveler_id': traveler['id'],
            'name': f"{traveler['first_name']} {traveler['last_name']}",
            'passport': traveler['passport_no']
        })
    else:
        return jsonify({'success': False, 'error': 'Invalid passport number or PIN'}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Logout API"""
    user_id = session.get('user_id')
    if user_id:
        log_activity(user_id, 'logout', 'auth', 'User logged out', request.remote_addr)
    session.clear()
    return jsonify({'success': True})

@app.route('/api/traveler/logout', methods=['POST'])
def api_traveler_logout():
    """Traveler logout API"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/check-session', methods=['GET'])
def check_session():
    """Check if user is logged in"""
    if session.get('user_id'):
        return jsonify({
            'success': True,
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'username': session['username'],
                'role': session['role']
            }
        })
    elif session.get('traveler_id'):
        return jsonify({
            'success': True,
            'authenticated': True,
            'traveler': {
                'id': session['traveler_id'],
                'name': session['traveler_name'],
                'passport': session['traveler_passport']
            }
        })
    else:
        return jsonify({'success': True, 'authenticated': False})

# ==================== DASHBOARD API ====================

@app.route('/api/admin/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """Get dashboard statistics"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    db = get_db()
    
    # Get counts
    travelers_count = db.execute('SELECT COUNT(*) as count FROM travelers').fetchone()['count']
    batches_count = db.execute('SELECT COUNT(*) as count FROM batches').fetchone()['count']
    active_batches = db.execute('SELECT COUNT(*) as count FROM batches WHERE status = "Open"').fetchone()['count']
    
    # Payment stats
    payments = db.execute('SELECT SUM(amount) as total, COUNT(*) as count FROM payments WHERE status = "completed"').fetchone()
    total_collected = payments['total'] or 0
    
    pending_payments = db.execute('SELECT SUM(amount) as total FROM payments WHERE status = "pending"').fetchone()
    pending_amount = pending_payments['total'] or 0
    
    # Recent activity
    recent = db.execute('''
        SELECT 'traveler' as type, first_name || ' ' || last_name as name, created_at 
        FROM travelers ORDER BY created_at DESC LIMIT 5
    ''').fetchall()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_travelers': travelers_count,
            'total_batches': batches_count,
            'active_batches': active_batches,
            'total_collected': total_collected,
            'pending_amount': pending_amount,
            'paid_count': payments['count'] or 0,
            'pending_count': db.execute('SELECT COUNT(*) as count FROM payments WHERE status = "pending"').fetchone()['count']
        },
        'recent_activity': [dict(row) for row in recent]
    })

# ==================== FRONTPAGE API ====================

@app.route('/api/frontpage/config', methods=['GET'])
def get_frontpage_config():
    """Get frontpage configuration"""
    db = get_db()
    config = db.execute('SELECT * FROM frontpage_settings WHERE id = 1').fetchone()
    
    if config:
        return jsonify({
            'success': True,
            **dict(config)
        })
    else:
        return jsonify({'success': False, 'error': 'Configuration not found'}), 404

@app.route('/api/frontpage/config', methods=['POST'])
def update_frontpage_config():
    """Update frontpage configuration"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.json
    
    db = get_db()
    db.execute('''
        UPDATE frontpage_settings SET
            hero_heading = ?, hero_subheading = ?, hero_button_text = ?, hero_button_link = ?,
            packages_title = ?, footer_text = ?, footer_phone = ?, footer_email = ?,
            facebook_url = ?, twitter_url = ?, instagram_url = ?,
            alert_enabled = ?, alert_message = ?, alert_link = ?, alert_color = ?, alert_style = ?,
            whatsapp_number = ?, whatsapp_message = ?, booking_email = ?, email_subject = ?,
            whatsapp_enabled = ?, email_enabled = ?,
            packages = ?, features = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
    ''', (
        data.get('hero_heading'), data.get('hero_subheading'), data.get('hero_button_text'), data.get('hero_button_link'),
        data.get('packages_title'), data.get('footer_text'), data.get('footer_phone'), data.get('footer_email'),
        data.get('facebook_url'), data.get('twitter_url'), data.get('instagram_url'),
        data.get('alert_enabled'), data.get('alert_message'), data.get('alert_link'), data.get('alert_color'), data.get('alert_style'),
        data.get('whatsapp_number'), data.get('whatsapp_message'), data.get('booking_email'), data.get('email_subject'),
        data.get('whatsapp_enabled'), data.get('email_enabled'),
        json.dumps(data.get('packages', [])), json.dumps(data.get('features', []))
    ))
    db.commit()
    
    log_activity(session['user_id'], 'update', 'frontpage', 'Updated frontpage configuration', request.remote_addr)
    
    return jsonify({'success': True})

@app.route('/api/frontpage/whatsapp', methods=['GET'])
def get_whatsapp_config():
    """Get WhatsApp configuration"""
    db = get_db()
    config = db.execute('SELECT number, message_template FROM whatsapp_settings WHERE id = 1').fetchone()
    frontpage = db.execute('SELECT whatsapp_number, whatsapp_message FROM frontpage_settings WHERE id = 1').fetchone()
    
    return jsonify({
        'success': True,
        'whatsappNumber': config['number'] if config else frontpage['whatsapp_number'] if frontpage else None,
        'whatsappMessage': config['message_template'] if config else frontpage['whatsapp_message'] if frontpage else None
    })

@app.route('/api/frontpage/email', methods=['GET'])
def get_email_config():
    """Get email configuration"""
    db = get_db()
    config = db.execute('SELECT from_email, reply_to, subject_prefix FROM email_settings WHERE id = 1').fetchone()
    frontpage = db.execute('SELECT booking_email, email_subject FROM frontpage_settings WHERE id = 1').fetchone()
    
    return jsonify({
        'success': True,
        'bookingEmail': config['from_email'] if config else frontpage['booking_email'] if frontpage else None,
        'emailSubject': config['subject_prefix'] if config else frontpage['email_subject'] if frontpage else None,
        'footerEmail': config['reply_to'] if config else None
    })

@app.route('/api/frontpage/publish', methods=['POST'])
def publish_frontpage():
    """Publish frontpage changes to live site"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.json
    
    # In production, this would write to a file or update a live database
    # For now, we'll just log it
    log_activity(session['user_id'], 'publish', 'frontpage', 'Published frontpage to live site', request.remote_addr)
    
    return jsonify({'success': True, 'message': 'Website published successfully'})

# ==================== REPORTS API ====================

@app.route('/api/reports/generate', methods=['POST'])
def generate_report():
    """Generate custom report"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.json
    report_type = data.get('type', 'custom')
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    batch_id = data.get('batchId')
    status = data.get('status')
    
    db = get_db()
    
    # Build query based on filters
    query = "SELECT * FROM travelers WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND created_at >= ?"
        params.append(start_date)
    if end_date:
        query += " AND created_at <= ?"
        params.append(end_date)
    if batch_id and batch_id != 'all':
        query += " AND batch_id = ?"
        params.append(batch_id)
    
    travelers = db.execute(query, params).fetchall()
    
    # Get payments
    payment_query = "SELECT * FROM payments WHERE 1=1"
    payment_params = []
    
    if start_date:
        payment_query += " AND payment_date >= ?"
        payment_params.append(start_date)
    if end_date:
        payment_query += " AND payment_date <= ?"
        payment_params.append(end_date)
    if batch_id and batch_id != 'all':
        payment_query += " AND batch_id = ?"
        payment_params.append(batch_id)
    
    payments = db.execute(payment_query, payment_params).fetchall()
    
    # Calculate totals
    total_collected = sum(p['amount'] for p in payments if p['status'] == 'completed')
    pending_amount = sum(p['amount'] for p in payments if p['status'] == 'pending')
    
    log_activity(session['user_id'], 'generate', 'report', f'Generated {report_type} report', request.remote_addr)
    
    return jsonify({
        'success': True,
        'report': {
            'summary': {
                'totalTravelers': len(travelers),
                'totalPayments': total_collected,
                'pendingAmount': pending_amount,
                'completedPayments': len([p for p in payments if p['status'] == 'completed']),
                'pendingPayments': len([p for p in payments if p['status'] == 'pending'])
            },
            'travelers': [dict(t) for t in travelers],
            'payments': [dict(p) for p in payments]
        }
    })

# ==================== BACKUP API ====================

@app.route('/api/backup/create', methods=['POST'])
def create_backup():
    """Create database backup"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.json
    backup_type = data.get('type', 'manual')
    backup_name = data.get('name', f"Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    # In production, this would create actual database backup
    # For now, we'll just log it
    db = get_db()
    db.execute('''
        INSERT INTO backup_history (backup_name, backup_type, file_size, tables_count, status, location)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (backup_name, backup_type, '2.4 MB', 12, 'completed', 'local'))
    db.commit()
    
    log_activity(session['user_id'], 'create', 'backup', f'Created backup: {backup_name}', request.remote_addr)
    
    return jsonify({'success': True, 'backup_name': backup_name})

@app.route('/api/backup/list', methods=['GET'])
def list_backups():
    """List all backups"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    db = get_db()
    backups = db.execute('SELECT * FROM backup_history ORDER BY created_at DESC').fetchall()
    
    return jsonify({
        'success': True,
        'backups': [dict(b) for b in backups]
    })

@app.route('/api/backup/restore/<int:backup_id>', methods=['POST'])
def restore_backup(backup_id):
    """Restore from backup"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    log_activity(session['user_id'], 'restore', 'backup', f'Restored backup ID: {backup_id}', request.remote_addr)
    
    return jsonify({'success': True, 'message': 'Backup restored successfully'})

@app.route('/api/backup/delete/<int:backup_id>', methods=['DELETE'])
def delete_backup(backup_id):
    """Delete backup"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    db = get_db()
    db.execute('DELETE FROM backup_history WHERE id = ?', (backup_id,))
    db.commit()
    
    log_activity(session['user_id'], 'delete', 'backup', f'Deleted backup ID: {backup_id}', request.remote_addr)
    
    return jsonify({'success': True})

# ==================== COMPANY SETTINGS API ====================

@app.route('/api/company/settings', methods=['GET'])
def get_company_settings():
    """Get company settings"""
    db = get_db()
    settings = db.execute('SELECT * FROM company_settings WHERE id = 1').fetchone()
    
    if settings:
        return jsonify({'success': True, 'settings': dict(settings)})
    else:
        return jsonify({'success': False, 'error': 'Settings not found'}), 404

@app.route('/api/company/settings', methods=['POST'])
def update_company_settings():
    """Update company settings"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.json
    
    db = get_db()
    db.execute('''
        UPDATE company_settings SET
            legal_name = ?, display_name = ?,
            address_line1 = ?, address_line2 = ?, city = ?, state = ?, country = ?, pin_code = ?,
            phone = ?, mobile = ?, email = ?, website = ?,
            gstin = ?, pan = ?, tan = ?, tcs_no = ?, tin = ?, cin = ?, iec = ?, msme = ?,
            bank_name = ?, bank_branch = ?, account_name = ?, account_no = ?, ifsc_code = ?, micr_code = ?, upi_id = ?, qr_code = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
    ''', (
        data.get('legal_name'), data.get('display_name'),
        data.get('address_line1'), data.get('address_line2'), data.get('city'), data.get('state'), data.get('country'), data.get('pin_code'),
        data.get('phone'), data.get('mobile'), data.get('email'), data.get('website'),
        data.get('gstin'), data.get('pan'), data.get('tan'), data.get('tcs_no'), data.get('tin'), data.get('cin'), data.get('iec'), data.get('msme'),
        data.get('bank_name'), data.get('bank_branch'), data.get('account_name'), data.get('account_no'), data.get('ifsc_code'), data.get('micr_code'), data.get('upi_id'), data.get('qr_code')
    ))
    db.commit()
    
    log_activity(session['user_id'], 'update', 'company', 'Updated company settings', request.remote_addr)
    
    return jsonify({'success': True})

# ==================== ACTIVITY LOG API ====================

@app.route('/api/activity/log', methods=['GET'])
def get_activity_log():
    """Get activity log"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    limit = request.args.get('limit', 50, type=int)
    
    db = get_db()
    activities = db.execute('''
        SELECT a.*, u.username 
        FROM activity_log a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC
        LIMIT ?
    ''', (limit,)).fetchall()
    
    return jsonify({
        'success': True,
        'activities': [dict(a) for a in activities]
    })

# ==================== HELPER FUNCTIONS ====================

def log_activity(user_id, action, module, description, ip_address=None):
    """Log user activity"""
    try:
        db = get_db()
        db.execute(
            'INSERT INTO activity_log (user_id, action, module, description, ip_address) VALUES (?, ?, ?, ?, ?)',
            (user_id, action, module, description, ip_address)
        )
        db.commit()
    except:
        pass  # Fail silently

# ==================== DEBUG ROUTES ====================

@app.route('/debug/paths')
def debug_paths():
    """Debug route to check all paths"""
    import os
    files_in_public = []
    files_in_admin = []
    
    try:
        files_in_public = os.listdir(PUBLIC_DIR) if os.path.exists(PUBLIC_DIR) else []
    except:
        pass
    
    try:
        files_in_admin = os.listdir(ADMIN_DIR) if os.path.exists(ADMIN_DIR) else []
    except:
        pass
    
    return {
        'base_dir': BASE_DIR,
        'public_dir': PUBLIC_DIR,
        'admin_dir': ADMIN_DIR,
        'public_exists': os.path.exists(PUBLIC_DIR),
        'admin_exists': os.path.exists(ADMIN_DIR),
        'files_in_public': files_in_public,
        'files_in_admin': files_in_admin,
        'dashboard_exists': os.path.exists(os.path.join(ADMIN_DIR, 'dashboard.html')),
        'dashboard_size': os.path.getsize(os.path.join(ADMIN_DIR, 'dashboard.html')) if os.path.exists(os.path.join(ADMIN_DIR, 'dashboard.html')) else 0
    }

@app.route('/debug/test')
def debug_test():
    """Simple test route"""
    return jsonify({'success': True, 'message': 'Debug route working!'})

@app.route('/debug/session')
def debug_session():
    """Debug session info"""
    return jsonify({
        'session': dict(session),
        'has_user': 'user_id' in session,
        'has_traveler': 'traveler_id' in session
    })

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
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'modules': [
            'auth', 'admin', 'batches', 'travelers', 'payments',
            'invoices', 'receipts', 'reports', 'users', 'frontpage',
            'whatsapp', 'email', 'backup', 'company'
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("=" * 60)
    print("🚀 Alhudha Haj Travel System v2.0")
    print("=" * 60)
    print(f"📁 Server starting on port {port}")
    print(f"📁 Debug mode: {debug}")
    print(f"📁 Public directory: {PUBLIC_DIR}")
    print(f"📁 Admin directory: {ADMIN_DIR}")
    print(f"📁 Uploads directory: {app.config['UPLOAD_FOLDER']}")
    print("=" * 60)
    print("📡 API Endpoints:")
    print("   - /api/health - Health check")
    print("   - /api/login - Admin login")
    print("   - /api/traveler/login - Traveler login")
    print("   - /api/admin/dashboard/stats - Dashboard stats")
    print("   - /api/frontpage/config - Frontpage config")
    print("   - /api/reports/generate - Generate reports")
    print("   - /api/backup/* - Backup management")
    print("   - /api/company/settings - Company settings")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
