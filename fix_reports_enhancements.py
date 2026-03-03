# fix_reports_enhancements.py
import os
import shutil
from datetime import datetime

print("=" * 60)
print("🚀 FIXING reports.html - Adding Enhancements")
print("=" * 60)

# Create backup
backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(backup_dir, exist_ok=True)
print(f"📁 Created backup folder: {backup_dir}/")

html_path = "public/admin/reports.html"
backup_path = f"{backup_dir}/reports.html.bak"

# Create backup
shutil.copy2(html_path, backup_path)
print(f"✅ Backup created: {backup_path}")

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# ============================================================
# FIX 1: Add Loading Indicator
# ============================================================
print("\n🔧 Adding loading indicator...")

loading_html = '''
        <!-- Loading Overlay -->
        <div id="reportLoadingOverlay" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.8); z-index: 9999; justify-content: center; align-items: center; flex-direction: column;">
            <div class="spinner" style="width: 60px; height: 60px; border: 6px solid #f3f3f3; border-top: 6px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite;"></div>
            <p style="margin-top: 20px; color: #2c3e50; font-size: 1.2rem;">Generating report...</p>
        </div>'''

if 'reportLoadingOverlay' not in content:
    # Insert after body start
    if '<body>' in content:
        content = content.replace('<body>', '<body>\n' + loading_html)
        print("   ✅ Loading indicator added")

# ============================================================
# FIX 2: Add Report Saving Functionality
# ============================================================
print("\n🔧 Adding report saving functionality...")

save_report_html = '''
        <!-- Save Report Modal -->
        <div id="saveReportModal" class="modal" style="display: none;">
            <div class="modal-header">
                <h3><i class="fas fa-save"></i> Save Report Configuration</h3>
                <button class="modal-close" onclick="closeSaveReportModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>Report Name</label>
                    <input type="text" id="savedReportName" placeholder="e.g., Monthly Payment Summary">
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea id="savedReportDesc" rows="3" placeholder="What does this report show?"></textarea>
                </div>
                <div class="form-group">
                    <label>Auto-generate Schedule</label>
                    <select id="reportSchedule">
                        <option value="none">No schedule</option>
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="monthly">Monthly</option>
                        <option value="quarterly">Quarterly</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Email to</label>
                    <input type="email" id="reportEmail" placeholder="recipient@example.com">
                </div>
            </div>
            <div class="modal-footer">
                <button class="action-btn btn-success" onclick="saveReportConfig()">
                    <i class="fas fa-save"></i> Save Report
                </button>
                <button class="action-btn btn-secondary" onclick="closeSaveReportModal()">
                    Cancel
                </button>
            </div>
        </div>'''

if 'saveReportModal' not in content:
    # Insert before closing body
    if '</body>' in content:
        content = content.replace('</body>', save_report_html + '\n</body>')
        print("   ✅ Save report modal added")

# ============================================================
# FIX 3: Add Saved Reports List
# ============================================================
print("\n🔧 Adding saved reports list...")

saved_reports_html = '''
        <!-- Saved Reports Panel -->
        <div class="dashboard-card" style="margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3><i class="fas fa-history"></i> Saved Reports</h3>
                <button class="action-btn btn-secondary" onclick="refreshSavedReports()">
                    <i class="fas fa-sync"></i> Refresh
                </button>
            </div>
            <div id="savedReportsList" style="margin-top: 15px;">
                <div style="text-align: center; padding: 20px; color: #7f8c8d;">
                    <i class="fas fa-inbox" style="font-size: 2rem; margin-bottom: 10px;"></i>
                    <p>No saved reports yet. Generate and save a report to see it here.</p>
                </div>
            </div>
        </div>'''

if 'Saved Reports' not in content:
    # Insert after report filters
    if '</div>\n\n        <!-- Column Selector -->' in content:
        content = content.replace(
            '</div>\n\n        <!-- Column Selector -->',
            '</div>\n' + saved_reports_html + '\n        <!-- Column Selector -->'
        )
        print("   ✅ Saved reports panel added")

# ============================================================
# FIX 4: Add Email Report Button
# ============================================================
print("\n🔧 Adding email report button...")

email_button = '''
                        <button class="action-btn btn-info" onclick="emailReport()" id="emailReportBtn">
                            <i class="fas fa-envelope"></i> Email Report
                        </button>'''

if 'emailReportBtn' not in content:
    # Add after export buttons
    content = content.replace(
        '</button>\n                        </div>',
        '</button>\n                        ' + email_button + '\n                        </div>'
    )
    print("   ✅ Email report button added")

# ============================================================
# FIX 5: Add Chart Type Selector
# ============================================================
print("\n🔧 Adding chart type selector...")

chart_selector = '''
                            <select id="chartTypeSelector" onchange="changeChartType()">
                                <option value="pie">Pie Chart</option>
                                <option value="bar">Bar Chart</option>
                                <option value="line">Line Chart</option>
                                <option value="area">Area Chart</option>
                                <option value="doughnut">Doughnut Chart</option>
                            </select>'''

# Add to first chart header
if '<select id="paymentChartPeriod">' in content:
    content = content.replace(
        '<select id="paymentChartPeriod">',
        '<select id="chartTypeSelector" onchange="changeChartType()">\n                                <option value="pie">Pie Chart</option>\n                                <option value="bar">Bar Chart</option>\n                                <option value="line">Line Chart</option>\n                                <option value="area">Area Chart</option>\n                                <option value="doughnut">Doughnut Chart</option>\n                            </select>\n                            <select id="paymentChartPeriod">'
    )
    print("   ✅ Chart type selector added")

# ============================================================
# FIX 6: Add JavaScript Functions
# ============================================================
print("\n🔧 Adding JavaScript enhancement functions...")

enhancement_js = '''

    // ==================== REPORT SAVING FUNCTIONS ====================
    let savedReports = JSON.parse(localStorage.getItem('savedReports') || '[]');

    function showSaveReportModal() {
        document.getElementById('saveReportModal').style.display = 'block';
        document.getElementById('modalOverlay').style.display = 'block';
    }

    function closeSaveReportModal() {
        document.getElementById('saveReportModal').style.display = 'none';
        document.getElementById('modalOverlay').style.display = 'none';
    }

    function saveReportConfig() {
        const name = document.getElementById('savedReportName').value;
        const desc = document.getElementById('savedReportDesc').value;
        const schedule = document.getElementById('reportSchedule').value;
        const email = document.getElementById('reportEmail').value;
        
        if (!name) {
            showNotification('Please enter a report name', 'error');
            return;
        }
        
        const reportConfig = {
            id: Date.now(),
            name: name,
            description: desc,
            schedule: schedule,
            email: email,
            type: currentReportType,
            filters: {
                dateRange: document.getElementById('dateRange').value,
                startDate: document.getElementById('startDate').value,
                endDate: document.getElementById('endDate').value,
                batch: document.getElementById('reportBatch').value,
                status: document.getElementById('reportStatus').value
            },
            createdAt: new Date().toISOString()
        };
        
        savedReports.push(reportConfig);
        localStorage.setItem('savedReports', JSON.stringify(savedReports));
        
        refreshSavedReports();
        closeSaveReportModal();
        showNotification('Report configuration saved!', 'success');
    }

    function refreshSavedReports() {
        const container = document.getElementById('savedReportsList');
        if (!container) return;
        
        savedReports = JSON.parse(localStorage.getItem('savedReports') || '[]');
        
        if (savedReports.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #7f8c8d;">
                    <i class="fas fa-inbox" style="font-size: 2rem; margin-bottom: 10px;"></i>
                    <p>No saved reports yet. Generate and save a report to see it here.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        savedReports.forEach(report => {
            html += `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 15px; border: 1px solid #ecf0f1; border-radius: 8px; margin-bottom: 10px; background: white;">
                    <div>
                        <strong>${report.name}</strong>
                        <p style="font-size: 0.85rem; color: #7f8c8d; margin-top: 5px;">${report.description || 'No description'}</p>
                        <small>${report.type} report • ${new Date(report.createdAt).toLocaleDateString()}</small>
                    </div>
                    <div style="display: flex; gap: 5px;">
                        <button class="icon-btn" onclick="loadSavedReport(${report.id})" title="Load Report">
                            <i class="fas fa-folder-open"></i>
                        </button>
                        <button class="icon-btn" onclick="deleteSavedReport(${report.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                        ${report.schedule !== 'none' ? '<span class="status-badge status-active">Auto</span>' : ''}
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }

    function loadSavedReport(reportId) {
        const report = savedReports.find(r => r.id === reportId);
        if (!report) return;
        
        // Apply filters
        document.getElementById('dateRange').value = report.filters.dateRange;
        document.getElementById('startDate').value = report.filters.startDate || '';
        document.getElementById('endDate').value = report.filters.endDate || '';
        document.getElementById('reportBatch').value = report.filters.batch;
        document.getElementById('reportStatus').value = report.filters.status;
        
        toggleDateInputs();
        generateReport();
        
        showNotification(`Loaded report: ${report.name}`, 'success');
    }

    function deleteSavedReport(reportId) {
        if (!confirm('Delete this saved report?')) return;
        
        savedReports = savedReports.filter(r => r.id !== reportId);
        localStorage.setItem('savedReports', JSON.stringify(savedReports));
        refreshSavedReports();
        showNotification('Report deleted', 'success');
    }

    // ==================== EMAIL REPORT ====================
    function emailReport() {
        if (!currentReportData) {
            showNotification('No report data to email', 'error');
            return;
        }
        
        const email = prompt('Enter email address(es) - separate multiple with commas:');
        if (!email) return;
        
        showNotification('Preparing email...', 'info');
        
        // Create email content
        const subject = `Alhudha Haj Report - ${new Date().toLocaleDateString()}`;
        let body = `Report generated on: ${new Date().toLocaleString()}\\n\\n`;
        body += `SUMMARY:\\n`;
        body += `- Travelers: ${currentReportData.summary?.totalTravelers || 0}\\n`;
        body += `- Batches: ${currentReportData.summary?.totalBatches || 0}\\n`;
        body += `- Collections: ₹${(currentReportData.summary?.totalPayments || 0).toLocaleString()}\\n\\n`;
        body += `See attached report for details.`;
        
        window.location.href = `mailto:${email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
        
        showNotification('Email client opened', 'success');
    }

    // ==================== CHART TYPE CHANGE ====================
    function changeChartType() {
        const type = document.getElementById('chartTypeSelector').value;
        
        if (!currentReportData) {
            showNotification('Generate a report first', 'warning');
            return;
        }
        
        // Update chart types
        if (paymentsChart) {
            paymentsChart.destroy();
            createPaymentsChart(currentReportData.paymentsByMethod, type);
        }
        
        if (travelersChart) {
            travelersChart.destroy();
            createTravelersChart(currentReportData.travelersByBatch, type === 'pie' || type === 'doughnut' ? 'bar' : type);
        }
    }

    // ==================== LOADING INDICATOR ====================
    function showReportLoading() {
        document.getElementById('reportLoadingOverlay').style.display = 'flex';
    }

    function hideReportLoading() {
        document.getElementById('reportLoadingOverlay').style.display = 'none';
    }

    // Override generateReport to show loading
    const originalGenerateReport = generateReport;
    generateReport = async function() {
        showReportLoading();
        try {
            await originalGenerateReport();
        } finally {
            hideReportLoading();
        }
    };

    // Initialize saved reports on load
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(refreshSavedReports, 500);
    });'''
    
content = content.replace('</script>', enhancement_js + '\n</script>')
print("   ✅ Enhancement JavaScript functions added")

# ============================================================
# FIX 7: Add Save Button to Report Actions
# ============================================================
print("\n🔧 Adding save report button...")

save_button = '''
                        <button class="action-btn btn-warning" onclick="showSaveReportModal()" id="saveReportBtn">
                            <i class="fas fa-save"></i> Save Report
                        </button>'''

if 'saveReportBtn' not in content:
    # Add after other buttons
    content = content.replace(
        '</button>\n                        <button class="action-btn btn-secondary" onclick="printReport()">',
        '</button>\n                        ' + save_button + '\n                        <button class="action-btn btn-secondary" onclick="printReport()">'
    )
    print("   ✅ Save report button added")

# ============================================================
# Write the file
# ============================================================
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "=" * 60)
print("✅ reports.html FIX COMPLETE!")
print("=" * 60)
print(f"\n📁 Backup saved: {backup_path}")
print("\n📋 FIXES APPLIED:")
print("   1. ✅ Loading indicator added")
print("   2. ✅ Save report modal added")
print("   3. ✅ Saved reports panel added")
print("   4. ✅ Email report button added")
print("   5. ✅ Chart type selector added")
print("   6. ✅ Enhancement JavaScript functions added")
print("   7. ✅ Save report button added")
print("\n⚠️ MANUAL CHECKS NEEDED:")
print("   - Test loading indicator")
print("   - Verify report saving/loading")
print("   - Test email functionality")
print("   - Try different chart types")
print("   - Check saved reports persistence")
print("\n🚀 NEXT STEPS:")
print("   1. Test reports.html in browser")
print("   2. If issues, restore from backup")
print("   3. Run: git add public/admin/reports.html")
print("   4. Run: git commit -m \"Add report saving, email, chart types and loading indicators to reports page\"")
print("   5. Run: git push origin main")