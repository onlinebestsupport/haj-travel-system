# railway_check.py
import os
import re
import glob

print("="*80)
print("🚀 RAILWAY & POSTGRESQL DEPLOYMENT CHECKER")
print("="*80)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"
issues = []

# ====== 1. CHECK DATABASE CONNECTION STRINGS ======
print("\n📁 CHECKING DATABASE CONNECTIONS...")

# Check for hardcoded localhost in database connections
py_files = glob.glob(os.path.join(project_root, 'app', '**', '*.py'), recursive=True)

for py_file in py_files:
    with open(py_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Look for hardcoded localhost database connections
            if 'localhost' in line and ('postgres' in line or '5432' in line):
                if 'os.getenv' not in line and 'DATABASE_URL' not in line:
                    issues.append({
                        'file': os.path.relpath(py_file, project_root),
                        'line': i,
                        'issue': 'HARDCODED DATABASE - Use DATABASE_URL environment variable',
                        'severity': 'HIGH',
                        'fix': 'Replace with: DATABASE_URL = os.getenv("DATABASE_URL")'
                    })
                    print(f"❌ {os.path.basename(py_file)}:{i} - Hardcoded database connection")

# Check for proper DATABASE_URL usage
db_files = []
for py_file in py_files:
    with open(py_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'DATABASE_URL' in content:
            db_files.append(py_file)
            if 'os.getenv' not in content and 'environ.get' not in content:
                issues.append({
                    'file': os.path.relpath(py_file, project_root),
                    'line': 'N/A',
                    'issue': 'DATABASE_URL used without os.getenv - may not read from environment',
                    'severity': 'MEDIUM',
                    'fix': 'Use: DATABASE_URL = os.getenv("DATABASE_URL")'
                })
                print(f"⚠️  {os.path.basename(py_file)} - DATABASE_URL without os.getenv")

# ====== 2. CHECK FILE PATHS FOR RAILWAY COMPATIBILITY ======
print("\n📁 CHECKING FILE PATHS FOR RAILWAY...")

html_files = glob.glob(os.path.join(project_root, 'public', '**', '*.html'), recursive=True)

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for absolute paths that won't work on Railway
            if 'C:\\' in line or 'C:/' in line or 'D:\\' in line:
                issues.append({
                    'file': os.path.relpath(html_file, project_root),
                    'line': i,
                    'issue': 'ABSOLUTE PATH - Use relative paths',
                    'severity': 'HIGH',
                    'fix': f'Replace with relative path: {line.split("C:")[1].strip()}'
                })
                print(f"❌ {os.path.basename(html_file)}:{i} - Absolute path detected")

# ====== 3. CHECK FOR SQLITE (WON'T WORK ON RAILWAY) ======
print("\n📁 CHECKING FOR SQLITE USAGE...")

for py_file in py_files:
    with open(py_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'sqlite' in content.lower() or 'sqlite3' in content:
            if 'DATABASE_URL' not in content or 'postgres' not in content.lower():
                issues.append({
                    'file': os.path.relpath(py_file, project_root),
                    'line': 'N/A',
                    'issue': 'SQLITE DETECTED - Railway requires PostgreSQL',
                    'severity': 'HIGH',
                    'fix': 'Replace SQLite with PostgreSQL using DATABASE_URL'
                })
                print(f"❌ {os.path.basename(py_file)} - SQLite detected - won't work on Railway")

# ====== 4. CHECK FOR PORT CONFIGURATION ======
print("\n📁 CHECKING PORT CONFIGURATION...")

server_py = os.path.join(project_root, 'app', 'server.py')
if os.path.exists(server_py):
    with open(server_py, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check if port is read from environment
        if 'PORT =' in content and 'os.getenv' not in content:
            issues.append({
                'file': 'app/server.py',
                'line': 'N/A',
                'issue': 'PORT hardcoded - Railway assigns port dynamically',
                'severity': 'HIGH',
                'fix': 'Use: port = int(os.getenv("PORT", 8080))'
            })
            print(f"❌ app/server.py - PORT should be read from environment")
        elif 'os.getenv' in content and 'PORT' in content:
            print(f"✅ app/server.py - PORT properly configured")

# ====== 5. CHECK FOR REQUIREMENTS.TXT ======
print("\n📁 CHECKING REQUIREMENTS.TXT...")

req_file = os.path.join(project_root, 'requirements.txt')
if os.path.exists(req_file):
    with open(req_file, 'r') as f:
        content = f.read()
        
    required_packages = ['psycopg2', 'flask', 'gunicorn']
    for pkg in required_packages:
        if pkg not in content:
            issues.append({
                'file': 'requirements.txt',
                'line': 'N/A',
                'issue': f'MISSING PACKAGE: {pkg} - Required for Railway',
                'severity': 'MEDIUM',
                'fix': f'Add: {pkg}'
            })
            print(f"⚠️  requirements.txt - Missing {pkg}")
        else:
            print(f"✅ requirements.txt - Found {pkg}")
else:
    issues.append({
        'file': 'requirements.txt',
        'line': 'N/A',
        'issue': 'MISSING FILE - Railway needs requirements.txt',
        'severity': 'HIGH',
        'fix': 'Create requirements.txt with all dependencies'
    })
    print(f"❌ requirements.txt not found")

# ====== 6. CHECK FOR PROCFILE ======
print("\n📁 CHECKING PROCFILE...")

procfile = os.path.join(project_root, 'Procfile')
if os.path.exists(procfile):
    with open(procfile, 'r') as f:
        content = f.read().strip()
    
    if 'gunicorn' in content:
        print(f"✅ Procfile correctly configured: {content}")
    else:
        issues.append({
            'file': 'Procfile',
            'line': 'N/A',
            'issue': 'Should use gunicorn for production',
            'severity': 'MEDIUM',
            'fix': 'web: gunicorn app.server:app'
        })
        print(f"⚠️  Procfile should use gunicorn")
else:
    issues.append({
        'file': 'Procfile',
        'line': 'N/A',
        'issue': 'MISSING FILE - Railway needs Procfile',
        'severity': 'HIGH',
        'fix': 'Create Procfile with: web: gunicorn app.server:app'
    })
    print(f"❌ Procfile not found")

# ====== 7. CHECK FOR RUNTIME.TXT ======
print("\n📁 CHECKING RUNTIME.TXT...")

runtime = os.path.join(project_root, 'runtime.txt')
if os.path.exists(runtime):
    with open(runtime, 'r') as f:
        content = f.read().strip()
    print(f"✅ runtime.txt: {content}")
else:
    print(f"ℹ️  runtime.txt optional - Railway will use default Python version")

# ====== 8. CHECK FOR .ENV EXAMPLE ======
print("\n📁 CHECKING .ENV EXAMPLE...")

env_example = os.path.join(project_root, '.env.example')
if os.path.exists(env_example):
    with open(env_example, 'r') as f:
        content = f.read()
    if 'DATABASE_URL' in content:
        print(f"✅ .env.example has DATABASE_URL template")
    else:
        issues.append({
            'file': '.env.example',
            'line': 'N/A',
            'issue': 'Missing DATABASE_URL template',
            'severity': 'LOW',
            'fix': 'Add: DATABASE_URL=postgresql://user:pass@host:port/dbname'
        })
        print(f"⚠️  .env.example missing DATABASE_URL")
else:
    issues.append({
        'file': '.env.example',
        'line': 'N/A',
        'issue': 'MISSING FILE - Helpful for deployment',
        'severity': 'LOW',
        'fix': 'Create .env.example with DATABASE_URL template'
    })
    print(f"⚠️  .env.example not found")

# ====== 9. CHECK FOR STATIC FILE SERVING ======
print("\n📁 CHECKING STATIC FILE CONFIGURATION...")

if os.path.exists(server_py):
    with open(server_py, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'send_from_directory' in content and 'PUBLIC_DIR' in content:
        print(f"✅ Static files properly configured")
    else:
        issues.append({
            'file': 'app/server.py',
            'line': 'N/A',
            'issue': 'Static file serving may not work on Railway',
            'severity': 'MEDIUM',
            'fix': 'Use send_from_directory with proper paths'
        })
        print(f"⚠️  Check static file configuration")

# ====== 10. CHECK FOR SESSION CONFIGURATION ======
print("\n📁 CHECKING SESSION CONFIGURATION...")

if os.path.exists(server_py):
    with open(server_py, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'SESSION_COOKIE_SECURE' in content:
        print(f"✅ Session cookie security configured")
    else:
        issues.append({
            'file': 'app/server.py',
            'line': 'N/A',
            'issue': 'SESSION_COOKIE_SECURE not set - may cause issues with HTTPS',
            'severity': 'MEDIUM',
            'fix': 'Add: app.config["SESSION_COOKIE_SECURE"] = True'
        })
        print(f"⚠️  Session cookie security not configured")

# ====== SUMMARY ======
print("\n" + "="*80)
print("📊 RAILWAY DEPLOYMENT READINESS SUMMARY")
print("="*80)

severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
for issue in issues:
    severity_counts[issue['severity']] += 1

print(f"\n🔴 HIGH severity: {severity_counts['HIGH']}")
print(f"🟡 MEDIUM severity: {severity_counts['MEDIUM']}")
print(f"🟢 LOW severity: {severity_counts['LOW']}")
print(f"\n📊 Total issues: {len(issues)}")

if issues:
    print("\n🔧 ISSUES TO FIX BEFORE DEPLOYMENT:")
    for i, issue in enumerate(issues[:10], 1):
        print(f"\n{i}. [{issue['severity']}] {issue['file']}")
        print(f"   ⚠️  {issue['issue']}")
        print(f"   ✅ FIX: {issue['fix']}")
    
    if len(issues) > 10:
        print(f"\n   ... and {len(issues)-10} more issues")
else:
    print("\n✅ NO ISSUES FOUND! Your system is ready for Railway deployment!")

# ====== FIX THE CURRENT ERRORS ======
print("\n" + "="*80)
print("🔧 AUTO-FIXING COMMON ERRORS")
print("="*80)

# Fix session manager
sm_path = os.path.join(project_root, 'public', 'admin', 'js', 'session-manager.js')
if os.path.exists(sm_path):
    with open(sm_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix SESSION_TIMEOUT
    content = re.sub(r'SESSION_TIMEOUT:\s*\d+\s*\*\s*\d+\s*\*\s*\d+\s*\*\s*\d+.*', 
                     'SESSION_TIMEOUT: 30 * 60 * 1000,  // 30 minutes', content)
    
    # Add WARNING_BEFORE if missing
    if 'WARNING_BEFORE:' not in content:
        content = re.sub(r'(SESSION_TIMEOUT:.*?\n)', 
                         r'\1    WARNING_BEFORE: 2 * 60 * 1000,  // 2 minutes\n', content)
    
    # Fix startTimers
    if 'startTimers:' in content and 'this.clearTimers' not in content.split('startTimers')[1][:100]:
        content = content.replace('startTimers: function() {',
                                   'startTimers: function() {\n        this.clearTimers();')
    
    # Remove duplicate startTimers
    if content.count('startTimers:') > 1:
        parts = content.split('startTimers:')
        content = parts[0] + 'startTimers:' + ''.join(parts[1:])
    
    with open(sm_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Fixed session-manager.js")

print("\n" + "="*80)
print("✅ CHECK COMPLETE")
print("="*80)
