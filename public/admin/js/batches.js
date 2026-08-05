// ================================================================
// BATCHES.JS - Complete Fixed Version
// ================================================================

// Global state
let batchesData = [];
let currentPage = 1;
let itemsPerPage = 10;
let filteredBatches = [];
let currentEditBatchId = null;

// ====== LOAD BATCHES FROM API ======
async function loadBatches() {
    try {
        const response = await fetch('/api/batches', {
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/admin/login.html';
                return;
            }
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.batches) {
            batchesData = data.batches;
            filteredBatches = [...batchesData];
            displayBatches();
            updateStatistics();
            return batchesData;
        } else {
            console.warn('No batches returned, using empty array');
            batchesData = [];
            filteredBatches = [];
            displayBatches();
            updateStatistics();
            return [];
        }
    } catch (error) {
        console.error('Error loading batches:', error);
        showNotification('Failed to load batches. Please try again.', 'error');
        batchesData = [];
        filteredBatches = [];
        displayBatches();
        updateStatistics();
        return [];
    }
}

// ====== DISPLAY BATCHES ======
function displayBatches() {
    const tbody = document.getElementById('batchesTableBody');
    if (!tbody) return;
    
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const pageItems = filteredBatches.slice(start, end);
    
    if (pageItems.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="11" style="text-align: center; padding: 40px;">
                    <i class="fas fa-inbox" style="font-size: 2rem; color: #bdc3c7;"></i>
                    <p style="margin-top: 10px; color: #7f8c8d;">No batches found</p>
                    <p style="color: #95a5a6; font-size: 0.9rem;">Click "Create New Batch" to add one</p>
                </td>
            </tr>
        `;
        updatePaginationInfo();
        return;
    }
    
    tbody.innerHTML = pageItems.map(batch => {
        const totalSeats = parseInt(batch.total_seats) || 0;
        const bookedSeats = parseInt(batch.booked_seats) || 0;
        const availableSeats = totalSeats - bookedSeats;
        const occupancyPercentage = totalSeats > 0 ? Math.round((bookedSeats / totalSeats) * 100) : 0;
        
        // Determine status badge
        let statusClass = 'status-active';
        if (batch.status === 'Closed' || batch.status === 'Full') {
            statusClass = 'status-inactive';
        } else if (batch.status === 'Closing Soon') {
            statusClass = 'status-warning';
        } else if (batch.status === 'Open') {
            statusClass = 'status-success';
        }
        
        // Format dates
        const departureDate = batch.departure_date ? new Date(batch.departure_date).toLocaleDateString('en-IN') : 'N/A';
        const returnDate = batch.return_date ? new Date(batch.return_date).toLocaleDateString('en-IN') : 'N/A';
        
        // Check if return date is set (for visual indicator)
        const hasReturnDate = batch.return_date && batch.return_date !== '0000-00-00';
        
        return `
            <tr>
                <td><strong>#${batch.id || 'N/A'}</strong></td>
                <td>
                    <strong>${batch.batch_name || 'Unnamed Batch'}</strong>
                    ${batch.description ? `<br><small style="color: #7f8c8d; font-size: 0.8rem;">${batch.description.substring(0, 30)}${batch.description.length > 30 ? '...' : ''}</small>` : ''}
                </td>
                <td>${departureDate}</td>
                <td>
                    ${returnDate}
                    ${hasReturnDate ? '<i class="fas fa-check-circle" style="color: #27ae60; margin-left: 5px;" title="Return date set"></i>' : '<i class="fas fa-exclamation-circle" style="color: #f39c12; margin-left: 5px;" title="Return date not set - required for travelers"></i>'}
                </td>
                <td>₹${parseInt(batch.price || 0).toLocaleString('en-IN')}</td>
                <td>${totalSeats}</td>
                <td>${bookedSeats}</td>
                <td>${availableSeats}</td>
                <td><span class="status-badge ${statusClass}">${batch.status || 'Open'}</span></td>
                <td>
                    <div style="display: flex; align-items: center; gap: 5px;">
                        <div style="flex: 1; height: 6px; background: #ecf0f1; border-radius: 3px; min-width: 50px;">
                            <div style="height: 100%; background: ${occupancyPercentage > 90 ? '#e74c3c' : occupancyPercentage > 70 ? '#f39c12' : '#27ae60'}; width: ${occupancyPercentage}%; border-radius: 3px;"></div>
                        </div>
                        <span style="font-size: 0.8rem; color: #7f8c8d; min-width: 40px;">${occupancyPercentage}%</span>
                    </div>
                </td>
                <td>
                    <div style="display: flex; gap: 5px; flex-wrap: wrap;">
                        <button class="icon-btn" onclick="viewBatch(${batch.id})" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="icon-btn" onclick="editBatch(${batch.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="icon-btn" onclick="deleteBatch(${batch.id})" title="Delete" style="color: #e74c3c;">
                            <i class="fas fa-trash"></i>
                        </button>
                        <button class="icon-btn" onclick="manageTravelers(${batch.id})" title="Manage Travelers" style="color: #27ae60;">
                            <i class="fas fa-users"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    updatePaginationInfo();
}

// ====== UPDATE STATISTICS ======
function updateStatistics() {
    const totalBatches = batchesData.length;
    const openBatches = batchesData.filter(b => b.status === 'Open' || b.status === 'Closing Soon').length;
    const totalSeats = batchesData.reduce((sum, b) => sum + (parseInt(b.total_seats) || 0), 0);
    const bookedSeats = batchesData.reduce((sum, b) => sum + (parseInt(b.booked_seats) || 0), 0);
    const totalValue = batchesData.reduce((sum, b) => sum + ((parseInt(b.price) || 0) * (parseInt(b.booked_seats) || 0)), 0);
    const batchesWithReturnDate = batchesData.filter(b => b.return_date && b.return_date !== '0000-00-00').length;
    
    document.getElementById('totalBatches').textContent = totalBatches;
    document.getElementById('openBatches').textContent = openBatches;
    document.getElementById('totalSeats').textContent = totalSeats;
    document.getElementById('bookedSeats').textContent = bookedSeats;
    document.getElementById('totalValue').textContent = `₹${totalValue.toLocaleString('en-IN')}`;
    document.getElementById('batchesWithReturnDate').textContent = batchesWithReturnDate;
}

// ====== CREATE BATCH ======
async function createBatch() {
    const batchName = document.getElementById('batch_name').value.trim();
    if (!batchName) {
        showNotification('Please enter a batch name', 'error');
        return;
    }
    
    const data = {
        batch_name: batchName,
        total_seats: parseInt(document.getElementById('total_seats').value) || 150,
        price: parseFloat(document.getElementById('price').value.replace(/,/g, '')) || 0,
        departure_date: document.getElementById('departure_date').value || null,
        return_date: document.getElementById('return_date').value || null,
        status: document.getElementById('status').value || 'Open',
        description: document.getElementById('description').value.trim() || null
    };
    
    // Validate dates if both are provided
    if (data.departure_date && data.return_date && data.return_date < data.departure_date) {
        showNotification('Return date must be after departure date', 'error');
        return;
    }
    
    // Validate return date is required
    if (!data.return_date) {
        showNotification('Return date is required for travelers to be added', 'warning');
        // Allow creation but warn
    }
    
    try {
        const response = await fetch('/api/batches', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Batch created successfully!', 'success');
            hideCreateBatchForm();
            await loadBatches();
        } else {
            throw new Error(result.message || 'Failed to create batch');
        }
    } catch (error) {
        console.error('Error creating batch:', error);
        showNotification('Failed to create batch: ' + error.message, 'error');
    }
}

// ====== EDIT BATCH ======
async function editBatch(id) {
    try {
        const response = await fetch(`/api/batches/${id}`, {
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success || !data.batch) {
            throw new Error(data.message || 'Batch not found');
        }
        
        const batch = data.batch;
        currentEditBatchId = id;
        
        document.getElementById('edit_batch_id').value = id;
        document.getElementById('edit_batch_name').value = batch.batch_name || '';
        document.getElementById('edit_departure_date').value = batch.departure_date || '';
        document.getElementById('edit_return_date').value = batch.return_date || '';
        document.getElementById('edit_price').value = batch.price || '';
        document.getElementById('edit_total_seats').value = batch.total_seats || '';
        document.getElementById('edit_status').value = batch.status || 'Open';
        
        // Show validation info for return date
        if (batch.return_date && batch.return_date !== '0000-00-00') {
            document.getElementById('edit_date_validation').innerHTML = 
                '<i class="fas fa-check-circle"></i> Return date set. Travelers can be auto-populated.';
            document.getElementById('edit_date_validation').className = 'date-validation-info valid';
        } else {
            document.getElementById('edit_date_validation').innerHTML = 
                '<i class="fas fa-exclamation-circle"></i> Return date is required for traveler management.';
            document.getElementById('edit_date_validation').className = 'date-validation-info warning';
        }
        
        document.getElementById('editBatchForm').style.display = 'block';
        document.getElementById('editBatchForm').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Error loading batch for edit:', error);
        showNotification('Failed to load batch details', 'error');
    }
}

// ====== UPDATE BATCH ======
async function updateBatch() {
    const id = document.getElementById('edit_batch_id').value;
    if (!id) {
        showNotification('Invalid batch ID', 'error');
        return;
    }
    
    const batchName = document.getElementById('edit_batch_name').value.trim();
    if (!batchName) {
        showNotification('Please enter a batch name', 'error');
        return;
    }
    
    const data = {
        batch_name: batchName,
        total_seats: parseInt(document.getElementById('edit_total_seats').value) || 150,
        price: parseFloat(document.getElementById('edit_price').value.replace(/,/g, '')) || 0,
        departure_date: document.getElementById('edit_departure_date').value || null,
        return_date: document.getElementById('edit_return_date').value || null,
        status: document.getElementById('edit_status').value || 'Open'
    };
    
    // Validate dates if both are provided
    if (data.departure_date && data.return_date && data.return_date < data.departure_date) {
        showNotification('Return date must be after departure date', 'error');
        return;
    }
    
    if (!data.return_date) {
        showNotification('Return date is required for travelers to be added', 'warning');
    }
    
    try {
        const response = await fetch(`/api/batches/${id}`, {
            method: 'PUT',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Batch updated successfully!', 'success');
            hideEditBatchForm();
            await loadBatches();
        } else {
            throw new Error(result.message || 'Failed to update batch');
        }
    } catch (error) {
        console.error('Error updating batch:', error);
        showNotification('Failed to update batch: ' + error.message, 'error');
    }
}

// ====== DELETE BATCH ======
async function deleteBatch(id) {
    // First check if batch has travelers
    try {
        const checkResponse = await fetch(`/api/batches/${id}/travelers`, {
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        });
        
        if (checkResponse.ok) {
            const data = await checkResponse.json();
            if (data.travelers && data.travelers.length > 0) {
                if (!confirm(`This batch has ${data.travelers.length} travelers. Deleting it will also remove all associated travelers. Are you sure?`)) {
                    return;
                }
            }
        }
    } catch (e) {
        console.warn('Could not check travelers:', e);
    }
    
    if (!confirm('Are you sure you want to delete this batch? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/batches/${id}`, {
            method: 'DELETE',
            credentials: 'include',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Batch deleted successfully!', 'success');
            await loadBatches();
        } else {
            throw new Error(result.message || 'Failed to delete batch');
        }
    } catch (error) {
        console.error('Error deleting batch:', error);
        showNotification('Failed to delete batch: ' + error.message, 'error');
    }
}

// ====== VIEW BATCH ======
async function viewBatch(id) {
    try {
        const response = await fetch(`/api/batches/${id}`, {
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success || !data.batch) {
            throw new Error(data.message || 'Batch not found');
        }
        
        const batch = data.batch;
        
        // Also get travelers for this batch
        let travelers = [];
        try {
            const travelerResponse = await fetch(`/api/batches/${id}/travelers`, {
                credentials: 'include',
                headers: { 'Accept': 'application/json' }
            });
            if (travelerResponse.ok) {
                const travelerData = await travelerResponse.json();
                travelers = travelerData.travelers || [];
            }
        } catch (e) {
            console.warn('Could not fetch travelers:', e);
        }
        
        const departureDate = batch.departure_date ? new Date(batch.departure_date).toLocaleDateString('en-IN') : 'N/A';
        const returnDate = batch.return_date ? new Date(batch.return_date).toLocaleDateString('en-IN') : 'Not Set';
        const totalSeats = parseInt(batch.total_seats) || 0;
        const bookedSeats = parseInt(batch.booked_seats) || 0;
        const availableSeats = totalSeats - bookedSeats;
        const occupancy = totalSeats > 0 ? Math.round((bookedSeats / totalSeats) * 100) : 0;
        
        let travelersHtml = '';
        if (travelers.length > 0) {
            travelersHtml = `
                <h4 style="margin: 15px 0 10px;"><i class="fas fa-users"></i> Travelers (${travelers.length})</h4>
                <div style="max-height: 200px; overflow-y: auto; border: 1px solid #ecf0f1; border-radius: 5px;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 8px; text-align: left;">Name</th>
                                <th style="padding: 8px; text-align: left;">Passport</th>
                                <th style="padding: 8px; text-align: left;">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${travelers.map(t => `
                                <tr>
                                    <td style="padding: 8px;">${t.name || 'N/A'}</td>
                                    <td style="padding: 8px;">${t.passport_number || 'N/A'}</td>
                                    <td style="padding: 8px;"><span class="status-badge ${t.status === 'Approved' ? 'status-success' : 'status-pending'}">${t.status || 'Pending'}</span></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            travelersHtml = `
                <p style="color: #7f8c8d; margin: 10px 0;">
                    <i class="fas fa-info-circle"></i> No travelers in this batch yet.
                    ${batch.return_date && batch.return_date !== '0000-00-00' ? ' Set return date to auto-populate.' : ' <strong style="color: #f39c12;">Set return date to enable traveler management.</strong>'}
                </p>
            `;
        }
        
        document.getElementById('batchDetails').innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div><strong>Batch Name:</strong> ${batch.batch_name || 'N/A'}</div>
                <div><strong>Status:</strong> <span class="status-badge ${batch.status === 'Open' ? 'status-success' : batch.status === 'Closed' ? 'status-inactive' : 'status-warning'}">${batch.status || 'Open'}</span></div>
                <div><strong>Departure Date:</strong> ${departureDate}</div>
                <div><strong>Return Date:</strong> ${returnDate} ${batch.return_date && batch.return_date !== '0000-00-00' ? '<i class="fas fa-check-circle" style="color: #27ae60;"></i>' : '<i class="fas fa-exclamation-circle" style="color: #f39c12;"></i>'}</div>
                <div><strong>Price:</strong> ₹${parseInt(batch.price || 0).toLocaleString('en-IN')}</div>
                <div><strong>Total Seats:</strong> ${totalSeats}</div>
                <div><strong>Booked Seats:</strong> ${bookedSeats}</div>
                <div><strong>Available Seats:</strong> ${availableSeats}</div>
                <div style="grid-column: 1 / -1;">
                    <strong>Occupancy:</strong>
                    <div style="display: flex; align-items: center; gap: 10px; margin-top: 5px;">
                        <div style="flex: 1; height: 10px; background: #ecf0f1; border-radius: 5px;">
                            <div style="height: 100%; background: ${occupancy > 90 ? '#e74c3c' : occupancy > 70 ? '#f39c12' : '#27ae60'}; width: ${occupancy}%; border-radius: 5px;"></div>
                        </div>
                        <span>${occupancy}%</span>
                    </div>
                </div>
                ${batch.description ? `<div style="grid-column: 1 / -1;"><strong>Description:</strong><br>${batch.description}</div>` : ''}
                <div style="grid-column: 1 / -1; border-top: 1px solid #ecf0f1; padding-top: 15px; margin-top: 5px;">
                    <strong>Created:</strong> ${batch.created_at ? new Date(batch.created_at).toLocaleString('en-IN') : 'N/A'}
                    ${batch.updated_at ? ` | <strong>Updated:</strong> ${new Date(batch.updated_at).toLocaleString('en-IN')}` : ''}
                </div>
                <div style="grid-column: 1 / -1;">
                    ${travelersHtml}
                </div>
            </div>
        `;
        
        document.getElementById('viewBatchModal').style.display = 'block';
        document.getElementById('modalOverlay').style.display = 'block';
    } catch (error) {
        console.error('Error viewing batch:', error);
        showNotification('Failed to load batch details', 'error');
    }
}

// ====== MANAGE TRAVELERS ======
function manageTravelers(id) {
    // Navigate to travelers page with batch filter
    window.location.href = `/admin/travelers.html?batch_id=${id}`;
}

// ====== CLOSE MODAL ======
function closeViewBatchModal() {
    document.getElementById('viewBatchModal').style.display = 'none';
    document.getElementById('modalOverlay').style.display = 'none';
}

// ====== PRINT BATCH DETAILS ======
function printBatchDetails() {
    const content = document.getElementById('batchDetails').innerHTML;
    const originalTitle = document.title;
    document.title = 'Batch Details';
    const printWindow = window.open('', '_blank', 'width=800,height=600');
    printWindow.document.write(`
        <html>
        <head><title>Batch Details</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            h2 { color: #2c3e50; }
            .status-badge { padding: 3px 10px; border-radius: 20px; font-size: 0.8rem; display: inline-block; }
            .status-success { background: #d4edda; color: #155724; }
            .status-warning { background: #fff3cd; color: #856404; }
            .status-inactive { background: #f8d7da; color: #721c24; }
            table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            th { background: #f8f9fa; padding: 8px; text-align: left; border: 1px solid #dee2e6; }
            td { padding: 8px; border: 1px solid #dee2e6; }
        </style>
        </head>
        <body>
            <h2><i class="fas fa-layer-group"></i> Batch Details</h2>
            ${content}
            <p style="margin-top: 20px; color: #7f8c8d; font-size: 0.8rem;">Printed on ${new Date().toLocaleString('en-IN')}</p>
        </body>
        </html>
    `);
    printWindow.document.close();
    setTimeout(() => {
        printWindow.print();
    }, 500);
    document.title = originalTitle;
}

// ====== SEARCH BATCHES ======
function searchBatches() {
    const query = document.getElementById('searchBatches').value.toLowerCase().trim();
    if (!query) {
        filteredBatches = [...batchesData];
    } else {
        filteredBatches = batchesData.filter(batch => {
            const name = (batch.batch_name || '').toLowerCase();
            const status = (batch.status || '').toLowerCase();
            const departure = batch.departure_date || '';
            const returnDate = batch.return_date || '';
            const desc = (batch.description || '').toLowerCase();
            
            return name.includes(query) || 
                   status.includes(query) || 
                   departure.includes(query) || 
                   returnDate.includes(query) ||
                   desc.includes(query);
        });
    }
    currentPage = 1;
    displayBatches();
}

// ====== CLEAR SEARCH ======
function clearSearch() {
    document.getElementById('searchBatches').value = '';
    filteredBatches = [...batchesData];
    currentPage = 1;
    displayBatches();
}

// ====== PAGINATION ======
function updatePaginationInfo() {
    const total = filteredBatches.length;
    const start = total > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0;
    const end = Math.min(currentPage * itemsPerPage, total);
    
    document.getElementById('showingFrom').textContent = start;
    document.getElementById('showingTo').textContent = end;
    document.getElementById('totalCount').textContent = total;
    
    document.getElementById('prevPageBtn').disabled = currentPage === 1;
    document.getElementById('nextPageBtn').disabled = end >= total;
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        displayBatches();
    }
}

function nextPage() {
    const totalPages = Math.ceil(filteredBatches.length / itemsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        displayBatches();
    }
}

// ====== EXPORT TO EXCEL ======
function exportBatchesToExcel() {
    if (filteredBatches.length === 0) {
        showNotification('No batches to export', 'warning');
        return;
    }
    
    // Simple CSV export
    const headers = ['ID', 'Batch Name', 'Departure Date', 'Return Date', 'Price', 'Total Seats', 'Booked Seats', 'Available Seats', 'Status', 'Occupancy %'];
    const rows = filteredBatches.map(batch => {
        const totalSeats = parseInt(batch.total_seats) || 0;
        const bookedSeats = parseInt(batch.booked_seats) || 0;
        const availableSeats = totalSeats - bookedSeats;
        const occupancy = totalSeats > 0 ? Math.round((bookedSeats / totalSeats) * 100) : 0;
        
        return [
            batch.id || '',
            batch.batch_name || '',
            batch.departure_date || '',
            batch.return_date || '',
            batch.price || 0,
            totalSeats,
            bookedSeats,
            availableSeats,
            batch.status || 'Open',
            occupancy
        ];
    });
    
    const csvContent = [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `batches_export_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    showNotification('Exported successfully!', 'success');
}

// ====== PRINT BATCHES ======
function printBatches() {
    const table = document.getElementById('batchesTable');
    const originalTitle = document.title;
    document.title = 'Batches List';
    const printWindow = window.open('', '_blank', 'width=1000,height=600');
    printWindow.document.write(`
        <html>
        <head><title>Batches List</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            h2 { color: #2c3e50; }
            table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            th { background: #2c3e50; color: white; padding: 10px; text-align: left; }
            td { padding: 10px; border-bottom: 1px solid #ecf0f1; }
            .status-badge { padding: 3px 10px; border-radius: 20px; font-size: 0.8rem; display: inline-block; }
            .status-success { background: #d4edda; color: #155724; }
            .status-warning { background: #fff3cd; color: #856404; }
            .status-inactive { background: #f8d7da; color: #721c24; }
            .status-active { background: #d4edda; color: #155724; }
        </style>
        </head>
        <body>
            <h2><i class="fas fa-layer-group"></i> Batches List</h2>
            <p>Generated on ${new Date().toLocaleString('en-IN')}</p>
            ${table.outerHTML}
        </body>
        </html>
    `);
    printWindow.document.close();
    setTimeout(() => {
        printWindow.print();
    }, 500);
    document.title = originalTitle;
}

// ====== ENSURE DATE VALIDATION ======
// This is called from the HTML onchange events
function validateDates() {
    const departure = document.getElementById('departure_date').value;
    const returnDate = document.getElementById('return_date').value;
    const validationDiv = document.getElementById('create_date_validation');
    
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

function validateEditDates() {
    const departure = document.getElementById('edit_departure_date').value;
    const returnDate = document.getElementById('edit_return_date').value;
    const validationDiv = document.getElementById('edit_date_validation');
    
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

// ====== EXPOSE FUNCTIONS TO GLOBAL SCOPE ======
window.loadBatches = loadBatches;
window.displayBatches = displayBatches;
window.updateStatistics = updateStatistics;
window.createBatch = createBatch;
window.editBatch = editBatch;
window.updateBatch = updateBatch;
window.deleteBatch = deleteBatch;
window.viewBatch = viewBatch;
window.manageTravelers = manageTravelers;
window.closeViewBatchModal = closeViewBatchModal;
window.printBatchDetails = printBatchDetails;
window.searchBatches = searchBatches;
window.clearSearch = clearSearch;
window.previousPage = previousPage;
window.nextPage = nextPage;
window.exportBatchesToExcel = exportBatchesToExcel;
window.printBatches = printBatches;
window.showCreateBatchForm = showCreateBatchForm;
window.hideCreateBatchForm = hideCreateBatchForm;
window.hideEditBatchForm = hideEditBatchForm;
window.validateDates = validateDates;
window.validateEditDates = validateEditDates;
window.allowNumbersOnly = allowNumbersOnly;

console.log('✅ batches.js loaded successfully');
