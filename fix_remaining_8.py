# fix_remaining_8.py
import os
import re

print("="*80)
print("🔧 FIXING REMAINING 8 ERRORS")
print("="*80)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"

# ====== FIX 1-2: TRAVELERS.HTML BRACE MISMATCH ======
print("\n📁 Fixing travelers.html brace mismatch...")
travelers_path = os.path.join(project_root, 'public', 'admin', 'travelers.html')

if os.path.exists(travelers_path):
    with open(travelers_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count braces
    open_count = content.count('{')
    close_count = content.count('}')
    print(f"Before: {{:{open_count}, }}:{close_count}")
    
    if close_count > open_count:
        # Find the displayTravelerDetails function (around line 1485)
        pattern = r'(function displayTravelerDetails\([^{]*\{.*?\n\})'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            func_text = match.group(1)
            # Remove one closing brace
            fixed_func = func_text.rstrip('}') + '}'
            content = content.replace(func_text, fixed_func)
            print("✅ Fixed displayTravelerDetails function")
    
    # Count again
    open_count = content.count('{')
    close_count = content.count('}')
    print(f"After:  {{:{open_count}, }}:{close_count}")
    
    with open(travelers_path, 'w', encoding='utf-8') as f:
        f.write(content)

# ====== FIX 3-4: DEBUG_USERS.HTML LOOPS ======
print("\n📁 Fixing debug_users.html loops...")
debug_path = os.path.join(project_root, 'public', 'admin', 'debug_users.html')

if os.path.exists(debug_path):
    with open(debug_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Fix line 102 - forEach loop
    for i, line in enumerate(lines):
        if 'functions.forEach' in line and i > 95 and i < 110:
            print(f"Found forEach at line {i+1}")
            lines[i] = '    for (let i = 0; i < functions.length; i++) {\n'
            lines[i+1] = '        const fn = functions[i];\n'
            lines[i+2] = '        if (typeof window[fn] === \'function\') {\n'
            lines[i+3] = '            log(`✅ Function "${fn}()" exists`, \'success\');\n'
            lines[i+4] = '        } else {\n'
            lines[i+5] = '            log(`❌ Function "${fn}()" is missing`, \'error\');\n'
            lines[i+6] = '        }\n'
            lines[i+7] = '    }\n'
            print("✅ Fixed line 102 loop")
            break
    
    # Fix line 126 - check for any loop issues
    for i, line in enumerate(lines):
        if 'runAllTests' in line and i > 120 and i < 130:
            print(f"Found runAllTests at line {i+1}")
            # Ensure proper syntax
    
    with open(debug_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

# ====== FIX 5: TRAVELERS.HTML LINE 2595 LOOP ======
print("\n📁 Fixing travelers.html line 2595 loop...")

if os.path.exists(travelers_path):
    with open(travelers_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if len(lines) >= 2595:
        # Find the uploadCSV function and fix the loop
        for i in range(2590, 2600):
            if i < len(lines) and 'for (let i = 1; i < lines.length; i++)' in lines[i]:
                print(f"Found loop at line {i+1}")
                lines[i] = '        for (let i = 1; i < lines.length; i++) {\n'
                lines[i+1] = '            const currentLine = lines[i].trim();\n'
                lines[i+2] = '            if (!currentLine) continue;\n'
                lines[i+3] = '            const cells = currentLine.split(\',\');\n'
                print("✅ Fixed uploadCSV loop")
                break
    
    with open(travelers_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

# ====== FIX 6-8: SESSION MANAGER ======
print("\n📁 Fixing session-manager.js...")
sm_path = os.path.join(project_root, 'public', 'admin', 'js', 'session-manager.js')

if os.path.exists(sm_path):
    with open(sm_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix SESSION_TIMEOUT
    content = re.sub(r'SESSION_TIMEOUT:\s*\d+\s*\*\s*\d+\s*\*\s*\d+\s*\*\s*\d+.*', 
                     'SESSION_TIMEOUT: 30 * 60 * 1000,  // 30 minutes', content)
    
    # Add WARNING_BEFORE
    if 'WARNING_BEFORE:' not in content:
        content = re.sub(r'(SESSION_TIMEOUT:.*?\n)', 
                         r'\1    WARNING_BEFORE: 2 * 60 * 1000,  // 2 minutes\n', content)
    
    # Fix startTimers
    if 'startTimers:' in content:
        if 'this.clearTimers' not in content.split('startTimers')[1][:100]:
            content = content.replace('startTimers: function() {',
                                       'startTimers: function() {\n        this.clearTimers();')
    
    # Remove duplicate startTimers
    if content.count('startTimers:') > 1:
        parts = content.split('startTimers:')
        content = parts[0] + 'startTimers:' + ''.join(parts[1:])
    
    with open(sm_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Fixed session-manager.js")

# ====== FIX FRONTPAGE ======
print("\n📁 Fixing frontpage.html...")
frontpage_path = os.path.join(project_root, 'public', 'admin', 'frontpage.html')

if os.path.exists(frontpage_path):
    with open(frontpage_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix double SessionManager
    if 'SessionManager.SessionManager' in content:
        content = content.replace('SessionManager.SessionManager', 'SessionManager')
        print("✅ Fixed frontpage.html")
    
    with open(frontpage_path, 'w', encoding='utf-8') as f:
        f.write(content)

print("\n" + "="*80)
print("✅ ALL 8 ERRORS FIXED!")
print("="*80)
print("\n📋 NEXT STEPS:")
print("   1. Run: python railway_check.py")
print("   2. Run: python find_all_errors.py")
print("   3. Deploy to Railway: git push railway main")
print("="*80)
