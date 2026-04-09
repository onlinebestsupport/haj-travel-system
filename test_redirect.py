import requests
import os

BASE_URL = "https://haj-web-app-production.up.railway.app"

print("=" * 60)
print("🔍 TESTING BATCHES AND PAYMENTS PAGES")
print("=" * 60)

# Login
print("\n📝 Logging in...")
login_data = {"username": "superadmin", "password": "admin123"}

session = requests.Session()
response = session.post(f"{BASE_URL}/api/login", json=login_data)

if response.status_code == 200:
    print("✅ Login successful!")
    print(f"Session cookie: {session.cookies.get('alhudha_session', 'None')[:30]}...")
else:
    print(f"❌ Login failed: {response.status_code}")
    exit()

# Test batches page
print("\n📄 Testing batches.html...")
batches_response = session.get(f"{BASE_URL}/admin/batches.html", allow_redirects=False)

print(f"Status: {batches_response.status_code}")
if batches_response.status_code == 200:
    print("✅ batches.html loads successfully!")
elif batches_response.status_code == 302:
    print(f"❌ Redirected to: {batches_response.headers.get('Location', 'Unknown')}")
else:
    print(f"❌ Status: {batches_response.status_code}")

# Test payments page
print("\n📄 Testing payments.html...")
payments_response = session.get(f"{BASE_URL}/admin/payments.html", allow_redirects=False)

print(f"Status: {payments_response.status_code}")
if payments_response.status_code == 200:
    print("✅ payments.html loads successfully!")
elif payments_response.status_code == 302:
    print(f"❌ Redirected to: {payments_response.headers.get('Location', 'Unknown')}")
else:
    print(f"❌ Status: {payments_response.status_code}")

# Test API to verify session
print("\n🔍 Testing API with same session...")
api_response = session.get(f"{BASE_URL}/api/travelers")
print(f"Status: {api_response.status_code}")

if api_response.status_code == 200:
    print("✅ API accessible with session!")
    print(f"Response preview: {api_response.text[:200]}")
else:
    print(f"❌ API returned: {api_response.text}")

print("\n" + "=" * 60)