# fix_receipts_pagination.py
import os
import shutil
from datetime import datetime

print("=" * 60)
print("🚀 FIXING receipts.html - Adding Pagination & Enhancements")
print("=" * 60)

# Create backup
backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(backup_dir, exist_ok=True)
print(f"📁 Created backup folder: {backup_dir}/")

html_path = "public/admin/receipts.html"
backup_path = f"{backup_dir}/receipts.html.bak"

# Create backup
shutil.copy2(html_path, backup_path)
print(f"✅ Backup created: {backup_path}")

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# ====== FIX 1: Add WhatsApp Share Button ======
print("\n🔧 Adding WhatsApp share button...")

if 'WhatsApp' not in content:
    whatsapp_button = '''
                            <button class="icon-btn" onclick="shareReceiptWhatsApp(${receipt.id}, '${receipt.traveler_name}', '${receipt.mobile}')" title="Share on WhatsApp">
                                <i class="fab fa-whatsapp"></i>
                            </button>'''
    
    # Add to actions column
    if 'fa-print' in content:
        content = content.replace(
            'fa-print" onclick="printReceipt',
            'fa-whatsapp" onclick="shareReceiptWhatsApp' + whatsapp_button + '\n                            <button class="icon-btn" onclick="printReceipt" title="Print"><i class="fas fa-print'
        )
        print("   ✅ WhatsApp button added")
    else:
        print("   ⚠️ Could not find insertion point")

# ====== FIX 2: Add Void/Cancel Button ======
print("\n🔧 Adding void/cancel button...")

void_button = '''
                            <button class="icon-btn" onclick="voidReceipt(${receipt.id}, '${receipt.receipt_number}')" title="Void Receipt">
                                <i class="fas fa-ban"></i>
                            </button>'''
    
content = content.replace(
    'fa-trash" onclick="deleteReceipt',
    'fa-ban" onclick="voidReceipt' + void_button + '\n                            <button class="icon-btn" onclick="deleteReceipt" title="Delete"><i class="fas fa-trash'
)
print("   ✅ Void button added")

# ====== FIX 3: Add Pagination HTML ======
if 'pagination' not in content.lower() and 'showingFrom' not in content:
    print("\n🔧 Adding pagination HTML...")
    
    pagination_html = '''
        <!-- Pagination -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px;">
            <div id="paginationInfo">
                Showing <span id="showingFrom">1</span> to <span id="showingTo">10</span> of <span id="totalCount">0</span> receipts
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
    if '</div>\n\n    <!-- Create Receipt Modal -->' in content:
        content = content.replace('</div>\n\n    <!-- Create Receipt Modal -->', pagination_html + '\n    </div>\n\n    <!-- Create Receipt Modal -->')
        print("   ✅ Pagination HTML added")
    else:
        print("   ⚠️ Could not find insertion point")

# Write modified content
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ receipts.html has been fixed!")
print("=" * 60)
