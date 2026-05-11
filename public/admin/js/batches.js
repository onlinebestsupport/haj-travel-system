/**
 * batches.js - Batch Management for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 * API base: /api/batches
 */

'use strict';

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
