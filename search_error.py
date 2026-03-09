#!/usr/bin/env python3
"""
Search for the syntax error in admin.py
Run: python search_error.py
"""

import re

with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("🔍 SEARCHING FOR SYNTAX ERROR PATTERNS\n")

# Look for duplicate function definitions
functions = {}
for i, line in enumerate(lines):
    if 'def ' in line and '(' in line:
        func_name = line.split('def ')[1].split('(')[0].strip()
        if func_name in functions:
            print(f"⚠️ DUPLICATE FUNCTION: {func_name}")
            print(f"   First at line {functions[func_name]+1}")
            print(f"   Second at line {i+1}")
            print(f"   Line {i+1}: {line.rstrip()}\n")
        else:
            functions[func_name] = i

# Look for the pattern we saw earlier (return with two status codes)
for i, line in enumerate(lines):
    if 'return jsonify' in line and '200' in line and '401' in line:
        print(f"❌ SUSPECT LINE {i+1}: {line.rstrip()}")
        print(f"   Context:")
        for j in range(max(0, i-3), min(len(lines), i+4)):
            prefix = "→ " if j == i else "  "
            print(f"   {prefix}{j+1}: {lines[j].rstrip()}")
        print()

# Look for the backup stats section
backup_stats_lines = []
for i, line in enumerate(lines):
    if 'def get_backup_stats' in line:
        backup_stats_lines.append(i+1)

if len(backup_stats_lines) > 1:
    print(f"⚠️ get_backup_stats appears {len(backup_stats_lines)} times at lines: {backup_stats_lines}")

# Look for malformed code around return statements
for i, line in enumerate(lines):
    if 'return' in line and not line.strip().endswith(')') and not line.strip().endswith('}'):
        next_line = lines[i+1] if i+1 < len(lines) else ""
        if next_line.strip() and not next_line.strip().startswith(('@', 'def', 'class', '#')):
            print(f"❌ POSSIBLE MALFORMED RETURN at line {i+1}")
            print(f"   {line.rstrip()}")
            print(f"   Next: {next_line.rstrip()}\n")

print(f"✅ Search complete. Total lines: {len(lines)}")