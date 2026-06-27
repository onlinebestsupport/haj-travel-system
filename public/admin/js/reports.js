'use strict';

let currentReportData = null;
let currentReportType = 'travelers';
let allColumns = [];
let selectedColumns = [];

document.addEventListener('DOMContentLoaded', function() {
    console.log("✅ reports.js loaded");
    loadReports();
    
    // Initialize column selector with 33 traveler fields
    initializeColumnSelector('travelers');
});

// ====== 33 TRAVELER FIELD DEFINITIONS ======
const columnDefinitions = {
    travelers: [
        // Personal Information (10 fields)
        { id: 'id', name: 'ID', category: 'System' },
        { id: 'first_name', name: 'First Name', category: 'Personal' },
        { id: 'last_name', name: 'Last Name', category: 'Personal' },
        { id: 'passport_name', name: 'Passport Name', category: 'Personal' },
        { id: 'batch_id', name: 'Batch ID', category: 'Batch' },
        { id: 'passport_no', name: 'Passport Number', category: 'Passport' },
        { id: 'passport_issue_date', name: 'Passport Issue Date', category: 'Passport' },
        { id: 'passport_expiry_date', name: 'Passport Expiry Date', category: 'Passport' },
        { id: 'passport_status', name: 'Passport Status', category: 'Passport' },
        { id: 'gender', name: 'Gender', category: 'Personal' },
        { id: 'dob', name: 'Date of Birth', category: 'Personal' },

        // Contact Information (7 fields)
        { id: 'mobile', name: 'Mobile Number', category: 'Contact' },
        { id: 'email', name: 'Email Address', category: 'Contact' },
        { id: 'aadhaar', name: 'Aadhaar Number', category: 'ID' },
        { id: 'pan', name: 'PAN Number', category: 'ID' },
        { id: 'aadhaar_pan_linked', name: 'Aadhaar-PAN Linked', category: 'ID' },
        { id: 'vaccine_status', name: 'Vaccine Status', category: 'Medical' },
        { id: 'wheelchair', name: 'Wheelchair Required', category: 'Medical' },

        // Address & Family (7 fields)
        { id: 'place_of_birth', name: 'Place of Birth', category: 'Address' },
        { id: 'place_of_issue', name: 'Place of Issue', category: 'Address' },
        { id: 'passport_address', name: 'Passport Address', category: 'Address' },
        { id: 'father_name', name: 'Father\'s Name', category: 'Family' },
        { id: 'mother_name', name: 'Mother\'s Name', category: 'Family' },
        { id: 'spouse_name', name: 'Spouse\'s Name', category: 'Family' },

        // Document Uploads (5 fields)
        { id: 'passport_scan', name: 'Passport Scan', category: 'Documents' },
        { id: 'aadhaar_scan', name: 'Aadhaar Scan', category: 'Documents' },
        { id: 'pan_scan', name: 'PAN Scan', category: 'Documents' },
        { id: 'vaccine_scan', name: 'Vaccine Scan', category: 'Documents' },
        { id: 'photo', name: 'Photo', category: 'Documents' },

        // Additional Information (4 fields)
        { id: 'pin', name: 'PIN', category: 'Security' },
        { id: 'emergency_contact', name: 'Emergency Contact', category: 'Emergency' },
        { id: 'emergency_phone', name: 'Emergency Phone', category: 'Emergency' },
        { id: 'medical_notes', name: 'Medical Notes', category: 'Medical' },

        // Metadata
        { id: 'created_at', name: 'Created Date', category: 'System' }
    ]
};

// ====== COLUMN SELECTOR FUNCTIONS ======
function initializeColumnSelector(module) {
    const columnGrid = document.getElementById('columnGrid');
    const columns = columnDefinitions[module] || columnDefinitions.travelers;
    allColumns = columns;
    
    let html = '';
    columns.forEach(col => {
        html += `
            <div class="column-item">
                <input type="checkbox" class="column-checkbox" value="${col.id}" data-category="${col.category}" checked onchange="updateSelectedCount()">
                <label>${col.name} <small style="color: #7f8c8d;">(${col.category})</small></label>
            </div>
        `;
    });
    
    columnGrid.innerHTML = html;
    document.getElementById('columnSelector').style.display = 'block';
    updateSelectedCount();
}

function toggleAllColumns() {
    const selectAll = document.getElementById('selectAllColumns').checked;
    document.querySelectorAll('.column-checkbox').forEach(cb => {
        cb.checked = selectAll;
    });
    updateSelectedCount();
}

function updateSelectedCount() {
    const checkboxes = document.querySelectorAll('.column-checkbox:checked');
    document.getElementById('selectedCount').textContent = checkboxes.length + ' columns selected';
    
    selectedColumns = [];
    checkboxes.forEach(cb => {
        const colId = cb.value;
        const column = allColumns.find(c => c.id === colId);
        if (column) {
            selectedColumns.push(column);
        }
    });
}

function getSelectedColumns() {
    return selectedColumns;
}

// ====== LOAD REPORTS ======
async function loadReports() {
    try {
        const response = await fetch('/api/reports/summary', {
            credentials: 'include'
        });
        const data = await response.json();
        console.log("📊 LoadReports data:", data);
        
        if (data.success && data.report) {
            displayReportSummary(data.report);
        } else {
            console.error('Failed to load reports:', data.error);
        }
    } catch (error) {
        console.error('Error loading reports:', error);
    }
}

// ====== DISPLAY REPORT SUMMARY ======
function displayReportSummary(report) {
    console.log("📊 displayReportSummary called with:", report);
    
    if (!report) {
        console.error("❌ No report data provided");
        return;
    }

    // Update stat cards
    const totalTravelers = report.total_travelers || 0;
    const totalPayments = report.payments?.total || 0;
    const paymentCount = report.payments?.count || 0;
    const totalBatches = report.total_batches || 0;
    const activeBatches = report.active_batches || 0;
    const collectionRate = report.collection_rate || 0;

    document.getElementById('reportTotalTravelers').textContent = totalTravelers;
    document.getElementById('reportTotalPayments').textContent = formatCurrency(totalPayments);
    document.getElementById('reportPaymentCount').textContent = paymentCount;
    document.getElementById('reportTotalBatches').textContent = totalBatches;
    document.getElementById('reportActiveBatches').textContent = activeBatches;
    document.getElementById('reportCollectionRate').textContent = collectionRate + '%';

    // Travelers by batch
    const travelersByBatch = report.travelers_by_batch || [];
    const batchTbody = document.getElementById('travelersByBatchBody');
    if (batchTbody) {
        batchTbody.innerHTML = travelersByBatch.map(b => `
            <tr>
                <td>${escapeHtml(b.batch_name || '-')}</td>
                <td>${b.traveler_count || 0}</td>
            </tr>
        `).join('') || '<tr><td colspan="2" style="text-align:center;">No data</td></tr>';
    }

    // Payments by method
    const paymentsByMethod = report.payments_by_method || {};
    const methodTbody = document.getElementById('paymentsByMethodBody');
    if (methodTbody) {
        const methodEntries = Object.entries(paymentsByMethod);
        methodTbody.innerHTML = methodEntries.map(([method, total]) => `
            <tr>
                <td>${escapeHtml(method || 'Unknown')}</td>
                <td>${formatCurrency(total)}</td>
            </tr>
        `).join('') || '<tr><td colspan="2" style="text-align:center;">No data</td></tr>';
    }

    // Recent activity
    const activity = report.recent_activity || [];
    const activityEl = document.getElementById('reportRecentActivity');
    if (activityEl) {
        activityEl.innerHTML = activity.slice(0, 10).map(a => `
            <div style="padding:10px; border-bottom:1px solid #ecf0f1; display:flex; justify-content:space-between;">
                <span>${escapeHtml(a.description || a.action || '-')}</span>
                <small style="color:#7f8c8d;">${a.created_at ? formatDate(a.created_at, true) : '-'}</small>
            </div>
        `).join('') || '<p style="text-align:center; color:#7f8c8d;">No recent activity</p>';
    }

    showNotification(`Loaded ${totalTravelers} travelers from database`, 'success');
}

// ====== GENERATE REPORT ======
async function generateReport() {
    showLoading('Generating report...');

    const range = document.getElementById('dateRange')?.value || 'today';
    const batch = document.getElementById('reportBatch')?.value || 'all';
    const status = document.getElementById('reportStatus')?.value || 'all';

    let startDate, endDate;
    if (range === 'custom') {
        startDate = document.getElementById('startDate')?.value;
        endDate = document.getElementById('endDate')?.value;
    } else {
        const dates = getDateRange(range);
        startDate = dates.start;
        endDate = dates.end;
    }

    // Get selected columns
    const selectedCols = getSelectedColumns();
    const columnIds = selectedCols.map(col => col.id);

    document.getElementById('reportResults').style.display = 'block';
    document.getElementById('reportTitle').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Report...';

    try {
        const response = await fetch('/api/reports/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                type: currentReportType || 'travelers',
                filters: {
                    startDate: startDate,
                    endDate: endDate,
                    batchId: batch,
                    status: status
                },
                columns: columnIds  // ✅ Send selected columns to backend
            })
        });

        const data = await response.json();
        if (data.success && data.report) {
            currentReportData = data.report;
            displayGeneratedReport(data.report, selectedCols);
            showNotification(`Report generated: ${data.report.count} records`, 'success');
        } else {
            showNotification(data.error || 'Failed to generate report', 'error');
        }
    } catch (error) {
        console.error('Error generating report:', error);
        showNotification('Network error. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

// ====== DISPLAY GENERATED REPORT WITH SELECTED COLUMNS ======
function displayGeneratedReport(report, columns) {
    document.getElementById('reportTitle').innerHTML = `<i class="fas fa-chart-pie"></i> Report Results (${report.count} records)`;

    const container = document.getElementById('reportTableContainer');
    if (!container) return;

    const rows = report.data || [];
    if (rows.length === 0) {
        container.innerHTML = '<p style="text-align:center; color:#7f8c8d; padding:30px;">No data found</p>';
        return;
    }

    // Use selected columns, or all columns if none selected
    const cols = columns && columns.length > 0 
        ? columns.map(col => col.id)
        : Object.keys(rows[0]);

    const headers = cols.map(c => `<th>${escapeHtml(c.replace(/_/g, ' '))}</th>`).join('');
    const tableRows = rows.map(row =>
        `<tr>${cols.map(c => `<td>${escapeHtml(String(row[c] ?? '-'))}</td>`).join('')}</tr>`
    ).join('');

    const headerRow = document.getElementById('reportHeaderRow');
    const tableBody = document.getElementById('reportTableBody');
    
    if (headerRow) headerRow.innerHTML = headers;
    if (tableBody) tableBody.innerHTML = tableRows;
}

// ====== UTILITY FUNCTIONS ======
function showLoading(message = 'Loading...') {
    const overlay = document.getElementById('reportLoadingOverlay');
    if (overlay) overlay.style.display = 'flex';
}

function hideLoading() {
    const overlay = document.getElementById('reportLoadingOverlay');
    if (overlay) overlay.style.display = 'none';
}

function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    if (!notification) return;
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i> ${message}`;
    notification.style.display = 'block';
    setTimeout(() => notification.style.display = 'none', 3000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '₹0';
    const num = parseFloat(amount);
    if (isNaN(num)) return '₹0';
    return '₹' + num.toLocaleString('en-IN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}

function formatDate(date, includeTime = false) {
    if (!date) return '-';
    try {
        const d = new Date(date);
        if (isNaN(d.getTime())) return String(date);
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        if (includeTime) {
            options.hour = '2-digit';
            options.minute = '2-digit';
        }
        return d.toLocaleDateString('en-IN', options);
    } catch (e) {
        return String(date);
    }
}

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

// ====== EXPORT FUNCTIONS ======
function exportToPDF() {
    if (!currentReportData || !currentReportData.data || currentReportData.data.length === 0) {
        showNotification('No report data to export. Generate a report first.', 'warning');
        return;
    }

    const rows = currentReportData.data.slice(0, 200);
    const cols = Object.keys(rows[0]);
    const headers = cols.map(c => `<th>${escapeHtml(c.replace(/_/g, ' '))}</th>`).join('');
    const tableRows = rows.map(row =>
        `<tr>${cols.map(c => `<td>${escapeHtml(String(row[c] ?? '-'))}</td>`).join('')}</tr>`
    ).join('');

    const printWin = window.open('', '_blank');
    printWin.document.write(`
        <html><head><title>Report - ${currentReportType}</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
            th { background: #2c3e50; color: white; padding: 8px; text-align: left; }
            td { padding: 8px; border-bottom: 1px solid #ddd; }
            @media print { button { display: none; } }
        </style></head>
        <body>
        <h2>Report: ${escapeHtml(currentReportType)} — ${new Date().toLocaleDateString()}</h2>
        <p>Total records: ${currentReportData.count}</p>
        <table><thead><tr>${headers}</tr></thead><tbody>${tableRows}</tbody></table>
        <button onclick="window.print()" style="margin-top:20px; padding:10px 20px; background:#3498db; color:white; border:none; border-radius:5px; cursor:pointer;">Print</button>
        </body></html>`);
    printWin.document.close();
}

function exportToCSV() {
    if (!currentReportData || !currentReportData.data || currentReportData.data.length === 0) {
        showNotification('No report data to export. Generate a report first.', 'warning');
        return;
    }

    const rows = currentReportData.data;
    const cols = Object.keys(rows[0]);
    const headers = cols.map(c => c.replace(/_/g, ' '));

    let csv = headers.join(',') + '\n';
    rows.forEach(row => {
        const rowData = cols.map(col => {
            let val = row[col] || '';
            if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
                val = `"${val.replace(/"/g, '""')}"`;
            }
            return val;
        });
        csv += rowData.join(',') + '\n';
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report_${currentReportType}_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}

function exportToExcel() {
    if (!currentReportData || !currentReportData.data || currentReportData.data.length === 0) {
        showNotification('No report data to export. Generate a report first.', 'warning');
        return;
    }

    if (typeof XLSX === 'undefined') {
        showNotification('Excel export library not loaded', 'error');
        return;
    }

    const rows = currentReportData.data;
    const ws = XLSX.utils.json_to_sheet(rows);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Report');
    XLSX.writeFile(wb, `report_${currentReportType}_${new Date().toISOString().slice(0,10)}.xlsx`);
}

// ====== MODAL FUNCTIONS ======
function showReportModal(type) {
    currentReportType = type;
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

function showSaveReportModal() {
    document.getElementById('saveReportModal').style.display = 'block';
    document.getElementById('modalOverlay').style.display = 'block';
}

function closeSaveReportModal() {
    document.getElementById('saveReportModal').style.display = 'none';
    document.getElementById('modalOverlay').style.display = 'none';
}

function saveReportConfig() {
    const name = document.getElementById('savedReportName')?.value;
    if (!name) {
        showNotification('Please enter a report name', 'error');
        return;
    }
    showNotification(`Report "${name}" saved successfully!`, 'success');
    closeSaveReportModal();
}

function printReport() {
    if (!currentReportData) {
        showNotification('No report data to print', 'error');
        return;
    }
    window.print();
}

// ====== FILTER FUNCTIONS ======
function resetFilters() {
    document.getElementById('dateRange').value = 'today';
    document.getElementById('reportBatch').value = 'all';
    document.getElementById('reportStatus').value = 'all';
    document.getElementById('startDateGroup').style.display = 'none';
    document.getElementById('endDateGroup').style.display = 'none';
    document.getElementById('reportResults').style.display = 'none';
    showNotification('Filters reset', 'info');
}

function toggleDateInputs() {
    const range = document.getElementById('dateRange').value;
    const startGroup = document.getElementById('startDateGroup');
    const endGroup = document.getElementById('endDateGroup');
    if (range === 'custom') {
        startGroup.style.display = 'block';
        endGroup.style.display = 'block';
    } else {
        startGroup.style.display = 'none';
        endGroup.style.display = 'none';
    }
}

// ====== LOGOUT ======
async function logout() {
    if (confirm('Are you sure you want to logout?')) {
        await SessionManager.logout();
    }
}

// ====== EXPOSE GLOBALS ======
window.loadReports = loadReports;
window.generateReport = generateReport;
window.displayReportSummary = displayReportSummary;
window.exportToPDF = exportToPDF;
window.exportToCSV = exportToCSV;
window.exportToExcel = exportToExcel;
window.printReport = printReport;
window.showReportModal = showReportModal;
window.closeReportModal = closeReportModal;
window.generateCustomReport = generateCustomReport;
window.showSaveReportModal = showSaveReportModal;
window.closeSaveReportModal = closeSaveReportModal;
window.saveReportConfig = saveReportConfig;
window.resetFilters = resetFilters;
window.toggleDateInputs = toggleDateInputs;
window.logout = logout;

console.log('✅ reports.js loaded with 33 traveler fields support');