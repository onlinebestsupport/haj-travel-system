'use strict';

// ====== STATE ======
let currentReportData = null;
let currentReportType = 'travelers';

// 33 TRAVELER FIELDS IN EXACT ORDER AS TRAVELERS.HTML MODULE
const TRAVELERS_COLUMNS = [
    { name: 'id', label: 'ID', type: 'number' },
    { name: 'first_name', label: 'First Name', type: 'text' },
    { name: 'last_name', label: 'Last Name', type: 'text' },
    { name: 'passport_name', label: 'Passport Name', type: 'text' },
    { name: 'batch_id', label: 'Batch ID', type: 'number' },
    { name: 'batch_name', label: 'Batch Name', type: 'text' },
    { name: 'passport_no', label: 'Passport Number', type: 'text' },
    { name: 'passport_issue_date', label: 'Passport Issue Date', type: 'date' },
    { name: 'passport_expiry_date', label: 'Passport Expiry Date', type: 'date' },
    { name: 'passport_status', label: 'Passport Status', type: 'text' },
    { name: 'gender', label: 'Gender', type: 'text' },
    { name: 'dob', label: 'Date of Birth', type: 'date' },
    { name: 'mobile', label: 'Mobile', type: 'text' },
    { name: 'email', label: 'Email', type: 'text' },
    { name: 'aadhaar', label: 'Aadhaar', type: 'text' },
    { name: 'pan', label: 'PAN', type: 'text' },
    { name: 'aadhaar_pan_linked', label: 'Aadhaar-PAN Linked', type: 'text' },
    { name: 'vaccine_status', label: 'Vaccine Status', type: 'text' },
    { name: 'wheelchair', label: 'Wheelchair', type: 'text' },
    { name: 'place_of_birth', label: 'Place of Birth', type: 'text' },
    { name: 'place_of_issue', label: 'Place of Issue', type: 'text' },
    { name: 'passport_address', label: 'Passport Address', type: 'text' },
    { name: 'father_name', label: "Father's Name", type: 'text' },
    { name: 'mother_name', label: "Mother's Name", type: 'text' },
    { name: 'spouse_name', label: "Spouse's Name", type: 'text' },
    { name: 'pin', label: 'PIN', type: 'text' },
    { name: 'emergency_contact', label: 'Emergency Contact', type: 'text' },
    { name: 'emergency_phone', label: 'Emergency Phone', type: 'text' },
    { name: 'medical_notes', label: 'Medical Notes', type: 'text' },
    { name: 'passport_scan', label: 'Passport Scan', type: 'text' },
    { name: 'aadhaar_scan', label: 'Aadhaar Scan', type: 'text' },
    { name: 'pan_scan', label: 'PAN Scan', type: 'text' },
    { name: 'vaccine_scan', label: 'Vaccine Scan', type: 'text' },
    { name: 'photo', label: 'Photo', type: 'text' },
    { name: 'created_at', label: 'Created At', type: 'datetime' }
];

document.addEventListener('DOMContentLoaded', function() {
    console.log("✅ reports.js loaded");
    // Verify XLSX is available
    setTimeout(() => {
        if (typeof XLSX !== 'undefined') {
            console.log("✅ XLSX library confirmed loaded");
        } else {
            console.error("❌ XLSX library not loaded");
        }
    }, 500);
    loadReports();
});

function initializeReports() {
    populateColumnSelector();
    loadBatchesForFilters();
}

// ====== POPULATE COLUMN SELECTOR ======
function populateColumnSelector() {
    const columnGrid = document.getElementById('columnGrid');
    if (!columnGrid) return;
    
    columnGrid.innerHTML = TRAVELERS_COLUMNS.map(col => `
        <div class="column-item">
            <input type="checkbox" class="column-checkbox" value="${col.name}" checked>
            <label>${col.label}</label>
        </div>
    `).join('');
    
    // Add event listener to update count
    document.querySelectorAll('.column-checkbox').forEach(cb => {
        cb.addEventListener('change', updateSelectedCount);
    });
    
    updateSelectedCount();
}

function updateSelectedCount() {
    const count = document.querySelectorAll('.column-checkbox:checked').length;
    const el = document.getElementById('selectedCount');
    if (el) el.textContent = count + ' columns selected';
}

function toggleAllColumns() {
    const selectAll = document.getElementById('selectAllColumns').checked;
    document.querySelectorAll('.column-checkbox').forEach(cb => {
        cb.checked = selectAll;
    });
    updateSelectedCount();
}

// ====== LOAD REPORTS ======
async function loadReports() {
    try {
        const response = await fetch('/api/reports/summary', { credentials: 'include' });
        const data = await response.json();
        console.log("📊 LoadReports data:", data);
        
        if (data.success && data.report) {
            displayReportSummary(data.report);
            initializeReports();
        } else {
            console.error('Failed to load reports:', data.error);
            initializeReports();
        }
    } catch (error) {
        console.error('Error loading reports:', error);
        initializeReports();
    }
}

// ====== DISPLAY REPORT SUMMARY ======
function displayReportSummary(report) {
    console.log("📊 displayReportSummary called with:", report);
    
    if (!report) {
        console.error("❌ No report data provided");
        return;
    }

    const totalTravelers = report.total_travelers || 0;
    const totalPayments = report.payments?.total || 0;
    const totalBatches = report.total_batches || 0;
    const collectionRate = report.collection_rate || 0;

    document.getElementById('reportTotalTravelers').textContent = totalTravelers;
    document.getElementById('reportTotalPayments').textContent = formatCurrency(totalPayments);
    document.getElementById('reportTotalBatches').textContent = totalBatches;
    document.getElementById('reportCollectionRate').textContent = collectionRate + '%';
}

// ====== LOAD BATCHES FOR FILTERS ======
async function loadBatchesForFilters() {
    try {
        const response = await fetch('/api/batches', { credentials: 'include' });
        const data = await response.json();
        if (data.success && Array.isArray(data.batches)) {
            const batchSelect = document.getElementById('reportBatch');
            if (batchSelect) {
                data.batches.forEach(batch => {
                    const option = document.createElement('option');
                    option.value = batch.id;
                    option.textContent = batch.batch_name || `Batch ${batch.id}`;
                    batchSelect.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.warn('Could not load batches:', error.message);
    }
}

// ====== SET REPORT TYPE ======
function setReportType(type) {
    currentReportType = type;
}

// ====== SHOW REPORT MODAL ======
function showReportModal() {
    document.getElementById('reportModal').style.display = 'block';
    document.getElementById('modalOverlay').style.display = 'block';
    document.getElementById('columnSelector').style.display = currentReportType === 'travelers' ? 'block' : 'none';
}

function closeReportModal() {
    document.getElementById('reportModal').style.display = 'none';
    document.getElementById('modalOverlay').style.display = 'none';
}

// ====== GENERATE CUSTOM REPORT ======
function generateCustomReport() {
    closeReportModal();
    generateReport();
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

    // Get selected columns for travelers report
    let selectedColumns = [];
    if (currentReportType === 'travelers') {
        selectedColumns = Array.from(document.querySelectorAll('.column-checkbox:checked'))
            .map(cb => cb.value);
        if (selectedColumns.length === 0) {
            showNotification('Please select at least one column', 'warning');
            hideLoading();
            return;
        }
    }

    document.getElementById('reportResults').style.display = 'block';
    document.getElementById('reportTitle').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Report...';

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
                },
                columns: selectedColumns
            })
        });

        const data = await response.json();
        if (data.success && data.report) {
            currentReportData = data.report;
            displayGeneratedReport(data.report, selectedColumns);
            showNotification(`Report generated: ${data.report.count} records`, 'success');
        } else {
            showNotification(data.error || 'Failed to generate report', 'error');
            document.getElementById('reportResults').style.display = 'none';
        }
    } catch (error) {
        console.error('Error generating report:', error);
        showNotification('Network error. Please try again.', 'error');
        document.getElementById('reportResults').style.display = 'none';
    } finally {
        hideLoading();
    }
}

// ====== DISPLAY GENERATED REPORT ======
function displayGeneratedReport(report, selectedColumns) {
    document.getElementById('reportTitle').innerHTML = `<i class="fas fa-chart-pie"></i> Report Results (${report.count} records)`;

    const rows = report.data || [];
    if (rows.length === 0) {
        document.getElementById('reportTableBody').innerHTML = '<tr><td colspan="10" style="text-align:center; padding:30px;">No data found</td></tr>';
        return;
    }

    // ✅ MAINTAIN COLUMN ORDER FROM TRAVELERS_COLUMNS
    // Only include selected columns in the original order
    const orderedCols = TRAVELERS_COLUMNS
        .filter(col => selectedColumns.includes(col.name))
        .map(col => col.name);

    const headerRow = document.getElementById('reportHeaderRow');
    headerRow.innerHTML = orderedCols.map(c => {
        const colDef = TRAVELERS_COLUMNS.find(col => col.name === c);
        const label = colDef ? colDef.label : c.replace(/_/g, ' ');
        return `<th>${escapeHtml(label)}</th>`;
    }).join('');

    const tableBody = document.getElementById('reportTableBody');
    tableBody.innerHTML = rows.map(row =>
        `<tr>${orderedCols.map(c => `<td>${escapeHtml(String(row[c] ?? '-'))}</td>`).join('')}</tr>`
    ).join('');
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
        showNotification('No report data to export', 'warning');
        return;
    }

    const rows = currentReportData.data.slice(0, 500);
    const selectedColumns = Array.from(document.querySelectorAll('.column-checkbox:checked'))
        .map(cb => cb.value);
    const orderedCols = TRAVELERS_COLUMNS
        .filter(col => selectedColumns.includes(col.name))
        .map(col => col.name);
    
    const headers = orderedCols.map(c => {
        const colDef = TRAVELERS_COLUMNS.find(col => col.name === c);
        return `<th>${escapeHtml(colDef ? colDef.label : c.replace(/_/g, ' '))}</th>`;
    }).join('');
    
    const tableRows = rows.map(row =>
        `<tr>${orderedCols.map(c => `<td>${escapeHtml(String(row[c] ?? '-'))}</td>`).join('')}</tr>`
    ).join('');

    const printWin = window.open('', '_blank');
    printWin.document.write(`
        <html><head><title>Report</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
            th { background: #2c3e50; color: white; padding: 8px; text-align: left; }
            td { padding: 8px; border-bottom: 1px solid #ddd; }
        </style></head>
        <body>
        <h2>Report: ${currentReportType} — ${new Date().toLocaleDateString()}</h2>
        <p>Total records: ${currentReportData.count}</p>
        <table><thead><tr>${headers}</tr></thead><tbody>${tableRows}</tbody></table>
        </body></html>`);
    printWin.document.close();
    printWin.print();
}

function exportToCSV() {
    if (!currentReportData || !currentReportData.data || currentReportData.data.length === 0) {
        showNotification('No report data to export', 'warning');
        return;
    }

    const rows = currentReportData.data;
    const selectedColumns = Array.from(document.querySelectorAll('.column-checkbox:checked'))
        .map(cb => cb.value);
    const orderedCols = TRAVELERS_COLUMNS
        .filter(col => selectedColumns.includes(col.name))
        .map(col => col.name);
    
    const headers = orderedCols.map(c => {
        const colDef = TRAVELERS_COLUMNS.find(col => col.name === c);
        return colDef ? colDef.label : c.replace(/_/g, ' ');
    });

    let csv = headers.join(',') + '\n';
    rows.forEach(row => {
        const rowData = orderedCols.map(col => {
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
    showNotification(`Exported ${rows.length} records to CSV`, 'success');
}

function exportToExcel() {
    if (!currentReportData || !currentReportData.data || currentReportData.data.length === 0) {
        showNotification('No report data to export', 'warning');
        return;
    }

    // Verify XLSX library is available
    if (typeof XLSX === 'undefined') {
        console.error('XLSX not loaded. Attempting fallback to CSV...');
        showNotification('Excel library loading... trying CSV export', 'warning');
        setTimeout(() => exportToCSV(), 500);
        return;
    }

    try {
        const rows = currentReportData.data;
        const selectedColumns = Array.from(document.querySelectorAll('.column-checkbox:checked'))
            .map(cb => cb.value);
        const orderedCols = TRAVELERS_COLUMNS
            .filter(col => selectedColumns.includes(col.name))
            .map(col => col.name);
        
        // Reorder data rows to match column order
        const reorderedRows = rows.map(row => {
            const newRow = {};
            orderedCols.forEach(col => {
                const colDef = TRAVELERS_COLUMNS.find(c => c.name === col);
                const label = colDef ? colDef.label : col.replace(/_/g, ' ');
                newRow[label] = row[col];
            });
            return newRow;
        });
        
        const ws = XLSX.utils.json_to_sheet(reorderedRows);
        const colWidths = orderedCols.map(key => ({
            wch: Math.min(25, Math.max(key.length, 12))
        }));
        ws['!cols'] = colWidths;
        
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Report');
        XLSX.writeFile(wb, `report_${currentReportType}_${new Date().toISOString().slice(0,10)}.xlsx`);
        showNotification(`Exported ${rows.length} records to Excel`, 'success');
    } catch (error) {
        console.error('Excel export error:', error);
        showNotification('Excel export failed. Using CSV instead.', 'warning');
        exportToCSV();
    }
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
        if (typeof SessionManager !== 'undefined' && SessionManager.logout) {
            await SessionManager.logout();
        } else {
            window.location.href = '/logout';
        }
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
window.resetFilters = resetFilters;
window.toggleDateInputs = toggleDateInputs;
window.logout = logout;
window.setReportType = setReportType;
window.toggleAllColumns = toggleAllColumns;
window.updateSelectedCount = updateSelectedCount;

console.log('✅ reports.js loaded');