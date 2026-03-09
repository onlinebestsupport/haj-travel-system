import os
import re

html_path = "public/admin/users.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add global variables at the top of script
if 'let currentPage' not in content:
    global_vars = '''
    // ====== GLOBAL VARIABLES ======
    let currentPage = 1;
    let itemsPerPage = 10;
    let allUsers = [];
    let selectedUsers = new Set();
    let userRole = '';'''
    
    content = content.replace('<script>', '<script>\n' + global_vars)
    print("✅ Added global variables")

# Add export function if missing
if 'function exportUsersToCSV' not in content:
    export_func = '''

    // ====== EXPORT FUNCTION ======
    function exportUsersToCSV() {
        if (!allUsers || allUsers.length === 0) {
            showNotification('No users to export', 'error');
            return;
        }
        
        let csv = [];
        csv.push('"ID","Username","Full Name","Email","Role","Department","Status","Last Login","Created"');
        
        allUsers.forEach(user => {
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
    
    content = content.replace('</script>', export_func + '\n</script>')
    print("✅ Added export function")

# Add pagination functions if missing
if 'function updatePaginationInfo' not in content:
    pagination_funcs = '''

    // ====== PAGINATION FUNCTIONS ======
    function updatePaginationInfo() {
        const total = allUsers.length;
        document.getElementById('totalCount').textContent = total;
        const start = (currentPage - 1) * itemsPerPage + 1;
        const end = Math.min(currentPage * itemsPerPage, total);
        document.getElementById('showingFrom').textContent = total > 0 ? start : 0;
        document.getElementById('showingTo').textContent = total > 0 ? end : 0;
        
        document.getElementById('prevPageBtn').disabled = currentPage === 1;
        document.getElementById('nextPageBtn').disabled = end >= total;
    }

    function previousPage() {
        if (currentPage > 1) {
            currentPage--;
            loadUsers();
        }
    }

    function nextPage() {
        if (currentPage * itemsPerPage < allUsers.length) {
            currentPage++;
            loadUsers();
        }
    }'''
    
    content = content.replace('</script>', pagination_funcs + '\n</script>')
    print("✅ Added pagination functions")

# Add bulk action functions if missing
if 'function toggleSelectAll' not in content:
    bulk_funcs = '''

    // ====== BULK ACTIONS ======
    function toggleSelectAll() {
        const checkboxes = document.querySelectorAll('.user-checkbox');
        const selectAll = document.getElementById('selectAllUsers');
        
        checkboxes.forEach(cb => {
            cb.checked = selectAll.checked;
            const userId = cb.value;
            if (selectAll.checked) {
                selectedUsers.add(userId);
            } else {
                selectedUsers.delete(userId);
            }
        });
        
        updateBulkButtons();
    }

    function toggleUserSelection(checkbox, userId) {
        if (checkbox.checked) {
            selectedUsers.add(userId);
        } else {
            selectedUsers.delete(userId);
            document.getElementById('selectAllUsers').checked = false;
        }
        updateBulkButtons();
    }

    function updateBulkButtons() {
        const hasSelection = selectedUsers.size > 0;
        const bulkEmailBtn = document.getElementById('bulkEmailBtn');
        const bulkActivateBtn = document.getElementById('bulkActivateBtn');
        const bulkDeactivateBtn = document.getElementById('bulkDeactivateBtn');
        
        if (bulkEmailBtn) bulkEmailBtn.disabled = !hasSelection;
        if (bulkActivateBtn) bulkActivateBtn.disabled = !hasSelection;
        if (bulkDeactivateBtn) bulkDeactivateBtn.disabled = !hasSelection;
    }

    function bulkEmail() {
        if (selectedUsers.size === 0) return;
        
        const selectedList = Array.from(selectedUsers).map(id => {
            const user = allUsers.find(u => u.id == id);
            return user?.email;
        }).filter(Boolean);
        
        if (selectedList.length === 0) {
            showNotification('No email addresses found', 'error');
            return;
        }
        
        window.location.href = `mailto:${selectedList.join(',')}`;
        showNotification(`Email client opened for ${selectedList.length} recipients`, 'success');
    }'''
    
    content = content.replace('</script>', bulk_funcs + '\n</script>')
    print("✅ Added bulk action functions")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ users.html fixed! Refresh the page.")
