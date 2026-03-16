#!/usr/bin/env python
"""
Fix cursor.close() usage to use release_db pattern
Run this to update files that use cursor.close() without release_db
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

def fix_file(file_path):
    """Fix a single file to use release_db instead of cursor.close()"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip backup directories
        if 'backup_' in file_path:
            return False
        
        modified = False
        
        # Add release_db import if missing
        if 'release_db' not in content and 'get_db' in content:
            if 'from app.database import' in content:
                # Add release_db to existing import
                content = re.sub(
                    r'(from app\.database import.*?)(\n)',
                    r'\1, release_db\2',
                    content,
                    flags=re.DOTALL
                )
                modified = True
                print(f"{Colors.GREEN}  ✅ Added release_db import to {file_path}{Colors.END}")
            elif 'import app.database' in content:
                # Add to existing import
                content = content.replace(
                    'import app.database',
                    'import app.database\nfrom app.database import release_db'
                )
                modified = True
                print(f"{Colors.GREEN}  ✅ Added release_db import to {file_path}{Colors.END}")
        
        # Look for patterns like:
        # cursor.execute(...)
        # cursor.close()
        # conn.close()
        # return ...
        
        # Replace with try/finally pattern
        patterns = [
            (r'(cursor\.execute\(.*?\).*?\n\s*cursor\.close\(\)\n\s*conn\.close\(\))',
             r'try:\n        \1\n    finally:\n        release_db(conn, cursor)'),
        ]
        
        for pattern, replacement in patterns:
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                modified = True
                print(f"{Colors.GREEN}  ✅ Fixed database cleanup pattern in {file_path}{Colors.END}")
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"{Colors.RED}  ❌ Error fixing {file_path}: {e}{Colors.END}")
        return False

def main():
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}🔧 FIX CURSOR.CLOSE() USAGE{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.END}\n")
    
    files_to_fix = [
        'add_test_data.py',
        'check_tables.py',
        'complete_fix.py',
        'fix_backup_stats.py',
        'test_railway_connection.py',
        'app/reset_database.py',
        'app/server.py',
        'app/routes/batches.py',
        'app/routes/company.py',
        'app/routes/invoices.py',
        'app/routes/payments.py',
        'app/routes/receipts.py',
        'app/routes/travelers.py',
        'app/routes/uploads.py'
    ]
    
    fixed_count = 0
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print(f"\n{Colors.BLUE}Processing: {file_path}{Colors.END}")
            if fix_file(file_path):
                fixed_count += 1
        else:
            print(f"{Colors.YELLOW}⚠️  File not found: {file_path}{Colors.END}")
    
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}✅ Fixed {fixed_count} files{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"\n{Colors.BLUE}Next steps:{Colors.END}")
    print("1. Review the changes made")
    print("2. Run: git add .")
    print("3. Run: git commit -m 'Fix: Replace cursor.close() with release_db pattern'")
    print("4. Run: git push origin main")

if __name__ == "__main__":
    main()