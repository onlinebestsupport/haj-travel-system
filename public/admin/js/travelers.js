/*
 * travelers.js - Complete implementation for 36-field traveler management
 * Includes: mailing_address, file_reference, expected_return_date
 * Client-side validation: passport expiry must be 6 months after expected return
 */

// ============================================================
// GLOBAL STATE
// ============================================================
let currentPage = 1;
const ITEMS_PER_PAGE = 10;
let travelersData = [];
let filteredTravelers = [];
let currentEditId = null;
let currentDocument = null;
let currentDocumentName = '';

// ============================================================
// INITIALIZATION
// ============================================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Travelers module loading...');
    
    if (typeof SessionManager !== 'undefined') {
        SessionManager.initPage(function() {
            initializeTravelersPage();
        });
    } else {
        initializeTravelersPage();
    }
});

function initializeTravelersPage() {
    loadBatches();
    loadTravelers();
    setupPassportNameAutoFill();
    setupSameMailingToggle();
    setupDateValidation();
    setupFormResets();
}

// ============================================================
// DATE HELPERS
// ============================================================
function parseDateYMD(str) {
    if (!str || !/^\d{4}-\d{2}-\d{2}$/.test(str)) return null;
    const [y, m, d] = str.split('-').map(Number);
    return new Date(Date.UTC(y, m - 1, d));
}

function addMonths(date, months) {
    if (!date) return null;
    const d = new Date(date.getTime());
    const day = d.getUTCDate();
    d.setUTCMonth(d.getUTCMonth() + months);
    if (d.getUTCDate() !== day) {
        d.setUTCDate(0);
    }
    return d;
}

function formatDateForInput(date) {
    if (!date) return '';
    if (typeof date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(date)) return date;
    if (date instanceof Date) {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    }
    try {
        const d = new Date(date);
        if (isNaN(d.getTime())) return '';
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
    } catch (e) {
        return '';
    }
}

function daysUntil(dateStr) {
    const d = parseDateYMD(dateStr);
    if (!d) return null;
    const now = new Date();
    const diff = d.getTime() - now.getTime();
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

function validatePassportValidity(passportExpiry, expectedReturn) {
    if (!passportExpiry || !expectedReturn) {
        return { valid: true, message: '' }; // Skip validation if dates not set
    }
    
    const expiry = parseDateYMD(passportExpiry);
    const ret = parseDateYMD(expectedReturn);
    
    if (!ret) {
        return { valid: false, message: 'Invalid expected return date format' };
    }
    if (!expiry) {
        return { valid: false, message: 'Invalid passport expiry date format' };
    }
    
    const minValid = addMonths(ret, 6);
    if (expiry.getTime() < minValid.getTime()) {
        return {
            valid: false,
            message: `Passport must be valid for at least 6 months after expected return date. Minimum expiry: ${minValid.toISOString().slice(0, 10)}`
        };
    }
    return { valid: true, message: '' };
}

// ============================================================
// SAME MAILING ADDRESS TOGGLE
// ============================================================
function setupSameMailingToggle() {
    ['add', 'edit'].forEach(prefix => {
        const cb = document.getElementById(`${prefix}_same_mailing`);
        if (cb) {
            cb.addEventListener('change', function() {
                toggleMailingAddress(prefix);
            });
        }
    });
}

function toggleMailingAddress(prefix) {
    const cb = document.getElementById(`${prefix}_same_mailing`);
    const passportAddr = document.getElementById(`${prefix}_passport_address`);
    const mailingEl = document.getElementById(`${prefix}_mailing_address`);
    
    if (!cb || !mailingEl || !passportAddr) return;
    
    if (cb.checked) {
        mailingEl.value = passportAddr.value || '';
        mailingEl.readOnly = true;
        mailingEl.style.background = '#e9ecef';
    } else {
        mailingEl.readOnly = false;
        mailingEl.style.background = '';
    }
}

// ============================================================
// PASSPORT NAME AUTO-FILL
// ============================================================
function setupPassportNameAutoFill() {
    ['add', 'edit'].forEach(prefix => {
        const first = document.getElementById(`${prefix}_first_name`);
        const last = document.getElementById(`${prefix}_last_name`);
        const passport = document.getElementById(`${prefix}_passport_name`);
        
        if (first && last && passport) {
            const updatePassportName = () => {
                passport.value = `${first.value || ''} ${last.value || ''}`.trim();
            };
            first.addEventListener('input', updatePassportName);
            last.addEventListener('input', updatePassportName);
        }
    });
}

// ============================================================
// DATE VALIDATION
// ============================================================
function setupDateValidation() {
    ['add', 'edit'].forEach(prefix => {
        const expiryEl = document.getElementById(`${prefix}_passport_expiry_date`);
        const returnEl = document.getElementById(`${prefix}_expected_return_date`);
        
        if (expiryEl && returnEl) {
            const validate = () => {
                const result = validatePassportValidity(expiryEl.value, returnEl.value);
                if (!result.valid) {
                    expiryEl.setCustomValidity(result.message);
                    expiryEl.style.borderColor = '#e74c3c';
                } else {
                    expiryEl.setCustomValidity('');
                    expiryEl.style.borderColor = '';
                }
            };
            
            expiryEl.addEventListener('change', validate);
            returnEl.addEventListener('change', validate);
        }
    });
}

// ============================================================
// LOAD BATCHES
// ============================================================
async function loadBatches() {
    try {
        const response = await fetch('/api/batches', { credentials: 'include' });
        const data = await response.json();
        let batches = [];
        
        if (data.success && data.batches) {
            batches = data.batches;
        } else {
            // Fallback
            batches = [
                { id: 1, batch_name: 'Haj Platinum 2026' },
                { id: 2, batch_name: 'Haj Gold 2026' },
                { id: 3, batch_name: 'Umrah Ramadhan Special' }
            ];
        }
        
        updateBatchDropdowns(batches);
    } catch (error) {
        console.error('Error loading batches:', error);
        // Use fallback
        const batches = [
            { id: 1, batch_name: 'Haj Platinum 2026' },
            { id: 2, batch_name: 'Haj Gold 2026' },
            { id: 3, batch_name: 'Umrah Ramadhan Special' }
        ];
        updateBatchDropdowns(batches);
    }
}

function updateBatchDropdowns(batches) {
    ['add', 'edit'].forEach(prefix => {
        const select = document.getElementById(`${prefix}_batch_id`);
        if (!select) return;
        
        select.innerHTML = '<option value="">Select Batch</option>';
        batches.forEach(b => {
            const option = document.createElement('option');
            option.value = b.id;
            option.textContent = b.batch_name;
            select.appendChild(option);
        });
    });
}

// ============================================================
// LOAD TRAVELERS
// ============================================================
async function loadTravelers() {
    const tableBody = document.getElementById('travelersTableBody');
    if (tableBody) {
        tableBody.innerHTML = '<tr><td colspan="11" class="loading"><i class="fas fa-spinner fa-spin"></i> Loading travelers...</td></tr>';
    }
    
    try {
        const response = await fetch('/api/travelers', { credentials: 'include' });
        const data = await response.json();
        
        if (data.success && data.travelers) {
            travelersData = data.travelers;
        } else {
            travelersData = getFallbackTravelers();
        }
    } catch (error) {
        console.error('Error loading travelers:', error);
        travelersData = getFallbackTravelers();
    }
    
    filteredTravelers = [...travelersData];
    displayTravelers();
    updateStats();
}

function getFallbackTravelers() {
    return [
        {
            id: 1, first_name: 'John', last_name: 'Doe',
            passport_name: 'John Doe', passport_no: 'A0000001',
            mobile: '9000000000', email: 'john@example.com',
            batch_id: 1, batch_name: 'Haj Platinum 2026',
            passport_status: 'Active', passport_expiry_date: '2030-01-01',
            expected_return_date: '2026-07-15', file_reference: 'REF-001',
            mailing_address: '123 Main St, Chennai, India',
            created_at: '2026-01-01T10:00:00'
        },
        {
            id: 2, first_name: 'Jane', last_name: 'Smith',
            passport_name: 'Jane Smith', passport_no: 'A0000002',
            mobile: '9000000001', email: 'jane@example.com',
            batch_id: 2, batch_name: 'Haj Gold 2026',
            passport_status: 'Active', passport_expiry_date: '2029-06-01',
            expected_return_date: '2026-07-20', file_reference: 'REF-002',
            mailing_address: '456 Park Ave, Mumbai, India',
            created_at: '2026-01-02T10:00:00'
        }
    ];
}

// ============================================================
// DISPLAY TRAVELERS
// ============================================================
function displayTravelers() {
    const tableBody = document.getElementById('travelersTableBody');
    if (!tableBody) return;
    
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const end = Math.min(start + ITEMS_PER_PAGE, filteredTravelers.length);
    const pageItems = filteredTravelers.slice(start, end);
    
    if (filteredTravelers.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="11" style="text-align: center; padding: 40px;">No travelers found</td></tr>';
        updatePaginationInfo(0);
        return;
    }
    
    let html = '';
    pageItems.forEach(t => {
        const fullName = `${t.first_name || ''} ${t.last_name || ''}`.trim() || 'N/A';
        const statusClass = t.passport_status === 'Active' ? 'status-active' :
                           t.passport_status === 'Submitted' ? 'status-pending' :
                           t.passport_status === 'Processing' ? 'status-warning' : 'status-inactive';
        
        const daysLeft = t.passport_expiry_date ? daysUntil(t.passport_expiry_date) : null;
        const expiryWarning = daysLeft !== null && daysLeft < 90 ? ' ⚠️' : '';
        
        // Document icons
        const docIcons = `
            <div class="doc-icons">
                <i class="fas fa-passport doc-icon ${t.passport_scan ? 'available' : 'missing'}"
                   onclick="${t.passport_scan ? `viewUploadedDocument('passport', '${t.passport_scan}')` : ''}"
                   title="Passport: ${t.passport_scan || 'Missing'}"
                   style="cursor: ${t.passport_scan ? 'pointer' : 'default'}"></i>
                <i class="fas fa-id-card doc-icon ${t.aadhaar_scan ? 'available' : 'missing'}"
                   onclick="${t.aadhaar_scan ? `viewUploadedDocument('aadhaar', '${t.aadhaar_scan}')` : ''}"
                   title="Aadhaar: ${t.aadhaar_scan || 'Missing'}"
                   style="cursor: ${t.aadhaar_scan ? 'pointer' : 'default'}"></i>
                <i class="fas fa-credit-card doc-icon ${t.pan_scan ? 'available' : 'missing'}"
                   onclick="${t.pan_scan ? `viewUploadedDocument('pan', '${t.pan_scan}')` : ''}"
                   title="PAN: ${t.pan_scan || 'Missing'}"
                   style="cursor: ${t.pan_scan ? 'pointer' : 'default'}"></i>
                <i class="fas fa-syringe doc-icon ${t.vaccine_scan ? 'available' : 'missing'}"
                   onclick="${t.vaccine_scan ? `viewUploadedDocument('vaccine', '${t.vaccine_scan}')` : ''}"
                   title="Vaccine: ${t.vaccine_scan || 'Missing'}"
                   style="cursor: ${t.vaccine_scan ? 'pointer' : 'default'}"></i>
                <i class="fas fa-camera doc-icon ${t.photo ? 'available' : 'missing'}"
                   onclick="${t.photo ? `viewUploadedDocument('photo', '${t.photo}')` : ''}"
                   title="Photo: ${t.photo || 'Missing'}"
                   style="cursor: ${t.photo ? 'pointer' : 'default'}"></i>
            </div>
        `;
        
        html += `<tr>
            <td>${t.id}</td>
            <td><strong>${escapeHtml(fullName)}</strong><br><small>${escapeHtml(t.passport_name || '')}</small></td>
            <td>${escapeHtml(t.passport_no || '-')}<br><small>Exp: ${t.passport_expiry_date || 'N/A'}${expiryWarning}</small></td>
            <td>${escapeHtml(t.mobile || '-')}</td>
            <td>${escapeHtml(t.email || '-')}</td>
            <td>${escapeHtml(t.batch_name || 'Not Assigned')}</td>
            <td>${t.expected_return_date ? escapeHtml(t.expected_return_date) : '-'}</td>
            <td>${escapeHtml(t.file_reference || '-')}</td>
            <td><span class="status-badge ${statusClass}">${escapeHtml(t.passport_status || 'Active')}</span></td>
            <td>${docIcons}</td>
            <td>
                <button class="icon-btn" onclick="viewTraveler(${t.id})" title="View"><i class="fas fa-eye"></i></button>
                <button class="icon-btn" onclick="editTraveler(${t.id})" title="Edit"><i class="fas fa-edit"></i></button>
                <button class="icon-btn" onclick="deleteTraveler(${t.id})" title="Delete"><i class="fas fa-trash"></i></button>
            </td>
        </tr>`;
    });
    
    tableBody.innerHTML = html;
    updatePaginationInfo(filteredTravelers.length);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================
// UPDATE STATS
// ============================================================
function updateStats() {
    const total = travelersData.length;
    const active = travelersData.filter(t => t.passport_status === 'Active').length;
    const vaccinated = travelersData.filter(t => t.vaccine_status === 'Fully Vaccinated').length;
    const docsComplete = travelersData.filter(t => t.passport_scan && t.aadhaar_scan && t.pan_scan && t.photo).length;
    
    document.getElementById('totalTravelersCount').textContent = total;
    document.getElementById('activeTravelersCount').textContent = active;
    document.getElementById('vaccinatedCount').textContent = vaccinated;
    document.getElementById('documentsComplete').textContent = docsComplete;
}

// ============================================================
// PAGINATION
// ============================================================
function updatePaginationInfo(total) {
    document.getElementById('totalCount').textContent = total;
    const start = total > 0 ? (currentPage - 1) * ITEMS_PER_PAGE + 1 : 0;
    const end = Math.min(currentPage * ITEMS_PER_PAGE, total);
    document.getElementById('showingFrom').textContent = start;
    document.getElementById('showingTo').textContent = end;
    
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    if (prevBtn) prevBtn.disabled = currentPage === 1;
    if (nextBtn) nextBtn.disabled = end >= total;
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        displayTravelers();
    }
}

function nextPage() {
    if (currentPage * ITEMS_PER_PAGE < filteredTravelers.length) {
        currentPage++;
        displayTravelers();
    }
}

// ============================================================
// SEARCH
// ============================================================
function searchTravelers() {
    const query = document.getElementById('searchTravelers').value.toLowerCase().trim();
    if (!query) {
        filteredTravelers = [...travelersData];
    } else {
        filteredTravelers = travelersData.filter(t => {
            const fullName = `${t.first_name || ''} ${t.last_name || ''}`.toLowerCase();
            const passport = (t.passport_no || '').toLowerCase();
            const mobile = (t.mobile || '').toLowerCase();
            const email = (t.email || '').toLowerCase();
            const batch = (t.batch_name || '').toLowerCase();
            const fileRef = (t.file_reference || '').toLowerCase();
            return fullName.includes(query) || passport.includes(query) || 
                   mobile.includes(query) || email.includes(query) || 
                   batch.includes(query) || fileRef.includes(query);
        });
    }
    currentPage = 1;
    displayTravelers();
}

function clearSearch() {
    document.getElementById('searchTravelers').value = '';
    filteredTravelers = [...travelersData];
    currentPage = 1;
    displayTravelers();
}

// ============================================================
// FORM VISIBILITY
// ============================================================
function showAddTravelerForm() {
    document.getElementById('addTravelerForm').style.display = 'block';
    loadBatches();
    document.getElementById('addTravelerForm').scrollIntoView({ behavior: 'smooth' });
}

function hideAddTravelerForm() {
    document.getElementById('addTravelerForm').style.display = 'none';
    document.getElementById('travelerAddForm').reset();
    resetDocumentPreviews('add');
}

function hideEditTravelerForm() {
    document.getElementById('editTravelerForm').style.display = 'none';
    currentEditId = null;
    resetDocumentPreviews('edit');
}

function resetDocumentPreviews(prefix) {
    const previewIds = [
        `${prefix}_passport_scan_preview`,
        `${prefix}_aadhaar_scan_preview`,
        `${prefix}_pan_scan_preview`,
        `${prefix}_vaccine_scan_preview`,
        `${prefix}_photo_preview`
    ];
    const textIds = [
        `${prefix}_passport_scan_text`,
        `${prefix}_aadhaar_scan_text`,
        `${prefix}_pan_scan_text`,
        `${prefix}_vaccine_scan_text`,
        `${prefix}_photo_text`
    ];
    
    previewIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.innerHTML = '';
            el.style.display = 'none';
        }
    });
    textIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = el.id.includes('edit') ? 'Click to update' : 'Click to upload';
        }
    });
}

function setupFormResets() {
    document.querySelectorAll('.form-container').forEach(container => {
        const resetBtn = container.querySelector('.btn-secondary');
        if (resetBtn) {
            resetBtn.addEventListener('click', function(e) {
                // Only reset if this is a cancel button
                if (this.textContent.trim().toLowerCase().includes('cancel')) {
                    const form = this.closest('form');
                    if (form) form.reset();
                }
            });
        }
    });
}

// ============================================================
// FILE HANDLING
// ============================================================
function handleFileSelect(input, textId, previewId) {
    const textEl = document.getElementById(textId);
    const previewEl = document.getElementById(previewId);
    
    if (!input.files || !input.files[0]) {
        if (textEl) textEl.textContent = textId.includes('edit') ? 'Click to update' : 'Click to upload';
        if (previewEl) previewEl.style.display = 'none';
        return;
    }
    
    const file = input.files[0];
    if (textEl) textEl.textContent = file.name;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        if (!previewEl) return;
        
        const fileType = file.type;
        const isImage = fileType.includes('image');
        const icon = fileType.includes('pdf') ? 'fa-file-pdf' : 'fa-file-image';
        
        previewEl.innerHTML = `
            <div class="file-info">
                <i class="fas ${icon}"></i>
                <span>${file.name} (${(file.size / 1024).toFixed(2)} KB)</span>
            </div>
            <div class="file-actions">
                <button onclick="previewNewDocument('${e.target.result}', '${file.name}', '${fileType}')" title="Preview">
                    <i class="fas fa-eye"></i>
                </button>
                <button onclick="removeNewDocument('${input.id}', '${textId}', '${previewId}')" class="delete" title="Remove">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        previewEl.style.display = 'flex';
    };
    reader.readAsDataURL(file);
}

function removeNewDocument(inputId, textId, previewId) {
    const input = document.getElementById(inputId);
    if (input) input.value = '';
    
    const textEl = document.getElementById(textId);
    if (textEl) textEl.textContent = textId.includes('edit') ? 'Click to update' : 'Click to upload';
    
    const previewEl = document.getElementById(previewId);
    if (previewEl) {
        previewEl.innerHTML = '';
        previewEl.style.display = 'none';
    }
}

// ============================================================
// DOCUMENT VIEWING
// ============================================================
function viewUploadedDocument(docType, filename) {
    if (!filename) {
        showNotification('No document available', 'error');
        return;
    }
    
    const subfolderMap = {
        'passport': 'passports',
        'aadhaar': 'aadhaar',
        'pan': 'pan',
        'vaccine': 'vaccine',
        'photo': 'photos'
    };
    
    const subfolder = subfolderMap[docType] || 'documents';
    const url = `/uploads/${subfolder}/${filename}`;
    window.open(url, '_blank');
}

function previewNewDocument(dataUrl, fileName, fileType) {
    currentDocument = { data: dataUrl, name: fileName, type: fileType };
    currentDocumentName = fileName;
    
    document.getElementById('documentViewerTitle').textContent = fileName;
    const content = document.getElementById('documentViewerContent');
    
    if (fileType.includes('pdf')) {
        content.innerHTML = `<iframe src="${dataUrl}" style="width:100%;height:500px;border:none;"></iframe>`;
    } else if (fileType.includes('image')) {
        content.innerHTML = `<img src="${dataUrl}" alt="${fileName}" style="max-width:100%;max-height:500px;">`;
    } else {
        content.innerHTML = `<p>Cannot preview this file type. Click Download to view.</p>`;
    }
    
    document.getElementById('documentViewerModal').style.display = 'block';
    document.getElementById('modalOverlay').style.display = 'block';
}

function closeDocumentViewer() {
    document.getElementById('documentViewerModal').style.display = 'none';
    document.getElementById('modalOverlay').style.display = 'none';
    currentDocument = null;
}

function downloadCurrentDocument() {
    if (!currentDocument) {
        showNotification('No document to download', 'error');
        return;
    }
    const a = document.createElement('a');
    a.href = currentDocument.data;
    a.download = currentDocumentName;
    a.click();
    showNotification('Document downloaded', 'success');
}

// ============================================================
// CREATE TRAVELER
// ============================================================
async function createTraveler() {
    const form = document.getElementById('travelerAddForm');
    if (!form) return;
    
    const formData = new FormData(form);
    
    // Get values for validation
    const firstName = document.getElementById('add_first_name')?.value?.trim();
    const lastName = document.getElementById('add_last_name')?.value?.trim();
    const passportNo = document.getElementById('add_passport_no')?.value?.trim();
    const mobile = document.getElementById('add_mobile')?.value?.trim();
    const batchId = document.getElementById('add_batch_id')?.value;
    const passportExpiry = document.getElementById('add_passport_expiry_date')?.value;
    const expectedReturn = document.getElementById('add_expected_return_date')?.value;
    
    // Validate required fields
    if (!firstName || !lastName || !passportNo || !mobile) {
        showNotification('First name, last name, passport number, and mobile are required', 'error');
        return;
    }
    if (!batchId) {
        showNotification('Please select a batch', 'error');
        return;
    }
    
    // Validate passport validity
    const validation = validatePassportValidity(passportExpiry, expectedReturn);
    if (!validation.valid) {
        showNotification(validation.message, 'error');
        return;
    }
    
    const submitBtn = form.querySelector('button[type="submit"]');
    showLoading(submitBtn, 'Saving...');
    
    try {
        const response = await fetch('/api/travelers', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const days = daysUntil(passportExpiry);
            if (days !== null) {
                showNotification(`Traveler created. Passport expires in ${days} day(s).`, 'success');
            } else {
                showNotification('Traveler created successfully!', 'success');
            }
            hideAddTravelerForm();
            await loadTravelers();
        } else {
            showNotification('Error: ' + (data.error || 'Could not create traveler'), 'error');
        }
    } catch (error) {
        console.error('Create error:', error);
        showNotification('Network error. Please try again.', 'error');
    } finally {
        hideLoading(submitBtn);
    }
}

// ============================================================
// EDIT TRAVELER
// ============================================================
function editTraveler(id) {
    const traveler = travelersData.find(t => t.id === id);
    if (!traveler) {
        showNotification('Traveler not found', 'error');
        return;
    }
    
    currentEditId = id;
    const form = document.getElementById('editTravelerForm');
    if (!form) return;
    
    // Populate fields
    const fieldMap = {
        'edit_traveler_id': id,
        'edit_first_name': traveler.first_name,
        'edit_last_name': traveler.last_name,
        'edit_passport_name': traveler.passport_name,
        'edit_batch_id': traveler.batch_id,
        'edit_passport_no': traveler.passport_no,
        'edit_passport_issue_date': formatDateForInput(traveler.passport_issue_date),
        'edit_passport_expiry_date': formatDateForInput(traveler.passport_expiry_date),
        'edit_passport_status': traveler.passport_status || 'Active',
        'edit_gender': traveler.gender || '',
        'edit_dob': formatDateForInput(traveler.dob),
        'edit_mobile': traveler.mobile,
        'edit_email': traveler.email,
        'edit_aadhaar': traveler.aadhaar,
        'edit_pan': traveler.pan,
        'edit_aadhaar_pan_linked': traveler.aadhaar_pan_linked || 'No',
        'edit_vaccine_status': traveler.vaccine_status || 'Not Vaccinated',
        'edit_wheelchair': traveler.wheelchair || 'No',
        'edit_place_of_birth': traveler.place_of_birth,
        'edit_place_of_issue': traveler.place_of_issue,
        'edit_passport_address': traveler.passport_address,
        'edit_mailing_address': traveler.mailing_address,
        'edit_expected_return_date': formatDateForInput(traveler.expected_return_date),
        'edit_file_reference': traveler.file_reference,
        'edit_father_name': traveler.father_name,
        'edit_mother_name': traveler.mother_name,
        'edit_spouse_name': traveler.spouse_name,
        'edit_pin': traveler.pin || '0000',
        'edit_emergency_contact': traveler.emergency_contact,
        'edit_emergency_phone': traveler.emergency_phone,
        'edit_medical_notes': traveler.medical_notes
    };
    
    Object.entries(fieldMap).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) el.value = value || '';
    });
    
    // Show existing documents
    showExistingDocument('edit_passport_scan_preview', traveler.passport_scan, 'passport');
    showExistingDocument('edit_aadhaar_scan_preview', traveler.aadhaar_scan, 'aadhaar');
    showExistingDocument('edit_pan_scan_preview', traveler.pan_scan, 'pan');
    showExistingDocument('edit_vaccine_scan_preview', traveler.vaccine_scan, 'vaccine');
    showExistingDocument('edit_photo_preview', traveler.photo, 'photo');
    
    form.style.display = 'block';
    form.scrollIntoView({ behavior: 'smooth' });
}

function showExistingDocument(previewId, filename, docType) {
    const previewEl = document.getElementById(previewId);
    if (!previewEl) return;
    
    if (!filename) {
        previewEl.style.display = 'none';
        return;
    }
    
    const subfolderMap = {
        'passport': 'passports',
        'aadhaar': 'aadhaar',
        'pan': 'pan',
        'vaccine': 'vaccine',
        'photo': 'photos'
    };
    const subfolder = subfolderMap[docType] || 'documents';
    const viewUrl = `/uploads/${subfolder}/${filename}`;
    
    previewEl.innerHTML = `
        <div class="file-info">
            <i class="fas fa-file"></i>
            <span>${filename} (Uploaded)</span>
        </div>
        <div class="file-actions">
            <button onclick="window.open('${viewUrl}', '_blank')" title="View">
                <i class="fas fa-eye"></i>
            </button>
            <a href="${viewUrl}" download="${filename}" title="Download">
                <i class="fas fa-download"></i>
            </a>
            <span title="File saved in database" style="color: #27ae60;">
                <i class="fas fa-check-circle"></i>
            </span>
        </div>
    `;
    previewEl.style.display = 'flex';
}

// ============================================================
// UPDATE TRAVELER
// ============================================================
async function updateTraveler() {
    if (!currentEditId) {
        showNotification('No traveler selected for editing', 'error');
        return;
    }
    
    const form = document.getElementById('travelerEditForm');
    if (!form) return;
    
    const formData = new FormData(form);
    
    // Validate required fields
    const firstName = document.getElementById('edit_first_name')?.value?.trim();
    const lastName = document.getElementById('edit_last_name')?.value?.trim();
    const passportNo = document.getElementById('edit_passport_no')?.value?.trim();
    const mobile = document.getElementById('edit_mobile')?.value?.trim();
    const batchId = document.getElementById('edit_batch_id')?.value;
    const passportExpiry = document.getElementById('edit_passport_expiry_date')?.value;
    const expectedReturn = document.getElementById('edit_expected_return_date')?.value;
    
    if (!firstName || !lastName || !passportNo || !mobile) {
        showNotification('First name, last name, passport number, and mobile are required', 'error');
        return;
    }
    if (!batchId) {
        showNotification('Please select a batch', 'error');
        return;
    }
    
    // Validate passport validity
    const validation = validatePassportValidity(passportExpiry, expectedReturn);
    if (!validation.valid) {
        showNotification(validation.message, 'error');
        return;
    }
    
    const submitBtn = form.querySelector('button[type="submit"]');
    showLoading(submitBtn, 'Updating...');
    
    try {
        const response = await fetch(`/api/travelers/${currentEditId}`, {
            method: 'PUT',
            body: formData,
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const days = daysUntil(passportExpiry);
            if (days !== null) {
                showNotification(`Traveler updated. Passport expires in ${days} day(s).`, 'success');
            } else {
                showNotification('Traveler updated successfully!', 'success');
            }
            hideEditTravelerForm();
            await loadTravelers();
        } else {
            showNotification('Error: ' + (data.error || 'Update failed'), 'error');
        }
    } catch (error) {
        console.error('Update error:', error);
        showNotification('Network error. Please try again.', 'error');
    } finally {
        hideLoading(submitBtn);
    }
}

// ============================================================
// DELETE TRAVELER
// ============================================================
async function deleteTraveler(id) {
    if (!confirm('Are you sure you want to delete this traveler? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/travelers/${id}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Traveler deleted successfully!', 'success');
            await loadTravelers();
        } else {
            showNotification('Error: ' + (data.error || 'Could not delete traveler'), 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showNotification('Network error. Please try again.', 'error');
    }
}

// ============================================================
// VIEW TRAVELER
// ============================================================
function viewTraveler(id) {
    const traveler = travelersData.find(t => t.id === id);
    if (!traveler) {
        showNotification('Traveler not found', 'error');
        return;
    }
    displayTravelerDetails(traveler);
}

function displayTravelerDetails(t) {
    const formatValue = (val) => val && val !== '' ? escapeHtml(val) : '<span style="color: #95a5a6;">Not specified</span>';
    const formatDate = (date) => date ? new Date(date).toLocaleDateString() : 'Not specified';
    
    const documentCards = `
        <div class="document-card" onclick="${t.passport_scan ? `viewUploadedDocument('passport', '${t.passport_scan}')` : ''}" style="cursor: ${t.passport_scan ? 'pointer' : 'default'}">
            <i class="fas fa-passport ${t.passport_scan ? '' : 'missing'}"></i>
            <p><strong>Passport</strong></p>
            <p>${t.passport_scan ? '✅ Uploaded' : '❌ Missing'}</p>
            ${t.passport_scan ? `<small>${t.passport_scan}</small>` : ''}
        </div>
        <div class="document-card" onclick="${t.aadhaar_scan ? `viewUploadedDocument('aadhaar', '${t.aadhaar_scan}')` : ''}" style="cursor: ${t.aadhaar_scan ? 'pointer' : 'default'}">
            <i class="fas fa-id-card ${t.aadhaar_scan ? '' : 'missing'}"></i>
            <p><strong>Aadhaar</strong></p>
            <p>${t.aadhaar_scan ? '✅ Uploaded' : '❌ Missing'}</p>
            ${t.aadhaar_scan ? `<small>${t.aadhaar_scan}</small>` : ''}
        </div>
        <div class="document-card" onclick="${t.pan_scan ? `viewUploadedDocument('pan', '${t.pan_scan}')` : ''}" style="cursor: ${t.pan_scan ? 'pointer' : 'default'}">
            <i class="fas fa-credit-card ${t.pan_scan ? '' : 'missing'}"></i>
            <p><strong>PAN</strong></p>
            <p>${t.pan_scan ? '✅ Uploaded' : '❌ Missing'}</p>
            ${t.pan_scan ? `<small>${t.pan_scan}</small>` : ''}
        </div>
        <div class="document-card" onclick="${t.vaccine_scan ? `viewUploadedDocument('vaccine', '${t.vaccine_scan}')` : ''}" style="cursor: ${t.vaccine_scan ? 'pointer' : 'default'}">
            <i class="fas fa-syringe ${t.vaccine_scan ? '' : 'missing'}"></i>
            <p><strong>Vaccine</strong></p>
            <p>${t.vaccine_scan ? '✅ Uploaded' : '❌ Missing'}</p>
            ${t.vaccine_scan ? `<small>${t.vaccine_scan}</small>` : ''}
        </div>
        <div class="document-card" onclick="${t.photo ? `viewUploadedDocument('photo', '${t.photo}')` : ''}" style="cursor: ${t.photo ? 'pointer' : 'default'}">
            <i class="fas fa-camera ${t.photo ? '' : 'missing'}"></i>
            <p><strong>Photo</strong></p>
            <p>${t.photo ? '✅ Uploaded' : '❌ Missing'}</p>
            ${t.photo ? `<small>${t.photo}</small>` : ''}
        </div>
    `;
    
    const detailsHtml = `
        <h4 style="color: #2c3e50; margin: 20px 0 10px; border-bottom: 2px solid #3498db; padding-bottom: 5px;">
            <i class="fas fa-user"></i> Personal Information
        </h4>
        <div class="detail-grid">
            <div class="detail-item"><strong>Full Name:</strong> <span>${t.first_name || ''} ${t.last_name || ''}</span></div>
            <div class="detail-item"><strong>Passport Name:</strong> <span>${formatValue(t.passport_name)}</span></div>
            <div class="detail-item"><strong>Batch:</strong> <span>${formatValue(t.batch_name)}</span></div>
            <div class="detail-item"><strong>Passport Number:</strong> <span>${formatValue(t.passport_no)}</span></div>
            <div class="detail-item"><strong>Passport Issue Date:</strong> <span>${formatDate(t.passport_issue_date)}</span></div>
            <div class="detail-item"><strong>Passport Expiry Date:</strong> <span>${formatDate(t.passport_expiry_date)}</span></div>
            <div class="detail-item"><strong>Passport Status:</strong> <span class="status-badge status-active">${formatValue(t.passport_status)}</span></div>
            <div class="detail-item"><strong>Gender:</strong> <span>${formatValue(t.gender)}</span></div>
            <div class="detail-item"><strong>Date of Birth:</strong> <span>${formatDate(t.dob)}</span></div>
        </div>

        <h4 style="color: #2c3e50; margin: 20px 0 10px; border-bottom: 2px solid #3498db; padding-bottom: 5px;">
            <i class="fas fa-address-book"></i> Contact Information
        </h4>
        <div class="detail-grid">
            <div class="detail-item"><strong>Mobile:</strong> <span>${formatValue(t.mobile)}</span></div>
            <div class="detail-item"><strong>Email:</strong> <span>${formatValue(t.email)}</span></div>
            <div class="detail-item"><strong>Aadhaar:</strong> <span>${formatValue(t.aadhaar)}</span></div>
            <div class="detail-item"><strong>PAN:</strong> <span>${formatValue(t.pan)}</span></div>
            <div class="detail-item"><strong>Aadhaar-PAN Linked:</strong> <span>${formatValue(t.aadhaar_pan_linked)}</span></div>
            <div class="detail-item"><strong>Vaccine Status:</strong> <span>${formatValue(t.vaccine_status)}</span></div>
            <div class="detail-item"><strong>Wheelchair Required:</strong> <span>${formatValue(t.wheelchair)}</span></div>
        </div>

        <h4 style="color: #2c3e50; margin: 20px 0 10px; border-bottom: 2px solid #3498db; padding-bottom: 5px;">
            <i class="fas fa-home"></i> Address & Family
        </h4>
        <div class="detail-grid">
            <div class="detail-item"><strong>Place of Birth:</strong> <span>${formatValue(t.place_of_birth)}</span></div>
            <div class="detail-item"><strong>Place of Issue:</strong> <span>${formatValue(t.place_of_issue)}</span></div>
            <div class="detail-item full-width"><strong>Passport Address:</strong> <span>${formatValue(t.passport_address)}</span></div>
            <div class="detail-item full-width"><strong>Mailing Address:</strong> <span>${formatValue(t.mailing_address)}</span></div>
            <div class="detail-item"><strong>Father's Name:</strong> <span>${formatValue(t.father_name)}</span></div>
            <div class="detail-item"><strong>Mother's Name:</strong> <span>${formatValue(t.mother_name)}</span></div>
            <div class="detail-item"><strong>Spouse's Name:</strong> <span>${formatValue(t.spouse_name)}</span></div>
        </div>

        <h4 style="color: #2c3e50; margin: 20px 0 10px; border-bottom: 2px solid #3498db; padding-bottom: 5px;">
            <i class="fas fa-calendar-alt"></i> Travel & Return Information
        </h4>
        <div class="detail-grid">
            <div class="detail-item"><strong>Expected Return Date:</strong> <span>${formatDate(t.expected_return_date)}</span></div>
            <div class="detail-item"><strong>File Reference:</strong> <span>${formatValue(t.file_reference)}</span></div>
        </div>

        <h4 style="color: #2c3e50; margin: 20px 0 10px; border-bottom: 2px solid #3498db; padding-bottom: 5px;">
            <i class="fas fa-file-alt"></i> Documents
        </h4>
        <div class="document-grid">${documentCards}</div>

        <h4 style="color: #2c3e50; margin: 20px 0 10px; border-bottom: 2px solid #3498db; padding-bottom: 5px;">
            <i class="fas fa-cog"></i> Additional Information
        </h4>
        <div class="detail-grid">
            <div class="detail-item"><strong>PIN:</strong> <span>${formatValue(t.pin)}</span></div>
            <div class="detail-item"><strong>Emergency Contact:</strong> <span>${formatValue(t.emergency_contact)}</span></div>
            <div class="detail-item"><strong>Emergency Phone:</strong> <span>${formatValue(t.emergency_phone)}</span></div>
            <div class="detail-item"><strong>Medical Notes:</strong> <span>${formatValue(t.medical_notes)}</span></div>
            <div class="detail-item"><strong>Created:</strong> <span>${t.created_at ? new Date(t.created_at).toLocaleString() : '-'}</span></div>
        </div>
    `;
    
    document.getElementById('travelerDetails').innerHTML = detailsHtml;
    document.getElementById('viewTravelerModal').style.display = 'block';
    document.getElementById('modalOverlay').style.display = 'block';
}

// ============================================================
// MODAL CONTROLS
// ============================================================
function closeTravelerModal() {
    document.getElementById('viewTravelerModal').style.display = 'none';
    document.getElementById('modalOverlay').style.display = 'none';
}

function closeAllModals() {
    closeTravelerModal();
    closeDocumentViewer();
}

// ============================================================
// EXPORT FUNCTIONS
// ============================================================
function exportTravelersToExcel() {
    const headers = [
        'ID', 'First Name', 'Last Name', 'Passport Name', 'Batch ID', 'Batch Name',
        'Passport Number', 'Passport Issue Date', 'Passport Expiry Date', 'Passport Status',
        'Gender', 'Date of Birth', 'Mobile', 'Email', 'Aadhaar', 'PAN', 'Aadhaar-PAN Linked',
        'Vaccine Status', 'Wheelchair', 'Place of Birth', 'Place of Issue', 'Passport Address',
        'Mailing Address', 'Father Name', 'Mother Name', 'Spouse Name',
        'Expected Return Date', 'File Reference',
        'PIN', 'Emergency Contact', 'Emergency Phone', 'Medical Notes',
        'Passport Scan', 'Aadhaar Scan', 'PAN Scan', 'Vaccine Scan', 'Photo', 'Created At'
    ];
    
    let csv = ['"' + headers.join('","') + '"'];
    
    travelersData.forEach(t => {
        const row = [
            t.id || '', t.first_name || '', t.last_name || '', t.passport_name || '',
            t.batch_id || '', t.batch_name || '', t.passport_no || '',
            t.passport_issue_date || '', t.passport_expiry_date || '', t.passport_status || '',
            t.gender || '', t.dob || '', t.mobile || '', t.email || '',
            t.aadhaar || '', t.pan || '', t.aadhaar_pan_linked || '',
            t.vaccine_status || '', t.wheelchair || '', t.place_of_birth || '', t.place_of_issue || '',
            (t.passport_address || '').replace(/"/g, '""'),
            (t.mailing_address || '').replace(/"/g, '""'),
            t.father_name || '', t.mother_name || '', t.spouse_name || '',
            t.expected_return_date || '', t.file_reference || '',
            t.pin || '', t.emergency_contact || '', t.emergency_phone || '',
            (t.medical_notes || '').replace(/"/g, '""'),
            t.passport_scan || '', t.aadhaar_scan || '', t.pan_scan || '',
            t.vaccine_scan || '', t.photo || '', t.created_at || ''
        ];
        csv.push('"' + row.join('","') + '"');
    });
    
    const blob = new Blob([csv.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `travelers_export_${new Date().toISOString().slice(0,10)}.csv`;
    link.click();
    showNotification('Travelers data exported successfully!', 'success');
}

function exportTravelersToPDF() {
    if (typeof window.jspdf === 'undefined') {
        showNotification('PDF library not loaded. Please refresh.', 'error');
        return;
    }
    
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF('landscape');
    
    doc.setFontSize(18);
    doc.text('Alhudha Haj Travel - Travelers List', 14, 22);
    doc.setFontSize(11);
    doc.text(`Generated on: ${new Date().toLocaleString()}`, 14, 30);
    
    const headers = ['ID', 'Name', 'Passport', 'Mobile', 'Email', 'Batch', 'Return Date', 'File Ref'];
    const rows = travelersData.map(t => {
        const name = `${t.first_name || ''} ${t.last_name || ''}`.trim() || 'N/A';
        return [
            t.id,
            name,
            t.passport_no || '-',
            t.mobile || '-',
            t.email || '-',
            t.batch_name || '-',
            t.expected_return_date || '-',
            t.file_reference || '-'
        ];
    });
    
    doc.autoTable({
        head: [headers],
        body: rows,
        startY: 35,
        styles: { fontSize: 7 },
        headStyles: { fillColor: [44, 62, 80] }
    });
    
    doc.save(`travelers_${new Date().toISOString().slice(0,10)}.pdf`);
    showNotification('PDF exported successfully!', 'success');
}

function printTravelersTable() {
    const table = document.getElementById('travelersTable');
    if (!table) return;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html><head><title>Travelers List</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            table { width: 100%; border-collapse: collapse; }
            th { background: #2c3e50; color: white; padding: 10px; text-align: left; }
            td { padding: 10px; border-bottom: 1px solid #ddd; }
        </style>
        </head><body>
        <h2>Alhudha Haj Travel - Travelers List</h2>
        <p>Generated on: ${new Date().toLocaleString()}</p>
        ${table.outerHTML}
        </body></html>
    `);
    printWindow.document.close();
    printWindow.print();
}

function printTravelerDetails() {
    const content = document.getElementById('travelerDetails');
    if (!content) return;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html><head><title>Traveler Details</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 30px; }
            .detail-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
            .detail-item { padding: 10px; background: #f8f9fa; border-radius: 5px; }
            .detail-item strong { display: block; color: #7f8c8d; margin-bottom: 5px; }
            .detail-item.full-width { grid-column: 1 / -1; }
            .document-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; }
            .document-card { background: white; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #ddd; }
            .status-badge { padding: 5px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; display: inline-block; }
            .status-active { background: #d4edda; color: #155724; }
            @media print { body { padding: 15px; } }
        </style>
        </head><body>
        ${content.innerHTML}
        </body></html>
    `);
    printWindow.document.close();
    printWindow.print();
}

function downloadTravelerPDF() {
    showNotification('PDF download feature coming soon', 'info');
}

// ============================================================
// CSV UPLOAD
// ============================================================
function showCSVUploadSection() {
    document.getElementById('csvUploadSection').style.display = 'block';
    document.getElementById('csvUploadSection').scrollIntoView({ behavior: 'smooth' });
}

function hideCSVUploadSection() {
    document.getElementById('csvUploadSection').style.display = 'none';
    document.getElementById('csvFileInput').value = '';
    document.getElementById('csvPreview').style.display = 'none';
}

function downloadCSVTemplate() {
    const headers = [
        'first_name', 'last_name', 'passport_name', 'batch_id',
        'passport_no', 'passport_issue_date', 'passport_expiry_date', 'passport_status',
        'gender', 'dob', 'mobile', 'email', 'aadhaar', 'pan', 'aadhaar_pan_linked',
        'vaccine_status', 'wheelchair', 'place_of_birth', 'place_of_issue', 'passport_address',
        'mailing_address', 'father_name', 'mother_name', 'spouse_name',
        'expected_return_date', 'file_reference',
        'pin', 'emergency_contact', 'emergency_phone', 'medical_notes'
    ];
    
    const sample = [
        'John', 'Doe', 'John Doe', '1',
        'A0000001', '2020-01-01', '2030-01-01', 'Active',
        'Male', '1990-01-01', '9000000000', 'john@example.com', '000000000000', 'AAAAA0000A', 'No',
        'Not Vaccinated', 'No', 'City Name', 'City Name', '123 Passport Street, City',
        '123 Mailing Street, City', 'Father Name', 'Mother Name', 'Spouse Name',
        '2026-07-15', 'REF-001',
        '0000', 'Emergency Contact', '9000000001', 'No medical notes'
    ];
    
    let csv = headers.join(',') + '\n';
    csv += sample.join(',') + '\n';
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'travelers_template.csv';
    link.click();
    showNotification('CSV template downloaded', 'success');
}

async function uploadCSV() {
    const fileInput = document.getElementById('csvFileInput');
    if (!fileInput.files || fileInput.files.length === 0) {
        showNotification('Please select a CSV file', 'error');
        return;
    }
    
    const file = fileInput.files[0];
    
    // Preview first
    const reader = new FileReader();
    reader.onload = function(e) {
        const lines = e.target.result.split('\n');
        const headers = lines[0].split(',');
        
        const previewDiv = document.getElementById('csvPreview');
        const previewContent = document.getElementById('csvPreviewContent');
        
        let html = '<table style="width:100%;border-collapse:collapse;font-size:12px;">';
        html += '<tr>';
        headers.slice(0, 10).forEach(h => {
            html += `<th style="padding:6px;border:1px solid #ddd;background:#f8f9fa;">${h}</th>`;
        });
        html += '<th>...</th></tr>';
        
        for (let i = 1; i < Math.min(lines.length, 6); i++) {
            if (lines[i].trim()) {
                const cells = lines[i].split(',');
                html += '<tr>';
                for (let j = 0; j < Math.min(10, cells.length); j++) {
                    html += `<td style="padding:6px;border:1px solid #ddd;">${cells[j]?.replace(/"/g, '') || ''}</td>`;
                }
                html += '<td>...</td></tr>';
            }
        }
        html += '</table>';
        previewContent.innerHTML = html;
        previewDiv.style.display = 'block';
    };
    reader.readAsText(file);
}

// ============================================================
// SESSION MANAGEMENT
// ============================================================
let sessionWarningTimeout = null;
let sessionLogoutTimeout = null;
let warningShown = false;

function resetSessionTimer() {
    if (sessionWarningTimeout) clearTimeout(sessionWarningTimeout);
    if (sessionLogoutTimeout) clearTimeout(sessionLogoutTimeout);
    hideSessionWarning();
    sessionWarningTimeout = setTimeout(showSessionWarning, 1500000);
    sessionLogoutTimeout = setTimeout(showSessionExpiredWarning, 1800000);
}

function showSessionWarning() {
    if (warningShown) return;
    const warning = document.getElementById('sessionWarning');
    if (!warning) return;
    warning.style.display = 'block';
    warningShown = true;
}

function hideSessionWarning() {
    const warning = document.getElementById('sessionWarning');
    if (warning) warning.style.display = 'none';
    warningShown = false;
}

function showSessionExpiredWarning() {
    hideSessionWarning();
    showNotification('Your session has expired. Redirecting to login...', 'warning');
    setTimeout(() => {
        if (typeof SessionManager !== 'undefined' && SessionManager.logout) {
            SessionManager.logout();
        } else {
            window.location.href = '/admin/login.html';
        }
    }, 3000);
}

async function extendSession() {
    try {
        if (typeof SessionManager !== 'undefined' && SessionManager.checkSession) {
            await SessionManager.checkSession();
        }
        hideSessionWarning();
        resetSessionTimer();
        showNotification('Session extended successfully', 'success');
    } catch (error) {
        console.error('Session extension failed:', error);
        showSessionExpiredWarning();
    }
}

// ============================================================
// UI HELPERS
// ============================================================
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    if (!notification) return;
    
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `<i class="fas fa-${icons[type] || 'info-circle'}"></i> ${message}`;
    notification.style.display = 'block';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

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
    btn.innerHTML = btn.innerHTML.replace('fas fa-spinner fa-spin', 'fas fa-save');
}

async function logout() {
    if (confirm('Are you sure you want to logout?')) {
        if (typeof SessionManager !== 'undefined' && SessionManager.logout) {
            await SessionManager.logout();
        } else {
            window.location.href = '/admin/login.html';
        }
    }
}

console.log('✅ Travelers module loaded successfully!');
