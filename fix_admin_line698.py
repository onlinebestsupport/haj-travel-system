#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix syntax error at line 698 in admin.py
Run: python fix_admin_line698.py
"""

import os
import re

def fix_line698():
    filepath = "app/routes/admin.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Total lines: {len(lines)}")
    
    if len(lines) >= 698:
        print(f"Line 698 content: {repr(lines[697])}")
        print("\nContext around line 698:")
        for i in range(693, min(703, len(lines))):
            prefix = "→ " if i == 697 else "  "
            print(f"{prefix}{i+1}: {lines[i].rstrip()}")
        
        # Common fixes
        line = lines[697]
        
        # Check for unclosed parenthesis
        if line.count('(') > line.count(')'):
            lines[697] = line.rstrip() + ')\n'
            print("✅ Added missing closing parenthesis")
        
        # Check for unclosed bracket
        elif line.count('[') > line.count(']'):
            lines[697] = line.rstrip() + ']\n'
            print("✅ Added missing closing bracket")
        
        # Check for unclosed curly brace
        elif line.count('{') > line.count('}'):
            lines[697] = line.rstrip() + '}\n'
            print("✅ Added missing closing curly brace")
        
        # Check for missing colon
        elif line.strip().startswith(('def ', 'if ', 'elif ', 'else', 'for ', 'while ')) and not line.strip().endswith(':'):
            lines[697] = line.rstrip() + ':\n'
            print("✅ Added missing colon")
        
        # Check for unclosed string
        elif line.count('"') % 2 == 1:
            lines[697] = line.rstrip() + '"\n'
            print("✅ Added missing double quote")
        elif line.count("'") % 2 == 1:
            lines[697] = line.rstrip() + "'\n"
            print("✅ Added missing single quote")
        
        else:
            print("⚠️ Could not auto-fix. Manual edit needed.")
            os.system(f'notepad {filepath}')
            return
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✅ File updated. Run scanner again.")
    else:
        print(f"File only has {len(lines)} lines")

if __name__ == "__main__":
    fix_line698()