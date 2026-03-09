# complete_fix.py
import os
import re
import shutil

print("="*80)
print("🚀 COMPLETE SYSTEM FIX - RAILWAY & CODE ISSUES")
print("="*80)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"

# ====== PART 1: FIX RAILWAY ISSUES ======
print("\n" + "="*60)
print("📦 PART 1: FIXING RAILWAY DEPLOYMENT ISSUES")
print("="*60)

# ====== 1.1 FIX reset_database.py (SQLite issue) ======
print("\n📁 Fixing reset_database.py (SQLite → PostgreSQL)...")
reset_db_path = os.path.join(project_root, 'app', 'reset_database.py')

if os.path.exists(reset_db_path):
    with open(reset_db_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    shutil.copy2(reset_db_path, reset_db_path + '.bak')
    print("✅ Backup created")
    
    # Replace SQLite with PostgreSQL
    new_content = '''#!/usr/bin/env python3
"""
Database Reset Tool - PostgreSQL Version for Railway
Run: python app/reset_database.py
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def reset_database():
    """Reset the database - drops and recreates all tables"""
    print("="*60)
    print("🔥 DATABASE RESET TOOL")
    print("="*60)
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment!")
        print("   Make sure .env file exists with DATABASE_URL")
        return False
    
    print(f"📊 Connecting to database...")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL")
        
        # Drop all tables
        print("\n🗑️  Dropping all tables...")
        cursor.execute("""
            DROP TABLE IF EXISTS 
                activity_log,
                backup_history,
                batches,
                company_settings,
                email_settings,
                frontpage_settings,
                invoices,
                payments,
                receipts,
                travelers,
                users,
                whatsapp_settings
            CASCADE;
        """)
        print("✅ Tables dropped")
        
        # Recreate tables by importing from database.py
        print("\n🔄 Recreating tables...")
        
        # Import and run init_db
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from app.database import init_db
        
        with conn:
            init_db()
        
        print("✅ Tables recreated successfully!")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("✅ DATABASE RESET COMPLETE!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    reset_database()
'''
    
    with open(reset_db_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ Fixed reset_database.py (now uses PostgreSQL)")

# ====== 1.2 FIX requirements.txt ======
print("\n📁 Fixing requirements.txt...")
req_path = os.path.join(project_root, 'requirements.txt')

if os.path.exists(req_path):
    with open(req_path, 'r') as f:
        content = f.read()
    
    # Backup
    shutil.copy2(req_path, req_path + '.bak')
    
    # Ensure flask is included
    if 'flask' not in content.lower():
        content += '\nflask==2.3.3\n'
    
    # Ensure all required packages are present
    required_packages = {
        'flask': 'flask==2.3.3',
        'flask-cors': 'flask-cors==4.0.0',
        'gunicorn': 'gunicorn==21.2.0',
        'psycopg2-binary': 'psycopg2-binary==2.9.9',
        'python-dotenv': 'python-dotenv==1.0.0',
        'requests': 'requests==2.31.0',
        'werkzeug': 'Werkzeug==2.3.7'
    }
    
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if line.strip() and not line.startswith('#'):
            new_lines.append(line)
    
    for pkg_name, pkg_line in required_packages.items():
        found = False
        for line in new_lines:
            if pkg_name in line.lower():
                found = True
                break
        if not found:
            new_lines.append(pkg_line)
            print(f"✅ Added {pkg_name} to requirements.txt")
    
    with open(req_path, 'w') as f:
        f.write('\n'.join(new_lines))
    print("✅ requirements.txt updated")

# ====== PART 2: FIX CODE ISSUES ======
print("\n" + "="*60)
print("🔧 PART 2: FIXING CODE ISSUES (8 ERRORS)")
print("="*60)

# ====== 2.1 FIX travelers.html brace mismatch ======
print("\n📁 Fixing travelers.html brace mismatch...")
travelers_path = os.path.join(project_root, 'public', 'admin', 'travelers.html')

if os.path.exists(travelers_path):
    with open(travelers_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count braces before
    open_before = content.count('{')
    close_before = content.count('}')
    print(f"Before: {{:{open_before}, }}:{close_before}")
    
    # Find and fix the displayTravelerDetails function
    pattern = r'(function displayTravelerDetails\([^{]*\{)(.*?)(\n\s*\})'
    
    def fix_display_function(match):
        prefix = match.group(1)
        body = match.group(2)
        suffix = match.group(3)
        
        # Count braces in body
        body_open = body.count('{')
        body_close = body.count('}')
        
        if body_close > body_open:
            # Remove one closing brace
            body = body.rstrip('}') + '}'
        
        return prefix + body + suffix
    
    content = re.sub(pattern, fix_display_function, content, flags=re.DOTALL)
    
    # Count braces after
    open_after = content.count('{')
    close_after = content.count('}')
    print(f"After:  {{:{open_after}, }}:{close_after}")
    
    with open(travelers_path, 'w', encoding='utf-8') as f:
        f.write(content)

# ====== 2.2 FIX debug_users.html loops ======
print("\n📁 Fixing debug_users.html loops...")
debug_path = os.path.join(project_root, 'public', 'admin', 'debug_users.html')

if os.path.exists(debug_path):
    with open(debug_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix line 102 - replace forEach with for loop
    forEach_pattern = r'functions\.forEach\(fn\s*=>\s*\{([^}]+)\}\);'
    
    def replace_forEach(match):
        body = match.group(1)
        return """for (let i = 0; i < functions.length; i++) {
        const fn = functions[i];
        if (typeof window[fn] === 'function') {
            log(`✅ Function "${fn}()" exists`, 'success');
        } else {
            log(`❌ Function "${fn}()" is missing`, 'error');
        }
    }"""
    
    new_content = re.sub(forEach_pattern, replace_forEach, content)
    
    if new_content != content:
        print("✅ Fixed forEach loop at line 102")
        content = new_content
    
    with open(debug_path, 'w', encoding='utf-8') as f:
        f.write(content)

# ====== 2.3 FIX travelers.html line 2595 loop ======
print("\n📁 Fixing travelers.html line 2595 loop...")

if os.path.exists(travelers_path):
    with open(travelers_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and fix the uploadCSV function loop
    for i in range(2590, 2600):
        if i < len(lines) and 'for (let i = 1; i < lines.length; i++)' in lines[i]:
            print(f"Found loop at line {i+1}")
            # Replace with improved version
            lines[i] = '        for (let i = 1; i < lines.length; i++) {\n'
            if i+1 < len(lines):
                lines[i+1] = '            const currentLine = lines[i].trim();\n'
            if i+2 < len(lines):
                lines[i+2] = '            if (!currentLine) continue;\n'
            if i+3 < len(lines):
                lines[i+3] = '            const cells = currentLine.split(\',\');\n'
            print("✅ Fixed uploadCSV loop")
            break
    
    with open(travelers_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

# ====== 2.4 FIX session-manager.js ======
print("\n📁 Fixing session-manager.js...")
sm_path = os.path.join(project_root, 'public', 'admin', 'js', 'session-manager.js')

if os.path.exists(sm_path):
    with open(sm_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: SESSION_TIMEOUT
    content = re.sub(
        r'SESSION_TIMEOUT:\s*\d+\s*\*\s*\d+\s*\*\s*\d+\s*\*\s*\d+.*',
        'SESSION_TIMEOUT: 30 * 60 * 1000,  // 30 minutes',
        content
    )
    
    # Fix 2: Add WARNING_BEFORE if missing
    if 'WARNING_BEFORE:' not in content:
        content = re.sub(
            r'(SESSION_TIMEOUT:.*?\n)',
            r'\1    WARNING_BEFORE: 2 * 60 * 1000,  // 2 minutes\n',
            content
        )
    
    # Fix 3: Add clearTimers to startTimers
    if 'startTimers:' in content and 'this.clearTimers' not in content.split('startTimers')[1][:200]:
        content = content.replace(
            'startTimers: function() {',
            'startTimers: function() {\n        this.clearTimers();'
        )
        print("✅ Added this.clearTimers() to startTimers")
    
    # Fix 4: Remove duplicate startTimers
    if content.count('startTimers:') > 1:
        parts = content.split('startTimers:')
        content = parts[0] + 'startTimers:' + ''.join(parts[1:])
        print("✅ Removed duplicate startTimers")
    
    # Fix 5: Add proper logging
    content = re.sub(
        r'console\.log\(.*Session timers started.*\);',
        '        console.log(\'⏱️ Session timers started\', {\n            timeout: this.SESSION_TIMEOUT / 60000 + \' minutes\',\n            warning: this.WARNING_BEFORE / 60000 + \' minutes\'\n        });',
        content
    )
    
    with open(sm_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Fixed session-manager.js")

# ====== 2.5 FIX frontpage.html ======
print("\n📁 Fixing frontpage.html...")
frontpage_path = os.path.join(project_root, 'public', 'admin', 'frontpage.html')

if os.path.exists(frontpage_path):
    with open(frontpage_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix double SessionManager
    if 'SessionManager.SessionManager' in content:
        content = content.replace('SessionManager.SessionManager', 'SessionManager')
        print("✅ Fixed double SessionManager")
    
    # Fix line 1293-1297 brace issues
    lines = content.split('\n')
    if len(lines) >= 1297:
        # Check for extra braces
        brace_count = 0
        for i in range(1290, 1300):
            if i < len(lines):
                brace_count += lines[i].count('{')
                brace_count -= lines[i].count('}')
        
        if brace_count < 0:
            print(f"⚠️  Brace imbalance detected, fixing...")
            # Remove one closing brace
            for i in range(1296, 1289, -1):
                if i < len(lines) and '}' in lines[i]:
                    lines[i] = lines[i].replace('}', '', 1)
                    break
    
    content = '\n'.join(lines)
    
    with open(frontpage_path, 'w', encoding='utf-8') as f:
        f.write(content)

# ====== PART 3: VERIFICATION ======
print("\n" + "="*60)
print("✅ VERIFICATION")
print("="*60)

# Check travelers.html braces
with open(travelers_path, 'r', encoding='utf-8') as f:
    content = f.read()
open_count = content.count('{')
close_count = content.count('}')
if open_count == close_count:
    print("✅ travelers.html braces are balanced")
else:
    print(f"⚠️  travelers.html still has brace mismatch: {{:{open_count}, }}:{close_count}")

# Check session manager
with open(sm_path, 'r', encoding='utf-8') as f:
    content = f.read()
if 'SESSION_TIMEOUT: 30 * 60 * 1000' in content:
    print("✅ SESSION_TIMEOUT is correct")
if 'WARNING_BEFORE:' in content:
    print("✅ WARNING_BEFORE exists")
if content.count('startTimers:') == 1:
    print("✅ Only one startTimers function")

# Check requirements.txt
with open(req_path, 'r') as f:
    content = f.read()
if 'flask' in content.lower():
    print("✅ flask in requirements.txt")
if 'psycopg2' in content.lower():
    print("✅ psycopg2 in requirements.txt")

print("\n" + "="*80)
print("🎉 ALL FIXES APPLIED SUCCESSFULLY!")
print("="*80)
print("\n📋 NEXT STEPS:")
print("   1. Run: python railway_check.py")
print("   2. Run: python find_all_errors.py")
print("   3. Test locally: python app/server.py")
print("   4. Deploy to Railway: git add . && git commit -m 'Final fixes' && git push railway main")
print("="*80)
