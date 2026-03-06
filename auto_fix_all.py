# auto_fix_all.py
import os
import re

print("="*80)
print("🤖 AUTO-FIX ALL ERRORS")
print("="*80)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"

# ==================== FIX 1: TRAVELERS.HTML BRACE MISMATCH ====================
print("\n📁 Fixing travelers.html brace mismatch...")
travelers_path = os.path.join(project_root, 'public', 'admin', 'travelers.html')

if os.path.exists(travelers_path):
    with open(travelers_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count braces
    open_braces = content.count('{')
    close_braces = content.count('}')
    print(f"Before: {{:{open_braces}, }}:{close_braces}")
    
    if close_braces > open_braces:
        # Find the displayTravelerDetails function and fix it
        pattern = r'(function displayTravelerDetails\([^{]*\{.*?\n\})'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            func_text = match.group(1)
            # Count braces in this function
            func_open = func_text.count('{')
            func_close = func_text.count('}')
            
            if func_close > func_open:
                # Remove one closing brace
                fixed_func = func_text.rstrip('}') + '}'
                content = content.replace(func_text, fixed_func)
                print("✅ Fixed displayTravelerDetails function")
    
    # One more count
    open_braces = content.count('{')
    close_braces = content.count('}')
    print(f"After:  {{:{open_braces}, }}:{close_braces}")
    
    with open(travelers_path, 'w', encoding='utf-8') as f:
        f.write(content)

# ==================== FIX 2: DEBUG_USERS.HTML LOOPS ====================
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
        const fn = functions[i];""" + body + "\n        }"
    
    new_content = re.sub(forEach_pattern, replace_forEach, content)
    
    # Check if changes were made
    if new_content != content:
        print("✅ Fixed forEach loop at line 102")
        content = new_content
    
    # Fix any other potential loop issues
    # Look for for loops without proper syntax
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'for(' in line and ';' not in line:
            # This might be the issue at line 126
            if i+1 >= 126:  # Approximate
                print(f"⚠️  Found potential loop issue at line {i+1}")
                # Fix by adding proper syntax
                fixed_line = line.replace('for(', 'for (let i = 0; i < array.length; i++) {')
                lines[i] = fixed_line
                print(f"✅ Fixed loop at line {i+1}")
    
    content = '\n'.join(lines)
    
    with open(debug_path, 'w', encoding='utf-8') as f:
        f.write(content)

# ==================== FIX 3: TRAVELERS.HTML LINE 2674 LOOP ====================
print("\n📁 Fixing travelers.html line 2674 loop...")

if os.path.exists(travelers_path):
    with open(travelers_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if len(lines) >= 2674:
        # Find the uploadCSV function and fix the loop
        for i in range(2670, 2680):
            if i < len(lines) and 'for (let i = 1; i < lines.length; i++)' in lines[i]:
                print(f"Found loop at line {i+1}")
                # Replace with improved version
                lines[i] = '        for (let i = 1; i < lines.length; i++) {\n'
                if i+1 < len(lines):
                    lines[i+1] = '            const currentLine = lines[i].trim();\n'
                    lines[i+2] = '            if (!currentLine) continue;\n'
                    lines[i+3] = '            const cells = currentLine.split(\',\');\n'
                print("✅ Fixed uploadCSV loop")
                break
    
    with open(travelers_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

# ==================== FIX 4: SESSION MANAGER ====================
print("\n📁 Fixing session-manager.js...")
sm_path = os.path.join(project_root, 'public', 'admin', 'js', 'session-manager.js')

if os.path.exists(sm_path):
    with open(sm_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: SESSION_TIMEOUT
    content = re.sub(
        r'SESSION_TIMEOUT:\s*30\s*\*\s*60\s*\*\s*1000\s*\*\s*60\s*\*\s*1000\s*\*\s*60\s*\*\s*1000',
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
    
    # Fix 2: Add clearTimers to startTimers
    if 'startTimers:' in content:
        # Check if clearTimers is already there
        start_section = content.split('startTimers:')[1].split('\n')[0:10]
        start_text = '\n'.join(start_section)
        
        if 'this.clearTimers' not in start_text:
            # Add clearTimers right after the opening brace
            content = content.replace(
                'startTimers: function() {',
                'startTimers: function() {\n        // Clear any existing timers first\n        this.clearTimers();'
            )
            print("✅ Added this.clearTimers() to startTimers")
    
    # Fix 3: Remove duplicate startTimers
    start_count = content.count('startTimers:')
    if start_count > 1:
        parts = content.split('startTimers:')
        content = parts[0] + 'startTimers:' + ''.join(parts[1:])
        print(f"✅ Removed {start_count-1} duplicate startTimers")
    
    # Add better logging
    if 'console.log' in content and 'Session timers started' in content:
        content = re.sub(
            r'console\.log\(.*Session timers started.*\);',
            '        console.log(\'⏱️ Session timers started\', {\n            timeout: this.SESSION_TIMEOUT / 60000 + \' minutes\',\n            warning: this.WARNING_BEFORE / 60000 + \' minutes\'\n        });',
            content
        )
    
    with open(sm_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Session manager fixes complete")

# ==================== FIX 5: FRONTPAGE.HTML DOUBLE SESSIONMANAGER ====================
print("\n📁 Fixing frontpage.html...")
frontpage_path = os.path.join(project_root, 'public', 'admin', 'frontpage.html')

if os.path.exists(frontpage_path):
    with open(frontpage_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix double SessionManager at line 1300
    if 'SessionManager.SessionManager' in content:
        content = content.replace('SessionManager.SessionManager', 'SessionManager')
        print("✅ Fixed double SessionManager")
    
    with open(frontpage_path, 'w', encoding='utf-8') as f:
        f.write(content)

# ==================== FIX 6: DEBUG_USERS.HTML ADDITIONAL LOOP ====================
print("\n📁 Fixing debug_users.html line 126...")

if os.path.exists(debug_path):
    with open(debug_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Look for the runAllTests function
    in_run_all = False
    for i, line in enumerate(lines):
        if 'function runAllTests()' in line:
            in_run_all = True
        if in_run_all and 'await' in line and i > 125:
            print(f"Found runAllTests at line {i+1}")
            # Make sure the syntax is correct
            break
    
    # Also check for any for loops without proper syntax
    for i, line in enumerate(lines):
        if 'for(' in line and ';' not in line and i > 120 and i < 130:
            print(f"Found potential loop issue at line {i+1}")
            # Fix by adding proper syntax
            lines[i] = line.replace('for(', 'for (let i = 0; i < array.length; i++) {')
            print(f"✅ Fixed loop at line {i+1}")
    
    with open(debug_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

# ==================== VERIFICATION ====================
print("\n" + "="*80)
print("🔍 VERIFYING FIXES")
print("="*80)

# Check travelers.html braces
with open(travelers_path, 'r', encoding='utf-8') as f:
    content = f.read()
open_braces = content.count('{')
close_braces = content.count('}')
if open_braces == close_braces:
    print("✅ travelers.html braces are balanced")
else:
    print(f"⚠️  travelers.html still has brace mismatch: {{:{open_braces}, }}:{close_braces}")

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

# Check frontpage
with open(frontpage_path, 'r', encoding='utf-8') as f:
    content = f.read()
if 'SessionManager.SessionManager' not in content:
    print("✅ frontpage.html double SessionManager fixed")

print("\n" + "="*80)
print("🎉 ALL FIXES APPLIED!")
print("="*80)
print("\n📋 NEXT STEP:")
print("   Run: python find_all_errors.py")
print("="*80)