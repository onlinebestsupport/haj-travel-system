#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Fix Syntax Error in admin.py
Run: python auto_fix_admin_syntax.py
"""

import os
import re
import shutil
from datetime import datetime

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️ {text}{Colors.ENDC}")

def create_backup(filepath):
    """Create a backup of the file"""
    backup_path = f"{filepath}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print_info(f"Backup created: {backup_path}")
    return backup_path

def fix_admin_py_syntax():
    """Fix syntax error in admin.py"""
    print_header("🔧 AUTO-FIXING admin.py SYNTAX ERRORS")
    
    filepath = "app/routes/admin.py"
    
    if not os.path.exists(filepath):
        print_error(f"File not found: {filepath}")
        return False
    
    # Create backup
    backup = create_backup(filepath)
    
    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    print_info(f"Total lines in file: {len(lines)}")
    
    # Fix 1: Remove duplicate/incomplete route decorators at the end
    print_info("Looking for incomplete route decorators...")
    
    # Find and remove lines that are just decorators without function definitions
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if this is a decorator followed by nothing or another decorator
        if line.strip().startswith('@bp.route'):
            # Look ahead to see if there's a function definition
            found_function = False
            j = i + 1
            while j < len(lines) and j < i + 5:
                if lines[j].strip().startswith('def '):
                    found_function = True
                    break
                elif lines[j].strip().startswith('@'):
                    break
                j += 1
            
            if not found_function and j >= len(lines) - 5:
                # This is likely an incomplete decorator at the end
                print_warning(f"Removing incomplete decorator at line {i+1}: {line[:50]}")
                i += 1
                continue
        
        fixed_lines.append(line)
        i += 1
    
    # Write back
    fixed_content = '\n'.join(fixed_lines)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print_success("File has been fixed!")
    
    # Verify syntax
    try:
        compile(fixed_content, filepath, 'exec')
        print_success("✅ Syntax is now valid!")
        return True
    except SyntaxError as e:
        print_error(f"Syntax error still exists: {e}")
        return False

if __name__ == '__main__':
    fix_admin_py_syntax()
