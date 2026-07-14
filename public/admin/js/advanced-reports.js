// ====== ADVANCED REPORTS MODULE ======
const ADVANCED_REPORTS = {
    currentReportType: 'travelers',
    currentReportData: null,
    selectedFields: [],

    // Field definitions for each report type
    FIELD_DEFINITIONS: {
        travelers: [
            { name: 'id', label: 'ID', type: 'number', default: true },
            { name: 'first_name', label: 'First Name', type: 'text', default: true },
            { name: 'last_name', label: 'Last Name', type: 'text', default: true },
            { name: 'passport_name', label: 'Passport Name', type: 'text', default: false },
            { name: 'batch_id', label: 'Batch ID', type: 'number', default: true },
            { name: 'batch_name', label: 'Batch Name', type: 'text', default: true },
            { name: 'passport_no', label: 'Passport Number', type: 'text', default: true },
            { name: 'passport_issue_date', label: 'Passport Issue Date', type: 'date', default: false },
            { name: 'passport_expiry_date', label: 'Passport Expiry Date', type: 'date', default: true },
            { name: 'passport_status', label: 'Passport Status', type: 'text', default: false },
            { name: 'gender', label: 'Gender', type: 'text', default: false },
            { name: 'dob', label: 'Date of Birth', type: 'date', default: false },
            { name: 'mobile', label: 'Mobile', type: 'text', default: true },
            { name: 'email', label: 'Email', type: 'text', default: true },
            { name: 'aadhaar', label: 'Aadhaar', type: 'text', default: false },
            { name: 'pan', label: 'PAN', type: 'text', default: false },
            { name: 'aadhaar_pan_linked', label: 'Aadhaar-PAN Linked', type: 'text', default: false },
            { name: 'vaccine_status', label: 'Vaccine Status', type: 'text', default: true },
            { name: 'wheelchair', label: 'Wheelchair Required', type: 'text', default: false },
            { name: 'place_of_birth', label: 'Place of Birth', type: 'text', default: false },
            { name: 'place_of_issue', label: 'Place of Issue', type: 'text', default: false },
            { name: 'passport_address', label: 'Passport Address', type: 'text', default: false },
            { name: 'father_name', label: "Father's Name", type: 'text', default: false },
            { name: 'mother_name', label: "Mother's Name", type: 'text', default: false },
            { name: 'spouse_name', label: "Spouse's Name", type: 'text', default: false },
            { name: 'pin', label: 'PIN Code', type: 'text', default: false },
            { name: 'emergency_contact', label: 'Emergency Contact', type: 'text', default: false },
            { name: 'emergency_phone', label: 'Emergency Phone', type: 'text', default: false },
            { name: 'medical_notes', label: 'Medical Notes', type: 'text', default: false },
            { name: 'created_at', label: 'Created At', type: 'datetime', default: true }
        ],
        batches: [
            { name: 'id', label: 'Batch ID', type: 'number', default: true },
            { name: 'batch_name', label: 'Batch Name', type: 'text', default: true },
            { name: 'status', label: 'Status', type: 'text', default: true },
            { name: 'total_travelers', label: 'Total Travelers', type: 'number', default: true },
            { name: 'start_date', label: 'Start Date', type: 'date', default: true },
            { name: 'end_date', label: 'End Date', type: 'date', default: true },
            { name: 'description', label: 'Description', type: 'text', default: false },
            { name: 'created_at', label: 'Created At', type: 'datetime', default: false }
        ],
        payments: [
            { name: 'id', label: 'Payment ID', type: 'number', default: true },
            { name: 'traveler_id', label: 'Traveler ID', type: 'number', default: false },
            { name: 'traveler_name', label: 'Traveler Name', type: 'text', default: true },
            { name: 'batch_id', label: 'Batch ID', type: 'number', default: true },
            { name: 'batch_name', label: 'Batch Name', type: 'text', default: true },
            { name: 'amount', label: 'Amount (₹)', type: 'currency', default: true },
            { name: 'payment_method', label: 'Payment Method', type: 'text', default: true },
            { name: 'status', label: 'Payment Status', type: 'text', default: true },
            { name: 'transaction_id', label: 'Transaction ID', type: 'text', default: false },
            { name: 'payment_date', label: 'Payment Date', type: 'date', default: true },
            { name: 'created_at', label: 'Created At', type: 'datetime', default: false }
        ],
    },

    init() {
        console.log('🚀 ADVANCED_REPORTS module initializing...');
        this.populateFieldSelector();
        this.setupExportButtons();
        this.setupBatchFilter();
        // Add event listeners for payment report
        this.setupPaymentReportSupport();
        document.addEventListener('DOMContentLoaded', () => this.onReady());
    },

    onReady() {
        console.log('✅ DOM Ready - Reports page fully loaded');
        this.populateFieldSelector();
        // Check if PDF libraries are loaded
        this.checkPDFLibraries();
    },

    // New method to check PDF libraries
    checkPDFLibraries() {
        if (typeof jsPDF === 'undefined') {
            console.warn('⚠️ jsPDF library not loaded. PDF export will be disabled.');
            const pdfBtn = document.querySelector('[data-format="pdf"]');
            if (pdfBtn) {
                pdfBtn.style.opacity = '0.5';
                pdfBtn.title = 'PDF export requires jsPDF library';
            }
        } else if (typeof jsPDF.autoTable === 'undefined') {
            console.warn('⚠️ jsPDF autoTable plugin not loaded. PDF export will be limited.');
        }
    },

    // New method to support payment reports
    setupPaymentReportSupport() {
        // Add event listeners for payment-specific filters if needed
        const statusFilter = document.getElementById('filterStatus');
        if (statusFilter) {
            // Add payment-specific status options
            const paymentStatuses = ['all', 'paid', 'pending', 'failed', 'refunded'];
            const currentOptions = Array.from(statusFilter.options).map(opt => opt.value);
            paymentStatuses.forEach(status => {
                if (!currentOptions.includes(status)) {
                    const option = document.createElement('option');
                    option.value = status;
                    option.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                    statusFilter.appendChild(option);
                }
            });
        }
    },

    populateFieldSelector() {
        const container = document.getElementById('fieldCheckboxContainer');
        const fields = this.FIELD_DEFINITIONS[this.currentReportType] || [];
        
        if (!container) {
            console.error('❌ fieldCheckboxContainer not found!');
            return;
        }

        container.innerHTML = '';

        // Add a search input for fields if there are many fields
        if (fields.length > 20) {
            const searchInput = document.createElement('input');
            searchInput.type = 'text';
            searchInput.placeholder = '🔍 Search fields...';
            searchInput.className = 'field-search-input';
            searchInput.style.cssText = 'width: 100%; padding: 5px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px;';
            searchInput.addEventListener('input', (e) => {
                const searchTerm = e.target.value.toLowerCase();
                document.querySelectorAll('.field-checkbox-label').forEach(label => {
                    const text = label.textContent.toLowerCase();
                    label.style.display = text.includes(searchTerm) ? 'flex' : 'none';
                });
            });
            container.appendChild(searchInput);
        }

        fields.forEach(field => {
            const label = document.createElement('label');
            label.className = 'field-checkbox-label';
            const defaultChecked = field.default ? 'checked' : '';
            label.innerHTML = `
                <input type="checkbox" class="field-checkbox" value="${field.name}" ${defaultChecked} onchange="ADVANCED_REPORTS.updateFieldCount()">
                <span>${field.label}</span>
            `;
            container.appendChild(label);
        });

        this.updateFieldCount();
        console.log(`✅ Populated ${fields.length} fields for ${this.currentReportType}`);
    },

    updateFieldCount() {
        const checked = document.querySelectorAll('.field-checkbox:checked').length;
        const countEl = document.querySelector('.field-count');
        if (countEl) {
            countEl.textContent = `${checked} fields selected`;
        }
    },

    toggleAllFields(checked) {
        document.querySelectorAll('.field-checkbox').forEach(cb => {
            cb.checked = checked;
        });
        this.updateFieldCount();
    },

    switchReportCategory(reportType) {
        this.currentReportType = reportType;
        this.populateFieldSelector();
        // Clear previous results when switching
        this.clearReportResults();
        console.log(`✅ Switched to ${reportType} report`);
    },

    clearReportResults() {
        const resultsDiv = document.getElementById('advancedReportResults');
        if (resultsDiv) {
            resultsDiv.style.display = 'none';
        }
        const tableContainer = document.getElementById('reportTableContainer');
        if (tableContainer) {
            tableContainer.innerHTML = '';
        }
        const statsDiv = document.getElementById('reportStatistics');
        if (statsDiv) {
            statsDiv.innerHTML = '';
        }
    },

    toggleCustomDateInputs() {
        const range = document.getElementById('dateRange');
        const customRange = document.getElementById('customDateRange');
        
        if (range && range.value === 'custom') {
            customRange.style.display = 'contents';
        } else if (customRange) {
            customRange.style.display = 'none';
        }
    },

    resetFieldSelection() {
        document.querySelectorAll('.field-checkbox').forEach(cb => {
            cb.checked = true;
        });
        this.updateFieldCount();
        this.showAlert('Field selection reset', 'info');
    },

    async generateAdvancedReport() {
        console.log('📊 Generating report...');

        // Get selected fields
        const selectedFields = Array.from(document.querySelectorAll('.field-checkbox:checked'))
            .map(cb => cb.value);

        if (selectedFields.length === 0) {
            this.showAlert('Please select at least one field', 'error');
            return;
        }

        // Get filters
        const dateRange = document.getElementById('dateRange')?.value || 'alltime';
        const batch = document.getElementById('filterBatch')?.value || 'all';
        const status = document.getElementById('filterStatus')?.value || 'all';
        const search = document.getElementById('filterSearch')?.value || '';

        let startDate = null, endDate = null;

        // Calculate date range
        if (dateRange === 'custom') {
            startDate = document.getElementById('startDate')?.value;
            endDate = document.getElementById('endDate')?.value;
            if (!startDate || !endDate) {
                this.showAlert('Please select both start and end dates', 'error');
                return;
            }
        } else if (dateRange !== 'alltime') {
            const dates = this.getDateRange(dateRange);
            startDate = dates.start;
            endDate = dates.end;
        }

        this.showLoader(true);

        try {
            const payload = {
                type: this.currentReportType,
                filters: {
                    startDate: startDate,
                    endDate: endDate,
                    batchId: batch,
                    status: status,
                    search: search
                },
                columns: selectedFields
            };

            console.log('📤 Sending payload:', payload);

            const response = await fetch('/api/reports/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            console.log('📥 Response:', data);

            if (data.success && data.report) {
                this.currentReportData = data.report;
                this.displayReport(data.report, selectedFields);
                this.showAlert(`Report generated: ${data.report.count} records`, 'success');
            } else {
                // Check if error is about unsupported report type
                if (data.error && data.error.includes('unsupported')) {
                    this.showAlert(`Payment reports are not yet supported by the backend. Please contact administrator.`, 'error');
                } else {
                    this.showAlert(data.error || 'Failed to generate report', 'error');
                }
            }
        } catch (error) {
            console.error('❌ Report generation error:', error);
            this.showAlert('Error generating report: ' + error.message, 'error');
        } finally {
            this.showLoader(false);
        }
    },

    displayReport(report, selectedFields) {
        const resultsDiv = document.getElementById('advancedReportResults');
        const statsDiv = document.getElementById('reportStatistics');
        const tableContainer = document.getElementById('reportTableContainer');

        if (!resultsDiv) return;

        // Show results section
        resultsDiv.style.display = 'block';

        // Display statistics
        if (statsDiv) {
            statsDiv.innerHTML = `
                <div class="stat-card">
                    <i class="fas fa-database"></i>
                    <h4>Total Records</h4>
                    <div class="stat-value">${report.count}</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-filter"></i>
                    <h4>Fields Selected</h4>
                    <div class="stat-value">${selectedFields.length}</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-clock"></i>
                    <h4>Generated</h4>
                    <div class="stat-value">${new Date(report.generated_at).toLocaleString()}</div>
                </div>
            `;
        }

        // Display table with improved styling for many columns
        if (tableContainer && report.data && report.data.length > 0) {
            const headers = selectedFields.map(f => {
                const field = this.FIELD_DEFINITIONS[this.currentReportType].find(d => d.name === f);
                return field ? field.label : f.replace(/_/g, ' ');
            });

            const headerRow = headers.map(h => `<th>${this.escapeHtml(h)}</th>`).join('');
            const bodyRows = report.data.map(row => {
                const cells = selectedFields.map(f => {
                    const value = row[f];
                    return `<td>${this.escapeHtml(this.formatValue(value))}</td>`;
                }).join('');
                return `<tr>${cells}</tr>`;
            }).join('');

            // Enhanced table wrapper with fixed height and horizontal scrolling
            tableContainer.innerHTML = `
                <div class="table-wrapper" style="max-height: 500px; overflow-y: auto; overflow-x: auto; border: 1px solid #ddd; border-radius: 4px;">
                    <table class="report-table" style="width: 100%; border-collapse: collapse; min-width: max-content;">
                        <thead style="position: sticky; top: 0; background: #f8f9fa; z-index: 10;">
                            <tr>${headerRow}</tr>
                        </thead>
                        <tbody>
                            ${bodyRows}
                        </tbody>
                    </table>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; padding: 5px 10px; background: #f8f9fa; border-radius: 4px;">
                    <span style="font-size: 12px; color: #666;">
                        <i class="fas fa-info-circle"></i> 
                        Scroll horizontally to see all ${selectedFields.length} columns
                    </span>
                    <span style="font-size: 12px; color: #666;">
                        ${report.data.length} records displayed
                    </span>
                </div>
            `;
        }
    },

    // Enhanced PDF export with better error handling
    exportToPDF(selectedFields) {
        // Check if jsPDF is available
        if (typeof jsPDF === 'undefined') {
            this.showAlert('PDF library (jsPDF) not loaded. Please include jsPDF library.', 'error');
            return;
        }

        try {
            const data = this.currentReportData.data;
            const headers = selectedFields.map(f => {
                const field = this.FIELD_DEFINITIONS[this.currentReportType].find(d => d.name === f);
                return field ? field.label : f.replace(/_/g, ' ');
            });

            const body = data.map(row => 
                selectedFields.map(f => this.formatValue(row[f]))
            );

            // Create PDF with landscape orientation for many columns
            const doc = new jsPDF('landscape', 'mm', 'a4');
            
            // Check if autoTable plugin is available
            if (typeof doc.autoTable === 'function') {
                doc.autoTable({
                    head: [headers],
                    body: body,
                    margin: 10,
                    styles: { fontSize: 8 },
                    headStyles: { fillColor: [41, 128, 185], textColor: 255, fontSize: 8 },
                    didDrawPage: (data) => {
                        doc.setFontSize(10);
                        doc.text(`Report: ${this.currentReportType.toUpperCase()}`, 14, 10);
                        doc.setFontSize(8);
                        doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 15);
                    },
                    // Handle many columns
                    pageBreak: 'auto',
                    tableWidth: 'auto',
                });
            } else {
                // Fallback without autoTable
                this.showAlert('PDF autoTable plugin not loaded. Using basic PDF export.', 'warning');
                
                // Simple text-based PDF
                doc.setFontSize(12);
                let y = 20;
                doc.text(`Report: ${this.currentReportType.toUpperCase()}`, 14, y);
                y += 10;
                
                // Add headers
                doc.setFontSize(10);
                let headerStr = headers.join(' | ');
                doc.text(headerStr, 14, y);
                y += 7;
                
                // Add data rows (limited for readability)
                const maxRows = Math.min(20, body.length);
                for (let i = 0; i < maxRows; i++) {
                    const rowStr = body[i].join(' | ');
                    const lines = doc.splitTextToSize(rowStr, 180);
                    lines.forEach(line => {
                        if (y > 270) {
                            doc.addPage();
                            y = 20;
                        }
                        doc.text(line, 14, y);
                        y += 5;
                    });
                }
                
                if (body.length > maxRows) {
                    doc.text(`... and ${body.length - maxRows} more records`, 14, y + 5);
                }
            }

            doc.save(`report_${this.currentReportType}_${new Date().toISOString().slice(0,10)}.pdf`);
            this.showAlert(`Exported ${data.length} records to PDF`, 'success');
        } catch (error) {
            console.error('PDF export error:', error);
            this.showAlert('PDF export failed: ' + error.message, 'error');
        }
    },

    // ... (rest of the methods remain the same)
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    formatValue(value) {
        if (value === null || value === undefined) return '-';
        if (typeof value === 'boolean') return value ? 'Yes' : 'No';
        if (typeof value === 'object') return JSON.stringify(value);
        return String(value);
    },

    getDateRange(range) {
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
                end.setHours(23,59,59,999);
                break;
            case 'thismonth':
                start.setDate(1);
                start.setHours(0,0,0,0);
                end.setHours(23,59,59,999);
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
                end.setHours(23,59,59,999);
                break;
        }

        return {
            start: start.toISOString().split('T')[0],
            end: end.toISOString().split('T')[0]
        };
    },

    setupExportButtons() {
        document.querySelectorAll('.export-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const format = e.target.closest('.export-btn').dataset.format;
                this.exportReport(format);
            });
        });
    },

    exportReport(format) {
        if (!this.currentReportData || !this.currentReportData.data || this.currentReportData.data.length === 0) {
            this.showAlert('No report data to export', 'error');
            return;
        }

        const selectedFields = Array.from(document.querySelectorAll('.field-checkbox:checked'))
            .map(cb => cb.value);

        if (format === 'csv') {
            this.exportToCSV(selectedFields);
        } else if (format === 'excel') {
            this.exportToExcel(selectedFields);
        } else if (format === 'pdf') {
            this.exportToPDF(selectedFields);
        }
    },

    exportToCSV(selectedFields) {
        const data = this.currentReportData.data;
        const headers = selectedFields.map(f => {
            const field = this.FIELD_DEFINITIONS[this.currentReportType].find(d => d.name === f);
            return field ? field.label : f.replace(/_/g, ' ');
        });

        let csv = headers.map(h => `"${h.replace(/"/g, '""')}"`).join(',') + '\n';
        
        data.forEach(row => {
            const cells = selectedFields.map(f => {
                let value = row[f] || '';
                if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                    value = `"${value.replace(/"/g, '""')}"`;
                }
                return value;
            });
            csv += cells.join(',') + '\n';
        });

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        this.downloadFile(blob, `report_${this.currentReportType}_${new Date().toISOString().slice(0,10)}.csv`);
        this.showAlert(`Exported ${data.length} records to CSV`, 'success');
    },

    exportToExcel(selectedFields) {
        if (typeof XLSX === 'undefined') {
            this.showAlert('Excel library not loaded. Using CSV instead.', 'error');
            this.exportToCSV(selectedFields);
            return;
        }

        try {
            const data = this.currentReportData.data;
            const headers = selectedFields.map(f => {
                const field = this.FIELD_DEFINITIONS[this.currentReportType].find(d => d.name === f);
                return field ? field.label : f.replace(/_/g, ' ');
            });

            const excelData = data.map(row => {
                const obj = {};
                selectedFields.forEach((f, i) => {
                    obj[headers[i]] = row[f];
                });
                return obj;
            });

            const ws = XLSX.utils.json_to_sheet(excelData);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, 'Report');
            XLSX.writeFile(wb, `report_${this.currentReportType}_${new Date().toISOString().slice(0,10)}.xlsx`);
            this.showAlert(`Exported ${data.length} records to Excel`, 'success');
        } catch (error) {
            console.error('Excel export error:', error);
            this.showAlert('Excel export failed: ' + error.message, 'error');
        }
    },

    downloadFile(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },

    async setupBatchFilter() {
        try {
            const response = await fetch('/api/batches');
            const data = await response.json();
            
            if (data.success && data.batches) {
                const select = document.getElementById('filterBatch');
                if (select) {
                    data.batches.forEach(batch => {
                        const option = document.createElement('option');
                        option.value = batch.id;
                        option.textContent = batch.batch_name;
                        select.appendChild(option);
                    });
                }
            }
        } catch (error) {
            console.error('Error loading batches:', error);
        }
    },

    showLoader(show) {
        const loader = document.getElementById('advancedReportLoader');
        if (loader) {
            loader.style.display = show ? 'block' : 'none';
            if (show) {
                loader.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating report...';
            }
        }
    },

    showAlert(message, type = 'info') {
        const alert = document.getElementById('advancedReportAlert');
        if (!alert) return;

        alert.className = `alert alert-${type}`;
        alert.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i> ${message}`;
        alert.style.display = 'block';

        setTimeout(() => {
            alert.style.display = 'none';
        }, 4000);
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    ADVANCED_REPORTS.init();
});

// Export for use
window.ADVANCED_REPORTS = ADVANCED_REPORTS;
console.log('✅ Advanced Reports Module Loaded');
