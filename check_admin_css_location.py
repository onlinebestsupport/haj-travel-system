# check_admin_css_location.py
import os

print("="*60)
print("🔍 CHECKING ALL admin-style.css LOCATIONS")
print("="*60)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"
found_files = []

# Search for all admin-style.css files
for root, dirs, files in os.walk(project_root):
    for file in files:
        if file == "admin-style.css":
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, project_root)
            size = os.path.getsize(full_path)
            found_files.append((rel_path, size))

print(f"\n📊 Found {len(found_files)} admin-style.css files:\n")

correct_location = "public\\admin\\admin-style.css"
correct_count = 0
incorrect_count = 0

for rel_path, size in found_files:
    if rel_path == correct_location:
        print(f"✅ {rel_path} - {size:,} bytes - CORRECT LOCATION")
        correct_count += 1
    else:
        print(f"❌ {rel_path} - {size:,} bytes - WRONG LOCATION")
        incorrect_count += 1

print("\n" + "="*60)
print("📊 SUMMARY")
print("="*60)
print(f"✅ Correct location files: {correct_count}")
print(f"❌ Wrong location files: {incorrect_count}")

if correct_count == 1 and incorrect_count == 0:
    print("\n🎉 PERFECT! Only one admin-style.css in the correct location!")
elif correct_count == 1 and incorrect_count > 0:
    print(f"\n⚠️  Found {incorrect_count} duplicate files that should be deleted:")
    for rel_path, size in found_files:
        if rel_path != correct_location:
            print(f"   • {rel_path} ({size:,} bytes)")
    print("\n💡 To delete duplicates:")
    for rel_path, size in found_files:
        if rel_path != correct_location:
            full_path = os.path.join(project_root, rel_path)
            print(f"   del \"{full_path}\"")
elif correct_count == 0:
    print("\n❌ CRITICAL: No admin-style.css found in correct location!")
    print("💡 The correct location should be: public\\admin\\admin-style.css")
elif correct_count > 1:
    print(f"\n❌ Multiple admin-style.css files in correct location: {correct_count}")
    print("💡 Keep only the largest/most recent one")

# Also check for any style.css in admin folders
print("\n" + "="*60)
print("🔍 CHECKING FOR style.css IN ADMIN FOLDERS")
print("="*60)

admin_style_files = []
for root, dirs, files in os.walk(project_root):
    if 'admin' in root.split(os.sep):
        for file in files:
            if file == "style.css" and not file.endswith('.bak'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, project_root)
                size = os.path.getsize(full_path)
                admin_style_files.append((rel_path, size))

if admin_style_files:
    print("\n⚠️  Found style.css files in admin folders (should use admin-style.css):")
    for rel_path, size in admin_style_files:
        print(f"   • {rel_path} ({size:,} bytes)")
else:
    print("\n✅ No style.css files found in admin folders - GOOD!")

print("\n" + "="*60)