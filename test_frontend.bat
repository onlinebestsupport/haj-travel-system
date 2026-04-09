@echo off
setlocal enabledelayedexpansion
set BASE_URL=https://haj-web-app-production.up.railway.app

echo ==========================================
echo 🔍 FRONT PAGE DIAGNOSTIC TEST
echo ==========================================

echo.
echo 📡 TEST 1: Home Page Status
curl -s -o nul -w "Status: %%{http_code}\n" %BASE_URL%/

echo.
echo 🔄 TEST 2: Login Page Status
curl -s -o nul -w "Admin Login: %%{http_code}\n" %BASE_URL%/admin.login.html

echo.
echo 🔄 TEST 3: Session Check API
curl -s %BASE_URL%/api/check-session

echo.
echo 🔄 TEST 4: Health Check
curl -s %BASE_URL%/health

echo.
echo ==========================================
echo ✅ TESTS COMPLETE
echo ==========================================
pause