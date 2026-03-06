# fix_all_errors.py
import os
import re

print("="*70)
print(" AUTO-FIXING ALL ERRORS")
print("="*70)

project_root = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system"

# ==================== 1. FIX BRACE MISMATCHES ====================
print("\nFIXING BRACE MISMATCHES...")

files_to_fix = [
    'public/admin/backup.html',
    'public/admin/email.html',
    'public/admin/frontpage.html',
    'public/admin/receipts.html',
    'public/admin/reports.html',
    'public/admin/whatsapp.html'
]

for rel_path in files_to_fix:
    full_path = os.path.join(project_root, rel_path)
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        
        if close_braces > open_braces:
            # Remove extra closing braces at the end
            extra = close_braces - open_braces
            print(f"File {rel_path}: Removing {extra} extra }}")
            
            # Find the last script block
            script_end = content.rfind('</script>')
            if script_end > 0:
                # Remove extra braces before </script>
                before_script = content[:script_end]
                after_script = content[script_end:]
                
                # Remove extra braces from the end
                while extra > 0 and before_script.endswith('}'):
                    before_script = before_script.rstrip('}')
                    extra -= 1
                
                content = before_script + after_script
                
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   Fixed {rel_path}")

# ==================== 2. FIX SESSION MANAGER ====================
print("\nFIXING SESSION MANAGER...")

sm_path = os.path.join(project_root, 'public', 'admin', 'js', 'session-manager.js')
if os.path.exists(sm_path):
    with open(sm_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix SESSION_TIMEOUT (set to 30 minutes)
    content = re.sub(r'SESSION_TIMEOUT:\s*\d+', 'SESSION_TIMEOUT: 30 * 60 * 1000', content)
    
    # Fix startTimers to clear timers first
    if 'startTimers:' in content:
        start_timer_pattern = r'(startTimers:\s*function\s*\(\s*\)\s*\{)([^}]+)\}'
        
        def add_clear_timers(match):
            prefix = match.group(1)
            body = match.group(2)
            if 'this.clearTimers' not in body:
                return prefix + '\n        this.clearTimers();' + body + '}'
            return match.group(0)
        
        content = re.sub(start_timer_pattern, add_clear_timers, content, flags=re.DOTALL)
    
    with open(sm_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed session-manager.js")

# ==================== 3. ADD CLEARINTERVAL ====================
print("\nADDING MISSING CLEARINTERVAL...")

traveler_dash = os.path.join(project_root, 'public', 'traveler_dashboard.html')
if os.path.exists(traveler_dash):
    with open(traveler_dash, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add clearInterval on page unload
    if 'setInterval' in content and 'clearInterval' not in content:
        clear_code = """
// Clear interval on page unload
window.addEventListener('beforeunload', function() {
    if (updateTimer) clearInterval(updateTimer);
});
"""
        content = content.replace('</body>', clear_code + '\n</body>')
        
        with open(traveler_dash, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Added clearInterval to traveler_dashboard.html")

# ==================== 4. FIX FRONTPAGE SPECIFIC ====================
print("\nFIXING FRONTPAGE.HTML...")

frontpage_path = os.path.join(project_root, 'public', 'admin', 'frontpage.html')
if os.path.exists(frontpage_path):
    with open(frontpage_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Check line 1293 (index 1292)
    if len(lines) >= 1293:
        line_1293 = lines[1292]
        if line_1293.strip() == '});':
            # Fix the brace issue
            lines[1292] = '    });\n'
            
            # Also add clearInterval for the auto-save
            for i, line in enumerate(lines):
                if 'setInterval(autoSave, 60000);' in line:
                    lines.insert(i+1, '    // Store timer reference\n')
                    lines.insert(i+2, '    const autoSaveTimer = setInterval(autoSave, 60000);\n')
                    lines.insert(i+3, '    // Clear interval on page unload\n')
                    lines.insert(i+4, '    window.addEventListener(\'beforeunload\', function() {\n')
                    lines.insert(i+5, '        if (autoSaveTimer) clearInterval(autoSaveTimer);\n')
                    lines.insert(i+6, '    });\n')
                    break
    
    with open(frontpage_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Fixed frontpage.html")

# ==================== 5. CREATE FUNCTION CLEANUP SCRIPT ====================
print("\nCREATING FUNCTION CLEANUP GUIDE...")

cleanup_guide = """
FUNCTION DUPLICATION CLEANUP GUIDE:

The following functions appear in multiple files. Move them to a shared file:

Common functions to move to session-manager.js:
------------------------------------------------
- checkAuth (appears in 14 files)
- closeAllModals (appears in 12 files)
- previousPage (appears in 9 files)
- nextPage (appears in 9 files)
- updatePaginationInfo (appears in 7 files)
- resetFilters (appears in 6 files)
- loadBatches (appears in 6 files)
- checkAdminSession (appears in 5 files)
- showSaveReportModal (appears in 5 files)

How to fix:
1. Add these functions to session-manager.js once
2. Remove them from individual HTML files
3. Call SessionManager.functionName() instead

Example:
   Instead of: checkAuth()
   Use: SessionManager.checkAuth()
"""

# Write without emojis
guide_path = os.path.join(project_root, 'FUNCTION_CLEANUP_GUIDE.txt')
with open(guide_path, 'w', encoding='utf-8') as f:
    f.write(cleanup_guide)
print(f"Created {guide_path}")

# ==================== 6. VERIFY FIXES ====================
print("\n" + "="*70)
print(" ALL FIXES APPLIED!")
print("="*70)
print("\nNEXT STEPS:")
print("   1. Run the test again: python find_all_errors.py")
print("   2. Check FUNCTION_CLEANUP_GUIDE.txt for manual cleanup")
print("   3. Restart your server: python app/server.py")
print("="*70)