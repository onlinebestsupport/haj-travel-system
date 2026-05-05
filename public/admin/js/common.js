/**
 * common.js - Shared utility functions for all admin pages
 * Alhudha Haj Travel Admin Panel
 */

'use strict';

// ====== NOTIFICATION ======
/**
 * Show a toast notification
 * @param {string} message - Message to display
 * @param {string} type - 'success' | 'error' | 'warning' | 'info'
 * @param {number} duration - Duration in ms (default 3500)
 */
function showNotification(message, type = 'success', duration = 3500) {
    let notification = document.getElementById('notification');
    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'notification';
        notification.className = 'notification';
        document.body.appendChild(notification);
    }

    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };

    notification.className = `notification notification-${type}`;
    notification.innerHTML = `<i class="fas fa-${icons[type] || 'info-circle'}"></i> ${escapeHtml(message)}`;
    notification.style.display = 'block';

    if (window._notificationTimeout) clearTimeout(window._notificationTimeout);
    window._notificationTimeout = setTimeout(() => {
        notification.style.display = 'none';
    }, duration);
}

// ====== MODAL ======
/**
 * Show a generic modal dialog
 * @param {string} title - Modal title
 * @param {string} content - HTML content for modal body
 * @param {string} [footerHtml] - Optional footer HTML
 */
function showModal(title, content, footerHtml = '') {
    let overlay = document.getElementById('modalOverlay');
    let modal = document.getElementById('genericModal');

    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'modalOverlay';
        overlay.className = 'modal-overlay';
        overlay.onclick = closeModal;
        document.body.appendChild(overlay);
    }

    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'genericModal';
        modal.className = 'modal';
        document.body.appendChild(modal);
    }

    modal.innerHTML = `
        <div class="modal-header">
            <h3>${title}</h3>
            <button class="modal-close" onclick="closeModal()">&times;</button>
        </div>
        <div class="modal-body">${content}</div>
        ${footerHtml ? `<div class="modal-footer">${footerHtml}</div>` : ''}
    `;

    modal.style.display = 'block';
    overlay.style.display = 'block';
}

/**
 * Close the active modal
 */
function closeModal() {
    const overlay = document.getElementById('modalOverlay');
    const modal = document.getElementById('genericModal');
    if (modal) modal.style.display = 'none';
    if (overlay) overlay.style.display = 'none';
}

// ====== HTML SANITIZATION ======
/**
 * Escape HTML special characters to prevent XSS
 * @param {*} text
 * @returns {string}
 */
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// ====== DATE FORMATTING ======
/**
 * Format a date string or Date object for display
 * @param {string|Date} date
 * @param {string} [locale='en-IN']
 * @returns {string}
 */
function formatDate(date, locale = 'en-IN') {
    if (!date) return '-';
    try {
        const d = new Date(date);
        if (isNaN(d.getTime())) return String(date);
        return d.toLocaleDateString(locale, { day: '2-digit', month: 'short', year: 'numeric' });
    } catch (e) {
        return String(date);
    }
}

/**
 * Format a date string to YYYY-MM-DD for input[type=date]
 * @param {string} dateStr
 * @returns {string}
 */
function formatDateForInput(dateStr) {
    if (!dateStr) return '';
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return dateStr;
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return '';
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
    } catch (e) {
        return '';
    }
}

// ====== CURRENCY FORMATTING ======
/**
 * Format a number as Indian Rupee currency
 * @param {number|string} amount
 * @returns {string}
 */
function formatCurrency(amount) {
    const num = parseFloat(amount);
    if (isNaN(num)) return '₹0';
    return '₹' + num.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

// ====== PHONE FORMATTING ======
/**
 * Format a phone number for display
 * @param {string} phone
 * @returns {string}
 */
function formatPhoneNumber(phone) {
    if (!phone) return '-';
    const cleaned = String(phone).replace(/\D/g, '');
    if (cleaned.length === 10) {
        return `+91 ${cleaned.slice(0, 5)} ${cleaned.slice(5)}`;
    }
    if (cleaned.length === 12 && cleaned.startsWith('91')) {
        return `+${cleaned.slice(0, 2)} ${cleaned.slice(2, 7)} ${cleaned.slice(7)}`;
    }
    return phone;
}

// ====== VALIDATION ======
/**
 * Validate an email address
 * @param {string} email
 * @returns {boolean}
 */
function validateEmail(email) {
    if (!email) return false;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email).trim());
}

/**
 * Validate a phone number (Indian format)
 * @param {string} phone
 * @returns {boolean}
 */
function validatePhone(phone) {
    if (!phone) return false;
    const cleaned = String(phone).replace(/\D/g, '');
    return cleaned.length >= 10 && cleaned.length <= 13;
}

// ====== API CALL WRAPPER ======
/**
 * Make an authenticated API call
 * @param {string} method - HTTP method
 * @param {string} endpoint - API endpoint URL
 * @param {Object|FormData|null} data - Request body
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
            // Let browser set Content-Type with boundary for FormData
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

// ====== ERROR HANDLING ======
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

// ====== LOADING STATE ======
/**
 * Show a loading spinner inside an element
 * @param {HTMLElement|string} element - Element or element ID
 * @param {string} [message='Loading...']
 */
function showLoading(element, message = 'Loading...') {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (!el) return;
    el.dataset.originalContent = el.innerHTML;
    el.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${escapeHtml(message)}`;
    if (el.tagName === 'BUTTON') el.disabled = true;
}

/**
 * Hide loading state and restore original content
 * @param {HTMLElement|string} element - Element or element ID
 */
function hideLoading(element) {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (!el) return;
    if (el.dataset.originalContent !== undefined) {
        el.innerHTML = el.dataset.originalContent;
        delete el.dataset.originalContent;
    }
    if (el.tagName === 'BUTTON') el.disabled = false;
}

// ====== CSV EXPORT HELPER ======
/**
 * Download data as a CSV file
 * @param {string[][]} rows - Array of rows (each row is an array of values)
 * @param {string} filename - Output filename
 */
function downloadCSV(rows, filename) {
    const csvContent = rows.map(row =>
        row.map(cell => {
            const val = cell === null || cell === undefined ? '' : String(cell);
            return '"' + val.replace(/"/g, '""') + '"';
        }).join(',')
    ).join('\n');

    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ====== PAGINATION HELPER ======
/**
 * Update pagination display elements
 * @param {number} total - Total number of items
 * @param {number} currentPage - Current page (1-based)
 * @param {number} itemsPerPage - Items per page
 */
function updatePaginationDisplay(total, currentPage, itemsPerPage) {
    const start = total > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0;
    const end = Math.min(currentPage * itemsPerPage, total);

    const fromEl = document.getElementById('showingFrom');
    const toEl = document.getElementById('showingTo');
    const totalEl = document.getElementById('totalCount');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    if (fromEl) fromEl.textContent = start;
    if (toEl) toEl.textContent = end;
    if (totalEl) totalEl.textContent = total;
    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = end >= total;
}

// ====== STATUS BADGE HELPER ======
/**
 * Get CSS class for a status badge
 * @param {string} status
 * @returns {string}
 */
function getStatusClass(status) {
    const map = {
        'active': 'status-active',
        'open': 'status-active',
        'paid': 'status-success',
        'completed': 'status-success',
        'success': 'status-success',
        'pending': 'status-pending',
        'processing': 'status-warning',
        'warning': 'status-warning',
        'closing soon': 'status-warning',
        'inactive': 'status-inactive',
        'expired': 'status-inactive',
        'closed': 'status-inactive',
        'full': 'status-inactive',
        'cancelled': 'status-inactive',
        'reversed': 'status-inactive',
        'overdue': 'status-inactive'
    };
    return map[(status || '').toLowerCase()] || 'status-pending';
}

console.log('✅ common.js loaded');
