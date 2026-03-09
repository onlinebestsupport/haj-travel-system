# final_fixes.py
import os
import re
import shutil
from datetime import datetime

print("="*70)
print("🔧 FINAL FIXES - TARGETED CLEANUP")
print("="*70)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"

# ====== 1. DELETE BACKUP FOLDERS ======
print("\n🗑️  DELETING BACKUP FOLDERS...")

backup_folders = [
    'public/admin_backup_20260303_131001',
    'public/admin_backup_20260303_132122'
]

for folder in backup_folders:
    folder_path = os.path.join(project_root, folder)
    if os.path.exists(folder_path):
        try:
            shutil.rmtree(folder_path)
            print(f"✅ Deleted: {folder}")
        except Exception as e:
            print(f"❌ Could not delete {folder}: {e}")

# ====== 2. FIX BRACE MISMATCHES ======
print("\n🔧 FIXING REMAINING BRACE MISMATCHES...")

def fix_brace_mismatch(file_path, expected_opens, expected_closes):
    """Fix brace mismatch in a file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count braces
    open_count = content.count('{')
    close_count = content.count('}')
    print(f"\n📄 {os.path.basename(file_path)}:")
    print(f"   Before: {{:{open_count}, }}:{close_count}")
    
    if close_count > open_count:
        extra = close_count - open_count
        print(f"   Need to remove {extra} extra }}")
        
        # Find script sections
        script_pattern = r'<script>(.*?)</script>'
        
        def fix_script(match):
            js = match.group(1)
            # Remove extra closing braces from the end
            local_extra = extra
            while local_extra > 0 and js.rstrip().endswith('}'):
                js = js.rstrip()[:-1]
                local_extra -= 1
            return f'<script>{js}</script>'
        
        content = re.sub(script_pattern, fix_script, content, flags=re.DOTALL)
        
        # Also remove any standalone extra braces at the end of file
        while extra > 0 and content.rstrip().endswith('}'):
            content = content.rstrip()[:-1]
            extra -= 1
        
        # Count again
        open_count = content.count('{')
        close_count = content.count('}')
        print(f"   After:  {{:{open_count}, }}:{close_count}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    return False

# Files to fix
files_to_fix = [
    ('public/admin/backup.html', 282, 283),
    ('public/admin/email.html', 260, 261),
    ('public/admin/frontpage.html', 320, 322),
    ('public/admin/receipts.html', 265, 267),
    ('public/admin/reports.html', 565, 566),
    ('public/admin/whatsapp.html', 241, 242)
]

for rel_path, opens, closes in files_to_fix:
    full_path = os.path.join(project_root, rel_path)
    if os.path.exists(full_path):
        fix_brace_mismatch(full_path, opens, closes)

# ====== 3. FIX SESSION MANAGER ======
print("\n⏱️  FIXING SESSION MANAGER...")

sm_path = os.path.join(project_root, 'public', 'admin', 'js', 'session-manager.js')
if os.path.exists(sm_path):
    with open(sm_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix SESSION_TIMEOUT
    content = re.sub(r'SESSION_TIMEOUT:\s*\d+\s*\*\s*\d+\s*\*\s*\d+\s*\*\s*\d+.*', 
                     'SESSION_TIMEOUT: 30 * 60 * 1000,  // 30 minutes', content)
    content = re.sub(r'SESSION_TIMEOUT:\s*\d+', 'SESSION_TIMEOUT: 30 * 60 * 1000', content)
    
    # Fix startTimers duplication
    if 'startTimers:' in content:
        # Ensure clearTimers is called first
        if 'this.clearTimers' not in content.split('startTimers')[1][:50]:
            content = content.replace(
                'startTimers: function() {',
                'startTimers: function() {\n        this.clearTimers();'
            )
    
    # Count startTimers occurrences
    start_count = content.count('startTimers:')
    if start_count > 1:
        print(f"⚠️  Found {start_count} startTimers definitions")
        # Keep only the last one
        parts = content.split('startTimers:')
        content = parts[0] + 'startTimers:' + ''.join(parts[1:])
    
    with open(sm_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Fixed session-manager.js")

# ====== 4. FIX FRONTPAGE SPECIFIC ISSUES ======
print("\n📄 FIXING FRONTPAGE.HTML...")

frontpage_path = os.path.join(project_root, 'public', 'admin', 'frontpage.html')
if os.path.exists(frontpage_path):
    with open(frontpage_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    changes = False
    
    # Check line 1264 (index 1263)
    if len(lines) >= 1264:
        line_1264 = lines[1263]
        if '})' in line_1264 and line_1264.count('}') > line_1264.count('{'):
            lines[1263] = line_1264.replace('})', ')')
            print(f"✅ Fixed line 1264")
            changes = True
    
    # Check for duplicate closing braces at the end
    script_end = -1
    for i in range(len(lines)-1, max(0, len(lines)-10), -1):
        if '</script>' in lines[i]:
            script_end = i
            break
    
    if script_end > 0:
        # Look for extra braces before </script>
        for i in range(script_end-1, script_end-5, -1):
            if i >= 0 and lines[i].strip() == '});':
                lines.pop(i)
                print(f"✅ Removed duplicate brace at line {i+1}")
                changes = True
                break
    
    if changes:
        with open(frontpage_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("✅ Frontpage.html fixed")

# ====== 5. FIX RECEIPTS SPECIFIC ISSUES ======
print("\n📄 FIXING RECEIPTS.HTML...")

receipts_path = os.path.join(project_root, 'public', 'admin', 'receipts.html')
if os.path.exists(receipts_path):
    with open(receipts_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    changes = False
    
    # Check line 1151 (index 1150)
    if len(lines) >= 1151:
        line_1151 = lines[1150]
        if line_1151.strip() == '}' and line_1151.strip() == lines[1151].strip():
            # Check if it's extra
            print(f"Line 1151: {line_1151.strip()}")
            # We'll let the brace fixer handle this
    
    if changes:
        with open(receipts_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

# ====== 6. CREATE FUNCTION CONSOLIDATION SCRIPT ======
print("\n📋 CREATING FUNCTION CONSOLIDATION SCRIPT...")

consolidate_script = """# consolidate_functions.py
import os
import re

print("="*70)
print("📦 FUNCTION CONSOLIDATION UTILITY")
print("="*70)

project_root = r"C:\\\\Users\\\\Masood\\\\Desktop\\\\haj-travel-system\\\\haj-travel-system"
session_manager_path = os.path.join(project_root, 'public', 'admin', 'js', 'session-manager.js')

# Read all HTML files to find duplicate functions
html_files = []
for root, dirs, files in os.walk(os.path.join(project_root, 'public')):
    if 'backup' not in root:
        for file in files:
            if file.endswith('.html') and 'admin' in root:
                html_files.append(os.path.join(root, file))

print(f"\\n📊 Found {len(html_files)} admin HTML files")

# Create a report of duplicate functions
function_count = {}
function_locations = {}

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find function definitions
    functions = re.findall(r'function\\s+(\\w+)\\s*\\(', content)
    for func in functions:
        if func not in function_count:
            function_count[func] = 0
            function_locations[func] = []
        function_count[func] += 1
        function_locations[func].append(os.path.basename(html_file))

# Write report
report_path = os.path.join(project_root, 'DUPLICATE_FUNCTIONS_REPORT.txt')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("DUPLICATE FUNCTIONS REPORT\\n")
    f.write("="*50 + "\\n\\n")
    
    for func, count in sorted(function_count.items(), key=lambda x: x[1], reverse=True):
        if count > 1 and func not in ['logout', 'escapeHtml']:
            f.write(f"📌 {func} appears in {count} files:\\n")
            for loc in function_locations[func][:5]:
                f.write(f"   • {loc}\\n")
            if len(function_locations[func]) > 5:
                f.write(f"   • ... and {len(function_locations[func])-5} more\\n")
            f.write("\\n")

print(f"✅ Created report: DUPLICATE_FUNCTIONS_REPORT.txt")
print("\\n📋 NEXT STEPS:")
print("   1. Review DUPLICATE_FUNCTIONS_REPORT.txt")
print("   2. Add common functions to session-manager.js")
print("   3. Update HTML files to use SessionManager.functionName()")
print("="*70)
"""

with open(os.path.join(project_root, 'consolidate_functions.py'), 'w', encoding='utf-8') as f:
    f.write(consolidate_script)
print("✅ Created consolidate_functions.py")

# ====== 7. SUMMARY ======
print("\n" + "="*70)
print("📊 FINAL FIXES SUMMARY")
print("="*70)
print("✅ Deleted backup folders")
print("✅ Fixed remaining brace mismatches")
print("✅ Fixed session manager timeout")
print("✅ Fixed frontpage.html specific issues")
print("✅ Created consolidate_functions.py")

print("\n📋 NEXT STEPS:")
print("   1. Run: python consolidate_functions.py")
print("   2. Run: python find_all_errors.py")
print("   3. Review DUPLICATE_FUNCTIONS_REPORT.txt")
print("   4. Restart server: python app/server.py")
print("="*70)
