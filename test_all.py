# test_all.py
import requests
import json

base_url = "http://localhost:8080"
session = requests.Session()

print("="*60)
print("🔍 COMPREHENSIVE SYSTEM TEST")
print("="*60)

# Test 1: Health Check
print("\n1️⃣ Testing Health Endpoint...")
r = requests.get(f"{base_url}/api/health")
print(f"   Status: {r.status_code} - {r.json()['status']}")

# Test 2: Login URL Redirect
print("\n2️⃣ Testing Login URL Redirect...")
r = requests.get(f"{base_url}/admin/login.html", allow_redirects=False)
print(f"   Status: {r.status_code}")
print(f"   Redirects to: {r.headers.get('Location', 'None')}")

# Test 3: Login
print("\n3️⃣ Testing Login...")
r = session.post(f"{base_url}/api/login", json={
    "username": "superadmin",
    "password": "admin123"
})
print(f"   Status: {r.status_code}")
print(f"   Success: {r.json().get('authenticated', False)}")

# Test 4: Session Check
print("\n4️⃣ Testing Session...")
r = session.get(f"{base_url}/api/check-session")
print(f"   Status: {r.status_code}")
print(f"   User: {r.json().get('user', {}).get('username')}")

# Test 5: Get Users
print("\n5️⃣ Testing Users API...")
r = session.get(f"{base_url}/api/admin/users")
users = r.json().get('users', [])
print(f"   Status: {r.status_code}")
print(f"   Users found: {len(users)}")

# Test 6: Dashboard Access
print("\n6️⃣ Testing Dashboard Access...")
r = session.get(f"{base_url}/admin/dashboard.html")
print(f"   Status: {r.status_code}")
print(f"   Content-Type: {r.headers.get('Content-Type')}")

print("\n" + "="*60)
print("✅ TEST COMPLETE")
print("="*60)