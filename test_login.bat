@echo off
echo ==========================================
echo TESTING LOGIN/LOGOUT
echo ==========================================

echo.
echo 1. Testing Login...
curl -X POST https://haj-web-app-production.up.railway.app/api/login -H "Content-Type: application/json" -d "{\"username\":\"superadmin\",\"password\":\"admin123\"}" -c cookies.txt

echo.
echo.
echo 2. Checking Session...
curl -b cookies.txt https://haj-web-app-production.up.railway.app/api/check-session

echo.
echo.
echo 3. Accessing Protected Endpoint (Travelers)...
curl -b cookies.txt https://haj-web-app-production.up.railway.app/api/travelers

echo.
echo.
echo 4. Logging Out...
curl -X POST https://haj-web-app-production.up.railway.app/api/logout -b cookies.txt

echo.
echo.
echo 5. Checking Session After Logout...
curl -b cookies.txt https://haj-web-app-production.up.railway.app/api/check-session

echo.
echo.
echo ==========================================
echo TEST COMPLETE
echo ==========================================
pause