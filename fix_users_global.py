import os
import re

filepath = "public/admin/users.html"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and fix the loadUsers function scope
pattern = r'\(\s*function\s*\([^)]*\)\s*\{\s*(var|let|const)?\s*loadUsers\s*=\s*async\s*function'
if re.search(pattern, content):
    # Replace with global function
    content = re.sub(pattern, 'async function loadUsers', content)
    print("✅ Fixed loadUsers scope")
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ users.html updated")
else:
    print("⚠️ Could not find pattern, manual fix needed")