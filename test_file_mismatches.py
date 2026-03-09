# test_file_mismatches.py
import os
import re
from collections import defaultdict

print("="*80)
print("🔍 COMPLETE FILE NAME MISMATCH TESTER")
print("="*80)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"

# Get all actual files in the project
actual_files = set()
file_extensions = defaultdict(list)

for root, dirs, files in os.walk(project_root):
    # Skip backup folders, virtual environments, etc.
    if any(skip in root for skip in ['backup', 'venv', '__pycache__', '.git']):
        continue
    
    for file in files:
        rel_path = os.path.relpath(os.path.join(root, file), project_root)
        actual_files.add(rel_path)
        
        # Group by extension
        ext = os.path.splitext(file)[1].lower()
        file_extensions[ext].append(rel_path)

print(f"\n📊 Total actual files found: {len(actual_files)}")
print("\n📁 Files by extension:")
for ext in sorted(file_extensions.keys()):
    print(f"   {ext}: {len(file_extensions[ext])} files")

# ====== PATTERNS TO SEARCH ======
patterns = [
    # HTML/CSS/JS references
    (r'["\']([\w\/\.-]+\.html)["\']', 'HTML links'),
    (r'["\']([\w\/\.-]+\.css)["\']', 'CSS links'),
    (r'["\']([\w\/\.-]+\.js)["\']', 'JavaScript links'),
    (r'["\']([\w\/\.-]+\.png)["\']', 'PNG images'),
    (r'["\']([\w\/\.-]+\.jpg)["\']', 'JPG images'),
    (r'["\']([\w\/\.-]+\.svg)["\']', 'SVG images'),
    (r'["\']([\w\/\.-]+\.ico)["\']', 'ICO files'),
    (r'["\']([\w\/\.-]+\.woff2?)["\']', 'Font files'),
    
    # Python imports
    (r'from ([\w\.]+) import', 'Python imports (from)'),
    (r'import ([\w\.]+)', 'Python imports (import)'),
    (r'blueprint.*[\'"]([\w-]+)[\'"]', 'Blueprint names'),
    (r'url_prefix.*[\'"]([\w\/-]+)[\'"]', 'URL prefixes'),
    
    # Flask routes
    (r'@app\.route\([\'"]([\w\/-]+)[\'"]', 'Flask routes'),
    (r'@bp\.route\([\'"]([\w\/-]+)[\'"]', 'Blueprint routes'),
    (r'redirect\([\'"]([\w\/-]+)[\'"]', 'Redirects'),
    (r'url_for\([\'"]([\w\.-]+)[\'"]', 'url_for references'),
    
    # JavaScript
    (r'fetch\([\'"]([\w\/\.-]+)[\'"]', 'fetch API calls'),
    (r'window\.location[\s]*=[\s]*[\'"]([\w\/\.-]+)[\'"]', 'window.location redirects'),
    (r'\.href[\s]*=[\s]*[\'"]([\w\/\.-]+)[\'"]', 'href assignments'),
    
    # Images in CSS
    (r'url\([\'"]?([\w\/\.-]+\.(png|jpg|svg|gif))[\'"]?\)', 'CSS background images'),
    
    # File operations
    (r'open\([\'"]([\w\/\.-]+)[\'"]', 'file open operations'),
    (r'send_from_directory.*[\'"]([\w\/\.-]+)[\'"]', 'send_from_directory'),
    (r'os\.path\.join\(.*[\'"]([\w\/\.-]+)[\'"]', 'os.path.join references'),
]

# Collect all references
all_references = []
file_references = defaultdict(list)

print("\n" + "="*80)
print("📄 SCANNING FILES FOR REFERENCES")
print("="*80)

# Scan all files
file_count = 0
for root, dirs, files in os.walk(project_root):
    if any(skip in root for skip in ['backup', 'venv', '__pycache__', '.git']):
        continue
    
    for file in files:
        if not file.endswith(('.py', '.html', '.js', '.css')):
            continue
        
        file_path = os.path.join(root, file)
        rel_path = os.path.relpath(file_path, project_root)
        file_count += 1
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            for pattern, desc in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Handle tuple matches (like from regex groups)
                    if isinstance(match, tuple):
                        match = match[0]
                    
                    # Clean up the match
                    match = match.strip('./\\')
                    
                    if match and not match.startswith(('http', 'https', '//', 'data:')):
                        all_references.append((rel_path, match, desc))
                        file_references[rel_path].append((match, desc))
                        
        except Exception as e:
            print(f"⚠️  Error reading {rel_path}: {e}")

print(f"\n📊 Scanned {file_count} files")
print(f"📊 Found {len(all_references)} total references")

# ====== CHECK FOR MISMATCHES ======
print("\n" + "="*80)
print("🔍 CHECKING FOR FILE NAME MISMATCHES")
print("="*80)

mismatches = []
checked_pairs = set()

for ref_file, ref_name, desc in all_references:
    # Skip if it's a URL or absolute path
    if ref_name.startswith(('http', 'https', '/', '\\')):
        continue
    
    # Try different possible paths
    possible_paths = [
        ref_name,  # as is
        os.path.join('public', ref_name),  # in public folder
        os.path.join('public', 'admin', ref_name),  # in admin folder
        os.path.join('app', ref_name),  # in app folder
        os.path.join('app', 'routes', ref_name),  # in routes folder
    ]
    
    found = False
    for possible_path in possible_paths:
        # Normalize path
        possible_path = possible_path.replace('\\', '/')
        
        # Check if file exists in actual files
        for actual_file in actual_files:
            if actual_file.endswith(ref_name) or actual_file == possible_path:
                found = True
                break
        
        if found:
            break
    
    if not found:
        # Check if it's a module import (like 'flask', 'os')
        if ref_name in ['flask', 'os', 'sys', 'json', 'datetime', 'hashlib', 'uuid', 'threading', 'time', 'logging']:
            continue
        
        # Check if it's a blueprint or route
        if desc in ['Blueprint names', 'URL prefixes', 'Flask routes', 'Blueprint routes']:
            continue
        
        key = (ref_name, ref_file)
        if key not in checked_pairs:
            mismatches.append((ref_file, ref_name, desc))
            checked_pairs.add(key)

# ====== SPECIFIC CHECKS ======
print("\n" + "="*80)
print("🔧 SPECIFIC FILE CHECKS")
print("="*80)

# Check admin HTML files for correct CSS
admin_html_files = [f for f in actual_files if 'admin' in f and f.endswith('.html')]
print(f"\n📊 Checking {len(admin_html_files)} admin HTML files for CSS...")

css_issues = []
for html_file in admin_html_files:
    full_path = os.path.join(project_root, html_file)
    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    if 'admin-style.css' not in content:
        css_issues.append(html_file)

if css_issues:
    print(f"❌ {len(css_issues)} admin files missing admin-style.css:")
    for f in css_issues[:10]:
        print(f"   • {f}")
else:
    print("✅ All admin files reference admin-style.css")

# Check public HTML files for correct CSS
public_html_files = [f for f in actual_files if 'public' in f and f.endswith('.html') and 'admin' not in f]
print(f"\n📊 Checking {len(public_html_files)} public HTML files for CSS...")

public_css_issues = []
for html_file in public_html_files:
    full_path = os.path.join(project_root, html_file)
    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    if 'style.css' not in content:
        public_css_issues.append(html_file)

if public_css_issues:
    print(f"❌ {len(public_css_issues)} public files missing style.css:")
    for f in public_css_issues:
        print(f"   • {f}")
else:
    print("✅ All public files reference style.css")

# Check for missing __init__.py files
print("\n📊 Checking for missing __init__.py files...")
python_dirs = set()
for root, dirs, files in os.walk(os.path.join(project_root, 'app')):
    if any(skip in root for skip in ['__pycache__']):
        continue
    
    rel_dir = os.path.relpath(root, project_root)
    if os.path.basename(root) != 'app' and '__init__.py' not in files:
        print(f"⚠️  Missing __init__.py in {rel_dir}")

# ====== SUMMARY ======
print("\n" + "="*80)
print("📊 FILE NAME MISMATCH SUMMARY")
print("="*80)

if mismatches:
    print(f"\n❌ Found {len(mismatches)} potential file name mismatches:\n")
    for ref_file, ref_name, desc in mismatches[:20]:  # Show first 20
        print(f"   📄 {ref_file}")
        print(f"      references: '{ref_name}' ({desc})")
        print()
    
    if len(mismatches) > 20:
        print(f"   ... and {len(mismatches) - 20} more")
else:
    print("\n✅ NO FILE NAME MISMATCHES FOUND! Perfect!")

# List all file extensions found
print("\n📁 All file extensions in project:")
for ext in sorted(file_extensions.keys()):
    print(f"   {ext}: {len(file_extensions[ext])} files")

# Show sample of actual files
print("\n📋 Sample of actual files (first 20):")
sample_files = sorted(actual_files)[:20]
for f in sample_files:
    print(f"   • {f}")

print("\n" + "="*80)
if not mismatches and not css_issues and not public_css_issues:
    print("🎉 PERFECT! No file name mismatches found!")
else:
    print("⚠️  Some issues found. Check the output above.")
print("="*80)
