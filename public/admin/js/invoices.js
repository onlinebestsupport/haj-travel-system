/**
 * invoices.js - Invoice Management for Alhudha Haj Travel Admin
 * Handles CRUD operations for invoices with GST/TCS calculation
 * Depends on: common.js, session-manager.js
 * API base: /api/invoices
 */

'use strict';

// ====== STATE ======
let invoicesData = [];
let filteredInvoicesData = [];
let invoicesCurrentPage = 1;
const INVOICES_PER_PAGE = 10;
let travelersData = [];
let batchesData = [];

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
        console.log('🔄 Loading invoices...');
        const response = await fetch('/api/invoices', {
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
        console.log('📦 Invoices API response:', data);
        
        if (data.success && Array.isArray(data.invoices)) {
            invoicesData = data.invoices;
            filteredInvoicesData = [...invoicesData];
            console.log(`✅ Loaded ${invoicesData.length} invoices`);
        } else {
            console.warn('⚠️ No invoices found, using demo data');
            useDemoInvoices();
        }
    } catch (error) {
        console.error('❌ Error loading invoices:', error);
        useDemoInvoices();
    }

    displayInvoices();
    updateInvoiceStats();
}

/**
 * Use demo invoice data when API is unavailable
 */
function useDemoInvoices() {
    const today = new Date().toISOString().split('T')[0];
    invoicesData = [
        {
            id: 1,
            invoice_number: 'INV-20260101-1-1234',
            traveler_id: 1,
            batch_id: 1,
            amount: 26750,
            base_amount: 25000,
            gst_percent: 5,
            gst_amount: 1250,
            tcs_percent: 1,
            tcs_amount: 262.50,
            status: 'paid',
            due_date: '2026-02-15',
            invoice_date: '2026-01-15',
            created_at: '2026-01-15T10:00:00',
            first_name: 'John',
            last_name: 'Doe',
            passport_no: 'A0000001',
            batch_name: 'Haj Platinum 2026',
            batch_price: 850000,
            traveler_name: 'John Doe',
            description: 'Haj Package - Platinum',
            notes: 'Full payment received'
        },
        {
            id: 2,
            invoice_number: 'INV-20260120-2-5678',
            traveler_id: 2,
            batch_id: 2,
            amount: 58850,
            base_amount: 55000,
            gst_percent: 5,
            gst_amount: 2750,
            tcs_percent: 1,
            tcs_amount: 577.50,
            status: 'pending',
            due_date: '2026-02-20',
            invoice_date: '2026-01-20',
            created_at: '2026-01-20T10:00:00',
            first_name: 'Jane',
            last_name: 'Smith',
            passport_no: 'A0000002',
            batch_name: 'Haj Gold 2026',
            batch_price: 550000,
            traveler_name: 'Jane Smith',
            description: 'Haj Package - Gold',
            notes: 'First installment'
        },
        {
            id: 3,
            invoice_number: 'INV-20260201-3-9012',
            traveler_id: 3,
            batch_id: 3,
            amount: 131250,
            base_amount: 125000,
            gst_percent: 5,
            gst_amount: 6250,
            tcs_percent: 1,
            tcs_amount: 1312.50,
            status: 'pending',
            due_date: '2026-03-01',
            invoice_date: '2026-02-01',
            created_at: '2026-02-01T10:00:00',
            first_name: 'Ahmed',
            last_name: 'Khan',
            passport_no: 'A0000003',
            batch_name: 'Umrah Ramadhan Special',
            batch_price: 125000,
            traveler_name: 'Ahmed Khan',
            description: 'Umrah Package - Ramadhan',
            notes: 'Booking confirmed'
        }
    ];
    filteredInvoicesData = [...invoicesData];
}

// ====== DISPLAY INVOICES ======
/**
 * Render the invoices table with status badges
 */
function displayInvoices() {
    const tableBody = document.getElementById('invoicesTableBody');
    if (!tableBody) return;

    if (!filteredInvoicesData || filteredInvoicesData.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:#7f8c8d;">No invoices found. Create your first invoice!</td></tr>';
        updatePaginationDisplay(0);
        return;
    }

    const start = (invoicesCurrentPage - 1) * INVOICES_PER_PAGE;
    const end = Math.min(start + INVOICES_PER_PAGE, filteredInvoicesData.length);
    const pageData = filteredInvoicesData.slice(start, end);

    let html = '';
    pageData.forEach(inv => {
        const travelerName = inv.traveler_name || `${inv.first_name || ''} ${inv.last_name || ''}`.trim() || '-';
        const statusText = inv.status === 'paid' ? 'Paid' : 'Pending';
        const statusClass = inv.status === 'paid' ? 'status-paid' : 'status-pending';
        const amount = parseFloat(inv.amount || 0);

        html += `<tr>
            <td><strong>${escapeHtml(inv.invoice_number || 'N/A')}</strong></td>
            <td>${inv.invoice_date ? formatDate(inv.invoice_date) : (inv.created_at ? formatDate(inv.created_at) : '-')}</td>
            <td>${escapeHtml(travelerName)}</td>
            <td>${escapeHtml(inv.batch_name || '-')}</td>
            <td><strong>₹${amount.toLocaleString('en-IN')}</strong></td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td class="invoice-actions">
                <button class="icon-btn btn-view" onclick="viewInvoiceDetails(${inv.id})" title="View"><i class="fas fa-eye"></i></button>
                <button class="icon-btn btn-edit" onclick="openEditModal(${inv.id})" title="Edit"><i class="fas fa-edit"></i></button>
                <button class="icon-btn btn-delete" onclick="deleteInvoice(${inv.id})" title="Delete"><i class="fas fa-trash"></i></button>
            </td>
        </tr>`;
    });

    tableBody.innerHTML = html;
    updatePaginationDisplay(filteredInvoicesData.length);
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
    const start = total > 0 ? (invoicesCurrentPage - 1) * INVOICES_PER_PAGE + 1 : 0;
    const end = Math.min(invoicesCurrentPage * INVOICES_PER_PAGE, total);
    if (fromEl) fromEl.textContent = start;
    if (toEl) toEl.textContent = end;

    if (prevBtn) prevBtn.disabled = invoicesCurrentPage === 1;
    if (nextBtn) nextBtn.disabled = end >= total;
}

// ====== FILTER INVOICES ======
/**
 * Filter invoices by search text and status
 */
function filterInvoices() {
    const searchEl = document.getElementById('searchInput');
    const statusEl = document.getElementById('statusFilter');
    
    const search = searchEl ? searchEl.value.toLowerCase().trim() : '';
    const status = statusEl ? statusEl.value : 'all';

    if (!search && status === 'all') {
        filteredInvoicesData = [...invoicesData];
    } else {
        filteredInvoicesData = invoicesData.filter(inv => {
            const travelerName = `${inv.first_name || ''} ${inv.last_name || ''}`.toLowerCase();
            const invNum = (inv.invoice_number || '').toLowerCase();
            const matchesSearch = !search || travelerName.includes(search) || invNum.includes(search);
            const matchesStatus = status === 'all' || (inv.status || '').toLowerCase() === status.toLowerCase();
            return matchesSearch && matchesStatus;
        });
    }

    invoicesCurrentPage = 1;
    displayInvoices();
    showNotification(`Found ${filteredInvoicesData.length} invoice(s)`, 'info');
}

/**
 * Reset filters
 */
function resetFilters() {
    const searchEl = document.getElementById('searchInput');
    const statusEl = document.getElementById('statusFilter');
    
    if (searchEl) searchEl.value = '';
    if (statusEl) statusEl.value = 'all';
    
    filteredInvoicesData = [...invoicesData];
    invoicesCurrentPage = 1;
    displayInvoices();
    showNotification('Filters reset', 'info');
}

// ====== PAGINATION ======
function previousPage() {
    if (invoicesCurrentPage > 1) {
        invoicesCurrentPage--;
        displayInvoices();
    }
}

function nextPage() {
    if (invoicesCurrentPage * INVOICES_PER_PAGE < filteredInvoicesData.length) {
        invoicesCurrentPage++;
        displayInvoices();
    }
}

// ====== LOAD TRAVELERS ======
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
                updateTravelerSelect();
            }
        }
    } catch (error) {
        console.error('Error loading travelers:', error);
    }
}

/**
 * Update traveler dropdown
 */
function updateTravelerSelect() {
    const select = document.getElementById('travelerId');
    if (!select) return;

    select.innerHTML = '<option value="">Select Traveler</option>';
    travelersData.forEach(t => {
        const name = `${t.first_name || ''} ${t.last_name || ''}`.trim();
        const batch = batchesData.find(b => b.id === t.batch_id);
        const batchInfo = batch ? ` - ${batch.batch_name}` : '';
        select.innerHTML += `<option value="${t.id}" data-batch-id="${t.batch_id || ''}">${name} (${t.passport_no || 'N/A'})${batchInfo}</option>`;
    });
}

// ====== LOAD BATCHES ======
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

// ====== LOAD TRAVELER BATCH ======
async function loadTravelerBatch() {
    const travelerId = document.getElementById('travelerId').value;
    const batchNameField = document.getElementById('batchName');
    const baseAmountField = document.getElementById('baseAmount');

    if (!travelerId) {
        batchNameField.value = '';
        baseAmountField.value = '';
        calculateTotal();
        return;
    }

    const traveler = travelersData.find(t => t.id == travelerId);
    if (traveler && traveler.batch_id) {
        const batch = batchesData.find(b => b.id == traveler.batch_id);
        if (batch) {
            batchNameField.value = batch.batch_name || '';
            baseAmountField.value = batch.price || 0;
        } else {
            // Try fetching batch details
            try {
                const response = await fetch(`/api/batches/${traveler.batch_id}`, {
                    credentials: 'include'
                });
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.batch) {
                        batchNameField.value = data.batch.batch_name || '';
                        baseAmountField.value = data.batch.price || 0;
                    }
                }
            } catch (e) {
                console.error('Error fetching batch:', e);
            }
        }
    } else {
        batchNameField.value = 'No batch assigned';
        baseAmountField.value = 0;
    }
    calculateTotal();
}

// ====== CALCULATE TOTAL ======
function calculateTotal() {
    const baseAmount = parseFloat(document.getElementById('baseAmount').value) || 0;
    const gstPercent = parseFloat(document.getElementById('gstPercent').value) || 5;
    const tcsPercent = parseFloat(document.getElementById('tcsPercent').value) || 1;

    const gstAmount = baseAmount * (gstPercent / 100);
    const subtotal = baseAmount + gstAmount;
    const tcsAmount = subtotal * (tcsPercent / 100);
    const totalAmount = subtotal + tcsAmount;

    document.getElementById('displayBase').innerHTML = '₹' + baseAmount.toLocaleString('en-IN');
    document.getElementById('gstPercentDisplay').textContent = gstPercent;
    document.getElementById('displayGST').innerHTML = '₹' + gstAmount.toLocaleString('en-IN');
    document.getElementById('displaySubtotal').innerHTML = '₹' + subtotal.toLocaleString('en-IN');
    document.getElementById('tcsPercentDisplay').textContent = tcsPercent;
    document.getElementById('displayTCS').innerHTML = '₹' + tcsAmount.toLocaleString('en-IN');
    document.getElementById('displayTotal').innerHTML = '₹' + totalAmount.toLocaleString('en-IN');
}

// ====== INVOICE STATS ======
function updateInvoiceStats() {
    const total = invoicesData.length;
    const paid = invoicesData.filter(i => i.status === 'paid').length;
    const pending = invoicesData.filter(i => i.status === 'pending').length;
    const totalAmount = invoicesData.reduce((sum, i) => sum + (parseFloat(i.amount) || 0), 0);

    document.getElementById('totalInvoices').textContent = total;
    document.getElementById('paidInvoices').textContent = paid;
    document.getElementById('pendingInvoices').textContent = pending;
    document.getElementById('totalAmount').innerHTML = '₹' + totalAmount.toLocaleString('en-IN');
}

// ====== SHOW/HIDE MODALS ======
function openCreateModal() {
    document.getElementById('createModal').style.display = 'flex';
    document.body.style.overflow = 'hidden';
    
    // Set default due date (30 days from now)
    const dueDate = new Date();
    dueDate.setDate(dueDate.getDate() + 30);
    document.getElementById('dueDate').value = dueDate.toISOString().split('T')[0];
    
    // Set default status
    document.getElementById('status').value = 'pending';
    
    // Reset form
    document.getElementById('createForm').reset();
    document.getElementById('batchName').value = '';
    document.getElementById('baseAmount').value = '';
    document.getElementById('gstPercent').value = 5;
    document.getElementById('tcsPercent').value = 1;
    calculateTotal();
    
    // Load travelers and batches
    loadTravelers();
    loadBatches();
}

function closeCreateModal() {
    document.getElementById('createModal').style.display = 'none';
    document.body.style.overflow = '';
}

function openEditModal(invoiceId) {
    const invoice = invoicesData.find(i => i.id === invoiceId);
    if (!invoice) {
        showNotification('Invoice not found', 'error');
        return;
    }

    document.getElementById('editId').value = invoice.id;
    document.getElementById('editInvoiceNumber').value = invoice.invoice_number || '';
    document.getElementById('editDate').value = invoice.invoice_date ? formatDate(invoice.invoice_date) : (invoice.created_at ? formatDate(invoice.created_at) : '');
    document.getElementById('editTraveler').value = invoice.traveler_name || `${invoice.first_name || ''} ${invoice.last_name || ''}`.trim() || 'N/A';
    document.getElementById('editBatch').value = invoice.batch_name || 'N/A';
    document.getElementById('editAmount').value = invoice.amount || 0;
    document.getElementById('editDueDate').value = invoice.due_date || '';
    document.getElementById('editStatus').value = invoice.status || 'pending';

    document.getElementById('editModal').style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
    document.body.style.overflow = '';
}

function closeViewModal() {
    document.getElementById('viewModal').style.display = 'none';
    document.body.style.overflow = '';
}

// ====== CREATE INVOICE ======
async function createInvoice() {
    const travelerId = document.getElementById('travelerId').value;
    const baseAmount = parseFloat(document.getElementById('baseAmount').value) || 0;
    const gstPercent = parseFloat(document.getElementById('gstPercent').value) || 5;
    const tcsPercent = parseFloat(document.getElementById('tcsPercent').value) || 1;

    if (!travelerId) {
        showNotification('Please select a traveler', 'error');
        return;
    }

    if (baseAmount <= 0) {
        showNotification('Please ensure the traveler has a valid batch amount', 'error');
        return;
    }

    const traveler = travelersData.find(t => t.id == travelerId);
    const invoiceData = {
        traveler_id: parseInt(travelerId),
        batch_id: traveler?.batch_id || null,
        amount: baseAmount,
        gst_percent: gstPercent,
        tcs_percent: tcsPercent,
        due_date: document.getElementById('dueDate').value || null,
        status: document.getElementById('status').value,
        description: document.getElementById('batchName').value || 'Travel Package',
        notes: '',
        invoice_date: new Date().toISOString().split('T')[0]
    };

    const submitBtn = document.querySelector('#createForm button[type="submit"]');
    showLoading(submitBtn, 'Creating...');

    try {
        const response = await fetch('/api/invoices', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(invoiceData)
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
            showNotification(`Invoice ${data.invoice_number} created successfully!`, 'success');
            closeCreateModal();
            await loadInvoices();
        } else {
            showNotification('Error: ' + (data.error || 'Could not create invoice'), 'error');
        }
    } catch (error) {
        console.error('Create error:', error);
        // Demo mode fallback
        const demoInvoice = {
            id: invoicesData.length + 1,
            invoice_number: `INV-${new Date().toISOString().split('T')[0].replace(/-/g, '')}-${travelerId}-${Math.floor(Math.random() * 10000)}`,
            traveler_id: parseInt(travelerId),
            batch_id: traveler?.batch_id || null,
            amount: baseAmount + (baseAmount * gstPercent / 100) + ((baseAmount + (baseAmount * gstPercent / 100)) * tcsPercent / 100),
            base_amount: baseAmount,
            gst_percent: gstPercent,
            gst_amount: baseAmount * gstPercent / 100,
            tcs_percent: tcsPercent,
            tcs_amount: (baseAmount + (baseAmount * gstPercent / 100)) * tcsPercent / 100,
            status: document.getElementById('status').value || 'pending',
            due_date: document.getElementById('dueDate').value || null,
            invoice_date: new Date().toISOString().split('T')[0],
            created_at: new Date().toISOString(),
            first_name: traveler?.first_name || 'Demo',
            last_name: traveler?.last_name || 'Traveler',
            passport_no: traveler?.passport_no || 'N/A',
            batch_name: document.getElementById('batchName').value || 'Demo Batch',
            traveler_name: `${traveler?.first_name || 'Demo'} ${traveler?.last_name || 'Traveler'}`.trim(),
            description: document.getElementById('batchName').value || 'Travel Package',
            notes: 'Created in demo mode'
        };
        invoicesData.push(demoInvoice);
        filteredInvoicesData = [...invoicesData];
        showNotification('Invoice created (demo mode)', 'success');
        closeCreateModal();
        displayInvoices();
        updateInvoiceStats();
    } finally {
        hideLoading(submitBtn);
    }
}

// ====== UPDATE INVOICE ======
async function updateInvoice() {
    const id = document.getElementById('editId').value;
    const amount = parseFloat(document.getElementById('editAmount').value);
    const dueDate = document.getElementById('editDueDate').value;
    const status = document.getElementById('editStatus').value;

    if (!id) {
        showNotification('No invoice selected', 'error');
        return;
    }

    if (!amount || amount <= 0) {
        showNotification('Please enter a valid amount', 'error');
        return;
    }

    const updateData = {
        amount: amount,
        due_date: dueDate || null,
        status: status
    };

    const submitBtn = document.querySelector('#editForm button[type="submit"]');
    showLoading(submitBtn, 'Updating...');

    try {
        const response = await fetch(`/api/invoices/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(updateData)
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
            showNotification('Invoice updated successfully!', 'success');
            closeEditModal();
            await loadInvoices();
        } else {
            showNotification('Error: ' + (data.error || 'Could not update invoice'), 'error');
        }
    } catch (error) {
        console.error('Update error:', error);
        // Demo mode fallback
        const invoice = invoicesData.find(i => i.id == id);
        if (invoice) {
            invoice.amount = amount;
            invoice.due_date = dueDate;
            invoice.status = status;
            filteredInvoicesData = [...invoicesData];
            showNotification('Invoice updated (demo mode)', 'success');
            closeEditModal();
            displayInvoices();
            updateInvoiceStats();
        } else {
            showNotification('Error updating invoice', 'error');
        }
    } finally {
        hideLoading(submitBtn);
    }
}

// ====== DELETE INVOICE ======
async function deleteInvoice(id) {
    if (!confirm('⚠️ Are you sure you want to delete this invoice? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/api/invoices/${id}`, {
            method: 'DELETE',
            credentials: 'include'
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
            showNotification('Invoice deleted successfully!', 'success');
            await loadInvoices();
        } else {
            showNotification('Error: ' + (data.error || 'Could not delete invoice'), 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        // Demo mode fallback
        const index = invoicesData.findIndex(i => i.id === id);
        if (index !== -1) {
            invoicesData.splice(index, 1);
            filteredInvoicesData = [...invoicesData];
            showNotification('Invoice deleted (demo mode)', 'success');
            displayInvoices();
            updateInvoiceStats();
        } else {
            showNotification('Error deleting invoice', 'error');
        }
    }
}

// ====== VIEW INVOICE ======
function viewInvoiceDetails(id) {
    const invoice = invoicesData.find(i => i.id === id);
    if (!invoice) {
        showNotification('Invoice not found', 'error');
        return;
    }

    const travelerName = invoice.traveler_name || `${invoice.first_name || ''} ${invoice.last_name || ''}`.trim() || 'N/A';
    const statusText = invoice.status === 'paid' ? 'Paid' : 'Pending';
    const statusClass = invoice.status === 'paid' ? 'status-paid' : 'status-pending';
    const amount = parseFloat(invoice.amount || 0);
    const baseAmount = parseFloat(invoice.base_amount || 0);
    const gstAmount = parseFloat(invoice.gst_amount || 0);
    const tcsAmount = parseFloat(invoice.tcs_amount || 0);

    const detailsHtml = `
        <div style="padding: 10px;">
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px;">
                <div style="background: #f8f9fa; padding: 12px; border-radius: 8px;">
                    <strong>Invoice Number:</strong><br>
                    <span style="font-weight: 500;">${escapeHtml(invoice.invoice_number || 'N/A')}</span>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 8px;">
                    <strong>Status:</strong><br>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 8px;">
                    <strong>Traveler:</strong><br>
                    <span style="font-weight: 500;">${escapeHtml(travelerName)}</span>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 8px;">
                    <strong>Batch:</strong><br>
                    <span style="font-weight: 500;">${escapeHtml(invoice.batch_name || 'N/A')}</span>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 8px;">
                    <strong>Invoice Date:</strong><br>
                    <span style="font-weight: 500;">${invoice.invoice_date ? formatDate(invoice.invoice_date) : (invoice.created_at ? formatDate(invoice.created_at) : 'N/A')}</span>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 8px;">
                    <strong>Due Date:</strong><br>
                    <span style="font-weight: 500;">${invoice.due_date ? formatDate(invoice.due_date) : 'N/A'}</span>
                </div>
            </div>

            <div style="background: #f8f9fa; padding: 20px; border-radius: 12px; border: 2px solid #d4af37;">
                <h4 style="color: #1a472a; margin-bottom: 15px;">Tax Breakdown</h4>
                <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #ecf0f1;">
                    <span>Base Amount:</span>
                    <strong>₹${baseAmount.toLocaleString('en-IN')}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #ecf0f1;">
                    <span>GST (${invoice.gst_percent || 5}%):</span>
                    <strong>₹${gstAmount.toLocaleString('en-IN')}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #ecf0f1;">
                    <span>Subtotal:</span>
                    <strong>₹${(baseAmount + gstAmount).toLocaleString('en-IN')}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #ecf0f1;">
                    <span>TCS (${invoice.tcs_percent || 1}%):</span>
                    <strong>₹${tcsAmount.toLocaleString('en-IN')}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 12px 0; font-size: 1.2rem; font-weight: bold; color: #27ae60; border-top: 2px solid #d4af37; margin-top: 8px;">
                    <span>TOTAL AMOUNT:</span>
                    <strong>₹${amount.toLocaleString('en-IN')}</strong>
                </div>
            </div>

            ${invoice.description ? `
                <div style="margin-top: 15px; padding: 15px; background: #e8f4f8; border-radius: 8px;">
                    <strong>Description:</strong>
                    <p style="margin-top: 5px;">${escapeHtml(invoice.description)}</p>
                </div>
            ` : ''}
            ${invoice.notes ? `
                <div style="margin-top: 10px; padding: 15px; background: #fff3cd; border-radius: 8px;">
                    <strong>Notes:</strong>
                    <p style="margin-top: 5px;">${escapeHtml(invoice.notes)}</p>
                </div>
            ` : ''}
        </div>
    `;

    document.getElementById('viewDetails').innerHTML = detailsHtml;
    document.getElementById('viewModal').style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// ====== EXPORT INVOICES ======
function exportInvoices() {
    const data = filteredInvoicesData.length > 0 ? filteredInvoicesData : invoicesData;
    if (!data || data.length === 0) {
        showNotification('No invoices to export', 'warning');
        return;
    }

    const headers = ['Invoice #', 'Date', 'Traveler', 'Batch', 'Base Amount', 'GST %', 'GST Amount', 'TCS %', 'TCS Amount', 'Total Amount', 'Status', 'Due Date', 'Description'];
    
    const rows = data.map(inv => {
        const travelerName = inv.traveler_name || `${inv.first_name || ''} ${inv.last_name || ''}`.trim() || 'N/A';
        return [
            inv.invoice_number || '',
            inv.invoice_date || inv.created_at || '',
            travelerName,
            inv.batch_name || '',
            inv.base_amount || 0,
            inv.gst_percent || 5,
            inv.gst_amount || 0,
            inv.tcs_percent || 1,
            inv.tcs_amount || 0,
            inv.amount || 0,
            inv.status || '',
            inv.due_date || '',
            inv.description || ''
        ];
    });

    let csv = headers.map(h => `"${h}"`).join(',') + '\n';
    csv += rows.map(row => row.map(v => `"${v}"`).join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `invoices_export_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    showNotification(`Exported ${data.length} invoices to CSV`, 'success');
}

// ====== UI HELPERS ======
function showLoading(btn, text) {
    if (!btn) return;
    btn.disabled = true;
    const icon = btn.querySelector('i');
    if (icon) {
        icon.className = 'fas fa-spinner fa-spin';
    }
    btn.textContent = text || 'Loading...';
}

function hideLoading(btn) {
    if (!btn) return;
    btn.disabled = false;
    const icon = btn.querySelector('i');
    if (icon) {
        icon.className = 'fas fa-save';
    }
    btn.textContent = btn.textContent.replace('Loading...', 'Create Invoice');
    btn.textContent = btn.textContent.replace('Updating...', 'Save Changes');
    btn.textContent = btn.textContent.replace('Creating...', 'Create Invoice');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

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
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Invoices page initializing...');
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
    console.log('📋 Initializing invoices page...');
    resetSessionTimer();

    // Monitor user activity
    ['click', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
        document.addEventListener(event, resetSessionTimer);
    });

    // Load data
    await Promise.all([
        loadTravelers(),
        loadBatches(),
        loadInvoices()
    ]);

    console.log('✅ Invoices page loaded successfully!');
}

// Session timer
function resetSessionTimer() {
    console.log('Session timer reset');
}

// Logout
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
window.loadInvoices = loadInvoices;
window.filterInvoices = filterInvoices;
window.resetFilters = resetFilters;
window.previousPage = previousPage;
window.nextPage = nextPage;
window.openCreateModal = openCreateModal;
window.closeCreateModal = closeCreateModal;
window.createInvoice = createInvoice;
window.openEditModal = openEditModal;
window.closeEditModal = closeEditModal;
window.updateInvoice = updateInvoice;
window.deleteInvoice = deleteInvoice;
window.viewInvoiceDetails = viewInvoiceDetails;
window.closeViewModal = closeViewModal;
window.exportInvoices = exportInvoices;
window.loadTravelerBatch = loadTravelerBatch;
window.calculateTotal = calculateTotal;
window.logout = logout;
window.showNotification = showNotification;

console.log('✅ invoices.js loaded successfully with GST/TCS support!');
