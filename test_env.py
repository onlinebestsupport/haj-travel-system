import os
from dotenv import load_dotenv

print("Current directory:", os.getcwd())
print("Checking for .env file...")

if os.path.exists('.env'):
    print("✅ .env file found")
    print("File contents:")
    with open('.env', 'r') as f:
        print(f.read())
else:
    print("❌ .env file NOT found!")

print("\nLoading .env file...")
load_dotenv()

database_url = os.getenv('DATABASE_URL')
print(f"DATABASE_URL after loading: {database_url}")

if database_url and database_url != 'None':
    print("✅ DATABASE_URL loaded successfully!")
else:
    print("❌ DATABASE_URL not loaded!")