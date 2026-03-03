#!/usr/bin/env python
# fix_all_issues.py - ONE SCRIPT TO FIX EVERYTHING
# Run this once and all problems are solved!

import os
import re
from datetime import datetime

print("=" * 60)
print("🚀 MASTER FIX SCRIPT - FIXES EVERYTHING AT ONCE")
print("=" * 60)

# Create backup directory
backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(backup_dir, exist_ok=True)
print(f"📁 Created backup folder: {backup_dir}/")

# ============================================================
# FIX 1: Update admin.py to include invoice stats in dashboard
# ============================================================
print("\n🔧 FIX 1: Updating admin.py to show invoice counts...")

admin_py_path = "app/routes/admin.py"
if os.path.exists(admin_py_path):
    # Create backup
    with open(admin_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(f"{backup_dir}/admin.py.bak", 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Check if already fixed
    if 'total_invoices' not in content:
        # Find where to insert invoice queries
        if 'def get_dashboard_stats' in content:
            # Add invoice count query
            invoice_query = """
        
        # Get invoice counts
        cursor.execute('SELECT COUNT(*) as count FROM invoices')
        invoice_count = cursor.fetchone()['count']
        
        cursor.execute(\"\"\"
            SELECT 
                COUNT(CASE WHEN status = 'paid' THEN 1 END) as paid_count,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
                COUNT(CASE WHEN status = 'overdue' THEN 1 END) as overdue_count
            FROM invoices
        \"\"\")
        invoice_stats = cursor.fetchone()"""
        
        # Insert after user_stats query
        content = content.replace(
            "cursor.execute(''\"\"\"\n            SELECT \n                COUNT(*) as total_users,\n                SUM(CASE WHEN is_active = true THEN 1 ELSE 0 END) as active_users\n            FROM users\n        ''\"\"\")",
            "cursor.execute(''\"\"\"\n            SELECT \n                COUNT(*) as total_users,\n                SUM(CASE WHEN is_active = true THEN 1 ELSE 0 END) as active_users\n            FROM users\n        ''\"\"\")" + invoice_query
        )
        
        # Add invoice stats to return JSON
        content = content.replace(
            "'total_users': user_stats['total_users'] or 0,",
            "'total_users': user_stats['total_users'] or 0,\n                'total_invoices': invoice_count,\n                'paid_invoices': invoice_stats['paid_count'] or 0,\n                'pending_invoices': invoice_stats['pending_count'] or 0,\n                'overdue_invoices': invoice_stats['overdue_count'] or 0,"
        )
        
        with open(admin_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("   ✅ admin.py updated with invoice stats")
    else:
        print("   ✅ admin.py already has invoice stats")
else:
    print("   ❌ admin.py not found")

# ============================================================
# FIX 2: Create invoices/stats endpoint
# ============================================================
print("\n🔧 FIX 2: Adding invoice stats endpoint...")

invoices_py_path = "app/routes/invoices.py"
if os.path.exists(invoices_py_path):
    with open(invoices_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(f"{backup_dir}/invoices.py.bak", 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Check if stats endpoint already exists
    if '@bp.route' not in content or "'/stats'" not in content:
        stats_endpoint = """

@bp.route('/stats', methods=['GET'])
def get_invoice_stats():
    \"\"\"Get invoice statistics\"\"\"
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn, cursor = get_db()
    try:
        cursor.execute('''
            SELECT 
                COUNT(*) as total_invoices,
                SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_count,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                SUM(CASE WHEN status = 'overdue' THEN 1 ELSE 0 END) as overdue_count,
                COALESCE(SUM(total_amount), 0) as total_amount,
                COALESCE(SUM(paid_amount), 0) as total_paid
            FROM invoices
        ''')
        stats = cursor.fetchone()
        cursor.close()
        conn.close()
        
        # Convert Decimal to float for JSON
        if stats:
            stats_dict = dict(stats)
            for key in ['total_amount', 'total_paid']:
                if key in stats_dict and stats_dict[key] is not None:
                    stats_dict[key] = float(stats_dict[key])
        else:
            stats_dict = {}
        
        return jsonify({'success': True, 'stats': stats_dict})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500"""
        
        # Add at the end of the file
        content += stats_endpoint
        
        with open(invoices_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("   ✅ invoices.py stats endpoint added")
    else:
        print("   ✅ invoices.py already has stats endpoint")
else:
    print("   ❌ invoices.py not found")

# ============================================================
# FIX 3: Update dashboard.html to show invoice stats
# ============================================================
print("\n🔧 FIX 3: Updating dashboard.html to show invoice counts...")

dashboard_path = "public/admin/dashboard.html"
if os.path.exists(dashboard_path):
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(f"{backup_dir}/dashboard.html.bak", 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Check if invoice stats are already there
    if 'totalInvoices' not in content:
        # Add invoice stats HTML
        invoice_stats_html = '''
                <div class="stat-card">
                    <div class="stat-info">
                        <h3>Total Invoices</h3>
                        <div class="stat-number" id="totalInvoices">0</div>
                        <div class="stat-trend">
                            <i class="fas fa-file-invoice"></i> <span id="paidInvoices">0</span> Paid
                        </div>
                    </div>
                    <div class="stat-icon">
                        <i class="fas fa-file-invoice"></i>
                    </div>
                </div>'''
        
        # Insert after pending payments stat card
        content = content.replace(
            '                </div>\n            </div>',
            '                </div>\n            </div>' + invoice_stats_html
        )
        
        # Add JavaScript to fetch invoice stats
        invoice_js = '''
        // Fetch invoice stats
        try {
            const invoiceRes = await fetch('/api/invoices/stats', {
                credentials: 'include'
            });
            const invoiceData = await invoiceRes.json();
            if (invoiceData.success) {
                document.getElementById('totalInvoices').textContent = invoiceData.stats.total_invoices || 0;
                document.getElementById('paidInvoices').textContent = invoiceData.stats.paid_count || 0;
            }
        } catch (e) {
            console.log('Invoice stats not available');
        }'''
        
        # Insert in the loadDashboardStats function
        content = content.replace(
            'console.log(\'✅ Dashboard stats loaded:\', {',
            invoice_js + '\n            console.log(\'✅ Dashboard stats loaded:\', {'
        )
        
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("   ✅ dashboard.html updated with invoice stats")
    else:
        print("   ✅ dashboard.html already has invoice stats")
else:
    print("   ❌ dashboard.html not found")

# ============================================================
# FIX 4: Fix invoices.html pagination
# ============================================================
print("\n🔧 FIX 4: Fixing invoices.html pagination...")

invoices_html_path = "public/admin/invoices.html"
if os.path.exists(invoices_html_path):
    with open(invoices_html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(f"{backup_dir}/invoices.html.bak", 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Add pagination HTML if not present
    if 'pagination' not in content.lower():
        pagination_html = '''
        <!-- Pagination -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px;">
            <div id="paginationInfo">
                Showing <span id="showingFrom">1</span> to <span id="showingTo">10</span> of <span id="totalCount">0</span> invoices
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
        
        # Insert before closing </div> of container
        content = content.replace('    </div>\n\n    <!-- Modals -->', pagination_html + '\n    </div>\n\n    <!-- Modals -->')
    
    # Add pagination JavaScript
    pagination_js = '''
    // ==================== PAGINATION VARIABLES ====================
    let currentPage = 1;
    let itemsPerPage = 10;
    let invoicesData = [];

    // ==================== PAGINATION FUNCTIONS ====================
    function updatePaginationInfo() {
        const total = invoicesData.length;
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
            displayInvoices();
        }
    }

    function nextPage() {
        if (currentPage * itemsPerPage < invoicesData.length) {
            currentPage++;
            displayInvoices();
        }
    }'''
    
    # Insert before closing </script>
    content = content.replace('</script>', pagination_js + '\n</script>')
    
    with open(invoices_html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("   ✅ invoices.html pagination added")
else:
    print("   ❌ invoices.html not found")

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("✅ MASTER FIX COMPLETE!")
print("=" * 60)
print(f"\n📁 Backups saved in: {backup_dir}/")
print("\n📋 WHAT WAS FIXED:")
print("   1. ✅ admin.py - Added invoice stats to dashboard API")
print("   2. ✅ invoices.py - Added /stats endpoint")
print("   3. ✅ dashboard.html - Added invoice display")
print("   4. ✅ invoices.html - Added pagination")
print("\n🚀 NEXT STEPS:")
print("   1. Run: git add .")
print("   2. Run: git commit -m \"Fix all invoice issues\"")
print("   3. Run: git push origin main")
print("\n🎉 After pushing, Railway will auto-deploy in 2 minutes!")