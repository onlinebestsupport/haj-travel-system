# test_login_now.py
import requests
import json

base_url = "http://localhost:8080"

print("="*50)
print("🔐 TESTING LOGIN")
print("="*50)

# Test login
login_data = {
    "username": "superadmin",
    "password": "admin123",
    "remember_me": False
}

print(f"\n📝 Attempting login with: {login_data['username']}")

session = requests.Session()
response = session.post(f"{base_url}/api/login", json=login_data)

print(f"📡 Status: {response.status_code}")
print(f"📡 Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    print("\n✅ Login successful!")
    
    # Check session
    session_response = session.get(f"{base_url}/api/check-session")
    print(f"\n📡 Session check: {json.dumps(session_response.json(), indent=2)}")
    
    # Show cookies
    print(f"\n🍪 Cookies: {session.cookies.get_dict()}")
    
    # Try to access dashboard
    dashboard = session.get(f"{base_url}/admin/dashboard.html")
    print(f"\n📡 Dashboard access: {dashboard.status_code}")
else:
    print("\n❌ Login failed!")

print("\n" + "="*50)