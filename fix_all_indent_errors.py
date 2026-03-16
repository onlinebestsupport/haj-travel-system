#!/usr/bin/env python
"""
Fix all indentation errors in the project
"""

import os
import re

def fix_reset_database():
    """Fix indentation in app/reset_database.py"""
    file_path = 'app/reset_database.py'
    if not os.path.exists(file_path):
        print(f"❌ {file_path} not found")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix line 28-29 - missing indentation after try
    content = content.replace(
        'try:\n        # your code here',
        'try:\n            # your code here'
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Fixed {file_path}")

def fix_batches():
    """Fix indentation in app/routes/batches.py"""
    file_path = 'app/routes/batches.py'
    if not os.path.exists(file_path):
        print(f"❌ {file_path} not found")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Fix line 20-21
    if len(lines) >= 21:
        # Look for try statement without indented block
        for i in range(len(lines)):
            if 'try:' in lines[i] and i < len(lines)-1:
                next_line = lines[i+1].strip()
                if next_line and not next_line.startswith((' ', '\t')):
                    # Add indentation to next line
                    lines[i+1] = '    ' + lines[i+1].lstrip()
                    print(f"✅ Fixed batches.py at line {i+1}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"✅ Fixed {file_path}")

def fix_company():
    """Fix missing except/finally in app/routes/company.py"""
    file_path = 'app/routes/company.py'
    if not os.path.exists(file_path):
        print(f"❌ {file_path} not found")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for try without except/finally
    pattern = r'(try:\s*\n\s+.*?\n\s+settings = cursor\.fetchone\(\)\s*\n)'
    replacement = r'\1        conn.commit()\n    except Exception as e:\n        return jsonify({\'success\': False, \'error\': str(e)}), 500\n    finally:\n        release_db(conn, cursor)'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"✅ Fixed {file_path}")

def fix_invoices():
    """Fix missing except/finally in app/routes/invoices.py"""
    file_path = 'app/routes/invoices.py'
    if not os.path.exists(file_path):
        print(f"❌ {file_path} not found")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix line 33 - missing except/finally
    pattern = r'(try:\s*\n\s+.*?\n\s+invoices = cursor\.fetchall\(\)\s*\n)'
    replacement = r'\1        conn.commit()\n    except Exception as e:\n        return jsonify({\'success\': False, \'error\': str(e)}), 500\n    finally:\n        release_db(conn, cursor)'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"✅ Fixed {file_path}")

def fix_receipts():
    """Fix missing except/finally in app/routes/receipts.py"""
    file_path = 'app/routes/receipts.py'
    if not os.path.exists(file_path):
        print(f"❌ {file_path} not found")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix line 31 - missing except/finally
    pattern = r'(try:\s*\n\s+.*?\n\s+receipts = cursor\.fetchall\(\)\s*\n)'
    replacement = r'\1        conn.commit()\n    except Exception as e:\n        return jsonify({\'success\': False, \'error\': str(e)}), 500\n    finally:\n        release_db(conn, cursor)'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"✅ Fixed {file_path}")

def fix_travelers():
    """Fix indentation in app/routes/travelers.py"""
    file_path = 'app/routes/travelers.py'
    if not os.path.exists(file_path):
        print(f"❌ {file_path} not found")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Fix line 54-55
    if len(lines) >= 55:
        # Look for try statement without indented block
        for i in range(len(lines)):
            if 'try:' in lines[i] and i < len(lines)-1:
                next_line = lines[i+1].strip()
                if next_line and not next_line.startswith((' ', '\t')):
                    lines[i+1] = '    ' + lines[i+1].lstrip()
                    print(f"✅ Fixed travelers.py at line {i+1}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"✅ Fixed {file_path}")

def fix_uploads():
    """Fix indentation in app/routes/uploads.py"""
    file_path = 'app/routes/uploads.py'
    if not os.path.exists(file_path):
        print(f"❌ {file_path} not found")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Fix line 433-434
    if len(lines) >= 434:
        for i in range(len(lines)):
            if 'try:' in lines[i] and i < len(lines)-1:
                next_line = lines[i+1].strip()
                if next_line and not next_line.startswith((' ', '\t')):
                    lines[i+1] = '    ' + lines[i+1].lstrip()
                    print(f"✅ Fixed uploads.py at line {i+1}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"✅ Fixed {file_path}")

def main():
    print("=" * 60)
    print("🔧 FIXING ALL INDENTATION ERRORS")
    print("=" * 60)
    
    fix_reset_database()
    fix_batches()
    fix_company()
    fix_invoices()
    fix_receipts()
    fix_travelers()
    fix_uploads()
    
    print("\n" + "=" * 60)
    print("✅ ALL FIXES APPLIED!")
    print("=" * 60)
    print("\nRun these commands to deploy:")
    print("  git add app/")
    print('  git commit -m "Fix indentation errors in all route files"')
    print("  git push origin main")

if __name__ == "__main__":
    main()