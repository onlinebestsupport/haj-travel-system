/**
 * common.js - Shared utility functions for all admin pages
 * Alhudha Haj Travel Admin Panel
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

    const colors = {
        success: { bg: '#27ae60', icon: 'fa-check-circle' },
        error:   { bg: '#e74c3c', icon: 'fa-times-circle' },
        warning: { bg: '#f39c12', icon: 'fa-exclamation-triangle' },
        info:    { bg: '#3498db', icon: 'fa-info-circle' }
    };

    const cfg = colors[type] || colors.info;

    const notification = document.createElement('div');
    notification.id = 'adminNotification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${cfg.bg};
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        z-index: 99999;
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 0.95rem;
        font-weight: 500;
        max-width: 400px;
        animation: slideInRight 0.3s ease;
    `;

    notification.innerHTML = `
        <i class="fas ${cfg.icon}" style="font-size:1.2rem;flex-shrink:0;"></i>
        <span>${escapeHtml(message)}</span>
        <button onclick="this.parentElement.remove()" style="
            background:none;border:none;color:white;cursor:pointer;
            font-size:1.2rem;margin-left:auto;padding:0 0 0 10px;opacity:0.8;
        ">&times;</button>
    `;

    // Inject keyframe if not already present
    if (!document.getElementById('notificationStyles')) {
        const style = document.createElement('style');
        style.id = 'notificationStyles';
        style.textContent = `
            @keyframes slideInRight {
                from { opacity: 0; transform: translateX(100px); }
                to   { opacity: 1; transform: translateX(0); }
            }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(notification);

    // Auto-remove after duration
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
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
        background: rgba(0,0,0,0.5); z-index: 10000;
        display: flex; align-items: center; justify-content: center;
        animation: fadeIn 0.2s ease;
    `;

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
            @keyframes fadeIn {
                from { opacity: 0; }
                to   { opacity: 1; }
            }
            @keyframes modalFadeIn {
                from { opacity: 0; transform: translateY(-20px); }
                to   { opacity: 1; transform: translateY(0); }
            }
        `;
        document.head.appendChild(style);
    }

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeModal();
    });

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
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
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
    return '₹' + num.toLocaleString('en-IN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}

// ============================================================
// CONFIRMATION DIALOG
// ============================================================

/**
 * Show a confirmation dialog before a destructive action
 * @param {string}   message   - Confirmation message
 * @param {Function} onConfirm - Callback if user confirms
 */
function showConfirmation(message, onConfirm) {
    window._confirmCallback = onConfirm;

    showModal(
        '<i class="fas fa-exclamation-triangle" style="color:#f39c12;margin-right:8px;"></i>Confirm Action',
        `<p style="font-size:1rem;color:#2c3e50;line-height:1.6;">${escapeHtml(message)}</p>`,
        [
            {
                label: '<i class="fas fa-check"></i> Confirm',
                class: 'btn-danger',
                onClick: 'closeModal(); if(window._confirmCallback){ window._confirmCallback(); window._confirmCallback = null; }'
            },
            {
                label: '<i class="fas fa-times"></i> Cancel',
                class: 'btn-secondary',
                onClick: 'closeModal(); window._confirmCallback = null;'
            }
        ]
    );
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
        headers: {}
    };

    if (data !== null) {
        if (data instanceof FormData) {
            options.body = data;
        } else {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(data);
        }
    }

    options.headers['Accept'] = 'application/json';

    const response = await fetch(endpoint, options);

    if (response.status === 401) {
        showNotification('Session expired. Redirecting to login...', 'error');
        setTimeout(() => { window.location.href = '/admin.login.html'; }, 2000);
        throw new Error('Unauthorized');
    }

    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
        throw new Error(`Unexpected response type: ${contentType}`);
    }

    const json = await response.json();

    if (!response.ok) {
        throw new Error(json.error || json.message || `HTTP ${response.status}`);
    }

    return json;
}

// ============================================================
// ERROR HANDLING
// ============================================================

/**
 * Handle API errors gracefully
 * @param {Error} error
 * @param {string} [context] - Context description for logging
 */
function handleAPIError(error, context = '') {
    const msg = error.message || 'An unexpected error occurred';
    console.error(`API Error${context ? ' [' + context + ']' : ''}:`, error);
    if (msg !== 'Unauthorized') {
        showNotification(msg, 'error');
    }
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