/**
 * receipts.js - Receipt Management for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 * API base: /api/receipts
 */

'use strict';

// ── State ────────────────────────────────────────────────────
let allReceipts = [];
let filteredReceipts = [];
let receiptsPage = 1;
const RECEIPTS_PER_PAGE = 20;

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    SessionManager.initPage(async () => {
        await loadReceipts();
        initReceiptSearchListeners();
    });
});

function initReceiptSearchListeners() {
    const searchEl = document.getElementById('searchReceipts');
    const dateEl   = document.getElementById('receiptDateFilter');
    if (searchEl) searchEl.addEventListener('input', debounce(filterReceipts, 250));
    if (dateEl)   dateEl.addEventListener('change', filterReceipts);
}

// ── Load & Display ───────────────────────────────────────────

/**
 * Fetch all receipts from the API
 */
async function loadReceipts() {
    const container = document.getElementById('receiptsContainer') || document.getElementById('receiptsTableBody');
    if (container) container.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading receipts…</div>';

    try {
        const data = await makeAPICall('GET', '/api/receipts');
        if (data.success) {
            allReceipts = data.receipts || [];
            filteredReceipts = [...allReceipts];
            receiptsPage = 1;
            displayReceipts();
            updateReceiptStats();
        } else {
            throw new Error(data.error || 'Failed to load receipts');
        }
    } catch (error) {
        handleError(error, 'loadReceipts');
        if (container) {
            container.innerHTML = `<div style="text-align:center; padding:40px;">
                <i class="fas fa-exclamation-triangle" style="color:#e74c3c; font-size:2rem;"></i>
                <p style="color:#e74c3c; margin:10px 0;">${escapeHtml(error.message)}</p>
                <button class="action-btn btn-primary" onclick="loadReceipts()"><i class="fas fa-redo"></i> Retry</button>
            </div>`;
        }
    }
}

/**
 * Render receipts – supports both card layout and table layout
 */
function displayReceipts() {
    const start = (receiptsPage - 1) * RECEIPTS_PER_PAGE;
    const page  = filteredReceipts.slice(start, start + RECEIPTS_PER_PAGE);

    // Table layout
    const tbody = document.getElementById('receiptsTableBody');
    if (tbody) {
        if (page.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:30px; color:#7f8c8d;">No receipts found</td></tr>';
        } else {
            tbody.innerHTML = page.map((r) => `<tr>
                <td>${r.id}</td>
                <td><strong>${escapeHtml(r.receipt_number || '-')}</strong></td>
                <td>${escapeHtml(r.traveler_name || '-')}</td>
                <td>${escapeHtml(r.passport_no || '-')}</td>
                <td><strong>${formatCurrency(r.amount)}</strong></td>
                <td>${r.receipt_date ? formatDate(r.receipt_date) : '-'}</td>
                <td>${escapeHtml(r.payment_method || '-')}</td>
                <td>
                    <button class="icon-btn" onclick="viewReceiptDetails(${r.id})" title="View"><i class="fas fa-eye"></i></button>
                    <button class="icon-btn" onclick="printReceipt(${r.id})" title="Print"><i class="fas fa-print"></i></button>
                    <button class="icon-btn" style="color:#e74c3c;" onclick="deleteReceipt(${r.id})" title="Delete"><i class="fas fa-trash"></i></button>
                </td>
            </tr>`).join('');
        }
        updateReceiptPagination();
        return;
    }

    // Card layout (receipts.html uses cards)
    const container = document.getElementById('receiptsContainer');
    if (!container) return;

    if (page.length === 0) {
        container.innerHTML = '<div style="text-align:center; padding:40px; color:#7f8c8d;"><i class="fas fa-receipt" style="font-size:3rem; margin-bottom:15px;"></i><p>No receipts found</p></div>';
        updateReceiptPagination();
        return;
    }

    container.innerHTML = page.map((r) => `
        <div class="receipt-card">
            <div class="receipt-header">
                <span class="receipt-number"><i class="fas fa-receipt"></i> ${escapeHtml(r.receipt_number || `REC-${r.id}`)}</span>
                <span class="receipt-amount">${formatCurrency(r.amount)}</span>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:10px;">
                <div><i class="fas fa-user" style="color:#f1c40f;"></i> <strong>Traveler:</strong> ${escapeHtml(r.traveler_name || '-')}</div>
                <div><i class="fas fa-passport" style="color:#f1c40f;"></i> <strong>Passport:</strong> ${escapeHtml(r.passport_no || '-')}</div>
                <div><i class="fas fa-calendar" style="color:#f1c40f;"></i> <strong>Date:</strong> ${r.receipt_date ? formatDate(r.receipt_date) : '-'}</div>
                <div><i class="fas fa-credit-card" style="color:#f1c40f;"></i> <strong>Method:</strong> ${escapeHtml(r.payment_method || '-')}</div>
            </div>
            <div class="receipt-actions">
                <button class="btn-view" onclick="viewReceiptDetails(${r.id})"><i class="fas fa-eye"></i> View</button>
                <button class="btn-print-receipt" onclick="printReceipt(${r.id})"><i class="fas fa-print"></i> Print</button>
                <button class="action-btn btn-secondary" style="padding:8px 15px;" onclick="deleteReceipt(${r.id})"><i class="fas fa-trash"></i> Delete</button>
            </div>
        </div>`).join('');

    updateReceiptPagination();
}

// ── Filter ───────────────────────────────────────────────────

/**
 * Filter receipts by search text and date
 */
function filterReceipts() {
    const search = (document.getElementById('searchReceipts')?.value || '').toLowerCase();
    const date   = document.getElementById('receiptDateFilter')?.value || '';

    filteredReceipts = allReceipts.filter((r) => {
        const matchSearch = !search ||
            (r.receipt_number || '').toLowerCase().includes(search) ||
            (r.traveler_name || '').toLowerCase().includes(search) ||
            (r.passport_no || '').toLowerCase().includes(search);
        const matchDate = !date || (r.receipt_date && r.receipt_date.slice(0, 10) === date);
        return matchSearch && matchDate;
    });

    receiptsPage = 1;
    displayReceipts();
}

// ── Form Visibility ──────────────────────────────────────────

function showAddReceiptForm() {
    const form = document.getElementById('createReceiptForm') || document.getElementById('addReceiptForm');
    if (!form) return;
    form.style.display = 'block';
    form.scrollIntoView({ behavior: 'smooth' });
    const dateEl = document.getElementById('receipt_date');
    if (dateEl && !dateEl.value) dateEl.value = new Date().toISOString().slice(0, 10);
}

function hideAddReceiptForm() {
    const form = document.getElementById('createReceiptForm') || document.getElementById('addReceiptForm');
    if (form) form.style.display = 'none';
    document.getElementById('receiptCreateForm')?.reset();
}

// ── CRUD ─────────────────────────────────────────────────────

/**
 * Create a new receipt
 */
async function createReceipt(event) {
    if (event) event.preventDefault();

    const getData = (id) => (document.getElementById(id)?.value || '').trim();

    const receiptData = {
        traveler_id:    getData('receipt_traveler_id') || getData('traveler_id'),
        payment_id:     getData('receipt_payment_id') || getData('payment_id') || null,
        amount:         parseFloat(getData('receipt_amount') || getData('amount')),
        receipt_date:   getData('receipt_date') || new Date().toISOString().slice(0, 10),
        payment_method: getData('receipt_payment_method') || getData('payment_method') || null,
        notes:          getData('receipt_notes') || getData('notes') || null
    };

    if (!receiptData.traveler_id || !receiptData.amount || isNaN(receiptData.amount)) {
        showNotification('Traveler and a valid amount are required', 'error');
        return;
    }

    const btn  = document.querySelector('#receiptCreateForm button[type="submit"]');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating…'; btn.disabled = true; }

    try {
        const data = await makeAPICall('POST', '/api/receipts', receiptData);
        if (data.success) {
            showNotification(`Receipt ${data.receipt_number} created successfully!`, 'success');
            hideAddReceiptForm();
            await loadReceipts();
        } else {
            throw new Error(data.error || 'Could not create receipt');
        }
    } catch (error) {
        handleError(error, 'createReceipt');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Load receipt data into the edit modal
 * @param {number} id
 */
async function editReceipt(id) {
    try {
        const data = await makeAPICall('GET', `/api/receipts/${id}`);
        if (!data.success || !data.receipt) throw new Error(data.error || 'Receipt not found');

        const r = data.receipt;
        const set = (elId, val) => { const el = document.getElementById(elId); if (el) el.value = val || ''; };

        set('edit_receipt_id',     r.id);
        set('edit_receipt_amount', r.amount);
        set('edit_receipt_date',   r.receipt_date ? r.receipt_date.slice(0, 10) : '');
        set('edit_receipt_method', r.payment_method);
        set('edit_receipt_notes',  r.notes);

        const modal   = document.getElementById('editReceiptModal');
        const overlay = document.getElementById('modalOverlay');
        if (modal)   modal.style.display   = 'block';
        if (overlay) overlay.style.display = 'block';
    } catch (error) {
        handleError(error, 'editReceipt');
    }
}

/**
 * Submit the edit receipt form
 */
async function updateReceipt(event) {
    if (event) event.preventDefault();

    const id = document.getElementById('edit_receipt_id')?.value;
    if (!id) return;

    const getData = (elId) => (document.getElementById(elId)?.value || '').trim();

    const receiptData = {
        amount:         parseFloat(getData('edit_receipt_amount')),
        receipt_date:   getData('edit_receipt_date'),
        payment_method: getData('edit_receipt_method') || null,
        notes:          getData('edit_receipt_notes') || null
    };

    const btn  = document.querySelector('#editReceiptForm button[type="submit"]');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating…'; btn.disabled = true; }

    try {
        // Receipts API may not have a PUT endpoint; use a generic update
        const data = await makeAPICall('PUT', `/api/receipts/${id}`, receiptData);
        if (data.success) {
            showNotification('Receipt updated successfully!', 'success');
            closeReceiptModal();
            await loadReceipts();
        } else {
            throw new Error(data.error || 'Could not update receipt');
        }
    } catch (error) {
        handleError(error, 'updateReceipt');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Delete a receipt by ID
 * @param {number} id
 */
async function deleteReceipt(id) {
    if (!confirmAction(`Delete receipt ID ${id}? This cannot be undone.`)) return;

    try {
        const data = await makeAPICall('DELETE', `/api/receipts/${id}`);
        if (data.success) {
            showNotification('Receipt deleted successfully!', 'success');
            await loadReceipts();
        } else {
            throw new Error(data.error || 'Could not delete receipt');
        }
    } catch (error) {
        handleError(error, 'deleteReceipt');
    }
}

/**
 * View receipt details in a modal
 * @param {number} id
 */
async function viewReceiptDetails(id) {
    try {
        showLoading('Loading receipt…');
        const data = await makeAPICall('GET', `/api/receipts/${id}`);
        hideLoading();

        if (!data.success || !data.receipt) throw new Error(data.error || 'Receipt not found');
        const r = data.receipt;

        const content = `
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px;">
                <div><strong>Receipt #:</strong> ${escapeHtml(r.receipt_number || '-')}</div>
                <div><strong>Amount:</strong> <span style="color:#27ae60; font-size:1.2rem; font-weight:bold;">${formatCurrency(r.amount)}</span></div>
                <div><strong>Traveler:</strong> ${escapeHtml(r.traveler_name || '-')}</div>
                <div><strong>Passport:</strong> ${escapeHtml(r.passport_no || '-')}</div>
                <div><strong>Date:</strong> ${r.receipt_date ? formatDate(r.receipt_date) : '-'}</div>
                <div><strong>Method:</strong> ${escapeHtml(r.payment_method || '-')}</div>
                <div><strong>Payment ID:</strong> ${r.payment_id || '-'}</div>
                <div><strong>Created:</strong> ${r.created_at ? formatDate(r.created_at, true) : '-'}</div>
            </div>
            ${r.notes ? `<div style="margin-top:15px;"><strong>Notes:</strong> ${escapeHtml(r.notes)}</div>` : ''}`;

        showModal(`Receipt: ${r.receipt_number || id}`, content,
            `<button class="action-btn btn-success" onclick="printReceipt(${r.id}); closeModal();">
                <i class="fas fa-print"></i> Print Receipt
            </button>`);
    } catch (error) {
        hideLoading();
        handleError(error, 'viewReceiptDetails');
    }
}

/**
 * Print a receipt
 * @param {number} id
 */
async function printReceipt(id) {
    try {
        // Use the backend print endpoint if available
        const printUrl = `/api/receipts/${id}/print`;
        const win = window.open(printUrl, '_blank');
        if (win) {
            win.onload = () => win.print();
        } else {
            // Fallback: fetch and print
            const data = await makeAPICall('GET', `/api/receipts/${id}`);
            if (!data.success) throw new Error(data.error || 'Receipt not found');
            const r = data.receipt;
            const printWin = window.open('', '_blank');
            printWin.document.write(`<html><head><title>Receipt ${r.receipt_number}</title>
                <style>body{font-family:Arial;padding:30px;max-width:600px;margin:0 auto;} .header{text-align:center;margin-bottom:30px;} table{width:100%;border-collapse:collapse;} td{padding:10px;border:1px solid #ddd;}</style>
                </head><body>
                <div class="header"><h2>Payment Receipt</h2><h3>${escapeHtml(r.receipt_number || '')}</h3></div>
                <table>
                    <tr><td><strong>Traveler</strong></td><td>${escapeHtml(r.traveler_name || '-')}</td></tr>
                    <tr><td><strong>Passport</strong></td><td>${escapeHtml(r.passport_no || '-')}</td></tr>
                    <tr><td><strong>Date</strong></td><td>${r.receipt_date ? formatDate(r.receipt_date) : '-'}</td></tr>
                    <tr><td><strong>Amount</strong></td><td>${formatCurrency(r.amount)}</td></tr>
                    <tr><td><strong>Method</strong></td><td>${escapeHtml(r.payment_method || '-')}</td></tr>
                </table>
                </body></html>`);
            printWin.document.close();
            printWin.print();
        }
    } catch (error) {
        handleError(error, 'printReceipt');
    }
}

/**
 * Export receipts to PDF (print dialog)
 */
function exportReceiptsToPDF() {
    if (!filteredReceipts.length) { showNotification('No receipts to export', 'warning'); return; }

    const printWin = window.open('', '_blank');
    const rows = filteredReceipts.map((r) => `
        <tr>
            <td>${escapeHtml(r.receipt_number || '-')}</td>
            <td>${escapeHtml(r.traveler_name || '-')}</td>
            <td>${r.receipt_date ? formatDate(r.receipt_date) : '-'}</td>
            <td>${formatCurrency(r.amount)}</td>
            <td>${escapeHtml(r.payment_method || '-')}</td>
        </tr>`).join('');

    printWin.document.write(`<html><head><title>Receipts Export</title>
        <style>body{font-family:Arial;padding:20px;} table{width:100%;border-collapse:collapse;} th{background:#2c3e50;color:white;padding:10px;} td{padding:10px;border:1px solid #ddd;}</style>
        </head><body>
        <h2>Receipts Report - ${new Date().toLocaleDateString()}</h2>
        <table><thead><tr><th>Receipt #</th><th>Traveler</th><th>Date</th><th>Amount</th><th>Method</th></tr></thead>
        <tbody>${rows}</tbody></table>
        </body></html>`);
    printWin.document.close();
    printWin.print();
}

// ── Pagination ───────────────────────────────────────────────

function updateReceiptPagination() {
    const total = filteredReceipts.length;
    const start = total > 0 ? (receiptsPage - 1) * RECEIPTS_PER_PAGE + 1 : 0;
    const end   = Math.min(receiptsPage * RECEIPTS_PER_PAGE, total);
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalCount',  total);
    setEl('showingFrom', start);
    setEl('showingTo',   end);
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    if (prevBtn) prevBtn.disabled = receiptsPage === 1;
    if (nextBtn) nextBtn.disabled = end >= total;
}

function prevReceiptPage() {
    if (receiptsPage > 1) { receiptsPage--; displayReceipts(); }
}

function nextReceiptPage() {
    if (receiptsPage * RECEIPTS_PER_PAGE < filteredReceipts.length) { receiptsPage++; displayReceipts(); }
}

// ── Stats ────────────────────────────────────────────────────

function updateReceiptStats() {
    const today = new Date().toISOString().slice(0, 10);
    const todayReceipts = allReceipts.filter((r) => r.receipt_date && r.receipt_date.slice(0, 10) === today);
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalReceipts',   allReceipts.length);
    setEl('todayReceipts',   todayReceipts.length);
    setEl('totalReceiptAmount', formatCurrency(allReceipts.reduce((s, r) => s + (parseFloat(r.amount) || 0), 0)));
    setEl('todayAmount',     formatCurrency(todayReceipts.reduce((s, r) => s + (parseFloat(r.amount) || 0), 0)));
}

// ── Modal Helpers ────────────────────────────────────────────

function closeReceiptModal() {
    const modal   = document.getElementById('editReceiptModal');
    const overlay = document.getElementById('modalOverlay');
    if (modal)   modal.style.display   = 'none';
    if (overlay) overlay.style.display = 'none';
}

// ── Form submit wiring ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('receiptCreateForm')?.addEventListener('submit', createReceipt);
    document.getElementById('editReceiptForm')?.addEventListener('submit', updateReceipt);
});

// Expose globals
window.loadReceipts         = loadReceipts;
window.filterReceipts       = filterReceipts;
window.showAddReceiptForm   = showAddReceiptForm;
window.hideAddReceiptForm   = hideAddReceiptForm;
window.editReceipt          = editReceipt;
window.deleteReceipt        = deleteReceipt;
window.viewReceiptDetails   = viewReceiptDetails;
window.printReceipt         = printReceipt;
window.exportReceiptsToPDF  = exportReceiptsToPDF;
window.closeReceiptModal    = closeReceiptModal;
window.prevReceiptPage      = prevReceiptPage;
window.nextReceiptPage      = nextReceiptPage;

console.log('✅ receipts.js loaded');
