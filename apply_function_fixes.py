# apply_function_fixes.py
import os

print("="*70)
print("🔧 APPLYING FUNCTION FIXES")
print("="*70)

project_root = r"C:\\Users\\Masood\\Desktop\\haj-travel-system\\haj-travel-system"

replacements = {
    'checkAuth': 'SessionManager.checkAuth',
    'showNotification': 'SessionManager.showNotification',
    'previousPage': 'SessionManager.previousPage',
    'nextPage': 'SessionManager.nextPage',
    'closeAllModals': 'SessionManager.closeAllModals',
    'checkAdminSession': 'SessionManager.checkAdminSession',
    'resetFilters': 'SessionManager.resetFilters',
}

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

print("\n✅ Function replacements complete!")
print("="*70)
