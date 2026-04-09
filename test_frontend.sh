#!/bin/bash
# Front Page Diagnostic Test Suite

BASE_URL="https://haj-web-app-production.up.railway.app"
echo "=========================================="
echo "🔍 FRONT PAGE DIAGNOSTIC TEST"
echo "=========================================="

# Test 1: Basic connectivity
echo -e "\n📡 TEST 1: Basic Connectivity"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" $BASE_URL/

# Test 2: Check for redirects
echo -e "\n🔄 TEST 2: Redirect Chain"
curl -Ls -o /dev/null -w "Final URL: %{url_effective}\n" $BASE_URL/

# Test 3: Check response time
echo -e "\n⏱️ TEST 3: Response Time"
curl -s -o /dev/null -w "Time: %{time_total}s\n" $BASE_URL/

# Test 4: Check for session redirect loop
echo -e "\n🔄 TEST 4: Session Check Endpoint"
curl -s -w "\nHTTP: %{http_code}\n" $BASE_URL/api/check-session

# Test 5: Check login page
echo -e "\n🔐 TEST 5: Login Page"
curl -s -o /dev/null -w "Admin Login: %{http_code}\n" $BASE_URL/admin.login.html

# Test 6: Check CSS loading
echo -e "\n🎨 TEST 6: CSS Files"
curl -s -o /dev/null -w "style.css: %{http_code}\n" $BASE_URL/style.css
curl -s -o /dev/null -w "admin-style.css: %{http_code}\n" $BASE_URL/admin/admin-style.css

# Test 7: Check JavaScript files
echo -e "\n📜 TEST 7: JavaScript Files"
curl -s -o /dev/null -w "session-manager.js: %{http_code}\n" $BASE_URL/admin/js/session-manager.js
curl -s -o /dev/null -w "login.js: %{http_code}\n" $BASE_URL/js/login.js

# Test 8: Check for console errors (via HTML content)
echo -e "\n⚠️ TEST 8: Potential JavaScript Errors"
curl -s $BASE_URL/ | grep -i "error" | head -5 || echo "No obvious errors found"

# Test 9: Check page size
echo -e "\n📦 TEST 9: Page Size"
curl -s -o /dev/null -w "Size: %{size_download} bytes\n" $BASE_URL/

# Test 10: Check for infinite loop indicators
echo -e "\n🔄 TEST 10: Loop Detection"
curl -s $BASE_URL/ | grep -c "window.location" || echo "No redirect scripts found"

# Test 11: API Health
echo -e "\n🏥 TEST 11: API Health"
curl -s $BASE_URL/health | python -m json.tool 2>/dev/null || echo "Invalid JSON response"

# Test 12: Check for CORS issues
echo -e "\n🌐 TEST 12: CORS Headers"
curl -s -I $BASE_URL/ | grep -i "access-control"

echo -e "\n=========================================="
echo "✅ TESTS COMPLETE"
echo "=========================================="