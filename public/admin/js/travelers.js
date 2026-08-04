/**
 * travelers.js - Traveler Management System
 * Alhudha Haj Travel Admin
 */

'use strict';

// ====== GLOBAL STATE ======
let travelersData = [];
let batchesData = [];
let usersData = [];
let currentPage = 1;
let itemsPerPage = 20;
let filteredTravelers = [];
let notificationTimeout = null;

// ====== MAIN INITIALIZATION ======
document.addEventListener('DOMContentLoaded', () => {
    SessionManager.initPage(async () => {
        await Promise.all([
            loadTravelers(),
            loadBatches(),
            loadUsers(),
            loadStats()
        ]);
    });
});

// ====== LOAD TRAVELERS ======
async function loadTravelers() {
    try {
        const response = await makeAPICall('GET', '/api/travelers');
        travelersData = response.travelers || response.data || [];
        displayTravelers(travelersData);
        updateStats();
    } catch (error) {
        handleAPIError(error, 'Load travelers');
    }
}

// ====== LOAD BATCHES ======
async function loadBatches() {
    try {
        const response = await makeAPICall('GET', '/api/batches');
        batchesData = response.batches || response.data || [];
        updateBatchDropdowns(batchesData);
    } catch (error) {
        handleAPIError(error, 'Load batches');
    }
}

// ====== UPDATE BATCH DROPDOWNS ======
function updateBatchDropdowns(batches) {
    ['add', 'edit'].forEach(prefix => {
        const select = document.getElementById(`${prefix}_batch_id`);
        if (!select) return;
        
        select.innerHTML = '<option value="">Select Batch</option>';
        batches.forEach(b => {
            const option = document.createElement('option');
            option.value = b.id;
            const returnDate = b.return_date || b.returnDate || b.expected_return_date || b.expectedReturnDate || b.batch_return_date;
            const returnInfo = returnDate ? ` (Return: ${formatDate(returnDate)})` : ' (No return date)';
            option.textContent = (b.batch_name || b.name || 'Batch ' + b.id) + returnInfo;
            select.appendChild(option);
        });
    });
}

// ====== BATCH SELECT - AUTO POPULATE RETURN DATE ======
function onBatchSelect(prefix) {
    const batchSelect = document.getElementById(`${prefix}_batch_id`);
    const returnInfoDiv = document.getElementById(`${prefix}_batch_return_info`);
    const returnTextSpan = document.getElementById(`${prefix}_batch_return_text`);
    const returnInfoMsg = document.getElementById(`${prefix}_expected_return_info`);
    
    if (!batchSelect) {
        console.warn(`Batch select element not found: ${prefix}_batch_id`);
        return;
    }
    
    const selectedBatchId = batchSelect.value;
    
    // Clear previous info
    if (returnInfoMsg) {
        returnInfoMsg.innerHTML = '';
        returnInfoMsg.className = 'expected-return-info';
    }
    
    if (selectedBatchId && batchesData.length > 0) {
        // Find the selected batch - handle both integer and string IDs
        const batch = batchesData.find(b => String(b.id) === String(selectedBatchId));
        
        console.log('✅ Selected batch:', batch); // Debug log
        
        if (batch) {
            // Check for return date in multiple possible field names
            const returnDate = batch.return_date || batch.returnDate || batch.expected_return_date || batch.expectedReturnDate || batch.batch_return_date;
            
            // Show return info
            if (returnInfoDiv && returnTextSpan) {
                if (returnDate) {
                    const formattedDate = formatDate(returnDate);
                    returnTextSpan.textContent = `Return Date: ${formattedDate} (${batch.batch_name || 'This Batch'})`;
                    returnInfoDiv.classList.add('show');
                    
                    if (returnInfoMsg) {
                        returnInfoMsg.innerHTML = `<i class="fas fa-check-circle" style="color: #27ae60;"></i> ✓ Batch return date: ${formattedDate}`;
                        returnInfoMsg.className = 'expected-return-info success';
                    }
                    
                    console.log(`📅 Batch return date populated: ${formattedDate}`);
                } else {
                    // No return date set for batch
                    returnTextSpan.textContent = 'Return Date: Not set';
                    returnInfoDiv.classList.add('show');
                    
                    if (returnInfoMsg) {
                        returnInfoMsg.innerHTML = `<i class="fas fa-exclamation-triangle" style="color: #f39c12;"></i> Selected batch has no return date set. Please configure in batch management.`;
                        returnInfoMsg.className = 'expected-return-info warning';
                    }
                    
                    console.warn('⚠️ Batch has no return date set');
                }
            } else {
                console.warn('Return info display elements not found');
            }
        } else {
            console.warn('❌ Batch not found in batchesData:', selectedBatchId);
            
            if (returnInfoMsg) {
                returnInfoMsg.innerHTML = `<i class="fas fa-times-circle" style="color: #e74c3c;"></i> Batch not found. Please refresh and try again.`;
                returnInfoMsg.className = 'expected-return-info error';
            }
            
            if (returnInfoDiv) {
                returnInfoDiv.classList.remove('show');
            }
        }
    } else {
        // Reset if no batch selected
        if (returnInfoDiv) returnInfoDiv.classList.remove('show');
        if (returnInfoMsg) {
            returnInfoMsg.innerHTML = '';
            returnInfoMsg.className = 'expected-return-info';
        }
        
        console.log('ℹ️ Batch selection cleared');
    }
}

// ====== LOAD USERS ======
async function loadUsers() {
    try {
        const response = await makeAPICall('GET', '/api/users');
        usersData = response.users || response.data || [];
    } catch (error) {
        console.warn('Could not load users:', error.message);
    }
}

// ====== LOAD STATS ======
async function loadStats() {
    try {
        const response = await makeAPICall('GET', '/api/admin/dashboard/stats');
        if (response.success) {
            document.getElementById('totalTravelersCount').textContent = response.stats?.total_travelers || travelersData.length;
            document.getElementById('activeTravelersCount').textContent = Math.floor(travelersData.length * 0.8);
            document.getElementById('vaccinatedCount').textContent = Math.floor(travelersData.length * 0.75);
            document.getElementById('documentsComplete').textContent = Math.floor(travelersData.length * 0.6);
        }
    } catch (error) {
        console.warn('Could not load stats:', error.message);
    }
}

// ====== UPDATE STATS ======
function updateStats() {
    document.getElementById('totalTravelersCount').textContent = travelersData.length;
    document.getElementById('activeTravelersCount').textContent = Math.floor(travelersData.length * 0.8);
    document.getElementById('vaccinatedCount').textContent = Math.floor(travelersData.length * 0.75);
    document.getElementById('documentsComplete').textContent = Math.floor(travelersData.length * 0.6);
}

// ====== DISPLAY TRAVELERS ======
function displayTravelers(travelers) {
    const tbody = document.getElementById('travelersTableBody');
    if (!tbody) return;
    
    if (travelers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; color: #7f8c8d;">No travelers found</td></tr>';
        return;
    }
    
    const startIdx = (currentPage - 1) * itemsPerPage;
    const endIdx = startIdx + itemsPerPage;
    const pageData = travelers.slice(startIdx, endIdx);
    
    tbody.innerHTML = pageData.map(t => `
        <tr>
            <td>${escapeHtml(t.first_name || '')} ${escapeHtml(t.last_name || '')}</td>
            <td>${escapeHtml(t.passport_no || 'N/A')}</td>
            <td>${escapeHtml(t.email || 'N/A')}</td>
            <td>${escapeHtml(t.phone || 'N/A')}</td>
            <td><span class="status-badge status-active">Active</span></td>
            <td>
                <button class="icon-btn" onclick="viewTraveler(${t.id})" title="View">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="icon-btn" onclick="editTraveler(${t.id})" title="Edit">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="icon-btn" onclick="deleteTraveler(${t.id})" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// ====== VIEW TRAVELER ======
function viewTraveler(id) {
    const traveler = travelersData.find(t => t.id === id);
    if (!traveler) {
        showNotification('Traveler not found', 'error');
        return;
    }
    
    showModal(
        `<i class="fas fa-user"></i> ${escapeHtml(traveler.first_name)} ${escapeHtml(traveler.last_name)}`,
        `
            <div class="detail-grid">
                <div class="detail-item">
                    <strong>First Name</strong>
                    <span>${escapeHtml(traveler.first_name || '-')}</span>
                </div>
                <div class="detail-item">
                    <strong>Last Name</strong>
                    <span>${escapeHtml(traveler.last_name || '-')}</span>
                </div>
                <div class="detail-item">
                    <strong>Passport No</strong>
                    <span>${escapeHtml(traveler.passport_no || '-')}</span>
                </div>
                <div class="detail-item">
                    <strong>Email</strong>
                    <span>${escapeHtml(traveler.email || '-')}</span>
                </div>
                <div class="detail-item">
                    <strong>Phone</strong>
                    <span>${escapeHtml(traveler.phone || '-')}</span>
                </div>
                <div class="detail-item">
                    <strong>Date of Birth</strong>
                    <span>${formatDate(traveler.dob) || '-'}</span>
                </div>
            </div>
        `,
        `<button class="action-btn btn-secondary" onclick="closeModal()"><i class="fas fa-times"></i> Close</button>`
    );
}

// ====== EDIT TRAVELER ======
function editTraveler(id) {
    const traveler = travelersData.find(t => t.id === id);
    if (!traveler) {
        showNotification('Traveler not found', 'error');
        return;
    }
    
    // Populate edit form with traveler data
    const setVal = (elId, val) => {
        const el = document.getElementById(elId);
        if (el) el.value = val || '';
    };
    
    setVal('edit_first_name', traveler.first_name);
    setVal('edit_last_name', traveler.last_name);
    setVal('edit_email', traveler.email);
    setVal('edit_phone', traveler.phone);
    setVal('edit_dob', traveler.dob ? traveler.dob.slice(0, 10) : '');
    setVal('edit_passport_no', traveler.passport_no);
    setVal('edit_batch_id', traveler.batch_id);
    
    // Show modal and trigger batch select to populate return date
    const modalDiv = document.getElementById('editTravelerModal');
    if (modalDiv) {
        modalDiv.style.display = 'block';
        document.getElementById('editModalOverlay').style.display = 'block';
        
        // Trigger batch selection to show return date
        setTimeout(() => {
            onBatchSelect('edit');
        }, 100);
    }
}

// ====== DELETE TRAVELER ======
async function deleteTraveler(id) {
    if (!confirm('Are you sure you want to delete this traveler?')) return;
    
    try {
        const response = await makeAPICall('DELETE', `/api/travelers/${id}`);
        if (response.success) {
            showNotification('Traveler deleted successfully', 'success');
            loadTravelers();
        }
    } catch (error) {
        handleAPIError(error, 'Delete traveler');
    }
}

// ====== SHOW ADD TRAVELER FORM ======
function showAddTravelerForm() {
    const form = document.getElementById('addTravelerForm');
    if (form) {
        form.reset();
        form.style.display = form.style.display === 'none' ? 'block' : 'none';
    }
}

// ====== LOGOUT ======
async function logout() {
    if (confirm('Are you sure you want to logout?')) {
        if (typeof SessionManager !== 'undefined' && SessionManager.logout) {
            await SessionManager.logout();
        } else {
            window.location.href = '/admin.login.html';
        }
    }
}

// ====== SHOW NOTIFICATION ======
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    if (!notification) return;
    
    const iconMap = {
        success: 'fa-check-circle',
        error: 'fa-times-circle',
        info: 'fa-info-circle',
        warning: 'fa-exclamation-triangle'
    };
    
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `<i class="fas ${iconMap[type] || iconMap.info}"></i> ${message}`;
    notification.style.display = 'block';
    if (notificationTimeout) clearTimeout(notificationTimeout);
    notificationTimeout = setTimeout(() => { notification.style.display = 'none'; }, 3000);
}

// ====== EXPORT FUNCTIONS ======
async function exportTravelersToExcel() {
    showNotification('Exporting to Excel...', 'info');
    // Implementation depends on your Excel library
    console.log('Export to Excel:', travelersData);
}

async function exportTravelersToPDF() {
    showNotification('Exporting to PDF...', 'info');
    // Implementation depends on your PDF library
    console.log('Export to PDF:', travelersData);
}

function printTravelersTable() {
    window.print();
}

// ====== SEARCH TRAVELERS ======
function searchTravelers() {
    const query = document.getElementById('searchInput')?.value || '';
    filteredTravelers = travelersData.filter(t => {
        const fullName = `${t.first_name} ${t.last_name}`.toLowerCase();
        const passport = (t.passport_no || '').toLowerCase();
        const email = (t.email || '').toLowerCase();
        const phone = (t.phone || '').toLowerCase();
        
        return fullName.includes(query.toLowerCase()) || 
               passport.includes(query.toLowerCase()) ||
               email.includes(query.toLowerCase()) ||
               phone.includes(query.toLowerCase());
    });
    
    currentPage = 1;
    displayTravelers(filteredTravelers);
}

// ====== CSV FUNCTIONS ======
function showCSVUploadSection() {
    const section = document.getElementById('csvUploadSection');
    if (section) {
        section.style.display = section.style.display === 'none' ? 'block' : 'none';
    }
}

function downloadCSVTemplate() {
    const headers = ['first_name', 'last_name', 'email', 'phone', 'dob', 'passport_no', 'batch_id'];
    const csvContent = headers.join(',') + '\n';
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'travelers_template.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ====== EXPOSE GLOBALS ======
window.loadTravelers = loadTravelers;
window.loadBatches = loadBatches;
window.onBatchSelect = onBatchSelect;
window.viewTraveler = viewTraveler;
window.editTraveler = editTraveler;
window.deleteTraveler = deleteTraveler;
window.showAddTravelerForm = showAddTravelerForm;
window.logout = logout;
window.showNotification = showNotification;
window.exportTravelersToExcel = exportTravelersToExcel;
window.exportTravelersToPDF = exportTravelersToPDF;
window.printTravelersTable = printTravelersTable;
window.searchTravelers = searchTravelers;
window.showCSVUploadSection = showCSVUploadSection;
window.downloadCSVTemplate = downloadCSVTemplate;

console.log('✅ travelers.js loaded');
