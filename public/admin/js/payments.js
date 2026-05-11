/**
 * payments.js - Payment management functions
 * Alhudha Haj Travel Admin Panel
 * Alhudha Haj Travel Management System
 * payments.js - Payment Management for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 * API base: /api/payments
 */

'use strict';

// ====== STATE ======
let paymentsData = [];
let paymentsFiltered = [];
let paymentsCurrentPage = 1;
const paymentsPerPage = 10;
let paymentsCurrentId = null;
let paymentsTravelerData = null;
let paymentsBatchesData = [];
let paymentsTravelersData = [];

// ====== LOAD PAYMENTS ======
/**
 * Fetch all payments from /api/payments
 */
async function loadPayments() {
    const tableBody = document.getElementById('paymentsTableBody');
    if (tableBody) {
        tableBody.innerHTML = '<tr><td colspan="11" class="loading"><i class="fas fa-spinner fa-spin"></i> Loading payments...</td></tr>';
    }

    try {
        const data = await makeAPICall('GET', '/api/payments');
        if (data.success && Array.isArray(data.payments)) {
            paymentsData = data.payments;
            paymentsFiltered = [...paymentsData];
            console.log(`✅ Loaded ${paymentsData.length} payments`);
        } else {
            paymentsData = [];
            paymentsFiltered = [];
        }
    } catch (error) {
        handleAPIError(error, 'loadPayments');
        paymentsData = [];
        paymentsFiltered = [];
    }

    displayPayments();
    updatePaymentStats();
}

// ====== DISPLAY PAYMENTS ======
/**
 * Render the payments table with amount formatting
 */
function displayPayments() {
    const tableBody = document.getElementById('paymentsTableBody');
    if (!tableBody) return;

    if (!paymentsFiltered || paymentsFiltered.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="11" style="text-align:center;padding:40px;">No payments found</td></tr>';
        updatePaginationDisplay(0, 1, paymentsPerPage);
        return;
    }

    const start = (paymentsCurrentPage - 1) * paymentsPerPage;
    const end = start + paymentsPerPage;
    const pageData = paymentsFiltered.slice(start, end);

    let html = '';
    pageData.forEach(p => {
        const travelerName = p.first_name ? `${p.first_name} ${p.last_name || ''}`.trim() : (p.traveler_name || '-');
        const amount = formatCurrency(p.amount);
        const statusText = p.status === 'completed' ? 'Paid' : (p.status || 'Pending');
        const statusClass = getStatusClass(p.status === 'completed' ? 'paid' : p.status);

        html += `<tr>
// Module-level state
let paymentsData = [];
let filteredPaymentsData = [];

// ====== LOAD PAYMENTS ======
/**
 * Fetch all payments from the API and render them
 */
async function loadPayments() {
    showLoading(true);
    try {
        const data = await makeApiCall('GET', '/api/payments');
        paymentsData = Array.isArray(data) ? data : (data.payments || []);
        filteredPaymentsData = [...paymentsData];
        displayPayments(filteredPaymentsData);
        console.log(`✅ Loaded ${paymentsData.length} payments`);
    } catch (error) {
        handleApiError(error, 'Load payments');
    } finally {
        showLoading(false);
    }
}

// ====== DISPLAY PAYMENTS ======
/**
 * Render payments array into the table
 * @param {Array} payments
 */
function displayPayments(payments) {
    const tbody = document.getElementById('paymentsTableBody');
    if (!tbody) return;

    if (!payments || payments.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" style="text-align:center;padding:40px;color:#95a5a6;">
                    <i class="fas fa-credit-card" style="font-size:2rem;display:block;margin-bottom:10px;"></i>
                    No payments found
                </td>
            </tr>`;
        updatePaymentsCount(0);
        return;
    }

    tbody.innerHTML = payments.map(p => {
        const status = p.payment_status || p.status || 'Pending';
        const statusClass = status.toLowerCase() === 'paid'      ? 'status-active' :
                            status.toLowerCase() === 'pending'   ? 'status-pending' :
                            status.toLowerCase() === 'failed'    ? 'status-inactive' : 'status-pending';
        const travelerName = p.traveler_name ||
            `${p.first_name || ''} ${p.last_name || ''}`.trim() || `ID ${p.traveler_id}`;
        return `
            <tr>
                <td>${escapeHtml(String(p.id || ''))}</td>
                <td>${escapeHtml(travelerName)}</td>
                <td>${escapeHtml(p.batch_name || p.batch_id || '-')}</td>
                <td>${formatCurrency(p.amount)}</td>
                <td>${escapeHtml(p.payment_method || p.method || '-')}</td>
                <td>${formatDate(p.payment_date || p.date)}</td>
                <td>${escapeHtml(p.transaction_id || '-')}</td>
                <td><span class="status-badge ${statusClass}">${escapeHtml(status)}</span></td>
                <td>
                    <button class="icon-btn btn-view" onclick="viewPaymentDetails(${p.id})" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="icon-btn btn-edit" onclick="editPayment(${p.id})" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="icon-btn" onclick="generateReceipt(${p.id})" title="Generate Receipt" style="color:#27ae60;">
                        <i class="fas fa-receipt"></i>
                    </button>
                    <button class="icon-btn btn-delete" onclick="deletePayment(${p.id})" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>`;
    }).join('');

    updatePaymentsCount(payments.length);
    updatePaymentsTotals(payments);
}

/**
 * Update the payment count display element
 * @param {number} count
 */
function updatePaymentsCount(count) {
    const el = document.getElementById('paymentsCount');
    if (el) el.textContent = count;
}

/**
 * Update payment summary totals in stat cards
 * @param {Array} payments
 */
function updatePaymentsTotals(payments) {
    const total = payments.reduce((sum, p) => sum + parseFloat(p.amount || 0), 0);
    const paid  = payments.filter(p => (p.payment_status || p.status || '').toLowerCase() === 'paid')
                          .reduce((sum, p) => sum + parseFloat(p.amount || 0), 0);

    const totalEl = document.getElementById('totalPaymentsAmount');
    const paidEl  = document.getElementById('paidPaymentsAmount');
    if (totalEl) totalEl.textContent = formatCurrency(total);
    if (paidEl)  paidEl.textContent  = formatCurrency(paid);
}

// ====== FILTER PAYMENTS ======
/**
 * Filter payments by traveler, amount, date, or status
 */
function filterPayments() {
    const searchEl = document.getElementById('searchPayments');
    const statusEl = document.getElementById('filterPaymentStatus');
    const dateEl   = document.getElementById('filterPaymentDate');
    const search   = searchEl ? searchEl.value.toLowerCase().trim() : '';
    const status   = statusEl ? statusEl.value.toLowerCase() : '';
    const date     = dateEl   ? dateEl.value : '';

    filteredPaymentsData = paymentsData.filter(p => {
        const travelerName = (p.traveler_name || `${p.first_name || ''} ${p.last_name || ''}`).toLowerCase();
        const txId         = (p.transaction_id || '').toLowerCase();
        const pStatus      = (p.payment_status || p.status || '').toLowerCase();
        const pDate        = p.payment_date || p.date || '';

        const matchesSearch = !search ||
            travelerName.includes(search) ||
            txId.includes(search) ||
            String(p.amount || '').includes(search);

        const matchesStatus = !status || pStatus === status;
        const matchesDate   = !date   || pDate.startsWith(date);

        return matchesSearch && matchesStatus && matchesDate;
    });

    displayPayments(filteredPaymentsData);
}

// ====== RECORD PAYMENT ======
/**
 * Submit a new payment form to the API
 */
async function recordPayment() {
    const form = document.getElementById('paymentForm') || document.getElementById('addPaymentForm');
    if (!form) { showNotification('Payment form not found', 'error'); return; }

    const formData = new FormData(form);
    const paymentData = {};
    formData.forEach((value, key) => { if (value !== '') paymentData[key] = value; });

    if (!paymentData.traveler_id) {
        showNotification('Please select a traveler', 'error');
        return;
    }
    if (!paymentData.amount || parseFloat(paymentData.amount) <= 0) {
        showNotification('Please enter a valid amount', 'error');
        return;
    }

    showLoading(true);
    try {
        const result = await makeApiCall('POST', '/api/payments', paymentData);
        if (result.success || result.id) {
            showNotification('Payment recorded successfully!', 'success');
            form.reset();
            const container = document.getElementById('addPaymentForm') || document.getElementById('paymentFormContainer');
            if (container) container.style.display = 'none';
            await loadPayments();
        } else {
            showNotification(result.error || 'Failed to record payment', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Record payment');
    } finally {
        showLoading(false);
    }
}

// ====== EDIT PAYMENT ======
/**
 * Load payment data into the edit form
 * @param {number} paymentId
 */
async function editPayment(paymentId) {
    showLoading(true);
    try {
        const response = await makeApiCall('GET', `/api/payments/${paymentId}`);
        const p = response.payment || response;

        const fields = [
            'traveler_id','batch_id','amount','payment_method',
            'payment_date','transaction_id','payment_status','notes'
        ];

        fields.forEach(field => {
            const el = document.getElementById(`edit_${field}`) || document.getElementById(field);
            if (el && p[field] !== undefined) el.value = p[field];
        });

        const idField = document.getElementById('edit_payment_id') || document.getElementById('editPaymentId');
        if (idField) idField.value = paymentId;

        const editForm = document.getElementById('editPaymentForm') || document.getElementById('editPaymentContainer');
        if (editForm) {
            editForm.style.display = 'block';
            editForm.scrollIntoView({ behavior: 'smooth' });
        }
    } catch (error) {
        handleApiError(error, 'Load payment for editing');
    } finally {
        showLoading(false);
    }
}

// ====== UPDATE PAYMENT ======
/**
 * Save changes to an existing payment
 */
async function updatePayment() {
    const idField = document.getElementById('edit_payment_id') || document.getElementById('editPaymentId');
    if (!idField || !idField.value) {
        showNotification('No payment selected for update', 'error');
        return;
    }

    const paymentId = idField.value;
    const form = document.getElementById('editPaymentForm') || document.getElementById('editPaymentContainer');
    if (!form) { showNotification('Edit form not found', 'error'); return; }

    const formData = new FormData(form.querySelector('form') || form);
    const paymentData = {};
    formData.forEach((value, key) => { if (key !== 'id') paymentData[key] = value; });

    showLoading(true);
    try {
        const result = await makeApiCall('PUT', `/api/payments/${paymentId}`, paymentData);
        if (result.success || result.id) {
            showNotification('Payment updated successfully!', 'success');
            if (form) form.style.display = 'none';
            await loadPayments();
        } else {
            showNotification(result.error || 'Failed to update payment', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Update payment');
    } finally {
        showLoading(false);
    }
}

// ====== DELETE PAYMENT ======
/**
 * Delete a payment after confirmation
 * @param {number} paymentId
 */
function deletePayment(paymentId) {
    const payment = paymentsData.find(p => p.id === paymentId);
    const label   = payment ? `${formatCurrency(payment.amount)} on ${formatDate(payment.payment_date || payment.date)}` : `ID ${paymentId}`;

    showConfirmation(
        `Are you sure you want to delete payment "${label}"? This action cannot be undone.`,
        async () => {
            showLoading(true);
            try {
                const result = await makeApiCall('DELETE', `/api/payments/${paymentId}`);
                if (result.success || result.message) {
                    showNotification('Payment deleted successfully!', 'success');
                    await loadPayments();
                } else {
                    showNotification(result.error || 'Failed to delete payment', 'error');
                }
            } catch (error) {
                handleApiError(error, 'Delete payment');
            } finally {
                showLoading(false);
            }
        }
    );
}

// ====== VIEW PAYMENT DETAILS ======
/**
 * Show a modal with full payment details
 * @param {number} paymentId
 */
async function viewPaymentDetails(paymentId) {
    showLoading(true);
    try {
        const response = await makeApiCall('GET', `/api/payments/${paymentId}`);
        const p = response.payment || response;

        const travelerName = p.traveler_name ||
            `${p.first_name || ''} ${p.last_name || ''}`.trim() || `ID ${p.traveler_id}`;

        const content = `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;">
                <div><strong>Payment ID:</strong><br>${escapeHtml(String(p.id || '-'))}</div>
                <div><strong>Traveler:</strong><br>${escapeHtml(travelerName)}</div>
                <div><strong>Batch:</strong><br>${escapeHtml(p.batch_name || p.batch_id || '-')}</div>
                <div><strong>Amount:</strong><br>${formatCurrency(p.amount)}</div>
                <div><strong>Payment Method:</strong><br>${escapeHtml(p.payment_method || p.method || '-')}</div>
                <div><strong>Payment Date:</strong><br>${formatDate(p.payment_date || p.date)}</div>
                <div><strong>Transaction ID:</strong><br>${escapeHtml(p.transaction_id || '-')}</div>
                <div><strong>Status:</strong><br>${escapeHtml(p.payment_status || p.status || '-')}</div>
                <div style="grid-column:1/-1;"><strong>Notes:</strong><br>${escapeHtml(p.notes || '-')}</div>
                <div><strong>Created:</strong><br>${formatDate(p.created_at)}</div>
            </div>`;

        showModal(`<i class="fas fa-credit-card" style="color:#3498db;margin-right:8px;"></i>Payment Details`, content, [
            { label: '<i class="fas fa-receipt"></i> Generate Receipt', class: 'btn-success', onClick: `closeModal(); generateReceipt(${paymentId});` },
            { label: '<i class="fas fa-edit"></i> Edit', class: 'btn-primary', onClick: `closeModal(); editPayment(${paymentId});` },
            { label: '<i class="fas fa-times"></i> Close', class: 'btn-secondary', onClick: 'closeModal()' }
        ]);
    } catch (error) {
        handleApiError(error, 'Load payment details');
    } finally {
        showLoading(false);
    }
}

// ====== EXPORT TO CSV ======
/**
 * Export the current payment list to a CSV file
 */
function exportPaymentsToCSV() {
    const data = filteredPaymentsData.length > 0 ? filteredPaymentsData : paymentsData;
    if (!data || data.length === 0) {
        showNotification('No payments to export', 'warning');
        return;
    }

    const headers = ['ID','Traveler','Batch','Amount','Method','Date','Transaction ID','Status','Notes'];
    const rows = data.map(p => {
        const travelerName = p.traveler_name || `${p.first_name || ''} ${p.last_name || ''}`.trim();
        return [
            p.id, travelerName, p.batch_name || p.batch_id,
            p.amount, p.payment_method || p.method,
            p.payment_date || p.date, p.transaction_id,
            p.payment_status || p.status, p.notes
        ].map(v => `"${String(v || '').replace(/"/g, '""')}"`);
    });

    const csv  = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href     = url;
    link.download = `payments_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    showNotification(`Exported ${data.length} payments to CSV`, 'success');
}

// ====== GENERATE RECEIPT ======
/**
 * Generate a receipt PDF for a payment
 * @param {number} paymentId
 */
async function generateReceipt(paymentId) {
    showLoading(true);
    try {
        const response = await makeApiCall('GET', `/api/payments/${paymentId}`);
        const p = response.payment || response;

        const travelerName = p.traveler_name ||
            `${p.first_name || ''} ${p.last_name || ''}`.trim() || `ID ${p.traveler_id}`;

        // Try API-based receipt generation first
        try {
            const receiptResponse = await fetch(`/api/payments/${paymentId}/receipt`, {
                credentials: 'include'
            });
            if (receiptResponse.ok) {
                const blob = await receiptResponse.blob();
                const url  = URL.createObjectURL(blob);
                window.open(url, '_blank');
                showNotification('Receipt generated successfully!', 'success');
                return;
            }
        } catch (e) {
            console.log('API receipt not available, generating client-side');
        }

        // Client-side receipt generation
        const receiptHtml = `
            <!DOCTYPE html><html><head>
            <title>Receipt - Payment #${p.id}</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; }
                .header { text-align: center; border-bottom: 2px solid #2c3e50; padding-bottom: 20px; margin-bottom: 20px; }
                .header h1 { color: #2c3e50; }
                .receipt-no { font-size: 1.2rem; color: #7f8c8d; }
                .details { margin: 20px 0; }
                .row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #ecf0f1; }
                .label { font-weight: bold; color: #2c3e50; }
                .amount { font-size: 1.5rem; font-weight: bold; color: #27ae60; text-align: center; margin: 20px 0; }
                .footer { text-align: center; color: #95a5a6; font-size: 0.85rem; margin-top: 30px; }
            </style></head><body>
            <div class="header">
                <h1>&#x1F54B; Alhudha Haj Travel</h1>
                <div class="receipt-no">Receipt #REC-${String(p.id).padStart(6, '0')}</div>
            </div>
            <div class="details">
                <div class="row"><span class="label">Traveler:</span><span>${escapeHtml(travelerName)}</span></div>
                <div class="row"><span class="label">Payment Date:</span><span>${formatDate(p.payment_date || p.date)}</span></div>
                <div class="row"><span class="label">Payment Method:</span><span>${escapeHtml(p.payment_method || p.method || '-')}</span></div>
                <div class="row"><span class="label">Transaction ID:</span><span>${escapeHtml(p.transaction_id || '-')}</span></div>
                <div class="row"><span class="label">Status:</span><span>${escapeHtml(p.payment_status || p.status || '-')}</span></div>
            </div>
            <div class="amount">Amount Paid: ${formatCurrency(p.amount)}</div>
            <div class="footer">
                <p>Thank you for your payment. This is a computer-generated receipt.</p>
                <p>Generated on ${new Date().toLocaleString('en-IN')}</p>
            </div>
            </body></html>`;

        const blob = new Blob([receiptHtml], { type: 'text/html' });
        const url  = URL.createObjectURL(blob);
        const win  = window.open(url, '_blank');
        if (win) win.onload = () => win.print();

        showNotification('Receipt generated successfully!', 'success');
    } catch (error) {
        handleApiError(error, 'Generate receipt');
    } finally {
        showLoading(false);
    }
}
// ── State ────────────────────────────────────────────────────
let allPayments = [];
let filteredPayments = [];
let allTravelersForPayment = [];
let allBatchesForPayment = [];
let paymentsPage = 1;
const PAYMENTS_PER_PAGE = 20;

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    SessionManager.initPage(async () => {
        await Promise.all([loadPayments(), loadTravelersForSelect(), loadBatchesForPaymentSelect()]);
        initPaymentSearchListeners();
    });
});

function initPaymentSearchListeners() {
    const searchEl  = document.getElementById('searchPayments');
    const statusEl  = document.getElementById('paymentStatusFilter');
    const methodEl  = document.getElementById('paymentMethodFilter');
    if (searchEl) searchEl.addEventListener('input', debounce(filterPayments, 250));
    if (statusEl) statusEl.addEventListener('change', filterPayments);
    if (methodEl) methodEl.addEventListener('change', filterPayments);
}

async function loadTravelersForSelect() {
    try {
        const data = await makeAPICall('GET', '/api/travelers');
        if (data.success) {
            allTravelersForPayment = data.travelers || [];
            populateTravelerSelects();
        }
    } catch (e) { console.warn('Could not load travelers for select:', e.message); }
}

async function loadBatchesForPaymentSelect() {
    try {
        const data = await makeAPICall('GET', '/api/batches');
        if (data.success) {
            allBatchesForPayment = data.batches || [];
            populatePaymentBatchSelects();
        }
    } catch (e) { console.warn('Could not load batches for select:', e.message); }
}

function populateTravelerSelects() {
    document.querySelectorAll('.traveler-select, #payment_traveler_id').forEach((sel) => {
        const current = sel.value;
        sel.innerHTML = '<option value="">Select Traveler</option>';
        allTravelersForPayment.forEach((t) => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.textContent = `${t.first_name} ${t.last_name} (${t.passport_no || 'N/A'})`;
            sel.appendChild(opt);
        });
        if (current) sel.value = current;
    });
}

function populatePaymentBatchSelects() {
    document.querySelectorAll('.payment-batch-select, #payment_batch_id').forEach((sel) => {
        const current = sel.value;
        sel.innerHTML = '<option value="">Select Batch</option>';
        allBatchesForPayment.forEach((b) => {
            const opt = document.createElement('option');
            opt.value = b.id;
            opt.textContent = b.batch_name;
            sel.appendChild(opt);
        });
        if (current) sel.value = current;
    });
}

// ── Load & Display ───────────────────────────────────────────

/**
 * Fetch all payments from the API
 */
async function loadPayments() {
    const tbody = document.getElementById('paymentsTableBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="11" class="loading"><i class="fas fa-spinner fa-spin"></i> Loading payments…</td></tr>';

    try {
        const data = await makeAPICall('GET', '/api/payments');
        if (data.success) {
            allPayments = data.payments || [];
            filteredPayments = [...allPayments];
            paymentsPage = 1;
            displayPayments();
            updatePaymentStats();
        } else {
            throw new Error(data.error || 'Failed to load payments');
        }
    } catch (error) {
        handleError(error, 'loadPayments');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="11" style="text-align:center; padding:40px;">
                <i class="fas fa-exclamation-triangle" style="color:#e74c3c; font-size:2rem;"></i>
                <p style="color:#e74c3c; margin:10px 0;">${escapeHtml(error.message)}</p>
                <button class="action-btn btn-primary" onclick="loadPayments()"><i class="fas fa-redo"></i> Retry</button>
            </td></tr>`;
        }
    }
}

/**
 * Render the current page of payments
 */
function displayPayments() {
    const tbody = document.getElementById('paymentsTableBody');
    if (!tbody) return;

    const start = (paymentsPage - 1) * PAYMENTS_PER_PAGE;
    const page  = filteredPayments.slice(start, start + PAYMENTS_PER_PAGE);

    if (page.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" style="text-align:center; padding:30px; color:#7f8c8d;">No payments found</td></tr>';
        updatePaymentPagination();
        return;
    }

    tbody.innerHTML = page.map((p) => {
        const statusClass = p.status === 'completed' ? 'status-active' : 'status-inactive';
        const travelerName = p.first_name ? `${p.first_name} ${p.last_name}` : '-';
        return `<tr>
            <td>${p.id}</td>
            <td>${escapeHtml(travelerName)}</td>
            <td>${escapeHtml(p.passport_no || '-')}</td>
            <td>${escapeHtml(p.batch_name || '-')}</td>
            <td>${escapeHtml(p.installment || p.notes || '-')}</td>
            <td><strong>${amount}</strong></td>
            <td>${p.payment_date ? formatDate(p.payment_date) : '-'}</td>
            <td>${p.due_date ? formatDate(p.due_date) : '-'}</td>
            <td>${escapeHtml(p.payment_method || p.method || '-')}</td>
            <td>${escapeHtml(p.transaction_id || p.reference || '-')}</td>
            <td><span class="status-badge ${statusClass}">${escapeHtml(statusText)}</span></td>
            <td>
                <button class="icon-btn" onclick="viewPaymentDetails(${p.id})" title="View"><i class="fas fa-eye"></i></button>
                ${p.status === 'completed' ? `<button class="icon-btn" onclick="showReverseModal(${p.id}, ${p.amount})" title="Reverse"><i class="fas fa-undo-alt"></i></button>` : ''}
            </td>
        </tr>`;
    });

    tableBody.innerHTML = html;
    updatePaginationDisplay(paymentsFiltered.length, paymentsCurrentPage, paymentsPerPage);
}

// ====== FILTER PAYMENTS ======
/**
 * Filter payments by traveler, status, date, or method
 */
function filterPayments() {
    const search = (document.getElementById('searchPayments')?.value || '').toLowerCase().trim();
    const statusFilter = document.getElementById('paymentStatusFilter')?.value || 'all';
    const methodFilter = document.getElementById('paymentMethodFilter')?.value || 'all';

    paymentsFiltered = paymentsData.filter(p => {
        const travelerName = `${p.first_name || ''} ${p.last_name || ''}`.toLowerCase();
        const passport = (p.passport_no || '').toLowerCase();
        const txId = (p.transaction_id || p.reference || '').toLowerCase();
        const matchesSearch = !search || travelerName.includes(search) || passport.includes(search) || txId.includes(search);

        const pStatus = p.status === 'completed' ? 'Paid' : (p.status || 'Pending');
        const matchesStatus = statusFilter === 'all' || pStatus.toLowerCase() === statusFilter.toLowerCase();
        const matchesMethod = methodFilter === 'all' || (p.payment_method || p.method || '').toLowerCase() === methodFilter.toLowerCase();

        return matchesSearch && matchesStatus && matchesMethod;
    });

    paymentsCurrentPage = 1;
    displayPayments();
    showNotification(`Found ${paymentsFiltered.length} payment(s)`, 'info');
}

// ====== RECORD PAYMENT ======
/**
 * POST a new payment record
 */
async function recordPayment() {
    if (!paymentsTravelerData) {
        showNotification('Please verify a traveler first', 'error'); return;
    }

    const amountRaw = document.getElementById('amount')?.value?.replace(/,/g, '') || '';
    const amount = parseFloat(amountRaw);
    if (!amount || amount <= 0) {
        showNotification('Please enter a valid amount', 'error'); return;
    }

    const paymentDate = document.getElementById('payment_date')?.value;
    if (!paymentDate) {
        showNotification('Payment date is required', 'error'); return;
    }

    const paymentData = {
        traveler_id: paymentsTravelerData.id,
        batch_id: paymentsTravelerData.batch_id,
        amount: amount,
        payment_date: paymentDate,
        payment_method: document.getElementById('payment_method')?.value,
        installment: document.getElementById('installment')?.value,
        transaction_id: document.getElementById('transaction_id')?.value?.trim(),
        due_date: document.getElementById('due_date')?.value || null,
        remarks: document.getElementById('remarks')?.value?.trim(),
        status: 'completed'
    };

    if (!paymentData.payment_method) {
        showNotification('Payment method is required', 'error'); return;
    }

    const submitBtn = document.querySelector('#paymentForm button[type="submit"]');
    showLoading(submitBtn, 'Recording...');
            <td><strong>${formatCurrency(p.amount)}</strong></td>
            <td>${p.payment_date ? formatDate(p.payment_date) : '-'}</td>
            <td>${escapeHtml(p.payment_method || '-')}</td>
            <td>${escapeHtml(p.reference || '-')}</td>
            <td><span class="status-badge ${statusClass}">${escapeHtml(p.status || '-')}</span></td>
            <td>${p.created_at ? formatDate(p.created_at) : '-'}</td>
            <td>
                <button class="icon-btn" onclick="editPayment(${p.id})" title="Edit"><i class="fas fa-edit"></i></button>
                <button class="icon-btn" onclick="generateReceipt(${p.id})" title="Generate Receipt"><i class="fas fa-receipt"></i></button>
                <button class="icon-btn" style="color:#e74c3c;" onclick="deletePayment(${p.id})" title="Delete"><i class="fas fa-trash"></i></button>
            </td>
        </tr>`;
    }).join('');

    updatePaymentPagination();
}

// ── Filter ───────────────────────────────────────────────────

/**
 * Filter payments by search text, status, and method
 */
function filterPayments() {
    const search = (document.getElementById('searchPayments')?.value || '').toLowerCase();
    const status = document.getElementById('paymentStatusFilter')?.value || 'all';
    const method = document.getElementById('paymentMethodFilter')?.value || 'all';

    filteredPayments = allPayments.filter((p) => {
        const name = `${p.first_name || ''} ${p.last_name || ''}`.toLowerCase();
        const matchSearch = !search ||
            name.includes(search) ||
            (p.passport_no || '').toLowerCase().includes(search) ||
            (p.reference || '').toLowerCase().includes(search) ||
            (p.batch_name || '').toLowerCase().includes(search);
        const matchStatus = status === 'all' || p.status === status;
        const matchMethod = method === 'all' || p.payment_method === method;
        return matchSearch && matchStatus && matchMethod;
    });

    paymentsPage = 1;
    displayPayments();
}

// ── Form Visibility ──────────────────────────────────────────

function showAddPaymentForm() {
    const form = document.getElementById('addPaymentForm');
    if (!form) return;
    form.style.display = 'block';
    form.scrollIntoView({ behavior: 'smooth' });
    // Set today's date as default
    const dateEl = document.getElementById('payment_date');
    if (dateEl && !dateEl.value) dateEl.value = new Date().toISOString().slice(0, 10);
}

function hideAddPaymentForm() {
    const form = document.getElementById('addPaymentForm');
    if (form) form.style.display = 'none';
    document.getElementById('paymentCreateForm')?.reset();
}

// ── CRUD ─────────────────────────────────────────────────────

/**
 * Record a new payment
 */
async function recordPayment(event) {
    if (event) event.preventDefault();

    const getData = (id) => (document.getElementById(id)?.value || '').trim();

    const paymentData = {
        traveler_id:    getData('payment_traveler_id'),
        batch_id:       getData('payment_batch_id'),
        amount:         parseFloat(getData('payment_amount')),
        payment_date:   getData('payment_date'),
        payment_method: getData('payment_method') || null,
        reference:      getData('payment_reference') || null,
        notes:          getData('payment_notes') || null,
        status:         getData('payment_status') || 'completed'
    };

    if (!paymentData.traveler_id || !paymentData.batch_id || !paymentData.amount || !paymentData.payment_date) {
        showNotification('Traveler, batch, amount and date are required', 'error');
        return;
    }
    if (isNaN(paymentData.amount) || paymentData.amount <= 0) {
        showNotification('Please enter a valid amount greater than 0', 'error');
        return;
    }

    const btn  = document.querySelector('#paymentCreateForm button[type="submit"]');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Recording…'; btn.disabled = true; }

    try {
        const data = await makeAPICall('POST', '/api/payments', paymentData);
        if (data.success) {
            showNotification('Payment recorded successfully!', 'success');
            if (typeof hideAddPaymentForm === 'function') hideAddPaymentForm();
            paymentsTravelerData = null;
            await loadPayments();
        } else {
            showNotification('Error: ' + (data.error || 'Could not record payment'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'recordPayment');
    } finally {
        hideLoading(submitBtn);
    }
}

// ====== EDIT PAYMENT ======
/**
 * Load payment data for editing
 * @param {number} id
 */
function editPayment(id) {
    const payment = paymentsData.find(p => p.id === id);
    if (!payment) { showNotification('Payment not found', 'error'); return; }

    paymentsCurrentId = id;
    showNotification(`Edit payment #${id} - use the view modal to modify`, 'info');
    viewPaymentDetails(id);
}

// ====== UPDATE PAYMENT ======
/**
 * PUT updated payment data
 */
async function updatePayment() {
    if (!paymentsCurrentId) {
        showNotification('No payment selected for editing', 'error'); return;
    }

    const paymentData = {
        amount: parseFloat(document.getElementById('edit_amount')?.value || 0),
        payment_date: document.getElementById('edit_payment_date')?.value,
        payment_method: document.getElementById('edit_payment_method')?.value,
        status: document.getElementById('edit_payment_status')?.value,
        remarks: document.getElementById('edit_remarks')?.value?.trim()
    };

    try {
        const data = await makeAPICall('PUT', `/api/payments/${paymentsCurrentId}`, paymentData);
        if (data.success) {
            showNotification('Payment updated successfully!', 'success');
            paymentsCurrentId = null;
            closeModal();
            await loadPayments();
        } else {
            showNotification('Error: ' + (data.error || 'Update failed'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'updatePayment');
    }
}

// ====== DELETE PAYMENT ======
/**
 * DELETE a payment by ID
 * @param {number} id
 */
async function deletePayment(id) {
    if (!confirm('Are you sure you want to delete this payment? This action cannot be undone.')) return;
            hideAddPaymentForm();
            await loadPayments();
        } else {
            throw new Error(data.error || 'Could not record payment');
        }
    } catch (error) {
        handleError(error, 'recordPayment');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Load payment data into the edit modal
 * @param {number} id
 */
async function editPayment(id) {
    try {
        const data = await makeAPICall('GET', `/api/payments/${id}`);
        if (!data.success || !data.payment) throw new Error(data.error || 'Payment not found');

        const p = data.payment;
        const set = (elId, val) => { const el = document.getElementById(elId); if (el) el.value = val || ''; };

        set('edit_payment_id',     p.id);
        set('edit_payment_amount', p.amount);
        set('edit_payment_date',   p.payment_date ? p.payment_date.slice(0, 10) : '');
        set('edit_payment_method', p.payment_method);
        set('edit_payment_reference', p.reference);
        set('edit_payment_notes',  p.notes);
        set('edit_payment_status', p.status);

        const modal   = document.getElementById('editPaymentModal');
        const overlay = document.getElementById('modalOverlay');
        if (modal)   modal.style.display   = 'block';
        if (overlay) overlay.style.display = 'block';
    } catch (error) {
        handleError(error, 'editPayment');
    }
}

/**
 * Submit the edit payment form
 */
async function updatePayment(event) {
    if (event) event.preventDefault();

    const id = document.getElementById('edit_payment_id')?.value;
    if (!id) return;

    const getData = (elId) => (document.getElementById(elId)?.value || '').trim();

    const paymentData = {
        amount:         parseFloat(getData('edit_payment_amount')),
        payment_date:   getData('edit_payment_date'),
        payment_method: getData('edit_payment_method') || null,
        reference:      getData('edit_payment_reference') || null,
        notes:          getData('edit_payment_notes') || null,
        status:         getData('edit_payment_status')
    };

    const btn  = document.querySelector('#editPaymentForm button[type="submit"]');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating…'; btn.disabled = true; }

    try {
        const data = await makeAPICall('PUT', `/api/payments/${id}`, paymentData);
        if (data.success) {
            showNotification('Payment updated successfully!', 'success');
            closePaymentModal();
            await loadPayments();
        } else {
            throw new Error(data.error || 'Could not update payment');
        }
    } catch (error) {
        handleError(error, 'updatePayment');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Delete a payment by ID
 * @param {number} id
 */
async function deletePayment(id) {
    if (!confirmAction(`Delete payment ID ${id}? This cannot be undone.`)) return;

    try {
        const data = await makeAPICall('DELETE', `/api/payments/${id}`);
        if (data.success) {
            showNotification('Payment deleted successfully!', 'success');
            await loadPayments();
        } else {
            showNotification('Error: ' + (data.error || 'Could not delete payment'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'deletePayment');
    }
}

// ====== VIEW PAYMENT DETAILS ======
/**
 * Show a modal with full payment details and receipt
 * @param {number} id
 */
function viewPaymentDetails(id) {
    const p = paymentsData.find(p => p.id === id);
    if (!p) { showNotification('Payment not found', 'error'); return; }

    paymentsCurrentId = id;
    const travelerName = p.first_name ? `${p.first_name} ${p.last_name || ''}`.trim() : (p.traveler_name || '-');
    const statusText = p.status === 'completed' ? 'Paid' : (p.status || 'Pending');

    const detailsHtml = `
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:15px;">
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Traveler:</strong><br>${escapeHtml(travelerName)}
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Passport:</strong><br>${escapeHtml(p.passport_no || '-')}
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Batch:</strong><br>${escapeHtml(p.batch_name || '-')}
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Amount:</strong><br><span style="font-size:1.3rem;font-weight:bold;color:#27ae60;">${formatCurrency(p.amount)}</span>
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Payment Date:</strong><br>${formatDate(p.payment_date)}
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Method:</strong><br>${escapeHtml(p.payment_method || p.method || '-')}
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Transaction ID:</strong><br>${escapeHtml(p.transaction_id || p.reference || '-')}
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Status:</strong><br>
                <span class="status-badge ${getStatusClass(p.status === 'completed' ? 'paid' : p.status)}">${escapeHtml(statusText)}</span>
            </div>
            ${p.installment ? `<div style="background:#f8f9fa;padding:12px;border-radius:5px;"><strong>Installment:</strong><br>${escapeHtml(p.installment)}</div>` : ''}
            ${p.due_date ? `<div style="background:#f8f9fa;padding:12px;border-radius:5px;"><strong>Due Date:</strong><br>${formatDate(p.due_date)}</div>` : ''}
        </div>
        ${(p.remarks || p.notes) ? `<div style="margin-top:15px;padding:12px;background:#fff3cd;border-radius:5px;"><strong>Remarks:</strong><br>${escapeHtml(p.remarks || p.notes)}</div>` : ''}
    `;

    const existingModal = document.getElementById('paymentModal');
    const existingDetails = document.getElementById('paymentDetails');
    const existingOverlay = document.getElementById('modalOverlay');

    if (existingModal && existingDetails) {
        existingDetails.innerHTML = detailsHtml;
        existingModal.style.display = 'block';
        if (existingOverlay) existingOverlay.style.display = 'block';
    } else {
        showModal(`<i class="fas fa-file-invoice"></i> Payment Details #${id}`, detailsHtml,
            `<button class="action-btn btn-secondary" onclick="closeModal()">Close</button>`);
    }
}

// ====== EXPORT TO CSV ======
/**
 * Export all payments to a CSV file
 */
function exportPaymentsToCSV() {
    if (!paymentsData.length) { showNotification('No payments to export', 'warning'); return; }

    const headers = ['ID', 'Traveler Name', 'Passport', 'Batch', 'Installment',
        'Amount', 'Payment Date', 'Due Date', 'Method', 'Transaction ID', 'Status', 'Remarks'];

    const rows = [headers, ...paymentsData.map(p => {
        const travelerName = p.first_name ? `${p.first_name} ${p.last_name || ''}`.trim() : (p.traveler_name || '');
        return [
            p.id, travelerName, p.passport_no, p.batch_name, p.installment,
            p.amount, p.payment_date, p.due_date, p.payment_method || p.method,
            p.transaction_id || p.reference, p.status, p.remarks || p.notes
        ];
    })];

    downloadCSV(rows, `payments_${new Date().toISOString().slice(0, 10)}.csv`);
    showNotification(`Exported ${paymentsData.length} payments to CSV`, 'success');
}

// ====== GENERATE RECEIPT ======
/**
 * Create a receipt for a payment
 * @param {number} paymentId
 */
async function generateReceipt(paymentId) {
    const payment = paymentsData.find(p => p.id === paymentId);
    if (!payment) { showNotification('Payment not found', 'error'); return; }

    try {
        const data = await makeAPICall('POST', '/api/receipts', {
            payment_id: paymentId,
            traveler_id: payment.traveler_id,
            amount: payment.amount,
            payment_date: payment.payment_date,
            payment_method: payment.payment_method || payment.method
        });
        if (data.success) {
            showNotification('Receipt generated successfully!', 'success');
        } else {
            showNotification('Error: ' + (data.error || 'Could not generate receipt'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'generateReceipt');
    }
}

// ====== PAYMENT STATS ======
async function updatePaymentStats() {
    try {
        const data = await makeAPICall('GET', '/api/payments/stats');
        if (data.success && data.stats) {
            const s = data.stats;
            const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
            setEl('paymentTotalCollected', formatCurrency(s.total_collected || 0));
            setEl('paymentPendingAmount', formatCurrency(s.pending_amount || 0));
            setEl('paidCount', s.paid_count || 0);
            setEl('pendingCount', s.pending_count || 0);
            setEl('reversedCount', s.reversed_count || 0);
        }
    } catch (error) {
        // Stats are optional - compute from loaded data
        const totalCollected = paymentsData.filter(p => p.status === 'completed').reduce((s, p) => s + (p.amount || 0), 0);
        const paidCount = paymentsData.filter(p => p.status === 'completed').length;
        const pendingCount = paymentsData.filter(p => p.status !== 'completed').length;

        const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        setEl('paymentTotalCollected', formatCurrency(totalCollected));
        setEl('paidCount', paidCount);
        setEl('pendingCount', pendingCount);
    }
}

// ====== RESET FILTERS ======
function resetFilters() {
    const searchEl = document.getElementById('searchPayments');
    const statusEl = document.getElementById('paymentStatusFilter');
    const methodEl = document.getElementById('paymentMethodFilter');
    if (searchEl) searchEl.value = '';
    if (statusEl) statusEl.value = 'all';
    if (methodEl) methodEl.value = 'all';
    paymentsFiltered = [...paymentsData];
    paymentsCurrentPage = 1;
    displayPayments();
}

// ====== PAGINATION ======
function paymentsPreviousPage() {
    if (paymentsCurrentPage > 1) { paymentsCurrentPage--; displayPayments(); }
}
function paymentsNextPage() {
    if (paymentsCurrentPage * paymentsPerPage < paymentsFiltered.length) { paymentsCurrentPage++; displayPayments(); }
}

function previousPage() { paymentsPreviousPage(); }
function nextPage() { paymentsNextPage(); }
            throw new Error(data.error || 'Could not delete payment');
        }
    } catch (error) {
        handleError(error, 'deletePayment');
    }
}

/**
 * Generate a receipt for a payment
 * @param {number} paymentId
 */
async function generateReceipt(paymentId) {
    try {
        showLoading('Generating receipt…');
        const data = await makeAPICall('GET', `/api/payments/${paymentId}`);
        hideLoading();

        if (!data.success || !data.payment) throw new Error(data.error || 'Payment not found');
        const p = data.payment;

        // Check if receipt already exists
        if (data.payment.receipt) {
            showNotification('Receipt already exists for this payment', 'info');
            return;
        }

        // Create receipt via API
        const receiptData = {
            traveler_id:  p.traveler_id,
            payment_id:   p.id,
            amount:       p.amount,
            receipt_date: p.payment_date || new Date().toISOString().slice(0, 10)
        };

        const receiptResp = await makeAPICall('POST', '/api/receipts', receiptData);
        if (receiptResp.success) {
            showNotification(`Receipt ${receiptResp.receipt_number} generated successfully!`, 'success');
        } else {
            throw new Error(receiptResp.error || 'Could not generate receipt');
        }
    } catch (error) {
        hideLoading();
        handleError(error, 'generateReceipt');
    }
}

// ── Export ───────────────────────────────────────────────────

/**
 * Export filtered payments to CSV
 */
function exportPaymentsToCSV() {
    if (!filteredPayments.length) { showNotification('No payments to export', 'warning'); return; }

    const rows = filteredPayments.map((p) => ({
        ...p,
        traveler_name: `${p.first_name || ''} ${p.last_name || ''}`.trim()
    }));

    downloadCSV(
        rows,
        ['id', 'traveler_name', 'passport_no', 'batch_name', 'amount', 'payment_date', 'payment_method', 'reference', 'status'],
        ['ID', 'Traveler', 'Passport No', 'Batch', 'Amount', 'Date', 'Method', 'Reference', 'Status'],
        `payments_${new Date().toISOString().slice(0, 10)}.csv`
    );
}

// ── Pagination ───────────────────────────────────────────────

function updatePaymentPagination() {
    const total = filteredPayments.length;
    const start = total > 0 ? (paymentsPage - 1) * PAYMENTS_PER_PAGE + 1 : 0;
    const end   = Math.min(paymentsPage * PAYMENTS_PER_PAGE, total);
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalCount',  total);
    setEl('showingFrom', start);
    setEl('showingTo',   end);
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    if (prevBtn) prevBtn.disabled = paymentsPage === 1;
    if (nextBtn) nextBtn.disabled = end >= total;
}

function prevPaymentPage() {
    if (paymentsPage > 1) { paymentsPage--; displayPayments(); }
}

function nextPaymentPage() {
    if (paymentsPage * PAYMENTS_PER_PAGE < filteredPayments.length) { paymentsPage++; displayPayments(); }
}

// ── Stats ────────────────────────────────────────────────────

function updatePaymentStats() {
    const completed = allPayments.filter((p) => p.status === 'completed');
    const pending   = allPayments.filter((p) => p.status === 'pending');
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalPayments',    allPayments.length);
    setEl('completedPayments', completed.length);
    setEl('pendingPayments',   pending.length);
    setEl('totalCollected',   formatCurrency(completed.reduce((s, p) => s + (parseFloat(p.amount) || 0), 0)));
    setEl('pendingAmount',    formatCurrency(pending.reduce((s, p) => s + (parseFloat(p.amount) || 0), 0)));
}

// ── Modal Helpers ────────────────────────────────────────────

function closePaymentModal() {
    const modal   = document.getElementById('editPaymentModal');
    const overlay = document.getElementById('modalOverlay');
    if (modal)   modal.style.display   = 'none';
    if (overlay) overlay.style.display = 'none';
}

// ── Form submit wiring ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('paymentCreateForm')?.addEventListener('submit', recordPayment);
    document.getElementById('editPaymentForm')?.addEventListener('submit', updatePayment);
});

// Expose globals
window.loadPayments        = loadPayments;
window.filterPayments      = filterPayments;
window.showAddPaymentForm  = showAddPaymentForm;
window.hideAddPaymentForm  = hideAddPaymentForm;
window.editPayment         = editPayment;
window.deletePayment       = deletePayment;
window.generateReceipt     = generateReceipt;
window.exportPaymentsToCSV = exportPaymentsToCSV;
window.closePaymentModal   = closePaymentModal;
window.prevPaymentPage     = prevPaymentPage;
window.nextPaymentPage     = nextPaymentPage;

console.log('✅ payments.js loaded');
