# function_cleanup.py
import os
import re

print("="*70)
print("🧹 FUNCTION CLEANUP UTILITY")
print("="*70)

project_root = r"C:\\Users\\Masood\\Desktop\\haj-travel-system\\haj-travel-system"

# Common functions to move to session-manager.js
common_functions = [
    'checkAuth', 'closeAllModals', 'previousPage', 'nextPage', 
    'updatePaginationInfo', 'resetFilters', 'loadBatches',
    'checkAdminSession', 'showSaveReportModal', 'closeSaveReportModal'
]

# Read all HTML files
html_files = []
for root, dirs, files in os.walk(os.path.join(project_root, 'public')):
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

print(f"\n📊 Found {len(html_files)} HTML files to process")

# Create a report
with open(os.path.join(project_root, 'FUNCTION_CLEANUP_REPORT.txt'), 'w') as report:
    report.write("FUNCTION CLEANUP REPORT\n")
    report.write("="*50 + "\n\n")
    
    for func in common_functions:
        report.write(f"\n📌 Function: {func}\n")
        report.write("-"*30 + "\n")
        found_in = []
        
        for html_file in html_files:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if func in content:
                    rel_path = os.path.relpath(html_file, project_root)
                    found_in.append(rel_path)
                    report.write(f"  • {rel_path}\n")
        
        if len(found_in) > 1:
            report.write(f"\n  ⚠️  Found in {len(found_in)} files\n")

print("\n✅ Created FUNCTION_CLEANUP_REPORT.txt")
print("\n📋 NEXT STEPS:")
print("   1. Review FUNCTION_CLEANUP_REPORT.txt")
print("   2. Add common functions to session-manager.js")
print("   3. Remove duplicates from individual HTML files")
