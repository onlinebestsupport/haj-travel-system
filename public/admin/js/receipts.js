/**
 * receipts.js - Receipt management functions
 * Alhudha Haj Travel Management System
 * receipts.js - Receipt Management for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 * API base: /api/receipts
 */

'use strict';

// Module-level state
let receiptsData = [];
let filteredReceiptsData = [];

// ====== LOAD RECEIPTS ======
/**
 * Fetch all receipts from the API and render them
 */
async function loadReceipts() {
    showLoading(true);
    try {
        const data = await makeApiCall('GET', '/api/receipts');
        receiptsData = Array.isArray(data) ? data : (data.receipts || []);
        filteredReceiptsData = [...receiptsData];
        displayReceipts(filteredReceiptsData);
        console.log(`✅ Loaded ${receiptsData.length} receipts`);
    } catch (error) {
        handleApiError(error, 'Load receipts');
    } finally {
        showLoading(false);
    }
}

// ====== DISPLAY RECEIPTS ======
/**
 * Render receipts array into the table
 * @param {Array} receipts
 */
function displayReceipts(receipts) {
    const tbody = document.getElementById('receiptsTableBody');
    if (!tbody) return;

    if (!receipts || receipts.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align:center;padding:40px;color:#95a5a6;">
                    <i class="fas fa-receipt" style="font-size:2rem;display:block;margin-bottom:10px;"></i>
                    No receipts found
                </td>
            </tr>`;
        updateReceiptsCount(0);
        return;
    }

    tbody.innerHTML = receipts.map(r => {
        const receiptNo    = r.receipt_number || `REC-${String(r.id).padStart(6, '0')}`;
        const travelerName = r.traveler_name ||
            `${r.first_name || ''} ${r.last_name || ''}`.trim() || `ID ${r.traveler_id}`;
        return `
            <tr>
                <td>${escapeHtml(receiptNo)}</td>
                <td>${formatDate(r.receipt_date || r.created_at)}</td>
                <td>${escapeHtml(travelerName)}</td>
                <td>${formatCurrency(r.amount)}</td>
                <td>${escapeHtml(r.payment_method || '-')}</td>
                <td>${escapeHtml(r.transaction_id || '-')}</td>
                <td>
                    <button class="icon-btn btn-view" onclick="viewReceiptDetails(${r.id})" title="View">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="icon-btn btn-edit" onclick="editReceipt(${r.id})" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="icon-btn" onclick="printReceiptById(${r.id})" title="Print" style="color:#27ae60;">
                        <i class="fas fa-print"></i>
                    </button>
                    <button class="icon-btn btn-delete" onclick="deleteReceipt(${r.id})" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>`;
    }).join('');

    updateReceiptsCount(receipts.length);
}

/**
 * Update the receipt count display element
 * @param {number} count
 */
function updateReceiptsCount(count) {
    const el = document.getElementById('receiptsCount');
    if (el) el.textContent = count;
}

// ====== FILTER RECEIPTS ======
/**
 * Filter receipts by receipt number, traveler, or date
 */
function filterReceipts() {
    const searchEl = document.getElementById('searchReceipts') || document.getElementById('receiptSearch');
    const dateEl   = document.getElementById('filterReceiptDate');
    const search   = searchEl ? searchEl.value.toLowerCase().trim() : '';
    const date     = dateEl   ? dateEl.value : '';

    filteredReceiptsData = receiptsData.filter(r => {
        const receiptNo    = (r.receipt_number || '').toLowerCase();
        const travelerName = (r.traveler_name || `${r.first_name || ''} ${r.last_name || ''}`).toLowerCase();
        const txId         = (r.transaction_id || '').toLowerCase();
        const rDate        = r.receipt_date || r.created_at || '';

        const matchesSearch = !search ||
            receiptNo.includes(search) ||
            travelerName.includes(search) ||
            txId.includes(search);

        const matchesDate = !date || rDate.startsWith(date);

        return matchesSearch && matchesDate;
    });

    displayReceipts(filteredReceiptsData);
}

// ====== CREATE RECEIPT ======
/**
 * Submit a new receipt form to the API
 */
async function createReceipt() {
    const form = document.getElementById('receiptForm') || document.getElementById('receiptCreateForm');
    if (!form) { showNotification('Receipt form not found', 'error'); return; }

    const formData = new FormData(form);
    const receiptData = {};
    formData.forEach((value, key) => { if (value !== '') receiptData[key] = value; });

    if (!receiptData.traveler_id) {
        showNotification('Please select a traveler', 'error');
        return;
    }
    if (!receiptData.amount || parseFloat(receiptData.amount) <= 0) {
        showNotification('Please enter a valid amount', 'error');
        return;
    }

    showLoading(true);
    try {
        const result = await makeApiCall('POST', '/api/receipts', receiptData);
        if (result.success || result.id) {
            showNotification('Receipt created successfully!', 'success');
            form.reset();
            const container = document.getElementById('createReceiptForm') || document.getElementById('receiptFormContainer');
            if (container) container.style.display = 'none';
            await loadReceipts();
        } else {
            showNotification(result.error || 'Failed to create receipt', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Create receipt');
    } finally {
        showLoading(false);
    }
}

// ====== EDIT RECEIPT ======
/**
 * Load receipt data into the edit form
 * @param {number} receiptId
 */
async function editReceipt(receiptId) {
    showLoading(true);
    try {
        const response = await makeApiCall('GET', `/api/receipts/${receiptId}`);
        const r = response.receipt || response;

        const fields = [
            'traveler_id','payment_id','receipt_number','receipt_date',
            'amount','payment_method','transaction_id','notes'
        ];

        fields.forEach(field => {
            const el = document.getElementById(`edit_${field}`) || document.getElementById(field);
            if (el && r[field] !== undefined) el.value = r[field];
        });

        const idField = document.getElementById('edit_receipt_id') || document.getElementById('editReceiptId');
        if (idField) idField.value = receiptId;

        const editForm = document.getElementById('editReceiptForm') || document.getElementById('editReceiptContainer');
        if (editForm) {
            editForm.style.display = 'block';
            editForm.scrollIntoView({ behavior: 'smooth' });
        }
    } catch (error) {
        handleApiError(error, 'Load receipt for editing');
    } finally {
        showLoading(false);
    }
}

// ====== UPDATE RECEIPT ======
/**
 * Save changes to an existing receipt
 */
async function updateReceipt() {
    const idField = document.getElementById('edit_receipt_id') || document.getElementById('editReceiptId');
    if (!idField || !idField.value) {
        showNotification('No receipt selected for update', 'error');
        return;
    }

    const receiptId = idField.value;
    const form = document.getElementById('editReceiptForm') || document.getElementById('editReceiptContainer');
    if (!form) { showNotification('Edit form not found', 'error'); return; }

    const formData = new FormData(form.querySelector('form') || form);
    const receiptData = {};
    formData.forEach((value, key) => { if (key !== 'id') receiptData[key] = value; });

    showLoading(true);
    try {
        const result = await makeApiCall('PUT', `/api/receipts/${receiptId}`, receiptData);
        if (result.success || result.id) {
            showNotification('Receipt updated successfully!', 'success');
            if (form) form.style.display = 'none';
            await loadReceipts();
        } else {
            showNotification(result.error || 'Failed to update receipt', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Update receipt');
    } finally {
        showLoading(false);
    }
}

// ====== DELETE RECEIPT ======
/**
 * Delete a receipt after confirmation
 * @param {number} receiptId
 */
function deleteReceipt(receiptId) {
    const receipt = receiptsData.find(r => r.id === receiptId);
    const label   = receipt ? (receipt.receipt_number || `REC-${String(receipt.id).padStart(6,'0')}`) : `ID ${receiptId}`;

    showConfirmation(
        `Are you sure you want to delete receipt "${label}"? This action cannot be undone.`,
        async () => {
            showLoading(true);
            try {
                const result = await makeApiCall('DELETE', `/api/receipts/${receiptId}`);
                if (result.success || result.message) {
                    showNotification('Receipt deleted successfully!', 'success');
                    await loadReceipts();
                } else {
                    showNotification(result.error || 'Failed to delete receipt', 'error');
                }
            } catch (error) {
                handleApiError(error, 'Delete receipt');
            } finally {
                showLoading(false);
            }
        }
    );
}

// ====== VIEW RECEIPT DETAILS ======
/**
 * Show a modal with full receipt details
 * @param {number} receiptId
 */
async function viewReceiptDetails(receiptId) {
    showLoading(true);
    try {
        const response = await makeApiCall('GET', `/api/receipts/${receiptId}`);
        const r = response.receipt || response;

        const receiptNo    = r.receipt_number || `REC-${String(r.id).padStart(6, '0')}`;
        const travelerName = r.traveler_name ||
            `${r.first_name || ''} ${r.last_name || ''}`.trim() || `ID ${r.traveler_id}`;

        const content = `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;">
                <div><strong>Receipt #:</strong><br>${escapeHtml(receiptNo)}</div>
                <div><strong>Date:</strong><br>${formatDate(r.receipt_date || r.created_at)}</div>
                <div><strong>Traveler:</strong><br>${escapeHtml(travelerName)}</div>
                <div><strong>Amount:</strong><br>${formatCurrency(r.amount)}</div>
                <div><strong>Payment Method:</strong><br>${escapeHtml(r.payment_method || '-')}</div>
                <div><strong>Transaction ID:</strong><br>${escapeHtml(r.transaction_id || '-')}</div>
                <div style="grid-column:1/-1;"><strong>Notes:</strong><br>${escapeHtml(r.notes || '-')}</div>
            </div>`;

        showModal(`<i class="fas fa-receipt" style="color:#3498db;margin-right:8px;"></i>Receipt Details — ${escapeHtml(receiptNo)}`, content, [
            { label: '<i class="fas fa-print"></i> Print', class: 'btn-success', onClick: `closeModal(); printReceiptById(${receiptId});` },
            { label: '<i class="fas fa-edit"></i> Edit', class: 'btn-primary', onClick: `closeModal(); editReceipt(${receiptId});` },
            { label: '<i class="fas fa-times"></i> Close', class: 'btn-secondary', onClick: 'closeModal()' }
        ]);
    } catch (error) {
        handleApiError(error, 'Load receipt details');
    } finally {
        showLoading(false);
    }
}

// ====== EXPORT RECEIPTS TO PDF ======
/**
 * Export all receipts to a printable PDF page
 */
async function exportReceiptsToPDF() {
    const data = filteredReceiptsData.length > 0 ? filteredReceiptsData : receiptsData;
    if (!data || data.length === 0) {
        showNotification('No receipts to export', 'warning');
        return;
    }

    const rows = data.map(r => {
        const receiptNo    = r.receipt_number || `REC-${String(r.id).padStart(6, '0')}`;
        const travelerName = r.traveler_name || `${r.first_name || ''} ${r.last_name || ''}`.trim();
        return `
            <tr>
                <td>${escapeHtml(receiptNo)}</td>
                <td>${formatDate(r.receipt_date || r.created_at)}</td>
                <td>${escapeHtml(travelerName)}</td>
                <td>${formatCurrency(r.amount)}</td>
                <td>${escapeHtml(r.payment_method || '-')}</td>
                <td>${escapeHtml(r.transaction_id || '-')}</td>
            </tr>`;
    }).join('');

    const html = `
        <!DOCTYPE html><html><head>
        <title>Receipts Export</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            h1 { color: #2c3e50; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th { background: #2c3e50; color: white; padding: 10px; text-align: left; }
            td { padding: 8px 10px; border-bottom: 1px solid #ecf0f1; }
            tr:nth-child(even) { background: #f8f9fa; }
            .footer { margin-top: 20px; color: #95a5a6; font-size: 0.85rem; }
        </style></head><body>
        <h1>&#x1F54B; Alhudha Haj Travel — Receipts</h1>
        <p>Generated: ${new Date().toLocaleString('en-IN')} | Total: ${data.length} receipts</p>
        <table>
            <thead><tr>
                <th>Receipt #</th><th>Date</th><th>Traveler</th>
                <th>Amount</th><th>Method</th><th>Transaction ID</th>
            </tr></thead>
            <tbody>${rows}</tbody>
        </table>
        <div class="footer">This is a computer-generated report.</div>
        </body></html>`;

    const blob = new Blob([html], { type: 'text/html' });
    const url  = URL.createObjectURL(blob);
    const win  = window.open(url, '_blank');
    if (win) win.onload = () => win.print();

    showNotification(`Exporting ${data.length} receipts to PDF`, 'success');
}

// ====== PRINT RECEIPT BY ID ======
/**
 * Print a single receipt
 * @param {number} receiptId
 */
async function printReceiptById(receiptId) {
    showLoading(true);
    try {
        const response = await makeApiCall('GET', `/api/receipts/${receiptId}`);
        const r = response.receipt || response;

        const receiptNo    = r.receipt_number || `REC-${String(r.id).padStart(6, '0')}`;
        const travelerName = r.traveler_name ||
            `${r.first_name || ''} ${r.last_name || ''}`.trim() || `ID ${r.traveler_id}`;

        const html = `
            <!DOCTYPE html><html><head>
            <title>Receipt ${receiptNo}</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 500px; margin: 40px auto; padding: 20px; }
                .header { text-align: center; border-bottom: 2px solid #2c3e50; padding-bottom: 15px; margin-bottom: 20px; }
                .row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #ecf0f1; }
                .amount { font-size: 1.5rem; font-weight: bold; color: #27ae60; text-align: center; margin: 20px 0; }
                .footer { text-align: center; color: #95a5a6; font-size: 0.8rem; margin-top: 20px; }
            </style></head><body>
            <div class="header">
                <h2>&#x1F54B; Alhudha Haj Travel</h2>
                <div>Receipt: <strong>${escapeHtml(receiptNo)}</strong></div>
            </div>
            <div class="row"><span>Traveler:</span><span>${escapeHtml(travelerName)}</span></div>
            <div class="row"><span>Date:</span><span>${formatDate(r.receipt_date || r.created_at)}</span></div>
            <div class="row"><span>Method:</span><span>${escapeHtml(r.payment_method || '-')}</span></div>
            <div class="row"><span>Transaction ID:</span><span>${escapeHtml(r.transaction_id || '-')}</span></div>
            <div class="amount">${formatCurrency(r.amount)}</div>
            <div class="footer">Generated: ${new Date().toLocaleString('en-IN')}</div>
            </body></html>`;

        const blob = new Blob([html], { type: 'text/html' });
        const url  = URL.createObjectURL(blob);
        const win  = window.open(url, '_blank');
        if (win) win.onload = () => win.print();
    } catch (error) {
        handleApiError(error, 'Print receipt');
    } finally {
        showLoading(false);
    }
}
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
