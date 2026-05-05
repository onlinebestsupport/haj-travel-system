/**
 * receipts.js - Receipt management functions
 * Alhudha Haj Travel Management System
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
