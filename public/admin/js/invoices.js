/**
 * invoices.js - Invoice Management for Alhudha Haj Travel Admin
 * Handles CRUD operations for invoices with GST/TCS calculations
 * API base: /api/invoices
 */

'use strict';

// ====== GLOBALS ======
let invoicesData = [];
let filteredInvoicesData = [];
let currentPage = 1;
const PER_PAGE = 10;
let travelersData = [];
let batchesData = [];

// ====== LOAD INVOICES FROM API ======
async function loadInvoices() {
    const tbody = document.getElementById('invoicesTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading"><i class="fas fa-spinner fa-spin"></i> Loading invoices...</i></td></tr>';
    }

    try {
        const response = await fetch('/api/invoices', {
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
            if (response.status === 401) {
                showNotification('Session expired. Please login again', 'error');
                setTimeout(() => { window.location.href = '/admin/login.html'; }, 2000);
                return;
            }
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        
        if (data.success && Array.isArray(data.invoices)) {
            invoicesData = data.invoices;
            filteredInvoicesData = [...data.invoices];
            currentPage = 1;
            console.log(`✅ Loaded ${invoicesData.length} invoices from database`);
            showNotification(`Loaded ${invoicesData.length} invoices`, 'success');
        } else {
            invoicesData = [];
            filteredInvoicesData = [];
            console.warn('⚠️ No invoices found');
        }
    } catch (error) {
        console.error('❌ Error loading invoices:', error);
        invoicesData = [];
        filteredInvoicesData = [];
        showNotification('Failed to load invoices', 'error');
    }

    displayInvoices();
    updateStats();
}

// ====== DISPLAY INVOICES TABLE ======
function displayInvoices() {
    const tbody = document.getElementById('invoicesTableBody');
    if (!tbody) return;

    const data = filteredInvoicesData || [];
    
    if (data.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align:center;padding:40px;">
                    <i class="fas fa-file-invoice" style="font-size:3rem;color:#bdc3c7;display:block;margin-bottom:10px;"></i>
                    <p style="color:#7f8c8d;">No invoices found</p>
                    <p style="color:#95a5a6;font-size:0.9rem;">Click "Create Invoice" to generate a new invoice</p>
                </td>
            </tr>
        `;
        updatePagination(0);
        return;
    }

    const start = (currentPage - 1) * PER_PAGE;
    const end = Math.min(start + PER_PAGE, data.length);
    const pageData = data.slice(start, end);

    let html = '';
    pageData.forEach(inv => {
        const statusClass = inv.status === 'paid' ? 'status-paid' : 'status-pending';
        const statusText = inv.status === 'paid' ? 'Paid' : 'Pending';
        const travelerName = inv.traveler_name || inv.traveler_first_name ? `${inv.traveler_first_name || ''} ${inv.traveler_last_name || ''}`.trim() : '-';
        const amount = parseFloat(inv.total_amount || inv.amount || 0);

        html += `
            <tr>
                <td><strong>${escapeHtml(inv.invoice_number || '#')}</strong></td>
                <td>${inv.created_at ? formatDate(inv.created_at) : '-'}</td>
                <td>${escapeHtml(travelerName)}</td>
                <td>${escapeHtml(inv.batch_name || '-')}</td>
                <td><strong>₹${amount.toLocaleString('en-IN')}</strong></td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td>
                    <div class="invoice-actions">
                        <button class="icon-btn btn-view" onclick="viewInvoice(${inv.id})" title="View Details"><i class="fas fa-eye"></i></button>
                        <button class="icon-btn btn-edit" onclick="openEditModal(${inv.id})" title="Edit"><i class="fas fa-edit"></i></button>
                        <button class="icon-btn btn-delete" onclick="deleteInvoice(${inv.id})" title="Delete"><i class="fas fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
    updatePagination(data.length);
}

// ====== UPDATE STATS ======
function updateStats() {
    const total = invoicesData.length;
    const paid = invoicesData.filter(i => i.status === 'paid').length;
    const pending = invoicesData.filter(i => i.status === 'pending').length;
    const totalAmount = invoicesData.reduce((sum, i) => sum + parseFloat(i.total_amount || i.amount || 0), 0);

    document.getElementById('totalInvoices').textContent = total;
    document.getElementById('paidInvoices').textContent = paid;
    document.getElementById('pendingInvoices').textContent = pending;
    document.getElementById('totalAmount').textContent = `₹${totalAmount.toLocaleString('en-IN')}`;
}

// ====== PAGINATION ======
function updatePagination(total) {
    document.getElementById('totalCount').textContent = total;
    const start = total > 0 ? (currentPage - 1) * PER_PAGE + 1 : 0;
    const end = Math.min(currentPage * PER_PAGE, total);
    document.getElementById('showingFrom').textContent = start;
    document.getElementById('showingTo').textContent = end;
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        displayInvoices();
    }
}

function nextPage() {
    const total = filteredInvoicesData.length;
    if (currentPage * PER_PAGE < total) {
        currentPage++;
        displayInvoices();
    }
}

// ====== FILTER FUNCTIONS ======
function filterInvoices() {
    const search = document.getElementById('searchInput').value.toLowerCase().trim();
    const status = document.getElementById('statusFilter').value;

    filteredInvoicesData = invoicesData.filter(inv => {
        const travelerName = inv.traveler_name || inv.traveler_first_name ? `${inv.traveler_first_name || ''} ${inv.traveler_last_name || ''}`.toLowerCase() : '';
        const invNum = (inv.invoice_number || '').toLowerCase();
        const batch = (inv.batch_name || '').toLowerCase();
        
        const matchesSearch = !search || 
            travelerName.includes(search) || 
            invNum.includes(search) || 
            batch.includes(search);
        
        const matchesStatus = status === 'all' || inv.status === status;
        
        return matchesSearch && matchesStatus;
    });

    currentPage = 1;
    displayInvoices();
    showNotification(`Found ${filteredInvoicesData.length} invoices`, 'info');
}

function resetFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('statusFilter').value = 'all';
    filteredInvoicesData = [...invoicesData];
    currentPage = 1;
    displayInvoices();
    showNotification('Filters reset', 'info');
}

// ====== LOAD TRAVELERS FOR DROPDOWN ======
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
                const dropdown = document.getElementById('travelerId');
                if (dropdown) {
                    dropdown.innerHTML = '<option value="">Select Traveler</option>';
                    data.travelers.forEach(t => {
                        dropdown.innerHTML += `<option value="${t.id}" data-batch-id="${t.batch_id || ''}" data-batch-name="${t.batch_name || ''}" data-price="${t.price || 0}">
                            ${t.first_name} ${t.last_name} (${t.passport_no || ''})
                        </option>`;
                    });
                }
            }
        }
    } catch (error) {
        console.error('Error loading travelers:', error);
    }
}

// ====== LOAD TRAVELER BATCH DETAILS ======
function loadTravelerBatch() {
    const dropdown = document.getElementById('travelerId');
    const selected = dropdown.options[dropdown.selectedIndex];
    
    if (!selected || !selected.value) {
        document.getElementById('batchName').value = '';
        document.getElementById('baseAmount').value = '';
        calculateTotal();
        return;
    }

    const batchName = selected.dataset.batchName || '';
    const price = parseFloat(selected.dataset.price) || 0;

    document.getElementById('batchName').value = batchName;
    document.getElementById('baseAmount').value = price;
    calculateTotal();
}

// ====== CALCULATE TOTAL WITH GST/TCS ======
function calculateTotal() {
    const baseAmount = parseFloat(document.getElementById('baseAmount').value) || 0;
    const gstPercent = parseFloat(document.getElementById('gstPercent').value) || 0;
    const tcsPercent = parseFloat(document.getElementById('tcsPercent').value) || 0;

    // Update display labels
    document.getElementById('gstPercentDisplay').textContent = gstPercent;
    document.getElementById('tcsPercentDisplay').textContent = tcsPercent;

    // Calculate amounts
    const gstAmount = (baseAmount * gstPercent) / 100;
    const subtotal = baseAmount + gstAmount;
    const tcsAmount = (subtotal * tcsPercent) / 100;
    const totalAmount = subtotal + tcsAmount;

    // Display calculations
    document.getElementById('displayBase').textContent = `₹${baseAmount.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
    document.getElementById('displayGST').textContent = `₹${gstAmount.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
    document.getElementById('displaySubtotal').textContent = `₹${subtotal.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
    document.getElementById('displayTCS').textContent = `₹${tcsAmount.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
    document.getElementById('displayTotal').textContent = `₹${totalAmount.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
}

// ====== CREATE INVOICE ======
async function createInvoice() {
    const travelerId = document.getElementById('travelerId').value;
    if (!travelerId) {
        showNotification('Please select a traveler', 'error');
        return;
    }

    const selected = document.getElementById('travelerId').options[document.getElementById('travelerId').selectedIndex];
    const batchId = selected.dataset.batchId || null;
    const baseAmount = parseFloat(document.getElementById('baseAmount').value) || 0;
    
    if (baseAmount <= 0) {
        showNotification('Invalid base amount', 'error');
        return;
    }

    const gstPercent = parseFloat(document.getElementById('gstPercent').value) || 0;
    const tcsPercent = parseFloat(document.getElementById('tcsPercent').value) || 0;
    const dueDate = document.getElementById('dueDate').value || null;
    const status = document.getElementById('status').value || 'pending';

    // Calculate amounts
    const gstAmount = (baseAmount * gstPercent) / 100;
    const subtotal = baseAmount + gstAmount;
    const tcsAmount = (subtotal * tcsPercent) / 100;
    const totalAmount = subtotal + tcsAmount;

    const data = {
        traveler_id: parseInt(travelerId),
        batch_id: batchId ? parseInt(batchId) : null,
        base_amount: baseAmount,
        gst_percent: gstPercent,
        gst_amount: gstAmount,
        tcs_percent: tcsPercent,
        tcs_amount: tcsAmount,
        total_amount: totalAmount,
        status: status,
        due_date: dueDate
    };

    try {
        const response = await fetch('/api/invoices', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (response.status === 401) {
            showNotification('Session expired. Please login again', 'error');
            setTimeout(() => { window.location.href = '/admin/login.html'; }, 2000);
            return;
        }

        const result = await response.json();

        if (result.success) {
            showNotification('Invoice created successfully!', 'success');
            closeCreateModal();
            await loadInvoices();
        } else {
            showNotification('Error: ' + (result.message || 'Failed to create invoice'), 'error');
        }
    } catch (error) {
        console.error('Error creating invoice:', error);
        showNotification('Failed to create invoice', 'error');
    }
}

// ====== OPEN CREATE MODAL ======
function openCreateModal() {
    document.getElementById('createModal').style.display = 'flex';
    document.getElementById('createForm').reset();
    document.getElementById('batchName').value = '';
    document.getElementById('baseAmount').value = '';
    document.getElementById('gstPercent').value = '5';
    document.getElementById('tcsPercent').value = '1';
    document.getElementById('dueDate').value = '';
    document.getElementById('status').value = 'pending';
    calculateTotal();
    
    // Load travelers if not loaded
    if (travelersData.length === 0) {
        loadTravelers();
    }
}

// ====== CLOSE CREATE MODAL ======
function closeCreateModal() {
    document.getElementById('createModal').style.display = 'none';
}

// ====== VIEW INVOICE ======
function viewInvoice(id) {
    const inv = invoicesData.find(i => i.id === id);
    if (!inv) {
        showNotification('Invoice not found', 'error');
        return;
    }

    const travelerName = inv.traveler_name || inv.traveler_first_name ? `${inv.traveler_first_name || ''} ${inv.traveler_last_name || ''}`.trim() : '-';
    const amount = parseFloat(inv.total_amount || inv.amount || 0);
    const baseAmount = parseFloat(inv.base_amount || 0);
    const gstAmount = parseFloat(inv.gst_amount || 0);
    const tcsAmount = parseFloat(inv.tcs_amount || 0);
    const gstPercent = parseFloat(inv.gst_percent || 0);
    const tcsPercent = parseFloat(inv.tcs_percent || 0);
    const statusText = inv.status === 'paid' ? 'Paid' : 'Pending';
    const statusClass = inv.status === 'paid' ? 'status-paid' : 'status-pending';

    const html = `
        <div style="padding: 10px;">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:20px;">
                <div style="background:#f8f9fa;padding:15px;border-radius:8px;">
                    <div style="color:#7f8c8d;font-size:0.85rem;">Invoice Number</div>
                    <div style="font-weight:bold;font-size:1.1rem;">${escapeHtml(inv.invoice_number || '#')}</div>
                </div>
                <div style="background:#f8f9fa;padding:15px;border-radius:8px;">
                    <div style="color:#7f8c8d;font-size:0.85rem;">Date</div>
                    <div style="font-weight:bold;">${inv.created_at ? formatDate(inv.created_at) : '-'}</div>
                </div>
                <div style="background:#f8f9fa;padding:15px;border-radius:8px;">
                    <div style="color:#7f8c8d;font-size:0.85rem;">Traveler</div>
                    <div style="font-weight:bold;">${escapeHtml(travelerName)}</div>
                </div>
                <div style="background:#f8f9fa;padding:15px;border-radius:8px;">
                    <div style="color:#7f8c8d;font-size:0.85rem;">Batch</div>
                    <div style="font-weight:bold;">${escapeHtml(inv.batch_name || '-')}</div>
                </div>
                <div style="background:#f8f9fa;padding:15px;border-radius:8px;">
                    <div style="color:#7f8c8d;font-size:0.85rem;">Status</div>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </div>
                <div style="background:#f8f9fa;padding:15px;border-radius:8px;">
                    <div style="color:#7f8c8d;font-size:0.85rem;">Due Date</div>
                    <div style="font-weight:bold;">${inv.due_date ? formatDate(inv.due_date) : '-'}</div>
                </div>
            </div>
            <div style="background:#f8f9fa;padding:20px;border-radius:8px;border:2px solid #d4af37;">
                <h4 style="color:#1a472a;margin-bottom:15px;">Payment Breakdown</h4>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                    <div><strong>Base Amount:</strong> ₹${baseAmount.toLocaleString('en-IN', {minimumFractionDigits: 2})}</div>
                    <div><strong>GST (${gstPercent}%):</strong> ₹${gstAmount.toLocaleString('en-IN', {minimumFractionDigits: 2})}</div>
                    <div><strong>Subtotal:</strong> ₹${(baseAmount + gstAmount).toLocaleString('en-IN', {minimumFractionDigits: 2})}</div>
                    <div><strong>TCS (${tcsPercent}%):</strong> ₹${tcsAmount.toLocaleString('en-IN', {minimumFractionDigits: 2})}</div>
                    <div style="grid-column:1/-1;border-top:2px solid #d4af37;padding-top:10px;font-size:1.2rem;">
                        <strong>Total Amount:</strong> ₹${amount.toLocaleString('en-IN', {minimumFractionDigits: 2})}
                    </div>
                </div>
            </div>
            ${inv.notes ? `<div style="margin-top:15px;padding:15px;background:#fff3cd;border-radius:8px;"><strong>Notes:</strong> ${escapeHtml(inv.notes)}</div>` : ''}
            <div style="margin-top:15px;padding:15px;background:#e8f4f8;border-radius:8px;border-left:4px solid #3498db;">
                <div style="font-size:0.85rem;color:#7f8c8d;">Created: ${inv.created_at ? formatDate(inv.created_at) : '-'}</div>
                <div style="font-size:0.85rem;color:#7f8c8d;">Updated: ${inv.updated_at ? formatDate(inv.updated_at) : '-'}</div>
            </div>
        </div>
    `;

    document.getElementById('viewDetails').innerHTML = html;
    document.getElementById('viewModal').style.display = 'flex';
}

// ====== CLOSE VIEW MODAL ======
function closeViewModal() {
    document.getElementById('viewModal').style.display = 'none';
}

// ====== OPEN EDIT MODAL ======
async function openEditModal(id) {
    const inv = invoicesData.find(i => i.id === id);
    if (!inv) {
        showNotification('Invoice not found', 'error');
        return;
    }

    document.getElementById('editId').value = inv.id;
    document.getElementById('editInvoiceNumber').value = inv.invoice_number || '';
    document.getElementById('editDate').value = inv.created_at ? formatDate(inv.created_at) : '-';
    document.getElementById('editTraveler').value = inv.traveler_name || '-';
    document.getElementById('editBatch').value = inv.batch_name || '-';
    document.getElementById('editAmount').value = inv.total_amount || inv.amount || 0;
    document.getElementById('editStatus').value = inv.status || 'pending';
    document.getElementById('editDueDate').value = inv.due_date || '';

    document.getElementById('editModal').style.display = 'flex';
}

// ====== CLOSE EDIT MODAL ======
function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
}

// ====== UPDATE INVOICE ======
async function updateInvoice() {
    const id = document.getElementById('editId').value;
    const amount = parseFloat(document.getElementById('editAmount').value);
    const status = document.getElementById('editStatus').value;
    const dueDate = document.getElementById('editDueDate').value || null;

    if (amount <= 0) {
        showNotification('Amount must be greater than 0', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/invoices/${id}`, {
            method: 'PUT',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ 
                total_amount: amount, 
                status: status,
                due_date: dueDate
            })
        });

        if (response.status === 401) {
            showNotification('Session expired. Please login again', 'error');
            setTimeout(() => { window.location.href = '/admin/login.html'; }, 2000);
            return;
        }

        const result = await response.json();

        if (result.success) {
            showNotification('Invoice updated successfully!', 'success');
            closeEditModal();
            await loadInvoices();
        } else {
            showNotification('Error: ' + (result.message || 'Failed to update invoice'), 'error');
        }
    } catch (error) {
        console.error('Error updating invoice:', error);
        showNotification('Failed to update invoice', 'error');
    }
}

// ====== DELETE INVOICE ======
async function deleteInvoice(id) {
    if (!confirm('Are you sure you want to delete this invoice? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/api/invoices/${id}`, {
            method: 'DELETE',
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        });

        if (response.status === 401) {
            showNotification('Session expired. Please login again', 'error');
            setTimeout(() => { window.location.href = '/admin/login.html'; }, 2000);
            return;
        }

        const result = await response.json();

        if (result.success) {
            showNotification('Invoice deleted successfully!', 'success');
            await loadInvoices();
        } else {
            showNotification('Error: ' + (result.message || 'Failed to delete invoice'), 'error');
        }
    } catch (error) {
        console.error('Error deleting invoice:', error);
        showNotification('Failed to delete invoice', 'error');
    }
}

// ====== EXPORT INVOICES ======
function exportInvoices() {
    const data = filteredInvoicesData.length > 0 ? filteredInvoicesData : invoicesData;
    if (data.length === 0) {
        showNotification('No invoices to export', 'warning');
        return;
    }

    const headers = ['Invoice #', 'Date', 'Traveler', 'Batch', 'Base Amount', 'GST %', 'GST Amount', 'TCS %', 'TCS Amount', 'Total Amount', 'Status', 'Due Date'];
    
    const rows = data.map(inv => {
        const travelerName = inv.traveler_name || inv.traveler_first_name ? `${inv.traveler_first_name || ''} ${inv.traveler_last_name || ''}`.trim() : '-';
        return [
            inv.invoice_number || '',
            inv.created_at || '',
            travelerName,
            inv.batch_name || '',
            inv.base_amount || 0,
            inv.gst_percent || 0,
            inv.gst_amount || 0,
            inv.tcs_percent || 0,
            inv.tcs_amount || 0,
            inv.total_amount || inv.amount || 0,
            inv.status || '',
            inv.due_date || ''
        ];
    });

    let csv = headers.map(h => `"${h}"`).join(',') + '\n';
    csv += rows.map(row => row.map(v => `"${v}"`).join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `invoices_export_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    showNotification(`Exported ${data.length} invoices`, 'success');
}

// ====== UTILITY FUNCTIONS ======
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
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i> ${message}`;
    notification.style.display = 'block';
    if (window.notificationTimeout) clearTimeout(window.notificationTimeout);
    window.notificationTimeout = setTimeout(() => { notification.style.display = 'none'; }, 3000);
}

// ====== LOGOUT ======
async function logout() {
    if (!confirm('Are you sure you want to logout?')) return;
    sessionStorage.clear();
    window.location.href = '/admin/login.html';
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
    console.log('✅ User authenticated, loading invoices page...');
    
    // Load travelers for dropdown
    await loadTravelers();
    
    // Load invoices
    await loadInvoices();
    
    // Set up search listeners
    document.getElementById('searchInput')?.addEventListener('keyup', function(e) {
        if (e.key === 'Enter') filterInvoices();
    });
    
    console.log('✅ Invoices page loaded successfully!');
}

// ====== EXPOSE GLOBALS ======
window.loadInvoices = loadInvoices;
window.displayInvoices = displayInvoices;
window.filterInvoices = filterInvoices;
window.resetFilters = resetFilters;
window.previousPage = previousPage;
window.nextPage = nextPage;
window.openCreateModal = openCreateModal;
window.closeCreateModal = closeCreateModal;
window.createInvoice = createInvoice;
window.loadTravelerBatch = loadTravelerBatch;
window.calculateTotal = calculateTotal;
window.viewInvoice = viewInvoice;
window.closeViewModal = closeViewModal;
window.openEditModal = openEditModal;
window.closeEditModal = closeEditModal;
window.updateInvoice = updateInvoice;
window.deleteInvoice = deleteInvoice;
window.exportInvoices = exportInvoices;
window.logout = logout;

console.log('✅ invoices.js loaded successfully!');
