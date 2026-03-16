#!/usr/bin/env python3
"""
Remove duplicate get_backup_stats function
Run: python fix_duplicate_backup_stats.py
"""

import re
from app.database import get_db

with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the pattern with duplicate
pattern = r'(@bp\.route\(\'/backups/stats\'.*?def get_backup_stats\(.*?return jsonify\(.*?\), 200\).*?)(conn, cursor = get_db\(\)\n.*?return jsonify\(.*?\), 200)'
replacement = r'\1'

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Removed duplicate get_backup_stats function")