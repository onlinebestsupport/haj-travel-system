/**
 * receipts.js - Receipt management functions
 * Alhudha Haj Travel Admin Panel
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

console.log('✅ receipts.js loaded');
