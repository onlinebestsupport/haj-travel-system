/**
 * reports.js - Report generation and management functions
 * Alhudha Haj Travel Management System
 * reports.js - Reports Management for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 * API base: /api/reports
 */

'use strict';

// Module-level state
let reportsData = [];
let currentReportData = null;
let currentReportType = null;

// ====== LOAD REPORTS ======
/**
 * Fetch available reports from the API
 */
async function loadReports() {
    showLoading(true);
    try {
        const data = await makeApiCall('GET', '/api/reports');
        reportsData = Array.isArray(data) ? data : (data.reports || []);
        console.log(`✅ Loaded ${reportsData.length} reports`);

        const container = document.getElementById('savedReportsList');
        if (container) {
            if (reportsData.length === 0) {
                container.innerHTML = '<p style="color:#95a5a6;text-align:center;padding:20px;">No saved reports found</p>';
            } else {
                container.innerHTML = reportsData.map(r => `
                    <div style="background:white;padding:15px;border-radius:8px;margin-bottom:10px;box-shadow:0 2px 8px rgba(0,0,0,0.05);display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <strong>${escapeHtml(r.name || r.report_type || 'Report')}</strong>
                            <div style="font-size:0.85rem;color:#95a5a6;">${formatDate(r.created_at)} — ${escapeHtml(r.report_type || '')}</div>
                        </div>
                        <div style="display:flex;gap:8px;">
                            <button class="icon-btn btn-view" onclick="viewReportDetails(${r.id})" title="View"><i class="fas fa-eye"></i></button>
                            <button class="icon-btn" onclick="exportReportToCSV(${r.id})" title="Export CSV" style="color:#27ae60;"><i class="fas fa-file-csv"></i></button>
                            <button class="icon-btn" onclick="exportReportToPDF(${r.id})" title="Export PDF" style="color:#e74c3c;"><i class="fas fa-file-pdf"></i></button>
                        </div>
                    </div>`).join('');
            }
        }
    } catch (error) {
        handleApiError(error, 'Load reports');
    } finally {
        showLoading(false);
    }
}

// ====== GENERATE REPORT ======
/**
 * Generate a custom report based on type and filters
 * @param {string} reportType - 'travelers' | 'payments' | 'invoices' | 'batches' | 'financial'
 * @param {Object} filters    - { startDate, endDate, batchId, status, ... }
 */
async function generateReport(reportType, filters = {}) {
    if (!reportType) {
        const typeEl = document.getElementById('reportType') || document.getElementById('reportTypeSelect');
        reportType = typeEl ? typeEl.value : '';
    }

    if (!reportType) {
        showNotification('Please select a report type', 'error');
        return;
    }

    // Collect filters from form if not provided
    if (!filters.startDate) {
        const startEl = document.getElementById('reportStartDate') || document.getElementById('startDate');
        if (startEl) filters.startDate = startEl.value;
    }
    if (!filters.endDate) {
        const endEl = document.getElementById('reportEndDate') || document.getElementById('endDate');
        if (endEl) filters.endDate = endEl.value;
    }
    if (!filters.batchId) {
        const batchEl = document.getElementById('reportBatch') || document.getElementById('filterBatch');
        if (batchEl) filters.batchId = batchEl.value;
    }

    showLoading(true);
    try {
        const params = new URLSearchParams({ type: reportType, ...filters });
        const data   = await makeApiCall('GET', `/api/reports/generate?${params}`);

        currentReportData = data;
        currentReportType = reportType;

        renderReportResults(data, reportType);
        showNotification(`${reportType} report generated successfully!`, 'success');
    } catch (error) {
        handleApiError(error, 'Generate report');
    } finally {
        showLoading(false);
    }
}

/**
 * Render report results into the results container
 * @param {Object} data
 * @param {string} reportType
 */
function renderReportResults(data, reportType) {
    const container = document.getElementById('reportResults') || document.getElementById('reportOutput');
    if (!container) return;

    const rows = Array.isArray(data) ? data : (data.rows || data.data || data.results || []);

    if (rows.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:#95a5a6;padding:30px;">No data found for the selected filters.</p>';
        return;
    }

    const headers = Object.keys(rows[0]);
    const tableHtml = `
        <div style="margin-bottom:15px;display:flex;justify-content:space-between;align-items:center;">
            <strong>${rows.length} records found</strong>
            <div style="display:flex;gap:10px;">
                <button class="action-btn btn-success" onclick="exportReportToCSV(null)" style="padding:8px 15px;font-size:0.85rem;">
                    <i class="fas fa-file-csv"></i> Export CSV
                </button>
                <button class="action-btn btn-danger" onclick="exportReportToPDF(null)" style="padding:8px 15px;font-size:0.85rem;">
                    <i class="fas fa-file-pdf"></i> Export PDF
                </button>
            </div>
        </div>
        <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;">
                <thead>
                    <tr>${headers.map(h => `<th style="background:#2c3e50;color:white;padding:10px;text-align:left;">${escapeHtml(h.replace(/_/g,' '))}</th>`).join('')}</tr>
                </thead>
                <tbody>
                    ${rows.map(row => `
                        <tr style="border-bottom:1px solid #ecf0f1;">
                            ${headers.map(h => `<td style="padding:10px;">${escapeHtml(String(row[h] || '-'))}</td>`).join('')}
                        </tr>`).join('')}
                </tbody>
            </table>
        </div>`;

    container.innerHTML = tableHtml;
    container.style.display = 'block';
}

// ====== FILTER REPORTS ======
/**
 * Filter reports by date range, type, or traveler
 */
function filterReports() {
    const typeEl  = document.getElementById('reportType') || document.getElementById('reportTypeSelect');
    const startEl = document.getElementById('reportStartDate') || document.getElementById('startDate');
    const endEl   = document.getElementById('reportEndDate')   || document.getElementById('endDate');

    const filters = {
        type:      typeEl  ? typeEl.value  : '',
        startDate: startEl ? startEl.value : '',
        endDate:   endEl   ? endEl.value   : ''
    };

    if (filters.type) {
        generateReport(filters.type, filters);
    } else {
        showNotification('Please select a report type to filter', 'warning');
    }
}

// ====== EXPORT REPORT TO CSV ======
/**
 * Export a report to CSV
 * @param {number|null} reportId - null to export current report data
 */
async function exportReportToCSV(reportId) {
    let data;

    if (reportId !== null) {
        showLoading(true);
        try {
            const response = await makeApiCall('GET', `/api/reports/${reportId}`);
            data = Array.isArray(response) ? response : (response.rows || response.data || []);
        } catch (error) {
            handleApiError(error, 'Load report for export');
            showLoading(false);
            return;
        } finally {
            showLoading(false);
        }
    } else {
        data = currentReportData;
        if (data && !Array.isArray(data)) {
            data = data.rows || data.data || data.results || [];
        }
    }

    if (!data || data.length === 0) {
        showNotification('No report data to export', 'warning');
        return;
    }

    const headers = Object.keys(data[0]);
    const rows    = data.map(row =>
        headers.map(h => `"${String(row[h] || '').replace(/"/g, '""')}"`).join(',')
    );

    const csv  = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href     = url;
    link.download = `report_${currentReportType || 'export'}_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    showNotification(`Report exported to CSV (${data.length} rows)`, 'success');
}

// ====== EXPORT REPORT TO PDF ======
/**
 * Export a report to a printable PDF page
 * @param {number|null} reportId - null to export current report data
 */
async function exportReportToPDF(reportId) {
    let data;

    if (reportId !== null) {
        showLoading(true);
        try {
            const response = await makeApiCall('GET', `/api/reports/${reportId}`);
            data = Array.isArray(response) ? response : (response.rows || response.data || []);
        } catch (error) {
            handleApiError(error, 'Load report for PDF export');
            showLoading(false);
            return;
        } finally {
            showLoading(false);
        }
    } else {
        data = currentReportData;
        if (data && !Array.isArray(data)) {
            data = data.rows || data.data || data.results || [];
        }
    }

    if (!data || data.length === 0) {
        showNotification('No report data to export', 'warning');
        return;
    }

    const headers = Object.keys(data[0]);
    const rows    = data.map(row =>
        `<tr>${headers.map(h => `<td style="padding:8px;border-bottom:1px solid #ecf0f1;">${escapeHtml(String(row[h] || '-'))}</td>`).join('')}</tr>`
    ).join('');

    const html = `
        <!DOCTYPE html><html><head>
        <title>Report Export</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; font-size: 12px; }
            h1 { color: #2c3e50; font-size: 1.2rem; }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            th { background: #2c3e50; color: white; padding: 8px; text-align: left; font-size: 11px; }
            td { padding: 6px 8px; border-bottom: 1px solid #ecf0f1; }
            tr:nth-child(even) { background: #f8f9fa; }
            .footer { margin-top: 15px; color: #95a5a6; font-size: 10px; }
        </style></head><body>
        <h1>&#x1F54B; Alhudha Haj Travel — ${escapeHtml(currentReportType || 'Report')}</h1>
        <p>Generated: ${new Date().toLocaleString('en-IN')} | Records: ${data.length}</p>
        <table>
            <thead><tr>${headers.map(h => `<th>${escapeHtml(h.replace(/_/g,' '))}</th>`).join('')}</tr></thead>
            <tbody>${rows}</tbody>
        </table>
        <div class="footer">This is a computer-generated report.</div>
        </body></html>`;

    const blob = new Blob([html], { type: 'text/html' });
    const url  = URL.createObjectURL(blob);
    const win  = window.open(url, '_blank');
    if (win) win.onload = () => win.print();

    showNotification('Report PDF generated!', 'success');
}

// ====== VIEW REPORT DETAILS ======
/**
 * Show report details in a modal
 * @param {number} reportId
 */
async function viewReportDetails(reportId) {
    showLoading(true);
    try {
        const response = await makeApiCall('GET', `/api/reports/${reportId}`);
        const r = response.report || response;

        const content = `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;">
                <div><strong>Report Name:</strong><br>${escapeHtml(r.name || '-')}</div>
                <div><strong>Type:</strong><br>${escapeHtml(r.report_type || '-')}</div>
                <div><strong>Created:</strong><br>${formatDate(r.created_at)}</div>
                <div><strong>Records:</strong><br>${escapeHtml(String(r.record_count || '-'))}</div>
                <div style="grid-column:1/-1;"><strong>Description:</strong><br>${escapeHtml(r.description || '-')}</div>
            </div>`;

        showModal(`<i class="fas fa-chart-bar" style="color:#3498db;margin-right:8px;"></i>Report Details`, content, [
            { label: '<i class="fas fa-file-csv"></i> Export CSV', class: 'btn-success', onClick: `closeModal(); exportReportToCSV(${reportId});` },
            { label: '<i class="fas fa-file-pdf"></i> Export PDF', class: 'btn-danger',  onClick: `closeModal(); exportReportToPDF(${reportId});` },
            { label: '<i class="fas fa-times"></i> Close', class: 'btn-secondary', onClick: 'closeModal()' }
        ]);
    } catch (error) {
        handleApiError(error, 'Load report details');
    } finally {
        showLoading(false);
    }
}

// ====== SCHEDULE REPORT ======
/**
 * Schedule automatic report generation
 * @param {string} reportType - Report type to schedule
 * @param {string} schedule   - 'daily' | 'weekly' | 'monthly' | 'quarterly'
 */
async function scheduleReport(reportType, schedule) {
    if (!reportType || !schedule) {
        const typeEl     = document.getElementById('reportType') || document.getElementById('reportTypeSelect');
        const scheduleEl = document.getElementById('reportSchedule');
        reportType = reportType || (typeEl     ? typeEl.value     : '');
        schedule   = schedule   || (scheduleEl ? scheduleEl.value : '');
    }

    if (!reportType) { showNotification('Please select a report type', 'error'); return; }
    if (!schedule || schedule === 'none') { showNotification('Please select a schedule', 'error'); return; }

    const emailEl = document.getElementById('reportEmail');
    const nameEl  = document.getElementById('savedReportName');
    const descEl  = document.getElementById('savedReportDesc');

    const scheduleData = {
        report_type: reportType,
        schedule,
        email:       emailEl ? emailEl.value : '',
        name:        nameEl  ? nameEl.value  : `${reportType} - ${schedule}`,
        description: descEl  ? descEl.value  : ''
    };

    showLoading(true);
    try {
        const result = await makeApiCall('POST', '/api/reports/schedule', scheduleData);
        if (result.success || result.id) {
            showNotification(`Report scheduled to run ${schedule}!`, 'success');
            await loadReports();
        } else {
            showNotification(result.error || 'Failed to schedule report', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Schedule report');
    } finally {
        showLoading(false);
    }
}
// ── State ────────────────────────────────────────────────────
let currentReportData = null;
let currentReportType = 'travelers';

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    SessionManager.initPage(async () => {
        await loadReports();
        initReportListeners();
    });
});

function initReportListeners() {
    const typeEl  = document.getElementById('reportType');
    const daysEl  = document.getElementById('reportDays');
    if (typeEl) typeEl.addEventListener('change', () => { currentReportType = typeEl.value; });
    if (daysEl) daysEl.addEventListener('change', loadReports);
}

// ── Load ─────────────────────────────────────────────────────

/**
 * Load the summary report (default view)
 */
async function loadReports() {
    const days = document.getElementById('reportDays')?.value || 30;
    const container = document.getElementById('reportSummaryContainer') || document.getElementById('reportsContainer');
    if (container) container.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading report data…</div>';

    try {
        const data = await makeAPICall('GET', `/api/reports/summary?days=${days}`);
        if (data.success && data.report) {
            currentReportData = data.report;
            displayReportSummary(data.report);
        } else {
            throw new Error(data.error || 'Failed to load reports');
        }
    } catch (error) {
        handleError(error, 'loadReports');
        if (container) {
            container.innerHTML = `<div style="text-align:center; padding:40px;">
                <i class="fas fa-exclamation-triangle" style="color:#e74c3c; font-size:2rem;"></i>
                <p style="color:#e74c3c; margin:10px 0;">${escapeHtml(error.message)}</p>
                <button class="action-btn btn-primary" onclick="loadReports()"><i class="fas fa-redo"></i> Retry</button>
            </div>`;
        }
    }
}

/**
 * Display the summary report data
 * @param {Object} report
 */
function displayReportSummary(report) {
    // Update stat cards
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setEl('reportTotalTravelers', report.total_travelers || 0);
    setEl('reportTotalPayments',  formatCurrency(report.payments?.total || 0));
    setEl('reportPaymentCount',   report.payments?.count || 0);
    setEl('reportPeriod',         report.period || '');

    // Travelers by batch table
    const batchTbody = document.getElementById('travelersByBatchBody');
    if (batchTbody && report.travelers_by_batch) {
        batchTbody.innerHTML = report.travelers_by_batch.map((b) => `<tr>
            <td>${escapeHtml(b.batch_name || '-')}</td>
            <td>${b.traveler_count || 0}</td>
        </tr>`).join('') || '<tr><td colspan="2" style="text-align:center;">No data</td></tr>';
    }

    // Payments by method table
    const methodTbody = document.getElementById('paymentsByMethodBody');
    if (methodTbody && report.payments_by_method) {
        methodTbody.innerHTML = report.payments_by_method.map((m) => `<tr>
            <td>${escapeHtml(m.payment_method || 'Unknown')}</td>
            <td>${m.count || 0}</td>
            <td>${formatCurrency(m.total || 0)}</td>
        </tr>`).join('') || '<tr><td colspan="3" style="text-align:center;">No data</td></tr>';
    }

    // Recent activity
    const activityEl = document.getElementById('reportRecentActivity');
    if (activityEl && report.recent_activity) {
        activityEl.innerHTML = report.recent_activity.slice(0, 10).map((a) => `
            <div style="padding:10px; border-bottom:1px solid #ecf0f1; display:flex; justify-content:space-between;">
                <span>${escapeHtml(a.description || a.action || '-')}</span>
                <small style="color:#7f8c8d;">${a.created_at ? formatDate(a.created_at, true) : '-'}</small>
            </div>`).join('') || '<p style="text-align:center; color:#7f8c8d;">No recent activity</p>';
    }

    // Generic container fallback
    const container = document.getElementById('reportSummaryContainer') || document.getElementById('reportsContainer');
    if (container && !document.getElementById('travelersByBatchBody')) {
        container.innerHTML = buildSummaryHTML(report);
    }
}

function buildSummaryHTML(report) {
    const batchRows = (report.travelers_by_batch || []).map((b) =>
        `<tr><td>${escapeHtml(b.batch_name || '-')}</td><td>${b.traveler_count || 0}</td></tr>`
    ).join('') || '<tr><td colspan="2" style="text-align:center;">No data</td></tr>';

    const methodRows = (report.payments_by_method || []).map((m) =>
        `<tr><td>${escapeHtml(m.payment_method || 'Unknown')}</td><td>${m.count || 0}</td><td>${formatCurrency(m.total || 0)}</td></tr>`
    ).join('') || '<tr><td colspan="3" style="text-align:center;">No data</td></tr>';

    return `
        <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:20px; margin-bottom:30px;">
            <div class="stat-card"><h4>Total Travelers</h4><p style="font-size:2rem; font-weight:bold; color:#3498db;">${report.total_travelers || 0}</p></div>
            <div class="stat-card"><h4>Total Collected</h4><p style="font-size:2rem; font-weight:bold; color:#27ae60;">${formatCurrency(report.payments?.total || 0)}</p></div>
            <div class="stat-card"><h4>Transactions</h4><p style="font-size:2rem; font-weight:bold; color:#f39c12;">${report.payments?.count || 0}</p></div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
            <div>
                <h3 style="margin-bottom:15px;">Travelers by Batch</h3>
                <table style="width:100%; border-collapse:collapse;">
                    <thead><tr style="background:#2c3e50; color:white;"><th style="padding:10px;">Batch</th><th style="padding:10px;">Travelers</th></tr></thead>
                    <tbody>${batchRows}</tbody>
                </table>
            </div>
            <div>
                <h3 style="margin-bottom:15px;">Payments by Method</h3>
                <table style="width:100%; border-collapse:collapse;">
                    <thead><tr style="background:#2c3e50; color:white;"><th style="padding:10px;">Method</th><th style="padding:10px;">Count</th><th style="padding:10px;">Total</th></tr></thead>
                    <tbody>${methodRows}</tbody>
                </table>
            </div>
        </div>`;
}

// ── Generate Custom Report ────────────────────────────────────

/**
 * Generate a custom report based on selected type and filters
 */
async function generateReport() {
    const type      = document.getElementById('reportType')?.value || 'travelers';
    const startDate = document.getElementById('reportStartDate')?.value || null;
    const endDate   = document.getElementById('reportEndDate')?.value || null;
    const batchId   = document.getElementById('reportBatchFilter')?.value || null;
    const status    = document.getElementById('reportStatusFilter')?.value || null;

    const filters = {};
    if (startDate) filters.start_date = startDate;
    if (endDate)   filters.end_date   = endDate;
    if (batchId)   filters.batch_id   = batchId;
    if (status)    filters.status     = status;

    const container = document.getElementById('generatedReportContainer') || document.getElementById('reportsContainer');
    if (container) container.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Generating report…</div>';

    try {
        const data = await makeAPICall('POST', '/api/reports/generate', { type, filters });
        if (data.success && data.report) {
            currentReportData = data.report;
            currentReportType = type;
            displayGeneratedReport(data.report);
            showNotification(`Report generated: ${data.report.count} records`, 'success');
        } else {
            throw new Error(data.error || 'Failed to generate report');
        }
    } catch (error) {
        handleError(error, 'generateReport');
        if (container) container.innerHTML = `<p style="color:#e74c3c; text-align:center;">${escapeHtml(error.message)}</p>`;
    }
}

/**
 * Display a generated report
 * @param {Object} report
 */
function displayGeneratedReport(report) {
    const container = document.getElementById('generatedReportContainer') || document.getElementById('reportsContainer');
    if (!container) return;

    const rows = (report.data || []).slice(0, 100);
    if (rows.length === 0) {
        container.innerHTML = '<p style="text-align:center; color:#7f8c8d; padding:30px;">No data found for the selected filters</p>';
        return;
    }

    const cols = Object.keys(rows[0]).filter((k) => !['extra_fields', 'items'].includes(k));
    const headers = cols.map((c) => `<th style="padding:10px; background:#2c3e50; color:white;">${escapeHtml(c.replace(/_/g, ' '))}</th>`).join('');
    const tableRows = rows.map((row) =>
        `<tr>${cols.map((c) => `<td style="padding:10px; border-bottom:1px solid #ecf0f1;">${escapeHtml(String(row[c] ?? '-'))}</td>`).join('')}</tr>`
    ).join('');

    container.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
            <h3>Report: ${escapeHtml(report.type)} (${report.count} records)</h3>
            <div style="display:flex; gap:10px;">
                <button class="action-btn btn-success" onclick="exportReportToCSV()"><i class="fas fa-file-csv"></i> Export CSV</button>
                <button class="action-btn btn-primary" onclick="exportReportToPDF()"><i class="fas fa-file-pdf"></i> Export PDF</button>
            </div>
        </div>
        <div style="overflow-x:auto;">
            <table style="width:100%; border-collapse:collapse; font-size:0.9rem;">
                <thead><tr>${headers}</tr></thead>
                <tbody>${tableRows}</tbody>
            </table>
        </div>
        ${report.count > 100 ? `<p style="text-align:center; color:#7f8c8d; margin-top:10px;">Showing first 100 of ${report.count} records. Export to see all.</p>` : ''}`;
}

// ── Filter ───────────────────────────────────────────────────

/**
 * Filter the current report by date range
 */
function filterReports() {
    generateReport();
}

// ── View Details ─────────────────────────────────────────────

/**
 * View details of a specific report record
 * @param {number} id
 */
function viewReportDetails(id) {
    if (!currentReportData || !currentReportData.data) return;
    const record = currentReportData.data.find((r) => r.id === id);
    if (!record) { showNotification('Record not found', 'error'); return; }

    const content = Object.entries(record)
        .filter(([k]) => !['extra_fields', 'items'].includes(k))
        .map(([k, v]) => `<div style="padding:8px; border-bottom:1px solid #ecf0f1;">
            <strong>${escapeHtml(k.replace(/_/g, ' '))}:</strong> ${escapeHtml(String(v ?? '-'))}
        </div>`).join('');

    showModal('Record Details', `<div style="max-height:400px; overflow-y:auto;">${content}</div>`);
}

// ── Export ───────────────────────────────────────────────────

/**
 * Export the current report to CSV
 */
function exportReportToCSV() {
    if (!currentReportData || !currentReportData.data || currentReportData.data.length === 0) {
        showNotification('No report data to export. Generate a report first.', 'warning');
        return;
    }

    const rows = currentReportData.data;
    const cols = Object.keys(rows[0]).filter((k) => !['extra_fields', 'items'].includes(k));
    const headers = cols.map((c) => c.replace(/_/g, ' '));

    downloadCSV(rows, cols, headers, `report_${currentReportType}_${new Date().toISOString().slice(0, 10)}.csv`);
}

/**
 * Export the current report to PDF (print dialog)
 */
function exportReportToPDF() {
    if (!currentReportData || !currentReportData.data || currentReportData.data.length === 0) {
        showNotification('No report data to export. Generate a report first.', 'warning');
        return;
    }

    const rows = currentReportData.data.slice(0, 200);
    const cols = Object.keys(rows[0]).filter((k) => !['extra_fields', 'items'].includes(k));

    const headers = cols.map((c) => `<th style="padding:8px; background:#2c3e50; color:white;">${escapeHtml(c.replace(/_/g, ' '))}</th>`).join('');
    const tableRows = rows.map((row) =>
        `<tr>${cols.map((c) => `<td style="padding:8px; border:1px solid #ddd;">${escapeHtml(String(row[c] ?? '-'))}</td>`).join('')}</tr>`
    ).join('');

    const printWin = window.open('', '_blank');
    printWin.document.write(`<html><head><title>Report - ${currentReportType}</title>
        <style>body{font-family:Arial;padding:20px;} table{width:100%;border-collapse:collapse;font-size:0.85rem;} @media print{button{display:none;}}</style>
        </head><body>
        <h2>Report: ${escapeHtml(currentReportType)} — ${new Date().toLocaleDateString()}</h2>
        <p>Total records: ${currentReportData.count}</p>
        <table><thead><tr>${headers}</tr></thead><tbody>${tableRows}</tbody></table>
        <button onclick="window.print()" style="margin-top:20px; padding:10px 20px; background:#3498db; color:white; border:none; border-radius:5px; cursor:pointer;">Print</button>
        </body></html>`);
    printWin.document.close();
}

// ── Schedule ─────────────────────────────────────────────────

/**
 * Schedule a report (placeholder – requires backend support)
 */
function scheduleReport() {
    showModal('Schedule Report',
        `<div>
            <p style="margin-bottom:15px; color:#7f8c8d;">Configure automatic report generation and delivery.</p>
            <div class="form-group">
                <label>Report Type</label>
                <select id="scheduleReportType" style="width:100%; padding:10px; border:2px solid #ecf0f1; border-radius:5px;">
                    <option value="travelers">Travelers</option>
                    <option value="payments">Payments</option>
                    <option value="financial">Financial</option>
                </select>
            </div>
            <div class="form-group" style="margin-top:15px;">
                <label>Frequency</label>
                <select id="scheduleFrequency" style="width:100%; padding:10px; border:2px solid #ecf0f1; border-radius:5px;">
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                </select>
            </div>
            <div class="form-group" style="margin-top:15px;">
                <label>Email Recipients</label>
                <input type="email" id="scheduleEmail" placeholder="admin@example.com"
                    style="width:100%; padding:10px; border:2px solid #ecf0f1; border-radius:5px;">
            </div>
        </div>`,
        `<button class="action-btn btn-primary" onclick="saveReportSchedule()"><i class="fas fa-save"></i> Save Schedule</button>
         <button class="action-btn btn-secondary" onclick="closeModal()">Cancel</button>`
    );
}

function saveReportSchedule() {
    const type  = document.getElementById('scheduleReportType')?.value;
    const freq  = document.getElementById('scheduleFrequency')?.value;
    const email = document.getElementById('scheduleEmail')?.value;
    if (!email) { showNotification('Please enter an email address', 'error'); return; }
    // Placeholder – would POST to /api/reports/schedule
    showNotification(`Report scheduled: ${type} ${freq} to ${email}`, 'success');
    closeModal();
}

// Expose globals
window.loadReports         = loadReports;
window.generateReport      = generateReport;
window.filterReports       = filterReports;
window.viewReportDetails   = viewReportDetails;
window.exportReportToCSV   = exportReportToCSV;
window.exportReportToPDF   = exportReportToPDF;
window.scheduleReport      = scheduleReport;
window.saveReportSchedule  = saveReportSchedule;

console.log('✅ reports.js loaded');
