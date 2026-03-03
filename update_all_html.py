#!/usr/bin/env python
# update_all_html.py - Script to automatically fix all admin HTML files

import os
import shutil
from datetime import datetime

# Configuration
ADMIN_DIR = "public/admin"
BACKUP_DIR = "public/admin_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")

# Files that are already good (don't need changes)
FILES_OK = [
    "dashboard.html",
    "users.html",
    "frontpage.html",
    "backup.html"
]

# Files that need the full fix
FILES_TO_FIX = [
    "travelers.html",
    "batches.html",
    "payments.html",
    "invoices.html",
    "receipts.html",
    "reports.html",
    "company.html",
    "whatsapp.html",
    "email.html"
]

# The template to insert
TEMPLATE = '''
// ==================== SESSION MANAGEMENT & AUTHENTICATION ====================
// ADD THIS CODE RIGHT AFTER YOUR GLOBAL VARIABLES

// Session check function
async function checkAdminSession() {
    try {
        const response = await fetch('/api/check-session', {
            credentials: 'include',
            headers: { 'Cache-Control': 'no-cache' }
        });
        const data = await response.json();
        
        if (!data.authenticated) {
            console.log('⚠️ Session expired or not authenticated');
            sessionStorage.clear();
            window.location.href = '/admin.login.html';
            return false;
        }
        
        // Update role badge if exists
        const roleBadge = document.getElementById('roleBadge');
        if (roleBadge && data.user) {
            roleBadge.textContent = data.user.role.toUpperCase();
        }
        
        return true;
    } catch (error) {
        console.error('❌ Session check failed:', error);
        window.location.href = '/admin.login.html';
        return false;
    }
}

// Wrapper for authenticated API calls
async function authenticatedFetch(url, options = {}) {
    // First check if we're still authenticated
    const isAuthenticated = await checkAdminSession();
    if (!isAuthenticated) return null;
    
    // Make the actual API call with credentials
    const response = await fetch(url, {
        ...options,
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    });
    
    // Handle 401 specifically
    if (response.status === 401) {
        console.log('🔒 Session expired during API call');
        window.location.href = '/admin.login.html';
        return null;
    }
    
    return response;
}

// Show notification function (if not exists)
if (typeof showNotification !== 'function') {
    window.showNotification = function(message, type = 'success') {
        let notification = document.getElementById('notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'notification';
            notification.className = 'notification';
            document.body.appendChild(notification);
        }
        
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i> ${message}`;
        notification.style.display = 'block';
        
        setTimeout(() => {
            notification.style.display = 'none';
        }, 3000);
    };
}

// ==================== PAGE INITIALIZATION WITH SESSION CHECK ====================
// REPLACE YOUR EXISTING DOMContentLoaded WITH THIS
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Initializing page...');
    
    // Check session first - this will redirect if not authenticated
    const isValid = await checkAdminSession();
    if (!isValid) return;
    
    // Load page-specific data
    if (typeof loadPageData === 'function') {
        loadPageData();
    } else if (typeof loadTravelers === 'function') {
        loadTravelers();
    } else if (typeof loadBatches === 'function') {
        loadBatches();
    } else if (typeof loadPayments === 'function') {
        loadPayments();
    } else {
        console.log('ℹ️ No data loading function found');
    }
});

// ==================== LOGOUT FUNCTION ====================
// REPLACE YOUR EXISTING logout FUNCTION WITH THIS
async function logout() {
    try {
        if (typeof showNotification === 'function') {
            showNotification('Logging out...', 'info');
        }
        await fetch('/api/logout', { 
            method: 'POST', 
            credentials: 'include' 
        });
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        sessionStorage.clear();
        window.location.href = '/admin.login.html';
    }
}
'''

print("=" * 60)
print("🚀 ADMIN HTML FILES AUTO-UPDATER")
print("=" * 60)

# Create backup directory
print(f"\n📁 Creating backup directory: {BACKUP_DIR}/")
os.makedirs(BACKUP_DIR, exist_ok=True)

# Process each file
print("\n🔍 Processing files...")

for filename in FILES_TO_FIX:
    filepath = os.path.join(ADMIN_DIR, filename)
    backup_path = os.path.join(BACKUP_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"   ⚠️  {filename} - NOT FOUND")
        continue
    
    try:
        # Read the file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create backup
        shutil.copy2(filepath, backup_path)
        
        # Check if already fixed
        if 'checkAdminSession' in content:
            print(f"   ✅ {filename} - ALREADY FIXED (skipped)")
            continue
        
        # Find script section
        script_start = content.find('<script>')
        if script_start == -1:
            script_start = content.find('<script ')
        
        if script_start == -1:
            print(f"   ❌ {filename} - NO SCRIPT TAG FOUND")
            continue
        
        script_end = content.find('</script>', script_start)
        if script_end == -1:
            print(f"   ❌ {filename} - MALFORMED SCRIPT TAG")
            continue
        
        # Get the script content
        script_content = content[script_start:script_end + 9]  # include </script>
        
        # Find where to insert template (after global variables)
        # Look for common patterns
        insert_points = [
            '// ==================== GLOBAL VARIABLES',
            'let currentEditId',
            'let travelersData',
            'let batchesData',
            'let currentPage',
            '// Document storage'
        ]
        
        insert_pos = -1
        for marker in insert_points:
            pos = script_content.find(marker)
            if pos != -1:
                # Find the end of that line
                line_end = script_content.find('\n', pos)
                if line_end != -1:
                    insert_pos = line_end + 1
                    break
        
        if insert_pos == -1:
            # Default: insert after the opening <script> tag
            insert_pos = script_content.find('>') + 1
        
        # Insert the template
        new_script = script_content[:insert_pos] + TEMPLATE + script_content[insert_pos:]
        
        # Replace the script in the full content
        new_content = content[:script_start] + new_script + content[script_end + 9:]
        
        # Fix fetch calls - add credentials: 'include'
        import re
        def add_credentials(match):
            full_match = match.group(0)
            if 'credentials:' in full_match:
                return full_match
            # Add credentials before the closing brace
            return full_match.rstrip(')') + ", { credentials: 'include' })"
        
        # Pattern to find fetch('/api/...') without options
        new_content = re.sub(r'fetch\(\s*[\'"](/api/[^\'"]+)[\'"]\s*\)', 
                              r'fetch(\1, { credentials: \'include\' })', 
                              new_content)
        
        # Also fix fetch with options but missing credentials
        new_content = re.sub(r'fetch\(\s*[\'"](/api/[^\'"]+)[\'"]\s*,\s*\{([^}]*)\}\s*\)',
                              lambda m: f'fetch({m.group(1)}, {{{m.group(2)}, credentials: \'include\'}}' if 'credentials' not in m.group(2) else m.group(0),
                              new_content)
        
        # Write the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"   ✅ {filename} - FIXED (backup saved)")
        
    except Exception as e:
        print(f"   ❌ {filename} - ERROR: {str(e)}")

# Report on OK files
print("\n📊 Files already good (no changes needed):")
for filename in FILES_OK:
    filepath = os.path.join(ADMIN_DIR, filename)
    if os.path.exists(filepath):
        print(f"   ✅ {filename}")
    else:
        print(f"   ⚠️  {filename} - NOT FOUND")

print("\n" + "=" * 60)
print(f"✅ UPDATE COMPLETE!")
print(f"📁 Backups saved in: {BACKUP_DIR}/")
print("=" * 60)
print("\nNEXT STEPS:")
print("1. Test each fixed page in your browser")
print("2. If something goes wrong, restore from backup")
print("3. Commit and push to GitHub")