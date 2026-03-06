# complete_system_test.py
import requests
import json
import os
import sys
from datetime import datetime, timedelta
import time

class SystemTester:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
        self.issues = []
        self.test_data = {}
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        
    def print_header(self, text):
        print("\n" + "="*80)
        print(f" {text}")
        print("="*80)
    
    def print_subheader(self, text):
        print("\n" + "-"*60)
        print(f" {text}")
        print("-"*60)
    
    def print_result(self, test_name, status, message="", fix_suggestion=None):
        if status == 'PASS':
            print(f"  ✅ {test_name}: PASSED")
            if message:
                print(f"     {message}")
            self.results['passed'].append(test_name)
        elif status == 'FAIL':
            print(f"  ❌ {test_name}: FAILED - {message}")
            self.results['failed'].append(test_name)
            if fix_suggestion:
                self.issues.append(f"🔧 FIX: {test_name} - {fix_suggestion}")
        else:
            print(f"  ⚠️  {test_name}: {message}")
            self.results['warnings'].append(test_name)
            if fix_suggestion:
                self.issues.append(f"📝 NOTE: {test_name} - {fix_suggestion}")

    # ==================== SERVER CONNECTION TESTS ====================
    def test_server_connection(self):
        self.print_subheader("🔌 TESTING SERVER CONNECTION")
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_result("Server Connection", 'PASS', 
                                f"Status: {data.get('status')}")
                return True
            else:
                self.print_result("Server Connection", 'FAIL', 
                                f"HTTP {response.status_code}",
                                "Run 'python app/server.py' to start server")
                return False
        except requests.exceptions.ConnectionError:
            self.print_result("Server Connection", 'FAIL', 
                            "Cannot connect - server not running",
                            "Run 'python app/server.py' in a terminal")
            return False
        except Exception as e:
            self.print_result("Server Connection", 'FAIL', str(e),
                            "Check if server is running on port 8080")
            return False

    # ==================== LOGIN TESTS ====================
    def test_login(self):
        self.print_subheader("🔐 TESTING LOGIN")
        
        test_cases = [
            {"username": "superadmin", "password": "admin123", "should_pass": True},
            {"username": "admin1", "password": "admin123", "should_pass": True},
            {"username": "wrong", "password": "wrong", "should_pass": False}
        ]
        
        for test in test_cases:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/login",
                    json={
                        "username": test["username"],
                        "password": test["password"],
                        "remember_me": True
                    }
                )
                
                data = response.json()
                authenticated = data.get('authenticated', False)
                
                if test["should_pass"] and authenticated:
                    self.print_result(f"Login: {test['username']}", 'PASS')
                    self.test_data['user'] = data.get('user', {})
                    self.test_data['cookies'] = self.session.cookies.get_dict()
                elif not test["should_pass"] and not authenticated:
                    self.print_result(f"Login: {test['username']} (should fail)", 'PASS')
                else:
                    self.print_result(f"Login: {test['username']}", 'FAIL',
                                    f"Expected pass: {test['should_pass']}, Got: {authenticated}",
                                    "Check app/routes/auth.py - login() function")
            except Exception as e:
                self.print_result(f"Login: {test['username']}", 'FAIL', str(e),
                                "Check if login endpoint exists")

    # ==================== SESSION TESTS ====================
    def test_session(self):
        self.print_subheader("🍪 TESTING SESSION")
        
        try:
            response = self.session.get(f"{self.base_url}/api/check-session")
            data = response.json()
            
            if data.get('authenticated'):
                self.print_result("Session Check", 'PASS',
                                f"User: {data.get('user', {}).get('username')}")
            else:
                self.print_result("Session Check", 'FAIL', "Not authenticated",
                                "Check session cookie and login first")
        except Exception as e:
            self.print_result("Session Check", 'FAIL', str(e),
                            "Check app/routes/auth.py - check_session()")

    # ==================== CSS FILE TESTS ====================
    def test_css_files(self):
        self.print_subheader("🎨 TESTING CSS FILES")
        
        css_files = [
            ("public/admin/style.css", "Old style.css"),
            ("public/admin/fixes.css", "Fixes.css"),
            ("public/admin/admin-style.css", "New admin-style.css")
        ]
        
        for file_path, description in css_files:
            full_path = os.path.join(self.project_root, file_path)
            if os.path.exists(full_path):
                size = os.path.getsize(full_path)
                if file_path == "public/admin/admin-style.css":
                    # Check if admin-style.css has all required sections
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    required_sections = [
                        '.admin-header', 
                        '.modal', 
                        '.btn-primary',
                        '.table-container',
                        '@media (max-width: 768px)'
                    ]
                    
                    missing = []
                    for section in required_sections:
                        if section not in content:
                            missing.append(section)
                    
                    if missing:
                        self.print_result(f"CSS: {description}", 'WARNING',
                                        f"Missing sections: {missing}",
                                        "Add missing CSS sections to admin-style.css")
                    else:
                        self.print_result(f"CSS: {description}", 'PASS', f"Size: {size} bytes")
                else:
                    self.print_result(f"CSS: {description}", 'WARNING',
                                    f"File exists ({size} bytes) but should be deleted",
                                    f"Delete {file_path} and use admin-style.css only")
            else:
                if file_path == "public/admin/admin-style.css":
                    self.print_result(f"CSS: {description}", 'FAIL', "File not found",
                                    "Create admin-style.css by merging style.css and fixes.css")

    # ==================== HTML FILE TESTS ====================
    def test_html_files(self):
        self.print_subheader("📄 TESTING HTML FILES")
        
        html_files = [
            "public/admin/dashboard.html",
            "public/admin/users.html",
            "public/admin/invoices.html",
            "public/admin/batches.html",
            "public/admin/payments.html",
            "public/admin/receipts.html",
            "public/admin/travelers.html",
            "public/admin/whatsapp.html",
            "public/admin/email.html",
            "public/admin/frontpage.html",
            "public/admin/backup.html",
            "public/admin.login.html",
            "public/index.html"
        ]
        
        for file_path in html_files:
            full_path = os.path.join(self.project_root, file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check CSS links
                if 'style.css' in content and 'admin-style.css' not in content:
                    self.print_result(f"HTML: {file_path}", 'WARNING',
                                    "Still using old style.css",
                                    f"Change to: <link rel='stylesheet' href='admin-style.css'>")
                elif 'admin-style.css' in content:
                    self.print_result(f"HTML: {file_path}", 'PASS', "Using new CSS")
                else:
                    self.print_result(f"HTML: {file_path}", 'WARNING',
                                    "No CSS link found",
                                    "Add: <link rel='stylesheet' href='admin-style.css'>")
                
                # Check for duplicate modal CSS in invoices.html
                if file_path == "public/admin/invoices.html":
                    if '.modal {' in content and '/* ==================== MODAL SECTION (FIXED) ==================== */' not in content:
                        self.print_result(f"HTML: {file_path}", 'WARNING',
                                        "Has duplicate modal CSS",
                                        "Remove the modal CSS section from invoices.html")
            else:
                self.print_result(f"HTML: {file_path}", 'WARNING', "File not found",
                                f"Create {file_path} if needed")

    # ==================== API ENDPOINT TESTS ====================
    def test_api_endpoints(self):
        self.print_subheader("🔧 TESTING API ENDPOINTS")
        
        endpoints = [
            ("/api/health", "Health Check"),
            ("/api/check-session", "Session Check"),
            ("/api/admin/users", "Get Users"),
            ("/api/admin/dashboard/stats", "Dashboard Stats"),
            ("/api/batches", "Get Batches"),
            ("/api/travelers", "Get Travelers"),
            ("/api/payments", "Get Payments"),
            ("/api/invoices", "Get Invoices"),
            ("/api/receipts", "Get Receipts")
        ]
        
        for endpoint, name in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if endpoint == "/api/admin/users":
                            users = data.get('users', [])
                            self.print_result(f"API: {name}", 'PASS', f"Found {len(users)} users")
                        elif endpoint == "/api/admin/dashboard/stats":
                            stats = data.get('stats', {})
                            self.print_result(f"API: {name}", 'PASS', 
                                            f"Travelers: {stats.get('total_travelers', 0)}")
                        else:
                            self.print_result(f"API: {name}", 'PASS')
                    except:
                        self.print_result(f"API: {name}", 'WARNING', "Response not JSON",
                                        "Check content-type header")
                elif response.status_code == 401:
                    self.print_result(f"API: {name}", 'WARNING', "Authentication required",
                                    "Login first")
                else:
                    self.print_result(f"API: {name}", 'FAIL', f"HTTP {response.status_code}",
                                    f"Check app/routes/{endpoint.split('/')[2]}.py")
            except Exception as e:
                self.print_result(f"API: {name}", 'FAIL', str(e),
                                f"Check if {endpoint} endpoint exists")

    # ==================== CRUD OPERATION TESTS ====================
    def test_crud_operations(self):
        self.print_subheader("🔄 TESTING CRUD OPERATIONS")
        
        # Test CREATE user
        test_username = f"testuser_{datetime.now().strftime('%H%M%S')}"
        try:
            response = self.session.post(
                f"{self.base_url}/api/admin/users",
                json={
                    "username": test_username,
                    "password": "testpass123",
                    "email": f"{test_username}@test.com",
                    "full_name": "Test User",
                    "role": "staff"
                }
            )
            data = response.json()
            
            if data.get('success') and data.get('user_id'):
                user_id = data.get('user_id')
                self.print_result("CRUD: Create User", 'PASS', f"ID: {user_id}")
                self.test_data['test_user_id'] = user_id
            else:
                self.print_result("CRUD: Create User", 'FAIL', data.get('error', 'Unknown'),
                                "Check app/routes/admin.py - create_user()")
        except Exception as e:
            self.print_result("CRUD: Create User", 'FAIL', str(e),
                            "Check POST /api/admin/users endpoint")

        # Test READ user
        if self.test_data.get('test_user_id'):
            try:
                response = self.session.get(
                    f"{self.base_url}/api/admin/users/{self.test_data['test_user_id']}"
                )
                data = response.json()
                
                if data.get('success') and data.get('user'):
                    self.print_result("CRUD: Read User", 'PASS')
                else:
                    self.print_result("CRUD: Read User", 'FAIL', "User not found",
                                    f"Check GET /api/admin/users/{self.test_data['test_user_id']}")
            except Exception as e:
                self.print_result("CRUD: Read User", 'FAIL', str(e))

        # Test UPDATE user
        if self.test_data.get('test_user_id'):
            try:
                response = self.session.put(
                    f"{self.base_url}/api/admin/users/{self.test_data['test_user_id']}",
                    json={"full_name": "Updated Test User"}
                )
                data = response.json()
                
                if data.get('success'):
                    self.print_result("CRUD: Update User", 'PASS')
                else:
                    self.print_result("CRUD: Update User", 'FAIL', data.get('error', 'Unknown'),
                                    f"Check PUT /api/admin/users/{self.test_data['test_user_id']}")
            except Exception as e:
                self.print_result("CRUD: Update User", 'FAIL', str(e))

        # Test DELETE user
        if self.test_data.get('test_user_id'):
            try:
                response = self.session.delete(
                    f"{self.base_url}/api/admin/users/{self.test_data['test_user_id']}"
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.print_result("CRUD: Delete User", 'PASS')
                    else:
                        self.print_result("CRUD: Delete User", 'FAIL', data.get('error', 'Unknown'),
                                        f"Check DELETE /api/admin/users/{self.test_data['test_user_id']}")
                else:
                    self.print_result("CRUD: Delete User", 'FAIL', f"HTTP {response.status_code}",
                                    "Check if DELETE endpoint exists in admin.py")
            except Exception as e:
                self.print_result("CRUD: Delete User", 'FAIL', str(e))

    # ==================== PERMISSION TESTS ====================
    def test_permissions(self):
        self.print_subheader("🔑 TESTING PERMISSIONS")
        
        # Get current user's role
        try:
            response = self.session.get(f"{self.base_url}/api/check-session")
            data = response.json()
            if data.get('authenticated'):
                role = data.get('user', {}).get('role', 'unknown')
                self.print_result("Current User Role", 'PASS', f"Logged in as: {role}")
            else:
                self.print_result("Current User Role", 'WARNING', "Not logged in",
                                "Login first to test permissions")
        except Exception as e:
            self.print_result("Current User Role", 'FAIL', str(e))

    # ==================== DATABASE TESTS ====================
    def test_database(self):
        self.print_subheader("🗄️  TESTING DATABASE")
        
        # Check if database.py exists
        db_file = os.path.join(self.project_root, "app", "database.py")
        if os.path.exists(db_file):
            self.print_result("Database File", 'PASS', "database.py exists")
        else:
            self.print_result("Database File", 'FAIL', "database.py not found",
                            "Create app/database.py")

    # ==================== FOLDER STRUCTURE TESTS ====================
    def test_folder_structure(self):
        self.print_subheader("📁 TESTING FOLDER STRUCTURE")
        
        required_folders = [
            "app",
            "app/routes",
            "public",
            "public/admin",
            "public/admin/js",
            "public/traveler",
            "uploads",
            "uploads/passports",
            "uploads/aadhaar",
            "uploads/photos",
            "uploads/backups"
        ]
        
        for folder in required_folders:
            full_path = os.path.join(self.project_root, folder)
            if os.path.exists(full_path):
                self.print_result(f"Folder: {folder}", 'PASS')
            else:
                self.print_result(f"Folder: {folder}", 'WARNING', "Missing",
                                f"Create folder: {folder}")

    # ==================== JAVASCRIPT FILE TESTS ====================
    def test_javascript_files(self):
        self.print_subheader("📜 TESTING JAVASCRIPT FILES")
        
        js_files = [
            "public/admin/js/session-manager.js"
        ]
        
        for file_path in js_files:
            full_path = os.path.join(self.project_root, file_path)
            if os.path.exists(full_path):
                size = os.path.getsize(full_path)
                self.print_result(f"JS: {file_path}", 'PASS', f"Size: {size} bytes")
            else:
                self.print_result(f"JS: {file_path}", 'FAIL', "File not found",
                                f"Create {file_path}")

    # ==================== SUMMARY REPORT ====================
    def print_summary(self):
        self.print_header("📊 FINAL TEST SUMMARY")
        
        total = len(self.results['passed']) + len(self.results['failed']) + len(self.results['warnings'])
        passed = len(self.results['passed'])
        failed = len(self.results['failed'])
        warnings = len(self.results['warnings'])
        
        print(f"\n✅ PASSED: {passed}/{total}")
        print(f"❌ FAILED: {failed}/{total}")
        print(f"⚠️  WARNINGS: {warnings}/{total}")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        if self.issues:
            self.print_header("🔧 ACTION ITEMS")
            for issue in self.issues:
                print(issue)
        
        if failed == 0 and warnings == 0:
            print("\n🎉 PERFECT! Your system is 100% functional!")
        elif failed == 0:
            print("\n⚠️  System works but has some warnings to address.")
        else:
            print("\n❌ System has critical issues that need fixing.")

    # ==================== RUN ALL TESTS ====================
    def run_all_tests(self):
        self.print_header("🚀 STARTING COMPLETE SYSTEM TEST")
        print(f"Testing against: {self.base_url}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Project root: {self.project_root}")
        
        # Check server first
        if not self.test_server_connection():
            print("\n❌ Server not running. Cannot proceed with API tests.")
            print("💡 Start server with: python app/server.py")
            self.print_summary()
            return
        
        # Run all tests
        self.test_login()
        self.test_session()
        self.test_css_files()
        self.test_html_files()
        self.test_javascript_files()
        self.test_folder_structure()
        self.test_database()
        self.test_api_endpoints()
        self.test_crud_operations()
        self.test_permissions()
        
        # Print summary
        self.print_summary()

if __name__ == "__main__":
    # You can change the URL if needed
    base_url = "http://localhost:8080"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    tester = SystemTester(base_url)
    tester.run_all_tests()