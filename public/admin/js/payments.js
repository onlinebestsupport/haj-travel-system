/**
 * payments.js - Payment Management for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 * API base: /api/payments
 */

'use strict';

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
