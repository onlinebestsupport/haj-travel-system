# fix_session_manager.py
import os
import re

print("="*70)
print("🔧 FIXING SESSION MANAGER")
print("="*70)

sm_path = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system\public\admin\js\session-manager.js"

if os.path.exists(sm_path):
    with open(sm_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    backup_path = sm_path + '.bak'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Backup created at: {backup_path}")
    
    # Fix 1: Set SESSION_TIMEOUT correctly
    content = re.sub(
        r'SESSION_TIMEOUT:\s*\d+\s*\*\s*\d+\s*\*\s*\d+\s*\*\s*\d+.*', 
        'SESSION_TIMEOUT: 30 * 60 * 1000,  // 30 minutes', 
        content
    )
    content = re.sub(
        r'SESSION_TIMEOUT:\s*\d+', 
        'SESSION_TIMEOUT: 30 * 60 * 1000', 
        content
    )
    
    # Fix 2: Ensure clearTimers is called at the beginning of startTimers
    if 'startTimers: function() {' in content:
        # Check if clearTimers is already there
        start_timer_section = content.split('startTimers: function() {')[1].split('\n')[0:5]
        start_timer_text = '\n'.join(start_timer_section)
        
        if 'this.clearTimers' not in start_timer_text:
            # Add clearTimers right after the opening brace
            content = content.replace(
                'startTimers: function() {',
                'startTimers: function() {\n        this.clearTimers();'
            )
            print("✅ Added this.clearTimers() to startTimers")
    
    # Fix 3: Remove duplicate startTimers if any
    start_count = content.count('startTimers:')
    if start_count > 1:
        # Find all occurrences
        parts = content.split('startTimers:')
        # Keep the first part + first startTimers + the rest (merged)
        content = parts[0] + 'startTimers:' + ''.join(parts[1:])
        print(f"✅ Removed {start_count-1} duplicate startTimers definitions")
    
    # Fix 4: Add proper logging to show timeout value
    if 'console.log' in content and 'Session timers started' in content:
        # Update the log line to show actual values
        content = re.sub(
            r'console\.log\(\'⏱️ Session timers started\'.*\)',
            'console.log(\'⏱️ Session timers started\', {\n            timeout: this.SESSION_TIMEOUT / 60000 + \' minutes\',\n            warning: this.WARNING_BEFORE / 60000 + \' minutes\'\n        });',
            content
        )
    
    with open(sm_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ Session manager fixed!")
    print("   - SESSION_TIMEOUT set to 30 minutes")
    print("   - clearTimers() added to startTimers")
    print("   - Duplicate definitions removed")
else:
    print("❌ Session manager file not found!")

print("\n" + "="*70)