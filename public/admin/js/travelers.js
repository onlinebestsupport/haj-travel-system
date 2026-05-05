/**
 * travelers.js - Traveler management functions
 * Alhudha Haj Travel Admin Panel
 */

'use strict';

// ====== STATE ======
let travelersData = [];
let travelersFiltered = [];
let travelersBatches = [];
let travelersCurrentPage = 1;
const travelersPerPage = 10;
let travelersCurrentEditId = null;

// ====== LOAD TRAVELERS ======
/**
 * Fetch all travelers from /api/travelers and populate the table
 */
async function loadTravelers() {
    const tableBody = document.getElementById('travelersTableBody');
    if (tableBody) {
        tableBody.innerHTML = '<tr><td colspan="9" class="loading"><i class="fas fa-spinner fa-spin"></i> Loading travelers...</td></tr>';
    }

    try {
        const data = await makeAPICall('GET', '/api/travelers');
        if (data.success && Array.isArray(data.travelers)) {
            travelersData = data.travelers;
            travelersFiltered = [...travelersData];
            console.log(`✅ Loaded ${travelersData.length} travelers`);
        } else {
            travelersData = [];
            travelersFiltered = [];
            showNotification('No travelers found', 'info');
        }
    } catch (error) {
        handleAPIError(error, 'loadTravelers');
        travelersData = [];
        travelersFiltered = [];
    }

    displayTravelers();
    updateTravelerStats();
}

// ====== DISPLAY TRAVELERS ======
/**
 * Render the travelers table with pagination
 */
function displayTravelers() {
    const tableBody = document.getElementById('travelersTableBody');
    if (!tableBody) return;

    if (!travelersFiltered || travelersFiltered.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:40px;">No travelers found</td></tr>';
        updatePaginationDisplay(0, 1, travelersPerPage);
        return;
    }

    const start = (travelersCurrentPage - 1) * travelersPerPage;
    const end = start + travelersPerPage;
    const pageData = travelersFiltered.slice(start, end);

    let html = '';
    pageData.forEach(t => {
        const fullName = `${t.first_name || ''} ${t.last_name || ''}`.trim() || 'N/A';
        const batchName = t.batch_name || 'Not Assigned';
        const statusClass = getStatusClass(t.passport_status);

        const docIcons = `
            <div class="doc-icons">
                <i class="fas fa-passport doc-icon ${t.passport_scan ? 'available' : 'missing'}"
                   onclick="${t.passport_scan ? `viewUploadedDocument('passport','${t.passport_scan}')` : ''}"
                   title="Passport: ${t.passport_scan ? t.passport_scan : 'Missing'}"
                   style="cursor:${t.passport_scan ? 'pointer' : 'default'}"></i>
                <i class="fas fa-id-card doc-icon ${t.aadhaar_scan ? 'available' : 'missing'}"
                   onclick="${t.aadhaar_scan ? `viewUploadedDocument('aadhaar','${t.aadhaar_scan}')` : ''}"
                   title="Aadhaar: ${t.aadhaar_scan ? t.aadhaar_scan : 'Missing'}"
                   style="cursor:${t.aadhaar_scan ? 'pointer' : 'default'}"></i>
                <i class="fas fa-credit-card doc-icon ${t.pan_scan ? 'available' : 'missing'}"
                   onclick="${t.pan_scan ? `viewUploadedDocument('pan','${t.pan_scan}')` : ''}"
                   title="PAN: ${t.pan_scan ? t.pan_scan : 'Missing'}"
                   style="cursor:${t.pan_scan ? 'pointer' : 'default'}"></i>
                <i class="fas fa-syringe doc-icon ${t.vaccine_scan ? 'available' : 'missing'}"
                   onclick="${t.vaccine_scan ? `viewUploadedDocument('vaccine','${t.vaccine_scan}')` : ''}"
                   title="Vaccine: ${t.vaccine_scan ? t.vaccine_scan : 'Missing'}"
                   style="cursor:${t.vaccine_scan ? 'pointer' : 'default'}"></i>
                <i class="fas fa-camera doc-icon ${t.photo ? 'available' : 'missing'}"
                   onclick="${t.photo ? `viewUploadedDocument('photo','${t.photo}')` : ''}"
                   title="Photo: ${t.photo ? t.photo : 'Missing'}"
                   style="cursor:${t.photo ? 'pointer' : 'default'}"></i>
            </div>`;

        html += `<tr>
            <td>${t.id}</td>
            <td><strong>${escapeHtml(fullName)}</strong><br><small>${escapeHtml(t.passport_name || '')}</small></td>
            <td>${escapeHtml(t.passport_no || '-')}<br><small>Exp: ${t.passport_expiry_date || 'N/A'}</small></td>
            <td>${escapeHtml(t.mobile || '-')}</td>
            <td>${escapeHtml(t.email || '-')}</td>
            <td>${escapeHtml(batchName)}</td>
            <td><span class="status-badge ${statusClass}">${escapeHtml(t.passport_status || 'Active')}</span></td>
            <td>${docIcons}</td>
            <td>
                <button class="icon-btn" onclick="viewTravelerDetails(${t.id})" title="View"><i class="fas fa-eye"></i></button>
                <button class="icon-btn" onclick="editTraveler(${t.id})" title="Edit"><i class="fas fa-edit"></i></button>
                <button class="icon-btn" onclick="deleteTraveler(${t.id})" title="Delete"><i class="fas fa-trash"></i></button>
            </td>
        </tr>`;
    });

    tableBody.innerHTML = html;
    updatePaginationDisplay(travelersFiltered.length, travelersCurrentPage, travelersPerPage);
}

// ====== FILTER TRAVELERS ======
/**
 * Filter travelers by name, passport, email, or mobile
 */
function filterTravelers() {
    const searchEl = document.getElementById('searchTravelers');
    const search = searchEl ? searchEl.value.toLowerCase().trim() : '';

    if (!search) {
        travelersFiltered = [...travelersData];
    } else {
        travelersFiltered = travelersData.filter(t => {
            const name = `${t.first_name || ''} ${t.last_name || ''}`.toLowerCase();
            const passport = (t.passport_no || '').toLowerCase();
            const email = (t.email || '').toLowerCase();
            const mobile = (t.mobile || '').toLowerCase();
            const batch = (t.batch_name || '').toLowerCase();
            return name.includes(search) || passport.includes(search) ||
                   email.includes(search) || mobile.includes(search) || batch.includes(search);
        });
    }

    travelersCurrentPage = 1;
    displayTravelers();
    showNotification(`Found ${travelersFiltered.length} traveler(s)`, 'info');
}

// ====== CREATE TRAVELER ======
/**
 * POST a new traveler (with file uploads via FormData)
 */
async function createTraveler() {
    const formEl = document.getElementById('travelerAddForm');
    if (!formEl) return;

    const fields = {
        first_name: document.getElementById('add_first_name')?.value?.trim(),
        last_name: document.getElementById('add_last_name')?.value?.trim(),
        passport_name: document.getElementById('add_passport_name')?.value?.trim(),
        batch_id: document.getElementById('add_batch_id')?.value,
        passport_no: document.getElementById('add_passport_no')?.value?.trim(),
        passport_issue_date: document.getElementById('add_passport_issue_date')?.value,
        passport_expiry_date: document.getElementById('add_passport_expiry_date')?.value,
        passport_status: document.getElementById('add_passport_status')?.value,
        gender: document.getElementById('add_gender')?.value,
        dob: document.getElementById('add_dob')?.value,
        mobile: document.getElementById('add_mobile')?.value?.trim(),
        email: document.getElementById('add_email')?.value?.trim(),
        aadhaar: document.getElementById('add_aadhaar')?.value?.trim(),
        pan: document.getElementById('add_pan')?.value?.trim(),
        aadhaar_pan_linked: document.getElementById('add_aadhaar_pan_linked')?.value,
        vaccine_status: document.getElementById('add_vaccine_status')?.value,
        wheelchair: document.getElementById('add_wheelchair')?.value,
        place_of_birth: document.getElementById('add_place_of_birth')?.value?.trim(),
        place_of_issue: document.getElementById('add_place_of_issue')?.value?.trim(),
        passport_address: document.getElementById('add_passport_address')?.value?.trim(),
        father_name: document.getElementById('add_father_name')?.value?.trim(),
        mother_name: document.getElementById('add_mother_name')?.value?.trim(),
        spouse_name: document.getElementById('add_spouse_name')?.value?.trim(),
        pin: document.getElementById('add_pin')?.value?.trim(),
        emergency_contact: document.getElementById('add_emergency_contact')?.value?.trim(),
        emergency_phone: document.getElementById('add_emergency_phone')?.value?.trim(),
        medical_notes: document.getElementById('add_medical_notes')?.value?.trim()
    };

    if (!fields.first_name || !fields.last_name) {
        showNotification('First name and last name are required', 'error'); return;
    }
    if (!fields.passport_no) {
        showNotification('Passport number is required', 'error'); return;
    }
    if (!fields.mobile) {
        showNotification('Mobile number is required', 'error'); return;
    }
    if (!fields.batch_id) {
        showNotification('Please select a batch', 'error'); return;
    }

    const formData = new FormData();
    Object.entries(fields).forEach(([k, v]) => { if (v) formData.append(k, v); });

    const fileInputs = [
        { id: 'add_passport_scan', field: 'passport_scan' },
        { id: 'add_aadhaar_scan', field: 'aadhaar_scan' },
        { id: 'add_pan_scan', field: 'pan_scan' },
        { id: 'add_vaccine_scan', field: 'vaccine_scan' },
        { id: 'add_photo', field: 'photo' }
    ];
    fileInputs.forEach(({ id, field }) => {
        const input = document.getElementById(id);
        if (input?.files?.[0]) formData.append(field, input.files[0]);
    });

    const submitBtn = formEl.querySelector('button[type="submit"]');
    showLoading(submitBtn, 'Saving...');

    try {
        const response = await fetch('/api/travelers', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        const data = await response.json();
        if (data.success) {
            showNotification('Traveler created successfully!', 'success');
            if (typeof hideAddTravelerForm === 'function') hideAddTravelerForm();
            await loadTravelers();
        } else {
            showNotification('Error: ' + (data.error || 'Could not create traveler'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'createTraveler');
    } finally {
        hideLoading(submitBtn);
    }
}

// ====== EDIT TRAVELER ======
/**
 * Load traveler data into the edit form
 * @param {number} id
 */
function editTraveler(id) {
    const traveler = travelersData.find(t => t.id === id);
    if (!traveler) { showNotification('Traveler not found', 'error'); return; }

    travelersCurrentEditId = id;

    const set = (elId, val) => {
        const el = document.getElementById(elId);
        if (el) el.value = val || '';
    };

    set('edit_traveler_id', traveler.id);
    set('edit_first_name', traveler.first_name);
    set('edit_last_name', traveler.last_name);
    set('edit_passport_name', traveler.passport_name);
    set('edit_batch_id', traveler.batch_id);
    set('edit_passport_no', traveler.passport_no);
    set('edit_passport_issue_date', formatDateForInput(traveler.passport_issue_date));
    set('edit_passport_expiry_date', formatDateForInput(traveler.passport_expiry_date));
    set('edit_passport_status', traveler.passport_status || 'Active');
    set('edit_gender', traveler.gender);
    set('edit_dob', formatDateForInput(traveler.dob));
    set('edit_mobile', traveler.mobile);
    set('edit_email', traveler.email);
    set('edit_aadhaar', traveler.aadhaar);
    set('edit_pan', traveler.pan);
    set('edit_aadhaar_pan_linked', traveler.aadhaar_pan_linked || 'No');
    set('edit_vaccine_status', traveler.vaccine_status || 'Not Vaccinated');
    set('edit_wheelchair', traveler.wheelchair || 'No');
    set('edit_place_of_birth', traveler.place_of_birth);
    set('edit_place_of_issue', traveler.place_of_issue);
    set('edit_passport_address', traveler.passport_address);
    set('edit_father_name', traveler.father_name);
    set('edit_mother_name', traveler.mother_name);
    set('edit_spouse_name', traveler.spouse_name);
    set('edit_pin', traveler.pin || '0000');
    set('edit_emergency_contact', traveler.emergency_contact);
    set('edit_emergency_phone', traveler.emergency_phone);
    set('edit_medical_notes', traveler.medical_notes);

    // Show existing document previews if function exists
    if (typeof showExistingDocumentPreview === 'function') {
        showExistingDocumentPreview('edit_passport_scan_preview', traveler.passport_scan, 'passport');
        showExistingDocumentPreview('edit_aadhaar_scan_preview', traveler.aadhaar_scan, 'aadhaar');
        showExistingDocumentPreview('edit_pan_scan_preview', traveler.pan_scan, 'pan');
        showExistingDocumentPreview('edit_vaccine_scan_preview', traveler.vaccine_scan, 'vaccine');
        showExistingDocumentPreview('edit_photo_preview', traveler.photo, 'photo');
    }

    const editForm = document.getElementById('editTravelerForm');
    if (editForm) {
        editForm.style.display = 'block';
        editForm.scrollIntoView({ behavior: 'smooth' });
    }
}

// ====== UPDATE TRAVELER ======
/**
 * PUT updated traveler data
 */
async function updateTraveler() {
    if (!travelersCurrentEditId) {
        showNotification('No traveler selected for editing', 'error'); return;
    }

    const fields = {
        first_name: document.getElementById('edit_first_name')?.value?.trim(),
        last_name: document.getElementById('edit_last_name')?.value?.trim(),
        passport_name: document.getElementById('edit_passport_name')?.value?.trim(),
        batch_id: document.getElementById('edit_batch_id')?.value,
        passport_no: document.getElementById('edit_passport_no')?.value?.trim(),
        passport_issue_date: document.getElementById('edit_passport_issue_date')?.value,
        passport_expiry_date: document.getElementById('edit_passport_expiry_date')?.value,
        passport_status: document.getElementById('edit_passport_status')?.value,
        gender: document.getElementById('edit_gender')?.value,
        dob: document.getElementById('edit_dob')?.value,
        mobile: document.getElementById('edit_mobile')?.value?.trim(),
        email: document.getElementById('edit_email')?.value?.trim(),
        aadhaar: document.getElementById('edit_aadhaar')?.value?.trim(),
        pan: document.getElementById('edit_pan')?.value?.trim(),
        aadhaar_pan_linked: document.getElementById('edit_aadhaar_pan_linked')?.value,
        vaccine_status: document.getElementById('edit_vaccine_status')?.value,
        wheelchair: document.getElementById('edit_wheelchair')?.value,
        place_of_birth: document.getElementById('edit_place_of_birth')?.value?.trim(),
        place_of_issue: document.getElementById('edit_place_of_issue')?.value?.trim(),
        passport_address: document.getElementById('edit_passport_address')?.value?.trim(),
        father_name: document.getElementById('edit_father_name')?.value?.trim(),
        mother_name: document.getElementById('edit_mother_name')?.value?.trim(),
        spouse_name: document.getElementById('edit_spouse_name')?.value?.trim(),
        pin: document.getElementById('edit_pin')?.value?.trim(),
        emergency_contact: document.getElementById('edit_emergency_contact')?.value?.trim(),
        emergency_phone: document.getElementById('edit_emergency_phone')?.value?.trim(),
        medical_notes: document.getElementById('edit_medical_notes')?.value?.trim()
    };

    if (!fields.first_name || !fields.last_name) {
        showNotification('First name and last name are required', 'error'); return;
    }

    const formData = new FormData();
    Object.entries(fields).forEach(([k, v]) => { if (v) formData.append(k, v); });

    const fileInputs = [
        { id: 'edit_passport_scan', field: 'passport_scan' },
        { id: 'edit_aadhaar_scan', field: 'aadhaar_scan' },
        { id: 'edit_pan_scan', field: 'pan_scan' },
        { id: 'edit_vaccine_scan', field: 'vaccine_scan' },
        { id: 'edit_photo', field: 'photo' }
    ];
    fileInputs.forEach(({ id, field }) => {
        const input = document.getElementById(id);
        if (input?.files?.[0]) formData.append(field, input.files[0]);
    });

    const submitBtn = document.querySelector('#travelerEditForm button[type="submit"]');
    showLoading(submitBtn, 'Updating...');

    try {
        const response = await fetch(`/api/travelers/${travelersCurrentEditId}`, {
            method: 'PUT',
            body: formData,
            credentials: 'include'
        });
        const data = await response.json();
        if (data.success) {
            showNotification('Traveler updated successfully!', 'success');
            if (typeof hideEditTravelerForm === 'function') hideEditTravelerForm();
            travelersCurrentEditId = null;
            await loadTravelers();
        } else {
            showNotification('Error: ' + (data.error || 'Update failed'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'updateTraveler');
    } finally {
        hideLoading(submitBtn);
    }
}

// ====== DELETE TRAVELER ======
/**
 * DELETE a traveler by ID
 * @param {number} id
 */
async function deleteTraveler(id) {
    if (!confirm('Are you sure you want to delete this traveler? This action cannot be undone.')) return;

    try {
        const data = await makeAPICall('DELETE', `/api/travelers/${id}`);
        if (data.success) {
            showNotification('Traveler deleted successfully!', 'success');
            await loadTravelers();
        } else {
            showNotification('Error: ' + (data.error || 'Could not delete traveler'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'deleteTraveler');
    }
}

// ====== VIEW TRAVELER DETAILS ======
/**
 * Show a modal with full traveler details
 * @param {number} id
 */
function viewTravelerDetails(id) {
    const t = travelersData.find(t => t.id === id);
    if (!t) { showNotification('Traveler not found', 'error'); return; }

    const fullName = `${t.first_name || ''} ${t.last_name || ''}`.trim();

    const detailsHtml = `
        <div class="detail-grid">
            <div class="detail-item"><strong>Full Name</strong><span>${escapeHtml(fullName)}</span></div>
            <div class="detail-item"><strong>Passport Name</strong><span>${escapeHtml(t.passport_name || '-')}</span></div>
            <div class="detail-item"><strong>Passport No</strong><span>${escapeHtml(t.passport_no || '-')}</span></div>
            <div class="detail-item"><strong>Passport Status</strong><span>${escapeHtml(t.passport_status || '-')}</span></div>
            <div class="detail-item"><strong>Issue Date</strong><span>${formatDate(t.passport_issue_date)}</span></div>
            <div class="detail-item"><strong>Expiry Date</strong><span>${formatDate(t.passport_expiry_date)}</span></div>
            <div class="detail-item"><strong>Gender</strong><span>${escapeHtml(t.gender || '-')}</span></div>
            <div class="detail-item"><strong>Date of Birth</strong><span>${formatDate(t.dob)}</span></div>
            <div class="detail-item"><strong>Mobile</strong><span>${escapeHtml(t.mobile || '-')}</span></div>
            <div class="detail-item"><strong>Email</strong><span>${escapeHtml(t.email || '-')}</span></div>
            <div class="detail-item"><strong>Aadhaar</strong><span>${escapeHtml(t.aadhaar || '-')}</span></div>
            <div class="detail-item"><strong>PAN</strong><span>${escapeHtml(t.pan || '-')}</span></div>
            <div class="detail-item"><strong>Aadhaar-PAN Linked</strong><span>${escapeHtml(t.aadhaar_pan_linked || '-')}</span></div>
            <div class="detail-item"><strong>Vaccine Status</strong><span>${escapeHtml(t.vaccine_status || '-')}</span></div>
            <div class="detail-item"><strong>Wheelchair</strong><span>${escapeHtml(t.wheelchair || 'No')}</span></div>
            <div class="detail-item"><strong>Batch</strong><span>${escapeHtml(t.batch_name || 'Not Assigned')}</span></div>
            <div class="detail-item"><strong>Place of Birth</strong><span>${escapeHtml(t.place_of_birth || '-')}</span></div>
            <div class="detail-item"><strong>Place of Issue</strong><span>${escapeHtml(t.place_of_issue || '-')}</span></div>
            <div class="detail-item"><strong>Father's Name</strong><span>${escapeHtml(t.father_name || '-')}</span></div>
            <div class="detail-item"><strong>Mother's Name</strong><span>${escapeHtml(t.mother_name || '-')}</span></div>
            <div class="detail-item"><strong>Spouse's Name</strong><span>${escapeHtml(t.spouse_name || '-')}</span></div>
            <div class="detail-item"><strong>Emergency Contact</strong><span>${escapeHtml(t.emergency_contact || '-')}</span></div>
            <div class="detail-item"><strong>Emergency Phone</strong><span>${escapeHtml(t.emergency_phone || '-')}</span></div>
            <div class="detail-item"><strong>Registered</strong><span>${formatDate(t.created_at)}</span></div>
        </div>
        ${t.passport_address ? `<div style="margin-top:15px;padding:12px;background:#f8f9fa;border-radius:5px;"><strong>Passport Address:</strong><br>${escapeHtml(t.passport_address)}</div>` : ''}
        ${t.medical_notes ? `<div style="margin-top:10px;padding:12px;background:#fff3cd;border-radius:5px;"><strong>Medical Notes:</strong><br>${escapeHtml(t.medical_notes)}</div>` : ''}
    `;

    // Use existing modal if available, otherwise use generic
    const existingModal = document.getElementById('viewTravelerModal');
    const existingDetails = document.getElementById('travelerDetails');
    const existingOverlay = document.getElementById('modalOverlay');

    if (existingModal && existingDetails) {
        existingDetails.innerHTML = detailsHtml;
        existingModal.style.display = 'block';
        if (existingOverlay) existingOverlay.style.display = 'block';
    } else {
        showModal(`<i class="fas fa-user"></i> Traveler Details - ${escapeHtml(fullName)}`, detailsHtml,
            `<button class="action-btn btn-secondary" onclick="closeModal()"><i class="fas fa-times"></i> Close</button>`);
    }
}

// ====== EXPORT TO CSV ======
/**
 * Export all travelers to a CSV file
 */
function exportTravelersToCSV() {
    if (!travelersData.length) {
        showNotification('No travelers to export', 'warning'); return;
    }

    const headers = ['ID', 'First Name', 'Last Name', 'Passport Name', 'Passport No',
        'Passport Status', 'Issue Date', 'Expiry Date', 'Gender', 'DOB',
        'Mobile', 'Email', 'Aadhaar', 'PAN', 'Aadhaar-PAN Linked',
        'Vaccine Status', 'Wheelchair', 'Batch', 'Place of Birth', 'Place of Issue',
        'Father Name', 'Mother Name', 'Spouse Name', 'Emergency Contact', 'Emergency Phone',
        'Medical Notes', 'Registered'];

    const rows = [headers, ...travelersData.map(t => [
        t.id, t.first_name, t.last_name, t.passport_name, t.passport_no,
        t.passport_status, t.passport_issue_date, t.passport_expiry_date, t.gender, t.dob,
        t.mobile, t.email, t.aadhaar, t.pan, t.aadhaar_pan_linked,
        t.vaccine_status, t.wheelchair, t.batch_name, t.place_of_birth, t.place_of_issue,
        t.father_name, t.mother_name, t.spouse_name, t.emergency_contact, t.emergency_phone,
        t.medical_notes, t.created_at
    ])];

    downloadCSV(rows, `travelers_${new Date().toISOString().slice(0, 10)}.csv`);
    showNotification(`Exported ${travelersData.length} travelers to CSV`, 'success');
}

// ====== UPLOAD PASSPORT FILE ======
/**
 * Handle passport file upload for a specific traveler
 * @param {number} travelerId
 * @param {File} file
 */
async function uploadPassportFile(travelerId, file) {
    if (!travelerId || !file) {
        showNotification('Traveler ID and file are required', 'error'); return;
    }

    const formData = new FormData();
    formData.append('passport_scan', file);

    try {
        const response = await fetch(`/api/travelers/${travelerId}`, {
            method: 'PUT',
            body: formData,
            credentials: 'include'
        });
        const data = await response.json();
        if (data.success) {
            showNotification('Passport file uploaded successfully!', 'success');
            await loadTravelers();
        } else {
            showNotification('Upload failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        handleAPIError(error, 'uploadPassportFile');
    }
}

// ====== STATS UPDATE ======
function updateTravelerStats() {
    const total = travelersData.length;
    const active = travelersData.filter(t => t.passport_status === 'Active').length;
    const vaccinated = travelersData.filter(t => t.vaccine_status === 'Fully Vaccinated').length;
    const docsComplete = travelersData.filter(t => t.passport_scan && t.aadhaar_scan && t.pan_scan && t.photo).length;

    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('totalTravelersCount', total);
    setEl('activeTravelersCount', active);
    setEl('vaccinatedCount', vaccinated);
    setEl('documentsComplete', docsComplete);
}

// ====== PAGINATION ======
function travelersPreviousPage() {
    if (travelersCurrentPage > 1) { travelersCurrentPage--; displayTravelers(); }
}

function travelersNextPage() {
    if (travelersCurrentPage * travelersPerPage < travelersFiltered.length) {
        travelersCurrentPage++;
        displayTravelers();
    }
}

// Alias for inline HTML compatibility
function previousPage() { travelersPreviousPage(); }
function nextPage() { travelersNextPage(); }
function searchTravelers() { filterTravelers(); }
function clearSearch() {
    const el = document.getElementById('searchTravelers');
    if (el) el.value = '';
    travelersFiltered = [...travelersData];
    travelersCurrentPage = 1;
    displayTravelers();
}

console.log('✅ travelers.js loaded');
