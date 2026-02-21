import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"
session = requests.Session()

def print_result(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"      {details}")

def test_login():
    try:
        data = {"username": "superadmin", "password": "admin123"}
        res = session.post(f"{BASE_URL}/api/login", json=data)
        if res.status_code == 200 and res.json().get('success'):
            return True, "Login successful"
        return False, f"Login failed: {res.text}"
    except Exception as e:
        return False, str(e)

def test_api(endpoint, expected_status=200):
    try:
        res = session.get(f"{BASE_URL}{endpoint}")
        if res.status_code == expected_status:
            try:
                data = res.json()
                return True, f"Status {res.status_code}, Data received"
            except:
                return True, f"Status {res.status_code}"
        return False, f"Status {res.status_code}"
    except Exception as e:
        return False, str(e)

def test_post(endpoint, data):
    try:
        res = session.post(f"{BASE_URL}{endpoint}", json=data)
        if res.status_code in [200, 201]:
            return True, f"Success: {res.text[:100]}"
        return False, f"Failed: {res.status_code} - {res.text[:100]}"
    except Exception as e:
        return False, str(e)

def main():
    print("\n" + "="*60)
    print("🔍 HAJ TRAVEL SYSTEM DASHBOARD TESTER")
    print("="*60 + "\n")
    
    # Test 1: Server Connection
    print("📡 Testing Server Connection...")
    success, details = test_api("/api/batches")
    print_result("Server Connection", success, details)
    
    # Test 2: Login
    print("\n🔐 Testing Login...")
    success, details = test_login()
    print_result("Admin Login", success, details)
    
    if success:
        # Test 3: Dashboard Stats
        print("\n📊 Testing Dashboard APIs...")
        success, details = test_api("/api/admin/dashboard/stats")
        print_result("Dashboard Stats", success, details)
        
        # Test 4: Batches API
        success, details = test_api("/api/batches")
        print_result("Batches API", success, details)
        
        # Test 5: Travelers API
        success, details = test_api("/api/travelers")
        print_result("Travelers API", success, details)
        
        # Test 6: Payments API
        success, details = test_api("/api/payments")
        print_result("Payments API", success, details)
        
        # Test 7: Users API
        success, details = test_api("/api/admin/users")
        print_result("Users API", success, details)
        
        # Test 8: Create Batch (POST)
        print("\n➕ Testing POST Operations...")
        test_batch = {
            "batch_name": f"Test Batch {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "total_seats": 100,
            "price": 500000,
            "status": "Open"
        }
        success, details = test_post("/api/batches", test_batch)
        print_result("Create Batch", success, details)
        
        # Test 9: Create Traveler (POST)
        test_traveler = {
            "first_name": "Test",
            "last_name": "User",
            "batch_id": 1,
            "passport_no": f"TEST{datetime.now().strftime('%m%d%H%M')}",
            "mobile": "9876543210",
            "pin": "1234"
        }
        success, details = test_post("/api/travelers", test_traveler)
        print_result("Create Traveler", success, details)
    
    print("\n" + "="*60)
    print("✅ TESTING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()