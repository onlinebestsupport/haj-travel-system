/**
 * travelers.js - Complete implementation for 36-field traveler management
 * Includes: mailing_address, file_reference, expected_return_date
 * Auto-populates expected return date from selected batch
 * Client-side validation: passport expiry must be 6 months after expected return
 */

// ============================================================
// GLOBAL STATE
// ============================================================
let currentEditId = null;
let travelersData = [];
let batchesData = [];
let currentPage = 1;
const ITEMS_PER_PAGE = 10;
let currentDocument = null;
let currentDocumentName = '';
let sessionWarningTimeout = null;
let sessionLogoutTimeout = null;
let warningShown = false;
let notificationTimeout = null;

// ============================================================
// INITIALIZATION
// ============================================================
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Travelers module loading...');
    
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
    resetSessionTimer();
    ['click', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
        document.addEventListener(event, resetSessionTimer);
    });
    await loadBatches();
    await loadTravelers();
    setupPassportNameAutoFill();
    setupMailingAddressToggle();
    setupDateValidation();
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

function formatDateForInput(dateStr) {
    if (!dateStr) return '';
    if (typeof dateStr === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return dateStr;
    if (dateStr instanceof Date) {
        const y = dateStr.getFullYear();
        const m = String(dateStr.getMonth() + 1).padStart(2, '0');
        const d = String(dateStr.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    }
    try {
        const d = new Date(dateStr);
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
        return { valid: true, message: '' };
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
// BATCH SELECT - AUTO POPULATE EXPECTED RETURN DATE
// ============================================================
function onBatchSelect(prefix) {
    console.log(`🔄 onBatchSelect called for prefix: ${prefix}`);
    
    const batchSelect = document.getElementById(prefix + '_batch_id');
    const returnDateInput = document.getElementById(prefix + '_expected_return_date');
    const returnInfoDiv = document.getElementById(prefix + '_batch_return_info');
    const returnTextSpan = document.getElementById(prefix + '_batch_return_text');
    const returnInfoMsg = document.getElementById(prefix + '_expected_return_info');
    const validationDiv = document.getElementById(prefix + '_passport_validation');
    
    if (!batchSelect) {
        console.warn(`⚠️ Batch select not found: ${prefix}_batch_id`);
        return;
    }
    if (!returnDateInput) {
        console.warn(`⚠️ Return date input not found: ${prefix}_expected_return_date`);
        return;
    }
    
    const selectedBatchId = batchSelect.value;
    console.log(`📋 Selected batch ID: ${selectedBatchId}`);
    console.log(`📦 Batches data:`, batchesData);
    
    // Clear previous info
    if (returnInfoMsg) {
        returnInfoMsg.innerHTML = '';
        returnInfoMsg.className = 'expected-return-info';
    }
    if (validationDiv) {
        validationDiv.textContent = '';
        validationDiv.className = 'validation-message';
    }
    
    if (!selectedBatchId) {
        // No batch selected - reset
        returnDateInput.value = '';
        returnDateInput.style.borderColor = '';
        returnDateInput.style.background = '';
        if (returnInfoDiv) returnInfoDiv.classList.remove('show');
        if (returnInfoMsg) {
            returnInfoMsg.innerHTML = 'Please select a batch to auto-populate return date.';
            returnInfoMsg.className = 'expected-return-info warning';
        }
        return;
    }
    
    // Find the selected batch - handle both integer and string IDs
    const batch = batchesData.find(b => String(b.id) === String(selectedBatchId));
    console.log(`🔍 Found batch:`, batch);
    
    if (batch) {
        // Check for return date in multiple possible field names
        const returnDate = batch.return_date || batch.returnDate || batch.expected_return_date || batch.expectedReturnDate || batch.batch_return_date || batch.return_dt;
        console.log(`📅 Return date found: ${returnDate}`);
        
        // Show return info
        if (returnInfoDiv && returnTextSpan) {
            returnInfoDiv.classList.add('show');
            if (returnDate) {
                returnTextSpan.textContent = `Return Date: ${returnDate}`;
                returnInfoDiv.style.borderLeftColor = '#27ae60';
            } else {
                returnTextSpan.textContent = '⚠️ No return date set for this batch';
                returnInfoDiv.style.borderLeftColor = '#f39c12';
            }
        }
        
        // Auto-populate expected return date
        if (returnDate) {
            // Format date if needed (ensure YYYY-MM-DD)
            let formattedDate = returnDate;
            if (returnDate.includes('/')) {
                const parts = returnDate.split('/');
                if (parts.length === 3) {
                    formattedDate = `${parts[2]}-${String(parts[0]).padStart(2, '0')}-${String(parts[1]).padStart(2, '0')}`;
                }
            } else if (returnDate.includes('-')) {
                // Already in YYYY-MM-DD format
                formattedDate = returnDate;
            }
            
            returnDateInput.value = formattedDate;
            returnDateInput.style.borderColor = '#27ae60';
            returnDateInput.style.background = '#f0fff4';
            
            const batchName = batch.batch_name || batch.name || 'Selected Batch';
            if (returnInfoMsg) {
                returnInfoMsg.innerHTML = `<i class="fas fa-check-circle" style="color: #27ae60;"></i> Auto-populated from batch: ${batchName}`;
                returnInfoMsg.className = 'expected-return-info success';
            }
            
            // Clear validation message since return date is now set
            if (validationDiv) {
                validationDiv.textContent = '';
                validationDiv.className = 'validation-message';
            }
            
            // Trigger passport expiry validation
            validatePassportExpiry(prefix);
        } else {
            returnDateInput.value = '';
            returnDateInput.style.borderColor = '#f39c12';
            returnDateInput.style.background = '#fffbf0';
            
            if (returnInfoMsg) {
                returnInfoMsg.innerHTML = `<i class="fas fa-exclamation-triangle" style="color: #f39c12;"></i> Selected batch has no return date set. Please set in batch management.`;
                returnInfoMsg.className = 'expected-return-info warning';
            }
            
            // Show warning in validation area
            if (validationDiv) {
                validationDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Batch has no return date. Please set return date for this batch.`;
                validationDiv.className = 'validation-message warning';
            }
        }
    } else {
        console.warn(`⚠️ Batch not found in batchesData for ID: ${selectedBatchId}`);
        returnDateInput.value = '';
        returnDateInput.style.borderColor = '#e74c3c';
        returnDateInput.style.background = '#fff5f5';
        
        if (returnInfoMsg) {
            returnInfoMsg.innerHTML = `<i class="fas fa-times-circle" style="color: #e74c3c;"></i> Batch not found. Please refresh and try again.`;
            returnInfoMsg.className = 'expected-return-info error';
        }
        if (returnInfoDiv) returnInfoDiv.classList.remove('show');
    }
}

// ============================================================
// VALIDATE PASSPORT EXPIRY (6 months after return date)
// ============================================================
function validatePassportExpiry(prefix) {
    console.log(`🔍 validatePassportExpiry called for prefix: ${prefix}`);
    
    const expiryDateInput = document.getElementById(prefix + '_passport_expiry_date');
    const returnDateInput = document.getElementById(prefix + '_expected_return_date');
    const validationDiv = document.getElementById(prefix + '_passport_validation');
    
    if (!expiryDateInput || !validationDiv) {
        console.warn(`⚠️ Validation elements not found for prefix: ${prefix}`);
        return;
    }
    
    const expiryDate = expiryDateInput.value;
    const returnDate = returnDateInput ? returnDateInput.value : null;
    
    // Clear previous validation
    expiryDateInput.className = '';
    validationDiv.textContent = '';
    validationDiv.className = 'validation-message';
    
    if (!expiryDate) {
        console.log('ℹ️ No expiry date set');
        return;
    }
    
    if (!returnDate) {
        // No return date set - show warning but not error
        validationDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Expected return date not set. Please select a batch with return date.`;
        validationDiv.className = 'validation-message warning';
        expiryDateInput.classList.add('validation-warning');
        console.log('⚠️ No return date set');
        return;
    }
    
    // Parse dates
    const expiry = new Date(expiryDate + 'T00:00:00');
    const ret = new Date(returnDate + 'T00:00:00');
    
    if (isNaN(expiry.getTime()) || isNaN(ret.getTime())) {
        validationDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Invalid date format`;
        validationDiv.className = 'validation-message warning';
        expiryDateInput.classList.add('validation-warning');
        console.warn('⚠️ Invalid date format');
        return;
    }
    
    // Calculate 6 months after return date
    const minExpiry = new Date(ret);
    minExpiry.setMonth(minExpiry.getMonth() + 6);
    
    // Calculate days
    const today = new Date();
    const daysUntilExpiry = Math.ceil((expiry - today) / (1000 * 60 * 60 * 24));
    const daysUntilMinExpiry = Math.ceil((expiry - minExpiry) / (1000 * 60 * 60 * 24));
    
    console.log(`📅 Expiry: ${expiryDate}, Return: ${returnDate}, Min Expiry: ${minExpiry.toISOString().slice(0,10)}`);
    
    if (expiry < minExpiry) {
        validationDiv.innerHTML = `
            <i class="fas fa-times-circle"></i> 
            Passport expires on ${expiryDate}. Must be valid for at least 6 months after expected return date.
            <br><strong>Minimum expiry date: ${minExpiry.toISOString().slice(0, 10)}</strong>
            (${Math.abs(daysUntilMinExpiry)} days short)
        `;
        validationDiv.className = 'validation-message invalid';
        expiryDateInput.classList.add('validation-invalid');
        expiryDateInput.setCustomValidity('Passport must be valid for 6 months after expected return date');
    } else if (daysUntilExpiry < 180) {
        validationDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i> 
            Passport expires in ${daysUntilExpiry} days. Less than 6 months remaining.
            <br>Recommended: Renew passport before travel.
        `;
        validationDiv.className = 'validation-message warning';
        expiryDateInput.classList.add('validation-warning');
        expiryDateInput.setCustomValidity('');
    } else {
        validationDiv.innerHTML = `
            <i class="fas fa-check-circle"></i> 
            Passport is valid. Expires in ${daysUntilExpiry} days.
            <br>Remains valid for ${daysUntilMinExpiry} days after expected return.
        `;
        validationDiv.className = 'validation-message valid';
        expiryDateInput.classList.add('validation-valid');
        expiryDateInput.setCustomValidity('');
    }
}

// ============================================================
// SESSION MANAGEMENT
// ============================================================
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
    const message = document.getElementById('sessionWarningMessage');
    if (!warning || !message) return;
    message.textContent = 'Your session will expire in 2 minutes. Click to extend.';
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
// NOTIFICATION FUNCTION
// ============================================================
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    if (!notification) return;
    const icon = type === 'success' ? 'check-circle' :
        type === 'error' ? 'exclamation-circle' :
        type === 'warning' ? 'exclamation-triangle' : 'info-circle';
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `<i class="fas fa-${icon}"></i> ${message}`;
    notification.style.display = 'block';
    if (notificationTimeout) clearTimeout(notificationTimeout);
    notificationTimeout = setTimeout(() => { notification.style.display = 'none'; }, 3000);
}

// ============================================================
// LOGOUT FUNCTION
// ============================================================
async function logout() {
    if (confirm('Are you sure you want to logout?')) {
        if (typeof SessionManager !== 'undefined' && SessionManager.logout) {
            await SessionManager.logout();
        } else {
            window.location.href = '/admin/login.html';
        }
    }
}

// ============================================================
// FILE HANDLING - SELECT & PREVIEW
// ============================================================
function handleFileSelect(input, textElementId, previewElementId) {
    const textElement = document.getElementById(textElementId);
    const previewElement = document.getElementById(previewElementId);

    if (input.files && input.files[0]) {
        const file = input.files[0];
        textElement.textContent = file.name;

        const reader = new FileReader();
        reader.onload = function(e) {
            let previewHtml = `
                <div class="file-info">
                    <i class="fas fa-${file.type.includes('pdf') ? 'file-pdf' : 'file-image'}"></i>
                    <span>${file.name} (${(file.size / 1024).toFixed(2)} KB)</span>
                </div>
                <div class="file-actions">
                    <button onclick="previewNewDocument('${e.target.result}', '${file.name}', '${file.type}')" title="Preview">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button onclick="removeNewDocument('${input.id}', '${textElementId}', '${previewElementId}')" class="delete" title="Remove">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            previewElement.innerHTML = previewHtml;
            previewElement.style.display = 'flex';
        };
        reader.readAsDataURL(file);
    } else {
        textElement.textContent = textElementId.includes('edit') ? 'Click to update' : 'Click to upload';
        previewElement.style.display = 'none';
    }
}

function previewNewDocument(dataUrl, fileName, fileType) {
    currentDocument = { data: dataUrl, name: fileName, type: fileType };
    currentDocumentName = fileName;
    const titleEl = document.getElementById('documentViewerTitle');
    const contentEl = document.getElementById('documentViewerContent');
    titleEl.textContent = fileName;
    if (fileType.includes('pdf')) {
        contentEl.innerHTML = `<iframe src="${dataUrl}" style="width:100%;height:500px;border:none;"></iframe>`;
    } else if (fileType.includes('image')) {
        contentEl.innerHTML = `<img src="${dataUrl}" alt="${fileName}" style="max-width:100%;max-height:500px;">`;
    } else {
        contentEl.innerHTML = `<p>Cannot preview this file type. Click Download to view.</p>`;
    }
    document.getElementById('documentViewerModal').style.display = 'block';
    document.getElementById('modalOverlay').style.display = 'block';
}

function removeNewDocument(inputId, textElementId, previewElementId) {
    const input = document.getElementById(inputId);
    input.value = '';
    document.getElementById(textElementId).textContent = textElementId.includes('edit') ? 'Click to update' : 'Click to upload';
    document.getElementById(previewElementId).style.display = 'none';
    showNotification('Document removed', 'success');
}

function closeDocumentViewer() {
    document.getElementById('documentViewerModal').style.display = 'none';
    document.getElementById('modalOverlay').style.display = 'none';
    currentDocument = null;
}

// ============================================================
// VIEW UPLOADED DOCUMENT
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

// ============================================================
// SHOW EXISTING DOCUMENT PREVIEW
// ============================================================
function showExistingDocumentPreview(previewElementId, filename, docType) {
    if (!filename) return;
    const previewElement = document.getElementById(previewElementId);
    if (!previewElement) return;

    const subfolderMap = {
        'passport': 'passports',
        'aadhaar': 'aadhaar',
        'pan': 'pan',
        'vaccine': 'vaccine',
        'photo': 'photos'
    };
    const subfolder = subfolderMap[docType] || 'documents';
    const viewUrl = `/uploads/${subfolder}/${filename}`;

    const previewHtml = `
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

    previewElement.innerHTML = previewHtml;
    previewElement.style.display = 'flex';

    const textElementId = previewElementId.replace('_preview', '_text');
    const textElement = document.getElementById(textElementId);
    if (textElement) {
        textElement.textContent = filename;
    }
}

// ============================================================
// AUTO-FILL PASSPORT NAME
// ============================================================
function setupPassportNameAutoFill() {
    const addFirst = document.getElementById('add_first_name');
    const addLast = document.getElementById('add_last_name');
    const addPassport = document.getElementById('add_passport_name');
    if (addFirst && addLast && addPassport) {
        const updateAddPassport = () => {
            addPassport.value = `${addFirst.value || ''} ${addLast.value || ''}`.trim();
        };
        addFirst.addEventListener('input', updateAddPassport);
        addLast.addEventListener('input', updateAddPassport);
    }

    const editFirst = document.getElementById('edit_first_name');
    const editLast = document.getElementById('edit_last_name');
    const editPassport = document.getElementById('edit_passport_name');
    if (editFirst && editLast && editPassport) {
        const updateEditPassport = () => {
            editPassport.value = `${editFirst.value || ''} ${editLast.value || ''}`.trim();
        };
        editFirst.addEventListener('input', updateEditPassport);
        editLast.addEventListener('input', updateEditPassport);
    }
}

// ============================================================
// TOGGLE MAILING ADDRESS
// ============================================================
function setupMailingAddressToggle() {
    ['add', 'edit'].forEach(prefix => {
        const cb = document.getElementById(prefix + '_same_mailing');
        if (cb) {
            cb.addEventListener('change', function() {
                toggleMailingAddress(prefix);
            });
        }
    });
}

function toggleMailingAddress(prefix) {
    const cb = document.getElementById(prefix + '_same_mailing');
    const passportAddr = document.getElementById(prefix + '_passport_address');
    const mailingEl = document.getElementById(prefix + '_mailing_address');
    
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
// DATE VALIDATION SETUP
// ============================================================
function setupDateValidation() {
    ['add', 'edit'].forEach(prefix => {
        const expiryEl = document.getElementById(prefix + '_passport_expiry_date');
        if (expiryEl) {
            expiryEl.addEventListener('change', function() {
                validatePassportExpiry(prefix);
            });
            expiryEl.addEventListener('input', function() {
                validatePassportExpiry(prefix);
            });
        }
    });
}

// ============================================================
// LOAD BATCHES
// ============================================================
async function loadBatches() {
    try {
        console.log('🔄 Loading batches...');
        const response = await fetch('/api/batches', { 
            credentials: 'include',
            headers: {
                'Accept': 'application/json'
            }
        });
        const data = await response.json();
        console.log('📦 Batches API response:', data);
        
        if (data.success && data.batches && data.batches.length > 0) {
            batchesData = data.batches;
            console.log(`✅ Loaded ${batchesData.length} batches from API`);
        } else {
            console.warn('⚠️ No batches found in API response, using fallback');
            useFallbackBatches();
        }
    } catch (error) {
        console.error('❌ Error loading batches:', error);
        useFallbackBatches();
    }
    updateBatchDropdowns(batchesData);
}

function useFallbackBatches() {
    batchesData = [
        { 
            id: 1, 
            batch_name: 'Haj Platinum 2026', 
            return_date: '2026-07-15' 
        },
        { 
            id: 2, 
            batch_name: 'Haj Gold 2026', 
            return_date: '2026-07-20' 
        },
        { 
            id: 3, 
            batch_name: 'Umrah Ramadhan Special', 
            return_date: '2026-03-25' 
        },
        { 
            id: 4, 
            batch_name: 'Golden Short Term package_ Haj 2027', 
            return_date: '2027-07-15' 
        }
    ];
    console.log('📦 Using fallback batches:', batchesData);
}

function updateBatchDropdowns(batches) {
    console.log('🔄 Updating batch dropdowns with', batches.length, 'batches');
    
    ['add', 'edit'].forEach(prefix => {
        const select = document.getElementById(prefix + '_batch_id');
        if (!select) {
            console.warn(`⚠️ Batch select not found: ${prefix}_batch_id`);
            return;
        }
        
        const currentValue = select.value;
        select.innerHTML = '<option value="">Select Batch</option>';
        
        batches.forEach(b => {
            const option = document.createElement('option');
            option.value = b.id;
            const returnDate = b.return_date || b.returnDate || b.expected_return_date || b.expectedReturnDate || b.batch_return_date || b.return_dt;
            const returnInfo = returnDate ? ` (Return: ${returnDate})` : ' (No return date set)';
            option.textContent = (b.batch_name || b.name || 'Batch ' + b.id) + returnInfo;
            // Store return date as data attribute
            if (returnDate) {
                option.dataset.returnDate = returnDate;
            }
            select.appendChild(option);
        });
        
        // Restore selection if possible
        if (currentValue) {
            select.value = currentValue;
            // Trigger onBatchSelect to populate return date
            setTimeout(() => {
                onBatchSelect(prefix);
            }, 100);
        }
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
        const response = await fetch('/api/travelers', { 
            credentials: 'include',
            headers: {
                'Accept': 'application/json'
            }
        });
        const data = await response.json();
        console.log('📋 Travelers API response:', data);
        
        if (data.success && data.travelers) {
            travelersData = data.travelers;
            console.log(`✅ Loaded ${travelersData.length} travelers`);
        } else {
            console.warn('⚠️ No travelers found, using fallback');
            travelersData = getFallbackTravelers();
        }
    } catch (error) {
        console.error('❌ Error loading travelers:', error);
        travelersData = getFallbackTravelers();
    }
    
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

let filteredTravelers = [];

// ============================================================
// UPDATE STATS
// ============================================================
function updateStats() {
    const total = travelersData.length;
    const active = travelersData.filter(t => t.passport_status === 'Active').length;
    const vaccinated = travelersData.filter(t => t.vaccine_status === 'Fully Vaccinated').length;
    const docsComplete = travelersData.filter(t => t.passport_scan && t.aadhaar_scan && t.pan_scan && t.photo).length;
    
    const totalEl = document.getElementById('totalTravelersCount');
    const activeEl = document.getElementById('activeTravelersCount');
    const vaccinatedEl = document.getElementById('vaccinatedCount');
    const docsCompleteEl = document.getElementById('documentsComplete');
    
    if (totalEl) totalEl.textContent = total;
    if (activeEl) activeEl.textContent = active;
    if (vaccinatedEl) vaccinatedEl.textContent = vaccinated;
    if (docsCompleteEl) docsCompleteEl.textContent = docsComplete;
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
// PAGINATION
// ============================================================
function updatePaginationInfo(total) {
    const totalEl = document.getElementById('totalCount');
    const fromEl = document.getElementById('showingFrom');
    const toEl = document.getElementById('showingTo');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    
    if (totalEl) totalEl.textContent = total;
    const start = total > 0 ? (currentPage - 1) * ITEMS_PER_PAGE + 1 : 0;
    const end = Math.min(currentPage * ITEMS_PER_PAGE, total);
    if (fromEl) fromEl.textContent = start;
    if (toEl) toEl.textContent = end;
    
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
    const form = document.getElementById('addTravelerForm');
    if (form) {
        form.style.display = 'block';
        loadBatches();
        form.scrollIntoView({ behavior: 'smooth' });
    }
}

function hideAddTravelerForm() {
    const form = document.getElementById('addTravelerForm');
    if (form) form.style.display = 'none';
    const formEl = document.getElementById('travelerAddForm');
    if (formEl) formEl.reset();
    resetDocumentPreviews('add');
    
    // Reset validation
    const validationDiv = document.getElementById('add_passport_validation');
    if (validationDiv) {
        validationDiv.textContent = '';
        validationDiv.className = 'validation-message';
    }
    const expiryInput = document.getElementById('add_passport_expiry_date');
    if (expiryInput) expiryInput.className = '';
    const returnDateInput = document.getElementById('add_expected_return_date');
    if (returnDateInput) {
        returnDateInput.value = '';
        returnDateInput.style.borderColor = '';
        returnDateInput.style.background = '';
    }
    const returnInfoDiv = document.getElementById('add_batch_return_info');
    if (returnInfoDiv) returnInfoDiv.classList.remove('show');
    const returnInfoMsg = document.getElementById('add_expected_return_info');
    if (returnInfoMsg) {
        returnInfoMsg.innerHTML = '';
        returnInfoMsg.className = 'expected-return-info';
    }
}

function hideEditTravelerForm() {
    const form = document.getElementById('editTravelerForm');
    if (form) form.style.display = 'none';
    currentEditId = null;
    resetDocumentPreviews('edit');
    
    // Reset validation
    const validationDiv = document.getElementById('edit_passport_validation');
    if (validationDiv) {
        validationDiv.textContent = '';
        validationDiv.className = 'validation-message';
    }
    const expiryInput = document.getElementById('edit_passport_expiry_date');
    if (expiryInput) expiryInput.className = '';
    const returnInfoMsg = document.getElementById('edit_expected_return_info');
    if (returnInfoMsg) {
        returnInfoMsg.innerHTML = '';
        returnInfoMsg.className = 'expected-return-info';
    }
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
        'edit_gender': traveler.gender || '',
        'edit_dob': formatDateForInput(traveler.dob),
        'edit_batch_id': traveler.batch_id,
        'edit_passport_no': traveler.passport_no,
        'edit_passport_issue_date': formatDateForInput(traveler.passport_issue_date),
        'edit_passport_expiry_date': formatDateForInput(traveler.passport_expiry_date),
        'edit_passport_status': traveler.passport_status || 'Active',
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
    
    // Auto-populate return date from batch
    if (traveler.batch_id) {
        setTimeout(() => {
            onBatchSelect('edit');
        }, 300);
    }
    
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
            <div class="detail-item"><strong>Gender:</strong> <span>${formatValue(t.gender)}</span></div>
            <div class="detail-item"><strong>Date of Birth:</strong> <span>${formatDate(t.dob)}</span></div>
            <div class="detail-item"><strong>Batch:</strong> <span>${formatValue(t.batch_name)}</span></div>
            <div class="detail-item"><strong>Passport Number:</strong> <span>${formatValue(t.passport_no)}</span></div>
            <div class="detail-item"><strong>Passport Issue Date:</strong> <span>${formatDate(t.passport_issue_date)}</span></div>
            <div class="detail-item"><strong>Passport Expiry Date:</strong> <span>${formatDate(t.passport_expiry_date)}</span></div>
            <div class="detail-item"><strong>Passport Status:</strong> <span class="status-badge status-active">${formatValue(t.passport_status)}</span></div>
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
        'ID', 'First Name', 'Last Name', 'Passport Name', 'Gender', 'Date of Birth',
        'Batch ID', 'Batch Name', 'Passport Number', 'Passport Issue Date', 'Passport Expiry Date',
        'Passport Status', 'Mobile', 'Email', 'Aadhaar', 'PAN', 'Aadhaar-PAN Linked',
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
            t.gender || '', t.dob || '',
            t.batch_id || '', t.batch_name || '', t.passport_no || '',
            t.passport_issue_date || '', t.passport_expiry_date || '', t.passport_status || '',
            t.mobile || '', t.email || '',
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
    const section = document.getElementById('csvUploadSection');
    if (section) {
        section.style.display = 'block';
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

function hideCSVUploadSection() {
    const section = document.getElementById('csvUploadSection');
    if (section) section.style.display = 'none';
    const input = document.getElementById('csvFileInput');
    if (input) input.value = '';
    const preview = document.getElementById('csvPreview');
    if (preview) preview.style.display = 'none';
}

function downloadCSVTemplate() {
    const headers = [
        'first_name', 'last_name', 'passport_name', 'gender', 'dob', 'batch_id',
        'passport_no', 'passport_issue_date', 'passport_expiry_date', 'passport_status',
        'mobile', 'email', 'aadhaar', 'pan', 'aadhaar_pan_linked',
        'vaccine_status', 'wheelchair', 'place_of_birth', 'place_of_issue', 'passport_address',
        'mailing_address', 'father_name', 'mother_name', 'spouse_name',
        'expected_return_date', 'file_reference',
        'pin', 'emergency_contact', 'emergency_phone', 'medical_notes'
    ];
    
    const sample = [
        'John', 'Doe', 'John Doe', 'Male', '1990-01-01', '1',
        'A0000001', '2020-01-01', '2030-01-01', 'Active',
        '9000000000', 'john@example.com', '000000000000', 'AAAAA0000A', 'No',
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
    link.download = 'travelers_template_36_fields.csv';
    link.click();
    showNotification('CSV template downloaded', 'success');
}

async function uploadCSV() {
    const fileInput = document.getElementById('csvFileInput');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
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
// UI HELPERS
// ============================================================
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
    btn.textContent = btn.textContent.replace('Loading...', 'Save Traveler (36 Fields)');
    btn.textContent = btn.textContent.replace('Updating...', 'Update Traveler');
    btn.textContent = btn.textContent.replace('Saving...', 'Save Traveler (36 Fields)');
}

console.log('✅ travelers.js loaded successfully with batch auto-population!');
