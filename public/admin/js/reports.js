'use strict';

let currentReportData = null;
let currentReportType = 'travelers';

document.addEventListener('DOMContentLoaded', function() {
    console.log("✅ reports.js loaded");
});

// ====== ✅ FIXED: REPORT GENERATION ======
async function generateReport() {
    console.log("🚀 generateReport() CALLED");
    
    showReportLoading();

    const range = document.getElementById('dateRange').value;
    const batch = document.getElementById('reportBatch').value;
    const status = document.getElementById('reportStatus').value;

    let startDate, endDate;

    if (range === 'custom') {
        startDate = document.getElementById('startDate').value;
        endDate = document.getElementById('endDate').value;
    } else {
        const dates = getDateRange(range);
        startDate = dates.start;
        endDate = dates.end;
    }

    document.getElementById('reportResults').style.display = 'block';
    document.getElementById('reportTitle').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Report...';

    initializeColumnSelector('travelers');

    try {
        const response = await fetch('/api/reports/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                type: currentReportType,
                filters: {
                    startDate: startDate,
                    endDate: endDate,
                    batchId: batch,
                    status: status
                }
            })
        });

        console.log("📡 Response Status:", response.status);

        if (response.ok) {
            const data = await response.json();
            console.log("📦 Backend Data:", data);
            
            if (data.success) {
                displayReport(data.report);
            } else {
                showNotification('Backend error: ' + (data.error || 'Unknown error'), 'error');
            }
        } else {
            showNotification('Server error: ' + response.status, 'error');
        }
    } catch (error) {
        console.error('❌ Network Error:', error);
        showNotification('Network error. Please try again.', 'error');
    } finally {
        hideReportLoading();
    }
}

// ====== ✅ FIXED: DISPLAY REPORT ======
function displayReport(data) {
    console.log("🚀 displayReport() CALLED with data:", data);
    
    if (!data) {
        console.error("❌ displayReport() received null data!");
        showNotification('Report data is empty', 'error');
        return;
    }

    currentReportData = data;
    
    document.getElementById('reportTitle').innerHTML = '<i class="fas fa-chart-pie"></i> Report Results';
    
    // Display summary cards
    const summaryHtml = `
        <div class="stat-card">
            <i class="fas fa-users"></i>
            <h3>Total Travelers</h3>
            <div class="stat-number">${data.summary.totalTravelers}</div>
            <small>+${data.summary.newTravelers} this period</small>
        </div>
        <div class="stat-card">
            <i class="fas fa-rupee-sign"></i>
            <h3>Total Collections</h3>
            <div class="stat-number">₹${(data.summary.totalPayments / 100000).toFixed(2)}L</div>
            <small>₹${(data.summary.pendingPayments / 100000).toFixed(2)}L pending</small>
        </div>
        <div class="stat-card">
            <i class="fas fa-layer-group"></i>
            <h3>Active Batches</h3>
            <div class="stat-number">${data.summary.activeBatches}</div>
            <small>${data.summary.occupancyRate}% occupancy</small>
        </div>
        <div class="stat-card">
            <i class="fas fa-percent"></i>
            <h3>Collection Rate</h3>
            <div class="stat-number">${data.summary.collectionRate || 80}%</div>
            <small>of total expected</small>
        </div>
    `;
    document.getElementById('reportSummary').innerHTML = summaryHtml;
    
    // Display table
    displayReportTable(data);
    
    // Charts
    createPaymentsChart(data.paymentsByMethod || {});
    createTravelersChart(data.travelersByBatch || []);
    
    showNotification(`Report generated: ${data.count || data.data?.length || 0} records`, 'success');
}

// ====== ✅ FIXED: DISPLAY TABLE ======
function displayReportTable(data) {
    console.log("📊 displayReportTable() called");
    
    const tableHeader = document.getElementById('reportHeaderRow');
    const tableBody = document.getElementById('reportTableBody');
    
    // Get data source
    let dataSource = [];
    if (data.travelers) dataSource = data.travelers;
    else if (data.batches) dataSource = data.batches;
    else if (data.payments) dataSource = data.payments;
    else if (data.data) dataSource = data.data;
    
    console.log("📊 Data source found:", dataSource);

    if (dataSource.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="10" style="text-align: center;">No data available</td></tr>';
        return;
    }

    // Get columns
    const cols = Object.keys(dataSource[0]);
    
    // Build header
    let headerHtml = '';
    cols.forEach(col => {
        headerHtml += `<th>${col.replace(/_/g, ' ').toUpperCase()}</th>`;
    });
    tableHeader.innerHTML = headerHtml;
    
    // Build body
    let bodyHtml = '';
    dataSource.forEach(row => {
        bodyHtml += '<tr>';
        cols.forEach(col => {
            let value = row[col] !== undefined ? row[col] : '-';
            bodyHtml += `<td>${value}</td>`;
        });
        bodyHtml += '</tr>';
    });
    
    tableBody.innerHTML = bodyHtml;
    
    // Show column selector
    document.getElementById('columnSelector').style.display = 'block';
}

// ====== DATE RANGE HELPER ======
function getDateRange(range) {
    const today = new Date();
    const end = new Date(today);
    const start = new Date(today);
    
    switch(range) {
        case 'today':
            start.setHours(0,0,0,0);
            end.setHours(23,59,59,999);
            break;
        case 'yesterday':
            start.setDate(today.getDate() - 1);
            start.setHours(0,0,0,0);
            end.setDate(today.getDate() - 1);
            end.setHours(23,59,59,999);
            break;
        case 'thisweek':
            start.setDate(today.getDate() - today.getDay());
            start.setHours(0,0,0,0);
            break;
        case 'lastweek':
            start.setDate(today.getDate() - today.getDay() - 7);
            end.setDate(today.getDate() - today.getDay() - 1);
            end.setHours(23,59,59,999);
            break;
        case 'thismonth':
            start.setDate(1);
            start.setHours(0,0,0,0);
            break;
        case 'lastmonth':
            start.setMonth(today.getMonth() - 1, 1);
            start.setHours(0,0,0,0);
            end.setMonth(today.getMonth(), 0);
            end.setHours(23,59,59,999);
            break;
        case 'thisyear':
            start.setMonth(0, 1);
            start.setHours(0,0,0,0);
            break;
        case 'lastyear':
            start.setFullYear(today.getFullYear() - 1, 0, 1);
            start.setHours(0,0,0,0);
            end.setFullYear(today.getFullYear() - 1, 11, 31);
            end.setHours(23,59,59,999);
            break;
        case 'alltime':
            start.setFullYear(2000, 0, 1);
            end.setFullYear(2100, 0, 1);
            break;
    }
    
    return {
        start: start.toISOString().split('T')[0],
        end: end.toISOString().split('T')[0]
    };
}

// ====== COLUMN SELECTOR ======
function initializeColumnSelector(module) {
    // Placeholder - just show the selector
    document.getElementById('columnSelector').style.display = 'block';
}

function toggleAllColumns() {
    // Placeholder
}

// ====== LOADING FUNCTIONS ======
function showReportLoading() {
    document.getElementById('reportLoadingOverlay').style.display = 'flex';
}

function hideReportLoading() {
    document.getElementById('reportLoadingOverlay').style.display = 'none';
}

// ====== NOTIFICATION ======
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    if (!notification) return;
    
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i> ${message}`;
    notification.style.display = 'block';
    setTimeout(() => notification.style.display = 'none', 3000);
}

// ====== EXPORT FUNCTIONS ======
function exportToPDF() {
    if (!currentReportData) {
        showNotification('No report data to export', 'error');
        return;
    }
    showNotification('PDF export feature coming soon!', 'info');
}

function exportToExcel() {
    if (!currentReportData) {
        showNotification('No report data to export', 'error');
        return;
    }
    showNotification('Excel export feature coming soon!', 'info');
}

function exportToCSV() {
    if (!currentReportData) {
        showNotification('No report data to export', 'error');
        return;
    }
    showNotification('CSV export feature coming soon!', 'info');
}

// ====== REPORT MODAL ======
function showReportModal(type) {
    currentReportType = type;
    showNotification(`Opening ${type} report options`, 'info');
    document.getElementById('reportModal').style.display = 'block';
    document.getElementById('modalOverlay').style.display = 'block';
}

function closeReportModal() {
    document.getElementById('reportModal').style.display = 'none';
    document.getElementById('modalOverlay').style.display = 'none';
}

function generateCustomReport() {
    closeReportModal();
    generateReport();
}

// ====== RESET FILTERS ======
function resetFilters() {
    document.getElementById('dateRange').value = 'today';
    document.getElementById('reportBatch').value = 'all';
    document.getElementById('reportStatus').value = 'all';
    document.getElementById('startDateGroup').style.display = 'none';
    document.getElementById('endDateGroup').style.display = 'none';
    document.getElementById('reportResults').style.display = 'none';
    document.getElementById('columnSelector').style.display = 'none';
    showNotification('Filters reset', 'info');
}

// ====== PRINT ======
function printReport() {
    if (!currentReportData) {
        showNotification('No report data to print', 'error');
        return;
    }
    window.print();
}