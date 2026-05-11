/**
 * receipts.js - Receipt management functions
 * Alhudha Haj Travel Admin Panel
 * Alhudha Haj Travel Management System
 * receipts.js - Receipt Management for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 * API base: /api/receipts
 */

'use strict';

// ====== STATE ======
let receiptsData = [];
let receiptsFiltered = [];
let receiptsCurrentPage = 1;
const receiptsPerPage = 10;
let receiptsCurrentEditId = null;

// ====== LOAD RECEIPTS ======
/**
 * Fetch all receipts from /api/receipts
 */
async function loadReceipts() {
    const container = document.getElementById('receiptsListContainer');
    if (container) {
        container.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading receipts...</div>';
    }

    try {
        const data = await makeAPICall('GET', '/api/receipts');
        if (data.success && Array.isArray(data.receipts)) {
            receiptsData = data.receipts;
            receiptsFiltered = [...receiptsData];
            console.log(`✅ Loaded ${receiptsData.length} receipts`);
        } else {
            receiptsData = [];
            receiptsFiltered = [];
        }
    } catch (error) {
        handleAPIError(error, 'loadReceipts');
        receiptsData = [];
        receiptsFiltered = [];
    }

    displayReceipts();
    updateReceiptStats();
}

// ====== DISPLAY RECEIPTS ======
/**
 * Render the receipts list with pagination
 */
function displayReceipts() {
    const container = document.getElementById('receiptsListContainer');
    if (!container) return;

    if (!receiptsFiltered || receiptsFiltered.length === 0) {
        container.innerHTML = '<div style="text-align:center;padding:40px;">No receipts found</div>';
        updatePaginationDisplay(0, 1, receiptsPerPage);
        return;
    }

    const start = (receiptsCurrentPage - 1) * receiptsPerPage;
    const end = start + receiptsPerPage;
    const pageData = receiptsFiltered.slice(start, end);

    let html = '';
    pageData.forEach(r => {
        const travelerName = r.traveler_name || (r.first_name ? `${r.first_name} ${r.last_name || ''}`.trim() : '-');
        const receiptNum = r.receipt_number || `RCP-${String(r.id).padStart(4, '0')}`;

        html += `<div class="receipt-card">
            <div class="receipt-header">
                <div>
                    <div class="receipt-number">${escapeHtml(receiptNum)}</div>
                    <div style="color:#7f8c8d;font-size:0.9rem;">${formatDate(r.created_at || r.payment_date)}</div>
                </div>
                <div class="receipt-amount">${formatCurrency(r.amount)}</div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:10px 0;">
                <div><strong>Traveler:</strong><br>${escapeHtml(travelerName)}</div>
                <div><strong>Method:</strong><br>${escapeHtml(r.payment_method || '-')}</div>
                <div><strong>Passport:</strong><br>${escapeHtml(r.passport_no || '-')}</div>
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
                <button class="action-btn btn-danger" style="padding:8px 15px;" onclick="deleteReceipt(${r.id})"><i class="fas fa-trash"></i> Delete</button>
            </div>
        </div>`;
    });

    container.innerHTML = html;
    updatePaginationDisplay(receiptsFiltered.length, receiptsCurrentPage, receiptsPerPage);
}

// ====== FILTER RECEIPTS ======
/**
 * Filter receipts by number, traveler, or date range
 */
function filterReceipts() {
    const search = (document.getElementById('searchReceipt')?.value || '').toLowerCase().trim();
    const fromDate = document.getElementById('fromDate')?.value;
    const toDate = document.getElementById('toDate')?.value;

    receiptsFiltered = receiptsData.filter(r => {
        const travelerName = `${r.first_name || ''} ${r.last_name || ''} ${r.traveler_name || ''}`.toLowerCase();
        const receiptNum = (r.receipt_number || String(r.id)).toLowerCase();
        const passport = (r.passport_no || '').toLowerCase();
        const matchesSearch = !search || travelerName.includes(search) || receiptNum.includes(search) || passport.includes(search);

        let matchesDate = true;
        if (fromDate || toDate) {
            const rDate = new Date(r.created_at || r.payment_date);
            if (fromDate && rDate < new Date(fromDate)) matchesDate = false;
            if (toDate && rDate > new Date(toDate + 'T23:59:59')) matchesDate = false;
        }

        return matchesSearch && matchesDate;
    });

    receiptsCurrentPage = 1;
    displayReceipts();
    showNotification(`Found ${receiptsFiltered.length} receipt(s)`, 'info');
}

// ====== CREATE RECEIPT ======
/**
 * POST a new receipt
 */
async function createReceipt() {
    const travelerId = document.getElementById('receiptTravelerSelect')?.value;
    if (!travelerId) { showNotification('Please select a traveler', 'error'); return; }

    const amount = parseFloat(document.getElementById('receiptAmount')?.value || 0);
    if (!amount || amount <= 0) { showNotification('Please enter a valid amount', 'error'); return; }

    const paymentDate = document.getElementById('receiptDate')?.value;
    if (!paymentDate) { showNotification('Payment date is required', 'error'); return; }

    const receiptData = {
        traveler_id: travelerId,
        amount: amount,
        payment_date: paymentDate,
        payment_method: document.getElementById('receiptPaymentMethod')?.value,
        transaction_id: document.getElementById('receiptTransactionId')?.value?.trim(),
        remarks: document.getElementById('receiptRemarks')?.value?.trim()
    };

    const submitBtn = document.querySelector('#receiptCreateForm button[type="submit"]');
    showLoading(submitBtn, 'Generating...');
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
            showNotification('Receipt generated successfully!', 'success');
            if (typeof toggleCreateReceiptForm === 'function') toggleCreateReceiptForm();
            await loadReceipts();
        } else {
            showNotification('Error: ' + (data.error || 'Could not create receipt'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'createReceipt');
    } finally {
        hideLoading(submitBtn);
    }
}

// Alias for inline HTML
function generateReceipt() { createReceipt(); }

// ====== EDIT RECEIPT ======
/**
 * Load receipt data for editing
 * @param {number} id
 */
function editReceipt(id) {
    const receipt = receiptsData.find(r => r.id === id);
    if (!receipt) { showNotification('Receipt not found', 'error'); return; }

    receiptsCurrentEditId = id;
    showNotification(`Editing receipt #${id}`, 'info');
    viewReceiptDetails(id);
}

// ====== UPDATE RECEIPT ======
/**
 * PUT updated receipt data
 */
async function updateReceipt() {
    if (!receiptsCurrentEditId) {
        showNotification('No receipt selected for editing', 'error'); return;
    }

    const receiptData = {
        amount: parseFloat(document.getElementById('edit_receipt_amount')?.value || 0),
        payment_method: document.getElementById('edit_receipt_method')?.value,
        remarks: document.getElementById('edit_receipt_remarks')?.value?.trim()
    };

    try {
        const data = await makeAPICall('PUT', `/api/receipts/${receiptsCurrentEditId}`, receiptData);
        if (data.success) {
            showNotification('Receipt updated successfully!', 'success');
            receiptsCurrentEditId = null;
            closeModal();
            await loadReceipts();
        } else {
            showNotification('Error: ' + (data.error || 'Update failed'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'updateReceipt');
    }
}

// ====== DELETE RECEIPT ======
/**
 * DELETE a receipt by ID
 * @param {number} id
 */
async function deleteReceipt(id) {
    if (!confirm('Are you sure you want to delete this receipt?')) return;
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
            showNotification('Error: ' + (data.error || 'Could not delete receipt'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'deleteReceipt');
    }
}

// ====== VIEW RECEIPT DETAILS ======
/**
 * Show a modal with full receipt details
 * @param {number} id
 */
function viewReceiptDetails(id) {
    const r = receiptsData.find(r => r.id === id);
    if (!r) { showNotification('Receipt not found', 'error'); return; }

    const travelerName = r.traveler_name || (r.first_name ? `${r.first_name} ${r.last_name || ''}`.trim() : '-');
    const receiptNum = r.receipt_number || `RCP-${String(r.id).padStart(4, '0')}`;

    const detailsHtml = `
        <div style="text-align:center;padding:20px;background:linear-gradient(135deg,#2c3e50,#34495e);color:white;border-radius:10px;margin-bottom:20px;">
            <h2 style="margin:0;">Alhudha Haj Travel</h2>
            <p style="margin:5px 0;opacity:0.8;">Payment Receipt</p>
            <h3 style="margin:10px 0;color:#f1c40f;">${escapeHtml(receiptNum)}</h3>
        </div>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:15px;">
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Traveler:</strong><br>${escapeHtml(travelerName)}
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Passport:</strong><br>${escapeHtml(r.passport_no || '-')}
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Date:</strong><br>${formatDate(r.created_at || r.payment_date)}
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Method:</strong><br>${escapeHtml(r.payment_method || '-')}
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Transaction ID:</strong><br>${escapeHtml(r.transaction_id || '-')}
            </div>
            <div style="background:#d4edda;padding:12px;border-radius:5px;">
                <strong>Amount:</strong><br><span style="font-size:1.3rem;font-weight:bold;color:#27ae60;">${formatCurrency(r.amount)}</span>
            </div>
        </div>
        ${r.remarks ? `<div style="margin-top:15px;padding:12px;background:#fff3cd;border-radius:5px;"><strong>Remarks:</strong><br>${escapeHtml(r.remarks)}</div>` : ''}
    `;

    const existingModal = document.getElementById('receiptModal');
    const existingDetails = document.getElementById('receiptDetails');

    if (existingModal && existingDetails) {
        existingDetails.innerHTML = detailsHtml;
        existingModal.style.display = 'flex';
    } else {
        showModal(`<i class="fas fa-receipt"></i> Receipt ${receiptNum}`, detailsHtml,
            `<button class="action-btn btn-primary" onclick="printReceipt(${id})"><i class="fas fa-print"></i> Print</button>
             <button class="action-btn btn-secondary" onclick="closeModal()">Close</button>`);
    }
}

// ====== PRINT RECEIPT ======
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
function printReceipt(id) {
    const r = receiptsData.find(r => r.id === id);
    if (!r) { showNotification('Receipt not found', 'error'); return; }

    const travelerName = r.traveler_name || (r.first_name ? `${r.first_name} ${r.last_name || ''}`.trim() : '-');
    const receiptNum = r.receipt_number || `RCP-${String(r.id).padStart(4, '0')}`;

    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html><head><title>Receipt ${receiptNum}</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 30px; max-width: 600px; margin: 0 auto; }
            .header { text-align: center; background: #2c3e50; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            .row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
            .amount { font-size: 1.5rem; font-weight: bold; color: #27ae60; text-align: center; margin-top: 20px; }
        </style></head>
        <body>
            <div class="header">
                <h2>Alhudha Haj Travel</h2>
                <p>Payment Receipt - ${escapeHtml(receiptNum)}</p>
            </div>
            <div class="row"><span>Traveler:</span><strong>${escapeHtml(travelerName)}</strong></div>
            <div class="row"><span>Date:</span><strong>${formatDate(r.created_at || r.payment_date)}</strong></div>
            <div class="row"><span>Method:</span><strong>${escapeHtml(r.payment_method || '-')}</strong></div>
            <div class="row"><span>Transaction ID:</span><strong>${escapeHtml(r.transaction_id || '-')}</strong></div>
            <div class="amount">${formatCurrency(r.amount)}</div>
            <p style="text-align:center;color:#7f8c8d;margin-top:20px;">Thank you for your payment</p>
        </body></html>`);
    printWindow.document.close();
    printWindow.print();
}

// ====== EXPORT TO PDF ======
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
    if (!receiptsData.length) { showNotification('No receipts to export', 'warning'); return; }
    showNotification('Opening print dialog for PDF export...', 'info');
    window.print();
}

// ====== STATS ======
function updateReceiptStats() {
    const total = receiptsData.length;
    const totalAmount = receiptsData.reduce((s, r) => s + (r.amount || 0), 0);

    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalReceipts', total);
    setEl('totalReceiptAmount', formatCurrency(totalAmount));
}

// ====== PAGINATION ======
function receiptsPreviousPage() {
    if (receiptsCurrentPage > 1) { receiptsCurrentPage--; displayReceipts(); }
}
function receiptsNextPage() {
    if (receiptsCurrentPage * receiptsPerPage < receiptsFiltered.length) { receiptsCurrentPage++; displayReceipts(); }
}

function previousPage() { receiptsPreviousPage(); }
function nextPage() { receiptsNextPage(); }

function applyFilters() { filterReceipts(); }
function resetFilters() {
    const searchEl = document.getElementById('searchReceipt');
    const fromEl = document.getElementById('fromDate');
    const toEl = document.getElementById('toDate');
    if (searchEl) searchEl.value = '';
    if (fromEl) fromEl.value = '';
    if (toEl) toEl.value = '';
    receiptsFiltered = [...receiptsData];
    receiptsCurrentPage = 1;
    displayReceipts();
    showNotification('Filters reset', 'info');
}

function exportReceipts() { exportReceiptsToPDF(); }
function closeModal() {
    const modal = document.getElementById('receiptModal');
    if (modal) modal.style.display = 'none';
}

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
