/**
 * batches.js - Batch management functions
 * Alhudha Haj Travel Management System
 */

'use strict';

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
