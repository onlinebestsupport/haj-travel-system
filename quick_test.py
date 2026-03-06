# quick_test.py
import requests
import json

print("="*50)
print("🔍 QUICK LOGIN TEST")
print("="*50)

url = "http://localhost:8080/api/login"
data = {
    "username": "superadmin",
    "password": "admin123"
}

print(f"📡 Sending request to {url}")
print(f"📝 Data: {data}")

try:
    response = requests.post(url, json=data)
    print(f"\n✅ Status Code: {response.status_code}")
    print(f"📡 Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("\n✅ LOGIN SUCCESSFUL!")
        print(f"🍪 Cookies: {response.cookies.get_dict()}")
    else:
        print("\n❌ Login failed")
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to server! Is it running?")
except Exception as e:
    print(f"❌ Error: {e}")

print("="*50)