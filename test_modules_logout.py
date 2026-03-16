import requests
import time
from datetime import datetime

BASE_URL = "https://haj-web-app-production.up.railway.app"
LOGIN_URL = f"{BASE_URL}/api/login"
CHECK_SESSION_URL = f"{BASE_URL}/api/check-session"
LOGOUT_URL = f"{BASE_URL}/api/logout"

# Admin modules to test
MODULES = [
    {"name": "Dashboard", "url": f"{BASE_URL}/admin/dashboard"},
    {"name": "Travelers", "url": f"{BASE_URL}/admin/travelers"},
    {"name": "Batches", "url": f"{BASE_URL}/admin/batches"},
    {"name": "Payments", "url": f"{BASE_URL}/admin/payments"},
    {"name": "Invoices", "url": f"{BASE_URL}/admin/invoices"},
    {"name": "Receipts", "url": f"{BASE_URL}/admin/receipts"},
    {"name": "Reports", "url": f"{BASE_URL}/admin/reports"},
    {"name": "Users", "url": f"{BASE_URL}/admin/users"},
    {"name": "Backup", "url": f"{BASE_URL}/admin/backup"},
    {"name": "Email", "url": f"{BASE_URL}/admin/email"},
    {"name": "WhatsApp", "url": f"{BASE_URL}/admin/whatsapp"},
    {"name": "Frontpage", "url": f"{BASE_URL}/admin/frontpage"},
]

# Credentials
credentials = {"username": "superadmin", "password": "admin123"}

print("=" * 70)
print("🧪 HAJ TRAVEL SYSTEM - MODULE LOGOUT TESTER")
print("=" * 70)

def test_module_logout(module_name, module_url):
    """Test if logout function works in a module"""
    session = requests.Session()
    
    print(f"\n📋 Testing {module_name}...")
    
    # Step 1: Login
    login_resp = session.post(LOGIN_URL, json=credentials)
    if login_resp.status_code != 200:
        print(f"  ❌ Login failed: {login_resp.status_code}")
        return False
    
    print(f"  ✅ Login successful")
    
    # Step 2: Access the module page
    module_resp = session.get(module_url)
    if module_resp.status_code == 200:
        print(f"  ✅ Module accessible (Status: {module_resp.status_code})")
    else:
        print(f"  ❌ Module not accessible (Status: {module_resp.status_code})")
        return False
    
    # Step 3: Check if logout button exists in the HTML
    html_content = module_resp.text.lower()
    logout_indicators = [
        'logout', 'sign out', 'sign-out', 'signout',
        'onclick="logout()"', 'href="/api/logout"',
        'fa-sign-out-alt', 'fa-sign-out'
    ]
    
    found_indicators = []
    for indicator in logout_indicators:
        if indicator in html_content:
            found_indicators.append(indicator)
    
    if found_indicators:
        print(f"  ✅ Logout UI elements found: {', '.join(found_indicators[:3])}")
    else:
        print(f"  ❌ No logout UI elements found in {module_name}")
        return False
    
    # Step 4: Test logout via API
    logout_resp = session.post(LOGOUT_URL)
    if logout_resp.status_code == 200:
        print(f"  ✅ Logout API call successful")
    else:
        print(f"  ❌ Logout API failed: {logout_resp.status_code}")
        return False
    
    # Step 5: Verify session is cleared
    check_resp = session.get(CHECK_SESSION_URL)
    if check_resp.status_code == 200:
        session_data = check_resp.json()
        if not session_data.get('authenticated'):
            print(f"  ✅ Session properly cleared after logout")
        else:
            print(f"  ❌ Session still active after logout")
            return False
    else:
        print(f"  ❌ Session check failed: {check_resp.status_code}")
        return False
    
    # Step 6: Try to access module again (should redirect to login)
    after_logout_resp = session.get(module_url, allow_redirects=False)
    if after_logout_resp.status_code in [301, 302, 303, 307]:
        redirect_url = after_logout_resp.headers.get('Location', '')
        if 'login' in redirect_url.lower():
            print(f"  ✅ Module redirects to login page after logout")
        else:
            print(f"  ⚠️ Module redirects to {redirect_url}")
    elif after_logout_resp.status_code == 200:
        # Check if it's actually the login page
        if 'login' in after_logout_resp.text.lower():
            print(f"  ✅ Module shows login page after logout (Status 200)")
        else:
            print(f"  ❌ Module still accessible after logout (Status 200)")
            return False
    else:
        print(f"  ⚠️ Unexpected status after logout: {after_logout_resp.status_code}")
    
    return True

def test_session_manager_in_modules():
    """Check if session-manager.js is properly included in all modules"""
    print("\n" + "=" * 70)
    print("📁 TESTING SESSION-MANAGER.JS INCLUSION")
    print("=" * 70)
    
    session = requests.Session()
    session.post(LOGIN_URL, json=credentials)
    
    results = []
    
    for module in MODULES:
        print(f"\n📋 Checking {module['name']}...")
        resp = session.get(module['url'])
        
        if resp.status_code != 200:
            print(f"  ❌ Cannot access {module['name']}")
            continue
        
        html = resp.text
        
        # Check for session-manager.js
        if 'session-manager.js' in html:
            print(f"  ✅ session-manager.js included")
        else:
            print(f"  ❌ session-manager.js MISSING!")
            results.append(f"{module['name']}: missing session-manager.js")
        
        # Check for SessionManager initialization
        if 'SessionManager.initPage' in html:
            print(f"  ✅ SessionManager.initPage() called")
        else:
            print(f"  ⚠️ SessionManager.initPage() not found")
        
        # Check for logout button
        if 'logout()' in html or 'onclick="logout"' in html:
            print(f"  ✅ Logout button/function present")
        else:
            print(f"  ❌ Logout button/function MISSING!")
            results.append(f"{module['name']}: missing logout button")
    
    return results

def test_api_protection():
    """Test if API endpoints require authentication"""
    print("\n" + "=" * 70)
    print("🔒 TESTING API PROTECTION")
    print("=" * 70)
    
    api_endpoints = [
        "/api/travelers",
        "/api/batches",
        "/api/payments",
        "/api/invoices",
        "/api/receipts",
        "/api/users",
        "/api/reports",
        "/api/backup",
    ]
    
    # Test without session
    session = requests.Session()
    print("\n📋 Testing API endpoints WITHOUT authentication:")
    
    for endpoint in api_endpoints:
        url = f"{BASE_URL}{endpoint}"
        resp = session.get(url)
        if resp.status_code == 401:
            print(f"  ✅ {endpoint}: properly protected (401)")
        else:
            print(f"  ❌ {endpoint}: returns {resp.status_code} (should be 401)")
    
    # Test with session
    session.post(LOGIN_URL, json=credentials)
    print("\n📋 Testing API endpoints WITH authentication:")
    
    for endpoint in api_endpoints:
        url = f"{BASE_URL}{endpoint}"
        resp = session.get(url)
        if resp.status_code == 200:
            print(f"  ✅ {endpoint}: accessible (200)")
        else:
            print(f"  ⚠️ {endpoint}: returns {resp.status_code}")

def run_all_tests():
    """Run all module tests"""
    
    # Test 1: Module logout functionality
    print("\n" + "=" * 70)
    print("🧪 TEST 1: MODULE LOGOUT FUNCTIONALITY")
    print("=" * 70)
    
    module_results = []
    for module in MODULES:
        success = test_module_logout(module['name'], module['url'])
        module_results.append((module['name'], success))
        time.sleep(1)  # Be nice to the server
    
    # Test 2: Session manager inclusion
    missing_items = test_session_manager_in_modules()
    
    # Test 3: API protection
    test_api_protection()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    print("\n📋 Module Logout Results:")
    all_passed = True
    for name, passed in module_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {name}")
        if not passed:
            all_passed = False
    
    if missing_items:
        print("\n⚠️ Issues Found:")
        for item in missing_items:
            print(f"  ❌ {item}")
            all_passed = False
    else:
        print("\n✅ All modules have proper session manager inclusion")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL MODULES PASSED! Logout functionality is working correctly.")
    else:
        print("⚠️ Some modules have issues. Check the details above.")
    
    print("\n📝 Manual Testing Checklist:")
    print("  1. Login as superadmin")
    print("  2. Visit each module page")
    print("  3. Click the logout button")
    print("  4. Verify you're redirected to login page")
    print("  5. Try to go back to the module (should redirect to login)")

if __name__ == "__main__":
    run_all_tests()