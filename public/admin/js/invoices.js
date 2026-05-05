/**
 * invoices.js - Invoice management functions
 * Alhudha Haj Travel Management System
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
