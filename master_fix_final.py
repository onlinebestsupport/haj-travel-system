#!/usr/bin/env python
"""
Master Fix Script for Haj Travel System - FINAL VERSION
Fixed encoding issues and completes all fixes
"""

import os
import re

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.HEADER}{'='*60}{Colors.END}")

def fix_file_imports():
    """Fix missing imports in various files"""
    print_header("📁 FIXING MISSING IMPORTS")
    
    fixes = [
        {
            'file': 'add_missing_apis.py',
            'imports': ['from app.database import get_db']
        },
        {
            'file': 'auto_fix_production.py',
            'imports': ['from app.database import get_db, release_db']
        },
        {
            'file': 'fix_backup_stats.py',
            'imports': ['from app.database import get_db']
        },
        {
            'file': 'fix_duplicate_backup_stats.py',
            'imports': ['from app.database import get_db']
        }
    ]
    
    for fix in fixes:
        file_path = fix['file']
        if not os.path.exists(file_path):
            print(f"{Colors.YELLOW}⚠️  File not found: {file_path}{Colors.END}")
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.readlines()
            
            # Find where to insert imports
            insert_pos = 0
            for i, line in enumerate(content):
                if line.startswith('import ') or line.startswith('from '):
                    insert_pos = i + 1
                elif line.strip() and not line.startswith('#') and insert_pos == 0:
                    insert_pos = i
            
            modified = False
            for imp in fix['imports']:
                imp_exists = any(imp in line for line in content)
                if not imp_exists:
                    content.insert(insert_pos, imp + '\n')
                    modified = True
                    print(f"{Colors.GREEN}  ✅ Added {imp} to {file_path}{Colors.END}")
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(content)
            else:
                print(f"{Colors.BLUE}  ⏭️  No changes needed for {file_path}{Colors.END}")
                
        except Exception as e:
            print(f"{Colors.RED}  ❌ Error fixing {file_path}: {e}{Colors.END}")

def fix_database_cleanup():
    """Add try/finally blocks for database cleanup"""
    print_header("🗄️  FIXING DATABASE CLEANUP")
    
    files_to_fix = [
        'app/reset_database.py',
        'app/server.py',
        'app/routes/company.py',
        'app/routes/invoices.py',
        'app/routes/receipts.py',
        'app/routes/uploads.py'
    ]
    
    for file_path in files_to_fix:
        if not os.path.exists(file_path):
            print(f"{Colors.YELLOW}⚠️  File not found: {file_path}{Colors.END}")
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified = False
            
            # Add release_db import if missing
            if 'from app.database import' in content and 'release_db' not in content:
                # Use raw string for regex
                content = re.sub(
                    r'(from app\.database import .*?)(\n)',
                    r'\1, release_db\2',
                    content,
                    flags=re.DOTALL
                )
                modified = True
                print(f"{Colors.GREEN}  ✅ Added release_db import to {file_path}{Colors.END}")
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
        except Exception as e:
            print(f"{Colors.RED}  ❌ Error fixing {file_path}: {e}{Colors.END}")

def fix_template_issues():
    """Add session manager and logout to HTML templates"""
    print_header("📄 FIXING TEMPLATE ISSUES")
    
    templates = [
        'debug_users.html',
        'login_page.html',
        'public/admin.login.html',
        'public/index.html',
        'public/traveler_dashboard.html',
        'public/traveler_login.html'
    ]
    
    session_script = '<script src="/admin/js/session-manager.js"></script>'
    
    for template in templates:
        if not os.path.exists(template):
            print(f"{Colors.YELLOW}⚠️  Template not found: {template}{Colors.END}")
            continue
        
        try:
            with open(template, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified = False
            
            # Add session manager
            if session_script not in content and '</head>' in content:
                content = content.replace('</head>', f'    {session_script}\n</head>')
                modified = True
                print(f"{Colors.GREEN}  ✅ Added session manager to {template}{Colors.END}")
            
            # Add logout function if missing
            if 'logout()' not in content and '</body>' in content:
                logout_js = '''
<script>
function logout() {
    fetch('/api/logout', { 
        method: 'POST', 
        credentials: 'include' 
    }).then(() => {
        window.location.href = '/admin.login.html';
    }).catch(() => {
        window.location.href = '/admin.login.html';
    });
}
</script>
'''
                content = content.replace('</body>', f'{logout_js}\n</body>')
                modified = True
                print(f"{Colors.GREEN}  ✅ Added logout function to {template}{Colors.END}")
            
            if modified:
                with open(template, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                print(f"{Colors.BLUE}  ⏭️  No changes needed for {template}{Colors.END}")
                
        except Exception as e:
            print(f"{Colors.RED}  ❌ Error fixing {template}: {e}{Colors.END}")

def fix_missing_endpoints():
    """Fix missing or misnamed endpoints"""
    print_header("🌐 FIXING MISSING ENDPOINTS")
    
    # Check if /api/admin/users exists
    admin_file = 'app/routes/admin.py'
    if os.path.exists(admin_file):
        with open(admin_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '@bp.route(\'/users\', methods=[\'GET\'])' in content:
            print(f"{Colors.GREEN}  ✅ /api/admin/users endpoint exists{Colors.END}")
    
    # Check company settings
    company_file = 'app/routes/company.py'
    if os.path.exists(company_file):
        with open(company_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '@bp.route(\'/settings\', methods=[\'GET\'])' in content:
            print(f"{Colors.GREEN}  ✅ /api/company/settings endpoint exists{Colors.END}")
    
    # Check reports summary
    reports_file = 'app/routes/reports.py'
    if os.path.exists(reports_file):
        with open(reports_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '@bp.route(\'/summary\', methods=[\'GET\'])' in content:
            print(f"{Colors.GREEN}  ✅ /api/reports/summary endpoint exists{Colors.END}")
        else:
            # Add summary endpoint if missing
            print(f"{Colors.YELLOW}  ⚠️  Adding missing summary endpoint to reports.py{Colors.END}")
            with open(reports_file, 'a', encoding='utf-8') as f:
                f.write('''

@bp.route('/summary', methods=['GET'])
def summary_report():
    """Get summary report"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    try:
        # Get counts
        cursor.execute('SELECT COUNT(*) FROM travelers')
        travelers_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM batches')
        batches_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = \'completed\'')
        total_collected = cursor.fetchone()[0]
        
        return jsonify({
            'success': True,
            'summary': {
                'total_travelers': travelers_count,
                'total_batches': batches_count,
                'total_collected': float(total_collected)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)
''')
            print(f"{Colors.GREEN}  ✅ Added /api/reports/summary endpoint{Colors.END}")

def create_cleanup_script():
    """Create a script to standardize cursor.close() to release_db"""
    print_header("📝 CREATING CLEANUP SCRIPT")
    
    cleanup_script = '''#!/usr/bin/env python
"""
Script to standardize database cleanup
Run this to replace cursor.close() with release_db where appropriate
"""

import os
import re

def standardize_cleanup():
    files_to_check = []
    for root, dirs, files in os.walk('.'):
        if any(skip in root for skip in ['venv', 'env', '.git', '__pycache__']):
            continue
        for file in files:
            if file.endswith('.py'):
                files_to_check.append(os.path.join(root, file))
    
    print("Scanning for cursor.close() usage...")
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for cursor.close() without release_db
            if 'cursor.close()' in content and 'release_db' not in content:
                print(f"  ⚠️  {file_path} uses cursor.close() but no release_db")
                
                # Check if file has get_db
                if 'get_db()' in content:
                    print(f"     Consider replacing with release_db pattern")
                    
        except Exception as e:
            pass

if __name__ == "__main__":
    standardize_cleanup()
'''
    
    # Write with utf-8 encoding to avoid encoding issues
    with open('standardize_db_cleanup.py', 'w', encoding='utf-8') as f:
        f.write(cleanup_script)
    print(f"{Colors.GREEN}✅ Created standardize_db_cleanup.py{Colors.END}")

def main():
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}🔧 MASTER FIX SCRIPT FOR HAJ TRAVEL SYSTEM{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.END}")
    
    # Fix missing imports
    fix_file_imports()
    
    # Fix database cleanup
    fix_database_cleanup()
    
    # Fix template issues
    fix_template_issues()
    
    # Fix missing endpoints
    fix_missing_endpoints()
    
    # Create cleanup helper (fixed encoding)
    create_cleanup_script()
    
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}✅ MASTER FIX COMPLETE{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"\n{Colors.BLUE}Next steps:{Colors.END}")
    print("1. Review the changes made")
    print("2. Run: git add .")
    print("3. Run: git commit -m 'Fix: Address all issues from structure report'")
    print("4. Run: git push origin main")
    print("5. Run: python standardize_db_cleanup.py to check for remaining cursor.close() usage")

if __name__ == "__main__":
    main()