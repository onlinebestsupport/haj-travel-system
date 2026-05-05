/**
 * users.js - User Management for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 * API base: /api/admin/users
 */

'use strict';

// ── State ────────────────────────────────────────────────────
let allUsers = [];
let filteredUsers = [];
let currentPage = 1;
const ITEMS_PER_PAGE = 20;

// Permission templates per role
const ROLE_TEMPLATES = {
    super_admin: [
        'dashboard', 'batches', 'travelers', 'payments', 'invoices', 'receipts', 'reports',
        'create', 'read', 'update', 'delete', 'export', 'print',
        'manage_users', 'edit_users', 'delete_users', 'change_passwords', 'assign_roles',
        'backup', 'settings', 'frontpage', 'whatsapp', 'email',
        'view_financial', 'process_payments', 'refund', 'reports_financial'
    ],
    admin: [
        'dashboard', 'batches', 'travelers', 'payments', 'invoices', 'receipts', 'reports',
        'create', 'read', 'update', 'delete', 'export', 'print',
        'view_financial', 'process_payments', 'reports_financial'
    ],
    manager: [
        'dashboard', 'batches', 'travelers', 'payments', 'invoices', 'receipts',
        'create', 'read', 'update', 'export', 'print',
        'view_financial', 'process_payments'
    ],
    staff: ['dashboard', 'travelers', 'payments', 'receipts', 'create', 'read', 'update', 'print'],
    viewer: ['dashboard', 'travelers', 'payments', 'reports', 'read', 'export', 'print']
};

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    SessionManager.initPage(async () => {
        await loadUsers();
        initPermissions();
        initSearchListeners();
    });
});

function initSearchListeners() {
    const searchEl = document.getElementById('searchUsers');
    const roleEl   = document.getElementById('roleFilter');
    const statusEl = document.getElementById('statusFilter');
    if (searchEl) searchEl.addEventListener('input', debounce(filterUsers, 250));
    if (roleEl)   roleEl.addEventListener('change', filterUsers);
    if (statusEl) statusEl.addEventListener('change', filterUsers);
}

// ── Load & Display ───────────────────────────────────────────

/**
 * Fetch all users from the API and render the table
 */
async function loadUsers() {
    const tbody = document.getElementById('usersTableBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="11" class="loading"><i class="fas fa-spinner fa-spin"></i> Loading users…</td></tr>';

    try {
        const data = await makeAPICall('GET', '/api/admin/users');
        if (data.success && data.users) {
            allUsers = data.users;
            filteredUsers = [...allUsers];
            currentPage = 1;
            displayUsers();
            updateUserStats();
        } else {
            throw new Error(data.error || 'Failed to load users');
        }
    } catch (error) {
        handleError(error, 'loadUsers');
        if (tbody) {
            tbody.innerHTML = `
                <tr><td colspan="11" style="text-align:center; padding:40px;">
                    <div style="background:#fee; padding:20px; border-radius:8px; display:inline-block;">
                        <i class="fas fa-exclamation-triangle" style="color:#e74c3c; font-size:2rem;"></i>
                        <h3 style="color:#e74c3c; margin:10px 0;">Failed to Load Users</h3>
                        <p style="color:#7f8c8d; margin-bottom:15px;">${escapeHtml(error.message)}</p>
                        <button class="action-btn btn-primary" onclick="loadUsers()">
                            <i class="fas fa-redo"></i> Retry
                        </button>
                    </div>
                </td></tr>`;
        }
    }
}

/**
 * Render the current page of users into the table
 */
function displayUsers() {
    const tbody = document.getElementById('usersTableBody');
    if (!tbody) return;

    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const page  = filteredUsers.slice(start, start + ITEMS_PER_PAGE);

    if (page.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" style="text-align:center; padding:30px; color:#7f8c8d;">No users found</td></tr>';
        updatePaginationInfo();
        return;
    }

    tbody.innerHTML = page.map((user) => {
        let permCount = 0;
        if (user.permissions && typeof user.permissions === 'object') {
            permCount = Object.values(user.permissions).filter(Boolean).length;
        }
        return `<tr>
            <td>${user.id}</td>
            <td><strong>${escapeHtml(user.username)}</strong></td>
            <td>${escapeHtml(user.full_name || user.name || '-')}</td>
            <td>${escapeHtml(user.email)}</td>
            <td><span class="role-badge role-${escapeHtml(user.role)}">${escapeHtml(user.role)}</span></td>
            <td>${permCount}</td>
            <td>${escapeHtml(user.department || '-')}</td>
            <td><span class="status-badge ${user.is_active ? 'status-active' : 'status-inactive'}">${user.is_active ? 'Active' : 'Inactive'}</span></td>
            <td>${user.last_login ? formatDate(user.last_login, true) : 'Never'}</td>
            <td>${user.created_at ? formatDate(user.created_at) : '-'}</td>
            <td>
                <button class="icon-btn" onclick="viewUserDetails(${user.id})" title="View Details"><i class="fas fa-eye"></i></button>
                <button class="icon-btn" onclick="editUser(${user.id})" title="Edit User"><i class="fas fa-edit"></i></button>
                <button class="icon-btn" onclick="toggleUserStatus(${user.id})" title="${user.is_active ? 'Deactivate' : 'Activate'}">
                    <i class="fas fa-${user.is_active ? 'ban' : 'check-circle'}"></i>
                </button>
                <button class="icon-btn" style="color:#e74c3c;" onclick="deleteUser(${user.id})" title="Delete User"><i class="fas fa-trash"></i></button>
            </td>
        </tr>`;
    }).join('');

    updatePaginationInfo();
}

// ── Filter ───────────────────────────────────────────────────

/**
 * Filter users by search text, role, and status
 */
function filterUsers() {
    const search = (document.getElementById('searchUsers')?.value || '').toLowerCase();
    const role   = document.getElementById('roleFilter')?.value || 'all';
    const status = document.getElementById('statusFilter')?.value || 'all';

    filteredUsers = allUsers.filter((u) => {
        const matchSearch = !search ||
            (u.username || '').toLowerCase().includes(search) ||
            (u.full_name || u.name || '').toLowerCase().includes(search) ||
            (u.email || '').toLowerCase().includes(search);
        const matchRole   = role === 'all' || u.role === role;
        const matchStatus = status === 'all' ||
            (status === 'active' && u.is_active) ||
            (status === 'inactive' && !u.is_active);
        return matchSearch && matchRole && matchStatus;
    });

    currentPage = 1;
    displayUsers();
}

// ── Form Visibility ──────────────────────────────────────────

/**
 * Show the Add User form
 */
function showAddUserForm() {
    const form = document.getElementById('addUserForm');
    if (!form) return;
    form.style.display = 'block';
    form.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Hide the Add User form
 */
function hideAddUserForm() {
    const form = document.getElementById('addUserForm');
    if (form) form.style.display = 'none';
    document.getElementById('userCreateForm')?.reset();
    updatePermissionsCount();
}

// ── CRUD ─────────────────────────────────────────────────────

/**
 * Create a new user (called from form submit)
 */
async function createUser(event) {
    if (event) event.preventDefault();

    const permissions = {};
    document.querySelectorAll('#addUserForm .perm-checkbox').forEach((cb) => {
        permissions[cb.value] = cb.checked;
    });

    const userData = {
        username:   (document.getElementById('username')?.value || '').trim(),
        password:   document.getElementById('password')?.value || '',
        name:       (document.getElementById('fullname')?.value || '').trim() || null,
        email:      (document.getElementById('email')?.value || '').trim(),
        phone:      (document.getElementById('phone')?.value || '').trim() || null,
        department: (document.getElementById('department')?.value || '').trim() || null,
        role:       document.getElementById('role')?.value || 'viewer',
        permissions,
        is_active: true
    };

    if (!userData.username || !userData.password || !userData.email || !userData.role) {
        showNotification('Username, password, email and role are required', 'error');
        return;
    }
    if (userData.password.length < 6) {
        showNotification('Password must be at least 6 characters', 'error');
        return;
    }

    const btn = document.querySelector('#userCreateForm button[type="submit"]');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating…'; btn.disabled = true; }

    try {
        const data = await makeAPICall('POST', '/api/admin/users', userData);
        if (data.success) {
            showNotification('User created successfully!', 'success');
            hideAddUserForm();
            await loadUsers();
        } else {
            throw new Error(data.error || 'Could not create user');
        }
    } catch (error) {
        handleError(error, 'createUser');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Load a user's data into the edit modal
 * @param {number} userId
 */
async function editUser(userId) {
    const modal   = document.getElementById('editUserModal');
    const overlay = document.getElementById('modalOverlay');
    if (modal)   modal.style.display   = 'block';
    if (overlay) overlay.style.display = 'block';

    try {
        const data = await makeAPICall('GET', `/api/admin/users/${userId}`);
        if (data.success && data.user) {
            const u = data.user;
            const set = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ''; };
            set('edit_user_id',   u.id);
            set('edit_username',  u.username);
            set('edit_email',     u.email);
            set('edit_fullname',  u.full_name || u.name);
            set('edit_phone',     u.phone);
            set('edit_department', u.department);
            set('edit_role',      u.role);
        } else {
            throw new Error(data.error || 'User not found');
        }
    } catch (error) {
        handleError(error, 'editUser');
        closeEditModal();
    }
}

/**
 * Submit the edit user form
 */
async function updateUser(event) {
    if (event) event.preventDefault();

    const userId = document.getElementById('edit_user_id')?.value;
    if (!userId) return;

    const userData = {
        email:      (document.getElementById('edit_email')?.value || '').trim(),
        full_name:  (document.getElementById('edit_fullname')?.value || '').trim() || null,
        phone:      (document.getElementById('edit_phone')?.value || '').trim() || null,
        department: (document.getElementById('edit_department')?.value || '').trim() || null,
        role:       document.getElementById('edit_role')?.value
    };

    if (!userData.email || !userData.role) {
        showNotification('Email and role are required', 'error');
        return;
    }

    const btn = document.querySelector('#editUserForm button[type="submit"]');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating…'; btn.disabled = true; }

    try {
        const data = await makeAPICall('PUT', `/api/admin/users/${userId}`, userData);
        if (data.success) {
            showNotification('User updated successfully!', 'success');
            closeEditModal();
            await loadUsers();
        } else {
            throw new Error(data.error || 'Could not update user');
        }
    } catch (error) {
        handleError(error, 'updateUser');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Delete a user by ID
 * @param {number} userId
 */
async function deleteUser(userId) {
    const user = allUsers.find((u) => u.id === userId);
    if (!user) return;
    if (!confirmAction(`Delete user "${user.username}"? This cannot be undone.`)) return;

    try {
        const data = await makeAPICall('DELETE', `/api/admin/users/${userId}`);
        if (data.success) {
            showNotification('User deleted successfully!', 'success');
            await loadUsers();
        } else {
            throw new Error(data.error || 'Could not delete user');
        }
    } catch (error) {
        handleError(error, 'deleteUser');
    }
}

/**
 * Toggle a user's active/inactive status
 * @param {number} userId
 */
async function toggleUserStatus(userId) {
    const user = allUsers.find((u) => u.id === userId);
    if (!user) return;
    const action = user.is_active ? 'deactivate' : 'activate';
    if (!confirmAction(`Are you sure you want to ${action} user "${user.username}"?`)) return;

    try {
        const data = await makeAPICall('POST', `/api/admin/users/${userId}/toggle`, {});
        if (data.success) {
            showNotification(`User ${action}d successfully!`, 'success');
            await loadUsers();
        } else {
            throw new Error(data.error || `Could not ${action} user`);
        }
    } catch (error) {
        handleError(error, 'toggleUserStatus');
    }
}

// ── View Details ─────────────────────────────────────────────

/**
 * Show user details in a modal
 * @param {number} userId
 */
function viewUserDetails(userId) {
    const user = allUsers.find((u) => u.id === userId);
    if (!user) { showNotification('User not found', 'error'); return; }

    let permList = '';
    if (user.permissions && typeof user.permissions === 'object') {
        const active = Object.keys(user.permissions).filter((k) => user.permissions[k]);
        permList = active.map((p) => `<span class="permission-tag">${escapeHtml(p)}</span>`).join(' ');
    }

    const content = `
        <div style="display:grid; gap:10px;">
            <p><strong>Username:</strong> ${escapeHtml(user.username)}</p>
            <p><strong>Full Name:</strong> ${escapeHtml(user.full_name || user.name || '-')}</p>
            <p><strong>Email:</strong> ${escapeHtml(user.email)}</p>
            <p><strong>Role:</strong> <span class="role-badge role-${escapeHtml(user.role)}">${escapeHtml(user.role)}</span></p>
            <p><strong>Department:</strong> ${escapeHtml(user.department || '-')}</p>
            <p><strong>Status:</strong> <span class="status-badge ${user.is_active ? 'status-active' : 'status-inactive'}">${user.is_active ? 'Active' : 'Inactive'}</span></p>
            <p><strong>Last Login:</strong> ${user.last_login ? formatDate(user.last_login, true) : 'Never'}</p>
            <p><strong>Created:</strong> ${user.created_at ? formatDate(user.created_at, true) : '-'}</p>
            <div><strong>Permissions:</strong><div style="margin-top:8px; display:flex; flex-wrap:wrap; gap:5px;">${permList || '<em>None</em>'}</div></div>
        </div>`;

    // Try page-specific modal first, fall back to common modal
    const detailsContent = document.getElementById('userDetailsContent');
    const detailsModal   = document.getElementById('userDetailsModal');
    const overlay        = document.getElementById('modalOverlay');
    if (detailsContent && detailsModal) {
        detailsContent.innerHTML = content;
        detailsModal.style.display = 'block';
        if (overlay) overlay.style.display = 'block';
    } else {
        showModal(`User: ${user.username}`, content);
    }
}

// ── Export ───────────────────────────────────────────────────

/**
 * Export the current user list to CSV
 */
function exportUsersToCSV() {
    if (!filteredUsers.length) { showNotification('No users to export', 'warning'); return; }
    downloadCSV(
        filteredUsers,
        ['id', 'username', 'full_name', 'email', 'role', 'department', 'is_active', 'last_login', 'created_at'],
        ['ID', 'Username', 'Full Name', 'Email', 'Role', 'Department', 'Status', 'Last Login', 'Created'],
        `users_${new Date().toISOString().slice(0, 10)}.csv`
    );
}

// ── Role Templates ───────────────────────────────────────────

/**
 * Apply a role permission template to the add-user form checkboxes
 * @param {string} role
 */
function applyRoleTemplate(role) {
    const template = ROLE_TEMPLATES[role];
    if (!template) return;
    document.querySelectorAll('#addUserForm .perm-checkbox').forEach((cb) => {
        cb.checked = template.includes(cb.value);
    });
    const roleSelect = document.getElementById('role');
    if (roleSelect) roleSelect.value = role;
    updatePermissionsCount();
}

// ── Permissions Helpers ──────────────────────────────────────

function updatePermissionsCount() {
    const checked  = document.querySelectorAll('#addUserForm .perm-checkbox:checked');
    const countEl  = document.getElementById('selectedPermissionsCount');
    if (countEl) {
        countEl.textContent = `${checked.length} permissions selected`;
        countEl.style.color = checked.length > 0 ? '#27ae60' : '#7f8c8d';
    }
}

function initPermissions() {
    document.querySelectorAll('#addUserForm .perm-checkbox').forEach((cb) => {
        cb.addEventListener('change', updatePermissionsCount);
    });
    const selectAll = document.getElementById('selectAllPermissions');
    if (selectAll) {
        selectAll.addEventListener('change', function () {
            document.querySelectorAll('#addUserForm .perm-checkbox').forEach((cb) => { cb.checked = this.checked; });
            updatePermissionsCount();
        });
    }
    updatePermissionsCount();
}

// ── Modal Helpers ────────────────────────────────────────────

function closeEditModal() {
    const modal   = document.getElementById('editUserModal');
    const overlay = document.getElementById('modalOverlay');
    if (modal)   modal.style.display   = 'none';
    if (overlay) overlay.style.display = 'none';
}

function closeDetailsModal() {
    const modal   = document.getElementById('userDetailsModal');
    const overlay = document.getElementById('modalOverlay');
    if (modal)   modal.style.display   = 'none';
    if (overlay) overlay.style.display = 'none';
}

function closeAllModals() {
    ['editUserModal', 'userDetailsModal'].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
    const overlay = document.getElementById('modalOverlay');
    if (overlay) overlay.style.display = 'none';
    closeModal(); // common modal
}

// ── Pagination ───────────────────────────────────────────────

function updatePaginationInfo() {
    const total = filteredUsers.length;
    const start = total > 0 ? (currentPage - 1) * ITEMS_PER_PAGE + 1 : 0;
    const end   = Math.min(currentPage * ITEMS_PER_PAGE, total);

    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalCount',  total);
    setEl('showingFrom', start);
    setEl('showingTo',   end);

    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    if (prevBtn) prevBtn.disabled = currentPage === 1;
    if (nextBtn) nextBtn.disabled = end >= total;
}

function previousPage() {
    if (currentPage > 1) { currentPage--; displayUsers(); }
}

function nextPage() {
    if (currentPage * ITEMS_PER_PAGE < filteredUsers.length) { currentPage++; displayUsers(); }
}

// ── Stats ────────────────────────────────────────────────────

function updateUserStats() {
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalUsers',    allUsers.length);
    setEl('activeUsers',   allUsers.filter((u) => u.is_active).length);
    setEl('inactiveUsers', allUsers.filter((u) => !u.is_active).length);
    setEl('adminCount',    allUsers.filter((u) => u.role === 'super_admin' || u.role === 'admin').length);
}

// ── Form submit wiring ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('userCreateForm')?.addEventListener('submit', createUser);
    document.getElementById('editUserForm')?.addEventListener('submit', updateUser);
});

// Expose globals needed by inline HTML onclick handlers
window.loadUsers          = loadUsers;
window.filterUsers        = filterUsers;
window.showAddUserForm    = showAddUserForm;
window.hideAddUserForm    = hideAddUserForm;
window.editUser           = editUser;
window.deleteUser         = deleteUser;
window.toggleUserStatus   = toggleUserStatus;
window.viewUserDetails    = viewUserDetails;
window.exportUsersToCSV   = exportUsersToCSV;
window.applyRoleTemplate  = applyRoleTemplate;
window.closeEditModal     = closeEditModal;
window.closeDetailsModal  = closeDetailsModal;
window.closeAllModals     = closeAllModals;
window.previousPage       = previousPage;
window.nextPage           = nextPage;

console.log('✅ users.js loaded');
