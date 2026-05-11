/**
 * batches.js - Batch management functions
 * Alhudha Haj Travel Admin Panel
 * Alhudha Haj Travel Management System
 * batches.js - Batch Management for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 * API base: /api/batches
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
// Module-level state
let batchesData = [];
let filteredBatchesData = [];

// ====== LOAD BATCHES ======
/**
 * Fetch all batches from the API and render them
 */
async function loadBatches() {
    showLoading(true);
    try {
        const data = await makeApiCall('GET', '/api/batches');
        batchesData = Array.isArray(data) ? data : (data.batches || []);
        filteredBatchesData = [...batchesData];
        displayBatches(filteredBatchesData);
        console.log(`✅ Loaded ${batchesData.length} batches`);
    } catch (error) {
        handleApiError(error, 'Load batches');
    } finally {
        showLoading(false);
    }
}

// ====== DISPLAY BATCHES ======
/**
 * Render batches array into the table
 * @param {Array} batches
 */
function displayBatches(batches) {
    const tbody = document.getElementById('batchesTableBody');
    if (!tbody) return;

    if (!batches || batches.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align:center;padding:40px;color:#95a5a6;">
                    <i class="fas fa-layer-group" style="font-size:2rem;display:block;margin-bottom:10px;"></i>
                    No batches found
                </td>
            </tr>`;
        updateBatchesCount(0);
        return;
    }

    tbody.innerHTML = batches.map(b => {
        const status = b.status || 'Open';
        const statusClass = status.toLowerCase() === 'open'   ? 'status-active' :
                            status.toLowerCase() === 'closed' ? 'status-inactive' : 'status-pending';
        return `
            <tr>
                <td>${escapeHtml(String(b.id || ''))}</td>
                <td>${escapeHtml(b.batch_name || b.name || '-')}</td>
                <td>${formatDate(b.departure_date || b.start_date)}</td>
                <td>${formatDate(b.return_date || b.end_date)}</td>
                <td>${escapeHtml(String(b.capacity || b.max_capacity || '-'))}</td>
                <td>${escapeHtml(String(b.traveler_count || b.enrolled || 0))}</td>
                <td><span class="status-badge ${statusClass}">${escapeHtml(status)}</span></td>
                <td>
                    <button class="icon-btn btn-view" onclick="viewBatchDetails(${b.id})" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="icon-btn btn-edit" onclick="editBatch(${b.id})" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="icon-btn" onclick="updateBatchStatus(${b.id}, '${status === 'Open' ? 'Closed' : 'Open'}')"
                        title="Toggle Status" style="color:#f39c12;">
                        <i class="fas fa-toggle-${status === 'Open' ? 'on' : 'off'}"></i>
                    </button>
                    <button class="icon-btn btn-delete" onclick="deleteBatch(${b.id})" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>`;
    }).join('');

    updateBatchesCount(batches.length);
}

/**
 * Update the batch count display element
 * @param {number} count
 */
function updateBatchesCount(count) {
    const el = document.getElementById('batchesCount');
    if (el) el.textContent = count;
}

// ====== FILTER BATCHES ======
/**
 * Filter batches by name, status, or date
 */
function filterBatches() {
    const searchEl = document.getElementById('searchBatches');
    const statusEl = document.getElementById('filterBatchStatus');
    const search   = searchEl ? searchEl.value.toLowerCase().trim() : '';
    const status   = statusEl ? statusEl.value.toLowerCase() : '';

    filteredBatchesData = batchesData.filter(b => {
        const name = (b.batch_name || b.name || '').toLowerCase();
        const bStatus = (b.status || '').toLowerCase();

        const matchesSearch = !search || name.includes(search);
        const matchesStatus = !status || bStatus === status;

        return matchesSearch && matchesStatus;
    });

    displayBatches(filteredBatchesData);
}

// ====== CREATE BATCH ======
/**
 * Submit the new batch form to the API
 */
async function createBatch() {
    const form = document.getElementById('batchForm') || document.getElementById('addBatchForm');
    if (!form) { showNotification('Batch form not found', 'error'); return; }

    const formData = new FormData(form);
    const batchData = {};
    formData.forEach((value, key) => { if (value !== '') batchData[key] = value; });

    if (!batchData.batch_name && !batchData.name) {
// ── State ────────────────────────────────────────────────────
let allBatches = [];
let filteredBatches = [];
let batchesPage = 1;
const BATCHES_PER_PAGE = 20;

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    SessionManager.initPage(async () => {
        await loadBatches();
        initBatchSearchListeners();
    });
});

function initBatchSearchListeners() {
    const searchEl = document.getElementById('searchBatches');
    const statusEl = document.getElementById('batchStatusFilter');
    if (searchEl) searchEl.addEventListener('input', debounce(filterBatches, 250));
    if (statusEl) statusEl.addEventListener('change', filterBatches);
}

// ── Load & Display ───────────────────────────────────────────

/**
 * Fetch all batches from the API
 */
async function loadBatches() {
    const tbody = document.getElementById('batchesTableBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="10" class="loading"><i class="fas fa-spinner fa-spin"></i> Loading batches…</td></tr>';

    try {
        const data = await makeAPICall('GET', '/api/batches');
        if (data.success) {
            allBatches = data.batches || [];
            filteredBatches = [...allBatches];
            batchesPage = 1;
            displayBatches();
            updateBatchStats();
        } else {
            throw new Error(data.error || 'Failed to load batches');
        }
    } catch (error) {
        handleError(error, 'loadBatches');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; padding:40px;">
                <i class="fas fa-exclamation-triangle" style="color:#e74c3c; font-size:2rem;"></i>
                <p style="color:#e74c3c; margin:10px 0;">${escapeHtml(error.message)}</p>
                <button class="action-btn btn-primary" onclick="loadBatches()"><i class="fas fa-redo"></i> Retry</button>
            </td></tr>`;
        }
    }
}

/**
 * Render the current page of batches
 */
function displayBatches() {
    const tbody = document.getElementById('batchesTableBody');
    if (!tbody) return;

    const start = (batchesPage - 1) * BATCHES_PER_PAGE;
    const page  = filteredBatches.slice(start, start + BATCHES_PER_PAGE);

    if (page.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding:30px; color:#7f8c8d;">No batches found</td></tr>';
        updateBatchPagination();
        return;
    }

    tbody.innerHTML = page.map((b) => {
        const occupancy = b.total_seats > 0 ? Math.round((b.booked_seats / b.total_seats) * 100) : 0;
        const statusClass = b.status === 'Open' ? 'status-active' : 'status-inactive';
        return `<tr>
            <td>${b.id}</td>
            <td><strong>${escapeHtml(b.batch_name)}</strong></td>
            <td>${b.total_seats || 0}</td>
            <td>${b.booked_seats || 0}</td>
            <td>
                <div style="display:flex; align-items:center; gap:8px;">
                    <div style="flex:1; background:#ecf0f1; border-radius:10px; height:8px;">
                        <div style="width:${occupancy}%; background:${occupancy > 80 ? '#e74c3c' : '#27ae60'}; height:8px; border-radius:10px;"></div>
                    </div>
                    <span style="font-size:0.85rem;">${occupancy}%</span>
                </div>
            </td>
            <td>${formatCurrency(b.price || 0)}</td>
            <td>${b.departure_date ? formatDate(b.departure_date) : '-'}</td>
            <td>${b.return_date ? formatDate(b.return_date) : '-'}</td>
            <td><span class="status-badge ${statusClass}">${escapeHtml(b.status || 'Open')}</span></td>
            <td>
                <button class="icon-btn" onclick="editBatch(${b.id})" title="Edit"><i class="fas fa-edit"></i></button>
                <button class="icon-btn" onclick="updateBatchStatus(${b.id}, '${b.status === 'Open' ? 'Closed' : 'Open'}')" title="Toggle Status">
                    <i class="fas fa-${b.status === 'Open' ? 'lock' : 'lock-open'}"></i>
                </button>
                <button class="icon-btn" style="color:#e74c3c;" onclick="deleteBatch(${b.id})" title="Delete"><i class="fas fa-trash"></i></button>
            </td>
        </tr>`;
    }).join('');

    updateBatchPagination();
}

// ── Filter ───────────────────────────────────────────────────

/**
 * Filter batches by search text and status
 */
function filterBatches() {
    const search = (document.getElementById('searchBatches')?.value || '').toLowerCase();
    const status = document.getElementById('batchStatusFilter')?.value || 'all';

    filteredBatches = allBatches.filter((b) => {
        const matchSearch = !search || (b.batch_name || '').toLowerCase().includes(search);
        const matchStatus = status === 'all' || b.status === status;
        return matchSearch && matchStatus;
    });

    batchesPage = 1;
    displayBatches();
}

// ── Form Visibility ──────────────────────────────────────────

function showAddBatchForm() {
    const form = document.getElementById('addBatchForm');
    if (!form) return;
    form.style.display = 'block';
    form.scrollIntoView({ behavior: 'smooth' });
}

function hideAddBatchForm() {
    const form = document.getElementById('addBatchForm');
    if (form) form.style.display = 'none';
    document.getElementById('batchCreateForm')?.reset();
}

// ── CRUD ─────────────────────────────────────────────────────

/**
 * Create a new batch
 */
async function createBatch(event) {
    if (event) event.preventDefault();

    const getData = (id) => (document.getElementById(id)?.value || '').trim();

    const batchData = {
        batch_name:     getData('batch_name'),
        total_seats:    parseInt(getData('total_seats')) || 150,
        price:          parseFloat(getData('price')) || null,
        departure_date: getData('departure_date') || null,
        return_date:    getData('return_date') || null,
        status:         getData('batch_status') || 'Open',
        description:    getData('batch_description') || null
    };

    if (!batchData.batch_name) {
        showNotification('Batch name is required', 'error');
        return;
    }

    showLoading(true);
    try {
        const result = await makeApiCall('POST', '/api/batches', batchData);
        if (result.success || result.id) {
            showNotification('Batch created successfully!', 'success');
            form.reset();
            const container = document.getElementById('addBatchForm') || document.getElementById('batchFormContainer');
            if (container) container.style.display = 'none';
            await loadBatches();
        } else {
            showNotification(result.error || 'Failed to create batch', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Create batch');
    } finally {
        showLoading(false);
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
 * @param {number} batchId
 */
async function editBatch(batchId) {
    showLoading(true);
    try {
        const response = await makeApiCall('GET', `/api/batches/${batchId}`);
        const b = response.batch || response;

        const fields = [
            'batch_name','name','departure_date','start_date',
            'return_date','end_date','capacity','max_capacity',
            'status','description','price','notes'
        ];

        fields.forEach(field => {
            const el = document.getElementById(`edit_${field}`) || document.getElementById(field);
            if (el && b[field] !== undefined) el.value = b[field];
        });

        const idField = document.getElementById('edit_batch_id') || document.getElementById('editBatchId');
        if (idField) idField.value = batchId;

        const editForm = document.getElementById('editBatchForm') || document.getElementById('editBatchContainer');
        if (editForm) {
            editForm.style.display = 'block';
            editForm.scrollIntoView({ behavior: 'smooth' });
        }
    } catch (error) {
        handleApiError(error, 'Load batch for editing');
    } finally {
        showLoading(false);
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
 * Save changes to an existing batch
 */
async function updateBatch() {
    const idField = document.getElementById('edit_batch_id') || document.getElementById('editBatchId');
    if (!idField || !idField.value) {
        showNotification('No batch selected for update', 'error');
        return;
    }

    const batchId = idField.value;
    const form = document.getElementById('editBatchForm') || document.getElementById('editBatchContainer');
    if (!form) { showNotification('Edit form not found', 'error'); return; }

    const formData = new FormData(form.querySelector('form') || form);
    const batchData = {};
    formData.forEach((value, key) => { if (key !== 'id') batchData[key] = value; });

    showLoading(true);
    try {
        const result = await makeApiCall('PUT', `/api/batches/${batchId}`, batchData);
        if (result.success || result.id) {
            showNotification('Batch updated successfully!', 'success');
            if (form) form.style.display = 'none';
            await loadBatches();
        } else {
            showNotification(result.error || 'Failed to update batch', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Update batch');
    } finally {
        showLoading(false);
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

 * Delete a batch after confirmation
 * @param {number} batchId
 */
function deleteBatch(batchId) {
    const batch = batchesData.find(b => b.id === batchId);
    const name  = batch ? (batch.batch_name || batch.name || `ID ${batchId}`) : `ID ${batchId}`;

    showConfirmation(
        `Are you sure you want to delete batch "${name}"? This action cannot be undone.`,
        async () => {
            showLoading(true);
            try {
                const result = await makeApiCall('DELETE', `/api/batches/${batchId}`);
                if (result.success || result.message) {
                    showNotification('Batch deleted successfully!', 'success');
                    await loadBatches();
                } else {
                    showNotification(result.error || 'Failed to delete batch', 'error');
                }
            } catch (error) {
                handleApiError(error, 'Delete batch');
            } finally {
                showLoading(false);
            }
        }
    );
}

// ====== VIEW BATCH DETAILS ======
/**
 * Show a modal with full batch details
 * @param {number} batchId
 */
async function viewBatchDetails(batchId) {
    showLoading(true);
    try {
        const response = await makeApiCall('GET', `/api/batches/${batchId}`);
        const b = response.batch || response;

        const content = `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;">
                <div><strong>Batch Name:</strong><br>${escapeHtml(b.batch_name || b.name || '-')}</div>
                <div><strong>Status:</strong><br>${escapeHtml(b.status || '-')}</div>
                <div><strong>Departure Date:</strong><br>${formatDate(b.departure_date || b.start_date)}</div>
                <div><strong>Return Date:</strong><br>${formatDate(b.return_date || b.end_date)}</div>
                <div><strong>Capacity:</strong><br>${escapeHtml(String(b.capacity || b.max_capacity || '-'))}</div>
                <div><strong>Enrolled:</strong><br>${escapeHtml(String(b.traveler_count || b.enrolled || 0))}</div>
                <div><strong>Price:</strong><br>${formatCurrency(b.price)}</div>
                <div><strong>Created:</strong><br>${formatDate(b.created_at)}</div>
                <div style="grid-column:1/-1;"><strong>Description:</strong><br>${escapeHtml(b.description || '-')}</div>
                <div style="grid-column:1/-1;"><strong>Notes:</strong><br>${escapeHtml(b.notes || '-')}</div>
            </div>`;

        showModal(`<i class="fas fa-layer-group" style="color:#3498db;margin-right:8px;"></i>Batch Details — ${escapeHtml(b.batch_name || b.name || '')}`, content, [
            { label: '<i class="fas fa-edit"></i> Edit', class: 'btn-primary', onClick: `closeModal(); editBatch(${batchId});` },
            { label: '<i class="fas fa-times"></i> Close', class: 'btn-secondary', onClick: 'closeModal()' }
        ]);
    } catch (error) {
        handleApiError(error, 'Load batch details');
    } finally {
        showLoading(false);
    }
}

// ====== EXPORT TO CSV ======
/**
 * Export the current batch list to a CSV file
 */
function exportBatchesToCSV() {
    const data = filteredBatchesData.length > 0 ? filteredBatchesData : batchesData;
    if (!data || data.length === 0) {
        showNotification('No batches to export', 'warning');
        return;
    }

    const headers = ['ID','Batch Name','Departure Date','Return Date','Capacity','Enrolled','Status','Price','Description'];
    const rows = data.map(b => [
        b.id, b.batch_name || b.name,
        b.departure_date || b.start_date,
        b.return_date || b.end_date,
        b.capacity || b.max_capacity,
        b.traveler_count || b.enrolled || 0,
        b.status, b.price, b.description
    ].map(v => `"${String(v || '').replace(/"/g, '""')}"`));

    const csv  = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href     = url;
    link.download = `batches_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    showNotification(`Exported ${data.length} batches to CSV`, 'success');
}

// ====== UPDATE BATCH STATUS ======
/**
 * Change the status of a batch (Open / Closed)
 * @param {number} batchId
 * @param {string} status
 */
async function updateBatchStatus(batchId, status) {
    showLoading(true);
    try {
        const result = await makeApiCall('PUT', `/api/batches/${batchId}`, { status });
        if (result.success || result.id) {
            showNotification(`Batch status updated to "${status}"`, 'success');
            await loadBatches();
        } else {
            showNotification(result.error || 'Failed to update batch status', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Update batch status');
    } finally {
        showLoading(false);
    }
}
    const btn  = document.querySelector('#batchCreateForm button[type="submit"]');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating…'; btn.disabled = true; }

    try {
        const data = await makeAPICall('POST', '/api/batches', batchData);
        if (data.success) {
            showNotification('Batch created successfully!', 'success');
            hideAddBatchForm();
            await loadBatches();
        } else {
            throw new Error(data.error || 'Could not create batch');
        }
    } catch (error) {
        handleError(error, 'createBatch');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Load batch data into the edit modal
 * @param {number} id
 */
async function editBatch(id) {
    try {
        const data = await makeAPICall('GET', `/api/batches/${id}`);
        if (!data.success || !data.batch) throw new Error(data.error || 'Batch not found');

        const b = data.batch;
        const set = (elId, val) => { const el = document.getElementById(elId); if (el) el.value = val || ''; };

        set('edit_batch_id',          b.id);
        set('edit_batch_name',        b.batch_name);
        set('edit_total_seats',       b.total_seats);
        set('edit_price',             b.price);
        set('edit_departure_date',    b.departure_date ? b.departure_date.slice(0, 10) : '');
        set('edit_return_date',       b.return_date ? b.return_date.slice(0, 10) : '');
        set('edit_batch_status',      b.status);
        set('edit_batch_description', b.description);

        const modal   = document.getElementById('editBatchModal');
        const overlay = document.getElementById('modalOverlay');
        if (modal)   modal.style.display   = 'block';
        if (overlay) overlay.style.display = 'block';
    } catch (error) {
        handleError(error, 'editBatch');
    }
}

/**
 * Submit the edit batch form
 */
async function updateBatch(event) {
    if (event) event.preventDefault();

    const id = document.getElementById('edit_batch_id')?.value;
    if (!id) return;

    const getData = (elId) => (document.getElementById(elId)?.value || '').trim();

    const batchData = {
        batch_name:     getData('edit_batch_name'),
        total_seats:    parseInt(getData('edit_total_seats')) || undefined,
        price:          parseFloat(getData('edit_price')) || undefined,
        departure_date: getData('edit_departure_date') || null,
        return_date:    getData('edit_return_date') || null,
        status:         getData('edit_batch_status'),
        description:    getData('edit_batch_description') || null
    };

    const btn  = document.querySelector('#editBatchForm button[type="submit"]');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating…'; btn.disabled = true; }

    try {
        const data = await makeAPICall('PUT', `/api/batches/${id}`, batchData);
        if (data.success) {
            showNotification('Batch updated successfully!', 'success');
            closeBatchModal();
            await loadBatches();
        } else {
            throw new Error(data.error || 'Could not update batch');
        }
    } catch (error) {
        handleError(error, 'updateBatch');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Delete a batch by ID
 * @param {number} id
 */
async function deleteBatch(id) {
    const b = allBatches.find((x) => x.id === id);
    const name = b ? b.batch_name : `ID ${id}`;
    if (!confirmAction(`Delete batch "${name}"? This cannot be undone.`)) return;

    try {
        const data = await makeAPICall('DELETE', `/api/batches/${id}`);
        if (data.success) {
            showNotification('Batch deleted successfully!', 'success');
            await loadBatches();
        } else {
            throw new Error(data.error || 'Could not delete batch');
        }
    } catch (error) {
        handleError(error, 'deleteBatch');
    }
}

/**
 * Update a batch's status
 * @param {number} id
 * @param {string} status - 'Open' | 'Closed' | 'Full'
 */
async function updateBatchStatus(id, status) {
    const b = allBatches.find((x) => x.id === id);
    const name = b ? b.batch_name : `ID ${id}`;
    if (!confirmAction(`Change status of "${name}" to "${status}"?`)) return;

    try {
        const data = await makeAPICall('PUT', `/api/batches/${id}`, { status });
        if (data.success) {
            showNotification(`Batch status updated to ${status}`, 'success');
            await loadBatches();
        } else {
            throw new Error(data.error || 'Could not update batch status');
        }
    } catch (error) {
        handleError(error, 'updateBatchStatus');
    }
}

// ── Export ───────────────────────────────────────────────────

/**
 * Export filtered batches to CSV
 */
function exportBatchesToCSV() {
    if (!filteredBatches.length) { showNotification('No batches to export', 'warning'); return; }
    downloadCSV(
        filteredBatches,
        ['id', 'batch_name', 'total_seats', 'booked_seats', 'price', 'departure_date', 'return_date', 'status'],
        ['ID', 'Batch Name', 'Total Seats', 'Booked Seats', 'Price', 'Departure Date', 'Return Date', 'Status'],
        `batches_${new Date().toISOString().slice(0, 10)}.csv`
    );
}

// ── Pagination ───────────────────────────────────────────────

function updateBatchPagination() {
    const total = filteredBatches.length;
    const start = total > 0 ? (batchesPage - 1) * BATCHES_PER_PAGE + 1 : 0;
    const end   = Math.min(batchesPage * BATCHES_PER_PAGE, total);
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalCount',  total);
    setEl('showingFrom', start);
    setEl('showingTo',   end);
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    if (prevBtn) prevBtn.disabled = batchesPage === 1;
    if (nextBtn) nextBtn.disabled = end >= total;
}

function prevBatchPage() {
    if (batchesPage > 1) { batchesPage--; displayBatches(); }
}

function nextBatchPage() {
    if (batchesPage * BATCHES_PER_PAGE < filteredBatches.length) { batchesPage++; displayBatches(); }
}

// ── Stats ────────────────────────────────────────────────────

function updateBatchStats() {
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalBatches',  allBatches.length);
    setEl('openBatches',   allBatches.filter((b) => b.status === 'Open').length);
    setEl('closedBatches', allBatches.filter((b) => b.status === 'Closed').length);
    setEl('totalSeats',    allBatches.reduce((s, b) => s + (b.total_seats || 0), 0));
    setEl('bookedSeats',   allBatches.reduce((s, b) => s + (b.booked_seats || 0), 0));
}

// ── Modal Helpers ────────────────────────────────────────────

function closeBatchModal() {
    const modal   = document.getElementById('editBatchModal');
    const overlay = document.getElementById('modalOverlay');
    if (modal)   modal.style.display   = 'none';
    if (overlay) overlay.style.display = 'none';
}

// ── Form submit wiring ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('batchCreateForm')?.addEventListener('submit', createBatch);
    document.getElementById('editBatchForm')?.addEventListener('submit', updateBatch);
});

// Expose globals
window.loadBatches        = loadBatches;
window.filterBatches      = filterBatches;
window.showAddBatchForm   = showAddBatchForm;
window.hideAddBatchForm   = hideAddBatchForm;
window.editBatch          = editBatch;
window.deleteBatch        = deleteBatch;
window.updateBatchStatus  = updateBatchStatus;
window.exportBatchesToCSV = exportBatchesToCSV;
window.closeBatchModal    = closeBatchModal;
window.prevBatchPage      = prevBatchPage;
window.nextBatchPage      = nextBatchPage;

console.log('✅ batches.js loaded');
