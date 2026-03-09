#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final duplicate route fixer with UTF-8 encoding
Run: python fix_duplicates_final_fixed.py
"""

import re
from collections import defaultdict

def fix_admin_py():
    print("🔧 Fixing admin.py duplicate routes...")
    
    # Open with UTF-8 encoding
    with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into lines for processing
    lines = content.split('\n')
    
    # Track function names and their line numbers
    functions = defaultdict(list)
    current_func = None
    func_start = 0
    
    for i, line in enumerate(lines):
        # Check for function definition
        func_match = re.search(r'def (\w+)\(', line)
        if func_match:
            current_func = func_match.group(1)
            func_start = i
            functions[current_func].append(func_start)
    
    # Find duplicates
    duplicates = {func: positions for func, positions in functions.items() if len(positions) > 1}
    
    if duplicates:
        print(f"Found duplicate functions: {list(duplicates.keys())}")
        
        # Create new content without duplicates
        new_lines = []
        seen_functions = set()
        i = 0
        
        while i < len(lines):
            line = lines[i]
            func_match = re.search(r'def (\w+)\(', line)
            
            if func_match:
                func_name = func_match.group(1)
                if func_name in seen_functions:
                    print(f"  Removing duplicate: {func_name}")
                    i += 1
                    # Skip the function body
                    while i < len(lines) and (lines[i].startswith(' ') or lines[i].startswith('\t') or not lines[i].strip()):
                        i += 1
                    continue
                else:
                    seen_functions.add(func_name)
            
            new_lines.append(line)
            i += 1
        
        # Write back with UTF-8 encoding
        with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        print("✅ Fixed duplicates in admin.py")
    else:
        print("✅ No duplicates found")

def add_missing_imports():
    """Ensure all required imports are present"""
    print("\n🔧 Checking imports...")
    
    with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_imports = [
        'from flask import Blueprint, request, jsonify, session',
        'from app.database import get_db',
        'from datetime import datetime',
        'import json'
    ]
    
    modified = False
    for imp in required_imports:
        if imp not in content:
            print(f"  Adding missing import: {imp}")
            content = imp + '\n' + content
            modified = True
    
    if modified:
        with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Added missing imports")
    else:
        print("✅ All imports present")

def check_specific_duplicates():
    """Specifically check for create_backup duplicate"""
    print("\n🔍 Checking specifically for create_backup...")
    
    with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count occurrences
    count = content.count('def create_backup(')
    
    if count > 1:
        print(f"❌ Found {count} duplicates of create_backup")
        
        # Split and keep only first occurrence
        parts = content.split('def create_backup(', 1)
        first_part = parts[0]
        rest = parts[1]
        
        # Find end of first function
        lines = rest.split('\n')
        func_lines = []
        i = 0
        while i < len(lines):
            func_lines.append(lines[i])
            if lines[i].strip().startswith('def ') and i > 0:
                break
            i += 1
        
        # Reconstruct with only one create_backup
        new_content = first_part + 'def create_backup(' + '\n'.join(func_lines)
        
        # Write back
        with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Fixed create_backup duplicate")
    else:
        print("✅ create_backup appears once")

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 FINAL DUPLICATE ROUTE FIXER (UTF-8)")
    print("=" * 60)
    
    fix_admin_py()
    add_missing_imports()
    check_specific_duplicates()
    
    print("\n" + "=" * 60)
    print("✅ Fix complete! Run 'railway up' to deploy")
    print("=" * 60)