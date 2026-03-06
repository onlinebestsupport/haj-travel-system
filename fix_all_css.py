# fix_all_css.py
import os

print("="*70)
print("🔧 FIXING ALL CSS REFERENCES")
print("="*70)

admin_dir = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system\public\admin"
fixed_count = 0

# Fix all admin HTML files
for filename in os.listdir(admin_dir):
    if not filename.endswith('.html'):
        continue
    
    filepath = os.path.join(admin_dir, filename)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changed = False
    
    # Fix style.css → /admin/admin-style.css
    if 'href="style.css"' in content:
        content = content.replace('href="style.css"', 'href="/admin/admin-style.css"')
        print(f"✅ {filename}: Changed style.css → /admin/admin-style.css")
        changed = True
    
    # Fix href="admin-style.css" → href="/admin/admin-style.css"
    if 'href="admin-style.css"' in content:
        content = content.replace('href="admin-style.css"', 'href="/admin/admin-style.css"')
        print(f"✅ {filename}: Fixed path for admin-style.css")
        changed = True
    
    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        fixed_count += 1

print(f"\n✅ Fixed {fixed_count} files")

# Check admin.login.html separately
login_file = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system\public\admin.login.html"
with open(login_file, 'r', encoding='utf-8') as f:
    content = f.read()

if 'href="/admin/admin-style.css"' in content:
    print(f"✅ admin.login.html already correct")
else:
    print(f"⚠️ admin.login.html needs check")

print("\n" + "="*70)
print("📋 VERIFICATION COMMAND:")
print("python test_css_references.py")
print("="*70)