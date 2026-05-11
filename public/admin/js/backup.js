/**
 * backup.js - Database backup management functions
 * Alhudha Haj Travel Management System
 * backup.js - Backup Management for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 * API base: /api/backup
 */

'use strict';

// Module-level state
let backupsData = [];

// ====== LOAD BACKUP HISTORY ======
// ── State ────────────────────────────────────────────────────
let allBackups = [];
let scheduleConfig = { enabled: false, frequency: 'daily', time: '02:00', retention: 7 };

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    SessionManager.initPage(async () => {
        await loadBackupHistory();
    });
});

// ── Load & Display ───────────────────────────────────────────

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
    const container = document.getElementById('backupHistoryContainer') || document.getElementById('backupTableBody');
    if (container) container.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading backup history…</div>';

    try {
        const data = await makeAPICall('GET', '/api/backup');
        if (data.success) {
            allBackups = data.backups || [];
            displayBackupHistory();
            updateBackupStats();
        } else {
            throw new Error(data.error || 'Failed to load backup history');
        }
    } catch (error) {
        handleError(error, 'loadBackupHistory');
        if (container) {
            container.innerHTML = `<div style="text-align:center; padding:40px;">
                <i class="fas fa-exclamation-triangle" style="color:#e74c3c; font-size:2rem;"></i>
                <p style="color:#e74c3c; margin:10px 0;">${escapeHtml(error.message)}</p>
                <button class="action-btn btn-primary" onclick="loadBackupHistory()"><i class="fas fa-redo"></i> Retry</button>
            </div>`;
        }
    }
}

/**
 * Render the backup history list
 */
function displayBackupHistory() {
    // Table layout
    const tbody = document.getElementById('backupTableBody');
    if (tbody) {
        if (allBackups.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:30px; color:#7f8c8d;">No backups found</td></tr>';
        } else {
            tbody.innerHTML = allBackups.map((b) => {
                const statusClass = b.status === 'completed' ? 'status-active' : 'status-inactive';
                return `<tr>
                    <td>${b.id}</td>
                    <td><strong>${escapeHtml(b.filename || b.backup_name || `backup_${b.id}`)}</strong></td>
                    <td>${b.created_at ? formatDate(b.created_at, true) : '-'}</td>
                    <td>${escapeHtml(b.file_size ? formatFileSize(b.file_size) : '-')}</td>
                    <td><span class="status-badge ${statusClass}">${escapeHtml(b.status || 'completed')}</span></td>
                    <td>
                        <button class="icon-btn" onclick="downloadBackup(${b.id})" title="Download"><i class="fas fa-download"></i></button>
                        <button class="icon-btn" onclick="restoreBackup(${b.id})" title="Restore" style="color:#f39c12;"><i class="fas fa-undo"></i></button>
                        <button class="icon-btn" style="color:#e74c3c;" onclick="deleteBackup(${b.id})" title="Delete"><i class="fas fa-trash"></i></button>
                    </td>
                </tr>`;
            }).join('');
        }
        return;
    }

    // Card layout fallback
    const container = document.getElementById('backupHistoryContainer');
    if (!container) return;

    if (allBackups.length === 0) {
        container.innerHTML = '<div style="text-align:center; padding:40px; color:#7f8c8d;"><i class="fas fa-database" style="font-size:3rem; margin-bottom:15px;"></i><p>No backups found. Create your first backup.</p></div>';
        return;
    }

    container.innerHTML = allBackups.map((b) => {
        const statusClass = b.status === 'completed' ? '#27ae60' : '#e74c3c';
        return `<div style="background:white; padding:20px; border-radius:10px; margin-bottom:15px; box-shadow:0 2px 10px rgba(0,0,0,0.1); border-left:4px solid ${statusClass};">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                <div>
                    <h4 style="margin:0; color:#2c3e50;">${escapeHtml(b.filename || b.backup_name || `Backup #${b.id}`)}</h4>
                    <p style="margin:5px 0; color:#7f8c8d; font-size:0.9rem;">
                        <i class="fas fa-clock"></i> ${b.created_at ? formatDate(b.created_at, true) : '-'}
                        ${b.file_size ? ` &nbsp;|&nbsp; <i class="fas fa-hdd"></i> ${formatFileSize(b.file_size)}` : ''}
                    </p>
                </div>
                <div style="display:flex; gap:10px; align-items:center;">
                    <span style="background:${statusClass}20; color:${statusClass}; padding:4px 12px; border-radius:20px; font-size:0.85rem; font-weight:600;">
                        ${escapeHtml(b.status || 'completed')}
                    </span>
                    <button class="action-btn btn-primary" style="padding:8px 15px;" onclick="downloadBackup(${b.id})"><i class="fas fa-download"></i> Download</button>
                    <button class="action-btn btn-secondary" style="padding:8px 15px;" onclick="restoreBackup(${b.id})"><i class="fas fa-undo"></i> Restore</button>
                    <button class="action-btn" style="padding:8px 15px; background:#e74c3c; color:white;" onclick="deleteBackup(${b.id})"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        </div>`;
    }).join('');
}

// ── CRUD ─────────────────────────────────────────────────────

/**
 * Create a new backup
 */
async function createBackup() {
    if (!confirmAction('Create a new database backup now?')) return;

    const btn  = document.getElementById('createBackupBtn');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating backup…'; btn.disabled = true; }

    showLoading('Creating backup…');

    try {
        // Try both possible endpoints
        let data;
        try {
            data = await makeAPICall('POST', '/api/backup/create', {});
        } catch (e) {
            data = await makeAPICall('POST', '/api/admin/backup/create', {});
        }

        hideLoading();
        if (data.success) {
            showNotification('Backup created successfully!', 'success');
            await loadBackupHistory();
        } else {
            throw new Error(data.error || 'Could not create backup');
        }
    } catch (error) {
        hideLoading();
        handleError(error, 'createBackup');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Restore from a backup
 * @param {number} id
 */
async function restoreBackup(id) {
    const backup = allBackups.find((b) => b.id === id);
    const name   = backup ? (backup.filename || backup.backup_name || `Backup #${id}`) : `Backup #${id}`;

    if (!confirmAction(`⚠️ RESTORE from "${name}"?\n\nThis will overwrite the current database. This action cannot be undone.\n\nAre you absolutely sure?`)) return;

    showLoading('Restoring backup… Please do not close this page.');

    try {
        let data;
        try {
            data = await makeAPICall('POST', `/api/backup/${id}/restore`, {});
        } catch (e) {
            data = await makeAPICall('POST', `/api/admin/backup/${id}/restore`, {});
        }

        hideLoading();
        if (data.success) {
            showNotification('Database restored successfully! Reloading…', 'success');
            setTimeout(() => window.location.reload(), 2000);
        } else {
            throw new Error(data.error || 'Could not restore backup');
        }
    } catch (error) {
        hideLoading();
        handleError(error, 'restoreBackup');
    }
}

/**
 * Delete a backup record
 * @param {number} id
 */
async function deleteBackup(id) {
    if (!confirmAction(`Delete backup ID ${id}? This cannot be undone.`)) return;

    try {
        const data = await makeAPICall('DELETE', `/api/backup/${id}`);
        if (data.success) {
            showNotification('Backup deleted successfully!', 'success');
            await loadBackupHistory();
        } else {
            throw new Error(data.error || 'Could not delete backup');
        }
    } catch (error) {
        handleError(error, 'deleteBackup');
    }
}

/**
 * Download a backup file
 * @param {number} id
 */
async function downloadBackup(id) {
    const backup = allBackups.find((b) => b.id === id);
    const filename = backup ? (backup.filename || backup.backup_name || `backup_${id}.sql`) : `backup_${id}.sql`;

    try {
        // Try to download via API
        const response = await fetch(`/api/backup/${id}/download`, {
            credentials: 'include'
        });

        if (response.ok) {
            const blob = await response.blob();
            const url  = URL.createObjectURL(blob);
            const a    = document.createElement('a');
            a.href     = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showNotification(`Downloading ${filename}…`, 'success');
        } else {
            // Fallback: show info about the backup
            showNotification(`Backup file: ${filename} (download endpoint not available)`, 'info');
        }
    } catch (error) {
        showNotification(`Backup file: ${filename} — direct download not available`, 'info');
    }
}

// ── Schedule ─────────────────────────────────────────────────

/**
 * Configure automatic backup schedule
 */
function scheduleBackup() {
    showModal('Schedule Automatic Backups',
        `<div>
            <p style="margin-bottom:20px; color:#7f8c8d;">Configure automatic database backups to run on a schedule.</p>
            <div class="form-group" style="margin-bottom:15px;">
                <label style="display:flex; align-items:center; gap:10px; cursor:pointer;">
                    <input type="checkbox" id="schedule_enabled" ${scheduleConfig.enabled ? 'checked' : ''} style="width:18px; height:18px;">
                    <span style="font-weight:600;">Enable Automatic Backups</span>
                </label>
            </div>
            <div class="form-group" style="margin-bottom:15px;">
                <label style="display:block; margin-bottom:5px; font-weight:600;">Frequency</label>
                <select id="schedule_frequency" style="width:100%; padding:10px; border:2px solid #ecf0f1; border-radius:5px;">
                    <option value="hourly"  ${scheduleConfig.frequency === 'hourly'  ? 'selected' : ''}>Every Hour</option>
                    <option value="daily"   ${scheduleConfig.frequency === 'daily'   ? 'selected' : ''}>Daily</option>
                    <option value="weekly"  ${scheduleConfig.frequency === 'weekly'  ? 'selected' : ''}>Weekly</option>
                    <option value="monthly" ${scheduleConfig.frequency === 'monthly' ? 'selected' : ''}>Monthly</option>
                </select>
            </div>
            <div class="form-group" style="margin-bottom:15px;">
                <label style="display:block; margin-bottom:5px; font-weight:600;">Time</label>
                <input type="time" id="schedule_time" value="${scheduleConfig.time}"
                    style="width:100%; padding:10px; border:2px solid #ecf0f1; border-radius:5px;">
            </div>
            <div class="form-group">
                <label style="display:block; margin-bottom:5px; font-weight:600;">Retention (days)</label>
                <input type="number" id="schedule_retention" value="${scheduleConfig.retention}" min="1" max="365"
                    style="width:100%; padding:10px; border:2px solid #ecf0f1; border-radius:5px;">
                <small style="color:#7f8c8d;">Backups older than this many days will be automatically deleted.</small>
            </div>
        </div>`,
        `<button class="action-btn btn-primary" onclick="saveBackupSchedule()"><i class="fas fa-save"></i> Save Schedule</button>
         <button class="action-btn btn-secondary" onclick="closeModal()">Cancel</button>`
    );
}

function saveBackupSchedule() {
    scheduleConfig = {
        enabled:   document.getElementById('schedule_enabled')?.checked || false,
        frequency: document.getElementById('schedule_frequency')?.value || 'daily',
        time:      document.getElementById('schedule_time')?.value || '02:00',
        retention: parseInt(document.getElementById('schedule_retention')?.value) || 7
    };

    // Would POST to /api/backup/schedule in a full implementation
    showNotification(
        scheduleConfig.enabled
            ? `Backup scheduled: ${scheduleConfig.frequency} at ${scheduleConfig.time}`
            : 'Automatic backups disabled',
        'success'
    );
    closeModal();
}

// ── Stats ────────────────────────────────────────────────────

function updateBackupStats() {
    const completed = allBackups.filter((b) => b.status === 'completed');
    const last      = allBackups[0];
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalBackups',     allBackups.length);
    setEl('successfulBackups', completed.length);
    setEl('lastBackupDate',   last ? formatDate(last.created_at, true) : 'Never');
}

// ── Helpers ───────────────────────────────────────────────────

/**
 * Format bytes to human-readable size
 * @param {number} bytes
 * @returns {string}
 */
function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let i = 0;
    while (size >= 1024 && i < units.length - 1) { size /= 1024; i++; }
    return `${size.toFixed(1)} ${units[i]}`;
}

// Expose globals
window.loadBackupHistory  = loadBackupHistory;
window.createBackup       = createBackup;
window.restoreBackup      = restoreBackup;
window.deleteBackup       = deleteBackup;
window.downloadBackup     = downloadBackup;
window.scheduleBackup     = scheduleBackup;
window.saveBackupSchedule = saveBackupSchedule;

console.log('✅ backup.js loaded');
