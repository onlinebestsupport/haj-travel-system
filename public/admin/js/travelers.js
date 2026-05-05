/**
 * travelers.js - Traveler management functions
 * Alhudha Haj Travel Management System
 */

'use strict';

// Module-level state
let travelersData = [];
let filteredTravelersData = [];
let currentTravelersPage = 1;
const TRAVELERS_PAGE_SIZE = 20;

// ====== LOAD TRAVELERS ======
/**
 * Fetch all travelers from the API and render them
 */
async function loadTravelers() {
    showLoading(true);
    try {
        const data = await makeApiCall('GET', '/api/travelers');
        travelersData = Array.isArray(data) ? data : (data.travelers || []);
        filteredTravelersData = [...travelersData];
        currentTravelersPage = 1;
        displayTravelers(filteredTravelersData);
        console.log(`✅ Loaded ${travelersData.length} travelers`);
    } catch (error) {
        handleApiError(error, 'Load travelers');
    } finally {
        showLoading(false);
    }
}

// ====== DISPLAY TRAVELERS ======
/**
 * Render travelers array into the table
 * @param {Array} travelers
 */
function displayTravelers(travelers) {
    const tbody = document.getElementById('travelersTableBody');
    if (!tbody) return;

    if (!travelers || travelers.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" style="text-align:center;padding:40px;color:#95a5a6;">
                    <i class="fas fa-users" style="font-size:2rem;display:block;margin-bottom:10px;"></i>
                    No travelers found
                </td>
            </tr>`;
        updateTravelersCount(0);
        return;
    }

    // Pagination
    const start = (currentTravelersPage - 1) * TRAVELERS_PAGE_SIZE;
    const pageData = travelers.slice(start, start + TRAVELERS_PAGE_SIZE);

    tbody.innerHTML = pageData.map(t => {
        const fullName = `${escapeHtml(t.first_name || '')} ${escapeHtml(t.last_name || '')}`.trim();
        const passportStatus = t.passport_status || 'Active';
        const statusClass = passportStatus.toLowerCase() === 'active' ? 'status-active' :
                            passportStatus.toLowerCase() === 'expired' ? 'status-inactive' : 'status-pending';
        return `
            <tr>
                <td>${escapeHtml(String(t.id || ''))}</td>
                <td>${fullName || '-'}</td>
                <td>${escapeHtml(t.passport_no || '-')}</td>
                <td>${escapeHtml(t.mobile || '-')}</td>
                <td>${escapeHtml(t.email || '-')}</td>
                <td>${escapeHtml(t.batch_name || t.batch_id || '-')}</td>
                <td>${escapeHtml(t.gender || '-')}</td>
                <td>${formatDate(t.dob)}</td>
                <td><span class="status-badge ${statusClass}">${escapeHtml(passportStatus)}</span></td>
                <td>
                    <button class="icon-btn btn-view" onclick="viewTravelerDetails(${t.id})" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="icon-btn btn-edit" onclick="editTraveler(${t.id})" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="icon-btn btn-delete" onclick="deleteTraveler(${t.id})" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>`;
    }).join('');

    updateTravelersCount(travelers.length);
    renderTravelersPagination(travelers.length);
}

/**
 * Update the traveler count display element
 * @param {number} count
 */
function updateTravelersCount(count) {
    const el = document.getElementById('travelersCount');
    if (el) el.textContent = count;
}

/**
 * Render pagination controls for travelers table
 * @param {number} total
 */
function renderTravelersPagination(total) {
    const container = document.getElementById('travelersPagination');
    if (!container) return;

    const totalPages = Math.ceil(total / TRAVELERS_PAGE_SIZE);
    if (totalPages <= 1) { container.innerHTML = ''; return; }

    let html = '';
    for (let i = 1; i <= totalPages; i++) {
        html += `<button onclick="goToTravelersPage(${i})" style="
            padding:6px 12px;margin:0 3px;border:1px solid #ddd;border-radius:5px;
            cursor:pointer;background:${i === currentTravelersPage ? '#3498db' : 'white'};
            color:${i === currentTravelersPage ? 'white' : '#2c3e50'};
        ">${i}</button>`;
    }
    container.innerHTML = html;
}

/**
 * Navigate to a specific page of the travelers table
 * @param {number} page
 */
function goToTravelersPage(page) {
    currentTravelersPage = page;
    displayTravelers(filteredTravelersData);
}

// ====== FILTER TRAVELERS ======
/**
 * Filter travelers by name, passport number, or email
 */
function filterTravelers() {
    const searchEl = document.getElementById('searchTravelers');
    const batchEl  = document.getElementById('filterBatch');
    const search   = searchEl ? searchEl.value.toLowerCase().trim() : '';
    const batchId  = batchEl  ? batchEl.value : '';

    filteredTravelersData = travelersData.filter(t => {
        const fullName = `${t.first_name || ''} ${t.last_name || ''}`.toLowerCase();
        const passport = (t.passport_no || '').toLowerCase();
        const email    = (t.email || '').toLowerCase();
        const mobile   = (t.mobile || '').toLowerCase();

        const matchesSearch = !search ||
            fullName.includes(search) ||
            passport.includes(search) ||
            email.includes(search) ||
            mobile.includes(search);

        const matchesBatch = !batchId || String(t.batch_id) === String(batchId);

        return matchesSearch && matchesBatch;
    });

    currentTravelersPage = 1;
    displayTravelers(filteredTravelersData);
}

// ====== CREATE TRAVELER ======
/**
 * Submit the new traveler form to the API
 */
async function createTraveler() {
    const form = document.getElementById('travelerForm') || document.getElementById('addTravelerForm');
    if (!form) { showNotification('Traveler form not found', 'error'); return; }

    const formData = new FormData(form);
    const travelerData = {};
    formData.forEach((value, key) => { if (value !== '') travelerData[key] = value; });

    // Basic validation
    if (!travelerData.first_name || !travelerData.last_name) {
        showNotification('First name and last name are required', 'error');
        return;
    }
    if (!travelerData.passport_no) {
        showNotification('Passport number is required', 'error');
        return;
    }

    showLoading(true);
    try {
        const result = await makeApiCall('POST', '/api/travelers', travelerData);
        if (result.success || result.id) {
            showNotification('Traveler created successfully!', 'success');
            form.reset();
            const container = document.getElementById('addTravelerForm') || document.getElementById('travelerFormContainer');
            if (container) container.style.display = 'none';
            await loadTravelers();
        } else {
            showNotification(result.error || 'Failed to create traveler', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Create traveler');
    } finally {
        showLoading(false);
    }
}

// ====== EDIT TRAVELER ======
/**
 * Load traveler data into the edit form
 * @param {number} travelerId
 */
async function editTraveler(travelerId) {
    showLoading(true);
    try {
        const traveler = await makeApiCall('GET', `/api/travelers/${travelerId}`);
        const data = traveler.traveler || traveler;

        // Populate edit form fields
        const fields = [
            'first_name','last_name','passport_name','passport_no',
            'passport_issue_date','passport_expiry_date','passport_status',
            'gender','dob','mobile','email','aadhaar','pan',
            'aadhaar_pan_linked','vaccine_status','wheelchair',
            'place_of_birth','place_of_issue','passport_address',
            'father_name','mother_name','spouse_name','pin',
            'emergency_contact','emergency_phone','medical_notes','batch_id'
        ];

        fields.forEach(field => {
            const el = document.getElementById(`edit_${field}`) || document.getElementById(field);
            if (el && data[field] !== undefined) el.value = data[field];
        });

        // Set hidden ID field
        const idField = document.getElementById('edit_traveler_id') || document.getElementById('editTravelerId');
        if (idField) idField.value = travelerId;

        // Show edit form
        const editForm = document.getElementById('editTravelerForm') || document.getElementById('editFormContainer');
        if (editForm) {
            editForm.style.display = 'block';
            editForm.scrollIntoView({ behavior: 'smooth' });
        }
    } catch (error) {
        handleApiError(error, 'Load traveler for editing');
    } finally {
        showLoading(false);
    }
}

// ====== UPDATE TRAVELER ======
/**
 * Save changes to an existing traveler
 */
async function updateTraveler() {
    const idField = document.getElementById('edit_traveler_id') || document.getElementById('editTravelerId');
    if (!idField || !idField.value) {
        showNotification('No traveler selected for update', 'error');
        return;
    }

    const travelerId = idField.value;
    const form = document.getElementById('editTravelerForm') || document.getElementById('editFormContainer');
    if (!form) { showNotification('Edit form not found', 'error'); return; }

    const formData = new FormData(form.querySelector('form') || form);
    const travelerData = {};
    formData.forEach((value, key) => { if (key !== 'id') travelerData[key] = value; });

    showLoading(true);
    try {
        const result = await makeApiCall('PUT', `/api/travelers/${travelerId}`, travelerData);
        if (result.success || result.id) {
            showNotification('Traveler updated successfully!', 'success');
            if (form) form.style.display = 'none';
            await loadTravelers();
        } else {
            showNotification(result.error || 'Failed to update traveler', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Update traveler');
    } finally {
        showLoading(false);
    }
}

// ====== DELETE TRAVELER ======
/**
 * Delete a traveler after confirmation
 * @param {number} travelerId
 */
function deleteTraveler(travelerId) {
    const traveler = travelersData.find(t => t.id === travelerId);
    const name = traveler ? `${traveler.first_name || ''} ${traveler.last_name || ''}`.trim() : `ID ${travelerId}`;

    showConfirmation(
        `Are you sure you want to delete traveler "${name}"? This action cannot be undone.`,
        async () => {
            showLoading(true);
            try {
                const result = await makeApiCall('DELETE', `/api/travelers/${travelerId}`);
                if (result.success || result.message) {
                    showNotification('Traveler deleted successfully!', 'success');
                    await loadTravelers();
                } else {
                    showNotification(result.error || 'Failed to delete traveler', 'error');
                }
            } catch (error) {
                handleApiError(error, 'Delete traveler');
            } finally {
                showLoading(false);
            }
        }
    );
}

// ====== VIEW TRAVELER DETAILS ======
/**
 * Show a modal with full traveler details
 * @param {number} travelerId
 */
async function viewTravelerDetails(travelerId) {
    showLoading(true);
    try {
        const response = await makeApiCall('GET', `/api/travelers/${travelerId}`);
        const t = response.traveler || response;

        const fullName = `${t.first_name || ''} ${t.last_name || ''}`.trim();
        const content = `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;">
                <div><strong>Full Name:</strong><br>${escapeHtml(fullName || '-')}</div>
                <div><strong>Passport Name:</strong><br>${escapeHtml(t.passport_name || '-')}</div>
                <div><strong>Passport No:</strong><br>${escapeHtml(t.passport_no || '-')}</div>
                <div><strong>Passport Status:</strong><br>${escapeHtml(t.passport_status || '-')}</div>
                <div><strong>Issue Date:</strong><br>${formatDate(t.passport_issue_date)}</div>
                <div><strong>Expiry Date:</strong><br>${formatDate(t.passport_expiry_date)}</div>
                <div><strong>Gender:</strong><br>${escapeHtml(t.gender || '-')}</div>
                <div><strong>Date of Birth:</strong><br>${formatDate(t.dob)}</div>
                <div><strong>Mobile:</strong><br>${escapeHtml(t.mobile || '-')}</div>
                <div><strong>Email:</strong><br>${escapeHtml(t.email || '-')}</div>
                <div><strong>Aadhaar:</strong><br>${escapeHtml(t.aadhaar || '-')}</div>
                <div><strong>PAN:</strong><br>${escapeHtml(t.pan || '-')}</div>
                <div><strong>Batch:</strong><br>${escapeHtml(t.batch_name || t.batch_id || '-')}</div>
                <div><strong>Vaccine Status:</strong><br>${escapeHtml(t.vaccine_status || '-')}</div>
                <div><strong>Wheelchair:</strong><br>${escapeHtml(t.wheelchair || '-')}</div>
                <div><strong>Place of Birth:</strong><br>${escapeHtml(t.place_of_birth || '-')}</div>
                <div><strong>Father Name:</strong><br>${escapeHtml(t.father_name || '-')}</div>
                <div><strong>Mother Name:</strong><br>${escapeHtml(t.mother_name || '-')}</div>
                <div><strong>Emergency Contact:</strong><br>${escapeHtml(t.emergency_contact || '-')}</div>
                <div><strong>Emergency Phone:</strong><br>${escapeHtml(t.emergency_phone || '-')}</div>
                <div style="grid-column:1/-1;"><strong>Address:</strong><br>${escapeHtml(t.passport_address || '-')}</div>
                <div style="grid-column:1/-1;"><strong>Medical Notes:</strong><br>${escapeHtml(t.medical_notes || '-')}</div>
                <div><strong>Created:</strong><br>${formatDate(t.created_at)}</div>
            </div>`;

        showModal(`<i class="fas fa-user" style="color:#3498db;margin-right:8px;"></i>Traveler Details — ${escapeHtml(fullName)}`, content, [
            { label: '<i class="fas fa-edit"></i> Edit', class: 'btn-primary', onClick: `closeModal(); editTraveler(${travelerId});` },
            { label: '<i class="fas fa-times"></i> Close', class: 'btn-secondary', onClick: 'closeModal()' }
        ]);
    } catch (error) {
        handleApiError(error, 'Load traveler details');
    } finally {
        showLoading(false);
    }
}

// ====== EXPORT TO CSV ======
/**
 * Export the current traveler list to a CSV file
 */
function exportTravelersToCSV() {
    const data = filteredTravelersData.length > 0 ? filteredTravelersData : travelersData;
    if (!data || data.length === 0) {
        showNotification('No travelers to export', 'warning');
        return;
    }

    const headers = [
        'ID','First Name','Last Name','Passport Name','Batch','Passport No',
        'Issue Date','Expiry Date','Passport Status','Gender','DOB',
        'Mobile','Email','Aadhaar','PAN','Vaccine Status','Wheelchair',
        'Place of Birth','Father Name','Mother Name','Emergency Contact',
        'Emergency Phone','Medical Notes','Created At'
    ];

    const rows = data.map(t => [
        t.id, t.first_name, t.last_name, t.passport_name,
        t.batch_name || t.batch_id, t.passport_no,
        t.passport_issue_date, t.passport_expiry_date, t.passport_status,
        t.gender, t.dob, t.mobile, t.email, t.aadhaar, t.pan,
        t.vaccine_status, t.wheelchair, t.place_of_birth,
        t.father_name, t.mother_name, t.emergency_contact,
        t.emergency_phone, t.medical_notes, t.created_at
    ].map(v => `"${String(v || '').replace(/"/g, '""')}"`));

    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href     = url;
    link.download = `travelers_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    showNotification(`Exported ${data.length} travelers to CSV`, 'success');
}

// ====== UPLOAD PASSPORT SCAN ======
/**
 * Upload a passport scan document for a traveler
 * @param {number} travelerId
 * @param {File}   file
 */
async function uploadPassportScan(travelerId, file) {
    if (!file) { showNotification('No file selected', 'error'); return; }

    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
        showNotification('Only JPG, PNG, GIF, and PDF files are allowed', 'error');
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        showNotification('File size must be less than 5MB', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', 'passport_scan');

    showLoading(true);
    try {
        const response = await fetch(`/api/travelers/${travelerId}/upload`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });

        if (!response.ok) throw new Error(`Upload failed: HTTP ${response.status}`);

        const result = await response.json();
        if (result.success || result.url) {
            showNotification('Passport scan uploaded successfully!', 'success');
            await loadTravelers();
        } else {
            showNotification(result.error || 'Upload failed', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Upload passport scan');
    } finally {
        showLoading(false);
    }
}
