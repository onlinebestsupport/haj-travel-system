#!/usr/bin/env python3
"""
Cleanup script for haj-travel-system root directory
Run this to organize or delete unnecessary files
"""

import os
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent

# Files/directories to delete (garbage files)
GARBAGE_FILES = [
    '#',
    '(',
    '{',
    '0',
    'null)',
    '✅',
    'goToDashboard()',
    'curl',
    'psql',
    'python',
    'railway',
    'cookies.txt',
    'new-cookies.txt',
    'document.cookie',
]

# Backup directories to move/delete
BACKUP_DIRS = [d for d in ROOT_DIR.glob('backup_*') if d.is_dir()]
BACKUP_DIRS.extend([d for d in ROOT_DIR.glob('final_backup_*') if d.is_dir()])
BACKUP_DIRS.extend([d for d in ROOT_DIR.glob('backup_before_*') if d.is_dir()])

# Fix/test scripts to move to scripts/ directory
SCRIPT_PATTERNS = [
    'fix_*.py',
    'auto_fix_*.py',
    'ultimate_fix*.py',
    'final_*.py',
    'complete_fix.py',
    'test_*.py',
    'check_*.py',
    'railway_*.py',
    'verify_*.py',
    'consolidate_*.py',
    '*.bat',
]

def cleanup():
    print("🧹 Cleaning up root directory...")
    
    # Create scripts directory if it doesn't exist
    scripts_dir = ROOT_DIR / 'scripts'
    scripts_dir.mkdir(exist_ok=True)
    
    # Delete garbage files
    for filename in GARBAGE_FILES:
        filepath = ROOT_DIR / filename
        if filepath.exists():
            if filepath.is_file():
                filepath.unlink()
                print(f"  ✅ Deleted: {filename}")
            elif filepath.is_dir():
                shutil.rmtree(filepath)
                print(f"  ✅ Deleted directory: {filename}")
    
    # Move backup directories to a backup_archive/
    if BACKUP_DIRS:
        archive_dir = ROOT_DIR / 'backup_archive'
        archive_dir.mkdir(exist_ok=True)
        for dirpath in BACKUP_DIRS:
            dest = archive_dir / dirpath.name
            shutil.move(str(dirpath), str(dest))
            print(f"  ✅ Moved: {dirpath.name} → backup_archive/")
    
    # Move script files to scripts/
    for pattern in SCRIPT_PATTERNS:
        for filepath in ROOT_DIR.glob(pattern):
            if filepath.is_file():
                dest = scripts_dir / filepath.name
                shutil.move(str(filepath), str(dest))
                print(f"  ✅ Moved: {filepath.name} → scripts/")
    
    # Delete .bak files
    for bak in ROOT_DIR.glob('*.bak'):
        bak.unlink()
        print(f"  ✅ Deleted: {bak.name}")
    
    # Delete report files
    report_files = [
        'CLEANUP_REPORT.txt',
        'DUPLICATE_FUNCTIONS_REPORT.txt',
        'FUNCTION_CLEANUP_GUIDE.txt',
        'structure.txt',
        'result.txt',
    ]
    for report in report_files:
        filepath = ROOT_DIR / report
        if filepath.exists():
            filepath.unlink()
            print(f"  ✅ Deleted: {report}")
    
    print("\n✅ Cleanup complete!")
    print(f"📁 Scripts moved to: scripts/")
    print(f"📁 Backups moved to: backup_archive/")

if __name__ == '__main__':
    cleanup()
