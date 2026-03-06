# consolidate_functions.py
import os
import re

print("="*70)
print("📦 FUNCTION CONSOLIDATION UTILITY")
print("="*70)

project_root = r"C:\\Users\\Masood\\Desktop\\haj-travel-system\\haj-travel-system"
session_manager_path = os.path.join(project_root, 'public', 'admin', 'js', 'session-manager.js')

# Read all HTML files to find duplicate functions
html_files = []
for root, dirs, files in os.walk(os.path.join(project_root, 'public')):
    if 'backup' not in root:
        for file in files:
            if file.endswith('.html') and 'admin' in root:
                html_files.append(os.path.join(root, file))

print(f"\n📊 Found {len(html_files)} admin HTML files")

# Create a report of duplicate functions
function_count = {}
function_locations = {}

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find function definitions
    functions = re.findall(r'function\s+(\w+)\s*\(', content)
    for func in functions:
        if func not in function_count:
            function_count[func] = 0
            function_locations[func] = []
        function_count[func] += 1
        function_locations[func].append(os.path.basename(html_file))

# Write report
report_path = os.path.join(project_root, 'DUPLICATE_FUNCTIONS_REPORT.txt')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("DUPLICATE FUNCTIONS REPORT\n")
    f.write("="*50 + "\n\n")
    
    for func, count in sorted(function_count.items(), key=lambda x: x[1], reverse=True):
        if count > 1 and func not in ['logout', 'escapeHtml']:
            f.write(f"📌 {func} appears in {count} files:\n")
            for loc in function_locations[func][:5]:
                f.write(f"   • {loc}\n")
            if len(function_locations[func]) > 5:
                f.write(f"   • ... and {len(function_locations[func])-5} more\n")
            f.write("\n")

print(f"✅ Created report: DUPLICATE_FUNCTIONS_REPORT.txt")
print("\n📋 NEXT STEPS:")
print("   1. Review DUPLICATE_FUNCTIONS_REPORT.txt")
print("   2. Add common functions to session-manager.js")
print("   3. Update HTML files to use SessionManager.functionName()")
print("="*70)
