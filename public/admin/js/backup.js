/**
 * backup.js - Database backup management functions
 * Alhudha Haj Travel Management System
 */

'use strict';

// Module-level state
let backupsData = [];

// ====== LOAD BACKUP HISTORY ======
/**
 * Fetch backup history from the API
 */
async function loadBackupHistory() {
    showLoading(true);
    try {
        const data = await makeApiCall('GET', '/api/backup');
        backupsData = Array.isArray(data) ? data : (data.backups || []);
        displayBackupHistory(backupsData);
        console.log(`✅ Loaded ${backupsData.length} backups`);
    } catch (error) {
        handleApiError(error, 'Load backup history');
    } finally {
        showLoading(false);
    }
}

// ====== DISPLAY BACKUP HISTORY ======
/**
 * Render backup history in the table
 * @param {Array} backups
 */
function displayBackupHistory(backups) {
    const tbody = document.getElementById('backupsTableBody') || document.getElementById('backupList');
    if (!tbody) return;

    if (!backups || backups.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align:center;padding:40px;color:#95a5a6;">
                    <i class="fas fa-database" style="font-size:2rem;display:block;margin-bottom:10px;"></i>
                    No backups found
                </td>
            </tr>`;
        return;
    }

    tbody.innerHTML = backups.map(b => {
        const status = b.status || 'completed';
        const statusClass = status.toLowerCase() === 'completed' ? 'badge-success' :
                            status.toLowerCase() === 'failed'    ? 'badge-danger'  : 'badge-warning';
        const fileSize = b.file_size ? formatFileSize(b.file_size) : '-';
        return `
            <tr>
                <td>${escapeHtml(String(b.id || ''))}</td>
                <td>${escapeHtml(b.filename || b.file_name || `backup_${b.id}.sql`)}</td>
                <td>${formatDate(b.created_at || b.backup_date)}</td>
                <td>${fileSize}</td>
                <td><span class="status-badge ${statusClass}">${escapeHtml(status)}</span></td>
                <td>
                    <button class="icon-btn" onclick="downloadBackup(${b.id})" title="Download" style="color:#3498db;">
                        <i class="fas fa-download"></i>
                    </button>
                    <button class="icon-btn" onclick="restoreBackup(${b.id})" title="Restore" style="color:#f39c12;">
                        <i class="fas fa-undo"></i>
                    </button>
                    <button class="icon-btn btn-delete" onclick="deleteBackup(${b.id})" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>`;
    }).join('');
}

/**
 * Format file size in human-readable format
 * @param {number} bytes
 * @returns {string}
 */
function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

// ====== CREATE BACKUP ======
/**
 * Trigger a new database backup
 */
async function createBackup() {
    showConfirmation(
        'Create a new database backup now? This may take a few moments.',
        async () => {
            showLoading(true);
            try {
                const result = await makeApiCall('POST', '/api/backup', {
                    type: 'full',
                    timestamp: new Date().toISOString()
                });

                if (result.success || result.id || result.backup_id) {
                    showNotification('Backup created successfully!', 'success');
                    await loadBackupHistory();
                } else {
                    showNotification(result.error || 'Failed to create backup', 'error');
                }
            } catch (error) {
                handleApiError(error, 'Create backup');
            } finally {
                showLoading(false);
            }
        }
    );
}

// ====== RESTORE BACKUP ======
/**
 * Restore the database from a backup
 * @param {number} backupId
 */
function restoreBackup(backupId) {
    const backup = backupsData.find(b => b.id === backupId);
    const label  = backup ? (backup.filename || backup.file_name || `Backup #${backupId}`) : `Backup #${backupId}`;
    const date   = backup ? formatDate(backup.created_at || backup.backup_date) : '';

    showConfirmation(
        `⚠️ WARNING: Restoring "${label}" (${date}) will overwrite ALL current data. This action cannot be undone. Are you absolutely sure?`,
        async () => {
            showLoading(true);
            try {
                const result = await makeApiCall('POST', `/api/backup/${backupId}/restore`, {});
                if (result.success || result.message) {
                    showNotification('Database restored successfully! The page will reload.', 'success');
                    setTimeout(() => window.location.reload(), 2000);
                } else {
                    showNotification(result.error || 'Failed to restore backup', 'error');
                }
            } catch (error) {
                handleApiError(error, 'Restore backup');
            } finally {
                showLoading(false);
            }
        }
    );
}

// ====== DELETE BACKUP ======
/**
 * Delete a backup file after confirmation
 * @param {number} backupId
 */
function deleteBackup(backupId) {
    const backup = backupsData.find(b => b.id === backupId);
    const label  = backup ? (backup.filename || backup.file_name || `Backup #${backupId}`) : `Backup #${backupId}`;

    showConfirmation(
        `Are you sure you want to delete backup "${label}"? This action cannot be undone.`,
        async () => {
            showLoading(true);
            try {
                const result = await makeApiCall('DELETE', `/api/backup/${backupId}`);
                if (result.success || result.message) {
                    showNotification('Backup deleted successfully!', 'success');
                    await loadBackupHistory();
                } else {
                    showNotification(result.error || 'Failed to delete backup', 'error');
                }
            } catch (error) {
                handleApiError(error, 'Delete backup');
            } finally {
                showLoading(false);
            }
        }
    );
}

// ====== DOWNLOAD BACKUP ======
/**
 * Download a backup file
 * @param {number} backupId
 */
async function downloadBackup(backupId) {
    showLoading(true);
    try {
        const response = await fetch(`/api/backup/${backupId}/download`, {
            credentials: 'include'
        });

        if (!response.ok) throw new Error(`Download failed: HTTP ${response.status}`);

        const blob        = await response.blob();
        const backup      = backupsData.find(b => b.id === backupId);
        const filename    = backup ? (backup.filename || backup.file_name || `backup_${backupId}.sql`) : `backup_${backupId}.sql`;
        const url         = URL.createObjectURL(blob);
        const link        = document.createElement('a');
        link.href         = url;
        link.download     = filename;
        link.click();
        URL.revokeObjectURL(url);

        showNotification(`Backup "${filename}" downloaded successfully!`, 'success');
    } catch (error) {
        handleApiError(error, 'Download backup');
    } finally {
        showLoading(false);
    }
}

// Alias for backward compatibility with existing HTML
const loadBackups = loadBackupHistory;
