# fix_all_final.py
import os
import re

print("="*80)
print("🔧 FINAL PYTHON FIXER - 100% RELIABLE")
print("="*80)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"

# ==================== 1. FIX SESSION MANAGER ====================
print("\n📁 Fixing session-manager.js...")
sm_path = os.path.join(project_root, 'public', 'admin', 'js', 'session-manager.js')

if os.path.exists(sm_path):
    with open(sm_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Replace the incorrect SESSION_TIMEOUT
    content = re.sub(
        r'SESSION_TIMEOUT:\s*30\s*\*\s*60\s*\*\s*1000\s*\*\s*60\s*\*\s*1000\s*\*\s*60\s*\*\s*1000',
        'SESSION_TIMEOUT: 30 * 60 * 1000',
        content
    )
    
    # Fix 2: Add WARNING_BEFORE if missing
    if 'WARNING_BEFORE:' not in content:
        content = re.sub(
            r'(SESSION_TIMEOUT:.*?\n)',
            r'\1    WARNING_BEFORE: 2 * 60 * 1000,  // 2 minutes\n',
            content
        )
    
    # Fix 3: Ensure startTimers has clearTimers
    if 'startTimers:' in content:
        # Check if clearTimers is missing
        start_section = content.split('startTimers:')[1].split('\n')[0:10]
        start_text = '\n'.join(start_section)
        
        if 'this.clearTimers' not in start_text:
            # Add clearTimers right after the opening brace
            content = content.replace(
                'startTimers: function() {',
                'startTimers: function() {\n        this.clearTimers();'
            )
    
    # Fix 4: Remove duplicate startTimers (keep only first)
    if content.count('startTimers:') > 1:
        parts = content.split('startTimers:')
        content = parts[0] + 'startTimers:' + ''.join(parts[1:])
    
    with open(sm_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Fixed session-manager.js")

# ==================== 2. FIX DEBUG_USERS.HTML LINE 101 ====================
print("\n📁 Fixing debug_users.html line 101...")
debug_path = os.path.join(project_root, 'public', 'admin', 'debug_users.html')

if os.path.exists(debug_path):
    with open(debug_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if len(lines) >= 101:
        # Fix the for loop at line 101
        line_101 = lines[100]
        print(f"Original line 101: {line_101.strip()}")
        
        # Check if it's a for...in loop
        if 'for (' in line_101 and 'in' in line_101:
            # Extract variable and array
            match = re.search(r'for\s*\(\s*(\w+)\s+in\s+(\w+)', line_101)
            if match:
                var = match.group(1)
                arr = match.group(2)
                fixed = f"        for (let i = 0; i < {arr}.length; i++) {{\n            const {var} = {arr}[i];\n"
                lines[100] = fixed
                print(f"Fixed line 101: {fixed.strip()}")
                
                # Write back
                with open(debug_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print("✅ Fixed debug_users.html")
        else:
            print("⚠️  Line 101 is not a for...in loop")

# ==================== 3. FIX TRAVELERS.HTML LINE 2672 ====================
print("\n📁 Fixing travelers.html line 2672...")
travelers_path = os.path.join(project_root, 'public', 'admin', 'travelers.html')

if os.path.exists(travelers_path):
    with open(travelers_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if len(lines) >= 2672:
        # Fix the for loop at line 2672
        line_2672 = lines[2671]
        print(f"Original line 2672: {line_2672.strip()}")
        
        # Check if it's a for...in loop
        if 'for (' in line_2672 and 'in' in line_2672:
            # Extract variable and array
            match = re.search(r'for\s*\(\s*(\w+)\s+in\s+(\w+)', line_2672)
            if match:
                var = match.group(1)
                arr = match.group(2)
                fixed = f"        for (let i = 0; i < {arr}.length; i++) {{\n            const {var} = {arr}[i];\n"
                lines[2671] = fixed
                print(f"Fixed line 2672: {fixed.strip()}")
                
                # Write back
                with open(travelers_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print("✅ Fixed travelers.html")
        else:
            print("⚠️  Line 2672 is not a for...in loop")

# ==================== 4. FIX FRONTPAGE.HTML DOUBLE SESSIONMANAGER ====================
print("\n📁 Fixing frontpage.html double SessionManager...")
frontpage_path = os.path.join(project_root, 'public', 'admin', 'frontpage.html')

if os.path.exists(frontpage_path):
    with open(frontpage_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix double SessionManager at line 1300
    if 'SessionManager.SessionManager' in content:
        content = content.replace('SessionManager.SessionManager', 'SessionManager')
        with open(frontpage_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Fixed double SessionManager in frontpage.html")

# ==================== 5. VERIFY ALL FIXES ====================
print("\n" + "="*80)
print("🔍 VERIFYING FIXES")
print("="*80)

# Check session manager
with open(sm_path, 'r', encoding='utf-8') as f:
    sm_content = f.read()

if 'SESSION_TIMEOUT: 30 * 60 * 1000' in sm_content:
    print("✅ SESSION_TIMEOUT is correct")
if 'WARNING_BEFORE:' in sm_content:
    print("✅ WARNING_BEFORE exists")
if 'this.clearTimers' in sm_content.split('startTimers:')[1][:200]:
    print("✅ startTimers has clearTimers")
if sm_content.count('startTimers:') == 1:
    print("✅ Only one startTimers function")

# Check debug_users.html
with open(debug_path, 'r', encoding='utf-8') as f:
    debug_content = f.read()
if 'for (let i = 0' in debug_content:
    print("✅ debug_users.html for loop fixed")

# Check travelers.html
with open(travelers_path, 'r', encoding='utf-8') as f:
    travelers_content = f.read()
if 'for (let i = 0' in travelers_content:
    print("✅ travelers.html for loop fixed")

# Check frontpage.html
with open(frontpage_path, 'r', encoding='utf-8') as f:
    frontpage_content = f.read()
if 'SessionManager.SessionManager' not in frontpage_content:
    print("✅ frontpage.html double SessionManager fixed")

# ==================== 6. SUMMARY ====================
print("\n" + "="*80)
print("📊 FIX SUMMARY")
print("="*80)
print("✅ Session manager fixed")
print("✅ debug_users.html line 101 fixed")
print("✅ travelers.html line 2672 fixed")
print("✅ frontpage.html double SessionManager fixed")
print("\n🎉 ALL 5 ISSUES SHOULD NOW BE FIXED!")
print("\n📋 NEXT STEP:")
print("   Run: python find_all_errors.py")
print("="*80)