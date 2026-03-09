# find_all_errors.py
import os
import re
import json
from datetime import datetime

print("="*70)
print("🔍 COMPLETE ERROR DETECTION SYSTEM")
print("="*70)
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"
issues_found = []

# ====== 1. CHECK JAVASCRIPT SYNTAX ERRORS ======
print("\n📜 CHECKING JAVASCRIPT SYNTAX IN HTML FILES...")

html_files = []
for root, dirs, files in os.walk(os.path.join(project_root, 'public')):
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

print(f"Found {len(html_files)} HTML files to check")

def check_js_braces(content, file_path):
    """Check for unbalanced braces in JavaScript sections"""
    lines = content.split('\n')
    in_script = False
    script_lines = []
    script_start = 0
    
    for i, line in enumerate(lines, 1):
        if '<script>' in line or '<script ' in line:
            in_script = True
            script_start = i
            script_lines = []
        elif '</script>' in line:
            in_script = False
            # Check this script section
            script_content = '\n'.join(script_lines)
            open_braces = script_content.count('{')
            close_braces = script_content.count('}')
            
            if open_braces != close_braces:
                issues_found.append({
                    'file': file_path,
                    'line': script_start,
                    'issue': f'JavaScript brace mismatch: {open_braces} {{ vs {close_braces} }}',
                    'severity': 'HIGH'
                })
                print(f"❌ {file_path}:{script_start} - Brace mismatch ({{:{open_braces}, }}:{close_braces})")
        elif in_script:
            script_lines.append(line)
    
    # Check for unbalanced braces in the whole file (outside script tags too)
    all_braces_open = content.count('{')
    all_braces_close = content.count('}')
    if all_braces_open != all_braces_close:
        issues_found.append({
            'file': file_path,
            'line': 1,
            'issue': f'Global brace mismatch in file: {all_braces_open} {{ vs {all_braces_close} }}',
            'severity': 'HIGH'
        })
        print(f"❌ {file_path} - Global brace mismatch ({{:{all_braces_open}, }}:{all_braces_close})")

# Check each HTML file
for html_file in html_files:
    rel_path = os.path.relpath(html_file, project_root)
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        check_js_braces(content, rel_path)
    except Exception as e:
        print(f"⚠️  Error reading {rel_path}: {e}")

# ====== 2. CHECK SESSION MANAGER ======
print("\n🕒 CHECKING SESSION MANAGER...")

session_manager_path = os.path.join(project_root, 'public', 'admin', 'js', 'session-manager.js')
if os.path.exists(session_manager_path):
    with open(session_manager_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for timer issues
    if 'setTimeout' in content:
        timeout_count = content.count('setTimeout')
        print(f"Found {timeout_count} setTimeout calls")
    
    # Check for multiple timer starts
    start_timer_calls = content.count('startTimers(')
    if start_timer_calls > 1:
        issues_found.append({
            'file': 'public/admin/js/session-manager.js',
            'line': 'multiple',
            'issue': f'startTimers() appears {start_timer_calls} times - may cause timer duplication',
            'severity': 'MEDIUM'
        })
    
    # Check for clearTimers before setting new timers
    if 'startTimers' in content and 'clearTimers' not in content.split('startTimers')[0]:
        issues_found.append({
            'file': 'public/admin/js/session-manager.js',
            'line': 'startTimers',
            'issue': 'startTimers() may not clear existing timers first',
            'severity': 'HIGH'
        })
    
    # Check for duplicate timer messages
    if 'Session timers started' in content:
        print("✅ Session manager has timer logging")
    
    # Check session timeout values
    timeout_match = re.search(r'SESSION_TIMEOUT\s*:\s*(\d+)', content)
    if timeout_match:
        timeout = int(timeout_match.group(1))
        print(f"Session timeout: {timeout/60000:.0f} minutes")
        if timeout != 30 * 60 * 1000:
            issues_found.append({
                'file': 'public/admin/js/session-manager.js',
                'line': 'SESSION_TIMEOUT',
                'issue': f'Session timeout is {timeout/60000:.0f} minutes, should be 30 minutes',
                'severity': 'LOW'
            })
else:
    issues_found.append({
        'file': 'public/admin/js/session-manager.js',
        'line': 'N/A',
        'issue': 'Session manager file not found',
        'severity': 'HIGH'
    })

# ====== 3. CHECK FOR COMMON JAVASCRIPT ERRORS ======
print("\n🔧 CHECKING FOR COMMON JAVASCRIPT ERRORS...")

error_patterns = [
    (r'undefined\s*=', 'Assigning to undefined'),
    (r'console.log\s*\(\s*\)', 'Empty console.log'),
    (r'=\s*null;', 'Setting to null (maybe use undefined)'),
    (r'for\s*\([^)]+\)\s*{', 'Check for loop syntax'),
    (r'if\s*\([^)]+\)\s*;', 'If statement with semicolon'),
]

for html_file in html_files:
    rel_path = os.path.relpath(html_file, project_root)
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                for pattern, desc in error_patterns:
                    if re.search(pattern, line):
                        issues_found.append({
                            'file': rel_path,
                            'line': i,
                            'issue': f'Possible error: {desc}',
                            'severity': 'LOW',
                            'code': line.strip()
                        })
                        print(f"⚠️  {rel_path}:{i} - {desc}")
    except Exception as e:
        print(f"⚠️  Error reading {rel_path}: {e}")

# ====== 4. CHECK SESSION INIT IN HTML FILES ======
print("\n🔐 CHECKING SESSION INITIALIZATION...")

for html_file in html_files:
    if 'admin' in html_file and 'login' not in html_file:
        rel_path = os.path.relpath(html_file, project_root)
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for proper session initialization
            if 'SessionManager.initPage' not in content:
                issues_found.append({
                    'file': rel_path,
                    'line': 'N/A',
                    'issue': 'Missing SessionManager.initPage() call',
                    'severity': 'HIGH'
                })
                print(f"❌ {rel_path} - Missing SessionManager.initPage()")
        except Exception as e:
            print(f"⚠️  Error reading {rel_path}: {e}")

# ====== 5. CHECK FOR DUPLICATE FUNCTIONS ======
print("\n🔄 CHECKING FOR DUPLICATE FUNCTION DEFINITIONS...")

function_names = {}
for html_file in html_files:
    rel_path = os.path.relpath(html_file, project_root)
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Find all function definitions
            functions = re.findall(r'function\s+(\w+)\s*\(', content)
            for func in functions:
                if func not in function_names:
                    function_names[func] = []
                function_names[func].append(rel_path)
    except Exception as e:
        print(f"⚠️  Error reading {rel_path}: {e}")

for func, files in function_names.items():
    if len(files) > 1 and func not in ['logout', 'showNotification', 'escapeHtml']:  # Common safe duplicates
        issues_found.append({
            'file': 'multiple',
            'line': 'N/A',
            'issue': f'Function "{func}" defined in {len(files)} files: {files}',
            'severity': 'LOW'
        })
        print(f"⚠️  Function '{func}' appears in {len(files)} files")

# ====== 6. CHECK TIMER SPAM IN CONSOLE ======
print("\n⏱️  CHECKING FOR TIMER SPAM...")

for html_file in html_files:
    rel_path = os.path.relpath(html_file, project_root)
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for setInterval without clearInterval
        if 'setInterval' in content and 'clearInterval' not in content:
            issues_found.append({
                'file': rel_path,
                'line': 'N/A',
                'issue': 'setInterval used without clearInterval - may cause memory leaks',
                'severity': 'MEDIUM'
            })
            print(f"⚠️  {rel_path} - setInterval without clearInterval")
    except Exception as e:
        print(f"⚠️  Error reading {rel_path}: {e}")

# ====== 7. CHECK FOR EXTRA BRACES IN FRONTPAGE ======
print("\n📄 SPECIFIC CHECK FOR FRONTPAGE.HTML...")

frontpage_path = os.path.join(project_root, 'public', 'admin', 'frontpage.html')
if os.path.exists(frontpage_path):
    with open(frontpage_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Check line 1293 specifically
    if len(lines) >= 1293:
        line_1293 = lines[1292].strip()
        print(f"Line 1293 content: '{line_1293}'")
        
        # Count braces on this line and nearby
        brace_count = line_1293.count('{') + line_1293.count('}')
        if brace_count > 0:
            issues_found.append({
                'file': 'public/admin/frontpage.html',
                'line': 1293,
                'issue': f'Line contains braces: {line_1293}',
                'severity': 'HIGH'
            })
        
        # Check context (lines 1290-1300)
        print("\nContext around line 1293:")
        for i in range(max(0, 1290-1), min(len(lines), 1300)):
            line_num = i + 1
            marker = "👉" if line_num == 1293 else "  "
            print(f"{marker} {line_num}: {lines[i].rstrip()}")
    else:
        print(f"File only has {len(lines)} lines, line 1293 doesn't exist")
else:
    print("frontpage.html not found")

# ====== 8. SUMMARY REPORT ======
print("\n" + "="*70)
print("📊 ERROR DETECTION SUMMARY")
print("="*70)

if issues_found:
    # Group by severity
    high = [i for i in issues_found if i['severity'] == 'HIGH']
    medium = [i for i in issues_found if i['severity'] == 'MEDIUM']
    low = [i for i in issues_found if i['severity'] == 'LOW']
    
    print(f"\n❌ HIGH severity: {len(high)}")
    for issue in high[:5]:  # Show first 5 high severity
        print(f"   • {issue['file']}:{issue['line']} - {issue['issue']}")
    
    print(f"\n⚠️  MEDIUM severity: {len(medium)}")
    for issue in medium[:5]:
        print(f"   • {issue['file']}:{issue['line']} - {issue['issue']}")
    
    print(f"\n📝 LOW severity: {len(low)}")
    for issue in low[:5]:
        print(f"   • {issue['file']}:{issue['line']} - {issue['issue']}")
    
    print(f"\n📊 Total issues: {len(issues_found)}")
else:
    print("\n✅ NO ISSUES FOUND! Your code is perfect!")

# ====== 9. FIX SUGGESTIONS ======
print("\n" + "="*70)
print("🔧 RECOMMENDED FIXES")
print("="*70)

if issues_found:
    print("\n1️⃣ Fix frontpage.html syntax error:")
    print("   Open public/admin/frontpage.html and go to line 1293")
    print("   Look for an extra '}' or missing '{'")
    print("   Check the context shown above")
    
    print("\n2️⃣ Fix session manager timer spam:")
    print("   In public/admin/js/session-manager.js, modify startTimers():")
    print("   ```javascript")
    print("   startTimers: function() {")
    print("       this.clearTimers();  // Add this line first")
    print("       console.log('⏱️ Session timers started');")
    print("       // ... rest of code")
    print("   },")
    print("   ```")
    
    print("\n3️⃣ Add missing clearInterval where needed")
    print("\n4️⃣ Remove duplicate function definitions")
    print("\n5️⃣ Check session timeout value (should be 30 minutes)")

print("\n" + "="*70)
print(f"Scan completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
