/**
 * reports.js - Report generation and management functions
 * Alhudha Haj Travel Management System
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
