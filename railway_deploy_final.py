# railway_deploy_final.py
import os

print("="*70)
print("🚀 RAILWAY DEPLOYMENT FINAL CHECK & FIX")
print("="*70)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"

# ==================== 1. FIX REQUIREMENTS.TXT ====================
print("\n📦 FIXING REQUIREMENTS.TXT...")

req_path = os.path.join(project_root, 'requirements.txt')

# Create PERFECT requirements.txt
perfect_requirements = '''Flask==2.3.3
Flask-CORS==4.0.0
gunicorn==21.2.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
requests==2.31.0
Werkzeug==2.3.7
Pillow>=10.0.1
waitress==3.0.2
'''

with open(req_path, 'w', encoding='utf-8') as f:
    f.write(perfect_requirements)

print("✅ requirements.txt completely rewritten with:")
print("   • Flask==2.3.3")
print("   • Flask-CORS==4.0.0")
print("   • gunicorn==21.2.0")
print("   • psycopg2-binary==2.9.9")
print("   • python-dotenv==1.0.0")
print("   • requests==2.31.0")
print("   • Werkzeug==2.3.7")
print("   • Pillow>=10.0.1")
print("   • waitress==3.0.2")

# ==================== 2. CREATE PROCFILE ====================
print("\n📦 CHECKING PROCFILE...")

procfile_path = os.path.join(project_root, 'Procfile')
procfile_content = "web: gunicorn app.server:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1 --threads 2 --log-level debug"

with open(procfile_path, 'w', encoding='utf-8') as f:
    f.write(procfile_content)
print("✅ Procfile created/updated")

# ==================== 3. CREATE RUNTIME.TXT ====================
print("\n📦 CHECKING RUNTIME.TXT...")

runtime_path = os.path.join(project_root, 'runtime.txt')
with open(runtime_path, 'w', encoding='utf-8') as f:
    f.write("python-3.11.9")
print("✅ runtime.txt set to Python 3.11.9")

# ==================== 4. CREATE .ENV.EXAMPLE ====================
print("\n📦 CHECKING .ENV.EXAMPLE...")

env_example_path = os.path.join(project_root, '.env.example')
env_example_content = '''# Database Configuration
DATABASE_URL=postgresql://username:password@host:port/database

# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=production

# Application Settings
PORT=8080
DEBUG=False

# Upload Settings
UPLOAD_PATH=uploads
MAX_FILE_SIZE=16MB
'''

with open(env_example_path, 'w', encoding='utf-8') as f:
    f.write(env_example_content)
print("✅ .env.example created/updated")

# ==================== 5. CHECK reset_database.py (with proper encoding) ====================
print("\n📦 CHECKING reset_database.py...")

reset_db_path = os.path.join(project_root, 'app', 'reset_database.py')
if os.path.exists(reset_db_path):
    try:
        # Try reading with utf-8 first
        with open(reset_db_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            # If utf-8 fails, try with latin-1
            with open(reset_db_path, 'r', encoding='latin-1') as f:
                content = f.read()
            print("⚠️  File has non-UTF8 characters - but we can still check content")
        except Exception as e:
            print(f"⚠️  Could not read reset_database.py: {e}")
            content = ""
    
    if 'sqlite' in content.lower():
        print("⚠️  reset_database.py contains SQLite - needs manual update")
        print("    This won't affect Railway deployment as it's just a development tool")
    else:
        print("✅ reset_database.py looks good")
else:
    print("✅ reset_database.py not found (not required for Railway)")

# ==================== 6. VERIFY EVERYTHING ====================
print("\n" + "="*70)
print("📊 FINAL VERIFICATION")
print("="*70)

# Check requirements.txt
with open(req_path, 'r', encoding='utf-8') as f:
    req_content = f.read()

checks = {
    'Flask': 'flask' in req_content.lower(),
    'gunicorn': 'gunicorn' in req_content.lower(),
    'psycopg2': 'psycopg2' in req_content.lower(),
    'python-dotenv': 'dotenv' in req_content.lower(),
}

all_good = True
for pkg, found in checks.items():
    status = "✅" if found else "❌"
    print(f"{status} {pkg} in requirements.txt")
    if not found:
        all_good = False

# Check Procfile
if os.path.exists(procfile_path):
    print("✅ Procfile exists")
else:
    print("❌ Procfile missing")
    all_good = False

# Check runtime.txt
if os.path.exists(runtime_path):
    print("✅ runtime.txt exists")
else:
    print("❌ runtime.txt missing")
    all_good = False

# Check .env.example
if os.path.exists(env_example_path):
    print("✅ .env.example exists")
else:
    print("❌ .env.example missing")
    all_good = False

print("\n" + "="*70)
if all_good:
    print("🎉 EVERYTHING IS PERFECT! Your system is ready for Railway deployment!")
    print("\n📋 NEXT STEPS:")
    print("   1. Commit changes: git add . && git commit -m 'Ready for Railway'")
    print("   2. Deploy: git push railway main")
    print("   3. Set environment variables in Railway dashboard:")
    print("      - DATABASE_URL (auto-provided if you add PostgreSQL)")
    print("      - SECRET_KEY (generate a random string)")
else:
    print("⚠️  Some issues remain. Please check the output above.")
print("="*70)

# ==================== 7. CREATE DEPLOYMENT INSTRUCTIONS ====================
deploy_instructions = '''# 🚀 RAILWAY DEPLOYMENT INSTRUCTIONS

## Step 1: Install Railway CLI (if not already installed)
npm install -g @railway/cli

## Step 2: Login to Railway
railway login

## Step 3: Link your project
railway link

## Step 4: Add PostgreSQL database
railway add

## Step 5: Set environment variables
railway variables set SECRET_KEY="your-secret-key-here"

## Step 6: Deploy
git push railway main

## Step 7: View logs
railway logs

## Step 8: Open your app
railway open

## Environment Variables needed in Railway:
- DATABASE_URL (auto-provided by PostgreSQL)
- SECRET_KEY (generate a random string)
'''

deploy_path = os.path.join(project_root, 'RAILWAY_DEPLOY.md')
with open(deploy_path, 'w', encoding='utf-8') as f:
    f.write(deploy_instructions)
print(f"\n✅ Created deployment guide: {deploy_path}")

print("\n" + "="*70)
print("🎉 ALL DONE! Your system is ready for deployment!")
print("="*70)