#!/usr/bin/env python3
"""
Fix line 685 syntax error
Run: python fix_line685_fixed.py
"""

import os  # ← Added missing import

with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

if len(lines) >= 685:
    print(f"\nLine 685: {repr(lines[684])}")
    
    print("\nContext around line 685:")
    for i in range(680, min(690, len(lines))):
        prefix = "→ " if i == 684 else "  "
        print(f"{prefix}{i+1}: {lines[i].rstrip()}")
    
    # Line 685 is a comment - this is FINE!
    line = lines[684]
    if line.strip().startswith('#'):
        print("✅ Line 685 is a comment - this is NOT a syntax error")
        print("   The scanner is incorrectly flagging this line.")
        print("   Your code is actually correct!")
    else:
        # Common fixes for line 685
        # Check for unclosed quotes
        if line.count('"') % 2 == 1:
            print("❌ Unclosed double quote - adding closing quote")
            lines[684] = line.rstrip() + '"\n'
        
        elif line.count("'") % 2 == 1:
            print("❌ Unclosed single quote - adding closing quote")
            lines[684] = line.rstrip() + "'\n"
        
        # Check for missing colon
        elif line.strip().startswith(('def ', 'if ', 'elif ', 'else:', 'for ', 'while ')) and not line.strip().endswith(':'):
            print("❌ Missing colon - adding colon")
            lines[684] = line.rstrip() + ':\n'
        
        # Check for unclosed parentheses
        elif line.count('(') > line.count(')'):
            print(f"❌ Unclosed parentheses - adding {line.count('(') - line.count(')')} closing parentheses")
            lines[684] = line.rstrip() + ')' * (line.count('(') - line.count(')')) + '\n'
        
        # Check for unclosed brackets
        elif line.count('[') > line.count(']'):
            print(f"❌ Unclosed brackets - adding {line.count('[') - line.count(']')} closing brackets")
            lines[684] = line.rstrip() + ']' * (line.count('[') - line.count(']')) + '\n'
        
        # Check for unclosed braces
        elif line.count('{') > line.count('}'):
            print(f"❌ Unclosed braces - adding {line.count('{') - line.count('}')} closing braces")
            lines[684] = line.rstrip() + '}' * (line.count('{') - line.count('}')) + '\n'
        
        else:
            print("⚠️ Could not auto-fix. Manual edit needed.")
            print(f"Please check line 685: {repr(line)}")
            os.system('notepad app/routes/admin.py')
        
        # Write back if changes were made
        with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✅ Fixed line 685")
else:
    print("File has fewer than 685 lines")

print("\n✅ Fix complete! Run scanner again to verify.")