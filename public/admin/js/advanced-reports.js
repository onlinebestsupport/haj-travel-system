// ====== ADVANCED REPORTS MODULE ======
const ADVANCED_REPORTS = {
    currentReportType: 'travelers',
    currentReportData: null,
    selectedFields: [],

    // Field definitions for each report type
    FIELD_DEFINITIONS: {
        travelers: [
            { name: 'id', label: 'ID' },
            { name: 'first_name', label: 'First Name' },
            { name: 'last_name', label: 'Last Name' },
            { name: 'email', label: 'Email' },
            { name: 'mobile', label: 'Mobile' },
            { name: 'passport_no', label: 'Passport No' },
            { name: 'passport_expiry', label: 'Passport Expiry' },
            { name: 'passport_status', label: 'Passport Status' },
            { name: 'visa_status', label: 'Visa Status' },
            { name: 'date_of_birth', label: 'Date of Birth' },
            { name: 'gender', label: 'Gender' },
            { name: 'nationality', label: 'Nationality' },
            { name: 'batch_name', label: 'Batch' },
            { name: 'medical_cleared', label: 'Medical Cleared' },
            { name: 'document_status', label: 'Document Status' },
            { name: 'hotel_preference', label: 'Hotel Preference' },
            { name: 'seat_number', label: 'Seat Number' },
            { name: 'payment_status', label: 'Payment Status' },
            { name: 'created_at', label: 'Created Date' },
            { name: 'updated_at', label: 'Updated Date' }
        ],
        batches: [
            { name: 'id', label: 'Batch ID' },
            { name: 'batch_name', label: 'Batch Name' },
            { name: 'status', label: 'Status' },
            { name: 'total_seats', label: 'Total Seats' },
            { name: 'booked_seats', label: 'Booked Seats' },
            { name: 'amount', label: 'Amount' },
            { name: 'start_date', label: 'Start Date' },
            { name: 'end_date', label: 'End Date' },
            { name: 'travelers_count', label: 'Travelers Count' },
            { name: 'total_collected', label: 'Total Collected' },
            { name: 'created_at', label: 'Created Date' }
        ],
        payments: [
            { name: 'id', label: 'Payment ID' },
            { name: 'traveler_name', label: 'Traveler Name' },
            { name: 'batch_name', label: 'Batch Name' },
            { name: 'amount', label: 'Amount' },
            { name: 'payment_method', label: 'Payment Method' },
            { name: 'status', label: 'Status' },
            { name: 'payment_date', label: 'Payment Date' },
            { name: 'transaction_id', label: 'Transaction ID' },
            { name: 'created_at', label: 'Created Date' }
        ]
    },

    init() {
        console.log('🚀 ADVANCED_REPORTS module initializing...');
        this.populateFieldSelector();
        this.setupExportButtons();
        this.setupBatchFilter();
        document.addEventListener('DOMContentLoaded', () => this.onReady());
    },

    onReady() {
        console.log('✅ DOM Ready - Reports page fully loaded');
        this.populateFieldSelector();
    },

    populateFieldSelector() {
        const container = document.getElementById('fieldCheckboxContainer');
        const fields = this.FIELD_DEFINITIONS[this.currentReportType] || [];
        
        if (!container) {
            console.error('❌ fieldCheckboxContainer not found!');
            return;
        }

        container.innerHTML = '';

        fields.forEach(field => {
            const label = document.createElement('label');
            label.className = 'field-checkbox-label';
            label.innerHTML = `
                <input type="checkbox" class="field-checkbox" value="${field.name}" checked onchange="ADVANCED_REPORTS.updateFieldCount()">
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
        console.log(`✅ Switched to ${reportType} report`);
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
        // For alltime, leave startDate and endDate as null

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
                this.showAlert(data.error || 'Failed to generate report', 'error');
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

        // Display table
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

            tableContainer.innerHTML = `
                <div class="table-wrapper">
                    <table class="report-table">
                        <thead>
                            <tr>${headerRow}</tr>
                        </thead>
                        <tbody>
                            ${bodyRows}
                        </tbody>
                    </table>
                </div>
            `;
        }
    },

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

    exportToPDF(selectedFields) {
        if (typeof jsPDF === 'undefined') {
            this.showAlert('PDF library not loaded', 'error');
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

            const doc = new jsPDF();
            doc.autoTable({
                head: [headers],
                body: body,
                margin: 10,
                didDrawPage: (data) => {
                    doc.setFontSize(10);
                    doc.text(`Report: ${this.currentReportType}`, 14, 10);
                }
            });

            doc.save(`report_${this.currentReportType}_${new Date().toISOString().slice(0,10)}.pdf`);
            this.showAlert(`Exported ${data.length} records to PDF`, 'success');
        } catch (error) {
            console.error('PDF export error:', error);
            this.showAlert('PDF export failed: ' + error.message, 'error');
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
