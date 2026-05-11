/**
 * common.js - Shared utilities for all Alhudha Haj Travel admin pages
 * Provides: notifications, modals, loading states, API wrapper, formatters, error handling
 */

'use strict';

// ============================================================
// NOTIFICATION SYSTEM
// ============================================================

/**
 * Show a toast notification
 * @param {string} message - Message to display
 * @param {string} type - 'success' | 'error' | 'info' | 'warning'
 * @param {number} duration - Duration in ms (default 3500)
 */
function showNotification(message, type = 'success', duration = 3500) {
    // Remove any existing notification
    const existing = document.getElementById('adminNotification');
    if (existing) existing.remove();

    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };

    const notification = document.createElement('div');
    notification.id = 'adminNotification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        border-radius: 8px;
        color: white;
        z-index: 99999;
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 1rem;
        font-weight: 500;
        box-shadow: 0 5px 20px rgba(0,0,0,0.25);
        animation: slideInRight 0.3s ease;
        max-width: 400px;
        word-break: break-word;
    `;

    const colors = {
        success: '#27ae60',
        error: '#e74c3c',
        warning: '#f39c12',
        info: '#3498db'
    };
    notification.style.background = colors[type] || colors.info;

    const icon = icons[type] || 'info-circle';
    notification.innerHTML = `<i class="fas fa-${icon}"></i> ${escapeHtml(message)}`;

    // Inject keyframe if not already present
    if (!document.getElementById('notifKeyframes')) {
        const style = document.createElement('style');
        style.id = 'notifKeyframes';
        style.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(120%); opacity: 0; }
                to   { transform: translateX(0);    opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.transition = 'opacity 0.4s ease';
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 400);
    }, duration);
}

// ============================================================
// MODAL SYSTEM
// ============================================================

/**
 * Show a generic modal with title and HTML content
 * @param {string} title
 * @param {string} content - HTML string
 * @param {string} [footerHtml] - Optional footer HTML
 */
function showModal(title, content, footerHtml = '') {
    closeModal(); // close any existing

    const overlay = document.createElement('div');
    overlay.id = 'commonModalOverlay';
    overlay.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.5); z-index: 9000;
        display: flex; align-items: center; justify-content: center;
    `;
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeModal();
    });

    const modal = document.createElement('div');
    modal.id = 'commonModal';
    modal.style.cssText = `
        background: white; border-radius: 12px; padding: 30px;
        max-width: 700px; width: 90%; max-height: 85vh;
        overflow-y: auto; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        animation: modalFadeIn 0.25s ease;
    `;

    if (!document.getElementById('modalKeyframes')) {
        const style = document.createElement('style');
        style.id = 'modalKeyframes';
        style.textContent = `
            @keyframes modalFadeIn {
                from { opacity: 0; transform: translateY(-20px); }
                to   { opacity: 1; transform: translateY(0); }
            }
        `;
        document.head.appendChild(style);
    }

    modal.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;
                    margin-bottom:20px; padding-bottom:15px; border-bottom:2px solid #ecf0f1;">
            <h3 style="color:#2c3e50; font-size:1.3rem;">${escapeHtml(title)}</h3>
            <button onclick="closeModal()" style="background:none; border:none; font-size:1.8rem;
                    cursor:pointer; color:#7f8c8d; line-height:1;" title="Close">&times;</button>
        </div>
        <div id="commonModalBody">${content}</div>
        ${footerHtml ? `<div style="margin-top:20px; padding-top:15px; border-top:1px solid #ecf0f1; display:flex; justify-content:flex-end; gap:10px;">${footerHtml}</div>` : ''}
    `;

    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    // Close on Escape
    const escHandler = (e) => { if (e.key === 'Escape') { closeModal(); document.removeEventListener('keydown', escHandler); } };
    document.addEventListener('keydown', escHandler);
}

/**
 * Close the common modal
 */
function closeModal() {
    const overlay = document.getElementById('commonModalOverlay');
    if (overlay) overlay.remove();
}

// ============================================================
// LOADING SPINNER
// ============================================================

/**
 * Show a full-page loading overlay
 */
function showLoading(message = 'Loading...') {
    if (document.getElementById('globalLoadingOverlay')) return;

    const overlay = document.createElement('div');
    overlay.id = 'globalLoadingOverlay';
    overlay.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(255,255,255,0.8); z-index: 99998;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center; gap: 15px;
    `;
    overlay.innerHTML = `
        <i class="fas fa-spinner fa-spin" style="font-size:3rem; color:#3498db;"></i>
        <p style="color:#2c3e50; font-size:1.1rem; font-weight:500;">${escapeHtml(message)}</p>
    `;
    document.body.appendChild(overlay);
}

/**
 * Hide the loading overlay
 */
function hideLoading() {
    const overlay = document.getElementById('globalLoadingOverlay');
    if (overlay) overlay.remove();
}

// ============================================================
// HTML ESCAPING
// ============================================================

/**
 * Escape HTML to prevent XSS
 * @param {*} text
 * @returns {string}
 */
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const str = String(text);
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return str.replace(/[&<>"']/g, (m) => map[m]);
}

// ============================================================
// DATE & CURRENCY FORMATTERS
// ============================================================

/**
 * Format a date string or Date object to a readable format
 * @param {string|Date} date
 * @param {boolean} includeTime
 * @returns {string}
 */
function formatDate(date, includeTime = false) {
    if (!date) return '-';
    try {
        const d = new Date(date);
        if (isNaN(d.getTime())) return String(date);
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        if (includeTime) {
            options.hour = '2-digit';
            options.minute = '2-digit';
        }
        return d.toLocaleDateString('en-IN', options);
    } catch (e) {
        return String(date);
    }
}

/**
 * Format a number as Indian Rupee currency
 * @param {number|string} amount
 * @returns {string}
 */
function formatCurrency(amount) {
    if (amount === null || amount === undefined || amount === '') return '₹0';
    const num = parseFloat(amount);
    if (isNaN(num)) return '₹0';
    return '₹' + num.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

// ============================================================
// ERROR HANDLER
// ============================================================

/**
 * Centralised error handler
 * @param {Error|string} error
 * @param {string} [context] - Optional context label
 */
function handleError(error, context = '') {
    const msg = error instanceof Error ? error.message : String(error);
    const label = context ? `[${context}] ` : '';
    console.error(`❌ ${label}${msg}`, error);

    if (error && error.status === 401) {
        showNotification('Session expired. Redirecting to login…', 'warning');
        setTimeout(() => { window.location.href = '/admin.login.html'; }, 2000);
        return;
    }

    showNotification(`${label}${msg}`, 'error');
}

// ============================================================
// API WRAPPER
// ============================================================

/**
 * Make an authenticated API call
 * @param {string} method - HTTP method (GET, POST, PUT, DELETE)
 * @param {string} endpoint - API endpoint (e.g. '/api/users')
 * @param {Object|null} data - Request body for POST/PUT
 * @returns {Promise<Object>} Parsed JSON response
 */
async function makeAPICall(method, endpoint, data = null) {
    const options = {
        method: method.toUpperCase(),
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
        }
    };

    if (data && ['POST', 'PUT', 'PATCH'].includes(options.method)) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(endpoint, options);

    if (response.status === 401) {
        const err = new Error('Unauthorized – session expired');
        err.status = 401;
        throw err;
    }

    let json;
    try {
        json = await response.json();
    } catch (e) {
        throw new Error(`Invalid JSON response from ${endpoint}`);
    }

    if (!response.ok) {
        throw new Error(json.error || json.message || `HTTP ${response.status}`);
    }

    return json;
}

// ============================================================
// CSV EXPORT HELPER
// ============================================================

/**
 * Download an array of objects as a CSV file
 * @param {Array<Object>} rows
 * @param {string[]} columns - Keys to include
 * @param {string[]} headers - Column header labels
 * @param {string} filename
 */
function downloadCSV(rows, columns, headers, filename) {
    if (!rows || rows.length === 0) {
        showNotification('No data to export', 'warning');
        return;
    }

    const escape = (val) => {
        if (val === null || val === undefined) return '';
        const s = String(val).replace(/"/g, '""');
        return `"${s}"`;
    };

    const lines = [headers.map(escape).join(',')];
    rows.forEach((row) => {
        lines.push(columns.map((col) => escape(row[col])).join(','));
    });

    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showNotification(`Exported ${rows.length} records to ${filename}`, 'success');
}

// ============================================================
// CONFIRM DIALOG HELPER
// ============================================================

/**
 * Show a styled confirmation dialog
 * @param {string} message
 * @returns {boolean}
 */
function confirmAction(message) {
    return window.confirm(message);
}

// ============================================================
// DEBOUNCE HELPER
// ============================================================

/**
 * Debounce a function call
 * @param {Function} fn
 * @param {number} delay
 * @returns {Function}
 */
function debounce(fn, delay = 300) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

console.log('✅ common.js loaded');
