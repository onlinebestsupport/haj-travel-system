/**
 * reports.js - Reports Management for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 */

'use strict';

// ── State ────────────────────────────────────────────────────
let reportsData = [];
let currentReportData = null;
let currentReportType = 'travelers';
let reportsChartInstances = {};

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    SessionManager.initPage(async () => {
        await loadReports();
        initReportListeners();
    });
});

function initReportListeners() {
    const typeEl = document.getElementById('reportType');
    const daysEl = document.getElementById('reportDays');
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
        handleAPIError(error, 'loadReports');
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
        handleAPIError(error, 'generateReport');
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