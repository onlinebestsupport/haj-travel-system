# test_users_final.py
import requests

base_url = "http://localhost:8080"

# Login first
session = requests.Session()
login = session.post(f"{base_url}/api/login", json={
    "username": "superadmin",
    "password": "admin123"
})

print(f"Login Status: {login.status_code}")
print(f"Login Response: {login.json()}")

# Check session
session_check = session.get(f"{base_url}/api/check-session")
print(f"\nSession Status: {session_check.status_code}")
print(f"Session Data: {session_check.json()}")

# Get users
users = session.get(f"{base_url}/api/admin/users")
print(f"\nUsers Status: {users.status_code}")
print(f"Users Data: {users.json()}")