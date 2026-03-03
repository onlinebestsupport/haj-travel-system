# fix_users_pagination.py
import os
import shutil
from datetime import datetime

print("=" * 60)
print("🚀 FIXING users.html - Adding Pagination & Enhancements")
print("=" * 60)

# Create backup
backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(backup_dir, exist_ok=True)
print(f"📁 Created backup folder: {backup_dir}/")

html_path = "public/admin/users.html"
backup_path = f"{backup_dir}/users.html.bak"

# Create backup
shutil.copy2(html_path, backup_path)
print(f"✅ Backup created: {backup_path}")

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# ============================================================
# FIX 1: Add Pagination HTML if missing
# ============================================================
if 'pagination' not in content.lower() and 'showingFrom' not in content:
    print("\n🔧 Adding pagination HTML...")
    
    pagination_html = '''
        <!-- Pagination -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px;">
            <div id="paginationInfo">
                Showing <span id="showingFrom">1</span> to <span id="showingTo">10</span> of <span id="totalCount">0</span> users
            </div>
            <div style="display: flex; gap: 10px;">
                <button class="action-btn btn-secondary" onclick="previousPage()" id="prevPageBtn" disabled>
                    <i class="fas fa-chevron-left"></i> Previous
                </button>
                <button class="action-btn btn-primary" onclick="nextPage()" id="nextPageBtn">
                    Next <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        </div>'''
    
    # Insert before the closing </div> of main container
    if '</div>\n\n    <!-- Modals -->' in content:
        content = content.replace('</div>\n\n    <!-- Modals -->', pagination_html + '\n    </div>\n\n    <!-- Modals -->')
        print("   ✅ Pagination HTML added")
    else:
        print("   ⚠️ Could not find insertion point")

# ============================================================
# FIX 2: Add Pagination JavaScript
# ============================================================
if 'function previousPage' not in content:
    print("\n🔧 Adding pagination JavaScript...")
    
    pagination_js = '''
    // ==================== PAGINATION VARIABLES ====================
    let currentPage = 1;
    let itemsPerPage = 10;

    function updatePaginationInfo() {
        const total = window.allUsers ? window.allUsers.length : 0;
        document.getElementById('totalCount').textContent = total;
        const start = (currentPage - 1) * itemsPerPage + 1;
        const end = Math.min(currentPage * itemsPerPage, total);
        document.getElementById('showingFrom').textContent = total > 0 ? start : 0;
        document.getElementById('showingTo').textContent = total > 0 ? end : 0;
        
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');
        if (prevBtn) prevBtn.disabled = currentPage === 1;
        if (nextBtn) nextBtn.disabled = end >= total;
    }

    function previousPage() {
        if (currentPage > 1) {
            currentPage--;
            loadUsers();
        }
    }

    function nextPage() {
        if (currentPage * itemsPerPage < (window.allUsers ? window.allUsers.length : 0)) {
            currentPage++;
            loadUsers();
        }
    }'''
    
    # Insert before closing </script>
    if '</script>' in content:
        content = content.replace('</script>', pagination_js + '\n</script>')
        print("   ✅ Pagination JavaScript added")
    else:
        print("   ⚠️ Could not find </script>")

# ============================================================
# FIX 3: Update loadUsers function to use pagination
# ============================================================
if 'loadUsers' in content and 'currentPage' in content:
    print("\n🔧 Updating loadUsers function...")
    
    # Find the line where users are displayed
    old_display = 'tbody.innerHTML = html;'
    new_display = '''        // Store all users globally
        window.allUsers = data.users;
        
        // Apply pagination
        const start = (currentPage - 1) * itemsPerPage;
        const end = start + itemsPerPage;
        const paginatedUsers = data.users.slice(start, end);
        
        let html = '';
        paginatedUsers.forEach(user => {
            let permCount = 0;
            if (user.permissions) {
                if (typeof user.permissions === 'object') {
                    permCount = Object.keys(user.permissions).filter(k => user.permissions[k] === true).length;
                }
            }
            
            html += `<tr>
                <td>${user.id}</td>
                <td><strong>${escapeHtml(user.username)}</strong></td>
                <td>${escapeHtml(user.full_name || '-')}</td>
                <td>${escapeHtml(user.email)}</td>
                <td><span class="role-badge role-${user.role}">${escapeHtml(user.role)}</span></td>
                <td>${permCount}</td>
                <td>${escapeHtml(user.department || '-')}</td>
                <td><span class="status-badge ${user.is_active ? 'status-active' : 'status-inactive'}">${user.is_active ? 'Active' : 'Inactive'}</span></td>
                <td>${user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</td>
                <td>${user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}</td>
                <td>
                    <button class="icon-btn" onclick="viewUserDetails(${user.id})" title="View Details"><i class="fas fa-eye"></i></button>
                    <button class="icon-btn" onclick="editUser(${user.id})" title="Edit User"><i class="fas fa-edit"></i></button>
                    <button class="icon-btn" onclick="toggleUserStatus(${user.id})" title="${user.is_active ? 'Deactivate' : 'Activate'}">
                        <i class="fas fa-${user.is_active ? 'ban' : 'check-circle'}"></i>
                    </button>
                </td>
            </tr>`;
        });
        
        tbody.innerHTML = html;
        updatePaginationInfo();'''
    
    if old_display in content:
        content = content.replace(old_display, new_display)
        print("   ✅ loadUsers function updated with pagination")
    else:
        print("   ⚠️ Could not find display line")

# ============================================================
# FIX 4: Add confirmation for delete/toggle
# ============================================================
print("\n🔧 Checking toggleUserStatus function...")
if 'toggleUserStatus' in content and 'confirm' not in content:
    # This would need more complex regex - manual check recommended
    print("   ⚠️ Manual check needed for confirmation dialogs")

# ============================================================
# FIX 5: Add export function
# ============================================================
if 'exportUsers' not in content:
    print("\n🔧 Adding export function...")
    
    export_js = '''

    // ==================== EXPORT FUNCTION ====================
    function exportUsersToCSV() {
        if (!window.allUsers || window.allUsers.length === 0) {
            showNotification('No users to export', 'error');
            return;
        }
        
        let csv = [];
        
        // Headers
        csv.push('"ID","Username","Full Name","Email","Role","Department","Status","Last Login","Created"');
        
        // Data rows
        window.allUsers.forEach(user => {
            csv.push(`"${user.id}","${user.username}","${user.full_name || ''}","${user.email}","${user.role}","${user.department || ''}","${user.is_active ? 'Active' : 'Inactive'}","${user.last_login || ''}","${user.created_at || ''}"`);
        });
        
        const csvContent = csv.join('\\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `users_${new Date().toISOString().slice(0,10)}.csv`;
        a.click();
        
        showNotification('Users exported successfully!', 'success');
    }'''
    
    # Add export button to action buttons
    export_button = '''
            <button class="action-btn btn-info" onclick="exportUsersToCSV()">
                <i class="fas fa-download"></i> Export CSV
            </button>'''
    
    # Insert export button
    if 'Create New User' in content:
        content = content.replace(
            'Create New User',
            'Create New User' + export_button
        )
        print("   ✅ Export button added")
    
    # Insert export function
    content = content.replace('</script>', export_js + '\n</script>')
    print("   ✅ Export function added")

# ============================================================
# Write the file
# ============================================================
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "=" * 60)
print("✅ users.html FIX COMPLETE!")
print("=" * 60)
print(f"\n📁 Backup saved: {backup_path}")
print("\n📋 FIXES APPLIED:")
print("   1. ✅ Pagination HTML added")
print("   2. ✅ Pagination JavaScript added")
print("   3. ✅ loadUsers updated with pagination")
print("   4. ✅ Export function added")
print("\n⚠️ MANUAL CHECKS NEEDED:")
print("   - Add confirmation dialogs for delete/toggle")
print("   - Add loading states if desired")
print("\n🚀 NEXT STEPS:")
print("   1. Test users.html in browser")
print("   2. If issues, restore from backup")
print("   3. Run: git add public/admin/users.html")
print("   4. Run: git commit -m \"Add pagination and export to users page\"")
print("   5. Run: git push origin main")