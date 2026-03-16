#!/usr/bin/env python
"""
Script to standardize database cleanup
Run this to replace cursor.close() with release_db where appropriate
"""

import os
import re

def standardize_cleanup():
    files_to_check = []
    for root, dirs, files in os.walk('.'):
        if any(skip in root for skip in ['venv', 'env', '.git', '__pycache__']):
            continue
        for file in files:
            if file.endswith('.py'):
                files_to_check.append(os.path.join(root, file))
    
    print("Scanning for cursor.close() usage...")
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for cursor.close() without release_db
            if 'cursor.close()' in content and 'release_db' not in content:
                print(f"  ⚠️  {file_path} uses cursor.close() but no release_db")
                
                # Check if file has get_db
                if 'get_db()' in content:
                    print(f"     Consider replacing with release_db pattern")
                    
        except Exception as e:
            pass

if __name__ == "__main__":
    standardize_cleanup()
