#!/usr/bin/env python3
"""
🔧 AUTOMATIC PRODUCTION FIXER
Applies all fixes to production issues
Run: python auto_fix_production.py
"""

import os
import sys

class AutoFixer:
    def __init__(self):
        self.fixes_applied = []
        self.errors = []
    
    def print_header(self, title):
        print("\n" + "="*80)
        print(title.center(80))
        print("="*80 + "\n")
    
    def log_fix(self, file_path, description):
        msg = f"✅ Fixed {file_path}: {description}"
        print(msg)
        self.fixes_applied.append(msg)
    
    def log_error(self, file_path, description):
        msg = f"❌ Error in {file_path}: {description}"
        print(msg)
        self.errors.append(msg)
    
    # ====== FIX 1: auth.py ======
    
    def fix_auth_routes(self):
        """Fix authentication routes - add methods=['POST']"""
        self.print_header("🔐 FIX 1: Authentication Routes")
        
        auth_file = "app/routes/auth.py"
        
        if not os.path.exists(auth_file):
            self.log_error(auth_file, "File not found")
            return False
        
        try:
            with open(auth_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix 1.1: Add methods to /login
            if "@bp.route('/login')" in content and "methods=['POST']" not in content:
                content = content.replace(
                    "@bp.route('/login')",
                    "@bp.route('/login', methods=['POST'])"
                )
                self.log_fix(auth_file, "Added methods=['POST'] to /login route")
            
            # Fix 1.2: Add methods to /logout
            if "@bp.route('/logout')" in content and "methods=['POST']" not in content:
                content = content.replace(
                    "@bp.route('/logout')",
                    "@bp.route('/logout', methods=['POST'])"
                )
                self.log_fix(auth_file, "Added methods=['POST'] to /logout route")
            
            # Fix 1.3: Add missing /me endpoint
            if "@bp.route('/me'" not in content:
                me_endpoint = '''
@bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user information"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        conn, cursor = get_db()
        try:
            cursor.execute("""
                SELECT id, username, full_name, email, role 
                FROM users WHERE id = %s AND is_active = true
            """, (session['user_id'],))
            
            user = cursor.fetchone()
            
            if user:
                return jsonify({'success': True, 'user': dict(user)}), 200
            else:
                session.clear()
                return jsonify({'success': False, 'error': 'User not found'}), 404
        finally:
            release_db(conn, cursor)
    except Exception as e:
        logger.error(f"Get user error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
'''
                # Add before the last part of file
                content = content.rstrip() + me_endpoint
                self.log_fix(auth_file, "Added missing /me endpoint")
            
            with open(auth_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        
        except Exception as e:
            self.log_error(auth_file, str(e))
            return False
    
    # ====== FIX 2: server.py Security Headers ======
    
    def fix_security_headers(self):
        """Add security headers middleware to server.py"""
        self.print_header("🛡️ FIX 2: Security Headers")
        
        server_file = "app/server.py"
        
        if not os.path.exists(server_file):
            self.log_error(server_file, "File not found")
            return False
        
        try:
            with open(server_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if security headers already added
            if 'X-Frame-Options' in content:
                print("⚠️ Security headers already present")
                return True
            
            # Add security headers function
            security_headers_code = '''
# ====== 🛡️ SECURITY HEADERS ======
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com unpkg.com; "
        "style-src 'self' 'unsafe-inline' fonts.googleapis.com cdnjs.cloudflare.com; "
        "font-src 'self' fonts.gstatic.com cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https:;"
    )
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

'''
            
            # Find the best place to insert (after app = Flask(__name__))
            if 'app = Flask(__name__)' in content:
                insert_pos = content.find('app = Flask(__name__)') + len('app = Flask(__name__)')
                next_newline = content.find('\n', insert_pos)
                content = content[:next_newline+1] + security_headers_code + content[next_newline+1:]
                self.log_fix(server_file, "Added security headers middleware")
            
            with open(server_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        
        except Exception as e:
            self.log_error(server_file, str(e))
            return False
    
    # ====== FIX 3: reports.py ======
    
    def fix_reports_endpoints(self):
        """Add missing /summary endpoint to reports.py"""
        self.print_header("📊 FIX 3: Reports Endpoints")
        
        reports_file = "app/routes/reports.py"
        
        if not os.path.exists(reports_file):
            self.log_error(reports_file, "File not found")
            return False
        
        try:
            with open(reports_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if /summary already exists
            if "@bp.route('/summary'" in content:
                print("⚠️ /summary endpoint already present")
                return True
            
            # Add summary endpoint
            summary_code = '''
# ====== SUMMARY REPORT ======
@bp.route('/summary', methods=['GET'])
def summary_report():
    """Get summary statistics"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        conn, cursor = get_db()
        
        try:
            cursor.execute('SELECT COUNT(*) as count FROM travelers')
            travelers_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM batches')
            batches_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT SUM(amount) as total FROM payments WHERE status = %s', ('completed',))
            total_payments = cursor.fetchone()['total'] or 0
            
            return jsonify({
                'success': True,
                'data': {
                    'total_travelers': travelers_count,
                    'total_batches': batches_count,
                    'total_payments': float(total_payments)
                }
            }), 200
        
        finally:
            release_db(conn, cursor)
    
    except Exception as e:
        logger.error(f"Summary report error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

'''
            
            # Add at the beginning after imports
            insert_pos = content.find('bp = Blueprint')
            if insert_pos > 0:
                insert_pos = content.find('\n', insert_pos) + 1
                content = content[:insert_pos] + summary_code + content[insert_pos:]
                self.log_fix(reports_file, "Added /summary endpoint")
            
            with open(reports_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        
        except Exception as e:
            self.log_error(reports_file, str(e))
            return False
    
    # ====== FIX 4: HTML Google Fonts ======
    
    def fix_html_fonts(self):
        """Fix Google Fonts CDN link in HTML files"""
        self.print_header("🎨 FIX 4: HTML Google Fonts")
        
        html_files = [
            'public/index.html',
            'public/admin.login.html',
            'public/traveler_login.html',
            'public/traveler_dashboard.html',
        ]
        
        wrong_url = 'https://fonts.googleapis.com/css2'
        correct_url = 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Amiri:wght@400;700&display=swap'
        
        fixed_count = 0
        
        for html_file in html_files:
            if not os.path.exists(html_file):
                continue
            
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if wrong_url in content:
                    content = content.replace(wrong_url, correct_url)
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.log_fix(html_file, "Fixed Google Fonts URL")
                    fixed_count += 1
            
            except Exception as e:
                self.log_error(html_file, str(e))
        
        if fixed_count > 0:
            return True
        return False
    
    # ====== RUN ALL FIXES ======
    
    def run_all_fixes(self):
        """Run all fixes"""
        print("\n" + "🔧 AUTOMATIC PRODUCTION FIXER".center(80))
        print("="*80 + "\n")
        
        results = {
            'auth': self.fix_auth_routes(),
            'security': self.fix_security_headers(),
            'reports': self.fix_reports_endpoints(),
            'fonts': self.fix_html_fonts(),
        }
        
        # Print summary
        self.print_header("📊 FIX SUMMARY")
        
        print(f"✅ Authentication routes: {'FIXED' if results['auth'] else 'FAILED'}")
        print(f"🛡️ Security headers: {'FIXED' if results['security'] else 'FAILED'}")
        print(f"📊 Reports endpoints: {'FIXED' if results['reports'] else 'FAILED'}")
        print(f"🎨 HTML fonts: {'FIXED' if results['fonts'] else 'FAILED'}\n")
        
        if len(self.fixes_applied) > 0:
            print("Applied Fixes:")
            for fix in self.fixes_applied:
                print("  " + fix)
        
        if len(self.errors) > 0:
            print("\nErrors:")
            for error in self.errors:
                print("  " + error)
        
        print("\n" + "="*80)
        
        all_success = all(results.values())
        
        if all_success:
            print("✅ ALL FIXES APPLIED SUCCESSFULLY!".center(80))
        else:
            print("⚠️ SOME FIXES FAILED - CHECK ERRORS ABOVE".center(80))
        
        print("="*80 + "\n")
        
        print("NEXT STEPS:")
        print("1. Run tests: python test_production_railway.py")
        print("2. Check if pass rate improved to 95%+")
        print("3. If OK, deploy: git push railway main\n")
        
        return all_success

if __name__ == "__main__":
    fixer = AutoFixer()
    success = fixer.run_all_fixes()
    sys.exit(0 if success else 1)
