# test_css_references.py
import os
import re
from collections import defaultdict

print("="*70)
print("🔍 COMPLETE PROJECT CSS REFERENCE TEST")
print("="*70)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"

# Files to check
html_files = []
py_files = []
js_files = []

# Collect all files
for root, dirs, files in os.walk(project_root):
    # Skip backup folders and virtual environments
    if 'backup' in root or 'venv' in root or '__pycache__' in root or '.git' in root:
        continue
    
    for file in files:
        full_path = os.path.join(root, file)
        rel_path = os.path.relpath(full_path, project_root)
        
        if file.endswith('.html'):
            html_files.append((rel_path, full_path))
        elif file.endswith('.py'):
            py_files.append((rel_path, full_path))
        elif file.endswith('.js'):
            js_files.append((rel_path, full_path))

print(f"\n📊 Files to check:")
print(f"   • HTML files: {len(html_files)}")
print(f"   • Python files: {len(py_files)}")
print(f"   • JavaScript files: {len(js_files)}")

# Patterns to search for
css_patterns = {
    'admin_style_correct': r'["\']/admin/admin-style\.css["\']',
    'admin_style_root': r'["\']admin-style\.css["\']',
    'style_css': r'["\']style\.css["\']',
    'fixes_css': r'["\']fixes\.css["\']',
    'other_css': r'["\'][\w\/-]+\.css["\']'
}

# Results storage
results = {
    'admin_style_correct': [],  # /admin/admin-style.css
    'admin_style_root': [],     # admin-style.css
    'style_css': [],            # style.css
    'fixes_css': [],            # fixes.css
    'other_css': []             # any other .css files
}

# Check HTML files
print("\n" + "="*70)
print("📄 CHECKING HTML FILES")
print("="*70)

for rel_path, full_path in html_files:
    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Skip backup files
    if 'backup' in rel_path:
        continue
    
    # Check for CSS references
    if '/admin/admin-style.css' in content:
        results['admin_style_correct'].append(rel_path)
        print(f"✅ {rel_path} - CORRECT: uses /admin/admin-style.css")
    elif 'admin-style.css' in content and '/admin/' not in content:
        results['admin_style_root'].append(rel_path)
        print(f"⚠️  {rel_path} - MAYBE WRONG: uses admin-style.css (no path)")
    elif 'style.css' in content:
        if 'admin' in rel_path:
            results['style_css'].append(rel_path)
            print(f"❌ {rel_path} - WRONG: admin page using style.css")
        else:
            results['style_css'].append(rel_path)
            print(f"✅ {rel_path} - CORRECT: public page using style.css")
    elif 'fixes.css' in content:
        results['fixes_css'].append(rel_path)
        print(f"❌ {rel_path} - WRONG: using old fixes.css")
    else:
        # Check for any other CSS
        css_match = re.search(r'["\']([\w\/-]+\.css)["\']', content)
        if css_match:
            css_file = css_match.group(1)
            results['other_css'].append((rel_path, css_file))
            print(f"❓ {rel_path} - UNKNOWN: uses {css_file}")

# Check Python files for CSS routes
print("\n" + "="*70)
print("🐍 CHECKING PYTHON FILES (Flask routes)")
print("="*70)

for rel_path, full_path in py_files:
    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Check for CSS routes in Flask
    if '@app.route' in content and ('.css' in content or 'style.css' in content):
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if '.css' in line and ('@app.route' in line or 'send_from_directory' in line):
                print(f"📌 {rel_path}:{i} - {line.strip()}")

# Check JavaScript files for CSS references
print("\n" + "="*70)
print("📜 CHECKING JAVASCRIPT FILES")
print("="*70)

for rel_path, full_path in js_files:
    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    if '.css' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if '.css' in line:
                print(f"📌 {rel_path}:{i} - {line.strip()[:100]}")

# ====== SUMMARY ======
print("\n" + "="*70)
print("📊 CSS REFERENCE SUMMARY")
print("="*70)

print(f"\n✅ CORRECT: Using /admin/admin-style.css:")
for item in results['admin_style_correct']:
    print(f"   • {item}")

print(f"\n⚠️  MAYBE WRONG: Using admin-style.css without path:")
for item in results['admin_style_root']:
    print(f"   • {item}")

print(f"\n❌ WRONG: Admin pages using style.css:")
for item in results['style_css']:
    if 'admin' in item:
        print(f"   • {item}")

print(f"\n✅ CORRECT: Public pages using style.css:")
for item in results['style_css']:
    if 'admin' not in item and 'backup' not in item:
        print(f"   • {item}")

print(f"\n❌ WRONG: Using old fixes.css:")
for item in results['fixes_css']:
    print(f"   • {item}")

# Count issues
total_issues = len(results['admin_style_root']) + len([x for x in results['style_css'] if 'admin' in x]) + len(results['fixes_css'])

print("\n" + "="*70)
print("📈 ISSUE COUNT")
print("="*70)
print(f"✅ Correct references: {len(results['admin_style_correct'])}")
print(f"⚠️  Needs attention: {len(results['admin_style_root'])}")
print(f"❌ Wrong references: {len([x for x in results['style_css'] if 'admin' in x]) + len(results['fixes_css'])}")
print(f"📊 Total issues: {total_issues}")

if total_issues == 0:
    print("\n🎉 PERFECT! All CSS references are correct!")
else:
    print(f"\n🔧 Files to fix: {total_issues}")
    print("\n💡 RECOMMENDED FIXES:")
    print("   1. For admin pages: Change 'style.css' → '/admin/admin-style.css'")
    print("   2. For admin pages: Change 'admin-style.css' → '/admin/admin-style.css'")
    print("   3. Delete any 'fixes.css' references")

print("\n" + "="*70)
