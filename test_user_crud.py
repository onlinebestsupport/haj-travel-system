# test_user_crud_fixed.py
import requests
import json
import time

base_url = "http://localhost:8080"

print("="*60)
print("🧪 TESTING USER CRUD OPERATIONS")
print("="*60)

# Login
session = requests.Session()
login_data = {"username": "superadmin", "password": "admin123"}
response = session.post(f"{base_url}/api/login", json=login_data)

if response.status_code != 200:
    print(f"❌ Login failed: {response.status_code}")
    exit()

print("✅ Login successful")

# 1. LIST all users
print("\n📋 1. LISTING ALL USERS...")
response = session.get(f"{base_url}/api/admin/users")
users = response.json()
print(f"   Found {len(users.get('users', []))} users")

# 2. CREATE a new user
print("\n➕ 2. CREATING NEW USER...")
timestamp = int(time.time())
new_user = {
    "username": f"testuser_{timestamp}",
    "password": "password123",
    "email": f"test{timestamp}@example.com",
    "full_name": "Test User",
    "role": "staff",
    "phone": "9876543210",
    "department": "Testing",
    "is_active": True
}

response = session.post(f"{base_url}/api/admin/users", json=new_user)
result = response.json()
print(f"   Response: {json.dumps(result, indent=2)}")

if result.get('success'):
    user_id = result.get('user_id')
    print(f"   ✅ User created with ID: {user_id}")
    
    # 3. GET the created user
    print(f"\n👁️ 3. GETTING USER {user_id}...")
    response = session.get(f"{base_url}/api/admin/users/{user_id}")
    print(f"   User data: {json.dumps(response.json(), indent=2)}")
    
    # 4. UPDATE the user
    print(f"\n✏️ 4. UPDATING USER {user_id}...")
    update_data = {
        "email": f"updated{timestamp}@example.com",
        "full_name": "Updated Test User",
        "role": "manager",
        "department": "Updated Dept"
    }
    response = session.put(f"{base_url}/api/admin/users/{user_id}", json=update_data)
    print(f"   Update result: {response.json()}")
    
    # 5. TOGGLE status
    print(f"\n🔄 5. TOGGLING USER {user_id} STATUS...")
    response = session.post(f"{base_url}/api/admin/users/{user_id}/toggle", json={})
    print(f"   Toggle result: {response.json()}")
    
    # 6. DELETE the user (FIXED)
    print(f"\n🗑️ 6. DELETING USER {user_id}...")
    response = session.delete(f"{base_url}/api/admin/users/{user_id}")
    
    # Check if response has content before parsing JSON
    if response.status_code == 200:
        if response.text:
            try:
                result = response.json()
                print(f"   Delete result: {result}")
            except:
                print(f"   ✅ User deleted successfully (no content response)")
        else:
            print(f"   ✅ User deleted successfully (empty response)")
    else:
        print(f"   ❌ Delete failed with status: {response.status_code}")
    
    # 7. Verify deletion
    print(f"\n✅ 7. VERIFYING DELETION...")
    response = session.get(f"{base_url}/api/admin/users/{user_id}")
    if response.status_code == 404:
        print("   ✅ User successfully deleted")
    else:
        print("   ❌ User still exists")

print("\n" + "="*60)
print("✅ TEST COMPLETE")
print("="*60)