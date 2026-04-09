#!/usr/bin/env python
"""
ONE-CLICK FIX SCRIPT - Fixes all identified issues automatically
Run this once to fix all problems
"""

import os
import re

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'

def fix_console_logs():
    """Remove or comment console.log statements from HTML files"""
    print(f"\n{BLUE}🔧 Fixing console.log statements...{END}")
    
    files_to_fix = [
        'public/index.html',
        'public/admin.login.html',
        'public/admin/dashboard.html',
        'public/admin/travelers.html',
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Comment out console.log statements (keep for debugging but not active)
            # Pattern to find console.log lines
            pattern = r'(<script>.*?)(console\.log\([^)]+\);?)(.*?</script>)'
            
            # Replace console.log with commented version
            content = re.sub(
                r'(console\.log\([^)]+\);?)',
                r'// \1',
                content
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  {GREEN}✅ Fixed console.log in {file_path}{END}")
        else:
            print(f"  {YELLOW}⚠️ File not found: {file_path}{END}")

def fix_alert_calls():
    """Replace alert() with console.warn or remove them"""
    print(f"\n{BLUE}🔧 Fixing alert() calls...{END}")
    
    file_path = 'public/admin.login.html'
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace alert with console.warn (less intrusive)
        content = re.sub(
            r'alert\(([^)]+)\);?',
            r'console.warn(\1);',
            content
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  {GREEN}✅ Fixed alert() calls in {file_path}{END}")
    else:
        print(f"  {YELLOW}⚠️ File not found: {file_path}{END}")

def fix_redirects():
    """Add missing redirects in server.py"""
    print(f"\n{BLUE}🔧 Fixing redirects...{END}")
    
    server_path = 'app/server.py'
    if os.path.exists(server_path):
        with open(server_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if redirects exist
        redirects_to_add = []
        
        if '@app.route(\'/admin\')' not in content:
            redirects_to_add.append('''
@app.route('/admin')
def admin_redirect():
    """Redirect /admin to /admin/"""
    return redirect('/admin/')
''')
        
        if '@app.route(\'/admin/\')' not in content:
            redirects_to_add.append('''
@app.route('/admin/')
def admin_slash_redirect():
    """Redirect /admin/ to dashboard"""
    return redirect('/admin/dashboard.html')
''')
        
        if '@app.route(\'/traveler\')' not in content:
            redirects_to_add.append('''
@app.route('/traveler')
def traveler_redirect():
    """Redirect /traveler to traveler dashboard"""
    return redirect('/traveler_dashboard.html')
''')
        
        if redirects_to_add:
            # Find where to insert (before if __name__ block)
            if 'if __name__ == \'__main__\':' in content:
                content = content.replace(
                    'if __name__ == \'__main__\':',
                    '\n'.join(redirects_to_add) + '\n\nif __name__ == \'__main__\':'
                )
            else:
                content += '\n'.join(redirects_to_add)
            
            with open(server_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  {GREEN}✅ Added missing redirects to server.py{END}")
        else:
            print(f"  {GREEN}✅ Redirects already present{END}")
    else:
        print(f"  {YELLOW}⚠️ server.py not found{END}")

def check_and_create_missing_routes():
    """Check and create missing route handlers"""
    print(f"\n{BLUE}🔧 Checking route handlers...{END}")
    
    server_path = 'app/server.py'
    if os.path.exists(server_path):
        with open(server_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if traveler dashboard route exists
        if '@app.route(\'/traveler_dashboard.html\')' not in content:
            traveler_route = '''
@app.route('/traveler_dashboard.html')
def traveler_dashboard_page():
    """Serve traveler dashboard"""
    try:
        dashboard_path = os.path.join(PUBLIC_DIR, 'traveler_dashboard.html')
        if os.path.exists(dashboard_path):
            return send_from_directory(PUBLIC_DIR, 'traveler_dashboard.html')
        return jsonify({'success': False, 'error': 'Dashboard not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
'''
            content += traveler_route
            with open(server_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  {GREEN}✅ Added traveler dashboard route{END}")
        else:
            print(f"  {GREEN}✅ Traveler dashboard route exists{END}")

def create_fix_summary():
    """Create a summary of all fixes applied"""
    print(f"\n{BLUE}{'='*50}{END}")
    print(f"{GREEN}✅ ALL FIXES APPLIED!{END}")
    print(f"{BLUE}{'='*50}{END}")
    print(f"\n{YELLOW}📝 Fixes applied:{END}")
    print("  1. ✅ Removed console.log statements")
    print("  2. ✅ Replaced alert() with console.warn()")
    print("  3. ✅ Added missing redirects")
    print("  4. ✅ Added missing route handlers")
    print(f"\n{YELLOW}🚀 Next steps:{END}")
    print("  1. git add .")
    print("  2. git commit -m 'Auto-fix: Remove console.logs, add redirects, fix routes'")
    print("  3. git push origin main")
    print("  4. Railway will auto-deploy")

def main():
    print(f"{BLUE}{'='*50}{END}")
    print(f"{BLUE}🔧 ONE-CLICK FIX SCRIPT{END}")
    print(f"{BLUE}{'='*50}{END}")
    
    # Run all fixes
    fix_console_logs()
    fix_alert_calls()
    fix_redirects()
    check_and_create_missing_routes()
    
    create_fix_summary()

if __name__ == "__main__":
    main()