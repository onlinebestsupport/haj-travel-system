/**
 * invoices.js - Invoice management functions
 * Alhudha Haj Travel Admin Panel
 */

'use strict';

// ====== STATE ======
let invoicesData = [];
let invoicesFiltered = [];
let invoicesCurrentPage = 1;
const invoicesPerPage = 10;
let invoicesCurrentEditId = null;
let invoicesTravelers = [];
let invoicesBatches = [];

// ====== LOAD INVOICES ======
/**
 * Fetch all invoices from /api/invoices
 */
async function loadInvoices() {
    const tableBody = document.getElementById('invoicesTableBody');
    if (tableBody) {
        tableBody.innerHTML = '<tr><td colspan="7" class="loading"><i class="fas fa-spinner fa-spin"></i> Loading invoices...</td></tr>';
    }

    try {
        const data = await makeAPICall('GET', '/api/invoices');
        if (data.success && Array.isArray(data.invoices)) {
            invoicesData = data.invoices;
            invoicesFiltered = [...invoicesData];
            console.log(`✅ Loaded ${invoicesData.length} invoices`);
        } else {
            invoicesData = [];
            invoicesFiltered = [];
        }
    } catch (error) {
        handleAPIError(error, 'loadInvoices');
        invoicesData = [];
        invoicesFiltered = [];
    }

    displayInvoices();
    updateInvoiceStats();
}

// ====== DISPLAY INVOICES ======
/**
 * Render the invoices table with GST/TCS calculations
 */
function displayInvoices() {
    const tableBody = document.getElementById('invoicesTableBody');
    if (!tableBody) return;

    if (!invoicesFiltered || invoicesFiltered.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;">No invoices found</td></tr>';
        updatePaginationDisplay(0, 1, invoicesPerPage);
        return;
    }

    const start = (invoicesCurrentPage - 1) * invoicesPerPage;
    const end = start + invoicesPerPage;
    const pageData = invoicesFiltered.slice(start, end);

    let html = '';
    pageData.forEach(inv => {
        const travelerName = inv.traveler_name || inv.first_name ?
            `${inv.first_name || ''} ${inv.last_name || ''}`.trim() : '-';
        const statusClass = getStatusClass(inv.status);
        const statusText = inv.status === 'paid' ? 'Paid' : 'Pending';
        const amount = formatCurrency(inv.amount || inv.total_amount || 0);

        html += `<tr>
            <td>${escapeHtml(inv.invoice_number || String(inv.id))}</td>
            <td>${formatDate(inv.created_at || inv.invoice_date)}</td>
            <td>${escapeHtml(travelerName)}</td>
            <td>${escapeHtml(inv.batch_name || '-')}</td>
            <td><strong>${amount}</strong></td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td class="invoice-actions">
                <button class="icon-btn btn-view" onclick="viewInvoiceDetails(${inv.id})" title="View"><i class="fas fa-eye"></i></button>
                <button class="icon-btn btn-edit" onclick="editInvoice(${inv.id})" title="Edit"><i class="fas fa-edit"></i></button>
                <button class="icon-btn btn-delete" onclick="deleteInvoice(${inv.id})" title="Delete"><i class="fas fa-trash"></i></button>
            </td>
        </tr>`;
    });

    tableBody.innerHTML = html;
    updatePaginationDisplay(invoicesFiltered.length, invoicesCurrentPage, invoicesPerPage);
}

// ====== FILTER INVOICES ======
/**
 * Filter invoices by number, traveler, or status
 */
function filterInvoices() {
    const search = (document.getElementById('searchInput')?.value || '').toLowerCase().trim();
    const statusFilter = document.getElementById('statusFilter')?.value || 'all';

    invoicesFiltered = invoicesData.filter(inv => {
        const travelerName = `${inv.first_name || ''} ${inv.last_name || ''}`.toLowerCase();
        const invoiceNum = (inv.invoice_number || String(inv.id)).toLowerCase();
        const matchesSearch = !search || travelerName.includes(search) || invoiceNum.includes(search);
        const matchesStatus = statusFilter === 'all' || (inv.status || '').toLowerCase() === statusFilter.toLowerCase();
        return matchesSearch && matchesStatus;
    });

    invoicesCurrentPage = 1;
    displayInvoices();
    showNotification(`Found ${invoicesFiltered.length} invoice(s)`, 'info');
}

// ====== CREATE INVOICE ======
/**
 * POST a new invoice with GST and TCS calculations
 */
async function createInvoice() {
    const travelerId = document.getElementById('travelerId')?.value;
    if (!travelerId) { showNotification('Please select a traveler', 'error'); return; }

    const baseAmount = parseFloat(document.getElementById('baseAmount')?.value || 0);
    const gstPercent = parseFloat(document.getElementById('gstPercent')?.value || 5);
    const tcsPercent = parseFloat(document.getElementById('tcsPercent')?.value || 1);
    const dueDate = document.getElementById('dueDate')?.value;
    const status = document.getElementById('status')?.value || 'pending';

    if (!baseAmount || baseAmount <= 0) {
        showNotification('Base amount must be greater than 0', 'error'); return;
    }

    const gstAmount = (baseAmount * gstPercent) / 100;
    const subtotal = baseAmount + gstAmount;
    const tcsAmount = (subtotal * tcsPercent) / 100;
    const totalAmount = subtotal + tcsAmount;

    const invoiceData = {
        traveler_id: travelerId,
        base_amount: baseAmount,
        gst_percent: gstPercent,
        gst_amount: gstAmount,
        tcs_percent: tcsPercent,
        tcs_amount: tcsAmount,
        amount: totalAmount,
        due_date: dueDate || null,
        status: status
    };

    const submitBtn = document.querySelector('#createForm button[type="submit"]');
    showLoading(submitBtn, 'Creating...');

    try {
        const data = await makeAPICall('POST', '/api/invoices', invoiceData);
        if (data.success) {
            showNotification('Invoice created successfully!', 'success');
            if (typeof closeCreateModal === 'function') closeCreateModal();
            await loadInvoices();
        } else {
            showNotification('Error: ' + (data.error || 'Could not create invoice'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'createInvoice');
    } finally {
        hideLoading(submitBtn);
    }
}

// ====== EDIT INVOICE ======
/**
 * Load invoice data into the edit form
 * @param {number} id
 */
function editInvoice(id) {
    const invoice = invoicesData.find(i => i.id === id);
    if (!invoice) { showNotification('Invoice not found', 'error'); return; }

    invoicesCurrentEditId = id;

    const set = (elId, val) => { const el = document.getElementById(elId); if (el) el.value = val || ''; };
    set('editId', invoice.id);
    set('editInvoiceNumber', invoice.invoice_number || invoice.id);
    set('editDate', formatDate(invoice.created_at || invoice.invoice_date));
    const travelerName = invoice.first_name ? `${invoice.first_name} ${invoice.last_name || ''}`.trim() : '-';
    set('editTraveler', travelerName);
    set('editBatch', invoice.batch_name || '-');
    set('editAmount', invoice.amount || invoice.total_amount || 0);
    set('editStatus', invoice.status || 'pending');
    set('editDueDate', formatDateForInput(invoice.due_date));

    const editModal = document.getElementById('editModal');
    if (editModal) {
        editModal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

// ====== UPDATE INVOICE ======
/**
 * PUT updated invoice data
 */
async function updateInvoice() {
    if (!invoicesCurrentEditId) {
        showNotification('No invoice selected for editing', 'error'); return;
    }

    const amount = parseFloat(document.getElementById('editAmount')?.value || 0);
    if (!amount || amount <= 0) {
        showNotification('Amount must be greater than 0', 'error'); return;
    }

    const invoiceData = {
        amount: amount,
        status: document.getElementById('editStatus')?.value || 'pending',
        due_date: document.getElementById('editDueDate')?.value || null
    };

    const submitBtn = document.querySelector('#editForm button[type="submit"]');
    showLoading(submitBtn, 'Saving...');

    try {
        const data = await makeAPICall('PUT', `/api/invoices/${invoicesCurrentEditId}`, invoiceData);
        if (data.success) {
            showNotification('Invoice updated successfully!', 'success');
            if (typeof closeEditModal === 'function') closeEditModal();
            invoicesCurrentEditId = null;
            await loadInvoices();
        } else {
            showNotification('Error: ' + (data.error || 'Update failed'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'updateInvoice');
    } finally {
        hideLoading(submitBtn);
    }
}

// ====== DELETE INVOICE ======
/**
 * DELETE an invoice by ID
 * @param {number} id
 */
async function deleteInvoice(id) {
    if (!confirm('Are you sure you want to delete this invoice?')) return;

    try {
        const data = await makeAPICall('DELETE', `/api/invoices/${id}`);
        if (data.success) {
            showNotification('Invoice deleted successfully!', 'success');
            await loadInvoices();
        } else {
            showNotification('Error: ' + (data.error || 'Could not delete invoice'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'deleteInvoice');
    }
}

// ====== VIEW INVOICE DETAILS ======
/**
 * Show a modal with full invoice breakdown
 * @param {number} id
 */
function viewInvoiceDetails(id) {
    const inv = invoicesData.find(i => i.id === id);
    if (!inv) { showNotification('Invoice not found', 'error'); return; }

    const travelerName = inv.first_name ? `${inv.first_name} ${inv.last_name || ''}`.trim() : '-';
    const baseAmount = inv.base_amount || 0;
    const gstAmount = inv.gst_amount || 0;
    const tcsAmount = inv.tcs_amount || 0;
    const totalAmount = inv.amount || inv.total_amount || 0;

    const detailsHtml = `
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:15px;margin-bottom:20px;">
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Invoice #:</strong><br>${escapeHtml(inv.invoice_number || String(inv.id))}
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Date:</strong><br>${formatDate(inv.created_at || inv.invoice_date)}
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Traveler:</strong><br>${escapeHtml(travelerName)}
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Batch:</strong><br>${escapeHtml(inv.batch_name || '-')}
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Due Date:</strong><br>${inv.due_date ? formatDate(inv.due_date) : 'N/A'}
            </div>
            <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                <strong>Status:</strong><br>
                <span class="status-badge ${getStatusClass(inv.status)}">${inv.status === 'paid' ? 'Paid' : 'Pending'}</span>
            </div>
        </div>
        <div style="background:#f8f9fa;padding:20px;border-radius:10px;border:2px solid #d4af37;">
            <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #ecf0f1;">
                <span>Base Amount:</span><strong>${formatCurrency(baseAmount)}</strong>
            </div>
            <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #ecf0f1;">
                <span>GST (${inv.gst_percent || 5}%):</span><strong>${formatCurrency(gstAmount)}</strong>
            </div>
            <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #ecf0f1;">
                <span>Subtotal:</span><strong>${formatCurrency(baseAmount + gstAmount)}</strong>
            </div>
            <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #ecf0f1;">
                <span>TCS (${inv.tcs_percent || 1}%):</span><strong>${formatCurrency(tcsAmount)}</strong>
            </div>
            <div style="display:flex;justify-content:space-between;padding:12px 0;font-size:1.2rem;font-weight:bold;color:#27ae60;border-top:2px solid #d4af37;margin-top:8px;">
                <span>TOTAL:</span><strong>${formatCurrency(totalAmount)}</strong>
            </div>
        </div>`;

    const existingModal = document.getElementById('viewModal');
    const existingDetails = document.getElementById('viewDetails');

    if (existingModal && existingDetails) {
        existingDetails.innerHTML = detailsHtml;
        existingModal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    } else {
        showModal(`<i class="fas fa-file-invoice"></i> Invoice #${inv.invoice_number || inv.id}`, detailsHtml,
            `<button class="action-btn btn-secondary" onclick="closeModal()">Close</button>`);
    }
}

// ====== EXPORT TO CSV ======
/**
 * Export all invoices to a CSV file
 */
function exportInvoicesToCSV() {
    const dataToExport = invoicesFiltered.length ? invoicesFiltered : invoicesData;
    if (!dataToExport.length) { showNotification('No invoices to export', 'warning'); return; }

    const headers = ['Invoice #', 'Date', 'Traveler', 'Batch', 'Base Amount',
        'GST %', 'GST Amount', 'TCS %', 'TCS Amount', 'Total Amount', 'Status', 'Due Date'];

    const rows = [headers, ...dataToExport.map(inv => {
        const travelerName = inv.first_name ? `${inv.first_name} ${inv.last_name || ''}`.trim() : '-';
        return [
            inv.invoice_number || inv.id, inv.created_at || inv.invoice_date, travelerName,
            inv.batch_name, inv.base_amount, inv.gst_percent, inv.gst_amount,
            inv.tcs_percent, inv.tcs_amount, inv.amount || inv.total_amount,
            inv.status, inv.due_date
        ];
    })];

    downloadCSV(rows, `invoices_${new Date().toISOString().slice(0, 10)}.csv`);
    showNotification(`Exported ${dataToExport.length} invoices to CSV`, 'success');
}

// ====== GENERATE INVOICE PDF ======
/**
 * Generate a PDF for an invoice
 * @param {number} id
 */
function generateInvoicePDF(id) {
    const inv = invoicesData.find(i => i.id === id);
    if (!inv) { showNotification('Invoice not found', 'error'); return; }

    const travelerName = inv.first_name ? `${inv.first_name} ${inv.last_name || ''}`.trim() : '-';
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html><head><title>Invoice #${inv.invoice_number || inv.id}</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 30px; }
            h1 { color: #1a472a; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th { background: #1a472a; color: white; padding: 10px; }
            td { padding: 10px; border: 1px solid #ddd; }
            .total { font-size: 1.2rem; font-weight: bold; color: #27ae60; }
        </style></head>
        <body>
            <h1>Alhudha Haj Travel - Invoice</h1>
            <p><strong>Invoice #:</strong> ${escapeHtml(inv.invoice_number || String(inv.id))}</p>
            <p><strong>Date:</strong> ${formatDate(inv.created_at)}</p>
            <p><strong>Traveler:</strong> ${escapeHtml(travelerName)}</p>
            <p><strong>Batch:</strong> ${escapeHtml(inv.batch_name || '-')}</p>
            <table>
                <tr><th>Description</th><th>Amount</th></tr>
                <tr><td>Base Amount</td><td>${formatCurrency(inv.base_amount || 0)}</td></tr>
                <tr><td>GST (${inv.gst_percent || 5}%)</td><td>${formatCurrency(inv.gst_amount || 0)}</td></tr>
                <tr><td>TCS (${inv.tcs_percent || 1}%)</td><td>${formatCurrency(inv.tcs_amount || 0)}</td></tr>
                <tr><td class="total">TOTAL</td><td class="total">${formatCurrency(inv.amount || inv.total_amount || 0)}</td></tr>
            </table>
        </body></html>`);
    printWindow.document.close();
    printWindow.print();
    showNotification('Invoice PDF generated', 'success');
}

// ====== STATS ======
function updateInvoiceStats() {
    const total = invoicesData.length;
    const paid = invoicesData.filter(i => i.status === 'paid').length;
    const pending = invoicesData.filter(i => i.status !== 'paid').length;
    const totalAmount = invoicesData.reduce((s, i) => s + (i.amount || i.total_amount || 0), 0);

    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalInvoices', total);
    setEl('paidInvoices', paid);
    setEl('pendingInvoices', pending);
    setEl('totalAmount', formatCurrency(totalAmount));
}

// ====== PAGINATION ======
function invoicesPrevPage() {
    if (invoicesCurrentPage > 1) { invoicesCurrentPage--; displayInvoices(); }
}
function invoicesNextPage() {
    if (invoicesCurrentPage * invoicesPerPage < invoicesFiltered.length) { invoicesCurrentPage++; displayInvoices(); }
}

function prevPage() { invoicesPrevPage(); }
function nextPage() { invoicesNextPage(); }

function applyFilters() { filterInvoices(); }
function resetFilters() {
    const searchEl = document.getElementById('searchInput');
    const statusEl = document.getElementById('statusFilter');
    if (searchEl) searchEl.value = '';
    if (statusEl) statusEl.value = 'all';
    invoicesFiltered = [...invoicesData];
    invoicesCurrentPage = 1;
    displayInvoices();
    showNotification('Filters reset', 'info');
}

function exportInvoices() { exportInvoicesToCSV(); }

console.log('✅ invoices.js loaded');
