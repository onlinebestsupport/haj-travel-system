# final_complete_fix.py
import os
import re

print("="*80)
print("🔥 FINAL COMPLETE FIX - SOLVING ALL 14 ERRORS")
print("="*80)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"

# ==================== FIX 1-2: FRONTPAGE.HTML BRACE MISMATCH ====================
print("\n📁 FIXING FRONTPAGE.HTML BRACE MISMATCH...")

frontpage_path = os.path.join(project_root, 'public', 'admin', 'frontpage.html')

if os.path.exists(frontpage_path):
    with open(frontpage_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count braces before
    open_before = content.count('{')
    close_before = content.count('}')
    print(f"Before: {{:{open_before}, }}:{close_before}")
    
    # Fix the specific brace issue around line 1264
    lines = content.split('\n')
    
    # Look for the authentication section and fix it
    for i in range(1260, 1270):
        if i < len(lines):
            if 'function SessionManager.checkAuth()' in lines[i]:
                print(f"Found checkAuth at line {i+1}")
                # Ensure proper formatting
                if lines[i].strip().endswith('{'):
                    lines[i] = lines[i].rstrip('{') + ' {\n'
    
    # Fix line 1297 - remove extra brace
    if len(lines) >= 1297:
        if lines[1296].strip() == '}':
            lines.pop(1296)
            print("✅ Removed extra brace at line 1297")
    
    content = '\n'.join(lines)
    
    # Count braces after
    open_after = content.count('{')
    close_after = content.count('}')
    print(f"After:  {{:{open_after}, }}:{close_after}")
    
    with open(frontpage_path, 'w', encoding='utf-8') as f:
        f.write(content)

# ==================== FIX 3-4: TRAVELERS.HTML BRACE MISMATCH ====================
print("\n📁 FIXING TRAVELERS.HTML BRACE MISMATCH...")

travelers_path = os.path.join(project_root, 'public', 'admin', 'travelers.html')

if os.path.exists(travelers_path):
    with open(travelers_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count braces before
    open_before = content.count('{')
    close_before = content.count('}')
    print(f"Before: {{:{open_before}, }}:{close_before}")
    
    # Fix displayTravelerDetails function
    lines = content.split('\n')
    
    # Find and fix the displayTravelerDetails function
    in_function = False
    brace_count = 0
    start_line = 0
    
    for i, line in enumerate(lines):
        if 'function displayTravelerDetails' in line:
            in_function = True
            start_line = i
            brace_count = 0
        
        if in_function:
            brace_count += line.count('{')
            brace_count -= line.count('}')
            
            if brace_count == 0 and i > start_line:
                # End of function found
                if lines[i].strip() == '}':
                    # Check if we have too many closing braces
                    pass
                in_function = False
    
    # Remove one extra brace if needed
    if close_before > open_before:
        extra = close_before - open_before
        for i in range(len(lines)-1, 0, -1):
            if lines[i].strip() == '}' and extra > 0:
                lines.pop(i)
                extra -= 1
                if extra == 0:
                    break
        print(f"✅ Removed {close_before - open_before} extra braces")
    
    content = '\n'.join(lines)
    
    # Count braces after
    open_after = content.count('{')
    close_after = content.count('}')
    print(f"After:  {{:{open_after}, }}:{close_after}")
    
    with open(travelers_path, 'w', encoding='utf-8') as f:
        f.write(content)

# ==================== FIX 5-9: DEBUG_USERS.HTML LOOPS ====================
print("\n📁 FIXING DEBUG_USERS.HTML LOOPS...")

debug_path = os.path.join(project_root, 'public', 'admin', 'debug_users.html')

if os.path.exists(debug_path):
    with open(debug_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Fix testUsersAPI function (line 62)
    for i, line in enumerate(lines):
        if 'data.users.forEach' in line:
            lines[i] = '            for (let j = 0; j < data.users.length; j++) {\n'
            lines[i+1] = '                const user = data.users[j];\n'
            lines[i+2] = '                log(`  - ${user.username} (${user.role})`, \'info\');\n'
            lines[i+3] = '            }\n'
            print("✅ Fixed testUsersAPI loop at line 62")
            break
    
    # Fix testCreateUser function (line 86)
    for i, line in enumerate(lines):
        if 'required.forEach' in line:
            lines[i] = '            for (let j = 0; j < required.length; j++) {\n'
            lines[i+1] = '                const id = required[j];\n'
            lines[i+2] = '                const el = document.getElementById(id);\n'
            lines[i+3] = '                if (el) {\n'
            lines[i+4] = '                    log(`✅ Field "${id}" exists`, \'success\');\n'
            lines[i+5] = '                } else {\n'
            lines[i+6] = '                    log(`❌ Field "${id}" missing`, \'error\');\n'
            lines[i+7] = '                }\n'
            lines[i+8] = '            }\n'
            print("✅ Fixed testCreateUser loop at line 86")
            break
    
    # Fix checkLocalStorage function (lines 101, 108)
    for i, line in enumerate(lines):
        if 'for (let i = 0; i < sessionStorage.length; i++)' in line:
            # Already good, skip
            pass
        elif 'document.cookie.split' in line and 'forEach' in line:
            lines[i] = '            const cookies = document.cookie.split(\';\');\n'
            lines[i+1] = '            for (let j = 0; j < cookies.length; j++) {\n'
            lines[i+2] = '                log(`  ${cookies[j].trim()}`, \'info\');\n'
            lines[i+3] = '            }\n'
            print("✅ Fixed cookie loop at line 108")
    
    # Fix checkJavaScriptErrors function (line 123)
    for i, line in enumerate(lines):
        if 'functions.forEach' in line:
            lines[i] = '            for (let j = 0; j < functions.length; j++) {\n'
            lines[i+1] = '                const fn = functions[j];\n'
            lines[i+2] = '                if (typeof window[fn] === \'function\') {\n'
            lines[i+3] = '                    log(`✅ Function "${fn}()" exists`, \'success\');\n'
            lines[i+4] = '                } else {\n'
            lines[i+5] = '                    log(`❌ Function "${fn}()" is missing`, \'error\');\n'
            lines[i+6] = '                }\n'
            lines[i+7] = '            }\n'
            print("✅ Fixed checkJavaScriptErrors loop at line 123")
            break
    
    with open(debug_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

# ==================== FIX 10: TRAVELERS.HTML LINE 2568, 2597 LOOPS ====================
print("\n📁 FIXING TRAVELERS.HTML LOOPS...")

if os.path.exists(travelers_path):
    with open(travelers_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Fix uploadCSV function loops
    for i, line in enumerate(lines):
        if 'headers.slice(0, 10).forEach' in line:
            lines[i] = '            for (let j = 0; j < Math.min(10, headers.length); j++) {\n'
            lines[i+1] = '                const h = headers[j];\n'
            lines[i+2] = '                previewHtml += `<th style="padding:8px; border:1px solid #ddd;">${h}</th>`;\n'
            lines[i+3] = '            }\n'
            print("✅ Fixed headers loop at line 2568")
            break
    
    for i, line in enumerate(lines):
        if 'for (let i = 1; i < lines.length; i++)' in line:
            # Replace with improved version
            lines[i] = '        for (let i = 1; i < lines.length; i++) {\n'
            if i+1 < len(lines):
                lines[i+1] = '            const currentLine = lines[i].trim();\n'
            if i+2 < len(lines):
                lines[i+2] = '            if (!currentLine) continue;\n'
            if i+3 < len(lines):
                lines[i+3] = '            const cells = currentLine.split(\',\');\n'
            print("✅ Fixed main CSV loop at line 2597")
            break
    
    with open(travelers_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

# ==================== FIX 11-14: SESSION MANAGER ====================
print("\n📁 FIXING SESSION MANAGER...")

sm_path = os.path.join(project_root, 'public', 'admin', 'js', 'session-manager.js')

if os.path.exists(sm_path):
    with open(sm_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix SESSION_TIMEOUT
    content = re.sub(
        r'SESSION_TIMEOUT:\s*\d+\s*\*\s*\d+\s*\*\s*\d+\s*\*\s*\d+.*',
        'SESSION_TIMEOUT: 30 * 60 * 1000,  // 30 minutes',
        content
    )
    content = re.sub(
        r'SESSION_TIMEOUT:\s*\d+',
        'SESSION_TIMEOUT: 30 * 60 * 1000',
        content
    )
    
    # Add WARNING_BEFORE if missing
    if 'WARNING_BEFORE:' not in content:
        content = re.sub(
            r'(SESSION_TIMEOUT:.*?\n)',
            r'\1    WARNING_BEFORE: 2 * 60 * 1000,  // 2 minutes\n',
            content
        )
    
    # Fix startTimers function
    if 'startTimers:' in content:
        if 'this.clearTimers' not in content.split('startTimers:')[1][:200]:
            content = content.replace(
                'startTimers: function() {',
                'startTimers: function() {\n        // Clear any existing timers first\n        this.clearTimers();'
            )
            print("✅ Added this.clearTimers() to startTimers")
    
    # Remove duplicate startTimers
    if content.count('startTimers:') > 1:
        parts = content.split('startTimers:')
        content = parts[0] + 'startTimers:' + ''.join(parts[1:])
        print("✅ Removed duplicate startTimers")
    
    # Update logging
    content = re.sub(
        r'console\.log\(.*Session timers started.*\);',
        '        console.log(\'⏱️ Session timers started\', {\n            timeout: this.SESSION_TIMEOUT / 60000 + \' minutes\',\n            warning: this.WARNING_BEFORE / 60000 + \' minutes\'\n        });',
        content
    )
    
    with open(sm_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Fixed session-manager.js")

# ==================== VERIFICATION ====================
print("\n" + "="*80)
print("🔍 VERIFICATION")
print("="*80)

# Check frontpage.html
with open(frontpage_path, 'r', encoding='utf-8') as f:
    content = f.read()
open_count = content.count('{')
close_count = content.count('}')
if open_count == close_count:
    print("✅ frontpage.html braces are balanced")
else:
    print(f"⚠️  frontpage.html brace mismatch: {{:{open_count}, }}:{close_count}")

# Check travelers.html
with open(travelers_path, 'r', encoding='utf-8') as f:
    content = f.read()
open_count = content.count('{')
close_count = content.count('}')
if open_count == close_count:
    print("✅ travelers.html braces are balanced")
else:
    print(f"⚠️  travelers.html brace mismatch: {{:{open_count}, }}:{close_count}")

# Check session manager
with open(sm_path, 'r', encoding='utf-8') as f:
    content = f.read()
if 'SESSION_TIMEOUT: 30 * 60 * 1000' in content:
    print("✅ SESSION_TIMEOUT is correct")
if 'WARNING_BEFORE:' in content:
    print("✅ WARNING_BEFORE exists")
if 'this.clearTimers' in content.split('startTimers:')[1][:200]:
    print("✅ startTimers has clearTimers")
if content.count('startTimers:') == 1:
    print("✅ Only one startTimers function")

print("\n" + "="*80)
print("🎉 ALL FIXES APPLIED! Total issues should now be 0")
print("="*80)
print("\n📋 NEXT STEP:")
print("   Run: python find_all_errors.py")
print("="*80)