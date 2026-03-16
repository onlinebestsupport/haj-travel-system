#!/usr/bin/env python
"""
Auto-fix script for all identified issues
Fixed version with proper UTF-8 encoding
"""

import os
import re

def fix_missing_imports():
    """Add missing database imports"""
    fixes = [
        {
            'file': 'add_missing_apis.py',
            'imports': ['from app.database import get_db, release_db']
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
        if os.path.exists(file_path):
            try:
                # Read with UTF-8 encoding
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.readlines()
                
                # Add imports after existing imports
                insert_pos = 0
                for i, line in enumerate(content):
                    if line.startswith('import ') or line.startswith('from '):
                        insert_pos = i + 1
                
                modified = False
                for imp in fix['imports']:
                    imp_exists = False
                    for line in content:
                        if imp in line:
                            imp_exists = True
                            break
                    
                    if not imp_exists:
                        content.insert(insert_pos, imp + '\n')
                        modified = True
                        print(f"  ✅ Added {imp} to {file_path}")
                
                if modified:
                    # Write back with UTF-8 encoding
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(content)
                else:
                    print(f"  ⏭️  No changes needed for {file_path}")
                    
            except UnicodeDecodeError:
                # Try with different encoding if UTF-8 fails
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.readlines()
                    
                    # Same logic as above
                    insert_pos = 0
                    for i, line in enumerate(content):
                        if line.startswith('import ') or line.startswith('from '):
                            insert_pos = i + 1
                    
                    modified = False
                    for imp in fix['imports']:
                        imp_exists = False
                        for line in content:
                            if imp in line:
                                imp_exists = True
                                break
                        
                        if not imp_exists:
                            content.insert(insert_pos, imp + '\n')
                            modified = True
                            print(f"  ✅ Added {imp} to {file_path} (latin-1 encoding)")
                    
                    if modified:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.writelines(content)
                            
                except Exception as e:
                    print(f"  ❌ Error processing {file_path}: {e}")
            except Exception as e:
                print(f"  ❌ Error processing {file_path}: {e}")
        else:
            print(f"  ❌ File not found: {file_path}")

def fix_database_cleanup():
    """Add finally blocks for database cleanup"""
    files_to_fix = [
        'app/routes/company.py',
        'app/routes/invoices.py',
        'app/routes/receipts.py',
        'app/routes/uploads.py'
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                modified = False
                
                # Add release_db import if missing
                if 'release_db' not in content and 'from app.database import' in content:
                    content = content.replace(
                        'from app.database import',
                        'from app.database import release_db,'
                    )
                    modified = True
                    print(f"  ✅ Added release_db import to {file_path}")
                
                # Look for functions with get_db() but no finally block
                if modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                    
                    if 'release_db' not in content and 'from app.database import' in content:
                        content = content.replace(
                            'from app.database import',
                            'from app.database import release_db,'
                        )
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"  ✅ Added release_db import to {file_path} (latin-1 encoding)")
                        
                except Exception as e:
                    print(f"  ❌ Error processing {file_path}: {e}")
            except Exception as e:
                print(f"  ❌ Error processing {file_path}: {e}")

def fix_template_issues():
    """Add session manager to HTML templates"""
    templates = [
        'public/index.html',
        'public/traveler_dashboard.html',
        'public/traveler_login.html',
        'debug_users.html',
        'login_page.html'
    ]
    
    session_script = '<script src="/admin/js/session-manager.js"></script>'
    
    for template in templates:
        if os.path.exists(template):
            try:
                with open(template, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                modified = False
                
                # Add session manager
                if session_script not in content and '</head>' in content:
                    content = content.replace('</head>', f'    {session_script}\n</head>')
                    modified = True
                    print(f"  ✅ Added session manager to {template}")
                
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
                    print(f"  ✅ Added logout function to {template}")
                
                if modified:
                    with open(template, 'w', encoding='utf-8') as f:
                        f.write(content)
                else:
                    print(f"  ⏭️  No changes needed for {template}")
                    
            except UnicodeDecodeError:
                try:
                    with open(template, 'r', encoding='latin-1') as f:
                        content = f.read()
                    
                    if session_script not in content and '</head>' in content:
                        content = content.replace('</head>', f'    {session_script}\n</head>')
                        with open(template, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"  ✅ Added session manager to {template} (latin-1 encoding)")
                        
                except Exception as e:
                    print(f"  ❌ Error processing {template}: {e}")
            except Exception as e:
                print(f"  ❌ Error processing {template}: {e}")

def main():
    print("=" * 60)
    print("🔧 AUTO-FIX SCRIPT FOR HAJ TRAVEL SYSTEM")
    print("=" * 60)
    
    print("\n📁 Fixing missing imports...")
    fix_missing_imports()
    
    print("\n📁 Fixing database cleanup...")
    fix_database_cleanup()
    
    print("\n📁 Fixing template issues...")
    fix_template_issues()
    
    print("\n" + "=" * 60)
    print("✅ All fixes applied!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review the changes")
    print("2. Run: git add .")
    print("3. Run: git commit -m 'Fix: Add missing imports, database cleanup, template issues'")
    print("4. Run: git push origin main")

if __name__ == "__main__":
    main()