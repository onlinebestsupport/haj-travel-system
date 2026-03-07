#!/usr/bin/env python3
"""
🚀 PRODUCTION TEST SUITE - Railway Deployment
Alhudha Haj Travel System - Complete Testing for Production
Language: Python (19.7%), HTML (76%), CSS (3.1%), JavaScript (1.2%)
Base URL: https://haj-web-app-production.up.railway.app

Run: python test_production_railway.py
"""

import requests
import json
import sys
import time
from datetime import datetime

# ==================== CONFIGURATION ====================
BASE_URL = "https://haj-web-app-production.up.railway.app"
TIMEOUT = 15

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# ==================== TEST RUNNER ====================

class ProductionTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.results = {
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'total': 0,
            'errors': []
        }
        self.auth_session = None
    
    def print_header(self, title):
        print("\n" + Colors.HEADER + Colors.BOLD + "="*80 + Colors.ENDC)
        print(Colors.HEADER + Colors.BOLD + title.center(80) + Colors.ENDC)
        print(Colors.HEADER + Colors.BOLD + "="*80 + Colors.ENDC + "\n")
    
    def print_test(self, name, passed, details="", skip=False):
        self.results['total'] += 1
        
        if skip:
            print(Colors.WARNING + "⊘ SKIP" + Colors.ENDC + " | " + name)
            self.results['skipped'] += 1
        elif passed:
            print(Colors.OKGREEN + "✅ PASS" + Colors.ENDC + " | " + name)
            if details:
                print("   └─ " + Colors.OKCYAN + details + Colors.ENDC)
            self.results['passed'] += 1
        else:
            print(Colors.FAIL + "❌ FAIL" + Colors.ENDC + " | " + name)
            if details:
                print("   └─ " + Colors.FAIL + details + Colors.ENDC)
            self.results['failed'] += 1
            self.results['errors'].append((name, details))
    
    def authenticate(self):
        """Authenticate and create session"""
        try:
            response = self.session.post(
                BASE_URL + "/api/auth/login",
                json={'username': 'superadmin', 'password': 'admin123'},
                timeout=TIMEOUT,
                verify=True
            )
            if response.status_code == 200:
                self.auth_session = self.session
                return True
        except:
            pass
        return False
    
    # ==================== HTML TESTS (76%) ====================
    
    def test_html_pages(self):
        """Test all HTML pages"""
        self.print_header("📄 HTML PAGES TESTS (76%)")
        
        pages = {
            '/': 'Homepage',
            '/index.html': 'Homepage (explicit)',
            '/admin.login.html': 'Admin Login',
            '/traveler_login.html': 'Traveler Login',
        }
        
        for path, name in pages.items():
            try:
                response = self.session.get(
                    BASE_URL + path,
                    timeout=TIMEOUT,
                    verify=True
                )
                passed = response.status_code == 200
                details = "HTTP " + str(response.status_code) + ", Size: " + str(len(response.content)) + " bytes"
                self.print_test("HTML: " + name, passed, details)
            except Exception as e:
                self.print_test("HTML: " + name, False, str(e))
    
    def test_html_structure(self):
        """Test HTML structure and validity"""
        self.print_header("🏗️ HTML STRUCTURE TESTS")
        
        try:
            response = self.session.get(
                BASE_URL + "/",
                timeout=TIMEOUT,
                verify=True
            )
            html = response.text
            
            # Check DOCTYPE
            has_doctype = '<!DOCTYPE html>' in html or '<!doctype html>' in html.lower()
            self.print_test("HTML has DOCTYPE", has_doctype)
            
            # Check meta tags
            has_charset = 'charset' in html
            self.print_test("HTML has charset meta", has_charset)
            
            has_viewport = 'viewport' in html
            self.print_test("HTML has viewport meta", has_viewport)
            
            # Check title
            has_title = '<title>' in html and '</title>' in html
            self.print_test("HTML has title tag", has_title)
            
            # Check CSS links
            has_css = 'style.css' in html or 'href="' in html
            self.print_test("HTML has CSS links", has_css)
            
            # Check proper closing tags
            opening_html = html.count('<html')
            closing_html = html.count('</html>')
            details = "Opening: " + str(opening_html) + ", Closing: " + str(closing_html)
            self.print_test("HTML has proper <html> tags", opening_html == closing_html, details)
            
        except Exception as e:
            self.print_test("HTML structure analysis", False, str(e))
    
    # ==================== CSS TESTS (3.1%) ====================
    
    def test_css_files(self):
        """Test CSS files"""
        self.print_header("🎨 CSS TESTS (3.1%)")
        
        css_files = {
            '/style.css': 'Main stylesheet',
            '/admin/admin-style.css': 'Admin stylesheet',
        }
        
        for path, name in css_files.items():
            try:
                response = self.session.get(
                    BASE_URL + path,
                    timeout=TIMEOUT,
                    verify=True
                )
                passed = response.status_code in [200, 304]
                details = "HTTP " + str(response.status_code) + ", Size: " + str(len(response.content)) + " bytes"
                self.print_test("CSS: " + name, passed, details)
                
                if passed:
                    # Check CSS has content
                    has_content = len(response.content) > 100
                    self.print_test("  CSS has content", has_content)
                    
                    # Check for common CSS patterns
                    has_selectors = '{' in response.text and '}' in response.text
                    self.print_test("  CSS has selectors", has_selectors)
                    
            except Exception as e:
                self.print_test("CSS: " + name, False, str(e))
    
    # ==================== JAVASCRIPT TESTS (1.2%) ====================
    
    def test_javascript_resources(self):
        """Test JavaScript resources"""
        self.print_header("⚙️ JAVASCRIPT TESTS (1.2%)")
        
        # Test external JS libraries
        js_libs = [
            ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css', 'Font Awesome'),
            ('https://fonts.googleapis.com/css2', 'Google Fonts'),
        ]
        
        for url, name in js_libs:
            try:
                response = requests.get(url, timeout=10, verify=True)
                passed = response.status_code in [200, 304]
                self.print_test("JS Library: " + name, passed, "HTTP " + str(response.status_code))
            except Exception as e:
                self.print_test("JS Library: " + name, False, str(e))
    
    # ==================== PYTHON BACKEND TESTS (19.7%) ====================
    
    def test_api_endpoints(self):
        """Test Python API endpoints"""
        self.print_header("🐍 PYTHON API TESTS (19.7%)")
        
        # Health check
        try:
            response = self.session.get(
                BASE_URL + "/health",
                timeout=TIMEOUT,
                verify=True
            )
            passed = response.status_code == 200
            if passed:
                data = response.json()
                details = "Status: " + str(data.get('status', 'unknown'))
            else:
                details = "HTTP " + str(response.status_code)
            self.print_test("Health endpoint", passed, details)
        except Exception as e:
            self.print_test("Health endpoint", False, str(e))
        
        # API Endpoints
        endpoints = [
            ('/api/auth/login', 'POST', 'Authentication'),
            ('/api/auth/logout', 'POST', 'Logout'),
            ('/api/auth/me', 'GET', 'Current User'),
            ('/api/batches', 'GET', 'Batches List'),
            ('/api/travelers', 'GET', 'Travelers List'),
            ('/api/payments', 'GET', 'Payments List'),
            ('/api/invoices', 'GET', 'Invoices List'),
            ('/api/receipts', 'GET', 'Receipts List'),
            ('/api/reports/summary', 'GET', 'Summary Report'),
            ('/api/admin/users', 'GET', 'Users List'),
            ('/api/company/settings', 'GET', 'Company Settings'),
        ]
        
        for endpoint, method, name in endpoints:
            try:
                if method == 'GET':
                    response = self.session.get(
                        BASE_URL + endpoint,
                        timeout=TIMEOUT,
                        verify=True
                    )
                else:
                    response = self.session.post(
                        BASE_URL + endpoint,
                        json={},
                        timeout=TIMEOUT,
                        verify=True
                    )
                
                # Accept 200, 401 (not authenticated), 405 (method not allowed in some cases)
                passed = response.status_code in [200, 401, 405]
                details = "HTTP " + str(response.status_code)
                self.print_test("API: " + name, passed, details)
                
            except Exception as e:
                self.print_test("API: " + name, False, str(e))
    
    def test_authentication(self):
        """Test authentication system"""
        self.print_header("🔐 AUTHENTICATION TESTS")
        
        # Test valid login
        try:
            response = self.session.post(
                BASE_URL + "/api/auth/login",
                json={'username': 'superadmin', 'password': 'admin123'},
                timeout=TIMEOUT,
                verify=True
            )
            passed = response.status_code == 200
            if passed:
                data = response.json()
                details = "Login successful: " + str(data.get('success', False))
            else:
                details = "HTTP " + str(response.status_code)
            self.print_test("Valid login", passed, details)
        except Exception as e:
            self.print_test("Valid login", False, str(e))
        
        # Test invalid login
        try:
            response = self.session.post(
                BASE_URL + "/api/auth/login",
                json={'username': 'invalid', 'password': 'invalid'},
                timeout=TIMEOUT,
                verify=True
            )
            passed = response.status_code in [401, 400]
            details = "HTTP " + str(response.status_code)
            self.print_test("Invalid login rejected", passed, details)
        except Exception as e:
            self.print_test("Invalid login rejected", False, str(e))
    
    def test_database_operations(self):
        """Test database operations"""
        self.print_header("🗄️ DATABASE TESTS")
        
        if not self.auth_session:
            self.print_test("Authenticated session", False, "Not authenticated", skip=True)
            return
        
        # Test data retrieval
        queries = [
            ('/api/batches', 'Batches'),
            ('/api/travelers', 'Travelers'),
            ('/api/payments', 'Payments'),
        ]
        
        for endpoint, name in queries:
            try:
                response = self.auth_session.get(
                    BASE_URL + endpoint,
                    timeout=TIMEOUT,
                    verify=True
                )
                passed = response.status_code in [200, 401]
                if passed and response.status_code == 200:
                    data = response.json()
                    count = len(data.get('data', []))
                    details = "Retrieved " + str(count) + " records"
                else:
                    details = "HTTP " + str(response.status_code)
                self.print_test("DB Query: " + name, passed, details)
            except Exception as e:
                self.print_test("DB Query: " + name, False, str(e))
    
    # ==================== SECURITY TESTS ====================
    
    def test_security_headers(self):
        """Test security headers"""
        self.print_header("🛡️ SECURITY TESTS")
        
        try:
            response = self.session.get(
                BASE_URL + "/",
                timeout=TIMEOUT,
                verify=True
            )
            
            headers_to_check = {
                'X-Frame-Options': 'Clickjacking protection',
                'X-Content-Type-Options': 'MIME type protection',
                'Strict-Transport-Security': 'HTTPS enforcement',
                'Content-Security-Policy': 'XSS protection',
            }
            
            for header, purpose in headers_to_check.items():
                has_header = header in response.headers
                if has_header:
                    details = response.headers.get(header, 'Not set')[:50]
                else:
                    details = 'Not set'
                self.print_test("Security: " + header, has_header, details)
            
        except Exception as e:
            self.print_test("Security headers check", False, str(e))
    
    def test_ssl_certificate(self):
        """Test SSL certificate"""
        self.print_header("🔒 SSL CERTIFICATE TESTS")
        
        try:
            response = self.session.get(
                BASE_URL + "/",
                timeout=TIMEOUT,
                verify=True
            )
            passed = response.status_code == 200
            self.print_test("SSL certificate valid", passed, "HTTPS connection successful")
        except requests.exceptions.SSLError as e:
            self.print_test("SSL certificate valid", False, "SSL Error: " + str(e))
        except Exception as e:
            self.print_test("SSL certificate check", False, str(e))
    
    # ==================== PERFORMANCE TESTS ====================
    
    def test_performance(self):
        """Test performance metrics"""
        self.print_header("⚡ PERFORMANCE TESTS")
        
        # Test homepage load time
        try:
            start = time.time()
            response = self.session.get(
                BASE_URL + "/",
                timeout=TIMEOUT,
                verify=True
            )
            elapsed = (time.time() - start) * 1000
            
            passed = elapsed < 3000
            details = "Load time: " + str(int(elapsed)) + "ms"
            self.print_test("Homepage load time", passed, details)
        except Exception as e:
            self.print_test("Homepage load time", False, str(e))
        
        # Test API response time
        try:
            start = time.time()
            response = self.session.get(
                BASE_URL + "/health",
                timeout=TIMEOUT,
                verify=True
            )
            elapsed = (time.time() - start) * 1000
            
            passed = elapsed < 1000
            details = "Response time: " + str(int(elapsed)) + "ms"
            self.print_test("API response time", passed, details)
        except Exception as e:
            self.print_test("API response time", False, str(e))
    
    # ==================== COMPREHENSIVE TESTS ====================
    
    def test_full_workflow(self):
        """Test complete user workflow"""
        self.print_header("🔄 COMPLETE WORKFLOW TESTS")
        
        try:
            # 1. Access homepage
            r1 = self.session.get(BASE_URL + "/", timeout=TIMEOUT, verify=True)
            step1 = r1.status_code == 200
            self.print_test("Step 1: Access homepage", step1, "HTTP " + str(r1.status_code))
            
            # 2. Access login page
            r2 = self.session.get(BASE_URL + "/admin.login.html", timeout=TIMEOUT, verify=True)
            step2 = r2.status_code == 200
            self.print_test("Step 2: Access login page", step2, "HTTP " + str(r2.status_code))
            
            # 3. Login
            r3 = self.session.post(
                BASE_URL + "/api/auth/login",
                json={'username': 'superadmin', 'password': 'admin123'},
                timeout=TIMEOUT,
                verify=True
            )
            step3 = r3.status_code == 200
            self.print_test("Step 3: Login", step3, "HTTP " + str(r3.status_code))
            
            # 4. Access API
            r4 = self.session.get(BASE_URL + "/api/batches", timeout=TIMEOUT, verify=True)
            step4 = r4.status_code in [200, 401]
            self.print_test("Step 4: Access API", step4, "HTTP " + str(r4.status_code))
            
            all_passed = all([step1, step2, step3, step4])
            return all_passed
        except Exception as e:
            self.print_test("Workflow test", False, str(e))
            return False
    
    # ==================== SUMMARY ====================
    
    def print_summary(self):
        """Print final summary"""
        total = self.results['passed'] + self.results['failed']
        if total > 0:
            pass_rate = (self.results['passed'] / total) * 100
        else:
            pass_rate = 0
        
        self.print_header("📊 FINAL TEST REPORT")
        
        print(Colors.OKGREEN + "✅ Passed: " + Colors.ENDC + str(self.results['passed']) + "/" + str(total))
        print(Colors.FAIL + "❌ Failed: " + Colors.ENDC + str(self.results['failed']) + "/" + str(total))
        print(Colors.WARNING + "⊘ Skipped: " + Colors.ENDC + str(self.results['skipped']))
        print(Colors.OKBLUE + "📈 Pass Rate: " + Colors.ENDC + str(round(pass_rate, 1)) + "%\n")
        
        if self.results['errors']:
            print(Colors.FAIL + Colors.BOLD + "FAILED TESTS:" + Colors.ENDC)
            for name, error in self.results['errors'][:10]:
                print("  • " + name)
                if error:
                    print("    → " + error + "\n")
        
        print(Colors.HEADER + Colors.BOLD + "="*80 + Colors.ENDC)
        
        if pass_rate >= 95:
            print(Colors.OKGREEN + Colors.BOLD + "✅ EXCELLENT - Production Ready!" + Colors.ENDC)
        elif pass_rate >= 85:
            print(Colors.OKGREEN + Colors.BOLD + "✅ GOOD - Minor issues" + Colors.ENDC)
        elif pass_rate >= 75:
            print(Colors.WARNING + Colors.BOLD + "⚠️ FAIR - Address issues" + Colors.ENDC)
        else:
            print(Colors.FAIL + Colors.BOLD + "❌ POOR - Critical issues" + Colors.ENDC)
        
        print(Colors.HEADER + Colors.BOLD + "="*80 + Colors.ENDC + "\n")
        
        return self.results['failed'] == 0
    
    def run(self):
        """Run all tests"""
        print("\n" + Colors.BOLD + Colors.OKBLUE)
        print("╔" + "="*78 + "╗")
        print("║" + " "*78 + "║")
        print("║" + "🚀 PRODUCTION TEST SUITE - RAILWAY DEPLOYMENT 🚀".center(78) + "║")
        print("║" + "Alhudha Haj Travel System - Complete Testing".center(78) + "║")
        print("║" + "Language: Python (19.7%) | HTML (76%) | CSS (3.1%) | JS (1.2%)".center(78) + "║")
        print("║" + " "*78 + "║")
        print("╚" + "="*78 + "╝")
        print(Colors.ENDC)
        
        print("🎯 URL: " + Colors.BOLD + BASE_URL + Colors.ENDC)
        print("⏰ Started: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("⏱️ Timeout: " + str(TIMEOUT) + " seconds\n")
        
        # Authenticate
        print("🔑 Authenticating...")
        if self.authenticate():
            print("   ✅ Authenticated as superadmin\n")
        else:
            print("   ⚠️  Could not authenticate (some tests may be skipped)\n")
        
        # Run tests
        self.test_html_pages()
        self.test_html_structure()
        self.test_css_files()
        self.test_javascript_resources()
        self.test_api_endpoints()
        self.test_authentication()
        self.test_database_operations()
        self.test_security_headers()
        self.test_ssl_certificate()
        self.test_performance()
        self.test_full_workflow()
        
        # Print summary
        success = self.print_summary()
        
        return success

# ==================== MAIN ====================

if __name__ == "__main__":
    suite = ProductionTestSuite()
    try:
        success = suite.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n" + Colors.WARNING + "Tests interrupted by user" + Colors.ENDC)
        sys.exit(1)
    except Exception as e:
        print("\n" + Colors.FAIL + "Unexpected error: " + str(e) + Colors.ENDC)
        sys.exit(1)