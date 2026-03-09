#!/usr/bin/env python3
"""
Check exactly what's at line 684
Run: python check_line684.py
"""

import os

filepath = "app/routes/admin.py"

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
print(f"Line 684 exists: {len(lines) >= 684}")

if len(lines) >= 684:
    print(f"\nLine 684 content: {repr(lines[683])}")
    
    print("\nContext around line 684:")
    start = max(0, 683-5)
    end = min(len(lines), 683+6)
    
    for i in range(start, end):
        prefix = "→ " if i == 683 else "  "
        line_num = i + 1
        print(f"{prefix}{line_num}: {lines[i].rstrip()}")
    
    # Check for common issues
    line = lines[683]
    
    # Check for unclosed quotes
    if line.count('"') % 2 == 1:
        print("\n❌ Unclosed double quote detected")
    if line.count("'") % 2 == 1:
        print("\n❌ Unclosed single quote detected")
    
    # Check for unclosed brackets
    if line.count('(') > line.count(')'):
        print(f"\n❌ Unclosed parentheses: {line.count('(')} open, {line.count(')')} closed")
    if line.count('[') > line.count(']'):
        print(f"\n❌ Unclosed brackets: {line.count('[')} open, {line.count(']')} closed")
    if line.count('{') > line.count('}'):
        print(f"\n❌ Unclosed braces: {line.count('{')} open, {line.count('}')} closed")
    
    # Check for invalid characters
    invalid_chars = ['@', '#', '$', '%', '^', '&', '*', '+', '=', '<', '>']
    found = [c for c in invalid_chars if c in line and not any(x in line for x in [f'"{c}"', f"'{c}'"])]
    if found:
        print(f"\n❌ Possibly invalid characters: {found}")