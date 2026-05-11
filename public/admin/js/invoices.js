/**
 * invoices.js - Invoice management functions
 * Alhudha Haj Travel Management System
 * invoices.js - Invoice Management for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 * API base: /api/invoices
 */

'use strict';

// Module-level state
let invoicesData = [];
let filteredInvoicesData = [];

// ====== LOAD INVOICES ======
/**
 * Fetch all invoices from the API and render them
 */
async function loadInvoices() {
    showLoading(true);
    try {
        const data = await makeApiCall('GET', '/api/invoices');
        invoicesData = Array.isArray(data) ? data : (data.invoices || []);
        filteredInvoicesData = [...invoicesData];
        displayInvoices(filteredInvoicesData);
        updateInvoiceStats(invoicesData);
        console.log(`✅ Loaded ${invoicesData.length} invoices`);
    } catch (error) {
        handleApiError(error, 'Load invoices');
    } finally {
        showLoading(false);
    }
}

// ====== DISPLAY INVOICES ======
/**
 * Render invoices array into the table
 * @param {Array} invoices
 */
function displayInvoices(invoices) {
    const tbody = document.getElementById('invoicesTableBody');
    if (!tbody) return;

    if (!invoices || invoices.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align:center;padding:40px;color:#95a5a6;">
                    <i class="fas fa-file-invoice" style="font-size:2rem;display:block;margin-bottom:10px;"></i>
                    No invoices found
                </td>
            </tr>`;
        return;
    }

    tbody.innerHTML = invoices.map(inv => {
        const status = inv.status || 'Pending';
        const statusClass = status.toLowerCase() === 'paid'    ? 'status-paid' :
                            status.toLowerCase() === 'pending' ? 'status-pending' : 'status-pending';
        const travelerName = inv.traveler_name ||
            `${inv.first_name || ''} ${inv.last_name || ''}`.trim() || `ID ${inv.traveler_id}`;
        return `
            <tr>
                <td>${escapeHtml(inv.invoice_number || `INV-${String(inv.id).padStart(6,'0')}`)}</td>
                <td>${formatDate(inv.invoice_date || inv.created_at)}</td>
                <td>${escapeHtml(travelerName)}</td>
                <td>${escapeHtml(inv.batch_name || inv.batch_id || '-')}</td>
                <td>${formatCurrency(inv.amount)}</td>
                <td><span class="status-badge ${statusClass}">${escapeHtml(status)}</span></td>
                <td>
                    <div class="invoice-actions">
                        <button class="icon-btn btn-view" onclick="viewInvoiceDetails(${inv.id})" title="View">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="icon-btn btn-edit" onclick="editInvoice(${inv.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="icon-btn" onclick="generateInvoicePDF(${inv.id})" title="Download PDF" style="color:#27ae60;">
                            <i class="fas fa-file-pdf"></i>
                        </button>
                        <button class="icon-btn btn-delete" onclick="deleteInvoice(${inv.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
    }).join('');
}

/**
 * Update invoice stat cards
 * @param {Array} invoices
 */
function updateInvoiceStats(invoices) {
    const total   = invoices.length;
    const paid    = invoices.filter(i => (i.status || '').toLowerCase() === 'paid').length;
    const pending = invoices.filter(i => (i.status || '').toLowerCase() !== 'paid').length;
    const revenue = invoices.filter(i => (i.status || '').toLowerCase() === 'paid')
                            .reduce((sum, i) => sum + parseFloat(i.amount || 0), 0);

    const els = {
        totalInvoices:   total,
        paidInvoices:    paid,
        pendingInvoices: pending,
        totalRevenue:    formatCurrency(revenue)
    };

    Object.entries(els).forEach(([id, val]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    });
}

// ====== FILTER INVOICES ======
/**
 * Filter invoices by invoice number, traveler, or status
 */
function filterInvoices() {
    const searchEl = document.getElementById('searchInvoices') || document.getElementById('invoiceSearch');
    const statusEl = document.getElementById('filterInvoiceStatus') || document.getElementById('statusFilter');
    const search   = searchEl ? searchEl.value.toLowerCase().trim() : '';
    const status   = statusEl ? statusEl.value.toLowerCase() : '';

    filteredInvoicesData = invoicesData.filter(inv => {
        const invNo        = (inv.invoice_number || '').toLowerCase();
        const travelerName = (inv.traveler_name || `${inv.first_name || ''} ${inv.last_name || ''}`).toLowerCase();
        const invStatus    = (inv.status || '').toLowerCase();

        const matchesSearch = !search ||
            invNo.includes(search) ||
            travelerName.includes(search) ||
            String(inv.amount || '').includes(search);

        const matchesStatus = !status || invStatus === status;

        return matchesSearch && matchesStatus;
    });

    displayInvoices(filteredInvoicesData);
}

// ====== CREATE INVOICE ======
/**
 * Submit a new invoice form to the API
 */
async function createInvoice() {
    const form = document.getElementById('invoiceForm') || document.getElementById('addInvoiceForm');
    if (!form) { showNotification('Invoice form not found', 'error'); return; }

    const formData = new FormData(form);
    const invoiceData = {};
    formData.forEach((value, key) => { if (value !== '') invoiceData[key] = value; });

    if (!invoiceData.traveler_id) {
        showNotification('Please select a traveler', 'error');
        return;
    }
    if (!invoiceData.amount || parseFloat(invoiceData.amount) <= 0) {
        showNotification('Please enter a valid amount', 'error');
        return;
    }

    showLoading(true);
    try {
        const result = await makeApiCall('POST', '/api/invoices', invoiceData);
        if (result.success || result.id) {
            showNotification('Invoice created successfully!', 'success');
            form.reset();
            const container = document.getElementById('addInvoiceForm') || document.getElementById('invoiceFormContainer');
            if (container) container.style.display = 'none';
            await loadInvoices();
        } else {
            showNotification(result.error || 'Failed to create invoice', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Create invoice');
    } finally {
        showLoading(false);
    }
}

// ====== EDIT INVOICE ======
/**
 * Load invoice data into the edit form
 * @param {number} invoiceId
 */
async function editInvoice(invoiceId) {
    showLoading(true);
    try {
        const response = await makeApiCall('GET', `/api/invoices/${invoiceId}`);
        const inv = response.invoice || response;

        const fields = [
            'traveler_id','batch_id','invoice_number','invoice_date',
            'amount','status','due_date','notes','description'
        ];

        fields.forEach(field => {
            const el = document.getElementById(`edit_${field}`) || document.getElementById(field);
            if (el && inv[field] !== undefined) el.value = inv[field];
        });

        const idField = document.getElementById('edit_invoice_id') || document.getElementById('editInvoiceId');
        if (idField) idField.value = invoiceId;

        const editForm = document.getElementById('editInvoiceForm') || document.getElementById('editInvoiceContainer');
        if (editForm) {
            editForm.style.display = 'block';
            editForm.scrollIntoView({ behavior: 'smooth' });
        }
    } catch (error) {
        handleApiError(error, 'Load invoice for editing');
    } finally {
        showLoading(false);
    }
}

// ====== UPDATE INVOICE ======
/**
 * Save changes to an existing invoice
 */
async function updateInvoice() {
    const idField = document.getElementById('edit_invoice_id') || document.getElementById('editInvoiceId');
    if (!idField || !idField.value) {
        showNotification('No invoice selected for update', 'error');
        return;
    }

    const invoiceId = idField.value;
    const form = document.getElementById('editInvoiceForm') || document.getElementById('editInvoiceContainer');
    if (!form) { showNotification('Edit form not found', 'error'); return; }

    const formData = new FormData(form.querySelector('form') || form);
    const invoiceData = {};
    formData.forEach((value, key) => { if (key !== 'id') invoiceData[key] = value; });

    showLoading(true);
    try {
        const result = await makeApiCall('PUT', `/api/invoices/${invoiceId}`, invoiceData);
        if (result.success || result.id) {
            showNotification('Invoice updated successfully!', 'success');
            if (form) form.style.display = 'none';
            await loadInvoices();
        } else {
            showNotification(result.error || 'Failed to update invoice', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Update invoice');
    } finally {
        showLoading(false);
    }
}

// ====== DELETE INVOICE ======
/**
 * Delete an invoice after confirmation
 * @param {number} invoiceId
 */
function deleteInvoice(invoiceId) {
    const inv   = invoicesData.find(i => i.id === invoiceId);
    const label = inv ? (inv.invoice_number || `INV-${String(inv.id).padStart(6,'0')}`) : `ID ${invoiceId}`;

    showConfirmation(
        `Are you sure you want to delete invoice "${label}"? This action cannot be undone.`,
        async () => {
            showLoading(true);
            try {
                const result = await makeApiCall('DELETE', `/api/invoices/${invoiceId}`);
                if (result.success || result.message) {
                    showNotification('Invoice deleted successfully!', 'success');
                    await loadInvoices();
                } else {
                    showNotification(result.error || 'Failed to delete invoice', 'error');
                }
            } catch (error) {
                handleApiError(error, 'Delete invoice');
            } finally {
                showLoading(false);
            }
        }
    );
}

// ====== VIEW INVOICE DETAILS ======
/**
 * Show a modal with full invoice details
 * @param {number} invoiceId
 */
async function viewInvoiceDetails(invoiceId) {
    showLoading(true);
    try {
        const response = await makeApiCall('GET', `/api/invoices/${invoiceId}`);
        const inv = response.invoice || response;

        const travelerName = inv.traveler_name ||
            `${inv.first_name || ''} ${inv.last_name || ''}`.trim() || `ID ${inv.traveler_id}`;

        const content = `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;">
                <div><strong>Invoice #:</strong><br>${escapeHtml(inv.invoice_number || `INV-${String(inv.id).padStart(6,'0')}`)}</div>
                <div><strong>Status:</strong><br>${escapeHtml(inv.status || '-')}</div>
                <div><strong>Traveler:</strong><br>${escapeHtml(travelerName)}</div>
                <div><strong>Batch:</strong><br>${escapeHtml(inv.batch_name || inv.batch_id || '-')}</div>
                <div><strong>Invoice Date:</strong><br>${formatDate(inv.invoice_date || inv.created_at)}</div>
                <div><strong>Due Date:</strong><br>${formatDate(inv.due_date)}</div>
                <div><strong>Amount:</strong><br>${formatCurrency(inv.amount)}</div>
                <div><strong>Created:</strong><br>${formatDate(inv.created_at)}</div>
                <div style="grid-column:1/-1;"><strong>Description:</strong><br>${escapeHtml(inv.description || '-')}</div>
                <div style="grid-column:1/-1;"><strong>Notes:</strong><br>${escapeHtml(inv.notes || '-')}</div>
            </div>`;

        showModal(`<i class="fas fa-file-invoice" style="color:#3498db;margin-right:8px;"></i>Invoice Details`, content, [
            { label: '<i class="fas fa-file-pdf"></i> Download PDF', class: 'btn-success', onClick: `closeModal(); generateInvoicePDF(${invoiceId});` },
            { label: '<i class="fas fa-edit"></i> Edit', class: 'btn-primary', onClick: `closeModal(); editInvoice(${invoiceId});` },
            { label: '<i class="fas fa-times"></i> Close', class: 'btn-secondary', onClick: 'closeModal()' }
        ]);
    } catch (error) {
        handleApiError(error, 'Load invoice details');
    } finally {
        showLoading(false);
    }
}

// ====== EXPORT TO CSV ======
/**
 * Export the current invoice list to a CSV file
 */
function exportInvoicesToCSV() {
    const data = filteredInvoicesData.length > 0 ? filteredInvoicesData : invoicesData;
    if (!data || data.length === 0) {
        showNotification('No invoices to export', 'warning');
        return;
    }

    const headers = ['Invoice #','Date','Traveler','Batch','Amount','Status','Due Date','Notes'];
    const rows = data.map(inv => {
        const travelerName = inv.traveler_name || `${inv.first_name || ''} ${inv.last_name || ''}`.trim();
        return [
            inv.invoice_number || `INV-${String(inv.id).padStart(6,'0')}`,
            inv.invoice_date || inv.created_at,
            travelerName,
            inv.batch_name || inv.batch_id,
            inv.amount, inv.status, inv.due_date, inv.notes
        ].map(v => `"${String(v || '').replace(/"/g, '""')}"`);
    });

    const csv  = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href     = url;
    link.download = `invoices_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    showNotification(`Exported ${data.length} invoices to CSV`, 'success');
}

// ====== GENERATE INVOICE PDF ======
/**
 * Generate and download an invoice PDF
 * @param {number} invoiceId
 */
async function generateInvoicePDF(invoiceId) {
    showLoading(true);
    try {
        const response = await makeApiCall('GET', `/api/invoices/${invoiceId}`);
        const inv = response.invoice || response;

        const travelerName = inv.traveler_name ||
            `${inv.first_name || ''} ${inv.last_name || ''}`.trim() || `ID ${inv.traveler_id}`;
        const invoiceNo = inv.invoice_number || `INV-${String(inv.id).padStart(6, '0')}`;

        // Try API-based PDF generation first
        try {
            const pdfResponse = await fetch(`/api/invoices/${invoiceId}/pdf`, {
                credentials: 'include'
            });
            if (pdfResponse.ok) {
                const blob = await pdfResponse.blob();
                const url  = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href     = url;
                link.download = `invoice_${invoiceNo}.pdf`;
                link.click();
                URL.revokeObjectURL(url);
                showNotification('Invoice PDF downloaded!', 'success');
                return;
            }
        } catch (e) {
            console.log('API PDF not available, generating client-side');
        }

        // Client-side printable invoice
        const invoiceHtml = `
            <!DOCTYPE html><html><head>
            <title>Invoice ${invoiceNo}</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 20px; color: #2c3e50; }
                .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #1a472a; padding-bottom: 20px; margin-bottom: 30px; }
                .company h1 { color: #1a472a; margin: 0; }
                .invoice-info { text-align: right; }
                .invoice-info h2 { color: #d4af37; margin: 0 0 5px; }
                .details-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }
                .detail-box { background: #f8f9fa; padding: 15px; border-radius: 8px; }
                .detail-box h4 { color: #1a472a; margin: 0 0 10px; }
                .amount-box { background: #1a472a; color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; }
                .amount-box .amount { font-size: 2rem; font-weight: bold; color: #d4af37; }
                .footer { text-align: center; color: #95a5a6; font-size: 0.85rem; margin-top: 30px; border-top: 1px solid #ecf0f1; padding-top: 15px; }
            </style></head><body>
            <div class="header">
                <div class="company">
                    <h1>&#x1F54B; Alhudha Haj Travel</h1>
                    <p>Hajj &amp; Umrah Travel Management</p>
                </div>
                <div class="invoice-info">
                    <h2>INVOICE</h2>
                    <p><strong>${invoiceNo}</strong></p>
                    <p>Date: ${formatDate(inv.invoice_date || inv.created_at)}</p>
                    <p>Due: ${formatDate(inv.due_date) || 'On Receipt'}</p>
                </div>
            </div>
            <div class="details-grid">
                <div class="detail-box">
                    <h4>Bill To</h4>
                    <p>${escapeHtml(travelerName)}</p>
                    <p>Batch: ${escapeHtml(inv.batch_name || inv.batch_id || '-')}</p>
                </div>
                <div class="detail-box">
                    <h4>Invoice Details</h4>
                    <p>Status: ${escapeHtml(inv.status || '-')}</p>
                    <p>Description: ${escapeHtml(inv.description || 'Hajj Travel Package')}</p>
                </div>
            </div>
            <div class="amount-box">
                <div>Total Amount Due</div>
                <div class="amount">${formatCurrency(inv.amount)}</div>
            </div>
            ${inv.notes ? `<p><strong>Notes:</strong> ${escapeHtml(inv.notes)}</p>` : ''}
            <div class="footer">
                <p>This is a computer-generated invoice. Generated on ${new Date().toLocaleString('en-IN')}</p>
            </div>
            </body></html>`;

        const blob = new Blob([invoiceHtml], { type: 'text/html' });
        const url  = URL.createObjectURL(blob);
        const win  = window.open(url, '_blank');
        if (win) win.onload = () => win.print();

        showNotification('Invoice PDF generated!', 'success');
    } catch (error) {
        handleApiError(error, 'Generate invoice PDF');
    } finally {
        showLoading(false);
    }
}
// ── State ────────────────────────────────────────────────────
let allInvoices = [];
let filteredInvoices = [];
let invoicesPage = 1;
const INVOICES_PER_PAGE = 20;

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    SessionManager.initPage(async () => {
        await loadInvoices();
        initInvoiceSearchListeners();
        initTaxCalculation();
    });
});

function initInvoiceSearchListeners() {
    const searchEl = document.getElementById('searchInvoices');
    const statusEl = document.getElementById('invoiceStatusFilter');
    if (searchEl) searchEl.addEventListener('input', debounce(filterInvoices, 250));
    if (statusEl) statusEl.addEventListener('change', filterInvoices);
}

function initTaxCalculation() {
    ['amount', 'gst_percent', 'tcs_percent'].forEach((id) => {
        document.getElementById(id)?.addEventListener('input', recalculateTotals);
    });
}

function recalculateTotals() {
    const base = parseFloat(document.getElementById('amount')?.value) || 0;
    const gst  = parseFloat(document.getElementById('gst_percent')?.value) || 5;
    const tcs  = parseFloat(document.getElementById('tcs_percent')?.value) || 1;

    const gstAmt   = base * (gst / 100);
    const subtotal = base + gstAmt;
    const tcsAmt   = subtotal * (tcs / 100);
    const total    = subtotal + tcsAmt;

    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.value = val.toFixed(2); };
    setEl('gst_amount',   gstAmt);
    setEl('tcs_amount',   tcsAmt);
    setEl('total_amount', total);
}

// ── Load & Display ───────────────────────────────────────────

/**
 * Fetch all invoices from the API
 */
async function loadInvoices() {
    const tbody = document.getElementById('invoicesTableBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="10" class="loading"><i class="fas fa-spinner fa-spin"></i> Loading invoices…</td></tr>';

    try {
        const data = await makeAPICall('GET', '/api/invoices');
        if (data.success) {
            allInvoices = data.invoices || [];
            filteredInvoices = [...allInvoices];
            invoicesPage = 1;
            displayInvoices();
            updateInvoiceStats();
        } else {
            throw new Error(data.error || 'Failed to load invoices');
        }
    } catch (error) {
        handleError(error, 'loadInvoices');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; padding:40px;">
                <i class="fas fa-exclamation-triangle" style="color:#e74c3c; font-size:2rem;"></i>
                <p style="color:#e74c3c; margin:10px 0;">${escapeHtml(error.message)}</p>
                <button class="action-btn btn-primary" onclick="loadInvoices()"><i class="fas fa-redo"></i> Retry</button>
            </td></tr>`;
        }
    }
}

/**
 * Render the current page of invoices
 */
function displayInvoices() {
    const tbody = document.getElementById('invoicesTableBody');
    if (!tbody) return;

    const start = (invoicesPage - 1) * INVOICES_PER_PAGE;
    const page  = filteredInvoices.slice(start, start + INVOICES_PER_PAGE);

    if (page.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding:30px; color:#7f8c8d;">No invoices found</td></tr>';
        updateInvoicePagination();
        return;
    }

    tbody.innerHTML = page.map((inv) => {
        const statusClass = inv.status === 'paid' ? 'status-paid' : 'status-pending';
        return `<tr>
            <td>${inv.id}</td>
            <td><strong>${escapeHtml(inv.invoice_number || '-')}</strong></td>
            <td>${escapeHtml(inv.traveler_name || `${inv.first_name || ''} ${inv.last_name || ''}`.trim() || '-')}</td>
            <td>${escapeHtml(inv.passport_no || '-')}</td>
            <td>${escapeHtml(inv.batch_name || '-')}</td>
            <td><strong>${formatCurrency(inv.amount)}</strong></td>
            <td>${inv.invoice_date ? formatDate(inv.invoice_date) : '-'}</td>
            <td>${inv.due_date ? formatDate(inv.due_date) : '-'}</td>
            <td><span class="status-badge ${statusClass}">${escapeHtml(inv.status || 'pending')}</span></td>
            <td class="invoice-actions">
                <button class="icon-btn btn-view" onclick="viewInvoiceDetails(${inv.id})" title="View"><i class="fas fa-eye"></i></button>
                <button class="icon-btn btn-edit" onclick="editInvoice(${inv.id})" title="Edit"><i class="fas fa-edit"></i></button>
                <button class="icon-btn" onclick="generateInvoicePDF(${inv.id})" title="Download PDF"><i class="fas fa-file-pdf"></i></button>
                <button class="icon-btn btn-delete" onclick="deleteInvoice(${inv.id})" title="Delete"><i class="fas fa-trash"></i></button>
            </td>
        </tr>`;
    }).join('');

    updateInvoicePagination();
}

// ── Filter ───────────────────────────────────────────────────

/**
 * Filter invoices by search text and status
 */
function filterInvoices() {
    const search = (document.getElementById('searchInvoices')?.value || '').toLowerCase();
    const status = document.getElementById('invoiceStatusFilter')?.value || 'all';

    filteredInvoices = allInvoices.filter((inv) => {
        const name = (inv.traveler_name || `${inv.first_name || ''} ${inv.last_name || ''}`).toLowerCase();
        const matchSearch = !search ||
            name.includes(search) ||
            (inv.invoice_number || '').toLowerCase().includes(search) ||
            (inv.passport_no || '').toLowerCase().includes(search) ||
            (inv.batch_name || '').toLowerCase().includes(search);
        const matchStatus = status === 'all' || inv.status === status;
        return matchSearch && matchStatus;
    });

    invoicesPage = 1;
    displayInvoices();
}

// ── Form Visibility ──────────────────────────────────────────

function showAddInvoiceForm() {
    const modal = document.getElementById('createInvoiceModal');
    if (modal) {
        modal.style.display = 'flex';
        // Set today's date
        const dateEl = document.getElementById('invoice_date');
        if (dateEl && !dateEl.value) dateEl.value = new Date().toISOString().slice(0, 10);
        recalculateTotals();
        return;
    }
    const form = document.getElementById('addInvoiceForm');
    if (form) { form.style.display = 'block'; form.scrollIntoView({ behavior: 'smooth' }); }
}

function hideAddInvoiceForm() {
    const modal = document.getElementById('createInvoiceModal');
    if (modal) { modal.style.display = 'none'; return; }
    const form = document.getElementById('addInvoiceForm');
    if (form) form.style.display = 'none';
    document.getElementById('invoiceCreateForm')?.reset();
}

// ── CRUD ─────────────────────────────────────────────────────

/**
 * Create a new invoice
 */
async function createInvoice(event) {
    if (event) event.preventDefault();

    const getData = (id) => (document.getElementById(id)?.value || '').trim();

    const invoiceData = {
        traveler_id:  getData('invoice_traveler_id') || getData('traveler_id'),
        batch_id:     getData('invoice_batch_id') || getData('batch_id') || null,
        amount:       parseFloat(getData('amount')),
        gst_percent:  parseFloat(getData('gst_percent')) || 5,
        tcs_percent:  parseFloat(getData('tcs_percent')) || 1,
        due_date:     getData('due_date') || null,
        invoice_date: getData('invoice_date') || new Date().toISOString().slice(0, 10),
        status:       getData('invoice_status') || 'pending',
        description:  getData('description') || 'Travel Package',
        notes:        getData('notes') || null
    };

    if (!invoiceData.traveler_id || !invoiceData.amount || isNaN(invoiceData.amount)) {
        showNotification('Traveler and a valid amount are required', 'error');
        return;
    }

    const btn  = document.querySelector('#invoiceCreateForm button[type="submit"]');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating…'; btn.disabled = true; }

    try {
        const data = await makeAPICall('POST', '/api/invoices', invoiceData);
        if (data.success) {
            showNotification(`Invoice ${data.invoice_number} created successfully!`, 'success');
            hideAddInvoiceForm();
            await loadInvoices();
        } else {
            throw new Error(data.error || 'Could not create invoice');
        }
    } catch (error) {
        handleError(error, 'createInvoice');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Load invoice data into the edit modal
 * @param {number} id
 */
async function editInvoice(id) {
    try {
        const data = await makeAPICall('GET', `/api/invoices/${id}`);
        if (!data.success || !data.invoice) throw new Error(data.error || 'Invoice not found');

        const inv = data.invoice;
        const set = (elId, val) => { const el = document.getElementById(elId); if (el) el.value = val || ''; };

        set('edit_invoice_id',     inv.id);
        set('edit_invoice_amount', inv.base_amount || inv.amount);
        set('edit_invoice_due',    inv.due_date ? inv.due_date.slice(0, 10) : '');
        set('edit_invoice_status', inv.status);

        const modal   = document.getElementById('editInvoiceModal');
        const overlay = document.getElementById('modalOverlay');
        if (modal)   modal.style.display   = 'block';
        if (overlay) overlay.style.display = 'block';
    } catch (error) {
        handleError(error, 'editInvoice');
    }
}

/**
 * Submit the edit invoice form
 */
async function updateInvoice(event) {
    if (event) event.preventDefault();

    const id = document.getElementById('edit_invoice_id')?.value;
    if (!id) return;

    const getData = (elId) => (document.getElementById(elId)?.value || '').trim();

    const invoiceData = {
        amount:   parseFloat(getData('edit_invoice_amount')),
        due_date: getData('edit_invoice_due') || null,
        status:   getData('edit_invoice_status')
    };

    const btn  = document.querySelector('#editInvoiceForm button[type="submit"]');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating…'; btn.disabled = true; }

    try {
        const data = await makeAPICall('PUT', `/api/invoices/${id}`, invoiceData);
        if (data.success) {
            showNotification('Invoice updated successfully!', 'success');
            closeInvoiceModal();
            await loadInvoices();
        } else {
            throw new Error(data.error || 'Could not update invoice');
        }
    } catch (error) {
        handleError(error, 'updateInvoice');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Delete an invoice by ID
 * @param {number} id
 */
async function deleteInvoice(id) {
    if (!confirmAction(`Delete invoice ID ${id}? This cannot be undone.`)) return;

    try {
        const data = await makeAPICall('DELETE', `/api/invoices/${id}`);
        if (data.success) {
            showNotification('Invoice deleted successfully!', 'success');
            await loadInvoices();
        } else {
            throw new Error(data.error || 'Could not delete invoice');
        }
    } catch (error) {
        handleError(error, 'deleteInvoice');
    }
}

/**
 * View invoice details in a modal
 * @param {number} id
 */
async function viewInvoiceDetails(id) {
    try {
        showLoading('Loading invoice…');
        const data = await makeAPICall('GET', `/api/invoices/${id}`);
        hideLoading();

        if (!data.success || !data.invoice) throw new Error(data.error || 'Invoice not found');
        const inv = data.invoice;

        const content = `
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px; margin-bottom:20px;">
                <div><strong>Invoice #:</strong> ${escapeHtml(inv.invoice_number || '-')}</div>
                <div><strong>Status:</strong> <span class="status-badge ${inv.status === 'paid' ? 'status-paid' : 'status-pending'}">${escapeHtml(inv.status)}</span></div>
                <div><strong>Traveler:</strong> ${escapeHtml(inv.traveler_name || `${inv.first_name || ''} ${inv.last_name || ''}`.trim())}</div>
                <div><strong>Passport:</strong> ${escapeHtml(inv.passport_no || '-')}</div>
                <div><strong>Batch:</strong> ${escapeHtml(inv.batch_name || '-')}</div>
                <div><strong>Invoice Date:</strong> ${inv.invoice_date ? formatDate(inv.invoice_date) : '-'}</div>
                <div><strong>Due Date:</strong> ${inv.due_date ? formatDate(inv.due_date) : '-'}</div>
            </div>
            <table style="width:100%; border-collapse:collapse; font-size:0.95rem;">
                <tr style="background:#f8f9fa;"><td style="padding:10px;"><strong>Base Amount</strong></td><td style="padding:10px; text-align:right;">${formatCurrency(inv.base_amount || inv.amount)}</td></tr>
                <tr><td style="padding:10px;">GST (${inv.gst_percent || 5}%)</td><td style="padding:10px; text-align:right;">${formatCurrency(inv.gst_amount || 0)}</td></tr>
                <tr><td style="padding:10px;">TCS (${inv.tcs_percent || 1}%)</td><td style="padding:10px; text-align:right;">${formatCurrency(inv.tcs_amount || 0)}</td></tr>
                <tr style="background:#2c3e50; color:white;"><td style="padding:10px;"><strong>Total Amount</strong></td><td style="padding:10px; text-align:right;"><strong>${formatCurrency(inv.amount)}</strong></td></tr>
            </table>`;

        showModal(`Invoice: ${inv.invoice_number}`, content,
            `<button class="action-btn btn-primary" onclick="generateInvoicePDF(${inv.id}); closeModal();">
                <i class="fas fa-file-pdf"></i> Download PDF
            </button>`);
    } catch (error) {
        hideLoading();
        handleError(error, 'viewInvoiceDetails');
    }
}

/**
 * Generate and download a PDF for an invoice
 * @param {number} id
 */
async function generateInvoicePDF(id) {
    try {
        showLoading('Generating PDF…');
        const data = await makeAPICall('GET', `/api/invoices/${id}`);
        hideLoading();

        if (!data.success || !data.invoice) throw new Error(data.error || 'Invoice not found');
        const inv = data.invoice;

        // Use jsPDF if available
        if (typeof window.jspdf !== 'undefined' || typeof window.jsPDF !== 'undefined') {
            const { jsPDF } = window.jspdf || window;
            const doc = new jsPDF();

            doc.setFontSize(18);
            doc.text('INVOICE', 105, 20, { align: 'center' });
            doc.setFontSize(12);
            doc.text(`Invoice #: ${inv.invoice_number || id}`, 20, 40);
            doc.text(`Date: ${inv.invoice_date ? formatDate(inv.invoice_date) : '-'}`, 20, 50);
            doc.text(`Traveler: ${inv.traveler_name || `${inv.first_name || ''} ${inv.last_name || ''}`.trim()}`, 20, 60);
            doc.text(`Passport: ${inv.passport_no || '-'}`, 20, 70);
            doc.text(`Batch: ${inv.batch_name || '-'}`, 20, 80);
            doc.text(`Status: ${inv.status}`, 20, 90);

            doc.line(20, 100, 190, 100);
            doc.text(`Base Amount: ${formatCurrency(inv.base_amount || inv.amount)}`, 20, 110);
            doc.text(`GST (${inv.gst_percent || 5}%): ${formatCurrency(inv.gst_amount || 0)}`, 20, 120);
            doc.text(`TCS (${inv.tcs_percent || 1}%): ${formatCurrency(inv.tcs_amount || 0)}`, 20, 130);
            doc.setFontSize(14);
            doc.text(`Total: ${formatCurrency(inv.amount)}`, 20, 145);

            doc.save(`invoice_${inv.invoice_number || id}.pdf`);
            showNotification('Invoice PDF downloaded!', 'success');
        } else {
            // Fallback: print window
            const printWin = window.open('', '_blank');
            printWin.document.write(`<html><head><title>Invoice ${inv.invoice_number}</title>
                <style>body{font-family:Arial;padding:30px;} table{width:100%;border-collapse:collapse;} td{padding:10px;border:1px solid #ddd;}</style>
                </head><body>
                <h2>Invoice #${escapeHtml(inv.invoice_number || String(id))}</h2>
                <p><strong>Traveler:</strong> ${escapeHtml(inv.traveler_name || '')}</p>
                <p><strong>Batch:</strong> ${escapeHtml(inv.batch_name || '-')}</p>
                <p><strong>Date:</strong> ${inv.invoice_date ? formatDate(inv.invoice_date) : '-'}</p>
                <table>
                    <tr><td>Base Amount</td><td>${formatCurrency(inv.base_amount || inv.amount)}</td></tr>
                    <tr><td>GST (${inv.gst_percent || 5}%)</td><td>${formatCurrency(inv.gst_amount || 0)}</td></tr>
                    <tr><td>TCS (${inv.tcs_percent || 1}%)</td><td>${formatCurrency(inv.tcs_amount || 0)}</td></tr>
                    <tr><td><strong>Total</strong></td><td><strong>${formatCurrency(inv.amount)}</strong></td></tr>
                </table>
                </body></html>`);
            printWin.document.close();
            printWin.print();
        }
    } catch (error) {
        hideLoading();
        handleError(error, 'generateInvoicePDF');
    }
}

// ── Export ───────────────────────────────────────────────────

/**
 * Export filtered invoices to CSV
 */
function exportInvoicesToCSV() {
    if (!filteredInvoices.length) { showNotification('No invoices to export', 'warning'); return; }
    downloadCSV(
        filteredInvoices,
        ['id', 'invoice_number', 'traveler_name', 'passport_no', 'batch_name', 'amount', 'invoice_date', 'due_date', 'status'],
        ['ID', 'Invoice #', 'Traveler', 'Passport No', 'Batch', 'Amount', 'Invoice Date', 'Due Date', 'Status'],
        `invoices_${new Date().toISOString().slice(0, 10)}.csv`
    );
}

// ── Pagination ───────────────────────────────────────────────

function updateInvoicePagination() {
    const total = filteredInvoices.length;
    const start = total > 0 ? (invoicesPage - 1) * INVOICES_PER_PAGE + 1 : 0;
    const end   = Math.min(invoicesPage * INVOICES_PER_PAGE, total);
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalCount',  total);
    setEl('showingFrom', start);
    setEl('showingTo',   end);
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    if (prevBtn) prevBtn.disabled = invoicesPage === 1;
    if (nextBtn) nextBtn.disabled = end >= total;
}

function prevInvoicePage() {
    if (invoicesPage > 1) { invoicesPage--; displayInvoices(); }
}

function nextInvoicePage() {
    if (invoicesPage * INVOICES_PER_PAGE < filteredInvoices.length) { invoicesPage++; displayInvoices(); }
}

// ── Stats ────────────────────────────────────────────────────

function updateInvoiceStats() {
    const paid    = allInvoices.filter((i) => i.status === 'paid');
    const pending = allInvoices.filter((i) => i.status === 'pending');
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalInvoices',   allInvoices.length);
    setEl('paidInvoices',    paid.length);
    setEl('pendingInvoices', pending.length);
    setEl('totalInvoiceAmount', formatCurrency(allInvoices.reduce((s, i) => s + (parseFloat(i.amount) || 0), 0)));
}

// ── Modal Helpers ────────────────────────────────────────────

function closeInvoiceModal() {
    ['editInvoiceModal', 'createInvoiceModal'].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
    const overlay = document.getElementById('modalOverlay');
    if (overlay) overlay.style.display = 'none';
}

// ── Form submit wiring ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('invoiceCreateForm')?.addEventListener('submit', createInvoice);
    document.getElementById('editInvoiceForm')?.addEventListener('submit', updateInvoice);
});

// Expose globals
window.loadInvoices         = loadInvoices;
window.filterInvoices       = filterInvoices;
window.showAddInvoiceForm   = showAddInvoiceForm;
window.hideAddInvoiceForm   = hideAddInvoiceForm;
window.editInvoice          = editInvoice;
window.deleteInvoice        = deleteInvoice;
window.viewInvoiceDetails   = viewInvoiceDetails;
window.generateInvoicePDF   = generateInvoicePDF;
window.exportInvoicesToCSV  = exportInvoicesToCSV;
window.closeInvoiceModal    = closeInvoiceModal;
window.prevInvoicePage      = prevInvoicePage;
window.nextInvoicePage      = nextInvoicePage;
window.recalculateTotals    = recalculateTotals;

console.log('✅ invoices.js loaded');
