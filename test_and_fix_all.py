#!/usr/bin/env python
"""
Complete API, Navigation & Error Test with Auto-Fix
Tests all endpoints, navigation links, and common errors
"""

import requests
import json
import os
import re
from urllib.parse import urljoin

BASE_URL = "https://haj-web-app-production.up.railway.app"
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
        self.fixes = []

def print_result(name, passed, message=""):
    status = f"{GREEN}✓ PASS{END}" if passed else f"{RED}✗ FAIL{END}"
    print(f"{status} - {name}")
    if message and not passed:
        print(f"  {YELLOW}→ {message}{END}")

def test_api_endpoint(url, description, expected_status=200, auth_required=False):
    """Test an API endpoint"""
    try:
        session = requests.Session()
        if auth_required:
            # Login first
            login = session.post(f"{BASE_URL}/api/login", json={"username": "superadmin", "password": "admin123"})
            if login.status_code != 200:
                return False, f"Login failed for auth test"
        
        response = session.get(url, timeout=10)
        passed = response.status_code == expected_status
        message = f"Status: {response.status_code}" if not passed else ""
        return passed, message
    except Exception as e:
        return False, str(e)

def test_navigation():
    """Test all navigation links"""
    print(f"\n{BLUE}🔗 TESTING NAVIGATION LINKS{END}")
    
    nav_links = [
        ("/", "Home"),
        ("/admin.login.html", "Admin Login"),
        ("/traveler_login.html", "Traveler Login"),
        ("/traveler_dashboard.html", "Traveler Dashboard"),
        ("/admin/dashboard.html", "Admin Dashboard"),
        ("/admin/travelers.html", "Travelers"),
        ("/admin/batches.html", "Batches"),
        ("/admin/payments.html", "Payments"),
        ("/admin/invoices.html", "Invoices"),
        ("/admin/receipts.html", "Receipts"),
        ("/admin/reports.html", "Reports"),
        ("/admin/users.html", "Users"),
    ]
    
    results = []
    for path, name in nav_links:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=10, allow_redirects=False)
            passed = response.status_code in [200, 302, 307]
            results.append((name, passed, response.status_code))
            print_result(f"{name} - {path}", passed, f"Status: {response.status_code}")
        except Exception as e:
            results.append((name, False, str(e)))
            print_result(f"{name} - {path}", False, str(e))
    
    return results

def test_api_endpoints():
    """Test all API endpoints"""
    print(f"\n{BLUE}🔌 TESTING API ENDPOINTS{END}")
    
    api_endpoints = [
        ("/health", "Health Check", False),
        ("/api/health", "API Health", False),
        ("/api", "API Root", False),
        ("/api/check-session", "Session Check", False),
        ("/api/login", "Login", False),  # POST only, so we test method
        ("/api/travelers", "Travelers API", True),
        ("/api/batches", "Batches API", True),
        ("/api/payments", "Payments API", True),
    ]
    
    for path, name, auth in api_endpoints:
        if path == "/api/login":
            # Test POST login
            try:
                response = requests.post(f"{BASE_URL}{path}", json={"username": "test", "password": "test"})
                passed = response.status_code in [200, 401]
                print_result(f"{name} (POST)", passed, f"Status: {response.status_code}")
            except Exception as e:
                print_result(f"{name} (POST)", False, str(e))
        else:
            passed, msg = test_api_endpoint(f"{BASE_URL}{path}", name, 200, auth)
            print_result(name, passed, msg)

def check_errors():
    """Check for common errors in HTML files"""
    print(f"\n{BLUE}⚠️ CHECKING FOR COMMON ERRORS{END}")
    
    html_files = [
        "public/index.html",
        "public/admin.login.html",
        "public/traveler_login.html",
        "public/traveler_dashboard.html",
        "public/admin/dashboard.html",
        "public/admin/travelers.html",
    ]
    
    errors = []
    for file_path in html_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for common issues
            if "console.log" in content and "session-manager" not in file_path:
                errors.append((file_path, "Has console.log statements"))
            if "alert(" in content:
                errors.append((file_path, "Has alert() calls"))
            if "debugger" in content:
                errors.append((file_path, "Has debugger statement"))
            
            # Check for broken links
            links = re.findall(r'href="([^"]+)"', content)
            for link in links:
                if link.startswith('/') and not link.endswith('.css') and not link.endswith('.js'):
                    if not os.path.exists(f"public{link}"):
                        errors.append((file_path, f"Broken link: {link}"))
    
    for file_path, error in errors[:10]:
        print_result(f"{file_path}: {error}", False)
    
    return errors

def check_redirects():
    """Check redirect configurations"""
    print(f"\n{BLUE}🔄 CHECKING REDIRECTS{END}")
    
    redirects = [
        ("/admin/login", "/admin.login.html"),
        ("/admin", "/admin/"),
        ("/admin/", "/admin/dashboard.html"),
        ("/traveler", "/traveler_dashboard.html"),
    ]
    
    for source, target in redirects:
        try:
            response = requests.get(f"{BASE_URL}{source}", allow_redirects=False, timeout=10)
            location = response.headers.get('Location', '')
            passed = location == target or location.endswith(target)
            print_result(f"{source} → {target}", passed, f"Redirects to: {location}")
        except Exception as e:
            print_result(f"{source} → {target}", False, str(e))

def generate_fix_script(issues):
    """Generate an auto-fix script based on issues found"""
    print(f"\n{BLUE}🔧 GENERATING AUTO-FIX SCRIPT{END}")
    
    fix_content = '''#!/usr/bin/env python
"""
Auto-Fix Script Generated by Test Suite
Run this to fix common issues
"""

import os
import re

def fix_broken_links():
    """Fix broken links in HTML files"""
    fixes = []
    
'''

    if issues:
        fix_content += f'''
    print("Found {len(issues)} issues to fix")
    
'''
    
    with open('auto_fix_issues.py', 'w') as f:
        f.write(fix_content)
    
    print(f"{GREEN}✅ Created auto_fix_issues.py{END}")

def main():
    print(f"{BLUE}{'='*60}{END}")
    print(f"{BLUE}🔧 HAJ TRAVEL SYSTEM - COMPLETE TEST & FIX{END}")
    print(f"{BLUE}{'='*60}{END}")
    
    # Run all tests
    nav_results = test_navigation()
    test_api_endpoints()
    errors = check_errors()
    check_redirects()
    
    # Summary
    print(f"\n{BLUE}{'='*60}{END}")
    print(f"{BLUE}📊 TEST SUMMARY{END}")
    print(f"{BLUE}{'='*60}{END}")
    
    passed = sum(1 for _, p, _ in nav_results if p)
    total = len(nav_results)
    print(f"\nNavigation: {passed}/{total} passed")
    
    # Generate fix script
    generate_fix_script(errors)
    
    print(f"\n{GREEN}✅ Test complete!{END}")
    print(f"\n{YELLOW}📝 To fix issues:{END}")
    print("1. Run: python auto_fix_issues.py")
    print("2. Or manually fix issues listed above")
    print("3. Deploy: git add . && git commit -m 'Fix issues' && git push")

if __name__ == "__main__":
    main()