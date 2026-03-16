#!/usr/bin/env python
"""
Find indentation errors in server.py
"""

def find_indent_error():
    with open('app/server.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("🔍 Scanning app/server.py for indentation errors...\n")
    
    errors_found = False
    for i, line in enumerate(lines, 1):
        # Look for try: with no indented line after
        if line.strip().startswith('try:') and i < len(lines):
            next_line = lines[i].strip()  # lines[i] is the next line (0-indexed)
            if next_line and not next_line.startswith((' ', '\t')):
                errors_found = True
                print(f"❌ Possible indentation error at line {i}")
                print(f"   Line {i}: {line.rstrip()}")
                print(f"   Line {i+1}: {lines[i].rstrip()}")
                print()
        
        # Also check for any other indentation issues
        if 'try:' in line and not line.strip().startswith('try:'):
            # This might be a false positive
            pass
    
    if not errors_found:
        print("✅ No obvious indentation errors found!")
        print("\nLet's look at line 674 specifically:")
        if len(lines) >= 674:
            print(f"Line 674: {lines[673].rstrip()}")
            if len(lines) >= 675:
                print(f"Line 675: {lines[674].rstrip()}")
        else:
            print("File has less than 674 lines")

if __name__ == "__main__":
    find_indent_error()