/**
 * travelers.js - Traveler Management for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 * API base: /api/travelers
 */

'use strict';

// ── State ────────────────────────────────────────────────────
let allTravelers = [];
let filteredTravelers = [];
let allBatches = [];
let travelersPage = 1;
const TRAVELERS_PER_PAGE = 20;

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    SessionManager.initPage(async () => {
        await Promise.all([loadTravelers(), loadBatchesForSelect()]);
        initTravelerSearchListeners();
    });
});

function initTravelerSearchListeners() {
    const searchEl = document.getElementById('searchTravelers');
    const batchEl  = document.getElementById('batchFilter');
    const statusEl = document.getElementById('statusFilter');
    if (searchEl) searchEl.addEventListener('input', debounce(filterTravelers, 250));
    if (batchEl)  batchEl.addEventListener('change', filterTravelers);
    if (statusEl) statusEl.addEventListener('change', filterTravelers);
}

// ── Load & Display ───────────────────────────────────────────

/**
 * Fetch all travelers from the API
 */
async function loadTravelers() {
    const tbody = document.getElementById('travelersTableBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="12" class="loading"><i class="fas fa-spinner fa-spin"></i> Loading travelers…</td></tr>';

    try {
        const data = await makeAPICall('GET', '/api/travelers');
        if (data.success) {
            allTravelers = data.travelers || [];
            filteredTravelers = [...allTravelers];
            travelersPage = 1;
            displayTravelers();
            updateTravelerStats();
        } else {
            throw new Error(data.error || 'Failed to load travelers');
        }
    } catch (error) {
        handleError(error, 'loadTravelers');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="12" style="text-align:center; padding:40px;">
                <i class="fas fa-exclamation-triangle" style="color:#e74c3c; font-size:2rem;"></i>
                <p style="color:#e74c3c; margin:10px 0;">${escapeHtml(error.message)}</p>
                <button class="action-btn btn-primary" onclick="loadTravelers()"><i class="fas fa-redo"></i> Retry</button>
            </td></tr>`;
        }
    }
}

/**
 * Load batches for the batch select dropdown
 */
async function loadBatchesForSelect() {
    try {
        const data = await makeAPICall('GET', '/api/batches');
        if (data.success) {
            allBatches = data.batches || [];
            populateBatchSelects();
        }
    } catch (error) {
        console.warn('Could not load batches for select:', error.message);
    }
}

function populateBatchSelects() {
    const selects = document.querySelectorAll('.batch-select, #batch_id, #batchFilter');
    selects.forEach((sel) => {
        const isFilter = sel.id === 'batchFilter';
        const current  = sel.value;
        sel.innerHTML  = isFilter ? '<option value="all">All Batches</option>' : '<option value="">Select Batch</option>';
        allBatches.forEach((b) => {
            const opt = document.createElement('option');
            opt.value = b.id;
            opt.textContent = `${b.batch_name} (${b.status || 'Open'})`;
            sel.appendChild(opt);
        });
        if (current) sel.value = current;
    });
}

/**
 * Render the current page of travelers
 */
function displayTravelers() {
    const tbody = document.getElementById('travelersTableBody');
    if (!tbody) return;

    const start = (travelersPage - 1) * TRAVELERS_PER_PAGE;
    const page  = filteredTravelers.slice(start, start + TRAVELERS_PER_PAGE);

    if (page.length === 0) {
        tbody.innerHTML = '<tr><td colspan="12" style="text-align:center; padding:30px; color:#7f8c8d;">No travelers found</td></tr>';
        updateTravelerPagination();
        return;
    }

    tbody.innerHTML = page.map((t) => `<tr>
        <td>${t.id}</td>
        <td><strong>${escapeHtml(t.first_name)} ${escapeHtml(t.last_name)}</strong></td>
        <td>${escapeHtml(t.passport_no || '-')}</td>
        <td>${escapeHtml(t.mobile || '-')}</td>
        <td>${escapeHtml(t.email || '-')}</td>
        <td>${escapeHtml(t.batch_name || '-')}</td>
        <td><span class="status-badge ${t.passport_status === 'Active' ? 'status-active' : 'status-inactive'}">${escapeHtml(t.passport_status || '-')}</span></td>
        <td>${escapeHtml(t.vaccine_status || '-')}</td>
        <td>${formatCurrency(t.total_paid || 0)}</td>
        <td>${formatCurrency(t.pending_amount || 0)}</td>
        <td>${t.created_at ? formatDate(t.created_at) : '-'}</td>
        <td>
            <button class="icon-btn" onclick="viewTravelerDetails(${t.id})" title="View"><i class="fas fa-eye"></i></button>
            <button class="icon-btn" onclick="editTraveler(${t.id})" title="Edit"><i class="fas fa-edit"></i></button>
            <button class="icon-btn" style="color:#e74c3c;" onclick="deleteTraveler(${t.id})" title="Delete"><i class="fas fa-trash"></i></button>
        </td>
    </tr>`).join('');

    updateTravelerPagination();
}

// ── Filter ───────────────────────────────────────────────────

/**
 * Filter travelers by search text, batch, and status
 */
function filterTravelers() {
    const search = (document.getElementById('searchTravelers')?.value || '').toLowerCase();
    const batch  = document.getElementById('batchFilter')?.value || 'all';
    const status = document.getElementById('statusFilter')?.value || 'all';

    filteredTravelers = allTravelers.filter((t) => {
        const name = `${t.first_name} ${t.last_name}`.toLowerCase();
        const matchSearch = !search ||
            name.includes(search) ||
            (t.passport_no || '').toLowerCase().includes(search) ||
            (t.mobile || '').includes(search) ||
            (t.email || '').toLowerCase().includes(search);
        const matchBatch  = batch === 'all' || String(t.batch_id) === String(batch);
        const matchStatus = status === 'all' || t.passport_status === status;
        return matchSearch && matchBatch && matchStatus;
    });

    travelersPage = 1;
    displayTravelers();
}

// ── Form Visibility ──────────────────────────────────────────

function showAddTravelerForm() {
    const form = document.getElementById('addTravelerForm');
    if (!form) return;
    form.style.display = 'block';
    form.scrollIntoView({ behavior: 'smooth' });
}

function hideAddTravelerForm() {
    const form = document.getElementById('addTravelerForm');
    if (form) form.style.display = 'none';
    document.getElementById('travelerCreateForm')?.reset();
}

// ── CRUD ─────────────────────────────────────────────────────

/**
 * Create a new traveler
 */
async function createTraveler(event) {
    if (event) event.preventDefault();

    const getData = (id) => (document.getElementById(id)?.value || '').trim();

    const travelerData = {
        first_name:   getData('first_name'),
        last_name:    getData('last_name'),
        passport_no:  getData('passport_no'),
        mobile:       getData('mobile'),
        email:        getData('email') || null,
        batch_id:     getData('batch_id'),
        gender:       getData('gender') || null,
        dob:          getData('dob') || null,
        passport_status:    getData('passport_status') || 'Active',
        vaccine_status:     getData('vaccine_status') || 'Not Vaccinated',
        emergency_contact:  getData('emergency_contact') || null,
        emergency_phone:    getData('emergency_phone') || null,
        medical_notes:      getData('medical_notes') || null
    };

    if (!travelerData.first_name || !travelerData.last_name || !travelerData.passport_no || !travelerData.mobile || !travelerData.batch_id) {
        showNotification('First name, last name, passport number, mobile and batch are required', 'error');
        return;
    }

    const btn  = document.querySelector('#travelerCreateForm button[type="submit"]');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating…'; btn.disabled = true; }

    try {
        const data = await makeAPICall('POST', '/api/travelers', travelerData);
        if (data.success) {
            showNotification('Traveler created successfully!', 'success');
            hideAddTravelerForm();
            await loadTravelers();
        } else {
            throw new Error(data.error || 'Could not create traveler');
        }
    } catch (error) {
        handleError(error, 'createTraveler');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Load traveler data into the edit form/modal
 * @param {number} id
 */
async function editTraveler(id) {
    try {
        const data = await makeAPICall('GET', `/api/travelers/${id}`);
        if (!data.success || !data.traveler) throw new Error(data.error || 'Traveler not found');

        const t = data.traveler;
        const set = (elId, val) => { const el = document.getElementById(elId); if (el) el.value = val || ''; };

        set('edit_traveler_id',  t.id);
        set('edit_first_name',   t.first_name);
        set('edit_last_name',    t.last_name);
        set('edit_passport_no',  t.passport_no);
        set('edit_mobile',       t.mobile);
        set('edit_email',        t.email);
        set('edit_batch_id',     t.batch_id);
        set('edit_gender',       t.gender);
        set('edit_dob',          t.dob ? t.dob.slice(0, 10) : '');
        set('edit_passport_status',  t.passport_status);
        set('edit_vaccine_status',   t.vaccine_status);
        set('edit_emergency_contact', t.emergency_contact);
        set('edit_emergency_phone',   t.emergency_phone);
        set('edit_medical_notes',     t.medical_notes);

        const modal   = document.getElementById('editTravelerModal');
        const overlay = document.getElementById('modalOverlay');
        if (modal)   modal.style.display   = 'block';
        if (overlay) overlay.style.display = 'block';
    } catch (error) {
        handleError(error, 'editTraveler');
    }
}

/**
 * Submit the edit traveler form
 */
async function updateTraveler(event) {
    if (event) event.preventDefault();

    const id = document.getElementById('edit_traveler_id')?.value;
    if (!id) return;

    const getData = (elId) => (document.getElementById(elId)?.value || '').trim();

    const travelerData = {
        first_name:   getData('edit_first_name'),
        last_name:    getData('edit_last_name'),
        passport_no:  getData('edit_passport_no'),
        mobile:       getData('edit_mobile'),
        email:        getData('edit_email') || null,
        batch_id:     getData('edit_batch_id'),
        gender:       getData('edit_gender') || null,
        dob:          getData('edit_dob') || null,
        passport_status:    getData('edit_passport_status'),
        vaccine_status:     getData('edit_vaccine_status'),
        emergency_contact:  getData('edit_emergency_contact') || null,
        emergency_phone:    getData('edit_emergency_phone') || null,
        medical_notes:      getData('edit_medical_notes') || null
    };

    const btn  = document.querySelector('#editTravelerForm button[type="submit"]');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating…'; btn.disabled = true; }

    try {
        const data = await makeAPICall('PUT', `/api/travelers/${id}`, travelerData);
        if (data.success) {
            showNotification('Traveler updated successfully!', 'success');
            closeTravelerModal();
            await loadTravelers();
        } else {
            throw new Error(data.error || 'Could not update traveler');
        }
    } catch (error) {
        handleError(error, 'updateTraveler');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Delete a traveler by ID
 * @param {number} id
 */
async function deleteTraveler(id) {
    const t = allTravelers.find((x) => x.id === id);
    const name = t ? `${t.first_name} ${t.last_name}` : `ID ${id}`;
    if (!confirmAction(`Delete traveler "${name}"? This cannot be undone.`)) return;

    try {
        const data = await makeAPICall('DELETE', `/api/travelers/${id}`);
        if (data.success) {
            showNotification('Traveler deleted successfully!', 'success');
            await loadTravelers();
        } else {
            throw new Error(data.error || 'Could not delete traveler');
        }
    } catch (error) {
        handleError(error, 'deleteTraveler');
    }
}

/**
 * Show full traveler details in a modal
 * @param {number} id
 */
async function viewTravelerDetails(id) {
    try {
        showLoading('Loading traveler details…');
        const data = await makeAPICall('GET', `/api/travelers/${id}`);
        hideLoading();

        if (!data.success || !data.traveler) throw new Error(data.error || 'Traveler not found');
        const t = data.traveler;

        const paymentRows = (t.payments || []).map((p) => `
            <tr>
                <td>${formatDate(p.payment_date)}</td>
                <td>${formatCurrency(p.amount)}</td>
                <td>${escapeHtml(p.payment_method || '-')}</td>
                <td><span class="status-badge ${p.status === 'completed' ? 'status-active' : 'status-inactive'}">${escapeHtml(p.status)}</span></td>
            </tr>`).join('') || '<tr><td colspan="4" style="text-align:center;">No payments</td></tr>';

        const content = `
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px; margin-bottom:20px;">
                <div><strong>Name:</strong> ${escapeHtml(t.first_name)} ${escapeHtml(t.last_name)}</div>
                <div><strong>Passport:</strong> ${escapeHtml(t.passport_no || '-')}</div>
                <div><strong>Mobile:</strong> ${escapeHtml(t.mobile || '-')}</div>
                <div><strong>Email:</strong> ${escapeHtml(t.email || '-')}</div>
                <div><strong>Batch:</strong> ${escapeHtml(t.batch_name || '-')}</div>
                <div><strong>Gender:</strong> ${escapeHtml(t.gender || '-')}</div>
                <div><strong>DOB:</strong> ${t.dob ? formatDate(t.dob) : '-'}</div>
                <div><strong>Passport Status:</strong> ${escapeHtml(t.passport_status || '-')}</div>
                <div><strong>Vaccine Status:</strong> ${escapeHtml(t.vaccine_status || '-')}</div>
                <div><strong>Wheelchair:</strong> ${escapeHtml(t.wheelchair || 'No')}</div>
                <div><strong>Total Paid:</strong> ${formatCurrency(t.payment_summary?.total_paid || 0)}</div>
                <div><strong>Pending:</strong> ${formatCurrency(t.payment_summary?.pending_amount || 0)}</div>
            </div>
            <h4 style="margin-bottom:10px;">Payment History</h4>
            <div style="overflow-x:auto;">
                <table style="width:100%; border-collapse:collapse; font-size:0.9rem;">
                    <thead><tr style="background:#2c3e50; color:white;">
                        <th style="padding:8px;">Date</th>
                        <th style="padding:8px;">Amount</th>
                        <th style="padding:8px;">Method</th>
                        <th style="padding:8px;">Status</th>
                    </tr></thead>
                    <tbody>${paymentRows}</tbody>
                </table>
            </div>`;

        showModal(`Traveler: ${t.first_name} ${t.last_name}`, content);
    } catch (error) {
        hideLoading();
        handleError(error, 'viewTravelerDetails');
    }
}

// ── Export ───────────────────────────────────────────────────

/**
 * Export filtered travelers to CSV
 */
function exportTravelersToCSV() {
    if (!filteredTravelers.length) { showNotification('No travelers to export', 'warning'); return; }
    downloadCSV(
        filteredTravelers,
        ['id', 'first_name', 'last_name', 'passport_no', 'mobile', 'email', 'batch_name', 'passport_status', 'vaccine_status', 'total_paid', 'created_at'],
        ['ID', 'First Name', 'Last Name', 'Passport No', 'Mobile', 'Email', 'Batch', 'Passport Status', 'Vaccine Status', 'Total Paid', 'Created'],
        `travelers_${new Date().toISOString().slice(0, 10)}.csv`
    );
}

// ── Pagination ───────────────────────────────────────────────

function updateTravelerPagination() {
    const total = filteredTravelers.length;
    const start = total > 0 ? (travelersPage - 1) * TRAVELERS_PER_PAGE + 1 : 0;
    const end   = Math.min(travelersPage * TRAVELERS_PER_PAGE, total);
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalCount',  total);
    setEl('showingFrom', start);
    setEl('showingTo',   end);
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    if (prevBtn) prevBtn.disabled = travelersPage === 1;
    if (nextBtn) nextBtn.disabled = end >= total;
}

function prevTravelerPage() {
    if (travelersPage > 1) { travelersPage--; displayTravelers(); }
}

function nextTravelerPage() {
    if (travelersPage * TRAVELERS_PER_PAGE < filteredTravelers.length) { travelersPage++; displayTravelers(); }
}

// ── Stats ────────────────────────────────────────────────────

function updateTravelerStats() {
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalTravelers',    allTravelers.length);
    setEl('activeTravelers',   allTravelers.filter((t) => t.passport_status === 'Active').length);
    setEl('vaccinatedCount',   allTravelers.filter((t) => t.vaccine_status === 'Vaccinated').length);
    setEl('totalCollected',    formatCurrency(allTravelers.reduce((s, t) => s + (parseFloat(t.total_paid) || 0), 0)));
}

// ── Modal Helpers ────────────────────────────────────────────

function closeTravelerModal() {
    const modal   = document.getElementById('editTravelerModal');
    const overlay = document.getElementById('modalOverlay');
    if (modal)   modal.style.display   = 'none';
    if (overlay) overlay.style.display = 'none';
}

// ── Form submit wiring ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('travelerCreateForm')?.addEventListener('submit', createTraveler);
    document.getElementById('editTravelerForm')?.addEventListener('submit', updateTraveler);
});

// Expose globals
window.loadTravelers         = loadTravelers;
window.filterTravelers       = filterTravelers;
window.showAddTravelerForm   = showAddTravelerForm;
window.hideAddTravelerForm   = hideAddTravelerForm;
window.editTraveler          = editTraveler;
window.deleteTraveler        = deleteTraveler;
window.viewTravelerDetails   = viewTravelerDetails;
window.exportTravelersToCSV  = exportTravelersToCSV;
window.closeTravelerModal    = closeTravelerModal;
window.prevTravelerPage      = prevTravelerPage;
window.nextTravelerPage      = nextTravelerPage;

console.log('✅ travelers.js loaded');
