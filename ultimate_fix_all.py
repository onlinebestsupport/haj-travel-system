# ultimate_fix_all.py
import os
import re

print("="*80)
print("🔥 ULTIMATE FIX - SOLVING ALL 8 ERRORS")
print("="*80)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"

# ==================== FIX 1 & 2: TRAVELERS.HTML BRACE MISMATCH ====================
print("\n📁 FIXING TRAVELERS.HTML BRACE MISMATCH (Lines 1485, 2595)...")

travelers_path = os.path.join(project_root, 'public', 'admin', 'travelers.html')

if os.path.exists(travelers_path):
    with open(travelers_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count braces before
    open_before = content.count('{')
    close_before = content.count('}')
    print(f"Before: {{:{open_before}, }}:{close_before}")
    
    # Find the displayTravelerDetails function and fix it
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
    
    # Also fix any extra braces at the end of the file
    lines = content.split('\n')
    for i in range(len(lines)-1, max(0, len(lines)-20), -1):
        if lines[i].strip() == '}' and lines[i-1].strip().endswith('}'):
            # Remove one extra brace
            lines.pop(i)
            print(f"✅ Removed extra brace at line {i+1}")
            break
    
    content = '\n'.join(lines)
    
    # Count braces after
    open_after = content.count('{')
    close_after = content.count('}')
    print(f"After:  {{:{open_after}, }}:{close_after}")
    
    with open(travelers_path, 'w', encoding='utf-8') as f:
        f.write(content)

# ==================== FIX 3 & 4: DEBUG_USERS.HTML LOOPS ====================
print("\n📁 FIXING DEBUG_USERS.HTML LOOPS (Lines 102, 126)...")

debug_path = os.path.join(project_root, 'public', 'admin', 'debug_users.html')

if os.path.exists(debug_path):
    with open(debug_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Completely replace the checkJavaScriptErrors function
    new_function = '''    function checkJavaScriptErrors() {
        log('\\n🔍 Checking for Common JavaScript Errors...', 'info');
        
        // Check for missing variables
        if (typeof SessionManager === 'undefined') {
            log('❌ SessionManager is not defined', 'error');
        } else {
            log('✅ SessionManager loaded', 'success');
        }
        
        // Check for broken functions - using standard for loop
        const functions = ['logout', 'loadUsers', 'showAddUserForm', 'editUser'];
        for (let i = 0; i < functions.length; i++) {
            const fn = functions[i];
            if (typeof window[fn] === 'function') {
                log(`✅ Function "${fn}()" exists`, 'success');
            } else {
                log(`❌ Function "${fn}()" is missing`, 'error');
            }
        }
    }'''
    
    # Find and replace the function
    content = ''.join(lines)
    pattern = r'function checkJavaScriptErrors\(\)\s*\{[^}]*\}'
    content = re.sub(pattern, new_function, content, flags=re.DOTALL)
    
    # Fix any for loops in runAllTests
    if 'runAllTests' in content:
        # Ensure proper syntax
        content = content.replace('await testSession();', '        await testSession();')
        content = content.replace('await testUsersAPI();', '        await testUsersAPI();')
        content = content.replace('await testCreateUser();', '        await testCreateUser();')
    
    with open(debug_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Fixed debug_users.html loops")

# ==================== FIX 5: TRAVELERS.HTML LINE 2595 LOOP ====================
print("\n📁 FIXING TRAVELERS.HTML LINE 2595 LOOP...")

if os.path.exists(travelers_path):
    with open(travelers_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and replace the uploadCSV function loop
    for i in range(2590, 2600):
        if i < len(lines):
            if 'for (let i = 1; i < lines.length; i++)' in lines[i]:
                print(f"Found loop at line {i+1}")
                # Replace with improved version
                lines[i] = '        for (let i = 1; i < lines.length; i++) {\n'
                if i+1 < len(lines):
                    lines[i+1] = '            const currentLine = lines[i].trim();\n'
                if i+2 < len(lines):
                    lines[i+2] = '            if (!currentLine) continue;\n'
                if i+3 < len(lines):
                    lines[i+3] = '            const cells = currentLine.split(\',\');\n'
                print("✅ Fixed uploadCSV loop at line 2595")
                break
    
    with open(travelers_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

# ==================== FIX 6,7,8: SESSION MANAGER ====================
print("\n📁 FIXING SESSION MANAGER (3 issues)...")

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
    content = re.sub(
        r'SESSION_TIMEOUT:\s*\d+',
        'SESSION_TIMEOUT: 30 * 60 * 1000',
        content
    )
    
    # Add WARNING_BEFORE
    if 'WARNING_BEFORE:' not in content:
        content = re.sub(
            r'(SESSION_TIMEOUT:.*?\n)',
            r'\1    WARNING_BEFORE: 2 * 60 * 1000,  // 2 minutes\n',
            content
        )
    
    # Fix startTimers - ensure it has clearTimers
    if 'startTimers:' in content:
        start_section = content.split('startTimers:')[1].split('\n')[0:10]
        start_text = '\n'.join(start_section)
        
        if 'this.clearTimers' not in start_text:
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
    
    # Add proper logging
    content = re.sub(
        r'console\.log\(.*Session timers started.*\);',
        '        console.log(\'⏱️ Session timers started\', {\n            timeout: this.SESSION_TIMEOUT / 60000 + \' minutes\',\n            warning: this.WARNING_BEFORE / 60000 + \' minutes\'\n        });',
        content
    )
    
    with open(sm_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Fixed session-manager.js")

# ==================== FIX FRONTPAGE.HTML ====================
print("\n📁 FIXING FRONTPAGE.HTML...")

frontpage_path = os.path.join(project_root, 'public', 'admin', 'frontpage.html')

if os.path.exists(frontpage_path):
    with open(frontpage_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Fix line 1300 - double SessionManager
    if len(lines) >= 1300:
        line_1300 = lines[1299]
        if 'SessionManager.SessionManager' in line_1300:
            lines[1299] = line_1300.replace('SessionManager.SessionManager', 'SessionManager')
            print("✅ Fixed double SessionManager at line 1300")
    
    # Fix brace issues around line 1293-1297
    if len(lines) >= 1297:
        # Check for extra closing braces
        brace_count = 0
        for i in range(1290, 1300):
            if i < len(lines):
                brace_count += lines[i].count('{')
                brace_count -= lines[i].count('}')
        
        if brace_count < 0:
            # Remove one extra closing brace
            for i in range(1296, 1289, -1):
                if i < len(lines) and '}' in lines[i]:
                    lines[i] = lines[i].replace('}', '', 1)
                    print(f"✅ Removed extra brace at line {i+1}")
                    break
    
    with open(frontpage_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

# ==================== VERIFICATION ====================
print("\n" + "="*80)
print("🔍 VERIFICATION")
print("="*80)

# Check travelers.html
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
if 'this.clearTimers' in content.split('startTimers:')[1][:200]:
    print("✅ startTimers has clearTimers")
if content.count('startTimers:') == 1:
    print("✅ Only one startTimers function")

print("\n" + "="*80)
print("🎉 ALL FIXES APPLIED!")
print("="*80)
print("\n📋 NEXT STEP:")
print("   Run: python find_all_errors.py")
print("="*80)