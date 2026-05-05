/**
 * backup.js - Backup management functions
 * Alhudha Haj Travel Admin Panel
 */

'use strict';

// ====== STATE ======
let backupsData = [];

// ====== LOAD BACKUP HISTORY ======
/**
 * Fetch backup history from /api/backup
 */
async function loadBackupHistory() {
    const tableBody = document.getElementById('backupsTableBody');
    if (tableBody) {
        tableBody.innerHTML = '<tr><td colspan="6" class="loading"><i class="fas fa-spinner fa-spin"></i> Loading backups...</td></tr>';
    }

    try {
        const data = await makeAPICall('GET', '/api/backup');
        if (data.success && Array.isArray(data.backups)) {
            backupsData = data.backups;
            console.log(`✅ Loaded ${backupsData.length} backups`);
        } else {
            backupsData = [];
        }
    } catch (error) {
        handleAPIError(error, 'loadBackupHistory');
        backupsData = [];
    }

    displayBackupHistory();
}

// Alias for inline HTML
function loadBackups() { loadBackupHistory(); }

// ====== DISPLAY BACKUP HISTORY ======
/**
 * Render the backup history table
 */
function displayBackupHistory() {
    const tableBody = document.getElementById('backupsTableBody');
    if (!tableBody) return;

    if (!backupsData || backupsData.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;">No backups found. Click "Create Backup" to create one.</td></tr>';
        return;
    }

    tableBody.innerHTML = backupsData.map(b => {
        const size = b.file_size ? formatFileSize(b.file_size) : '-';
        const statusClass = b.status === 'completed' ? 'badge-success' : b.status === 'failed' ? 'badge-danger' : 'badge-warning';

        return `<tr>
            <td>${b.id}</td>
            <td>${escapeHtml(b.filename || '-')}</td>
            <td>${formatDate(b.created_at)}</td>
            <td>${size}</td>
            <td><span class="badge ${statusClass}">${escapeHtml(b.status || '-')}</span></td>
            <td>
                <button class="action-btn btn-info" onclick="downloadBackup(${b.id})" style="padding:5px 12px;font-size:0.8rem;" title="Download">
                    <i class="fas fa-download"></i> Download
                </button>
                <button class="action-btn btn-warning" onclick="restoreBackup(${b.id})" style="padding:5px 12px;font-size:0.8rem;" title="Restore">
                    <i class="fas fa-undo"></i> Restore
                </button>
                <button class="action-btn btn-danger" onclick="deleteBackup(${b.id})" style="padding:5px 12px;font-size:0.8rem;" title="Delete">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </td>
        </tr>`;
    }).join('');
}

// ====== CREATE BACKUP ======
/**
 * Trigger a new database backup
 */
async function createBackup() {
    const btn = document.getElementById('createBackupBtn');
    showLoading(btn, 'Creating...');

    try {
        const data = await makeAPICall('POST', '/api/backup/create', {});
        if (data.success) {
            showNotification('Backup created successfully!', 'success');
            await loadBackupHistory();
        } else {
            showNotification('Error: ' + (data.error || 'Could not create backup'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'createBackup');
    } finally {
        hideLoading(btn);
    }
}

// ====== RESTORE BACKUP ======
/**
 * Restore the database from a backup
 * @param {number} id
 */
async function restoreBackup(id) {
    const backup = backupsData.find(b => b.id === id);
    const filename = backup ? backup.filename : `backup #${id}`;

    if (!confirm(`⚠️ WARNING: Restoring from "${filename}" will overwrite all current data. This action cannot be undone.\n\nAre you absolutely sure?`)) return;

    showNotification('Restoring backup... Please wait.', 'info');

    try {
        const data = await makeAPICall('POST', `/api/backup/${id}/restore`, {});
        if (data.success) {
            showNotification('Backup restored successfully! The page will reload.', 'success');
            setTimeout(() => window.location.reload(), 3000);
        } else {
            showNotification('Error: ' + (data.error || 'Could not restore backup'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'restoreBackup');
    }
}

// ====== DELETE BACKUP ======
/**
 * Delete a backup record
 * @param {number} id
 */
async function deleteBackup(id) {
    if (!confirm('Are you sure you want to delete this backup?')) return;

    try {
        const data = await makeAPICall('DELETE', `/api/backup/${id}`);
        if (data.success) {
            showNotification('Backup deleted successfully!', 'success');
            await loadBackupHistory();
        } else {
            showNotification('Error: ' + (data.error || 'Could not delete backup'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'deleteBackup');
    }
}

// ====== DOWNLOAD BACKUP ======
/**
 * Download a backup file
 * @param {number} id
 */
async function downloadBackup(id) {
    const backup = backupsData.find(b => b.id === id);
    if (!backup) { showNotification('Backup not found', 'error'); return; }

    showNotification('Preparing download...', 'info');

    try {
        // Try direct download link
        const downloadUrl = `/api/backup/${id}/download`;
        const response = await fetch(downloadUrl, { credentials: 'include' });

        if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = backup.filename || `backup_${id}.sql`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showNotification('Download started!', 'success');
        } else if (response.status === 401) {
            showNotification('Session expired. Please login again.', 'error');
            setTimeout(() => { window.location.href = '/admin.login.html'; }, 2000);
        } else {
            showNotification('Download failed. File may not be available.', 'error');
        }
    } catch (error) {
        showNotification('Download failed: ' + (error.message || 'Network error'), 'error');
        console.error('Download error:', error);
    }
}

// ====== FORMAT FILE SIZE ======
function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

console.log('✅ backup.js loaded');
