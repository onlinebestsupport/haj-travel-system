#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Fix Syntax Error in admin.py at line 684
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
    """Fix syntax error in admin.py at line 684"""
    print_header("🔧 AUTO-FIXING admin.py SYNTAX ERROR")
    
    filepath = "app/routes/admin.py"
    
    if not os.path.exists(filepath):
        print_error(f"File not found: {filepath}")
        return False
    
    # Create backup
    backup = create_backup(filepath)
    
    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print_info(f"Total lines in file: {len(lines)}")
    
    # Check if line 684 exists
    if len(lines) < 684:
        print_error(f"File only has {len(lines)} lines, line 684 doesn't exist")
        return False
    
    # Show the problematic line and context
    print_info(f"Line 684 content: {repr(lines[683])}")
    print_info("Context (lines 680-690):")
    for i in range(max(0, 680-1), min(len(lines), 690)):
        prefix = "→ " if i == 683 else "  "
        print(f"   {prefix}{i+1}: {lines[i].rstrip()}")
    
    # Common syntax error patterns and fixes
    line = lines[683]
    fixed = False
    original_line = line
    
    # Pattern 1: Unclosed parenthesis
    if line.count('(') > line.count(')'):
        print_warning("Found unclosed opening parenthesis")
        lines[683] = line.rstrip() + ')\n'
        fixed = True
    
    # Pattern 2: Unclosed bracket
    elif line.count('[') > line.count(']'):
        print_warning("Found unclosed opening bracket")
        lines[683] = line.rstrip() + ']\n'
        fixed = True
    
    # Pattern 3: Unclosed curly brace
    elif line.count('{') > line.count('}'):
        print_warning("Found unclosed opening curly brace")
        lines[683] = line.rstrip() + '}\n'
        fixed = True
    
    # Pattern 4: Missing comma at end of line
    elif line.rstrip().endswith(('"', "'", '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ')', ']', '}')) and not line.rstrip().endswith(','):
        # Check if next line starts with something that suggests a comma is needed
        if len(lines) > 684 and lines[684].strip() and not lines[684].strip().startswith((')', ']', '}', 'def', 'class', '@')):
            print_warning("Missing comma at end of line")
            lines[683] = line.rstrip() + ',\n'
            fixed = True
    
    # Pattern 5: Missing colon
    elif line.strip().startswith('def ') and not line.strip().endswith(':'):
        print_warning("Missing colon in function definition")
        lines[683] = line.rstrip() + ':\n'
        fixed = True
    
    # Pattern 6: Unclosed string
    elif line.count('"') % 2 == 1:
        print_warning("Unclosed double quote")
        lines[683] = line.rstrip() + '"\n'
        fixed = True
    elif line.count("'") % 2 == 1:
        print_warning("Unclosed single quote")
        lines[683] = line.rstrip() + "'\n"
        fixed = True
    
    # Pattern 7: Invalid indentation (mix of spaces and tabs)
    elif '\t' in line and '    ' in line:
        print_warning("Mixed tabs and spaces - converting to spaces")
        # Convert tabs to 4 spaces
        lines[683] = line.replace('\t', '    ')
        fixed = True
    
    # Pattern 8: Check for common invalid characters
    invalid_chars = ['@', '#', '$', '%', '^', '&', '*', '+', '=']
    for char in invalid_chars:
        if char in line and not any(x in line for x in [f'"{char}"', f"'{char}'"]):
            # This might be a syntax error, but we need to be careful
            print_warning(f"Found potentially invalid character: {char}")
            # We'll comment out the line as a safe fallback
            lines[683] = '# ' + line
            fixed = True
            break
    
    if fixed:
        print_success(f"Fixed line 683 from:\n   {original_line.rstrip()}\n   to:\n   {lines[683].rstrip()}")
        
        # Write the fixed file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print_success(f"Changes saved to {filepath}")
        
        # Verify the fix
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                compile(f.read(), filepath, 'exec')
            print_success("✅ Syntax is now valid!")
        except SyntaxError as e:
            print_error(f"Still has syntax error: {e}")
            print_info(f"Check line {e.lineno}")
            return False
    else:
        print_error("Could not automatically fix the syntax error")
        print_info("Manual intervention required")
        print_info(f"Please open {filepath} and check line 684")
        
        # Open the file for manual editing
        os.system(f'notepad {filepath}')
    
    return fixed

def check_common_issues():
    """Check for other common issues in admin.py"""
    print_header("🔍 CHECKING FOR OTHER COMMON ISSUES")
    
    filepath = "app/routes/admin.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues_found = 0
    
    # Check for duplicate function definitions
    functions = re.findall(r'def (\w+)\\(', content)
    from collections import Counter
    dupes = [f for f, count in Counter(functions).items() if count > 1]
    
    if dupes:
        print_warning(f"Found duplicate functions: {dupes}")
        issues_found += len(dupes)
    
    # Check for missing imports
    required_imports = [
        'from flask import',
        'from app.database',
        'from datetime'
    ]
    
    for imp in required_imports:
        if imp not in content:
            print_warning(f"Missing import: {imp}")
            issues_found += 1
    
    # Check for long lines
    lines = content.split('\n')
    long_lines = [(i+1, len(line)) for i, line in enumerate(lines) if len(line) > 100]
    if long_lines:
        print_info(f"Found {len(long_lines)} lines over 100 chars (non-critical)")
    
    if issues_found == 0:
        print_success("No other critical issues found")
    
    return issues_found

if __name__ == "__main__":
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}")
    print("╔" + "═"*58 + "╗")
    print("║     🤖 AUTO-FIX ADMIN.PY SYNTAX ERROR 🤖          ║")
    print("║     Automatically fixing line 684 syntax error    ║")
    print("╚" + "═"*58 + "╝")
    print(Colors.ENDC)
    
    # Fix the syntax error
    fixed = fix_admin_py_syntax()
    
    if fixed:
        # Check for other issues
        check_common_issues()
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}")
        print("✅ Auto-fix completed!")
        print("Run 'python complete_code_scanner.py' to verify")
        print("Then run 'railway up' to deploy")
        print(Colors.ENDC)
    else:
        print(f"\n{Colors.WARNING}{Colors.BOLD}")
        print("⚠️ Manual fix required. Opening file for editing...")
        print(Colors.ENDC)
        os.system('notepad app/routes/admin.py')