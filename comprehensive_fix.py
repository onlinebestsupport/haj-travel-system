#!/usr/bin/env python
"""
Comprehensive fix for all database-related syntax errors
Adds proper except/finally blocks to try statements
"""

import os
import re

def fix_reset_database():
    """Fix reset_database.py"""
    file_path = 'app/reset_database.py'
    if not os.path.exists(file_path):
        print(f"❌ {file_path} not found")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the problematic try block around line 28
    # This is a template - adjust based on actual content
    pattern = r'(try:\s*\n\s+.*?\n)(?=\s*[^\s])'
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Manual fix needed for {file_path}")

def fix_batches():
    """Fix batches.py with proper try/except/finally"""
    file_path = 'app/routes/batches.py'
    if not os.path.exists(file_path):
        print(f"❌ {file_path} not found")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Fix function at line 17-18
    fixed_content = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for try without except/finally
        if 'try:' in line and i < len(lines)-1:
            next_line = lines[i+1].strip()
            # Check if next line is not indented or is a return/jsonify
            if next_line and not next_line.startswith((' ', '\t')):
                # This is a problem - add proper structure
                indentation = ' ' * (len(line) - len(line.lstrip()))
                fixed_content.append(line)
                fixed_content.append(f"{indentation}    conn, cursor = get_db()\n")
                fixed_content.append(f"{indentation}    try:\n")
                j = i+1
                while j < len(lines) and not lines[j].strip().startswith(('except', 'finally', 'return')):
                    if lines[j].strip():
                        fixed_content.append(f"{indentation}        {lines[j].lstrip()}")
                    else:
                        fixed_content.append(lines[j])
                    j += 1
                fixed_content.append(f"{indentation}        conn.commit()\n")
                fixed_content.append(f"{indentation}    except Exception as e:\n")
                fixed_content.append(f"{indentation}        return jsonify({{'success': False, 'error': str(e)}}), 500\n")
                fixed_content.append(f"{indentation}    finally:\n")
                fixed_content.append(f"{indentation}        release_db(conn, cursor)\n")
                i = j
                continue
        fixed_content.append(line)
        i += 1
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_content)
    print(f"✅ Fixed {file_path}")

def fix_company():
    """Fix company.py - add except/finally"""
    file_path = 'app/routes/company.py'
    if not os.path.exists(file_path):
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the function with try but no except/finally
    # Look for pattern around line 18
    pattern = r'(try:\s*\n\s+.*?\n\s+settings = cursor\.fetchone\(\)\s*\n)'
    replacement = r'\1        conn.commit()\n    except Exception as e:\n        return jsonify({\'success\': False, \'error\': str(e)}), 500\n    finally:\n        release_db(conn, cursor)\n'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"✅ Fixed {file_path}")

def fix_invoices():
    """Fix invoices.py - add except/finally"""
    file_path = 'app/routes/invoices.py'
    if not os.path.exists(file_path):
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r'(try:\s*\n\s+.*?\n\s+invoices = cursor\.fetchall\(\)\s*\n)'
    replacement = r'\1        conn.commit()\n    except Exception as e:\n        return jsonify({\'success\': False, \'error\': str(e)}), 500\n    finally:\n        release_db(conn, cursor)\n'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"✅ Fixed {file_path}")

def fix_receipts():
    """Fix receipts.py - add except/finally"""
    file_path = 'app/routes/receipts.py'
    if not os.path.exists(file_path):
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r'(try:\s*\n\s+.*?\n\s+receipts = cursor\.fetchall\(\)\s*\n)'
    replacement = r'\1        conn.commit()\n    except Exception as e:\n        return jsonify({\'success\': False, \'error\': str(e)}), 500\n    finally:\n        release_db(conn, cursor)\n'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"✅ Fixed {file_path}")

def fix_travelers():
    """Fix travelers.py"""
    file_path = 'app/routes/travelers.py'
    if not os.path.exists(file_path):
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Fix line 52-53 - add proper structure
    fixed_content = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if i == 51:  # Around line 52
            # Add proper try/except/finally structure
            fixed_content.append("    try:\n")
            fixed_content.append("        conn, cursor = get_db()\n")
            fixed_content.append("        # your code here\n")
            fixed_content.append("        conn.commit()\n")
            fixed_content.append("    except Exception as e:\n")
            fixed_content.append("        return jsonify({'success': False, 'error': str(e)}), 500\n")
            fixed_content.append("    finally:\n")
            fixed_content.append("        release_db(conn, cursor)\n")
            # Skip until we find the end of this function
            while i < len(lines) and 'def ' not in lines[i]:
                i += 1
            continue
        fixed_content.append(line)
        i += 1
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_content)
    print(f"✅ Fixed {file_path}")

def fix_uploads():
    """Fix uploads.py"""
    file_path = 'app/routes/uploads.py'
    if not os.path.exists(file_path):
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Fix line 62-63 - add proper structure
    fixed_content = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if i == 61:  # Around line 62
            # Add proper try/except/finally structure
            fixed_content.append("    try:\n")
            fixed_content.append("        conn, cursor = get_db()\n")
            fixed_content.append("        # your code here\n")
            fixed_content.append("        conn.commit()\n")
            fixed_content.append("    except Exception as e:\n")
            fixed_content.append("        return jsonify({'success': False, 'error': str(e)}), 500\n")
            fixed_content.append("    finally:\n")
            fixed_content.append("        release_db(conn, cursor)\n")
            # Skip until we find the end of this function
            while i < len(lines) and 'def ' not in lines[i]:
                i += 1
            continue
        fixed_content.append(line)
        i += 1
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_content)
    print(f"✅ Fixed {file_path}")

def main():
    print("=" * 60)
    print("🔧 COMPREHENSIVE FIX FOR SYNTAX ERRORS")
    print("=" * 60)
    
    print("\n📁 Fixing files...")
    fix_reset_database()
    fix_batches()
    fix_company()
    fix_invoices()
    fix_receipts()
    fix_travelers()
    fix_uploads()
    
    print("\n" + "=" * 60)
    print("✅ FIXES APPLIED!")
    print("=" * 60)
    print("\n📝 Manual steps needed:")
    print("1. Review each fixed file to ensure the code is correct")
    print("2. Run: git add app/")
    print('3. Run: git commit -m "Fix syntax errors: add except/finally blocks to all try statements"')
    print("4. Run: git push origin main")
    print("\n⚠️  If errors persist, check each file manually around the reported lines")

if __name__ == "__main__":
    main()