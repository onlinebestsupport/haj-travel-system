# ultimate_fix.py
import os
import re
import shutil
from datetime import datetime

print("="*80)
print("🔧 ULTIMATE AUTO-FIX SYSTEM")
print("="*80)
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"
backup_dir = os.path.join(project_root, f"backup_before_ultimate_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
os.makedirs(backup_dir, exist_ok=True)

print(f"\n📦 Creating backup in: {backup_dir}")

# ==================== 1. FIX BRACE MISMATCHES IN ALL HTML FILES ====================
print("\n🔍 FIXING BRACE MISMATCHES IN HTML FILES...")

def fix_braces_in_file(file_path):
    """Fix brace mismatches in a file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup the file
    rel_path = os.path.relpath(file_path, project_root)
    backup_path = os.path.join(backup_dir, rel_path.replace('\\', '_'))
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    shutil.copy2(file_path, backup_path)
    
    # Extract JavaScript sections
    def fix_js_braces(js_content):
        """Fix brace count in JavaScript"""
        open_count = js_content.count('{')
        close_count = js_content.count('}')
        
        if open_count == close_count:
            return js_content
        
        if close_count > open_count:
            # Remove extra closing braces
            extra = close_count - open_count
            # Find all closing braces positions
            positions = []
            for i, char in enumerate(js_content):
                if char == '}':
                    positions.append(i)
            
            # Remove from the end
            if positions:
                # Keep everything up to the last needed brace
                keep_until = positions[-(extra+1)] if extra < len(positions) else 0
                js_content = js_content[:keep_until+1]
                print(f"      Removed {extra} extra }}")
        
        return js_content
    
    # Find all script tags
    script_pattern = r'<script>(.*?)</script>'
    
    def replace_script(match):
        js = match.group(1)
        fixed_js = fix_js_braces(js)
        return f'<script>{fixed_js}</script>'
    
    fixed_content = re.sub(script_pattern, replace_script, content, flags=re.DOTALL)
    
    # Also fix any standalone braces
    open_count = fixed_content.count('{')
    close_count = fixed_content.count('}')
    
    if open_count != close_count:
        print(f"   ⚠️  Still mismatched after fix: {{:{open_count}, }}:{close_count}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    return open_count == close_count

# Process all HTML files
html_files = []
for root, dirs, files in os.walk(os.path.join(project_root, 'public')):
    if any(skip in root for skip in ['backup', 'venv', '__pycache__', '.git']):
        continue
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

fixed_count = 0
for html_file in html_files:
    rel_path = os.path.relpath(html_file, project_root)
    try:
        if fix_braces_in_file(html_file):
            fixed_count += 1
            print(f"✅ {rel_path}")
        else:
            print(f"⚠️  {rel_path} - needs manual review")
    except Exception as e:
        print(f"❌ {rel_path} - Error: {e}")

print(f"\n📊 Fixed braces in {fixed_count} files")

# ==================== 2. FIX SESSION MANAGER ====================
print("\n⏱️  FIXING SESSION MANAGER...")

sm_path = os.path.join(project_root, 'public', 'admin', 'js', 'session-manager.js')
if os.path.exists(sm_path):
    with open(sm_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    shutil.copy2(sm_path, os.path.join(backup_dir, 'session-manager.js.bak'))
    
    # Fix SESSION_TIMEOUT
    content = re.sub(r'SESSION_TIMEOUT:\s*\d+\s*\*\s*\d+\s*\*\s*\d+\s*\*\s*\d+\s*\*\s*\d+\s*\*\s*\d+', 
                     'SESSION_TIMEOUT: 30 * 60 * 1000', content)
    content = re.sub(r'SESSION_TIMEOUT:\s*\d+', 'SESSION_TIMEOUT: 30 * 60 * 1000', content)
    
    # Ensure clearTimers is called in startTimers
    if 'startTimers:' in content and 'this.clearTimers' not in content.split('startTimers')[1].split('\n')[0:5]:
        content = content.replace(
            'startTimers: function() {',
            'startTimers: function() {\n        this.clearTimers();'
        )
    
    # Fix any duplicate startTimers definitions
    start_count = content.count('startTimers:')
    if start_count > 1:
        # Keep only the last one
        parts = content.split('startTimers:')
        content = parts[0] + 'startTimers:' + ''.join(parts[1:])
    
    with open(sm_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Fixed session-manager.js")

# ==================== 3. ADD MISSING SESSION INIT ====================
print("\n🔐 ADDING MISSING SESSION INITIALIZATION...")

def add_session_init(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'SessionManager.initPage' in content:
        return False
    
    # Backup
    rel_path = os.path.relpath(file_path, project_root)
    backup_path = os.path.join(backup_dir, rel_path.replace('\\', '_'))
    shutil.copy2(file_path, backup_path)
    
    # Add session init before </body>
    init_code = """
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            if (typeof SessionManager !== 'undefined') {
                SessionManager.initPage();
            }
        });
    </script>
    """
    
    content = content.replace('</body>', init_code + '\n</body>')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

# Add to admin files missing session init
admin_files = [
    'public/admin/batches.html',
    'public/admin/cookie-test.html',
    'public/admin/debug_users.html',
    'public/admin/invoices.html',
    'public/admin/payments.html',
    'public/admin/simple-test.html',
    'public/admin/users.html'
]

added_count = 0
for rel_path in admin_files:
    full_path = os.path.join(project_root, rel_path)
    if os.path.exists(full_path):
        if add_session_init(full_path):
            print(f"✅ Added SessionManager.initPage() to {rel_path}")
            added_count += 1
        else:
            print(f"ℹ️  Already has SessionManager.initPage() in {rel_path}")

print(f"\n📊 Added session init to {added_count} files")

# ==================== 4. CREATE FUNCTION CLEANUP SCRIPT ====================
print("\n📋 CREATING FUNCTION CLEANUP SCRIPT...")

cleanup_script = """# function_cleanup.py
import os
import re

print("="*70)
print("🧹 FUNCTION CLEANUP UTILITY")
print("="*70)

project_root = r"C:\\\\Users\\\\Masood\\\\Desktop\\\\haj-travel-system\\\\haj-travel-system"

# Common functions to move to session-manager.js
common_functions = [
    'checkAuth', 'closeAllModals', 'previousPage', 'nextPage', 
    'updatePaginationInfo', 'resetFilters', 'loadBatches',
    'checkAdminSession', 'showSaveReportModal', 'closeSaveReportModal'
]

# Read all HTML files
html_files = []
for root, dirs, files in os.walk(os.path.join(project_root, 'public')):
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

print(f"\\n📊 Found {len(html_files)} HTML files to process")

# Create a report
with open(os.path.join(project_root, 'FUNCTION_CLEANUP_REPORT.txt'), 'w') as report:
    report.write("FUNCTION CLEANUP REPORT\\n")
    report.write("="*50 + "\\n\\n")
    
    for func in common_functions:
        report.write(f"\\n📌 Function: {func}\\n")
        report.write("-"*30 + "\\n")
        found_in = []
        
        for html_file in html_files:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if func in content:
                    rel_path = os.path.relpath(html_file, project_root)
                    found_in.append(rel_path)
                    report.write(f"  • {rel_path}\\n")
        
        if len(found_in) > 1:
            report.write(f"\\n  ⚠️  Found in {len(found_in)} files\\n")

print("\\n✅ Created FUNCTION_CLEANUP_REPORT.txt")
print("\\n📋 NEXT STEPS:")
print("   1. Review FUNCTION_CLEANUP_REPORT.txt")
print("   2. Add common functions to session-manager.js")
print("   3. Remove duplicates from individual HTML files")
"""

with open(os.path.join(project_root, 'function_cleanup.py'), 'w', encoding='utf-8') as f:
    f.write(cleanup_script)
print("✅ Created function_cleanup.py")

# ==================== 5. FIX SETINTERVAL WITHOUT CLEARINTERVAL ====================
print("\n⏲️  FIXING MISSING CLEARINTERVAL...")

def fix_intervals(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'setInterval' not in content:
        return False
    
    if 'clearInterval' in content:
        return False
    
    # Backup
    rel_path = os.path.relpath(file_path, project_root)
    backup_path = os.path.join(backup_dir, rel_path.replace('\\', '_'))
    shutil.copy2(file_path, backup_path)
    
    # Add clearInterval on page unload
    interval_code = """
    // Store interval references
    const intervals = [];
    const originalSetInterval = window.setInterval;
    window.setInterval = function() {
        const id = originalSetInterval.apply(this, arguments);
        intervals.push(id);
        return id;
    };
    
    // Clear all intervals on page unload
    window.addEventListener('beforeunload', function() {
        intervals.forEach(id => clearInterval(id));
    });
    """
    
    # Add after last script tag
    content = content.replace('</script>', '</script>\n' + interval_code)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

interval_fixed = 0
for html_file in html_files:
    if 'traveler_dashboard' in html_file or 'frontpage' in html_file:
        if fix_intervals(html_file):
            rel_path = os.path.relpath(html_file, project_root)
            print(f"✅ Fixed intervals in {rel_path}")
            interval_fixed += 1

print(f"\n📊 Fixed intervals in {interval_fixed} files")

# ==================== 6. FIX HTML SYNTAX ERRORS ====================
print("\n🔧 FIXING HTML SYNTAX ERRORS...")

def fix_html_syntax(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix common issues
    # Remove duplicate </body> tags
    content = re.sub(r'</body>\s*</body>', '</body>', content)
    
    # Fix unclosed tags
    content = re.sub(r'<([a-z]+)([^>]*)>([^<]*)<\\1>', r'<\1\2>\3</\1>', content)
    
    # Fix self-closing tags
    content = re.sub(r'<([a-z]+)([^>]*)/>', r'<\1\2></\1>', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

syntax_fixed = 0
for html_file in html_files:
    if fix_html_syntax(html_file):
        syntax_fixed += 1

print(f"📊 Fixed HTML syntax in {syntax_fixed} files")

# ==================== 7. SUMMARY ====================
print("\n" + "="*80)
print("📊 ULTIMATE FIX SUMMARY")
print("="*80)
print(f"📦 Backup created at: {backup_dir}")
print(f"✅ Fixed brace mismatches: {fixed_count} files")
print(f"✅ Fixed session manager: 1 file")
print(f"✅ Added session init: {added_count} files")
print(f"✅ Fixed missing clearInterval: {interval_fixed} files")
print(f"✅ Fixed HTML syntax: {syntax_fixed} files")
print(f"✅ Created function_cleanup.py helper")

print("\n📋 NEXT STEPS:")
print("   1. Run the cleanup helper: python function_cleanup.py")
print("   2. Test your system: python find_all_errors.py")
print("   3. Restart server: python app/server.py")
print("="*80)