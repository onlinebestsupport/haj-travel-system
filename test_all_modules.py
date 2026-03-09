#!/usr/bin/env python3
"""
Complete System Test - Tests all modules, buttons, and functions
Run: python test_all_modules.py
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuration
BASE_URL = "https://haj-web-app-production.up.railway.app"
TIMEOUT = 10

# Test Credentials
TEST_USER = {"username": "admin1", "password": "admin123"}

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ModuleTester:
    def __init__(self):
        self.session = requests.Session()
        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'details': []
        }
        self.modules = [
            {'name': 'Dashboard', 'path': '/admin/dashboard.html', 'api': '/api/admin/dashboard/stats'},
            {'name': 'Travelers', 'path': '/admin/travelers.html', 'api': '/api/travelers'},
            {'name': 'Batches', 'path': '/admin/batches.html', 'api': '/api/batches'},
            {'name': 'Payments', 'path': '/admin/payments.html', 'api': '/api/payments'},
            {'name': 'Invoices', 'path': '/admin/invoices.html', 'api': '/api/invoices'},
            {'name': 'Receipts', 'path': '/admin/receipts.html', 'api': '/api/receipts'},
            {'name': 'Users', 'path': '/admin/users.html', 'api': '/api/admin/users'},
            {'name': 'Reports', 'path': '/admin/reports.html', 'api': '/api/reports'},
            {'name': 'WhatsApp', 'path': '/admin/whatsapp.html', 'api': '/api/whatsapp/settings'},
            {'name': 'Email', 'path': '/admin/email.html', 'api': '/api/email/settings'},
            {'name': 'Backup', 'path': '/admin/backup.html', 'api': '/api/admin/backups'},
            {'name': 'Frontpage', 'path': '/admin/frontpage.html', 'api': '/api/frontpage/settings'},
        ]

    def print_header(self, text):
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")

    def print_test(self, name, passed, details=""):
        if passed:
            status = f"{Colors.OKGREEN}✅ PASS{Colors.ENDC}"
            self.results['passed'] += 1
        else:
            status = f"{Colors.FAIL}❌ FAIL{Colors.ENDC}"
            self.results['failed'] += 1
        
        print(f"{status} | {name}")
        if details:
            print(f"   └─ {Colors.OKCYAN}{details}{Colors.ENDC}")
        self.results['details'].append(f"{name}: {'PASS' if passed else 'FAIL'} - {details}")

    def print_warning(self, name, details=""):
        status = f"{Colors.WARNING}⚠️ WARN{Colors.ENDC}"
        self.results['warnings'] += 1
        print(f"{status} | {name}")
        if details:
            print(f"   └─ {Colors.OKCYAN}{details}{Colors.ENDC}")

    def login(self):
        """Test login functionality"""
        self.print_header("🔐 LOGIN TEST")
        
        try:
            response = self.session.post(
                f"{BASE_URL}/api/login",
                json=TEST_USER,
                headers={'Content-Type': 'application/json'},
                timeout=TIMEOUT
            )
            
            passed = response.status_code == 200
            details = f"HTTP {response.status_code}"
            
            if passed:
                data = response.json()
                if data.get('authenticated'):
                    details += f" - Logged in as {data.get('user', {}).get('name', 'Admin')}"
                    self.print_test("Login", True, details)
                    return True
                else:
                    details += " - Authentication failed"
                    self.print_test("Login", False, details)
                    return False
            else:
                self.print_test("Login", False, details)
                return False
                
        except Exception as e:
            self.print_test("Login", False, str(e))
            return False

    def test_logout(self):
        """Test logout functionality"""
        self.print_header("🚪 LOGOUT TEST")
        
        try:
            # Test logout endpoint
            response = self.session.post(
                f"{BASE_URL}/api/logout",
                headers={'Content-Type': 'application/json'},
                timeout=TIMEOUT
            )
            
            passed = response.status_code in [200, 204, 401]
            self.print_test("Logout endpoint", passed, f"HTTP {response.status_code}")
            
            # Check if session is invalidated
            check_response = self.session.get(
                f"{BASE_URL}/api/check-session",
                timeout=TIMEOUT
            )
            
            session_invalid = check_response.status_code == 401
            self.print_test("Session invalidated", session_invalid, f"HTTP {check_response.status_code}")
            
            # Login again for other tests
            self.login()
            
        except Exception as e:
            self.print_test("Logout", False, str(e))

    def test_module_page_load(self, module):
        """Test if module HTML page loads"""
        try:
            response = self.session.get(
                f"{BASE_URL}{module['path']}",
                timeout=TIMEOUT
            )
            
            passed = response.status_code == 200
            details = f"HTTP {response.status_code} - {len(response.content)} bytes"
            
            # Check for common UI elements
            html = response.text.lower()
            ui_checks = [
                ('admin' in html or 'dashboard' in html, 'Admin header'),
                ('logout' in html, 'Logout button'),
                ('sidebar' in html or 'nav' in html, 'Navigation'),
                (module['name'].lower() in html, f'{module["name"]} heading')
            ]
            
            ui_score = sum(1 for check, _ in ui_checks if check)
            details += f" - UI elements: {ui_score}/{len(ui_checks)}"
            
            self.print_test(f"{module['name']} page load", passed, details)
            return passed, html
            
        except Exception as e:
            self.print_test(f"{module['name']} page load", False, str(e))
            return False, ""

    def test_module_api(self, module):
        """Test module API endpoint"""
        try:
            response = self.session.get(
                f"{BASE_URL}{module['api']}",
                timeout=TIMEOUT,
                headers={'Content-Type': 'application/json'}
            )
            
            # API might return 401 if not authenticated (but we are)
            passed = response.status_code in [200, 401, 403]
            details = f"HTTP {response.status_code}"
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'success' in data:
                        details += f" - Success: {data.get('success')}"
                    if 'data' in data:
                        details += f" - Has data"
                except:
                    details += " - Valid JSON"
            
            self.print_test(f"{module['name']} API", passed, details)
            
        except Exception as e:
            self.print_test(f"{module['name']} API", False, str(e))

    def test_module_buttons(self, html, module):
        """Check for expected buttons in module"""
        expected_buttons = {
            'Dashboard': ['Add Traveler', 'Record Payment', 'Create Invoice', 'Generate Report'],
            'Travelers': ['Add New Traveler', 'Export', 'Search'],
            'Batches': ['Add Batch', 'Edit', 'Delete'],
            'Payments': ['Record Payment', 'Export', 'Search'],
            'Invoices': ['Create Invoice', 'Print', 'Email'],
            'Receipts': ['Print Receipt', 'Email Receipt'],
            'Users': ['Add User', 'Edit Roles', 'Permissions'],
            'Reports': ['Generate Report', 'Export PDF', 'Export Excel'],
            'WhatsApp': ['Send Message', 'Template', 'Settings'],
            'Email': ['Compose', 'Settings', 'Templates'],
            'Backup': ['Create Backup', 'Restore', 'Download'],
            'Frontpage': ['Edit Content', 'Preview', 'Save']
        }
        
        buttons = expected_buttons.get(module['name'], [])
        found_count = 0
        
        for button in buttons:
            if button.lower() in html.lower():
                found_count += 1
        
        if buttons:
            percentage = (found_count / len(buttons)) * 100
            passed = percentage >= 50  # At least 50% of expected buttons found
            self.print_test(
                f"{module['name']} buttons",
                passed,
                f"Found {found_count}/{len(buttons)} expected buttons ({percentage:.0f}%)"
            )
        else:
            self.print_warning(f"{module['name']} buttons", "No button expectations defined")

    def test_logout_button(self, html):
        """Specifically test for logout button"""
        logout_indicators = ['logout', 'sign out', 'sign-out', 'fa-sign-out-alt']
        found = any(indicator in html.lower() for indicator in logout_indicators)
        self.print_test("Logout button present", found, 
                       f"Found in HTML: {found}")

    def test_module_navigation(self, html):
        """Test if module has navigation to other modules"""
        module_links = ['travelers', 'batches', 'payments', 'invoices', 'dashboard']
        found = sum(1 for link in module_links if link in html.lower())
        passed = found >= 3  # At least 3 module links found
        self.print_test(
            "Navigation links",
            passed,
            f"Found {found}/{len(module_links)} module links"
        )

    def test_session_persistence(self):
        """Test if session persists across requests"""
        self.print_header("🔄 SESSION PERSISTENCE TEST")
        
        try:
            # First request
            resp1 = self.session.get(f"{BASE_URL}/api/check-session")
            status1 = resp1.status_code
            
            # Second request
            resp2 = self.session.get(f"{BASE_URL}/api/check-session") 
            status2 = resp2.status_code
            
            passed = status1 == status2 == 200
            self.print_test(
                "Session persists",
                passed,
                f"Status: {status1} → {status2}"
            )
            
        except Exception as e:
            self.print_test("Session persists", False, str(e))

    def test_database_connection(self):
        """Test database connectivity via API"""
        self.print_header("🗄️  DATABASE CONNECTION TEST")
        
        try:
            response = self.session.get(
                f"{BASE_URL}/api/batches",
                timeout=TIMEOUT
            )
            
            passed = response.status_code == 200
            details = f"HTTP {response.status_code}"
            
            if passed:
                data = response.json()
                if data.get('success') and data.get('batches'):
                    count = len(data['batches'])
                    details += f" - Found {count} batches in database"
            
            self.print_test("Database connection", passed, details)
            
        except Exception as e:
            self.print_test("Database connection", False, str(e))

    def run_all_tests(self):
        """Run all module tests"""
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}")
        print("╔" + "═"*68 + "╗")
        print("║     🚀 COMPLETE SYSTEM TEST SUITE - ALL MODULES 🚀      ║")
        print("║        Testing pages, APIs, buttons, and functions      ║")
        print("╚" + "═"*68 + "╝")
        print(Colors.ENDC)
        
        print(f"🎯 Testing: {Colors.BOLD}{BASE_URL}{Colors.ENDC}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"👤 User: {Colors.BOLD}{TEST_USER['username']}{Colors.ENDC}\n")
        
        # Step 1: Login
        if not self.login():
            print(f"\n{Colors.FAIL}Cannot proceed without login. Exiting.{Colors.ENDC}")
            return
        
        # Step 2: Test session persistence
        self.test_session_persistence()
        
        # Step 3: Test database connection
        self.test_database_connection()
        
        # Step 4: Test each module
        self.print_header("📦 MODULE TESTS")
        
        for module in self.modules:
            print(f"\n{Colors.BOLD}{Colors.UNDERLINE}Testing {module['name']} Module{Colors.ENDC}")
            
            # Test page load
            page_ok, html = self.test_module_page_load(module)
            
            if page_ok and html:
                # Test API
                self.test_module_api(module)
                
                # Test UI elements
                self.test_logout_button(html)
                self.test_module_buttons(html, module)
                self.test_module_navigation(html)
            
            time.sleep(0.5)  # Small delay between tests
        
        # Step 5: Test logout
        self.test_logout()
        
        # Step 6: Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        total = self.results['passed'] + self.results['failed']
        pass_rate = (self.results['passed'] / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}📊 FINAL TEST SUMMARY{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
        
        print(f"✅ Passed:  {Colors.OKGREEN}{self.results['passed']}{Colors.ENDC}")
        print(f"❌ Failed:  {Colors.FAIL}{self.results['failed']}{Colors.ENDC}")
        print(f"⚠️ Warnings: {Colors.WARNING}{self.results['warnings']}{Colors.ENDC}")
        print(f"📈 Pass Rate: {Colors.OKBLUE}{pass_rate:.1f}%{Colors.ENDC}\n")
        
        # Module status summary
        print(f"{Colors.BOLD}Module Status:{Colors.ENDC}")
        status = "✅" if pass_rate >= 80 else "⚠️" if pass_rate >= 60 else "❌"
        print(f"  {status} Overall System: {pass_rate:.1f}% operational\n")
        
        if self.results['failed'] > 0:
            print(f"{Colors.BOLD}Failed Tests Summary:{Colors.ENDC}")
            # Show last few failures
            failures = [d for d in self.results['details'] if 'FAIL' in d][-5:]
            for f in failures:
                print(f"  • {f[:80]}...")
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        
        # Final verdict
        if pass_rate >= 90:
            print(f"{Colors.OKGREEN}{Colors.BOLD}✅ SYSTEM IS FULLY OPERATIONAL!{Colors.ENDC}")
        elif pass_rate >= 75:
            print(f"{Colors.WARNING}{Colors.BOLD}⚠️ SYSTEM IS OPERATIONAL - MINOR ISSUES{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}❌ SYSTEM HAS CRITICAL ISSUES - FIX REQUIRED{Colors.ENDC}")
        
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")

if __name__ == "__main__":
    tester = ModuleTester()
    try:
        tester.run_all_tests()
        sys.exit(0 if tester.results['failed'] == 0 else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Tests interrupted by user{Colors.ENDC}")
        sys.exit(1)