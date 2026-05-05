/**
 * payments.js - Payment management functions
 * Alhudha Haj Travel Management System
 */

'use strict';

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
