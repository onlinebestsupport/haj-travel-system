#!/usr/bin/env python3
"""
🔧 FIX GIT MERGE CONFLICTS
Removes all <<<<<<, ======, >>>>>> markers from Python files
"""

import os
import re
import sys

def fix_merge_conflicts():
    """Fix all merge conflict markers"""
    
    print("\n" + "="*80)
    print("🔧 FIXING GIT MERGE CONFLICTS".center(80))
    print("="*80 + "\n")
    
    # Python files to check
    files_to_check = [
        'app/server.py',
        'app/database.py',
        'app/routes/auth.py',
        'app/routes/admin.py',
        'app/routes/batches.py',
        '.env.example',
        'requirements.txt',
        'public/admin.login.html',
    ]
    
    fixed_files = []
    errors = []
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for merge conflict markers
            if '<<<<<<< HEAD' in content or '=======' in content or '>>>>>>>' in content:
                print(f"📝 Processing: {file_path}")
                
                # Remove conflict markers - keep the HEAD version
                lines = content.split('\n')
                new_lines = []
                in_conflict = False
                keep_head = True
                
                i = 0
                while i < len(lines):
                    line = lines[i]
                    
                    # Start of conflict
                    if line.startswith('<<<<<<< HEAD'):
                        in_conflict = True
                        keep_head = True
                        i += 1
                        continue
                    
                    # Middle marker
                    elif line.startswith('=======') and in_conflict:
                        keep_head = False
                        i += 1
                        continue
                    
                    # End of conflict
                    elif line.startswith('>>>>>>>') and in_conflict:
                        in_conflict = False
                        keep_head = True
                        i += 1
                        continue
                    
                    # During conflict - keep HEAD version
                    elif in_conflict and not keep_head:
                        # Skip non-HEAD lines
                        i += 1
                        continue
                    
                    # Normal line
                    else:
                        new_lines.append(line)
                    
                    i += 1
                
                # Write fixed content
                new_content = '\n'.join(new_lines)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"   ✅ Fixed: {file_path}\n")
                fixed_files.append(file_path)
        
        except Exception as e:
            error_msg = f"❌ Error in {file_path}: {str(e)}"
            print(error_msg + "\n")
            errors.append(error_msg)
    
    # Summary
    print("="*80)
    print(f"✅ Fixed {len(fixed_files)} files".center(80))
    print("="*80 + "\n")
    
    if fixed_files:
        print("Files fixed:")
        for f in fixed_files:
            print(f"  ✅ {f}")
    
    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  {e}")
    
    print("\n" + "="*80)
    print("NEXT: Run 'python app/server.py' to test".center(80))
    print("="*80 + "\n")
    
    return len(errors) == 0

if __name__ == "__main__":
    success = fix_merge_conflicts()
    sys.exit(0 if success else 1)