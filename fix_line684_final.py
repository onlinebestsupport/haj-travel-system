#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final fix for line 684 syntax error
Run: python fix_line684_final.py
"""

import os

def fix_line684():
    filepath = "app/routes/admin.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Line 684: {repr(lines[683])}")
    print("\nContext:")
    for i in range(680, min(690, len(lines))):
        print(f"{i+1}: {lines[i].rstrip()}")
    
    # Remove any duplicate or malformed code around line 684
    # This is likely the duplicate backup stats code
    
    # Find the start of the backup section
    backup_start = None
    for i in range(650, 700):
        if i < len(lines) and "BACKUP API ENDPOINTS" in lines[i]:
            backup_start = i
            break
    
    if backup_start:
        print(f"Found BACKUP section at line {backup_start+1}")
        
        # Keep only the first occurrence of each function
        new_lines = []
        seen_functions = set()
        i = 0
        
        while i < len(lines):
            line = lines[i]
            if 'def ' in line and i > backup_start:
                func_name = line.split('def ')[1].split('(')[0].strip()
                if func_name in seen_functions:
                    print(f"Removing duplicate {func_name} at line {i+1}")
                    # Skip this function
                    i += 1
                    while i < len(lines) and (lines[i].startswith(' ') or lines[i].startswith('\t') or not lines[i].strip()):
                        i += 1
                    continue
                else:
                    seen_functions.add(func_name)
            
            new_lines.append(line)
            i += 1
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print("✅ Removed duplicate functions")
    else:
        print("Could not find BACKUP section")

if __name__ == "__main__":
    fix_line684()