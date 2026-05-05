/**
 * reports.js - Report generation and management functions
 * Alhudha Haj Travel Admin Panel
 */

'use strict';

// ====== STATE ======
let reportsData = [];
let reportsCurrentData = null;
let reportsCurrentType = 'travelers';
let reportsChartInstances = {};

// ====== LOAD REPORTS ======
/**
 * Fetch saved reports from /api/reports
 */
async function loadReports() {
    try {
        const data = await makeAPICall('GET', '/api/reports');
        if (data.success && Array.isArray(data.reports)) {
            reportsData = data.reports;
            console.log(`✅ Loaded ${reportsData.length} saved reports`);
        } else {
            reportsData = [];
        }
    } catch (error) {
        // Reports endpoint may not exist - use local storage fallback
        reportsData = JSON.parse(localStorage.getItem('savedReports') || '[]');
        console.log('ℹ️ Using local saved reports');
    }
}

// ====== GENERATE REPORT ======
/**
 * Generate a report based on current filter settings
 */
async function generateReport() {
    const range = document.getElementById('dateRange')?.value || 'today';
    const batch = document.getElementById('reportBatch')?.value || 'all';
    const status = document.getElementById('reportStatus')?.value || 'all';

    let startDate = null;
    let endDate = null;

    if (range === 'custom') {
        startDate = document.getElementById('startDate')?.value;
        endDate = document.getElementById('endDate')?.value;
        if (!startDate || !endDate) {
            showNotification('Please select start and end dates', 'error'); return;
        }
    } else {
        const dates = getReportDateRange(range);
        startDate = dates.start;
        endDate = dates.end;
    }

    const loadingOverlay = document.getElementById('reportLoadingOverlay');
    if (loadingOverlay) loadingOverlay.style.display = 'flex';

    try {
        const params = new URLSearchParams({
            start_date: startDate,
            end_date: endDate,
            batch_id: batch,
            status: status
        });

        const data = await makeAPICall('GET', `/api/reports/generate?${params}`);
        if (data.success) {
            reportsCurrentData = data;
            displayReport(data);
            showNotification('Report generated successfully!', 'success');
        } else {
            showDemoReport();
        }
    } catch (error) {
        console.warn('Report API not available, showing demo data');
        showDemoReport();
    } finally {
        if (loadingOverlay) loadingOverlay.style.display = 'none';
    }
}

// ====== FILTER REPORTS ======
/**
 * Filter reports by type and date range
 */
function filterReports() {
    const type = document.getElementById('reportType')?.value || 'all';
    const fromDate = document.getElementById('reportFromDate')?.value;
    const toDate = document.getElementById('reportToDate')?.value;

    let filtered = [...reportsData];

    if (type !== 'all') {
        filtered = filtered.filter(r => r.type === type);
    }
    if (fromDate) {
        filtered = filtered.filter(r => new Date(r.created_at) >= new Date(fromDate));
    }
    if (toDate) {
        filtered = filtered.filter(r => new Date(r.created_at) <= new Date(toDate + 'T23:59:59'));
    }

    showNotification(`Found ${filtered.length} report(s)`, 'info');
    return filtered;
}

// ====== EXPORT REPORT TO CSV ======
/**
 * Export the current report data to CSV
 */
function exportReportToCSV() {
    if (!reportsCurrentData) {
        showNotification('Please generate a report first', 'warning'); return;
    }

    const rows = reportsCurrentData.rows || reportsCurrentData.data || [];
    if (!rows.length) { showNotification('No data to export', 'warning'); return; }

    const headers = Object.keys(rows[0]);
    const csvRows = [headers, ...rows.map(row => headers.map(h => row[h]))];

    downloadCSV(csvRows, `report_${new Date().toISOString().slice(0, 10)}.csv`);
    showNotification('Report exported to CSV', 'success');
}

// ====== EXPORT REPORT TO PDF ======
/**
 * Export the current report to PDF via print dialog
 */
function exportReportToPDF() {
    if (!reportsCurrentData) {
        showNotification('Please generate a report first', 'warning'); return;
    }

    const content = document.getElementById('reportResults')?.innerHTML;
    if (!content) { showNotification('No report content to export', 'warning'); return; }

    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html><head><title>Report - ${new Date().toLocaleDateString()}</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            table { width: 100%; border-collapse: collapse; }
            th { background: #2c3e50; color: white; padding: 10px; }
            td { padding: 8px; border: 1px solid #ddd; }
            .stat-card { display: inline-block; padding: 15px; margin: 10px; background: #f8f9fa; border-radius: 5px; }
        </style></head>
        <body>
            <h1>Alhudha Haj Travel - Report</h1>
            <p>Generated: ${new Date().toLocaleString()}</p>
            ${content}
        </body></html>`);
    printWindow.document.close();
    printWindow.print();
    showNotification('PDF export initiated', 'success');
}

// ====== VIEW REPORT DETAILS ======
/**
 * View details of a saved report
 * @param {number} id
 */
function viewReportDetails(id) {
    const report = reportsData.find(r => r.id === id);
    if (!report) { showNotification('Report not found', 'error'); return; }

    showModal(
        `<i class="fas fa-chart-bar"></i> ${escapeHtml(report.name || 'Report')}`,
        `<div style="padding:15px;">
            <p><strong>Type:</strong> ${escapeHtml(report.type || '-')}</p>
            <p><strong>Created:</strong> ${formatDate(report.created_at)}</p>
            <p><strong>Description:</strong> ${escapeHtml(report.description || 'No description')}</p>
            ${report.schedule && report.schedule !== 'none' ? `<p><strong>Schedule:</strong> ${escapeHtml(report.schedule)}</p>` : ''}
        </div>`,
        `<button class="action-btn btn-primary" onclick="loadSavedReport(${id})">Load Report</button>
         <button class="action-btn btn-secondary" onclick="closeModal()">Close</button>`
    );
}

// ====== SCHEDULE REPORT ======
/**
 * Schedule automatic report generation
 */
function scheduleReport() {
    const name = document.getElementById('savedReportName')?.value?.trim();
    const schedule = document.getElementById('reportSchedule')?.value;

    if (!name) { showNotification('Please enter a report name', 'error'); return; }
    if (!schedule || schedule === 'none') {
        showNotification('Please select a schedule', 'error'); return;
    }

    const reportConfig = {
        id: Date.now(),
        name: name,
        type: reportsCurrentType,
        schedule: schedule,
        description: document.getElementById('savedReportDesc')?.value?.trim(),
        email: document.getElementById('reportEmail')?.value?.trim(),
        createdAt: new Date().toISOString()
    };

    const saved = JSON.parse(localStorage.getItem('savedReports') || '[]');
    saved.push(reportConfig);
    localStorage.setItem('savedReports', JSON.stringify(saved));
    reportsData = saved;

    showNotification(`Report "${name}" scheduled for ${schedule} generation`, 'success');
    if (typeof closeSaveReportModal === 'function') closeSaveReportModal();
}

// ====== DISPLAY REPORT ======
function displayReport(data) {
    reportsCurrentData = data;

    const resultsEl = document.getElementById('reportResults');
    if (resultsEl) resultsEl.style.display = 'block';

    // Update summary cards
    const summary = data.summary || {};
    const summaryEl = document.getElementById('reportSummary');
    if (summaryEl) {
        summaryEl.innerHTML = `
            <div class="stat-card"><i class="fas fa-users"></i><h3>Total Travelers</h3><div class="stat-number">${summary.totalTravelers || 0}</div></div>
            <div class="stat-card"><i class="fas fa-layer-group"></i><h3>Active Batches</h3><div class="stat-number">${summary.activeBatches || 0}</div></div>
            <div class="stat-card"><i class="fas fa-rupee-sign"></i><h3>Total Collections</h3><div class="stat-number">${formatCurrency(summary.totalCollections || 0)}</div></div>
            <div class="stat-card"><i class="fas fa-clock"></i><h3>Pending Payments</h3><div class="stat-number">${formatCurrency(summary.pendingPayments || 0)}</div></div>
        `;
    }

    // Populate table
    const rows = data.rows || data.data || data.travelers || data.payments || [];
    if (rows.length > 0) {
        const headerRow = document.getElementById('reportHeaderRow');
        const tableBody = document.getElementById('reportTableBody');

        if (headerRow && tableBody) {
            const cols = Object.keys(rows[0]);
            headerRow.innerHTML = cols.map(c => `<th>${escapeHtml(c.replace(/_/g, ' ').toUpperCase())}</th>`).join('');
            tableBody.innerHTML = rows.map(row =>
                `<tr>${cols.map(c => `<td>${escapeHtml(row[c] !== null && row[c] !== undefined ? String(row[c]) : '-')}</td>`).join('')}</tr>`
            ).join('');
        }
    }

    // Initialize charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        initReportCharts(data);
    }
}

// ====== DEMO REPORT ======
function showDemoReport() {
    const demoData = {
        summary: {
            totalTravelers: 156,
            activeBatches: 3,
            totalCollections: 12500000,
            pendingPayments: 2300000
        },
        rows: [
            { name: 'Ahmed Khan', batch: 'Haj Platinum 2026', status: 'Active', amount: 850000 },
            { name: 'Fatima Begum', batch: 'Haj Gold 2026', status: 'Active', amount: 550000 },
            { name: 'Mohammed Rafiq', batch: 'Umrah Ramadhan', status: 'Pending', amount: 125000 }
        ]
    };
    displayReport(demoData);
    showNotification('Showing demo report data', 'info');
}

// ====== CHART INITIALIZATION ======
function initReportCharts(data) {
    try {
        const paymentsCtx = document.getElementById('paymentsChart')?.getContext('2d');
        const travelersCtx = document.getElementById('travelersChart')?.getContext('2d');

        if (reportsChartInstances.payments) reportsChartInstances.payments.destroy();
        if (reportsChartInstances.travelers) reportsChartInstances.travelers.destroy();

        if (paymentsCtx) {
            reportsChartInstances.payments = new Chart(paymentsCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Cash', 'Bank Transfer', 'UPI', 'Cheque'],
                    datasets: [{ data: [40, 30, 20, 10], backgroundColor: ['#3498db', '#27ae60', '#f39c12', '#e74c3c'] }]
                },
                options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
            });
        }

        if (travelersCtx) {
            const batches = data.batchDistribution || [
                { name: 'Haj Platinum', count: 50 },
                { name: 'Haj Gold', count: 82 },
                { name: 'Umrah', count: 24 }
            ];
            reportsChartInstances.travelers = new Chart(travelersCtx, {
                type: 'bar',
                data: {
                    labels: batches.map(b => b.name),
                    datasets: [{ label: 'Travelers', data: batches.map(b => b.count), backgroundColor: '#3498db' }]
                },
                options: { responsive: true, plugins: { legend: { display: false } } }
            });
        }
    } catch (e) {
        console.warn('Chart initialization failed:', e);
    }
}

// ====== DATE RANGE HELPER ======
function getReportDateRange(range) {
    const today = new Date();
    const pad = n => String(n).padStart(2, '0');
    const fmt = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

    switch (range) {
        case 'today': return { start: fmt(today), end: fmt(today) };
        case 'yesterday': {
            const y = new Date(today); y.setDate(y.getDate() - 1);
            return { start: fmt(y), end: fmt(y) };
        }
        case 'thisweek': {
            const start = new Date(today); start.setDate(today.getDate() - today.getDay());
            return { start: fmt(start), end: fmt(today) };
        }
        case 'thismonth': {
            const start = new Date(today.getFullYear(), today.getMonth(), 1);
            return { start: fmt(start), end: fmt(today) };
        }
        case 'lastmonth': {
            const start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            const end = new Date(today.getFullYear(), today.getMonth(), 0);
            return { start: fmt(start), end: fmt(end) };
        }
        case 'thisyear': {
            const start = new Date(today.getFullYear(), 0, 1);
            return { start: fmt(start), end: fmt(today) };
        }
        default: return { start: fmt(today), end: fmt(today) };
    }
}

console.log('✅ reports.js loaded');
