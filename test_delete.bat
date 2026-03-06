@echo off
echo 🔍 Testing User Delete Operation
echo ================================

echo.
echo Step 1: Logging in...
curl -s -X POST http://localhost:8080/api/login -H "Content-Type: application/json" -d "{\"username\":\"superadmin\",\"password\":\"admin123\"}" -c cookies.txt > nul
echo ✅ Logged in

echo.
echo Step 2: Creating test user...
curl -s -X POST http://localhost:8080/api/admin/users -H "Content-Type: application/json" -b cookies.txt -d "{\"username\":\"delete_test\",\"password\":\"pass123\",\"email\":\"delete@test.com\",\"role\":\"staff\"}" > result.txt
type result.txt
echo ✅ User created

echo.
echo Step 3: Deleting user...
curl -s -X DELETE http://localhost:8080/api/admin/users/8 -b cookies.txt -v
echo ✅ Delete attempted

echo.
echo Step 4: Verifying deletion...
curl -X GET http://localhost:8080/api/admin/users/8 -b cookies.txt

echo.
echo ================================
echo ✅ Test complete
pause