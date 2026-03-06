# fix_duplicate_functions.py
import os
import re
from collections import defaultdict

print("="*70)
print("🔧 FIXING DUPLICATE FUNCTIONS")
print("="*70)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"
session_manager_path = os.path.join(project_root, 'public', 'admin', 'js', 'session-manager.js')

# Common functions that should be in session-manager.js
common_functions = {
    'checkAuth': '''    checkAuth: function() {
        const isLoggedIn = sessionStorage.getItem('adminLoggedIn');
        if (!isLoggedIn) {
            window.location.href = '/admin.login.html';
            return false;
        }
        return true;
    },''',
    
    'closeAllModals': '''    closeAllModals: function() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => modal.style.display = 'none');
        const overlay = document.getElementById('modalOverlay');
        if (overlay) overlay.style.display = 'none';
    },''',
    
    'previousPage': '''    previousPage: function(currentPage, callback) {
        if (currentPage > 1) {
            callback(currentPage - 1);
        }
    },''',
    
    'nextPage': '''    nextPage: function(currentPage, totalPages, callback) {
        if (currentPage < totalPages) {
            callback(currentPage + 1);
        }
    },''',
    
    'resetFilters': '''    resetFilters: function(searchId, roleId, statusId, displayCallback) {
        if (searchId) document.getElementById(searchId).value = '';
        if (roleId) document.getElementById(roleId).value = 'all';
        if (statusId) document.getElementById(statusId).value = 'all';
        if (displayCallback) displayCallback();
    },''',
    
    'showNotification': '''    showNotification: function(message, type = 'success') {
        const notification = document.getElementById('notification');
        if (!notification) return;
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `<i class="fas fa-${
            type === 'success' ? 'check-circle' : 
            type === 'error' ? 'exclamation-circle' : 'info-circle'
        }"></i> ${message}`;
        notification.style.display = 'block';
        setTimeout(() => notification.style.display = 'none', 3000);
    },''',
    
    'checkAdminSession': '''    checkAdminSession: async function() {
        try {
            const response = await fetch('/api/check-session', {
                credentials: 'include',
                headers: { 'Cache-Control': 'no-cache' }
            });
            const data = await response.json();
            return data.authenticated || false;
        } catch (error) {
            console.error('Session check failed:', error);
            return false;
        }
    },'''
}

# Read current session-manager.js
with open(session_manager_path, 'r', encoding='utf-8') as f:
    sm_content = f.read()

# Add missing common functions
added = 0
for func_name, func_code in common_functions.items():
    if func_name not in sm_content:
        # Insert before the last '}'
        last_brace = sm_content.rfind('}')
        if last_brace > 0:
            sm_content = sm_content[:last_brace] + '\n' + func_code + '\n' + sm_content[last_brace:]
            print(f"✅ Added {func_name} to session-manager.js")
            added += 1

if added > 0:
    with open(session_manager_path, 'w', encoding='utf-8') as f:
        f.write(sm_content)
    print(f"\n📊 Added {added} common functions to session-manager.js")
else:
    print("✅ All common functions already present")

# Now scan HTML files and create a report of where to replace
print("\n📋 Scanning HTML files for duplicate functions...")

html_files = []
for root, dirs, files in os.walk(os.path.join(project_root, 'public')):
    if 'backup' not in root and 'admin' in root:
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))

function_usage = defaultdict(list)

for html_file in html_files:
    rel_path = os.path.relpath(html_file, project_root)
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for func_name in common_functions.keys():
        if func_name in content and f'SessionManager.{func_name}' not in content:
            # Find line numbers
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if f'function {func_name}(' in line or f'{func_name} = function' in line:
                    function_usage[func_name].append((rel_path, i))

# Create a fix script
fix_script = """# apply_function_fixes.py
import os

print("="*70)
print("🔧 APPLYING FUNCTION FIXES")
print("="*70)

project_root = r"C:\\\\Users\\\\Masood\\\\Desktop\\\\haj-travel-system\\\\haj-travel-system"

replacements = {
"""

for func_name, locations in function_usage.items():
    fix_script += f"    '{func_name}': 'SessionManager.{func_name}',\n"

fix_script += """}

# Process HTML files
html_files = []
for root, dirs, files in os.walk(os.path.join(project_root, 'public')):
    if 'backup' not in root:
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for old, new in replacements.items():
        # Replace function calls
        content = content.replace(old + '(', new + '(')
    
    if original != content:
        rel_path = os.path.relpath(html_file, project_root)
        print(f"✅ Updated {rel_path}")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)

print("\\n✅ Function replacements complete!")
print("="*70)
"""

with open(os.path.join(project_root, 'apply_function_fixes.py'), 'w', encoding='utf-8') as f:
    f.write(fix_script)

# Create a report
print("\n📊 DUPLICATE FUNCTIONS REPORT:")
print("-" * 40)

total_duplicates = 0
for func_name, locations in function_usage.items():
    if len(locations) > 1:
        print(f"\n📌 {func_name} appears in {len(locations)} files:")
        total_duplicates += len(locations)
        for loc, line in locations[:5]:  # Show first 5
            print(f"   • {loc}:{line}")
        if len(locations) > 5:
            print(f"   • ... and {len(locations)-5} more")

print(f"\n📊 Total duplicate function instances: {total_duplicates}")
print("\n✅ Created apply_function_fixes.py to automatically fix these")

print("\n" + "="*70)
print("📋 NEXT STEPS:")
print("   1. Run: python fix_session_manager.py")
print("   2. Run: python apply_function_fixes.py")
print("   3. Run: python find_all_errors.py")
print("="*70)