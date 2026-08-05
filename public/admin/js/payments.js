/**
 * payments.js - Payment Management for Alhudha Haj Travel Admin
 * Handles CRUD operations for payments
 * Depends on: common.js, session-manager.js
 * API base: /api/payments
 */

'use strict';

// ====== STATE ======
let paymentsData = [];
let filteredPaymentsData = [];
let paymentsCurrentPage = 1;
const PAYMENTS_PER_PAGE = 10;
let travelersData = [];
let batchesData = [];

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
        console.log('🔄 Loading payments...');
        const response = await fetch('/api/payments', {
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
            if (response.status === 401) {
                showNotification('Session expired. Please login again', 'error');
                setTimeout(() => {
                    window.location.href = '/admin/login.html';
                }, 2000);
                return;
            }
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        console.log('📦 Payments API response:', data);
        
        if (data.success && Array.isArray(data.payments)) {
            paymentsData = data.payments;
            filteredPaymentsData = [...paymentsData];
            console.log(`✅ Loaded ${paymentsData.length} payments`);
        } else {
            console.warn('⚠️ No payments found, using demo data');
            useDemoPayments();
        }
    } catch (error) {
        console.error('❌ Error loading payments:', error);
        useDemoPayments();
    }

    displayPayments();
    updatePaymentStats();
}

/**
 * Use demo payment data when API is unavailable
 */
function useDemoPayments() {
    paymentsData = [
        {
            id: 1,
            traveler_id: 1,
            batch_id: 1,
            amount: 25000,
            payment_date: '2026-01-15',
            payment_method: 'Cash',
            status: 'completed',
            reference: 'CASH-001',
            notes: 'Booking amount paid',
            installment: 'Booking Amount',
            first_name: 'John',
            last_name: 'Doe',
            passport_no: 'A0000001',
            batch_name: 'Haj Platinum 2026'
        },
        {
            id: 2,
            traveler_id: 2,
            batch_id: 2,
            amount: 50000,
            payment_date: '2026-01-20',
            payment_method: 'Bank Transfer',
            status: 'completed',
            reference: 'BT-2026-001',
            notes: '1st installment paid',
            installment: '1st Installment',
            first_name: 'Jane',
            last_name: 'Smith',
            passport_no: 'A0000002',
            batch_name: 'Haj Gold 2026'
        },
        {
            id: 3,
            traveler_id: 1,
            batch_id: 1,
            amount: 30000,
            payment_date: '2026-02-10',
            payment_method: 'UPI',
            status: 'pending',
            reference: 'UPI-001',
            notes: 'Pending 2nd installment',
            installment: '2nd Installment',
            first_name: 'John',
            last_name: 'Doe',
            passport_no: 'A0000001',
            batch_name: 'Haj Platinum 2026'
        }
    ];
    filteredPaymentsData = [...paymentsData];
}

// ====== DISPLAY PAYMENTS ======
/**
 * Render the payments table with status badges and pagination
 */
function displayPayments() {
    const tableBody = document.getElementById('paymentsTableBody');
    if (!tableBody) return;

    if (!filteredPaymentsData || filteredPaymentsData.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="11" style="text-align:center;padding:40px;">No payments found</td></tr>';
        updatePaginationDisplay(0);
        return;
    }

    const start = (paymentsCurrentPage - 1) * PAYMENTS_PER_PAGE;
    const end = Math.min(start + PAYMENTS_PER_PAGE, filteredPaymentsData.length);
    const pageData = filteredPaymentsData.slice(start, end);

    let html = '';
    pageData.forEach(p => {
        const travelerName = p.first_name ? `${p.first_name} ${p.last_name || ''}`.trim() : (p.traveler_name || '-');
        const amount = parseFloat(p.amount || 0);
        const statusText = p.status === 'completed' ? 'Paid' : (p.status === 'pending' ? 'Pending' : p.status === 'reversed' ? 'Reversed' : (p.status || 'Pending'));
        const statusClass = getStatusClass(p.status);

        // Check if overdue
        let isOverdue = false;
        if (p.status === 'pending' && p.due_date) {
            const today = new Date();
            const dueDate = new Date(p.due_date);
            if (dueDate < today) {
                isOverdue = true;
            }
        }

        const statusDisplay = isOverdue ? 'Overdue' : statusText;
        const statusClassDisplay = isOverdue ? 'status-inactive' : statusClass;

        html += `<tr>
            <td>${p.id}</td>
            <td><strong>${escapeHtml(travelerName)}</strong></td>
            <td>${escapeHtml(p.passport_no || '-')}</td>
            <td>${escapeHtml(p.batch_name || '-')}</td>
            <td>${escapeHtml(p.installment || '-')}</td>
            <td><strong>₹${amount.toLocaleString('en-IN')}</strong></td>
            <td>${p.payment_date ? formatDate(p.payment_date) : '-'}</td>
            <td>${escapeHtml(p.payment_method || '-')}</td>
            <td>${escapeHtml(p.reference || p.transaction_id || '-')}</td>
            <td><span class="status-badge ${statusClassDisplay}">${escapeHtml(statusDisplay)}</span></td>
            <td>
                <button class="icon-btn" onclick="viewPaymentDetails(${p.id})" title="View"><i class="fas fa-eye"></i></button>
                ${p.status === 'completed' ? `<button class="icon-btn" onclick="showReverseModal(${p.id}, ${p.amount})" title="Reverse"><i class="fas fa-undo-alt"></i></button>` : ''}
            </td>
        </tr>`;
    });

    tableBody.innerHTML = html;
    updatePaginationDisplay(filteredPaymentsData.length);
}

/**
 * Get CSS class for status badge
 */
function getStatusClass(status) {
    if (!status) return 'status-pending';
    const s = status.toLowerCase();
    if (s === 'completed' || s === 'paid') return 'status-active';
    if (s === 'pending') return 'status-pending';
    if (s === 'reversed') return 'status-inactive';
    if (s === 'overdue') return 'status-inactive';
    return 'status-pending';
}

/**
 * Update pagination display
 */
function updatePaginationDisplay(total) {
    const totalEl = document.getElementById('totalCount');
    const fromEl = document.getElementById('showingFrom');
    const toEl = document.getElementById('showingTo');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    if (totalEl) totalEl.textContent = total;
    const start = total > 0 ? (paymentsCurrentPage - 1) * PAYMENTS_PER_PAGE + 1 : 0;
    const end = Math.min(paymentsCurrentPage * PAYMENTS_PER_PAGE, total);
    if (fromEl) fromEl.textContent = start;
    if (toEl) toEl.textContent = end;

    if (prevBtn) prevBtn.disabled = paymentsCurrentPage === 1;
    if (nextBtn) nextBtn.disabled = end >= total;
}

// ====== FILTER PAYMENTS ======
/**
 * Filter payments by search text, status, and method
 */
function filterPayments() {
    const searchEl = document.getElementById('searchPayments');
    const statusEl = document.getElementById('paymentStatusFilter');
    const methodEl = document.getElementById('paymentMethodFilter');
    
    const search = searchEl ? searchEl.value.toLowerCase().trim() : '';
    const status = statusEl ? statusEl.value : 'all';
    const method = methodEl ? methodEl.value : 'all';

    if (!search && status === 'all' && method === 'all') {
        filteredPaymentsData = [...paymentsData];
    } else {
        filteredPaymentsData = paymentsData.filter(p => {
            const travelerName = `${p.first_name || ''} ${p.last_name || ''}`.toLowerCase();
            const passport = (p.passport_no || '').toLowerCase();
            const ref = (p.reference || p.transaction_id || '').toLowerCase();
            const batch = (p.batch_name || '').toLowerCase();

            let matchesSearch = true;
            if (search) {
                matchesSearch = travelerName.includes(search) || 
                               passport.includes(search) || 
                               ref.includes(search) || 
                               batch.includes(search);
            }

            let matchesStatus = true;
            if (status !== 'all') {
                if (status === 'Overdue') {
                    const today = new Date();
                    const dueDate = p.due_date ? new Date(p.due_date) : null;
                    matchesStatus = p.status === 'pending' && dueDate && dueDate < today;
                } else {
                    const statusMap = {
                        'Paid': 'completed',
                        'Pending': 'pending',
                        'Reversed': 'reversed'
                    };
                    matchesStatus = p.status === (statusMap[status] || status.toLowerCase());
                }
            }

            let matchesMethod = true;
            if (method !== 'all') {
                matchesMethod = (p.payment_method || '') === method;
            }

            return matchesSearch && matchesStatus && matchesMethod;
        });
    }

    paymentsCurrentPage = 1;
    displayPayments();
    showNotification(`Found ${filteredPaymentsData.length} payment(s)`, 'info');
}

/**
 * Clear search and reset filter
 */
function resetFilters() {
    const searchEl = document.getElementById('searchPayments');
    const statusEl = document.getElementById('paymentStatusFilter');
    const methodEl = document.getElementById('paymentMethodFilter');
    
    if (searchEl) searchEl.value = '';
    if (statusEl) statusEl.value = 'all';
    if (methodEl) methodEl.value = 'all';
    
    filteredPaymentsData = [...paymentsData];
    paymentsCurrentPage = 1;
    displayPayments();
    showNotification('Filters reset', 'info');
}

// ====== PAGINATION ======
function previousPage() {
    if (paymentsCurrentPage > 1) {
        paymentsCurrentPage--;
        displayPayments();
    }
}

function nextPage() {
    if (paymentsCurrentPage * PAYMENTS_PER_PAGE < filteredPaymentsData.length) {
        paymentsCurrentPage++;
        displayPayments();
    }
}

// ====== PAYMENT STATS ======
/**
 * Update payment statistics
 */
async function updatePaymentStats() {
    try {
        const response = await fetch('/api/payments/stats', {
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        });

        if (response.ok) {
            const data = await response.json();
            if (data.success && data.stats) {
                const s = data.stats;
                document.getElementById('paymentTotalCollected').innerHTML = `₹${(s.total_collected || 0).toLocaleString('en-IN')}`;
                document.getElementById('paymentPendingAmount').innerHTML = `₹${(s.pending_amount || 0).toLocaleString('en-IN')}`;
                document.getElementById('paidCount').textContent = s.completed_count || 0;
                document.getElementById('pendingCount').textContent = s.pending_count || 0;
                document.getElementById('reversedCount').textContent = s.reversed_count || 0;
                return;
            }
        }

        // Fallback: calculate from loaded data
        const totalCollected = paymentsData.filter(p => p.status === 'completed').reduce((sum, p) => sum + (parseFloat(p.amount) || 0), 0);
        const pendingAmount = paymentsData.filter(p => p.status === 'pending').reduce((sum, p) => sum + (parseFloat(p.amount) || 0), 0);
        const paidCount = paymentsData.filter(p => p.status === 'completed').length;
        const pendingCount = paymentsData.filter(p => p.status === 'pending').length;
        const reversedCount = paymentsData.filter(p => p.status === 'reversed').length;

        document.getElementById('paymentTotalCollected').innerHTML = `₹${totalCollected.toLocaleString('en-IN')}`;
        document.getElementById('paymentPendingAmount').innerHTML = `₹${pendingAmount.toLocaleString('en-IN')}`;
        document.getElementById('paidCount').textContent = paidCount;
        document.getElementById('pendingCount').textContent = pendingCount;
        document.getElementById('reversedCount').textContent = reversedCount;
    } catch (error) {
        console.error('Error loading payment stats:', error);
    }
}

// ====== VIEW PAYMENT DETAILS ======
/**
 * Show a modal with full payment details
 */
function viewPaymentDetails(id) {
    const p = paymentsData.find(p => p.id === id);
    if (!p) {
        showNotification('Payment not found', 'error');
        return;
    }

    const travelerName = p.first_name ? `${p.first_name} ${p.last_name || ''}`.trim() : (p.traveler_name || '-');
    const amount = parseFloat(p.amount || 0);
    const statusText = p.status === 'completed' ? 'Paid' : (p.status === 'pending' ? 'Pending' : p.status === 'reversed' ? 'Reversed' : (p.status || 'Pending'));
    const statusClass = getStatusClass(p.status);

    const detailsHtml = `
        <div style="padding: 10px;">
            <h4 style="color: #2c3e50; margin-bottom: 20px;">Payment #${p.id}</h4>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                <div style="background: #f8f9fa; padding: 12px; border-radius: 5px;">
                    <strong>Traveler:</strong><br>
                    <span style="font-weight: 500;">${escapeHtml(travelerName)}</span>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 5px;">
                    <strong>Passport Number:</strong><br>
                    <span style="font-weight: 500;">${escapeHtml(p.passport_no || '-')}</span>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 5px;">
                    <strong>Batch:</strong><br>
                    <span style="font-weight: 500;">${escapeHtml(p.batch_name || '-')}</span>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 5px;">
                    <strong>Amount:</strong><br>
                    <span style="font-size: 1.2rem; font-weight: bold; color: #27ae60;">₹${amount.toLocaleString('en-IN')}</span>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 5px;">
                    <strong>Payment Date:</strong><br>
                    <span style="font-weight: 500;">${p.payment_date ? formatDate(p.payment_date) : '-'}</span>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 5px;">
                    <strong>Payment Method:</strong><br>
                    <span style="font-weight: 500;">${escapeHtml(p.payment_method || '-')}</span>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 5px;">
                    <strong>Transaction ID:</strong><br>
                    <span style="font-weight: 500;">${escapeHtml(p.reference || p.transaction_id || '-')}</span>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 5px;">
                    <strong>Status:</strong><br>
                    <span class="status-badge ${statusClass}">${escapeHtml(statusText)}</span>
                </div>
                ${p.installment ? `
                <div style="background: #f8f9fa; padding: 12px; border-radius: 5px;">
                    <strong>Installment:</strong><br>
                    <span style="font-weight: 500;">${escapeHtml(p.installment)}</span>
                </div>
                ` : ''}
                ${p.due_date ? `
                <div style="background: #f8f9fa; padding: 12px; border-radius: 5px;">
                    <strong>Due Date:</strong><br>
                    <span style="font-weight: 500;">${formatDate(p.due_date)}</span>
                </div>
                ` : ''}
            </div>
            ${(p.notes) ? `
                <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 5px;">
                    <strong>Remarks:</strong>
                    <p style="margin-top: 5px;">${escapeHtml(p.notes)}</p>
                </div>
            ` : ''}
            <div style="margin-top: 20px; padding: 15px; background: #e8f4f8; border-radius: 5px; border-left: 4px solid #3498db;">
                <strong><i class="fas fa-info-circle"></i> Payment Info:</strong>
                <p style="margin-top: 5px; font-size: 0.9rem; color: #2c3e50;">
                    Recorded on: ${p.created_at ? formatDate(p.created_at) : '-'}
                    ${p.updated_at ? `<br>Last updated: ${formatDate(p.updated_at)}` : ''}
                </p>
            </div>
        </div>
    `;

    // Store current payment ID for reversal
    window.currentPaymentId = p.id;

    const modal = document.getElementById('paymentModal');
    const details = document.getElementById('paymentDetails');
    const overlay = document.getElementById('modalOverlay');

    if (modal && details) {
        details.innerHTML = detailsHtml;
        modal.style.display = 'block';
        if (overlay) overlay.style.display = 'block';
    } else {
        showNotification('View details: ' + p.id, 'info');
    }
}

/**
 * Close payment modal
 */
function closePaymentModal() {
    const modal = document.getElementById('paymentModal');
    const overlay = document.getElementById('modalOverlay');
    if (modal) modal.style.display = 'none';
    if (overlay) overlay.style.display = 'none';
}

// ====== REVERSAL FUNCTIONS ======
/**
 * Show reverse modal
 */
function showReverseModal(paymentId, amount) {
    document.getElementById('reverse_payment_id').value = paymentId;
    document.getElementById('reverse_amount').value = amount.toLocaleString();
    document.getElementById('reverseModal').style.display = 'block';
    document.getElementById('modalOverlay').style.display = 'block';
    window.currentPaymentId = paymentId;
}

/**
 * Close reverse modal
 */
function closeReverseModal() {
    document.getElementById('reverseModal').style.display = 'none';
    document.getElementById('modalOverlay').style.display = 'none';
    document.getElementById('reverseForm').reset();
    window.currentPaymentId = null;
}

/**
 * Reverse a payment
 */
function reversePayment() {
    if (!window.currentPaymentId) {
        showNotification('No payment selected', 'error');
        return;
    }
    closePaymentModal();
    // Get payment amount
    const payment = paymentsData.find(p => p.id === window.currentPaymentId);
    if (payment) {
        showReverseModal(window.currentPaymentId, payment.amount);
    }
}

/**
 * Process reversal
 */
async function processReversal() {
    const paymentId = document.getElementById('reverse_payment_id').value;
    const reason = document.getElementById('reverse_reason').value;
    const remarks = document.getElementById('reverse_remarks').value;

    if (!reason) {
        showNotification('Please select a reason for reversal', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/payments/${paymentId}/reverse`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                reason: reason,
                remarks: remarks || ''
            })
        });

        if (response.status === 401) {
            showNotification('Session expired. Please login again', 'error');
            setTimeout(() => {
                window.location.href = '/admin/login.html';
            }, 2000);
            return;
        }

        const data = await response.json();

        if (data.success) {
            showNotification('Payment reversed successfully!', 'success');
            closeReverseModal();
            await loadPayments();
            await updatePaymentStats();
        } else {
            showNotification('Error: ' + (data.error || 'Could not reverse payment'), 'error');
        }
    } catch (error) {
        console.error('Reversal error:', error);
        // Demo mode fallback
        showNotification('Payment reversed (demo mode)', 'success');
        closeReverseModal();
        loadPayments();
        updatePaymentStats();
    }
}

// ====== PRINT RECEIPT ======
/**
 * Print payment receipt
 */
function printPaymentReceipt() {
    const content = document.getElementById('paymentDetails')?.innerHTML;
    if (!content) {
        showNotification('No payment details to print', 'warning');
        return;
    }

    const printWindow = window.open('', '_blank');
    if (!printWindow) {
        showNotification('Please allow popups for printing', 'warning');
        return;
    }

    printWindow.document.write(`
        <html><head><title>Payment Receipt</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 30px; }
            .receipt-header { text-align: center; margin-bottom: 30px; }
            .receipt-header h1 { color: #2c3e50; }
            .receipt-header h2 { color: #3498db; }
            .detail-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
            .detail-item { padding: 10px; background: #f8f9fa; border-radius: 5px; }
            .detail-item strong { display: block; color: #7f8c8d; margin-bottom: 5px; }
            .status-badge { padding: 5px 12px; border-radius: 20px; display: inline-block; }
            .status-active { background: #d4edda; color: #155724; }
            @media print { body { padding: 15px; } }
        </style>
        </head>
        <body>
            <div class="receipt-header">
                <h1>Alhudha Haj Travel</h1>
                <h2>Payment Receipt</h2>
                <p>Date: ${new Date().toLocaleDateString()}</p>
            </div>
            ${content}
            <p style="text-align: center; margin-top: 40px; color: #7f8c8d;">This is a computer generated receipt</p>
        </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

// ====== EXPORT FUNCTIONS ======
/**
 * Export payments to Excel/CSV
 */
function exportPaymentsToExcel() {
    const data = filteredPaymentsData.length > 0 ? filteredPaymentsData : paymentsData;
    if (!data || data.length === 0) {
        showNotification('No payments to export', 'warning');
        return;
    }

    const headers = ['ID', 'Traveler Name', 'Passport Number', 'Batch', 'Installment',
        'Amount', 'Payment Date', 'Due Date', 'Method', 'Transaction ID', 'Status', 'Remarks'];

    const rows = data.map(p => {
        const travelerName = p.first_name ? `${p.first_name} ${p.last_name || ''}`.trim() : (p.traveler_name || '');
        return [
            p.id || '',
            travelerName,
            p.passport_no || '',
            p.batch_name || '',
            p.installment || '',
            p.amount || 0,
            p.payment_date || '',
            p.due_date || '',
            p.payment_method || '',
            p.reference || p.transaction_id || '',
            p.status || '',
            (p.notes || '').replace(/"/g, '""')
        ];
    });

    let csv = headers.map(h => `"${h}"`).join(',') + '\n';
    csv += rows.map(row => row.map(v => `"${v}"`).join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `payments_export_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    showNotification(`Exported ${data.length} payments to CSV`, 'success');
}

/**
 * Print payments table
 */
function printPaymentsTable() {
    const table = document.getElementById('paymentsTable');
    if (!table) {
        showNotification('Table not found', 'warning');
        return;
    }

    const printWindow = window.open('', '_blank');
    if (!printWindow) {
        showNotification('Please allow popups for printing', 'warning');
        return;
    }

    printWindow.document.write(`
        <html><head><title>Payments List</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th { background: #2c3e50; color: white; padding: 10px; text-align: left; }
            td { padding: 10px; border: 1px solid #ddd; }
            .status-badge { padding: 5px 12px; border-radius: 20px; display: inline-block; }
            .status-active { background: #d4edda; color: #155724; }
            .status-pending { background: #fff3cd; color: #856404; }
            .status-inactive { background: #f8d7da; color: #721c24; }
            @media print { th { background: #2c3e50 !important; color: white !important; } }
        </style>
        </head>
        <body>
            <h2>Alhudha Haj Travel - Payments List</h2>
            <p>Generated on: ${new Date().toLocaleString()}</p>
            ${table.outerHTML}
        </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

// ====== UI HELPERS ======
/**
 * Show loading state
 */
function showLoading(btn, text) {
    if (!btn) return;
    btn.disabled = true;
    const icon = btn.querySelector('i');
    if (icon) {
        icon.className = 'fas fa-spinner fa-spin';
    }
    btn.textContent = text || 'Loading...';
}

/**
 * Hide loading state
 */
function hideLoading(btn) {
    if (!btn) return;
    btn.disabled = false;
    const icon = btn.querySelector('i');
    if (icon) {
        icon.className = 'fas fa-save';
    }
    btn.textContent = btn.textContent.replace('Loading...', 'Save');
    btn.textContent = btn.textContent.replace('Updating...', 'Update');
    btn.textContent = btn.textContent.replace('Recording...', 'Record');
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format date
 */
function formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return dateStr;
        return date.toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch (e) {
        return dateStr;
    }
}

// ====== NOTIFICATION ======
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    if (!notification) {
        console.log(`${type.toUpperCase()}: ${message}`);
        return;
    }

    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };

    notification.className = `notification notification-${type}`;
    notification.innerHTML = `<i class="fas fa-${icons[type] || 'info-circle'}"></i> ${message}`;
    notification.style.display = 'block';

    if (window.notificationTimeout) {
        clearTimeout(window.notificationTimeout);
    }

    window.notificationTimeout = setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

// ====== INITIALIZATION ======
/**
 * Initialize page with session check
 */
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Payments page initializing...');
    try {
        if (typeof SessionManager !== 'undefined') {
            await SessionManager.initPage(initializePage);
        } else {
            initializePage();
        }
    } catch (error) {
        console.error('Failed to initialize page:', error);
        showNotification('Failed to load page', 'error');
    }
});

async function initializePage() {
    console.log('📋 Initializing page...');
    resetSessionTimer();

    // Monitor user activity
    ['click', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
        document.addEventListener(event, resetSessionTimer);
    });

    // Load data
    await Promise.all([
        loadTravelers(),
        loadBatches(),
        loadPayments(),
        updatePaymentStats()
    ]);

    // Set today's date for payment form
    setTodayDate();

    // Set up search listeners
    const searchEl = document.getElementById('searchPayments');
    if (searchEl) {
        searchEl.addEventListener('input', function() {
            filterPayments();
        });
    }

    const statusEl = document.getElementById('paymentStatusFilter');
    const methodEl = document.getElementById('paymentMethodFilter');
    if (statusEl) statusEl.addEventListener('change', filterPayments);
    if (methodEl) methodEl.addEventListener('change', filterPayments);

    console.log('✅ Payments page loaded successfully!');
}

/**
 * Load travelers for dropdown
 */
async function loadTravelers() {
    try {
        const response = await fetch('/api/travelers', {
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        });
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.travelers) {
                travelersData = data.travelers;
                updateTravelerDropdown();
            }
        }
    } catch (error) {
        console.error('Error loading travelers:', error);
    }
}

/**
 * Update traveler dropdown
 */
function updateTravelerDropdown() {
    const dropdown = document.getElementById('traveler_dropdown');
    if (!dropdown) return;

    dropdown.innerHTML = '<option value="">-- Select Traveler --</option>';
    travelersData.forEach(t => {
        dropdown.innerHTML += `<option value="${t.id}" data-passport="${t.passport_no}" data-batch="${t.batch_id}">${t.first_name} ${t.last_name} (${t.passport_no})</option>`;
    });
}

/**
 * Load batches for dropdown
 */
async function loadBatches() {
    try {
        const response = await fetch('/api/batches', {
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        });
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.batches) {
                batchesData = data.batches;
            }
        }
    } catch (error) {
        console.error('Error loading batches:', error);
    }
}

/**
 * Set today's date
 */
function setTodayDate() {
    const today = new Date().toISOString().split('T')[0];
    const dateEl = document.getElementById('payment_date');
    if (dateEl) dateEl.value = today;
}

// ====== FORM FUNCTIONS ======
/**
 * Show add payment form
 */
function showAddPaymentForm() {
    const form = document.getElementById('addPaymentForm');
    if (form) {
        form.style.display = 'block';
        document.getElementById('paymentSearchSection').style.display = 'block';
        document.getElementById('paymentForm').style.display = 'none';
        document.getElementById('payment_search').value = '';
        document.getElementById('traveler_dropdown').value = '';
        resetPaymentForm();
        setTodayDate();
        form.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Hide add payment form
 */
function hideAddPaymentForm() {
    const form = document.getElementById('addPaymentForm');
    if (form) form.style.display = 'none';
    resetPaymentForm();
    window.currentTravelerData = null;
}

/**
 * Reset payment form
 */
function resetPaymentForm() {
    const form = document.getElementById('paymentForm');
    if (form) form.reset();
    document.getElementById('payment_traveler_id').value = '';
    document.getElementById('payment_traveler_name').value = '';
    document.getElementById('payment_batch_id').value = '';
    document.getElementById('display_traveler_name').textContent = '-';
    document.getElementById('display_passport').textContent = '-';
    document.getElementById('display_batch_name').textContent = '-';
    document.getElementById('display_batch_price').textContent = '0';
    document.getElementById('display_total_paid').innerHTML = '₹0';
    document.getElementById('display_balance').innerHTML = '₹0';
    document.getElementById('summary_price').innerHTML = '₹0';
    document.getElementById('summary_paid').innerHTML = '₹0';
    document.getElementById('summary_new').innerHTML = '₹0';
    document.getElementById('summary_balance').innerHTML = '₹0';
    setTodayDate();
}

/**
 * Reset verification
 */
function resetVerification() {
    document.getElementById('paymentSearchSection').style.display = 'block';
    document.getElementById('paymentForm').style.display = 'none';
    document.getElementById('payment_search').value = '';
    document.getElementById('traveler_dropdown').value = '';
    resetPaymentForm();
    window.currentTravelerData = null;
}

/**
 * Select traveler from dropdown
 */
function selectTravelerFromDropdown() {
    const dropdown = document.getElementById('traveler_dropdown');
    const selectedOption = dropdown.options[dropdown.selectedIndex];
    if (!selectedOption.value) return;
    document.getElementById('payment_search').value = selectedOption.value;
    verifyTraveler();
}

/**
 * Verify traveler
 */
async function verifyTraveler() {
    const search = document.getElementById('payment_search')?.value?.trim() || '';
    if (!search) {
        showNotification('Please enter Traveler ID or Passport Number', 'error');
        return;
    }

    try {
        let traveler;
        if (!isNaN(search)) {
            traveler = travelersData.find(t => t.id == search);
        } else {
            traveler = travelersData.find(t => t.passport_no === search);
        }

        if (traveler) {
            await loadTravelerDetails(traveler);
        } else {
            // Try API
            let response;
            if (!isNaN(search)) {
                response = await fetch(`/api/travelers/${search}`, { credentials: 'include' });
            } else {
                response = await fetch(`/api/travelers/passport/${encodeURIComponent(search)}`, { credentials: 'include' });
            }

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    traveler = data.traveler;
                    await loadTravelerDetails(traveler);
                } else {
                    showNotification('Traveler not found', 'error');
                }
            } else {
                showNotification('Traveler not found. Please check the ID or Passport Number.', 'error');
            }
        }
    } catch (error) {
        console.error('Error verifying traveler:', error);
        showNotification('Error verifying traveler', 'error');
    }
}

/**
 * Load traveler details
 */
async function loadTravelerDetails(traveler) {
    const batch = batchesData.find(b => b.id == traveler.batch_id);
    let payments = [];

    try {
        const response = await fetch(`/api/payments/traveler/${traveler.id}`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                payments = data.payments || [];
            }
        }
    } catch (error) {
        console.error('Error loading payments:', error);
    }

    const totalPaid = payments
        .filter(p => p.status === 'completed')
        .reduce((sum, p) => sum + (parseFloat(p.amount) || 0), 0);

    const packagePrice = batch ? parseFloat(batch.price || 0) : 0;
    const balance = packagePrice - totalPaid;

    window.currentTravelerData = {
        ...traveler,
        batch: batch,
        payments: payments,
        totalPaid: totalPaid,
        packagePrice: packagePrice,
        balance: balance
    };

    document.getElementById('payment_traveler_id').value = traveler.id;
    document.getElementById('payment_traveler_name').value = `${traveler.first_name} ${traveler.last_name}`;
    document.getElementById('payment_batch_id').value = traveler.batch_id || '';

    document.getElementById('display_traveler_name').textContent = `${traveler.first_name} ${traveler.last_name}`;
    document.getElementById('display_passport').textContent = traveler.passport_no || '-';
    document.getElementById('display_batch_name').textContent = batch ? batch.batch_name : 'Not Assigned';
    document.getElementById('display_batch_price').textContent = packagePrice.toLocaleString('en-IN', { minimumFractionDigits: 2 });
    document.getElementById('display_total_paid').innerHTML = `₹${totalPaid.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

    const balanceEl = document.getElementById('display_balance');
    balanceEl.innerHTML = `₹${balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    balanceEl.className = balance <= 0 ? 'value positive' : 'value negative';

    document.getElementById('summary_price').innerHTML = `₹${packagePrice.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    document.getElementById('summary_paid').innerHTML = `₹${totalPaid.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    updateSummary();

    document.getElementById('paymentSearchSection').style.display = 'none';
    document.getElementById('paymentForm').style.display = 'block';
}

/**
 * Update payment summary
 */
function updateSummary() {
    const amountText = document.getElementById('amount')?.value?.replace(/,/g, '') || '';
    const amount = parseFloat(amountText) || 0;
    const totalPaid = parseFloat(window.currentTravelerData?.totalPaid || 0);
    const packagePrice = parseFloat(window.currentTravelerData?.packagePrice || 0);

    const summaryNew = document.getElementById('summary_new');
    const summaryBalance = document.getElementById('summary_balance');

    if (summaryNew) {
        summaryNew.innerHTML = `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    }

    if (summaryBalance) {
        const newBalance = packagePrice - (totalPaid + amount);
        if (newBalance < 0) {
            summaryBalance.style.color = '#e74c3c';
            summaryBalance.innerHTML = `₹${Math.abs(newBalance).toLocaleString('en-IN', { minimumFractionDigits: 2 })} (Overpaid)`;
        } else if (newBalance === 0) {
            summaryBalance.style.color = '#27ae60';
            summaryBalance.innerHTML = '₹0.00 (Paid in Full)';
        } else {
            summaryBalance.style.color = '#f39c12';
            summaryBalance.innerHTML = `₹${newBalance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
        }
    }
}

// ====== RECORD PAYMENT ======
/**
 * Record a new payment
 */
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('paymentForm');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            const amountText = document.getElementById('amount')?.value?.replace(/,/g, '') || '';
            const amount = parseFloat(amountText);
            if (amount <= 0) {
                showNotification('Please enter a valid amount greater than 0', 'error');
                return;
            }
            if (!window.currentTravelerData) {
                showNotification('Please verify a traveler first', 'error');
                return;
            }

            const paymentData = {
                traveler_id: document.getElementById('payment_traveler_id').value,
                batch_id: document.getElementById('payment_batch_id').value,
                amount: amount,
                payment_date: document.getElementById('payment_date').value,
                payment_method: document.getElementById('payment_method').value,
                installment: document.getElementById('installment').value,
                transaction_id: document.getElementById('transaction_id').value?.trim() || null,
                due_date: document.getElementById('due_date').value || null,
                remarks: document.getElementById('remarks').value?.trim() || null,
                status: 'completed'
            };

            if (!paymentData.traveler_id || !paymentData.batch_id) {
                showNotification('Please verify a traveler first', 'error');
                return;
            }
            if (!paymentData.payment_date) {
                showNotification('Payment date is required', 'error');
                return;
            }
            if (!paymentData.payment_method) {
                showNotification('Payment method is required', 'error');
                return;
            }

            const submitBtn = this.querySelector('button[type="submit"]');
            showLoading(submitBtn, 'Recording...');

            try {
                const response = await fetch('/api/payments', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify(paymentData)
                });

                if (response.status === 401) {
                    showNotification('Session expired. Please login again', 'error');
                    setTimeout(() => {
                        window.location.href = '/admin/login.html';
                    }, 2000);
                    return;
                }

                const data = await response.json();

                if (data.success) {
                    showNotification(`Payment of ₹${amount.toLocaleString()} recorded successfully!`, 'success');
                    hideAddPaymentForm();
                    await loadPayments();
                    await updatePaymentStats();
                } else {
                    showNotification('Error: ' + (data.error || 'Could not record payment'), 'error');
                }
            } catch (error) {
                console.error('Error recording payment:', error);
                // Demo mode fallback
                showNotification('Payment recorded (demo mode)', 'success');
                hideAddPaymentForm();
                loadPayments();
                updatePaymentStats();
            } finally {
                hideLoading(submitBtn);
            }
        });
    }

    // Amount input event listener
    const amountEl = document.getElementById('amount');
    if (amountEl) {
        amountEl.addEventListener('input', updateSummary);
    }

    // Number validation for amount
    const amountInput = document.getElementById('amount');
    if (amountInput) {
        amountInput.addEventListener('keypress', function(e) {
            const key = e.keyCode || e.which;
            if (key == 8 || key == 9 || key == 13 || key == 27 || key == 46 ||
                (key >= 35 && key <= 40) || (key >= 48 && key <= 57) ||
                (key >= 96 && key <= 105)) {
                return true;
            }
            return false;
        });
    }
});

// ====== CLOSE ALL MODALS ======
function closeAllModals() {
    closePaymentModal();
    closeReverseModal();
}

// ====== SESSION TIMER ======
function resetSessionTimer() {
    // Will be overridden by session-manager.js
    console.log('Session timer reset');
}

// ====== LOGOUT ======
async function logout() {
    if (confirm('Are you sure you want to logout?')) {
        if (typeof SessionManager !== 'undefined' && SessionManager.logout) {
            await SessionManager.logout();
        } else {
            sessionStorage.clear();
            window.location.href = '/admin/login.html';
        }
    }
}

// ====== EXPOSE GLOBALS ======
window.loadPayments = loadPayments;
window.filterPayments = filterPayments;
window.resetFilters = resetFilters;
window.previousPage = previousPage;
window.nextPage = nextPage;
window.showAddPaymentForm = showAddPaymentForm;
window.hideAddPaymentForm = hideAddPaymentForm;
window.verifyTraveler = verifyTraveler;
window.selectTravelerFromDropdown = selectTravelerFromDropdown;
window.resetVerification = resetVerification;
window.viewPaymentDetails = viewPaymentDetails;
window.closePaymentModal = closePaymentModal;
window.showReverseModal = showReverseModal;
window.closeReverseModal = closeReverseModal;
window.reversePayment = reversePayment;
window.processReversal = processReversal;
window.printPaymentReceipt = printPaymentReceipt;
window.exportPaymentsToExcel = exportPaymentsToExcel;
window.printPaymentsTable = printPaymentsTable;
window.closeAllModals = closeAllModals;
window.showNotification = showNotification;
window.logout = logout;

console.log('✅ payments.js loaded successfully!');
