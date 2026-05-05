/**
 * payments.js - Payment management functions
 * Alhudha Haj Travel Admin Panel
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

console.log('✅ payments.js loaded');
