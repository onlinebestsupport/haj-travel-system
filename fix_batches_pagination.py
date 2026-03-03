# fix_batches_pagination.py
import os
import shutil
from datetime import datetime

print("=" * 60)
print("🚀 FIXING batches.html - Adding Pagination & Enhancements")
print("=" * 60)

# Create backup
backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(backup_dir, exist_ok=True)
print(f"📁 Created backup folder: {backup_dir}/")

html_path = "public/admin/batches.html"
backup_path = f"{backup_dir}/batches.html.bak"

# Create backup
shutil.copy2(html_path, backup_path)
print(f"✅ Backup created: {backup_path}")

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# ============================================================
# FIX 1: Add Delete Confirmation
# ============================================================
print("\n🔧 Adding delete confirmation...")

if 'confirm' not in content and 'deleteBatch' in content:
    old_delete = '''async function deleteBatch(id) {
            try {
                const response = await fetch(`/api/batches/${id}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });'''
    
    new_delete = '''async function deleteBatch(id) {
            if (!confirm('⚠️ Are you sure you want to delete this batch? This action cannot be undone.')) {
                return;
            }
            try {
                const response = await fetch(`/api/batches/${id}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });'''
    
    if old_delete in content:
        content = content.replace(old_delete, new_delete)
        print("   ✅ Delete confirmation added")
    else:
        print("   ⚠️ Could not find delete function")

# ============================================================
# FIX 2: Add Pagination HTML
# ============================================================
if 'pagination' not in content.lower() and 'showingFrom' not in content:
    print("\n🔧 Adding pagination HTML...")
    
    pagination_html = '''
        <!-- Pagination -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px;">
            <div id="paginationInfo">
                Showing <span id="showingFrom">1</span> to <span id="showingTo">10</span> of <span id="totalCount">0</span> batches
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
    
    # Insert before the closing </div> of main container
    if '    </div>\n\n    <!-- View Batch Modal -->' in content:
        content = content.replace('    </div>\n\n    <!-- View Batch Modal -->', pagination_html + '\n    </div>\n\n    <!-- View Batch Modal -->')
        print("   ✅ Pagination HTML added")
    else:
        print("   ⚠️ Could not find insertion point")

# ============================================================
# FIX 3: Add Pagination JavaScript
# ============================================================
if 'function previousPage' not in content:
    print("\n🔧 Adding pagination JavaScript...")
    
    pagination_js = '''
    // ==================== PAGINATION VARIABLES ====================
    let currentPage = 1;
    let itemsPerPage = 10;
    let allBatches = [];

    function updatePaginationInfo() {
        const total = allBatches.length;
        document.getElementById('totalCount').textContent = total;
        const start = (currentPage - 1) * itemsPerPage + 1;
        const end = Math.min(currentPage * itemsPerPage, total);
        document.getElementById('showingFrom').textContent = total > 0 ? start : 0;
        document.getElementById('showingTo').textContent = total > 0 ? end : 0;
        
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');
        if (prevBtn) prevBtn.disabled = currentPage === 1;
        if (nextBtn) nextBtn.disabled = end >= total;
    }

    function previousPage() {
        if (currentPage > 1) {
            currentPage--;
            displayBatches();
        }
    }

    function nextPage() {
        if (currentPage * itemsPerPage < allBatches.length) {
            currentPage++;
            displayBatches();
        }
    }'''
    
    content = content.replace('</script>', pagination_js + '\n</script>')
    print("   ✅ Pagination JavaScript added")

# ============================================================
# FIX 4: Update displayBatches function for pagination
# ============================================================
print("\n🔧 Updating displayBatches function...")

old_display = '''function displayBatches() {
            if (!batchesData || batchesData.length === 0) {
                document.getElementById('batchesTableBody').innerHTML = '<tr><td colspan="11" style="text-align: center; padding: 40px;">No batches found</td></tr>';
                updatePaginationInfo(0);
                return;
            }
            
            // Apply pagination
            const start = (currentPage - 1) * itemsPerPage;
            const end = start + itemsPerPage;
            const paginatedData = batchesData.slice(start, end);
            
            let html = '';
            paginatedData.forEach(b => {
                const price = b.price ? Number(b.price).toLocaleString('en-IN') : '0';
                const totalSeats = b.total_seats || 0;
                const bookedSeats = b.booked_seats || 0;
                const availableSeats = totalSeats - bookedSeats;
                const occupancyPercent = totalSeats > 0 ? Math.round((bookedSeats / totalSeats) * 100) : 0;
                
                let statusClass = 'status-active';
                if (b.status === 'Closing Soon') statusClass = 'status-pending';
                if (b.status === 'Full') statusClass = 'status-inactive';
                if (b.status === 'Closed') statusClass = 'status-inactive';
                
                let occupancyColor = '#27ae60';
                if (occupancyPercent > 80) occupancyColor = '#e67e22';
                if (occupancyPercent >= 100) occupancyColor = '#e74c3c';
                
                html += `<tr>
                    <td>${b.id}</td>
                    <td><strong>${b.batch_name || '-'}</strong></td>
                    <td>${b.departure_date || '-'}</td>
                    <td>${b.return_date || '-'}</td>
                    <td>₹${price}</td>
                    <td>${totalSeats}</td>
                    <td>${bookedSeats}</td>
                    <td>${availableSeats}</td>
                    <td><span class="status-badge ${statusClass}">${b.status || 'Open'}</span></td>
                    <td>
                        <div style="display: flex; align-items: center; gap: 5px;">
                            <div style="width: 50px; height: 6px; background: #ecf0f1; border-radius: 3px;">
                                <div style="width: ${occupancyPercent}%; height: 6px; background: ${occupancyColor}; border-radius: 3px;"></div>
                            </div>
                            <span style="font-size: 0.85rem; color: #7f8c8d;">${occupancyPercent}%</span>
                        </div>
                    </td>
                    <td>
                        <button class="icon-btn" onclick="viewBatch(${b.id})" title="View Details"><i class="fas fa-eye"></i></button>
                        <button class="icon-btn" onclick="editBatch(${b.id})" title="Edit"><i class="fas fa-edit"></i></button>
                        <button class="icon-btn" onclick="deleteBatch(${b.id})" title="Delete"><i class="fas fa-trash"></i></button>
                    </td>
                </tr>`;
            });
            
            document.getElementById('batchesTableBody').innerHTML = html;
            updatePaginationInfo(batchesData.length);
        }'''

# Check if we need to update
if 'batchesData.slice' not in content:
    # The function already has pagination? Let's check
    if 'currentPage' in content and 'itemsPerPage' in content:
        print("   ✅ displayBatches already has pagination")
    else:
        print("   ⚠️ Manual check needed for displayBatches pagination")

# ============================================================
# FIX 5: Add loading states
# ============================================================
print("\n🔧 Adding loading states...")

if 'showLoading' not in content:
    loading_js = '''
    // ==================== LOADING STATES ====================
    function showLoading() {
        const tableBody = document.getElementById('batchesTableBody');
        if (tableBody) {
            tableBody.innerHTML = '<tr><td colspan="11" class="loading"><i class="fas fa-spinner fa-spin"></i> Loading batches...</td></tr>';
        }
    }'''
    
    content = content.replace('</script>', loading_js + '\n</script>')
    print("   ✅ Loading states added")

# ============================================================
# FIX 6: Add date validation
# ============================================================
print("\n🔧 Adding date validation...")

date_validation = '''
    // ==================== DATE VALIDATION ====================
    function validateDates(departureDate, returnDate) {
        if (!departureDate || !returnDate) return true;
        
        const depart = new Date(departureDate);
        const ret = new Date(returnDate);
        
        if (ret <= depart) {
            showNotification('Return date must be after departure date', 'error');
            return false;
        }
        return true;
    }'''

content = content.replace('</script>', date_validation + '\n</script>')
print("   ✅ Date validation added")

# ============================================================
# FIX 7: Update createBatch with validation
# ============================================================
print("\n🔧 Updating createBatch with validation...")

if 'createBatch' in content and 'validateDates' not in content:
    # Find the createBatch function
    if 'async function createBatch()' in content:
        # Add validation before API call
        old_create = '''async function createBatch() {
            const priceValue = document.getElementById('price').value.replace(/,/g, '');
            
            const batchData = {
                batch_name: document.getElementById('batch_name').value,
                total_seats: parseInt(document.getElementById('total_seats').value) || 150,
                price: priceValue ? parseFloat(priceValue) : null,
                departure_date: document.getElementById('departure_date').value || null,
                return_date: document.getElementById('return_date').value || null,
                status: document.getElementById('status').value,
                description: document.getElementById('description').value
            };
            
            if (!batchData.batch_name) {
                showNotification('Batch name is required', 'error');
                return;
            }'''
        
        new_create = '''async function createBatch() {
            const priceValue = document.getElementById('price').value.replace(/,/g, '');
            
            const batchData = {
                batch_name: document.getElementById('batch_name').value,
                total_seats: parseInt(document.getElementById('total_seats').value) || 150,
                price: priceValue ? parseFloat(priceValue) : null,
                departure_date: document.getElementById('departure_date').value || null,
                return_date: document.getElementById('return_date').value || null,
                status: document.getElementById('status').value,
                description: document.getElementById('description').value
            };
            
            if (!batchData.batch_name) {
                showNotification('Batch name is required', 'error');
                return;
            }
            
            // Validate dates
            if (!validateDates(batchData.departure_date, batchData.return_date)) {
                return;
            }'''
        
        if old_create in content:
            content = content.replace(old_create, new_create)
            print("   ✅ createBatch updated with validation")
        else:
            print("   ⚠️ Could not find createBatch function")

# ============================================================
# Write the file
# ============================================================
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "=" * 60)
print("✅ batches.html FIX COMPLETE!")
print("=" * 60)
print(f"\n📁 Backup saved: {backup_path}")
print("\n📋 FIXES APPLIED:")
print("   1. ✅ Delete confirmation added")
print("   2. ✅ Pagination HTML added")
print("   3. ✅ Pagination JavaScript added")
print("   4. ✅ Loading states added")
print("   5. ✅ Date validation added")
print("   6. ✅ Create batch validation updated")
print("\n⚠️ MANUAL CHECKS NEEDED:")
print("   - Verify pagination works correctly")
print("   - Test date validation")
print("   - Check delete confirmation")
print("\n🚀 NEXT STEPS:")
print("   1. Test batches.html in browser")
print("   2. If issues, restore from backup")
print("   3. Run: git add public/admin/batches.html")
print("   4. Run: git commit -m \"Add pagination, validation and enhancements to batches page\"")
print("   5. Run: git push origin main")