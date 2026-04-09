#!/usr/bin/env python
"""
Complete Front Page & Routes Test for Haj Travel System
Tests all public routes, static files, and page behavior
"""

import requests
import json
from urllib.parse import urljoin

BASE_URL = "https://haj-web-app-production.up.railway.app"
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'

def print_result(name, status, expected, actual):
    if status:
        print(f"{GREEN}✓ PASS{END} - {name}")
    else:
        print(f"{RED}✗ FAIL{END} - {name} (Expected: {expected}, Got: {actual})")

def test_page(url, description):
    """Test a single page"""
    try:
        response = requests.get(url, timeout=10, allow_redirects=False)
        success = response.status_code == 200
        print_result(description, success, 200, response.status_code)
        if response.status_code == 302:
            print(f"     Redirects to: {response.headers.get('Location', 'unknown')}")
        return response
    except Exception as e:
        print_result(description, False, "200", str(e))
        return None

def main():
    print(f"{BLUE}{'='*60}{END}")
    print(f"{BLUE}🌐 HAJ TRAVEL SYSTEM - FRONT PAGE & ROUTES TEST{END}")
    print(f"{BLUE}{'='*60}{END}")
    
    # ===== PUBLIC PAGES =====
    print(f"\n{YELLOW}📄 PUBLIC PAGES:{END}")
    
    public_pages = [
        ("/", "Home Page"),
        ("/index.html", "Index Page"),
        ("/admin.login.html", "Admin Login Page"),
        ("/traveler_login.html", "Traveler Login Page"),
        ("/traveler_dashboard.html", "Traveler Dashboard"),
    ]
    
    for path, name in public_pages:
        test_page(f"{BASE_URL}{path}", name)
    
    # ===== STATIC FILES =====
    print(f"\n{YELLOW}🎨 STATIC FILES:{END}")
    
    static_files = [
        ("/style.css", "Main CSS"),
        ("/admin/admin-style.css", "Admin CSS"),
        ("/js/login.js", "Login JS"),
        ("/admin/js/session-manager.js", "Session Manager JS"),
    ]
    
    for path, name in static_files:
        test_page(f"{BASE_URL}{path}", name)
    
    # ===== API ENDPOINTS =====
    print(f"\n{YELLOW}🔌 API ENDPOINTS:{END}")
    
    api_endpoints = [
        ("/health", "Health Check"),
        ("/api/health", "API Health"),
        ("/api", "API Root"),
        ("/api/check-session", "Session Check"),
        ("/api/travelers", "Travelers API"),
        ("/api/batches", "Batches API"),
        ("/api/payments", "Payments API"),
    ]
    
    for path, name in api_endpoints:
        test_page(f"{BASE_URL}{path}", name)
    
    # ===== ADMIN PAGES =====
    print(f"\n{YELLOW}👑 ADMIN PAGES:{END}")
    
    admin_pages = [
        ("/admin/dashboard.html", "Dashboard"),
        ("/admin/travelers.html", "Travelers Management"),
        ("/admin/batches.html", "Batches Management"),
        ("/admin/payments.html", "Payments Management"),
        ("/admin/invoices.html", "Invoices Management"),
        ("/admin/receipts.html", "Receipts Management"),
        ("/admin/reports.html", "Reports"),
        ("/admin/users.html", "Users Management"),
    ]
    
    for path, name in admin_pages:
        test_page(f"{BASE_URL}{path}", name)
    
    # ===== TRAVELER PAGES =====
    print(f"\n{YELLOW}👤 TRAVELER PAGES:{END}")
    
    traveler_pages = [
        ("/traveler/", "Traveler Dashboard"),
        ("/traveler/dashboard.html", "Traveler Dashboard HTML"),
    ]
    
    for path, name in traveler_pages:
        test_page(f"{BASE_URL}{path}", name)
    
    # ===== REDIRECT TESTS =====
    print(f"\n{YELLOW}🔄 REDIRECT TESTS:{END}")
    
    redirect_tests = [
        ("/admin", "/admin/"),
        ("/admin/", "/admin/dashboard.html"),
        ("/admin/login", "/admin.login.html"),
    ]
    
    for path, expected in redirect_tests:
        try:
            response = requests.get(f"{BASE_URL}{path}", allow_redirects=False, timeout=10)
            location = response.headers.get('Location', '')
            is_redirect = response.status_code in [301, 302, 303, 307, 308]
            print_result(f"Redirect: {path} → {expected}", is_redirect, "3xx", response.status_code)
        except Exception as e:
            print_result(f"Redirect: {path}", False, "3xx", str(e))
    
    # ===== SUMMARY =====
    print(f"\n{BLUE}{'='*60}{END}")
    print(f"{BLUE}✅ FRONT PAGE TEST COMPLETE{END}")
    print(f"{BLUE}{'='*60}{END}")
    
    print(f"\n{YELLOW}📝 Next Steps:{END}")
    print("1. If any pages fail, check server logs: railway logs --service haj-web-app")
    print("2. For 404 errors, verify files exist in public/ directory")
    print("3. For redirect issues, check app/server.py routes")

if __name__ == "__main__":
    main()