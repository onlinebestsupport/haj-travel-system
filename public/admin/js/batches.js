/**
 * batches.js - Batch Management for Alhudha Haj Travel Admin
 * Handles CRUD operations for Haj/Umrah batches/packages
 * Depends on: common.js, session-manager.js
 * API base: /api/batches
 */

'use strict';

// ====== STATE ======
let batchesData = [];
let filteredBatchesData = [];
let batchesCurrentPage = 1;
const BATCHES_PER_PAGE = 10;
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
        const response = await fetch('/api/batches', {
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
            if (response.status === 401) {
                showNotification('Session expired. Please login again', 'error');
                setTimeout(() => {
                    window.location.href = '/admin/login.html';
                }, 2000);
                return;
            }
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        
        if (data.success && Array.isArray(data.batches)) {
            batchesData = data.batches;
            filteredBatchesData = [...batchesData];
            console.log(`✅ Loaded ${batchesData.length} batches`);
        } else {
            console.warn('⚠️ No batches found in API response, using demo data');
            useDemoBatches();
        }
    } catch (error) {
        console.error('Error loading batches:', error);
        useDemoBatches();
    }

    updateBatchStatistics();
    displayBatches();
    updateBatchDropdowns();
}

/**
 * Use demo batch data when API is unavailable
 */
function useDemoBatches() {
    batchesData = [
        { 
            id: 1, 
            batch_name: 'Haj Platinum 2026', 
            departure_date: '2026-06-14', 
            return_date: '2026-07-31', 
            price: 850000, 
            total_seats: 50, 
            booked_seats: 45, 
            status: 'Open',
            description: 'Luxury Haj package with 5-star accommodation in Mina and Arafat.'
        },
        { 
            id: 2, 
            batch_name: 'Haj Gold 2026', 
            departure_date: '2026-06-15', 
            return_date: '2026-07-30', 
            price: 550000, 
            total_seats: 100, 
            booked_seats: 82, 
            status: 'Open',
            description: 'Standard Haj package with 4-star accommodation.'
        },
        { 
            id: 3, 
            batch_name: 'Umrah Ramadhan Special', 
            departure_date: '2026-03-01', 
            return_date: '2026-03-20', 
            price: 125000, 
            total_seats: 200, 
            booked_seats: 170, 
            status: 'Closing Soon',
            description: 'Umrah package during the last 10 days of Ramadhan.'
        },
        { 
            id: 4, 
            batch_name: 'Golden Short Term package_ Haj 2027', 
            departure_date: '2027-06-20', 
            return_date: '2027-07-15', 
            price: 950000, 
            total_seats: 30, 
            booked_seats: 12, 
            status: 'Open',
            description: 'Premium short term Haj package with exclusive services.'
        }
    ];
    filteredBatchesData = [...batchesData];
}

// ====== DISPLAY BATCHES ======
/**
 * Render the batches table with status badges and pagination
 */
function displayBatches() {
    const tableBody = document.getElementById('batchesTableBody');
    if (!tableBody) return;

    if (!filteredBatchesData || filteredBatchesData.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="11" style="text-align:center;padding:40px;">No batches found</td></tr>';
        updatePaginationDisplay(0);
        return;
    }

    const start = (batchesCurrentPage - 1) * BATCHES_PER_PAGE;
    const end = Math.min(start + BATCHES_PER_PAGE, filteredBatchesData.length);
    const pageData = filteredBatchesData.slice(start, end);

    let html = '';
    pageData.forEach(b => {
        const price = b.price ? Number(b.price).toLocaleString('en-IN') : '0';
        const totalSeats = b.total_seats || 0;
        const bookedSeats = b.booked_seats || 0;
        const availableSeats = totalSeats - bookedSeats;
        const occupancyPercent = totalSeats > 0 ? Math.round((bookedSeats / totalSeats) * 100) : 0;
        const statusClass = getStatusClass(b.status);
        const occupancyColor = occupancyPercent >= 100 ? '#e74c3c' : occupancyPercent > 80 ? '#e67e22' : '#27ae60';
        
        // Show return date indicator
        const hasReturnDate = b.return_date ? 
            '<i class="fas fa-check-circle" style="color: #27ae60;" title="Has Return Date - Auto-populates for travelers"></i>' : 
            '<i class="fas fa-times-circle" style="color: #e74c3c;" title="No Return Date Set - Travelers cannot auto-populate"></i>';

        html += `<tr>
            <td>${b.id}</td>
            <td><strong>${escapeHtml(b.batch_name || '-')}</strong> ${hasReturnDate}</td>
            <td>${b.departure_date ? formatDate(b.departure_date) : '-'}</td>
            <td style="${b.return_date ? 'color: #27ae60; font-weight: bold;' : 'color: #e74c3c;'}">${b.return_date ? formatDate(b.return_date) : '⚠️ Not Set'}</td>
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
                <button class="icon-btn" onclick="viewBatchDetails(${b.id})" title="View Details"><i class="fas fa-eye"></i></button>
                <button class="icon-btn" onclick="editBatch(${b.id})" title="Edit"><i class="fas fa-edit"></i></button>
                <button class="icon-btn" onclick="deleteBatch(${b.id})" title="Delete"><i class="fas fa-trash"></i></button>
            </td>
        </tr>`;
    });

    tableBody.innerHTML = html;
    updatePaginationDisplay(filteredBatchesData.length);
}

/**
 * Get CSS class for status badge
 */
function getStatusClass(status) {
    if (!status) return 'status-active';
    const s = status.toLowerCase();
    if (s === 'open') return 'status-active';
    if (s === 'closing soon' || s === 'closing') return 'status-pending';
    if (s === 'full') return 'status-warning';
    if (s === 'closed') return 'status-inactive';
    return 'status-active';
}

/**
 * Update pagination display
 */
function updatePaginationDisplay(total) {
    const totalEl = document.getElementById('totalCount');
    const fromEl = document.getElementById('showingFrom');
    const toEl = document.getElementById('showingTo');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    if (totalEl) totalEl.textContent = total;
    const start = total > 0 ? (batchesCurrentPage - 1) * BATCHES_PER_PAGE + 1 : 0;
    const end = Math.min(batchesCurrentPage * BATCHES_PER_PAGE, total);
    if (fromEl) fromEl.textContent = start;
    if (toEl) toEl.textContent = end;

    if (prevBtn) prevBtn.disabled = batchesCurrentPage === 1;
    if (nextBtn) nextBtn.disabled = end >= total;
}

// ====== FILTER BATCHES ======
/**
 * Filter batches by search text
 */
function filterBatches() {
    const searchEl = document.getElementById('searchBatches');
    const search = searchEl ? searchEl.value.toLowerCase().trim() : '';

    if (!search) {
        filteredBatchesData = [...batchesData];
    } else {
        filteredBatchesData = batchesData.filter(b => {
            const name = (b.batch_name || '').toLowerCase();
            const status = (b.status || '').toLowerCase();
            const departure = (b.departure_date || '').toLowerCase();
            const returnDate = (b.return_date || '').toLowerCase();
            return name.includes(search) || status.includes(search) || 
                   departure.includes(search) || returnDate.includes(search);
        });
    }

    batchesCurrentPage = 1;
    displayBatches();
}

/**
 * Clear search and reset filter
 */
function clearSearch() {
    const searchEl = document.getElementById('searchBatches');
    if (searchEl) searchEl.value = '';
    filteredBatchesData = [...batchesData];
    batchesCurrentPage = 1;
    displayBatches();
}

// ====== PAGINATION ======
function previousPage() {
    if (batchesCurrentPage > 1) {
        batchesCurrentPage--;
        displayBatches();
    }
}

function nextPage() {
    if (batchesCurrentPage * BATCHES_PER_PAGE < filteredBatchesData.length) {
        batchesCurrentPage++;
        displayBatches();
    }
}

// ====== CREATE BATCH ======
/**
 * Create a new batch
 */
async function createBatch() {
    const priceRaw = document.getElementById('price')?.value?.replace(/,/g, '') || '';
    
    // Validate dates
    const departureDate = document.getElementById('departure_date')?.value;
    const returnDate = document.getElementById('return_date')?.value;
    
    if (departureDate && returnDate && returnDate < departureDate) {
        showNotification('Return date must be after departure date.', 'error');
        return;
    }

    const batchData = {
        batch_name: document.getElementById('batch_name')?.value?.trim(),
        total_seats: parseInt(document.getElementById('total_seats')?.value) || 150,
        price: priceRaw ? parseFloat(priceRaw) : null,
        departure_date: departureDate || null,
        return_date: returnDate || null,
        status: document.getElementById('status')?.value || 'Open',
        description: document.getElementById('description')?.value?.trim() || ''
    };

    if (!batchData.batch_name) {
        showNotification('Batch name is required', 'error');
        return;
    }

    const submitBtn = document.querySelector('#batchCreateForm button[type="submit"]');
    const originalText = submitBtn ? submitBtn.innerHTML : '';
    if (submitBtn) {
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
        submitBtn.disabled = true;
    }

    try {
        const response = await fetch('/api/batches', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(batchData)
        });

        if (response.status === 401) {
            showNotification('Session expired. Please login again', 'error');
            setTimeout(() => {
                window.location.href = '/admin/login.html';
            }, 2000);
            return;
        }

        const data = await response.json();

        if (data.success) {
            const returnMsg = batchData.return_date ? ` Return date: ${batchData.return_date}` : '';
            showNotification('Batch created successfully!' + returnMsg, 'success');
            if (typeof hideCreateBatchForm === 'function') hideCreateBatchForm();
            await loadBatches();
        } else {
            showNotification('Error: ' + (data.error || 'Could not create batch'), 'error');
        }
    } catch (error) {
        // Demo mode fallback
        console.warn('Using demo mode for create:', error);
        const newId = Math.max(...batchesData.map(b => b.id), 0) + 1;
        batchData.id = newId;
        batchData.booked_seats = 0;
        batchesData.push(batchData);
        filteredBatchesData = [...batchesData];
        showNotification('Batch created (demo mode) with return date: ' + (batchData.return_date || 'Not set'), 'success');
        if (typeof hideCreateBatchForm === 'function') hideCreateBatchForm();
        updateBatchStatistics();
        displayBatches();
        updateBatchDropdowns();
    } finally {
        if (submitBtn) {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }
}

// ====== EDIT BATCH ======
/**
 * Load batch data into the edit form
 */
function editBatch(id) {
    const batch = batchesData.find(b => b.id === id);
    if (!batch) {
        showNotification('Batch not found', 'error');
        return;
    }

    batchesCurrentEditId = id;

    const setField = (elId, val) => {
        const el = document.getElementById(elId);
        if (el) el.value = val || '';
    };

    setField('edit_batch_id', batch.id);
    setField('edit_batch_name', batch.batch_name);
    setField('edit_departure_date', batch.departure_date || '');
    setField('edit_return_date', batch.return_date || '');
    setField('edit_price', batch.price || '');
    setField('edit_total_seats', batch.total_seats || 150);
    setField('edit_status', batch.status || 'Open');

    // Show date validation info
    if (batch.return_date) {
        const validationDiv = document.getElementById('edit_date_validation');
        if (validationDiv) {
            validationDiv.innerHTML = '<i class="fas fa-info-circle"></i> Return date set. Will be used for traveler auto-population.';
            validationDiv.className = 'date-validation-info warning';
        }
    }

    const editForm = document.getElementById('editBatchForm');
    if (editForm) {
        editForm.style.display = 'block';
        editForm.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Hide edit batch form
 */
function hideEditBatchForm() {
    const editForm = document.getElementById('editBatchForm');
    if (editForm) editForm.style.display = 'none';
    batchesCurrentEditId = null;
    const validationDiv = document.getElementById('edit_date_validation');
    if (validationDiv) {
        validationDiv.innerHTML = '';
        validationDiv.className = 'date-validation-info';
    }
}

/**
 * Hide create batch form
 */
function hideCreateBatchForm() {
    const createForm = document.getElementById('createBatchForm');
    if (createForm) createForm.style.display = 'none';
    document.getElementById('batchCreateForm')?.reset();
    const validationDiv = document.getElementById('create_date_validation');
    if (validationDiv) {
        validationDiv.innerHTML = '';
        validationDiv.className = 'date-validation-info';
    }
}

/**
 * Show create batch form
 */
function showCreateBatchForm() {
    const createForm = document.getElementById('createBatchForm');
    if (createForm) {
        createForm.style.display = 'block';
        createForm.scrollIntoView({ behavior: 'smooth' });
    }
}

// ====== UPDATE BATCH ======
/**
 * Update an existing batch
 */
async function updateBatch() {
    if (!batchesCurrentEditId) {
        showNotification('No batch selected for editing', 'error');
        return;
    }

    const batchId = document.getElementById('edit_batch_id')?.value;
    const batchName = document.getElementById('edit_batch_name')?.value?.trim();
    
    if (!batchName) {
        showNotification('Batch name is required', 'error');
        return;
    }

    // Validate dates
    const departureDate = document.getElementById('edit_departure_date')?.value;
    const returnDate = document.getElementById('edit_return_date')?.value;
    
    if (departureDate && returnDate && returnDate < departureDate) {
        showNotification('Return date must be after departure date.', 'error');
        return;
    }

    const priceRaw = document.getElementById('edit_price')?.value?.replace(/,/g, '') || '';
    
    const batchData = {
        batch_name: batchName,
        departure_date: departureDate || null,
        return_date: returnDate || null,
        price: priceRaw ? parseFloat(priceRaw) : null,
        total_seats: parseInt(document.getElementById('edit_total_seats')?.value) || 150,
        status: document.getElementById('edit_status')?.value || 'Open'
    };

    const submitBtn = document.querySelector('#batchEditForm button[type="submit"]');
    const originalText = submitBtn ? submitBtn.innerHTML : '';
    if (submitBtn) {
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
        submitBtn.disabled = true;
    }

    try {
        const response = await fetch(`/api/batches/${batchId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(batchData)
        });

        if (response.status === 401) {
            showNotification('Session expired. Please login again', 'error');
            setTimeout(() => {
                window.location.href = '/admin/login.html';
            }, 2000);
            return;
        }

        const data = await response.json();

        if (data.success) {
            showNotification('Batch updated successfully! Return date updated for travelers.', 'success');
            if (typeof hideEditBatchForm === 'function') hideEditBatchForm();
            batchesCurrentEditId = null;
            await loadBatches();
        } else {
            showNotification('Error: ' + (data.error || 'Update failed'), 'error');
        }
    } catch (error) {
        // Demo mode fallback
        console.warn('Using demo mode for update:', error);
        const index = batchesData.findIndex(b => b.id === batchesCurrentEditId);
        if (index !== -1) {
            batchesData[index] = { ...batchesData[index], ...batchData };
            filteredBatchesData = [...batchesData];
            showNotification('Batch updated (demo mode) with return date: ' + (batchData.return_date || 'Not set'), 'success');
            if (typeof hideEditBatchForm === 'function') hideEditBatchForm();
            batchesCurrentEditId = null;
            updateBatchStatistics();
            displayBatches();
            updateBatchDropdowns();
        } else {
            showNotification('Error updating batch', 'error');
        }
    } finally {
        if (submitBtn) {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }
}

// ====== DELETE BATCH ======
/**
 * Delete a batch by ID
 */
async function deleteBatch(id) {
    const batch = batchesData.find(b => b.id === id);
    const name = batch ? batch.batch_name : `ID ${id}`;
    
    if (!confirm(`⚠️ Are you sure you want to delete batch "${name}"? This action cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/batches/${id}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (response.status === 401) {
            showNotification('Session expired. Please login again', 'error');
            setTimeout(() => {
                window.location.href = '/admin/login.html';
            }, 2000);
            return;
        }

        const data = await response.json();

        if (data.success) {
            showNotification('Batch deleted successfully!', 'success');
            await loadBatches();
        } else {
            showNotification('Error: ' + (data.error || 'Could not delete batch'), 'error');
        }
    } catch (error) {
        // Demo mode fallback
        console.warn('Using demo mode for delete:', error);
        batchesData = batchesData.filter(b => b.id !== id);
        filteredBatchesData = [...batchesData];
        showNotification('Batch deleted (demo mode)', 'success');
        updateBatchStatistics();
        displayBatches();
        updateBatchDropdowns();
    }
}

// ====== VIEW BATCH DETAILS ======
/**
 * Show a modal with full batch details
 */
function viewBatchDetails(id) {
    const b = batchesData.find(b => b.id === id);
    if (!b) {
        showNotification('Batch not found', 'error');
        return;
    }

    const price = b.price ? Number(b.price).toLocaleString('en-IN') : '0';
    const totalSeats = b.total_seats || 0;
    const bookedSeats = b.booked_seats || 0;
    const availableSeats = totalSeats - bookedSeats;
    const occupancyPercent = totalSeats > 0 ? Math.round((bookedSeats / totalSeats) * 100) : 0;
    const occupancyColor = occupancyPercent >= 100 ? '#e74c3c' : occupancyPercent > 80 ? '#e67e22' : '#27ae60';

    const hasReturnDate = b.return_date ? 
        `<span style="color: #27ae60;"><i class="fas fa-check-circle"></i> ${formatDate(b.return_date)} (✅ Will auto-populate for travelers)</span>` : 
        `<span style="color: #e74c3c;"><i class="fas fa-times-circle"></i> Not Set (⚠️ Travelers cannot auto-populate return date)</span>`;

    const detailsHtml = `
        <div style="padding:10px;">
            <h4 style="color:#2c3e50;margin-bottom:15px;">${escapeHtml(b.batch_name)}</h4>
            
            <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:15px;margin-bottom:20px;">
                <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                    <strong>Departure Date:</strong><br>
                    <span>${b.departure_date ? formatDate(b.departure_date) : 'Not specified'}</span>
                </div>
                <div style="background:#f8f9fa;padding:12px;border-radius:5px;border-left:4px solid ${b.return_date ? '#27ae60' : '#e74c3c'};">
                    <strong>Return Date:</strong><br>
                    <span style="font-weight:bold;">${b.return_date ? formatDate(b.return_date) : '⚠️ Not Set'}</span>
                    <br><small style="color:${b.return_date ? '#27ae60' : '#e74c3c'};">${b.return_date ? '✅ Auto-populates for travelers' : '⚠️ Set this for traveler auto-population'}</small>
                </div>
                <div style="background:#f8f9fa;padding:12px;border-radius:5px;">
                    <strong>Price:</strong><br>
                    <span style="font-size:1.2rem;font-weight:bold;color:#27ae60;">₹${price}</span>
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
            
            ${b.description ? `
                <div style="background:#f8f9fa;padding:15px;border-radius:5px;margin-bottom:20px;">
                    <strong>Description:</strong><br>
                    <p style="margin-top:5px;color:#34495e;">${escapeHtml(b.description)}</p>
                </div>
            ` : ''}
            
            <div style="background:#e8f4f8;padding:15px;border-radius:5px;border-left:4px solid #3498db;">
                <strong><i class="fas fa-info-circle"></i> Traveler Auto-population:</strong><br>
                <p style="margin-top:5px;color:#2c3e50;font-size:0.95rem;">
                    ${b.return_date ? 
                        `✅ Travelers selecting this batch will automatically get "<strong>${formatDate(b.return_date)}</strong>" as their Expected Return Date.` : 
                        `⚠️ No return date set. Travelers will not be able to auto-populate their Expected Return Date from this batch.`
                    }
                </p>
            </div>
        </div>
    `;

    // Show modal
    const modal = document.getElementById('viewBatchModal');
    const details = document.getElementById('batchDetails');
    const overlay = document.getElementById('modalOverlay');

    if (modal && details) {
        details.innerHTML = detailsHtml;
        modal.style.display = 'block';
        if (overlay) overlay.style.display = 'block';
    } else {
        // Fallback: create modal dynamically
        showNotification('View details: ' + b.batch_name, 'info');
    }
}

/**
 * Close view batch modal
 */
function closeViewBatchModal() {
    const modal = document.getElementById('viewBatchModal');
    const overlay = document.getElementById('modalOverlay');
    if (modal) modal.style.display = 'none';
    if (overlay) overlay.style.display = 'none';
}

/**
 * Print batch details
 */
function printBatchDetails() {
    const content = document.getElementById('batchDetails')?.innerHTML;
    if (!content) {
        showNotification('No details to print', 'warning');
        return;
    }

    const printWindow = window.open('', '_blank');
    if (!printWindow) {
        showNotification('Please allow popups for printing', 'warning');
        return;
    }

    printWindow.document.write(`
        <html>
        <head>
            <title>Batch Details</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                .status-badge { padding: 5px 12px; border-radius: 20px; display: inline-block; }
                .status-active { background: #d4edda; color: #155724; }
                .status-pending { background: #fff3cd; color: #856404; }
                .status-inactive { background: #f8d7da; color: #721c24; }
                .status-warning { background: #fff3cd; color: #856404; }
                .status-success { background: #d4edda; color: #155724; }
            </style>
        </head>
        <body>
            <h2>Alhudha Haj Travel - Batch Details</h2>
            <p>Generated on: ${new Date().toLocaleString()}</p>
            ${content}
        </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

// ====== STATISTICS ======
/**
 * Update statistics cards
 */
function updateBatchStatistics() {
    const totalBatches = batchesData.length;
    const openBatches = batchesData.filter(b => b.status === 'Open' || b.status === 'Closing Soon').length;
    const totalSeats = batchesData.reduce((s, b) => s + (b.total_seats || 0), 0);
    const bookedSeats = batchesData.reduce((s, b) => s + (b.booked_seats || 0), 0);
    const totalValue = batchesData.reduce((s, b) => s + ((b.price || 0) * (b.booked_seats || 0)), 0);
    const batchesWithReturn = batchesData.filter(b => b.return_date).length;

    const setEl = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    };

    setEl('totalBatches', totalBatches);
    setEl('openBatches', openBatches);
    setEl('totalSeats', totalSeats);
    setEl('bookedSeats', bookedSeats);
    setEl('totalValue', '₹' + totalValue.toLocaleString('en-IN'));
    
    const returnEl = document.getElementById('batchesWithReturnDate');
    if (returnEl) returnEl.textContent = batchesWithReturn;
}

// ====== DROPDOWN UPDATE ======
/**
 * Update batch dropdowns for traveler forms
 */
function updateBatchDropdowns() {
    // Update add batch dropdown
    const addSelect = document.getElementById('add_batch_id');
    if (addSelect) {
        const currentVal = addSelect.value;
        addSelect.innerHTML = '<option value="">Select Batch</option>';
        batchesData.forEach(b => {
            const returnInfo = b.return_date ? ` (Return: ${b.return_date})` : ' (No return date)';
            const opt = document.createElement('option');
            opt.value = b.id;
            opt.textContent = b.batch_name + returnInfo;
            if (String(b.id) === String(currentVal)) opt.selected = true;
            addSelect.appendChild(opt);
        });
    }

    // Update edit batch dropdown
    const editSelect = document.getElementById('edit_batch_id');
    if (editSelect) {
        const currentVal = editSelect.value;
        editSelect.innerHTML = '<option value="">Select Batch</option>';
        batchesData.forEach(b => {
            const returnInfo = b.return_date ? ` (Return: ${b.return_date})` : ' (No return date)';
            const opt = document.createElement('option');
            opt.value = b.id;
            opt.textContent = b.batch_name + returnInfo;
            if (String(b.id) === String(currentVal)) opt.selected = true;
            editSelect.appendChild(opt);
        });
    }
}

// ====== EXPORT TO CSV ======
/**
 * Export all batches to a CSV file
 */
function exportBatchesToExcel() {
    const data = filteredBatchesData.length > 0 ? filteredBatchesData : batchesData;
    if (!data || data.length === 0) {
        showNotification('No batches to export', 'warning');
        return;
    }

    const headers = ['ID', 'Batch Name', 'Departure Date', 'Return Date', 'Price',
        'Total Seats', 'Booked Seats', 'Available Seats', 'Status', 'Description'];

    const rows = data.map(b => [
        b.id || '',
        b.batch_name || '',
        b.departure_date || '',
        b.return_date || '',
        b.price || 0,
        b.total_seats || 0,
        b.booked_seats || 0,
        (b.total_seats || 0) - (b.booked_seats || 0),
        b.status || 'Open',
        (b.description || '').replace(/"/g, '""')
    ]);

    let csv = headers.map(h => `"${h}"`).join(',') + '\n';
    csv += rows.map(row => row.map(v => `"${v}"`).join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `batches_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    showNotification(`Exported ${data.length} batches to CSV`, 'success');
}

/**
 * Print batches table
 */
function printBatches() {
    const table = document.getElementById('batchesTable');
    if (!table) {
        showNotification('Table not found', 'warning');
        return;
    }

    const printWindow = window.open('', '_blank');
    if (!printWindow) {
        showNotification('Please allow popups for printing', 'warning');
        return;
    }

    printWindow.document.write(`
        <html>
        <head>
            <title>Batches List</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th { background: #2c3e50; color: white; padding: 10px; text-align: left; }
                td { padding: 10px; border: 1px solid #ddd; }
                .status-badge { padding: 5px 12px; border-radius: 20px; display: inline-block; }
                .status-active { background: #d4edda; color: #155724; }
                .status-pending { background: #fff3cd; color: #856404; }
                .status-inactive { background: #f8d7da; color: #721c24; }
                .status-warning { background: #fff3cd; color: #856404; }
                @media print { th { background: #2c3e50 !important; color: white !important; } }
            </style>
        </head>
        <body>
            <h2>Alhudha Haj Travel - Batches List</h2>
            <p>Generated on: ${new Date().toLocaleString()}</p>
            ${table.outerHTML}
        </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

// ====== DATE VALIDATION ======
/**
 * Validate dates for create form
 */
function validateDates() {
    const departure = document.getElementById('departure_date')?.value;
    const returnDate = document.getElementById('return_date')?.value;
    const validationDiv = document.getElementById('create_date_validation');

    if (!validationDiv) return true;

    if (departure && returnDate) {
        if (returnDate < departure) {
            validationDiv.innerHTML = '<i class="fas fa-times-circle"></i> Return date must be after departure date.';
            validationDiv.className = 'date-validation-info invalid';
            return false;
        } else {
            validationDiv.innerHTML = '<i class="fas fa-check-circle"></i> Valid dates: Return is after departure.';
            validationDiv.className = 'date-validation-info valid';
            return true;
        }
    } else if (returnDate) {
        validationDiv.innerHTML = '<i class="fas fa-info-circle"></i> Return date set. Will be used for traveler auto-population.';
        validationDiv.className = 'date-validation-info warning';
        return true;
    } else {
        validationDiv.innerHTML = '';
        validationDiv.className = 'date-validation-info';
        return true;
    }
}

/**
 * Validate dates for edit form
 */
function validateEditDates() {
    const departure = document.getElementById('edit_departure_date')?.value;
    const returnDate = document.getElementById('edit_return_date')?.value;
    const validationDiv = document.getElementById('edit_date_validation');

    if (!validationDiv) return true;

    if (departure && returnDate) {
        if (returnDate < departure) {
            validationDiv.innerHTML = '<i class="fas fa-times-circle"></i> Return date must be after departure date.';
            validationDiv.className = 'date-validation-info invalid';
            return false;
        } else {
            validationDiv.innerHTML = '<i class="fas fa-check-circle"></i> Valid dates: Return is after departure.';
            validationDiv.className = 'date-validation-info valid';
            return true;
        }
    } else if (returnDate) {
        validationDiv.innerHTML = '<i class="fas fa-info-circle"></i> Return date set. Will be used for traveler auto-population.';
        validationDiv.className = 'date-validation-info warning';
        return true;
    } else {
        validationDiv.innerHTML = '';
        validationDiv.className = 'date-validation-info';
        return true;
    }
}

// ====== UI HELPERS ======
/**
 * Show loading state
 */
function showLoading(btn, text) {
    if (!btn) return;
    btn.disabled = true;
    const icon = btn.querySelector('i');
    if (icon) {
        icon.className = 'fas fa-spinner fa-spin';
    }
    btn.textContent = text || 'Loading...';
}

/**
 * Hide loading state
 */
function hideLoading(btn) {
    if (!btn) return;
    btn.disabled = false;
    const icon = btn.querySelector('i');
    if (icon) {
        icon.className = 'fas fa-save';
    }
    btn.textContent = btn.textContent.replace('Loading...', 'Save');
    btn.textContent = btn.textContent.replace('Updating...', 'Update');
    btn.textContent = btn.textContent.replace('Creating...', 'Create');
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format date
 */
function formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return dateStr;
        return date.toLocaleDateString('en-IN');
    } catch (e) {
        return dateStr;
    }
}

/**
 * Format date for input
 */
function formatDateForInput(dateStr) {
    if (!dateStr) return '';
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return dateStr;
    try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return '';
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    } catch (e) {
        return '';
    }
}

// ====== NOTIFICATION ======
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    if (!notification) {
        console.log(`${type.toUpperCase()}: ${message}`);
        return;
    }

    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };

    notification.className = `notification notification-${type}`;
    notification.innerHTML = `<i class="fas fa-${icons[type] || 'info-circle'}"></i> ${message}`;
    notification.style.display = 'block';

    if (window.notificationTimeout) {
        clearTimeout(window.notificationTimeout);
    }

    window.notificationTimeout = setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

// ====== INITIALIZATION ======
/**
 * Initialize page with session check
 */
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Batches page initializing...');
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
    console.log('📋 Initializing page...');
    resetSessionTimer();

    // Monitor user activity
    ['click', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
        document.addEventListener(event, resetSessionTimer);
    });

    // Load page data
    await loadBatches();

    // Set up search listeners
    const searchEl = document.getElementById('searchBatches');
    if (searchEl) {
        searchEl.addEventListener('input', function() {
            filterBatches();
        });
    }

    // Set up date validation listeners
    const depEl = document.getElementById('departure_date');
    const retEl = document.getElementById('return_date');
    if (depEl) depEl.addEventListener('change', validateDates);
    if (retEl) retEl.addEventListener('change', validateDates);

    const editDepEl = document.getElementById('edit_departure_date');
    const editRetEl = document.getElementById('edit_return_date');
    if (editDepEl) editDepEl.addEventListener('change', validateEditDates);
    if (editRetEl) editRetEl.addEventListener('change', validateEditDates);

    console.log('✅ Batches page loaded successfully with return date support!');
}

// Session timer functions
function resetSessionTimer() {
    // Will be overridden by session-manager.js
    console.log('Session timer reset');
}

// ====== EXPOSE GLOBALS ======
window.loadBatches = loadBatches;
window.filterBatches = filterBatches;
window.clearSearch = clearSearch;
window.previousPage = previousPage;
window.nextPage = nextPage;
window.showCreateBatchForm = showCreateBatchForm;
window.hideCreateBatchForm = hideCreateBatchForm;
window.hideEditBatchForm = hideEditBatchForm;
window.createBatch = createBatch;
window.editBatch = editBatch;
window.updateBatch = updateBatch;
window.deleteBatch = deleteBatch;
window.viewBatchDetails = viewBatchDetails;
window.closeViewBatchModal = closeViewBatchModal;
window.printBatchDetails = printBatchDetails;
window.exportBatchesToExcel = exportBatchesToExcel;
window.printBatches = printBatches;
window.validateDates = validateDates;
window.validateEditDates = validateEditDates;
window.showNotification = showNotification;
window.logout = async function() {
    if (confirm('Are you sure you want to logout?')) {
        if (typeof SessionManager !== 'undefined' && SessionManager.logout) {
            await SessionManager.logout();
        } else {
            window.location.href = '/admin/login.html';
        }
    }
};

console.log('✅ batches.js loaded successfully with return_date support!');
