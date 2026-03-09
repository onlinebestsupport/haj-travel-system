#!/usr/bin/env python3
"""
Fix line 682 where comment and route are merged
Run: python fix_line682.py
"""

with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check line 682 (index 681)
if len(lines) >= 682:
    line_682 = lines[681]
    print(f"Original line 682: {repr(line_682)}")
    
    # Split if it contains both comment and route
    if '# ==================== BACKUP API ENDPOINTS =============' in line_682 and '@bp.route' in line_682:
        # Split into two lines
        lines[681] = '# ==================== BACKUP API ENDPOINTS =============\n'
        lines.insert(682, '@bp.route(\'/backup/settings\', methods=[\'GET\'])\n')
        
        # Write back
        with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✅ Fixed line 682 - split into comment and route")
        print(f"   Now line 682: {repr(lines[681])}")
        print(f"   New line 682: {repr(lines[682])}")
    else:
        print("Line 682 doesn't have the merged pattern")
else:
    print("File has fewer than 682 lines")

print("\n✅ Fix complete! Run the scanner again to verify.")