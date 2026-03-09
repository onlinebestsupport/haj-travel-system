# fix_file_names.py
import os
import re
from datetime import datetime

print("="*70)
print("🔧 PROJECT FILE NAME FIXER")
print("="*70)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"
backup_dir = os.path.join(project_root, f"backup_before_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

# Create backup
print(f"\n📦 Creating backup in: {backup_dir}")
os.makedirs(backup_dir, exist_ok=True)

# ====== 1. FIND FILES WITHOUT EXTENSIONS ======
print("\n🔍 FINDING FILES WITHOUT EXTENSIONS...")

files_without_ext = []
all_files = []

for root, dirs, files in os.walk(project_root):
    # Skip backup folders and virtual environments
    if any(skip in root for skip in ['backup', 'venv', '__pycache__', '.git']):
        continue
    
    for file in files:
        rel_path = os.path.relpath(os.path.join(root, file), project_root)
        all_files.append(rel_path)
        
        if '.' not in file:
            files_without_ext.append(os.path.join(root, file))
            print(f"⚠️  Found: {rel_path}")

if files_without_ext:
    print(f"\n📊 Found {len(files_without_ext)} files without extensions")
    
    # Ask user what to do
    print("\n💡 How to fix?")
    print("   1. Add .txt extension (for text files)")
    print("   2. Add .py extension (for Python files)")
    print("   3. Add .cfg extension (for config files)")
    print("   4. Skip (don't fix)")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice in ['1', '2', '3']:
        ext_map = {'1': '.txt', '2': '.py', '3': '.cfg'}
        new_ext = ext_map[choice]
        
        for file_path in files_without_ext:
            # Backup the file
            rel_path = os.path.relpath(file_path, project_root)
            backup_path = os.path.join(backup_dir, rel_path.replace('\\', '_'))
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Rename the file
            new_path = file_path + new_ext
            os.rename(file_path, new_path)
            print(f"✅ Renamed: {rel_path} → {rel_path}{new_ext}")
else:
    print("✅ No files without extensions found!")

# ====== 2. CHECK FOR CASE SENSITIVITY ISSUES ======
print("\n" + "="*70)
print("🔍 CHECKING FOR CASE SENSITIVITY ISSUES")
print("="*70)

# Build a map of lowercase filenames
file_map = {}
for file_path in all_files:
    lower_name = file_path.lower()
    if lower_name in file_map:
        file_map[lower_name].append(file_path)
    else:
        file_map[lower_name] = [file_path]

# Find case conflicts
case_conflicts = []
for lower_name, paths in file_map.items():
    if len(paths) > 1:
        case_conflicts.append(paths)
        print(f"⚠️  Case conflict: {paths}")

if case_conflicts:
    print(f"\n📊 Found {len(case_conflicts)} case conflicts")
    print("💡 These should be resolved manually - they might cause issues on Linux/Railway")
else:
    print("✅ No case sensitivity issues found!")

# ====== 3. CHECK FOR BACKUP FILES ======
print("\n" + "="*70)
print("🗑️  CHECKING FOR BACKUP FILES")
print("="*70)

backup_extensions = ['.bak', '.bak2', '.old', '.backup']
backup_files = []

for root, dirs, files in os.walk(project_root):
    if any(skip in root for skip in ['backup', 'venv', '__pycache__', '.git']):
        continue
    
    for file in files:
        if any(file.endswith(ext) for ext in backup_extensions):
            backup_files.append(os.path.join(root, file))
            rel_path = os.path.relpath(os.path.join(root, file), project_root)
            print(f"📦 Found backup: {rel_path}")

if backup_files:
    print(f"\n📊 Found {len(backup_files)} backup files")
    print("\n💡 Options:")
    print("   1. Delete all backup files")
    print("   2. Move to backup folder")
    print("   3. Skip")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        for file_path in backup_files:
            os.remove(file_path)
            rel_path = os.path.relpath(file_path, project_root)
            print(f"✅ Deleted: {rel_path}")
    elif choice == '2':
        for file_path in backup_files:
            rel_path = os.path.relpath(file_path, project_root)
            backup_path = os.path.join(backup_dir, rel_path.replace('\\', '_'))
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            os.rename(file_path, backup_path)
            print(f"✅ Moved to backup: {rel_path}")
else:
    print("✅ No backup files found!")

# ====== 4. CHECK PYTHON IMPORT STATEMENTS ======
print("\n" + "="*70)
print("🐍 CHECKING PYTHON IMPORTS")
print("="*70)

python_files = []
for root, dirs, files in os.walk(project_root):
    if any(skip in root for skip in ['venv', '__pycache__', '.git']):
        continue
    for file in files:
        if file.endswith('.py'):
            python_files.append(os.path.join(root, file))

print(f"📊 Found {len(python_files)} Python files to check")

# List of common Python packages (these are fine)
common_packages = [
    'flask', 'os', 'sys', 'json', 'datetime', 'hashlib', 'uuid', 'threading',
    'time', 'logging', 'requests', 'psycopg2', 'dotenv', 'load_dotenv',
    'functools', 'wraps', 'contextlib', 'pathlib', 're', 'glob', 'subprocess',
    'random', 'math', 'collections', 'defaultdict', 'OrderedDict'
]

# Check for missing packages
missing_packages = set()
import_pattern = r'^(?:from|import)\s+([a-zA-Z0-9_\.]+)'

for py_file in python_files:
    with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    matches = re.findall(import_pattern, content, re.MULTILINE)
    for match in matches:
        package = match.split('.')[0]  # Get base package name
        if package not in common_packages and package != 'app':
            missing_packages.add(package)

if missing_packages:
    print("\n⚠️  These packages might need to be installed:")
    for pkg in sorted(missing_packages):
        print(f"   • {pkg}")
    print("\n💡 Install with: pip install " + " ".join(missing_packages))
else:
    print("✅ All imports look good!")

# ====== 5. CHECK FOR DUPLICATE CSS FILES ======
print("\n" + "="*70)
print("🎨 CHECKING FOR DUPLICATE CSS FILES")
print("="*70)

css_files = []
for root, dirs, files in os.walk(project_root):
    if any(skip in root for skip in ['venv', '__pycache__', '.git']):
        continue
    for file in files:
        if file.endswith('.css'):
            css_files.append(os.path.join(root, file))

# Group by filename
css_by_name = {}
for css_file in css_files:
    name = os.path.basename(css_file)
    if name not in css_by_name:
        css_by_name[name] = []
    css_by_name[name].append(css_file)

# Find duplicates
for name, paths in css_by_name.items():
    if len(paths) > 1:
        print(f"\n⚠️  Multiple copies of {name}:")
        for path in paths:
            rel_path = os.path.relpath(path, project_root)
            print(f"   • {rel_path}")

# ====== 6. CREATE REQUIREMENTS.TXT CHECK ======
print("\n" + "="*70)
print("📋 CHECKING REQUIREMENTS.TXT")
print("="*70)

req_file = os.path.join(project_root, 'requirements.txt')
if os.path.exists(req_file):
    with open(req_file, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    print(f"✅ Found requirements.txt with {len(requirements)} packages")
    
    # Check if any missing packages should be added
    if missing_packages:
        print("\n💡 Consider adding these to requirements.txt:")
        for pkg in missing_packages:
            print(f"   {pkg}")
else:
    print("⚠️  No requirements.txt found - should create one")

# ====== 7. CREATE .ENV EXAMPLE CHECK ======
print("\n" + "="*70)
print("🔐 CHECKING .ENV FILE")
print("="*70)

env_file = os.path.join(project_root, '.env')
env_example = os.path.join(project_root, '.env.example')

if os.path.exists(env_file):
    print("✅ .env file exists")
else:
    print("⚠️  No .env file found")

if os.path.exists(env_example):
    print("✅ .env.example file exists")
else:
    print("⚠️  No .env.example file found - should create one")

# ====== 8. SUMMARY REPORT ======
print("\n" + "="*70)
print("📊 FIXER SUMMARY")
print("="*70)
print(f"📦 Backup created at: {backup_dir}")
print(f"📊 Total files processed: {len(all_files)}")

if files_without_ext:
    print(f"\n✅ Fixed {len(files_without_ext)} files without extensions")
if backup_files and choice in ['1', '2']:
    print(f"✅ Cleaned up {len(backup_files)} backup files")
if case_conflicts:
    print(f"\n⚠️  {len(case_conflicts)} case conflicts need manual review")

print("\n" + "="*70)
print("🎉 FILE NAME FIXING COMPLETE!")
print("="*70)
print("\n📋 NEXT STEPS:")
print("   1. Run the test again: python test_file_mismatches.py")
print("   2. If any issues remain, they'll need manual review")
print("   3. Commit changes to Git: git add . && git commit -m 'Fixed file names'")
print("="*70)
