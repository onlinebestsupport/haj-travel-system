// ====== ADVANCED REPORTS MODULE WITH CUSTOM REPORTS ======
const ADVANCED_REPORTS = {
    currentReportType: 'travelers',
    currentReportData: null,
    selectedFields: [],

    // Field definitions for each report type
    FIELD_DEFINITIONS: {
        travelers: [
            { name: 'id', label: 'ID', type: 'number', default: true, category: 'Traveler Info' },
            { name: 'first_name', label: 'First Name', type: 'text', default: true, category: 'Personal Info' },
            { name: 'last_name', label: 'Last Name', type: 'text', default: true, category: 'Personal Info' },
            { name: 'passport_name', label: 'Passport Name', type: 'text', default: false, category: 'Passport Info' },
            { name: 'batch_id', label: 'Batch ID', type: 'number', default: true, category: 'Batch Info' },
            { name: 'batch_name', label: 'Batch Name', type: 'text', default: true, category: 'Batch Info' },
            { name: 'passport_no', label: 'Passport Number', type: 'text', default: true, category: 'Passport Info' },
            { name: 'passport_issue_date', label: 'Passport Issue Date', type: 'date', default: false, category: 'Passport Info' },
            { name: 'passport_expiry_date', label: 'Passport Expiry Date', type: 'date', default: true, category: 'Passport Info' },
            { name: 'passport_status', label: 'Passport Status', type: 'text', default: false, category: 'Passport Info' },
            { name: 'gender', label: 'Gender', type: 'text', default: false, category: 'Personal Info' },
            { name: 'dob', label: 'Date of Birth', type: 'date', default: false, category: 'Personal Info' },
            { name: 'mobile', label: 'Mobile', type: 'text', default: true, category: 'Contact Info' },
            { name: 'email', label: 'Email', type: 'text', default: true, category: 'Contact Info' },
            { name: 'aadhaar', label: 'Aadhaar', type: 'text', default: false, category: 'ID Documents' },
            { name: 'pan', label: 'PAN', type: 'text', default: false, category: 'ID Documents' },
            { name: 'aadhaar_pan_linked', label: 'Aadhaar-PAN Linked', type: 'text', default: false, category: 'ID Documents' },
            { name: 'vaccine_status', label: 'Vaccine Status', type: 'text', default: true, category: 'Health Info' },
            { name: 'wheelchair', label: 'Wheelchair Required', type: 'text', default: false, category: 'Health Info' },
            { name: 'place_of_birth', label: 'Place of Birth', type: 'text', default: false, category: 'Personal Info' },
            { name: 'place_of_issue', label: 'Place of Issue', type: 'text', default: false, category: 'Passport Info' },
            { name: 'passport_address', label: 'Passport Address', type: 'text', default: false, category: 'Passport Info' },
            { name: 'father_name', label: "Father's Name", type: 'text', default: false, category: 'Family Info' },
            { name: 'mother_name', label: "Mother's Name", type: 'text', default: false, category: 'Family Info' },
            { name: 'spouse_name', label: "Spouse's Name", type: 'text', default: false, category: 'Family Info' },
            { name: 'pin', label: 'PIN Code', type: 'text', default: false, category: 'Address Info' },
            { name: 'emergency_contact', label: 'Emergency Contact', type: 'text', default: false, category: 'Emergency Info' },
            { name: 'emergency_phone', label: 'Emergency Phone', type: 'text', default: false, category: 'Emergency Info' },
            { name: 'medical_notes', label: 'Medical Notes', type: 'text', default: false, category: 'Health Info' },
            { name: 'created_at', label: 'Created At', type: 'datetime', default: true, category: 'System Info' }
        ],
        batches: [
            { name: 'id', label: 'Batch ID', type: 'number', default: true, category: 'Batch Info' },
            { name: 'batch_name', label: 'Batch Name', type: 'text', default: true, category: 'Batch Info' },
            { name: 'status', label: 'Status', type: 'text', default: true, category: 'Batch Info' },
            { name: 'total_travelers', label: 'Total Travelers', type: 'number', default: true, category: 'Batch Statistics' },
            { name: 'start_date', label: 'Start Date', type: 'date', default: true, category: 'Batch Dates' },
            { name: 'end_date', label: 'End Date', type: 'date', default: true, category: 'Batch Dates' },
            { name: 'description', label: 'Description', type: 'text', default: false, category: 'Batch Info' },
            { name: 'created_at', label: 'Created At', type: 'datetime', default: false, category: 'System Info' }
        ],
        payments: [
            { name: 'id', label: 'Payment ID', type: 'number', default: true, category: 'Payment Details' },
            { name: 'traveler_id', label: 'Traveler ID', type: 'number', default: false, category: 'Payment Details' },
            { name: 'traveler_name', label: 'Traveler Name', type: 'text', default: true, category: 'Traveler Info' },
            { name: 'batch_id', label: 'Batch ID', type: 'number', default: true, category: 'Batch Info' },
            { name: 'batch_name', label: 'Batch Name', type: 'text', default: true, category: 'Batch Info' },
            { name: 'amount', label: 'Amount (₹)', type: 'currency', default: true, category: 'Payment Details' },
            { name: 'payment_method', label: 'Payment Method', type: 'text', default: true, category: 'Payment Details' },
            { name: 'status', label: 'Payment Status', type: 'text', default: true, category: 'Payment Details' },
            { name: 'transaction_id', label: 'Transaction ID', type: 'text', default: false, category: 'Payment Details' },
            { name: 'payment_date', label: 'Payment Date', type: 'date', default: true, category: 'Payment Details' },
            { name: 'created_at', label: 'Created At', type: 'datetime', default: false, category: 'System Info' }
        ],
    },

    init() {
        console.log('🚀 ADVANCED_REPORTS module initializing...');
        this.setupCustomReportUI();
        this.populateFieldSelector();
        this.setupExportButtons();
        this.setupBatchFilter();
        this.setupPaymentReportSupport();
        document.addEventListener('DOMContentLoaded', () => this.onReady());
    },

    onReady() {
        console.log('✅ DOM Ready - Reports page fully loaded');
        this.populateFieldSelector();
        this.checkPDFLibraries();
    },

    // Setup Custom Report UI
    setupCustomReportUI() {
        // Add custom report tab if not exists
        const reportTabs = document.querySelector('.report-tabs');
        if (reportTabs) {
            if (!document.querySelector('[data-report="custom"]')) {
                const customTab = document.createElement('button');
                customTab.className = 'report-tab';
                customTab.dataset.report = 'custom';
                customTab.innerHTML = '<i class="fas fa-layer-group"></i> Custom Report';
                customTab.onclick = () => this.switchReportCategory('custom');
                reportTabs.appendChild(customTab);
            }
        }

        // Add category filter for custom reports
        const fieldContainer = document.getElementById('fieldCheckboxContainer');
        if (fieldContainer && !document.getElementById('categoryFilter')) {
            const filterDiv = document.createElement('div');
            filterDiv.id = 'categoryFilter';
            filterDiv.style.cssText = 'margin-bottom: 10px; display: none;';
            filterDiv.innerHTML = `
                <select id="fieldCategoryFilter" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    <option value="all">All Categories</option>
                    <option value="Traveler Info">Traveler Info</option>
                    <option value="Personal Info">Personal Info</option>
                    <option value="Passport Info">Passport Info</option>
                    <option value="Contact Info">Contact Info</option>
                    <option value="Batch Info">Batch Info</option>
                    <option value="Payment Details">Payment Details</option>
                    <option value="Health Info">Health Info</option>
                    <option value="Family Info">Family Info</option>
                    <option value="Emergency Info">Emergency Info</option>
                    <option value="ID Documents">ID Documents</option>
                    <option value="Batch Statistics">Batch Statistics</option>
                    <option value="Batch Dates">Batch Dates</option>
                    <option value="System Info">System Info</option>
                    <option value="Address Info">Address Info</option>
                </select>
            `;
            fieldContainer.parentNode.insertBefore(filterDiv, fieldContainer);
            
            document.getElementById('fieldCategoryFilter')?.addEventListener('change', (e) => {
                this.filterFieldsByCategory(e.target.value);
            });
        }
    },

    // Filter fields by category
    filterFieldsByCategory(category) {
        const labels = document.querySelectorAll('.field-checkbox-label');
        labels.forEach(label => {
            const checkbox = label.querySelector('input[type="checkbox"]');
            if (!checkbox) return;
            
            // Check if this field belongs to the selected category
            const fieldName = checkbox.value;
            let fieldCategory = '';
            
            // Search in all field definitions
            for (const type in this.FIELD_DEFINITIONS) {
                const found = this.FIELD_DEFINITIONS[type].find(f => f.name === fieldName);
                if (found) {
                    fieldCategory = found.category || '';
                    break;
                }
            }
            
            if (category === 'all' || fieldCategory === category) {
                label.style.display = 'flex';
            } else {
                label.style.display = 'none';
            }
        });
    },

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

    setupPaymentReportSupport() {
        const statusFilter = document.getElementById('filterStatus');
        if (statusFilter) {
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
        if (!container) {
            console.error('❌ fieldCheckboxContainer not found!');
            return;
        }

        container.innerHTML = '';

        // Show/hide category filter
        const categoryFilter = document.getElementById('categoryFilter');
        if (categoryFilter) {
            categoryFilter.style.display = this.currentReportType === 'custom' ? 'block' : 'none';
        }

        let fields = [];
        
        if (this.currentReportType === 'custom') {
            // For custom reports, combine all fields with source info
            const allFields = [];
            for (const type in this.FIELD_DEFINITIONS) {
                const typeFields = this.FIELD_DEFINITIONS[type].map(f => ({
                    ...f,
                    source: type,
                    uniqueName: `${type}_${f.name}` // Unique name to avoid conflicts
                }));
                allFields.push(...typeFields);
            }
            
            // Group fields by category
            const categories = {};
            allFields.forEach(field => {
                const cat = field.category || 'Other';
                if (!categories[cat]) {
                    categories[cat] = [];
                }
                categories[cat].push(field);
            });
            
            // Add category headers and fields
            for (const category in categories) {
                const header = document.createElement('div');
                header.className = 'category-header';
                header.style.cssText = 'font-weight: bold; padding: 8px; background: #e9ecef; margin: 5px 0; border-radius: 4px; grid-column: 1 / -1;';
                header.textContent = `📁 ${category}`;
                container.appendChild(header);
                
                categories[category].forEach(field => {
                    const label = this.createFieldLabel(field);
                    container.appendChild(label);
                });
            }
            
            fields = allFields;
        } else {
            // Regular reports
            fields = this.FIELD_DEFINITIONS[this.currentReportType] || [];
            
            // Add search input if many fields
            if (fields.length > 15) {
                const searchInput = document.createElement('input');
                searchInput.type = 'text';
                searchInput.placeholder = '🔍 Search fields...';
                searchInput.className = 'field-search-input';
                searchInput.style.cssText = 'width: 100%; padding: 5px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px; grid-column: 1 / -1;';
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
                const label = this.createFieldLabel(field);
                container.appendChild(label);
            });
        }

        this.updateFieldCount();
        console.log(`✅ Populated ${fields.length} fields for ${this.currentReportType}`);
    },

    createFieldLabel(field) {
        const label = document.createElement('label');
        label.className = 'field-checkbox-label';
        label.style.cssText = 'display: flex; align-items: center; padding: 4px 8px; cursor: pointer; border-radius: 4px;';
        
        const defaultChecked = field.default ? 'checked' : '';
        const fieldValue = this.currentReportType === 'custom' ? field.uniqueName : field.name;
        
        let displayLabel = field.label;
        if (this.currentReportType === 'custom' && field.source) {
            const sourceIcons = {
                'travelers': '👤',
                'batches': '📦',
                'payments': '💳'
            };
            displayLabel = `${field.label} <span style="font-size: 10px; color: #666;">(${sourceIcons[field.source] || field.source})</span>`;
        }
        
        label.innerHTML = `
            <input type="checkbox" class="field-checkbox" value="${fieldValue}" ${defaultChecked} 
                   data-source="${field.source || ''}" 
                   data-original-name="${field.name}"
                   data-category="${field.category || ''}"
                   onchange="ADVANCED_REPORTS.updateFieldCount()">
            <span style="font-size: 13px;">${displayLabel}</span>
        `;
        
        return label;
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
        const selectedCheckboxes = document.querySelectorAll('.field-checkbox:checked');
        const selectedFields = Array.from(selectedCheckboxes).map(cb => cb.value);

        if (selectedFields.length === 0) {
            this.showAlert('Please select at least one field', 'error');
            return;
        }

        // For custom reports, map fields to their sources
        let customFieldMapping = null;
        let reportType = this.currentReportType;

        if (this.currentReportType === 'custom') {
            customFieldMapping = {};
            selectedCheckboxes.forEach(cb => {
                const source = cb.dataset.source;
                const originalName = cb.dataset.originalName;
                if (source && originalName) {
                    if (!customFieldMapping[source]) {
                        customFieldMapping[source] = [];
                    }
                    customFieldMapping[source].push(originalName);
                }
            });
            
            const neededTypes = Object.keys(customFieldMapping);
            if (neededTypes.length === 0) {
                this.showAlert('No valid fields selected', 'error');
                return;
            }
            
            reportType = 'custom';
        }

        // Get filters
        const dateRange = document.getElementById('dateRange')?.value || 'alltime';
        const batch = document.getElementById('filterBatch')?.value || 'all';
        const status = document.getElementById('filterStatus')?.value || 'all';
        const search = document.getElementById('filterSearch')?.value || '';

        let startDate = null, endDate = null;

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
                type: reportType,
                filters: {
                    startDate: startDate,
                    endDate: endDate,
                    batchId: batch,
                    status: status,
                    search: search
                },
                columns: selectedFields
            };

            // Add custom field mapping for custom reports
            if (this.currentReportType === 'custom' && customFieldMapping) {
                payload.customMapping = customFieldMapping;
            }

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

        resultsDiv.style.display = 'block';

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

        if (tableContainer && report.data && report.data.length > 0) {
            const headers = selectedFields.map(f => {
                let fieldDef = null;
                
                // For custom reports, try to find field definition
                if (this.currentReportType === 'custom') {
                    for (const type in this.FIELD_DEFINITIONS) {
                        const found = this.FIELD_DEFINITIONS[type].find(d => f === `${type}_${d.name}`);
                        if (found) {
                            fieldDef = found;
                            break;
                        }
                    }
                } else {
                    fieldDef = this.FIELD_DEFINITIONS[this.currentReportType].find(d => d.name === f);
                }
                
                return fieldDef ? fieldDef.label : f.replace(/_/g, ' ');
            });

            const headerRow = headers.map(h => `<th>${this.escapeHtml(h)}</th>`).join('');
            const bodyRows = report.data.map(row => {
                const cells = selectedFields.map(f => {
                    let value = row[f];
                    // For custom reports, try without prefix
                    if (value === undefined && this.currentReportType === 'custom') {
                        const cleanName = f.split('_').slice(1).join('_');
                        value = row[cleanName];
                    }
                    return `<td>${this.escapeHtml(this.formatValue(value))}</td>`;
                }).join('');
                return `<tr>${cells}</tr>`;
            }).join('');

            const needsScrolling = selectedFields.length > 10;

            tableContainer.innerHTML = `
                <div class="table-wrapper" style="max-height: 500px; overflow-y: auto; overflow-x: auto; border: 1px solid #ddd; border-radius: 4px;">
                    <table class="report-table" style="width: 100%; border-collapse: collapse; min-width: ${needsScrolling ? 'max-content' : '100%'};">
                        <thead style="position: sticky; top: 0; background: #f8f9fa; z-index: 10; box-shadow: 0 2px 2px rgba(0,0,0,0.1);">
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
                        ${needsScrolling ? `Scroll horizontally to see all ${selectedFields.length} columns` : `${selectedFields.length} columns displayed`}
                    </span>
                    <span style="font-size: 12px; color: #666;">
                        ${report.data.length} records displayed
                    </span>
                </div>
            `;
        }
    },

    exportToPDF(selectedFields) {
        if (typeof jsPDF === 'undefined') {
            this.showAlert('PDF library (jsPDF) not loaded. Please include jsPDF library.', 'error');
            return;
        }

        try {
            const data = this.currentReportData.data;
            const headers = selectedFields.map(f => {
                let fieldDef = null;
                if (this.currentReportType === 'custom') {
                    for (const type in this.FIELD_DEFINITIONS) {
                        const found = this.FIELD_DEFINITIONS[type].find(d => f === `${type}_${d.name}`);
                        if (found) {
                            fieldDef = found;
                            break;
                        }
                    }
                } else {
                    fieldDef = this.FIELD_DEFINITIONS[this.currentReportType].find(d => d.name === f);
                }
                return fieldDef ? fieldDef.label : f.replace(/_/g, ' ');
            });

            const body = data.map(row => 
                selectedFields.map(f => {
                    let value = row[f];
                    if (value === undefined && this.currentReportType === 'custom') {
                        const cleanName = f.split('_').slice(1).join('_');
                        value = row[cleanName];
                    }
                    return this.formatValue(value);
                })
            );

            const doc = new jsPDF('landscape', 'mm', 'a4');
            
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
                    pageBreak: 'auto',
                    tableWidth: 'auto',
                });
            } else {
                // Fallback without autoTable
                this.showAlert('PDF autoTable plugin not loaded. Using basic PDF export.', 'warning');
                
                doc.setFontSize(12);
                let y = 20;
                doc.text(`Report: ${this.currentReportType.toUpperCase()}`, 14, y);
                y += 10;
                
                doc.setFontSize(10);
                let headerStr = headers.join(' | ');
                doc.text(headerStr, 14, y);
                y += 7;
                
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
            let fieldDef = null;
            if (this.currentReportType === 'custom') {
                for (const type in this.FIELD_DEFINITIONS) {
                    const found = this.FIELD_DEFINITIONS[type].find(d => f === `${type}_${d.name}`);
                    if (found) {
                        fieldDef = found;
                        break;
                    }
                }
            } else {
                fieldDef = this.FIELD_DEFINITIONS[this.currentReportType].find(d => d.name === f);
            }
            return fieldDef ? fieldDef.label : f.replace(/_/g, ' ');
        });

        let csv = headers.map(h => `"${h.replace(/"/g, '""')}"`).join(',') + '\n';
        
        data.forEach(row => {
            const cells = selectedFields.map(f => {
                let value = row[f] || '';
                if (value === undefined && this.currentReportType === 'custom') {
                    const cleanName = f.split('_').slice(1).join('_');
                    value = row[cleanName] || '';
                }
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
                let fieldDef = null;
                if (this.currentReportType === 'custom') {
                    for (const type in this.FIELD_DEFINITIONS) {
                        const found = this.FIELD_DEFINITIONS[type].find(d => f === `${type}_${d.name}`);
                        if (found) {
                            fieldDef = found;
                            break;
                        }
                    }
                } else {
                    fieldDef = this.FIELD_DEFINITIONS[this.currentReportType].find(d => d.name === f);
                }
                return fieldDef ? fieldDef.label : f.replace(/_/g, ' ');
            });

            const excelData = data.map(row => {
                const obj = {};
                selectedFields.forEach((f, i) => {
                    let value = row[f];
                    if (value === undefined && this.currentReportType === 'custom') {
                        const cleanName = f.split('_').slice(1).join('_');
                        value = row[cleanName];
                    }
                    obj[headers[i]] = value;
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
console.log('✅ Advanced Reports Module with Custom Reports Loaded');
