/**
 * batches.js - Batch management functions
 * Alhudha Haj Travel Admin Panel
 */

'use strict';

// ====== STATE ======
let batchesData = [];
let batchesFiltered = [];
let batchesCurrentPage = 1;
const batchesPerPage = 10;
let batchesCurrentEditId = null;

// ====== LOAD BATCHES ======
/**
 * Fetch all batches from /api/batches
 */
async function loadBatches() {
    const tableBody = document.getElementById('batchesTableBody');
    if (tableBody) {
        tableBody.innerHTML = '<tr><td colspan="11" class="loading"><i class="fas fa-spinner fa-spin"></i> Loading batches...</td></tr>';
    }

    try {
        const data = await makeAPICall('GET', '/api/batches');
        if (data.success && Array.isArray(data.batches)) {
            batchesData = data.batches;
            batchesFiltered = [...batchesData];
            console.log(`✅ Loaded ${batchesData.length} batches`);
        } else {
            batchesData = [];
            batchesFiltered = [];
        }
    } catch (error) {
        handleAPIError(error, 'loadBatches');
        batchesData = [];
        batchesFiltered = [];
    }

    updateBatchStatistics();
    displayBatches();
    updateBatchDropdowns();
}

// ====== DISPLAY BATCHES ======
/**
 * Render the batches table with status badges and pagination
 */
function displayBatches() {
    const tableBody = document.getElementById('batchesTableBody');
    if (!tableBody) return;

    if (!batchesFiltered || batchesFiltered.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="11" style="text-align:center;padding:40px;">No batches found</td></tr>';
        updatePaginationDisplay(0, 1, batchesPerPage);
        return;
    }

    const start = (batchesCurrentPage - 1) * batchesPerPage;
    const end = start + batchesPerPage;
    const pageData = batchesFiltered.slice(start, end);

    let html = '';
    pageData.forEach(b => {
        const price = b.price ? Number(b.price).toLocaleString('en-IN') : '0';
        const totalSeats = b.total_seats || 0;
        const bookedSeats = b.booked_seats || 0;
        const availableSeats = totalSeats - bookedSeats;
        const occupancyPercent = totalSeats > 0 ? Math.round((bookedSeats / totalSeats) * 100) : 0;
        const statusClass = getStatusClass(b.status);
        const occupancyColor = occupancyPercent >= 100 ? '#e74c3c' : occupancyPercent > 80 ? '#e67e22' : '#27ae60';

        html += `<tr>
            <td>${b.id}</td>
            <td><strong>${escapeHtml(b.batch_name || '-')}</strong></td>
            <td>${b.departure_date ? formatDate(b.departure_date) : '-'}</td>
            <td>${b.return_date ? formatDate(b.return_date) : '-'}</td>
            <td>₹${price}</td>
            <td>${totalSeats}</td>
            <td>${bookedSeats}</td>
            <td>${availableSeats}</td>
            <td><span class="status-badge ${statusClass}">${escapeHtml(b.status || 'Open')}</span></td>
            <td>
                <div style="display:flex;align-items:center;gap:5px;">
                    <div style="width:50px;height:6px;background:#ecf0f1;border-radius:3px;">
                        <div style="width:${occupancyPercent}%;height:6px;background:${occupancyColor};border-radius:3px;"></div>
                    </div>
                    <span style="font-size:0.85rem;color:#7f8c8d;">${occupancyPercent}%</span>
                </div>
            </td>
            <td>
                <button class="icon-btn" onclick="viewBatchDetails(${b.id})" title="View"><i class="fas fa-eye"></i></button>
                <button class="icon-btn" onclick="editBatch(${b.id})" title="Edit"><i class="fas fa-edit"></i></button>
                <button class="icon-btn" onclick="deleteBatch(${b.id})" title="Delete"><i class="fas fa-trash"></i></button>
            </td>
        </tr>`;
    });

    tableBody.innerHTML = html;
    updatePaginationDisplay(batchesFiltered.length, batchesCurrentPage, batchesPerPage);
}

// ====== FILTER BATCHES ======
/**
 * Filter batches by name, status, or date
 */
function filterBatches() {
    const searchEl = document.getElementById('searchBatches');
    const search = searchEl ? searchEl.value.toLowerCase().trim() : '';

    if (!search) {
        batchesFiltered = [...batchesData];
    } else {
        batchesFiltered = batchesData.filter(b => {
            const name = (b.batch_name || '').toLowerCase();
            const status = (b.status || '').toLowerCase();
            const departure = (b.departure_date || '').toLowerCase();
            return name.includes(search) || status.includes(search) || departure.includes(search);
        });
    }

    batchesCurrentPage = 1;
    displayBatches();
}

// ====== CREATE BATCH ======
/**
 * POST a new batch
 */
async function createBatch() {
    const priceRaw = document.getElementById('price')?.value?.replace(/,/g, '') || '';
    const batchData = {
        batch_name: document.getElementById('batch_name')?.value?.trim(),
        total_seats: parseInt(document.getElementById('total_seats')?.value) || 150,
        price: priceRaw ? parseFloat(priceRaw) : null,
        departure_date: document.getElementById('departure_date')?.value || null,
        return_date: document.getElementById('return_date')?.value || null,
        status: document.getElementById('status')?.value || 'Open',
        description: document.getElementById('description')?.value?.trim() || ''
    };

    if (!batchData.batch_name) {
        showNotification('Batch name is required', 'error'); return;
    }

    const submitBtn = document.querySelector('#batchCreateForm button[type="submit"]');
    showLoading(submitBtn, 'Creating...');

    try {
        const data = await makeAPICall('POST', '/api/batches', batchData);
        if (data.success) {
            showNotification('Batch created successfully!', 'success');
            if (typeof hideCreateBatchForm === 'function') hideCreateBatchForm();
            await loadBatches();
        } else {
            showNotification('Error: ' + (data.error || 'Could not create batch'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'createBatch');
    } finally {
        hideLoading(submitBtn);
    }
}

// ====== EDIT BATCH ======
/**
 * Load batch data into the edit form
 * @param {number} id
 */
function editBatch(id) {
    const batch = batchesData.find(b => b.id === id);
    if (!batch) { showNotification('Batch not found', 'error'); return; }

    batchesCurrentEditId = id;

    const set = (elId, val) => { const el = document.getElementById(elId); if (el) el.value = val || ''; };
    set('edit_batch_id', batch.id);
    set('edit_batch_name', batch.batch_name);
    set('edit_departure_date', formatDateForInput(batch.departure_date));
    set('edit_return_date', formatDateForInput(batch.return_date));
    set('edit_price', batch.price || '');
    set('edit_total_seats', batch.total_seats || 150);
    set('edit_status', batch.status || 'Open');

    const editForm = document.getElementById('editBatchForm');
    if (editForm) {
        editForm.style.display = 'block';
        editForm.scrollIntoView({ behavior: 'smooth' });
    }
}

// ====== UPDATE BATCH ======
/**
 * PUT updated batch data
 */
async function updateBatch() {
    if (!batchesCurrentEditId) {
        showNotification('No batch selected for editing', 'error'); return;
    }

    const batchId = document.getElementById('edit_batch_id')?.value;
    const batchName = document.getElementById('edit_batch_name')?.value?.trim();
    if (!batchName) { showNotification('Batch name is required', 'error'); return; }

    const priceRaw = document.getElementById('edit_price')?.value?.replace(/,/g, '') || '';
    const batchData = {
        batch_name: batchName,
        departure_date: document.getElementById('edit_departure_date')?.value || null,
        return_date: document.getElementById('edit_return_date')?.value || null,
        price: priceRaw ? parseFloat(priceRaw) : null,
        total_seats: parseInt(document.getElementById('edit_total_seats')?.value) || 150,
        status: document.getElementById('edit_status')?.value || 'Open'
    };

    const submitBtn = document.querySelector('#batchEditForm button[type="submit"]');
    showLoading(submitBtn, 'Updating...');

    try {
        const data = await makeAPICall('PUT', `/api/batches/${batchId}`, batchData);
        if (data.success) {
            showNotification('Batch updated successfully!', 'success');
            if (typeof hideEditBatchForm === 'function') hideEditBatchForm();
            batchesCurrentEditId = null;
            await loadBatches();
        } else {
            showNotification('Error: ' + (data.error || 'Update failed'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'updateBatch');
    } finally {
        hideLoading(submitBtn);
    }
}

// ====== DELETE BATCH ======
/**
 * DELETE a batch by ID
 * @param {number} id
 */
async function deleteBatch(id) {
    if (!confirm('⚠️ Are you sure you want to delete this batch? This action cannot be undone.')) return;

    try {
        const data = await makeAPICall('DELETE', `/api/batches/${id}`);
        if (data.success) {
            showNotification('Batch deleted successfully!', 'success');
            await loadBatches();
        } else {
            showNotification('Error: ' + (data.error || 'Could not delete batch'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'deleteBatch');
    }
}

// ====== VIEW BATCH DETAILS ======
/**
 * Show a modal with full batch details and itinerary
 * @param {number} id
 */
function viewBatchDetails(id) {
    const b = batchesData.find(b => b.id === id);
    if (!b) { showNotification('Batch not found', 'error'); return; }

    const price = b.price ? Number(b.price).toLocaleString('en-IN') : '0';
    const totalSeats = b.total_seats || 0;
    const bookedSeats = b.booked_seats || 0;
    const availableSeats = totalSeats - bookedSeats;
    const occupancyPercent = totalSeats > 0 ? Math.round((bookedSeats / totalSeats) * 100) : 0;
    const occupancyColor = occupancyPercent >= 100 ? '#e74c3c' : occupancyPercent > 80 ? '#e67e22' : '#27ae60';

    const detailsHtml = `
        <div style="padding:10px;">
            <h4 style="color:#2c3e50;margin-bottom:15px;">${escapeHtml(b.batch_name)}</h4>
            <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:15px;margin-bottom:20px;">
                <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                    <strong>Departure Date:</strong><br><span>${b.departure_date ? formatDate(b.departure_date) : 'Not specified'}</span>
                </div>
                <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                    <strong>Return Date:</strong><br><span>${b.return_date ? formatDate(b.return_date) : 'Not specified'}</span>
                </div>
                <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                    <strong>Price:</strong><br><span style="font-size:1.2rem;font-weight:bold;color:#27ae60;">₹${price}</span>
                </div>
                <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                    <strong>Status:</strong><br>
                    <span class="status-badge ${getStatusClass(b.status)}">${escapeHtml(b.status || 'Open')}</span>
                </div>
            </div>
            <div style="background:#f8f9fa;padding:15px;border-radius:5px;margin-bottom:20px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
                    <span><strong>Total Seats:</strong> ${totalSeats}</span>
                    <span><strong>Booked:</strong> ${bookedSeats}</span>
                    <span><strong>Available:</strong> ${availableSeats}</span>
                </div>
                <div style="width:100%;height:20px;background:#ecf0f1;border-radius:10px;overflow:hidden;">
                    <div style="width:${occupancyPercent}%;height:20px;background:${occupancyColor};border-radius:10px;"></div>
                </div>
                <div style="text-align:right;margin-top:5px;color:#7f8c8d;">${occupancyPercent}% Occupied</div>
            </div>
            ${b.description ? `<div style="background:#f8f9fa;padding:15px;border-radius:5px;"><strong>Description:</strong><br><p style="margin-top:5px;color:#34495e;">${escapeHtml(b.description)}</p></div>` : ''}
        </div>`;

    const existingModal = document.getElementById('viewBatchModal');
    const existingDetails = document.getElementById('batchDetails');
    const existingOverlay = document.getElementById('modalOverlay');

    if (existingModal && existingDetails) {
        existingDetails.innerHTML = detailsHtml;
        existingModal.style.display = 'block';
        if (existingOverlay) existingOverlay.style.display = 'block';
    } else {
        showModal(`<i class="fas fa-layer-group"></i> Batch Details`, detailsHtml,
            `<button class="action-btn btn-secondary" onclick="closeModal()">Close</button>`);
    }
}

// ====== EXPORT TO CSV ======
/**
 * Export all batches to a CSV file
 */
function exportBatchesToCSV() {
    if (!batchesData.length) { showNotification('No batches to export', 'warning'); return; }

    const headers = ['ID', 'Batch Name', 'Departure Date', 'Return Date', 'Price',
        'Total Seats', 'Booked Seats', 'Available Seats', 'Status', 'Description'];

    const rows = [headers, ...batchesData.map(b => [
        b.id, b.batch_name, b.departure_date, b.return_date, b.price,
        b.total_seats, b.booked_seats, (b.total_seats || 0) - (b.booked_seats || 0),
        b.status, b.description
    ])];

    downloadCSV(rows, `batches_${new Date().toISOString().slice(0, 10)}.csv`);
    showNotification(`Exported ${batchesData.length} batches to CSV`, 'success');
}

// ====== UPDATE BATCH STATUS ======
/**
 * Change the status of a batch
 * @param {number} id
 * @param {string} status
 */
async function updateBatchStatus(id, status) {
    try {
        const data = await makeAPICall('PUT', `/api/batches/${id}`, { status });
        if (data.success) {
            showNotification(`Batch status updated to "${status}"`, 'success');
            await loadBatches();
        } else {
            showNotification('Error: ' + (data.error || 'Status update failed'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'updateBatchStatus');
    }
}

// ====== STATISTICS ======
function updateBatchStatistics() {
    const totalBatches = batchesData.length;
    const openBatches = batchesData.filter(b => b.status === 'Open').length;
    const totalSeats = batchesData.reduce((s, b) => s + (b.total_seats || 0), 0);
    const bookedSeats = batchesData.reduce((s, b) => s + (b.booked_seats || 0), 0);
    const totalValue = batchesData.reduce((s, b) => s + ((b.price || 0) * (b.booked_seats || 0)), 0);

    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalBatches', totalBatches);
    setEl('openBatches', openBatches);
    setEl('totalSeats', totalSeats);
    setEl('bookedSeats', bookedSeats);
    setEl('totalValue', '₹' + totalValue.toLocaleString('en-IN'));
}

// ====== DROPDOWN UPDATE ======
function updateBatchDropdowns() {
    ['add_batch_id', 'edit_batch_id'].forEach(selectId => {
        const select = document.getElementById(selectId);
        if (!select) return;
        const currentVal = select.value;
        select.innerHTML = '<option value="">Select Batch</option>';
        batchesData.forEach(b => {
            const opt = document.createElement('option');
            opt.value = b.id;
            opt.textContent = b.batch_name;
            if (String(b.id) === String(currentVal)) opt.selected = true;
            select.appendChild(opt);
        });
    });
}

// ====== PAGINATION ======
function batchesPreviousPage() {
    if (batchesCurrentPage > 1) { batchesCurrentPage--; displayBatches(); }
}
function batchesNextPage() {
    if (batchesCurrentPage * batchesPerPage < batchesFiltered.length) { batchesCurrentPage++; displayBatches(); }
}

// Aliases for inline HTML
function previousPage() { batchesPreviousPage(); }
function nextPage() { batchesNextPage(); }
function searchBatches() { filterBatches(); }
function clearSearch() {
    const el = document.getElementById('searchBatches');
    if (el) el.value = '';
    batchesFiltered = [...batchesData];
    batchesCurrentPage = 1;
    displayBatches();
}

console.log('✅ batches.js loaded');
