# fix_null_to_undefined.py
import os

print("="*70)
print("🔧 FIXING NULL TO UNDEFINED")
print("="*70)

# Use relative paths (current directory)
project_root = "."

# Process all HTML files
html_files = []
for root, dirs, files in os.walk(os.path.join(project_root, 'public')):
    if 'backup' not in root:
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))

fixed_count = 0
for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace '= null;' with '= undefined;'
    if '= null;' in content:
        new_content = content.replace('= null;', '= undefined;')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        fixed_count += 1
        print(f"✅ Fixed null in {os.path.basename(html_file)}")

print(f"\n📊 Fixed null to undefined in {fixed_count} files")
print("="*70)
