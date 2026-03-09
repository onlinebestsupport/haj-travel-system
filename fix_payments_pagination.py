# fix_payments_pagination.py
import os
import shutil
from datetime import datetime

print("=" * 60)
print("🚀 FIXING payments.html - Adding Pagination & Enhancements")
print("=" * 60)

# Create backup
backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(backup_dir, exist_ok=True)
print(f"📁 Created backup folder: {backup_dir}/")

html_path = "public/admin/payments.html"
backup_path = f"{backup_dir}/payments.html.bak"

# Create backup
shutil.copy2(html_path, backup_path)
print(f"✅ Backup created: {backup_path}")

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# ====== FIX 1: Add Receipt Generation Button ======
print("\n🔧 Adding receipt generation button...")

if 'Generate Receipt' not in content:
    receipt_button = '''
                            <button class="icon-btn" onclick="generateReceipt(${payment.id})" title="Generate Receipt">
                                <i class="fas fa-receipt"></i>
                            </button>'''
    
    # Add to actions column
    if 'fa-print' in content or 'print' in content.lower():
        content = content.replace(
            'fa-print" onclick="printPayment',
            'fa-receipt" onclick="generateReceipt' + receipt_button + '\n                            <button class="icon-btn" onclick="printPayment" title="Print"><i class="fas fa-print'
        )
        print("   ✅ Receipt button added")
    else:
        print("   ⚠️ Could not find insertion point")

# ====== FIX 2: Add Pagination HTML ======
if 'pagination' not in content.lower() and 'showingFrom' not in content:
    print("\n🔧 Adding pagination HTML...")
    
    pagination_html = '''
        <!-- Pagination -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px;">
            <div id="paginationInfo">
                Showing <span id="showingFrom">1</span> to <span id="showingTo">10</span> of <span id="totalCount">0</span> payments
            </div>
            <div style="display: flex; gap: 10px;">
                <button class="action-btn btn-secondary" onclick="previousPage()" id="prevPageBtn" disabled>
                    <i class="fas fa-chevron-left"></i> Previous
                </button>
                <button class="action-btn btn-primary" onclick="nextPage()" id="nextPageBtn">
                    Next <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        </div>'''
    
    # Insert before closing container
    if '</div>\n\n    <!-- Payment Summary Modal -->' in content:
        content = content.replace('</div>\n\n    <!-- Payment Summary Modal -->', pagination_html + '\n    </div>\n\n    <!-- Payment Summary Modal -->')
        print("   ✅ Pagination HTML added")
    else:
        print("   ⚠️ Could not find insertion point")

# ====== FIX 3: Add Pagination JavaScript ======
if 'function previousPage' not in content:
    print("\n🔧 Adding pagination JavaScript...")
    
    pagination_js = '''
    // ====== PAGINATION VARIABLES ======
    let currentPage = 1;
    let itemsPerPage = 10;
    let allPayments = [];
    
    // ====== PAGINATION FUNCTIONS ======
    function updatePaginationDisplay() {
        const totalPages = Math.ceil(allPayments.length / itemsPerPage);
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = Math.min(startIndex + itemsPerPage, allPayments.length);
        
        document.getElementById('showingFrom').textContent = allPayments.length > 0 ? startIndex + 1 : 0;
        document.getElementById('showingTo').textContent = endIndex;
        document.getElementById('totalCount').textContent = allPayments.length;
        document.getElementById('prevPageBtn').disabled = currentPage === 1;
        document.getElementById('nextPageBtn').disabled = currentPage === totalPages;
    }
    
    function nextPage() {
        const totalPages = Math.ceil(allPayments.length / itemsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            updatePaginationDisplay();
        }
    }
    
    function previousPage() {
        if (currentPage > 1) {
            currentPage--;
            updatePaginationDisplay();
        }
    }
    '''
    
    # Find script section and add before closing tag
    if '</script>' in content:
        content = content.replace('</script>', pagination_js + '\n    </script>')
        print("   ✅ Pagination JavaScript added")
    else:
        print("   ⚠️ Could not find script section")

# Write the modified content back
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ payments.html has been fixed!")
print("=" * 60)
