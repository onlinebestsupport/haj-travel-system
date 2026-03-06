# test_css_files.py
import os
import hashlib

print("="*60)
print("🔍 CSS FILE INVENTORY")
print("="*60)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"
css_files = []

# Find all CSS files
for root, dirs, files in os.walk(project_root):
    for file in files:
        if file.endswith('.css'):
            full_path = os.path.join(root, file)
            size = os.path.getsize(full_path)
            rel_path = os.path.relpath(full_path, project_root)
            css_files.append((rel_path, size, full_path))

# Sort by size
css_files.sort(key=lambda x: x[1], reverse=True)

print(f"\n📊 Found {len(css_files)} CSS files:\n")
print(f"{'FILE':<50} {'SIZE':<10} {'STATUS'}")
print("-" * 80)

for rel_path, size, full_path in css_files:
    # Determine status
    if 'admin-style.css' in rel_path:
        status = "✅ ADMIN MAIN"
    elif 'style.css' in rel_path and 'admin' not in rel_path:
        status = "✅ PUBLIC MAIN"
    elif '.bak' in rel_path:
        status = "🗑️  BACKUP (can delete)"
    elif 'fixes.css' in rel_path:
        status = "⚠️  OLD (use admin-style.css)"
    else:
        status = "❓ UNKNOWN"
    
    print(f"{rel_path:<50} {size:<10} {status}")

# Check which HTML files use which CSS
print("\n" + "="*60)
print("🔍 HTML CSS USAGE CHECK")
print("="*60)

html_files = []
for root, dirs, files in os.walk(os.path.join(project_root, 'public')):
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

print(f"\n📊 Checking {len(html_files)} HTML files:\n")

admin_css_count = 0
public_css_count = 0
old_css_count = 0
no_css_count = 0

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    rel_path = os.path.relpath(html_file, project_root)
    
    if 'admin-style.css' in content:
        print(f"✅ {rel_path} - using admin-style.css")
        admin_css_count += 1
    elif 'style.css' in content and 'admin' not in rel_path:
        print(f"✅ {rel_path} - using public style.css")
        public_css_count += 1
    elif 'style.css' in content and 'admin' in rel_path:
        print(f"⚠️ {rel_path} - using WRONG CSS (should be admin-style.css)")
        old_css_count += 1
    elif '.css' in content:
        print(f"⚠️ {rel_path} - using other CSS")
    else:
        print(f"❌ {rel_path} - NO CSS FOUND")
        no_css_count += 1

print("\n" + "="*60)
print("📊 SUMMARY")
print("="*60)
print(f"✅ Admin pages using admin-style.css: {admin_css_count}")
print(f"✅ Public pages using style.css: {public_css_count}")
print(f"⚠️  Pages using wrong CSS: {old_css_count}")
print(f"❌ Pages with no CSS: {no_css_count}")

# File size check
print("\n" + "="*60)
print("📏 CSS FILE SIZES")
print("="*60)
for rel_path, size, _ in css_files:
    if 'admin-style.css' in rel_path:
        print(f"📊 Admin CSS: {rel_path} - {size:,} bytes")
    elif 'style.css' in rel_path and 'admin' not in rel_path:
        print(f"📊 Public CSS: {rel_path} - {size:,} bytes")

# Suggest deletions
print("\n" + "="*60)
print("🗑️  CLEANUP SUGGESTIONS")
print("="*60)
for rel_path, size, full_path in css_files:
    if '.bak' in rel_path or 'fixes.css' in rel_path:
        print(f"   Delete: {rel_path} ({size:,} bytes)")

print("\n" + "="*60)