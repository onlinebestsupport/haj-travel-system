'use strict';

/**
 * Advanced Report Module
 * Provides comprehensive customizable reporting with:
 * - Travelers, Batches, and Payments sections
 * - Multi-field filtering with selectable formats
 * - CSV, Excel, PDF export
 * - Real-time preview and statistics
 */

const ADVANCED_REPORTS = {
    state: {
        currentReport: null,
        selectedFormat: 'table',
        reportFilters: {},
        selectedFields: {
            travelers: [],
            batches: [],
            payments: []
        }
    },

    // ===== TRAVELERS FIELDS =====
    TRAVELERS_FIELDS: [
        { id: 'id', label: 'ID', type: 'number', default: true },
        { id: 'first_name', label: 'First Name', type: 'text', default: true },
        { id: 'last_name', label: 'Last Name', type: 'text', default: true },
        { id: 'passport_name', label: 'Passport Name', type: 'text', default: false },
        { id: 'batch_id', label: 'Batch ID', type: 'number', default: true },
        { id: 'batch_name', label: 'Batch Name', type: 'text', default: true },
        { id: 'passport_no', label: 'Passport Number', type: 'text', default: true },
        { id: 'passport_issue_date', label: 'Passport Issue Date', type: 'date', default: false },
        { id: 'passport_expiry_date', label: 'Passport Expiry Date', type: 'date', default: true },
        { id: 'passport_status', label: 'Passport Status', type: 'text', default: false },
        { id: 'gender', label: 'Gender', type: 'text', default: false },
        { id: 'dob', label: 'Date of Birth', type: 'date', default: false },
        { id: 'mobile', label: 'Mobile', type: 'text', default: true },
        { id: 'email', label: 'Email', type: 'text', default: true },
        { id: 'aadhaar', label: 'Aadhaar', type: 'text', default: false },
        { id: 'pan', label: 'PAN', type: 'text', default: false },
        { id: 'aadhaar_pan_linked', label: 'Aadhaar-PAN Linked', type: 'text', default: false },
        { id: 'vaccine_status', label: 'Vaccine Status', type: 'text', default: true },
        { id: 'wheelchair', label: 'Wheelchair Required', type: 'text', default: false },
        { id: 'place_of_birth', label: 'Place of Birth', type: 'text', default: false },
        { id: 'place_of_issue', label: 'Place of Issue', type: 'text', default: false },
        { id: 'passport_address', label: 'Passport Address', type: 'text', default: false },
        { id: 'father_name', label: "Father's Name", type: 'text', default: false },
        { id: 'mother_name', label: "Mother's Name", type: 'text', default: false },
        { id: 'spouse_name', label: "Spouse's Name", type: 'text', default: false },
        { id: 'pin', label: 'PIN Code', type: 'text', default: false },
        { id: 'emergency_contact', label: 'Emergency Contact', type: 'text', default: false },
        { id: 'emergency_phone', label: 'Emergency Phone', type: 'text', default: false },
        { id: 'medical_notes', label: 'Medical Notes', type: 'text', default: false },
        { id: 'created_at', label: 'Created At', type: 'datetime', default: true }
    ],

    // ===== BATCHES FIELDS =====
    BATCHES_FIELDS: [
        { id: 'id', label: 'Batch ID', type: 'number', default: true },
        { id: 'batch_name', label: 'Batch Name', type: 'text', default: true },
        { id: 'status', label: 'Status', type: 'text', default: true },
        { id: 'total_travelers', label: 'Total Travelers', type: 'number', default: true },
        { id: 'start_date', label: 'Start Date', type: 'date', default: true },
        { id: 'end_date', label: 'End Date', type: 'date', default: true },
        { id: 'description', label: 'Description', type: 'text', default: false },
        { id: 'created_at', label: 'Created At', type: 'datetime', default: false }
    ],

    // ===== PAYMENTS FIELDS =====
    PAYMENTS_FIELDS: [
        { id: 'id', label: 'Payment ID', type: 'number', default: true },
        { id: 'traveler_id', label: 'Traveler ID', type: 'number', default: false },
        { id: 'traveler_name', label: 'Traveler Name', type: 'text', default: true },
        { id: 'batch_id', label: 'Batch ID', type: 'number', default: true },
        { id: 'batch_name', label: 'Batch Name', type: 'text', default: true },
        { id: 'amount', label: 'Amount (₹)', type: 'currency', default: true },
        { id: 'payment_method', label: 'Payment Method', type: 'text', default: true },
        { id: 'status', label: 'Payment Status', type: 'text', default: true },
        { id: 'transaction_id', label: 'Transaction ID', type: 'text', default: false },
        { id: 'payment_date', label: 'Payment Date', type: 'date', default: true },
        { id: 'created_at', label: 'Created At', type: 'datetime', default: false }
    ],

    /**
     * Initialize the advanced reports module
     */
    init() {
        console.log("✅ Advanced Reports Module Initialized");
        this.setupEventListeners();
        this.loadInitialData();
    },

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('field-checkbox')) {
                this.updateFieldSelection(e.target);
            }
            if (e.target.id === 'reportCategory') {
                this.switchReportCategory(e.target.value);
            }
            if (e.target.id === 'dateRange') {
                this.toggleCustomDateInputs();
            }
        });

        document.addEventListener('click', (e) => {
            if (e.target.id === 'selectAllFields') {
                this.toggleAllFields(e.target.checked);
            }
            if (e.target.classList.contains('generate-report-btn')) {
                this.generateAdvancedReport();
            }
            if (e.target.classList.contains('export-btn')) {
                this.exportReport(e.target.dataset.format);
            }
        });
    },

    /**
     * Load initial data and populate dropdowns
     */
    async loadInitialData() {
        try {
            // Load batches for filter dropdown
            const batchResponse = await fetch('/api/batches', { credentials: 'include' });
            const batchData = await batchResponse.json();
            
            if (batchData.success && Array.isArray(batchData.batches)) {
                this.populateBatchDropdown(batchData.batches);
            }

            // Initialize field selections with defaults
            this.resetFieldSelection();
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    },

    /**
     * Populate batch dropdown
     */
    populateBatchDropdown(batches) {
        const select = document.getElementById('filterBatch');
        if (!select) return;

        const defaultOption = select.querySelector('option[value="all"]');
        select.innerHTML = '';
        if (defaultOption) select.appendChild(defaultOption);

        batches.forEach(batch => {
            const option = document.createElement('option');
            option.value = batch.id;
            option.textContent = batch.batch_name || `Batch ${batch.id}`;
            select.appendChild(option);
        });
    },

    /**
     * Switch report category and update field selectors
     */
    switchReportCategory(category) {
        const fieldSelector = document.getElementById('advancedFieldSelector');
        if (!fieldSelector) return;

        let fields = [];
        switch(category) {
            case 'travelers':
                fields = this.TRAVELERS_FIELDS;
                break;
            case 'batches':
                fields = this.BATCHES_FIELDS;
                break;
            case 'payments':
                fields = this.PAYMENTS_FIELDS;
                break;
        }

        this.renderFieldSelector(fields, category);
        this.state.selectedFields[category] = fields
            .filter(f => f.default)
            .map(f => f.id);
    },

    /**
     * Render field selector checkboxes
     */
    renderFieldSelector(fields, category) {
        const container = document.getElementById('fieldCheckboxContainer');
        if (!container) return;

        const selected = this.state.selectedFields[category] || [];

        container.innerHTML = `
            <div class="select-all-container">
                <label>
                    <input type="checkbox" id="selectAllFields" 
                        ${selected.length === fields.length ? 'checked' : ''}>
                    <strong>Select All Fields</strong>
                </label>
                <span class="field-count">${selected.length} of ${fields.length} selected</span>
            </div>
            <div class="field-grid">
                ${fields.map(field => `
                    <label class="field-checkbox-label">
                        <input type="checkbox" class="field-checkbox" 
                            data-field="${field.id}" 
                            data-category="${category}"
                            ${selected.includes(field.id) ? 'checked' : ''}>
                        <span>${field.label}</span>
                    </label>
                `).join('')}
            </div>
        `;

        this.updateFieldCount();
    },

    /**
     * Update field selection and count
     */
    updateFieldSelection(checkbox) {
        const category = checkbox.dataset.category || document.getElementById('reportCategory').value;
        const fieldId = checkbox.dataset.field;

        if (!this.state.selectedFields[category]) {
            this.state.selectedFields[category] = [];
        }

        if (checkbox.checked) {
            if (!this.state.selectedFields[category].includes(fieldId)) {
                this.state.selectedFields[category].push(fieldId);
            }
        } else {
            this.state.selectedFields[category] = 
                this.state.selectedFields[category].filter(f => f !== fieldId);
        }

        this.updateFieldCount();
    },

    /**
     * Update field count display
     */
    updateFieldCount() {
        const category = document.getElementById('reportCategory').value;
        const selected = this.state.selectedFields[category] || [];
        const countEl = document.querySelector('.field-count');
        
        if (countEl) {
            const total = document.querySelectorAll('.field-checkbox').length;
            countEl.textContent = `${selected.length} of ${total} selected`;
        }
    },

    /**
     * Toggle all fields
     */
    toggleAllFields(checked) {
        document.querySelectorAll('.field-checkbox').forEach(cb => {
            cb.checked = checked;
            this.updateFieldSelection(cb);
        });
    },

    /**
     * Reset field selection to defaults
     */
    resetFieldSelection() {
        const category = document.getElementById('reportCategory')?.value || 'travelers';
        this.switchReportCategory(category);
    },

    /**
     * Toggle custom date inputs
     */
    toggleCustomDateInputs() {
        const range = document.getElementById('dateRange')?.value;
        const customDates = document.getElementById('customDateRange');
        if (customDates) {
            customDates.style.display = range === 'custom' ? 'flex' : 'none';
        }
    },

    /**
     * Generate advanced report
     */
    async generateAdvancedReport() {
        const category = document.getElementById('reportCategory').value;
        const selectedFields = this.state.selectedFields[category];

        if (selectedFields.length === 0) {
            this.showAlert('Please select at least one field', 'warning');
            return;
        }

        const filters = this.buildFilters();
        
        try {
            this.showLoading('Generating report...');

            const response = await fetch('/api/reports/advanced', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    category: category,
                    fields: selectedFields,
                    filters: filters
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.state.currentReport = data;
                this.displayReportResults(data, selectedFields, category);
                this.showAlert(`Report generated: ${data.count} records`, 'success');
            } else {
                this.showAlert(data.error || 'Failed to generate report', 'error');
            }
        } catch (error) {
            console.error('Report generation error:', error);
            this.showAlert('Error generating report', 'error');
        } finally {
            this.hideLoading();
        }
    },

    /**
     * Build filters from form inputs
     */
    buildFilters() {
        const range = document.getElementById('dateRange')?.value || 'today';
        let startDate, endDate;

        if (range === 'custom') {
            startDate = document.getElementById('startDate')?.value;
            endDate = document.getElementById('endDate')?.value;
        } else {
            const dates = this.getDateRange(range);
            startDate = dates.start;
            endDate = dates.end;
        }

        return {
            startDate: startDate,
            endDate: endDate,
            batchId: document.getElementById('filterBatch')?.value || 'all',
            status: document.getElementById('filterStatus')?.value || 'all',
            searchText: document.getElementById('filterSearch')?.value || ''
        };
    },

    /**
     * Get date range based on selection
     */
    getDateRange(range) {
        const today = new Date();
        const end = new Date(today);
        const start = new Date(today);

        const ranges = {
            today: () => {
                start.setHours(0, 0, 0, 0);
                end.setHours(23, 59, 59, 999);
            },
            yesterday: () => {
                start.setDate(today.getDate() - 1);
                start.setHours(0, 0, 0, 0);
                end.setDate(today.getDate() - 1);
                end.setHours(23, 59, 59, 999);
            },
            thisweek: () => {
                start.setDate(today.getDate() - today.getDay());
                start.setHours(0, 0, 0, 0);
            },
            thismonth: () => {
                start.setDate(1);
                start.setHours(0, 0, 0, 0);
            },
            lastmonth: () => {
                start.setMonth(today.getMonth() - 1, 1);
                start.setHours(0, 0, 0, 0);
                end.setMonth(today.getMonth(), 0);
                end.setHours(23, 59, 59, 999);
            },
            thisyear: () => {
                start.setMonth(0, 1);
                start.setHours(0, 0, 0, 0);
            },
            alltime: () => {
                start.setFullYear(2000, 0, 1);
                end.setFullYear(2100, 0, 1);
            }
        };

        if (ranges[range]) ranges[range]();

        return {
            start: start.toISOString().split('T')[0],
            end: end.toISOString().split('T')[0]
        };
    },

    /**
     * Display report results
     */
    displayReportResults(data, selectedFields, category) {
        const resultsContainer = document.getElementById('advancedReportResults');
        if (!resultsContainer) return;

        const fields = this.getFieldsForCategory(category);
        const fieldMap = {};
        fields.forEach(f => fieldMap[f.id] = f);

        // Display statistics
        const stats = this.calculateStatistics(data.data, selectedFields, category);
        this.displayStatistics(stats);

        // Display table
        this.displayReportTable(data.data, selectedFields, fieldMap);

        resultsContainer.style.display = 'block';
    },

    /**
     * Get fields for category
     */
    getFieldsForCategory(category) {
        const categoryMap = {
            travelers: this.TRAVELERS_FIELDS,
            batches: this.BATCHES_FIELDS,
            payments: this.PAYMENTS_FIELDS
        };
        return categoryMap[category] || [];
    },

    /**
     * Calculate statistics
     */
    calculateStatistics(data, selectedFields, category) {
        const stats = {
            total: data.length,
            summary: {}
        };

        if (category === 'payments' && data.length > 0) {
            const amounts = data
                .map(r => parseFloat(r.amount) || 0)
                .filter(a => a > 0);
            
            if (amounts.length > 0) {
                stats.summary = {
                    totalAmount: amounts.reduce((a, b) => a + b, 0),
                    averageAmount: amounts.reduce((a, b) => a + b, 0) / amounts.length,
                    minAmount: Math.min(...amounts),
                    maxAmount: Math.max(...amounts)
                };
            }
        }

        return stats;
    },

    /**
     * Display statistics
     */
    displayStatistics(stats) {
        const statsContainer = document.getElementById('reportStatistics');
        if (!statsContainer) return;

        let html = `<div class="stat-card">
            <i class="fas fa-list"></i>
            <h4>Total Records</h4>
            <p class="stat-value">${stats.total}</p>
        </div>`;

        if (stats.summary.totalAmount !== undefined) {
            html += `
                <div class="stat-card">
                    <i class="fas fa-rupee-sign"></i>
                    <h4>Total Amount</h4>
                    <p class="stat-value">₹${stats.summary.totalAmount.toLocaleString('en-IN', {
                        maximumFractionDigits: 2
                    })}</p>
                </div>
                <div class="stat-card">
                    <i class="fas fa-average"></i>
                    <h4>Average Amount</h4>
                    <p class="stat-value">₹${stats.summary.averageAmount.toLocaleString('en-IN', {
                        maximumFractionDigits: 2
                    })}</p>
                </div>
            `;
        }

        statsContainer.innerHTML = html;
    },

    /**
     * Display report table
     */
    displayReportTable(data, selectedFields, fieldMap) {
        const tableContainer = document.getElementById('reportTableContainer');
        if (!tableContainer) return;

        if (data.length === 0) {
            tableContainer.innerHTML = '<p style="text-align:center; padding:20px;">No data found</p>';
            return;
        }

        // Build table header
        const headers = selectedFields.map(fieldId => {
            const field = fieldMap[fieldId];
            return `<th>${field?.label || fieldId}</th>`;
        }).join('');

        // Build table rows
        const rows = data.map(row => {
            const cells = selectedFields.map(fieldId => {
                let value = row[fieldId] ?? '-';
                
                // Format value based on type
                const field = fieldMap[fieldId];
                if (field) {
                    if (field.type === 'currency' && value !== '-') {
                        value = `₹${parseFloat(value).toLocaleString('en-IN', {
                            maximumFractionDigits: 2
                        })}`;
                    } else if (field.type === 'date' && value !== '-') {
                        value = new Date(value).toLocaleDateString('en-IN');
                    } else if (field.type === 'datetime' && value !== '-') {
                        value = new Date(value).toLocaleString('en-IN');
                    }
                }
                
                return `<td>${this.escapeHtml(String(value))}</td>`;
            }).join('');

            return `<tr>${cells}</tr>`;
        }).join('');

        tableContainer.innerHTML = `
            <div class="table-wrapper">
                <table class="report-table">
                    <thead><tr>${headers}</tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `;
    },

    /**
     * Export report to format
     */
    async exportReport(format) {
        if (!this.state.currentReport || !this.state.currentReport.data) {
            this.showAlert('No report to export', 'warning');
            return;
        }

        const category = document.getElementById('reportCategory').value;
        const selectedFields = this.state.selectedFields[category];
        const data = this.state.currentReport.data;
        const fields = this.getFieldsForCategory(category);
        const fieldMap = {};
        fields.forEach(f => fieldMap[f.id] = f);

        try {
            if (format === 'csv') {
                this.exportToCSV(data, selectedFields, fieldMap, category);
            } else if (format === 'excel') {
                this.exportToExcel(data, selectedFields, fieldMap, category);
            } else if (format === 'pdf') {
                this.exportToPDF(data, selectedFields, fieldMap, category);
            }
            this.showAlert(`Exported to ${format.toUpperCase()}`, 'success');
        } catch (error) {
            console.error('Export error:', error);
            this.showAlert('Export failed', 'error');
        }
    },

    /**
     * Export to CSV
     */
    exportToCSV(data, selectedFields, fieldMap, category) {
        const headers = selectedFields.map(f => fieldMap[f]?.label || f);
        let csv = headers.join(',') + '\n';

        data.forEach(row => {
            const values = selectedFields.map(field => {
                let value = row[field] ?? '';
                // Escape quotes and wrap in quotes if contains comma
                if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                    value = `"${value.replace(/"/g, '""')}"`;
                }
                return value;
            });
            csv += values.join(',') + '\n';
        });

        this.downloadFile(csv, `report_${category}_${new Date().toISOString().slice(0, 10)}.csv`, 'text/csv');
    },

    /**
     * Export to Excel
     */
    async exportToExcel(data, selectedFields, fieldMap, category) {
        if (typeof XLSX === 'undefined') {
            this.showAlert('Excel library not available. Exporting as CSV instead.', 'warning');
            this.exportToCSV(data, selectedFields, fieldMap, category);
            return;
        }

        const headers = selectedFields.map(f => fieldMap[f]?.label || f);
        const rows = data.map(row => {
            const obj = {};
            selectedFields.forEach(field => {
                obj[fieldMap[field]?.label || field] = row[field] ?? '';
            });
            return obj;
        });

        const ws = XLSX.utils.json_to_sheet(rows);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, category);
        XLSX.writeFile(wb, `report_${category}_${new Date().toISOString().slice(0, 10)}.xlsx`);
    },

    /**
     * Export to PDF
     */
    exportToPDF(data, selectedFields, fieldMap, category) {
        if (typeof jsPDF === 'undefined') {
            this.showAlert('PDF library not available', 'error');
            return;
        }

        const doc = new jsPDF();
        const headers = selectedFields.map(f => fieldMap[f]?.label || f);
        const rows = data.slice(0, 500).map(row => 
            selectedFields.map(field => String(row[field] ?? '-').substring(0, 50))
        );

        doc.autoTable({
            head: [headers],
            body: rows,
            margin: 10,
            styles: { fontSize: 9 }
        });

        doc.save(`report_${category}_${new Date().toISOString().slice(0, 10)}.pdf`);
    },

    /**
     * Download file utility
     */
    downloadFile(content, filename, type) {
        const blob = new Blob([content], { type: type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    },

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Show loading indicator
     */
    showLoading(message) {
        const loader = document.getElementById('advancedReportLoader');
        if (loader) {
            loader.innerHTML = `<p><i class="fas fa-spinner fa-spin"></i> ${message}</p>`;
            loader.style.display = 'block';
        }
    },

    /**
     * Hide loading indicator
     */
    hideLoading() {
        const loader = document.getElementById('advancedReportLoader');
        if (loader) loader.style.display = 'none';
    },

    /**
     * Show alert message
     */
    showAlert(message, type = 'info') {
        const alertEl = document.getElementById('advancedReportAlert');
        if (!alertEl) return;

        alertEl.className = `alert alert-${type}`;
        alertEl.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            ${message}
        `;
        alertEl.style.display = 'block';

        if (type !== 'error') {
            setTimeout(() => alertEl.style.display = 'none', 3000);
        }
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    ADVANCED_REPORTS.init();
});

// Export for use
window.ADVANCED_REPORTS = ADVANCED_REPORTS;
console.log('✅ Advanced Reports Module Loaded');
