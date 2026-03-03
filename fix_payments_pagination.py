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

# ============================================================
# FIX 1: Add Receipt Generation Button
# ============================================================
print("\n🔧 Adding receipt generation button...")

if 'Generate Receipt' not in content:
    receipt_button = '''
                            <button class="icon-btn" onclick="generateReceipt(${payment.id})" title="Generate Receipt">
                                <i class="fas fa-receipt"></i>
                            </button>'''
    
    # Add to actions column
    if 'fa-print' in content or 'print' in content.lower():
        # Insert before print button or at end of actions
        content = content.replace(
            'fa-print" onclick="printPayment',
            'fa-receipt" onclick="generateReceipt' + receipt_button + 'fa-print" onclick="printPayment'
        )
        print("   ✅ Receipt button added")
    else:
        print("   ⚠️ Could not find insertion point")

# ============================================================
# FIX 2: Add Pagination HTML
# ============================================================
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
    if '    </div>\n\n    <!-- Payment Summary Modal -->' in content:
        content = content.replace('    </div>\n\n    <!-- Payment Summary Modal -->', pagination_html + '\n    </div>\n\n    <!-- Payment Summary Modal -->')
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
    let allPayments = [];

    function updatePaginationInfo() {
        const total = allPayments.length;
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
            loadPayments();
        }
    }

    function nextPage() {
        if (currentPage * itemsPerPage < allPayments.length) {
            currentPage++;
            loadPayments();
        }
    }'''
    
    content = content.replace('</script>', pagination_js + '\n</script>')
    print("   ✅ Pagination JavaScript added")

# ============================================================
# FIX 4: Add Receipt Generation Function
# ============================================================
print("\n🔧 Adding receipt generation function...")

receipt_function = '''

    // ==================== RECEIPT GENERATION ====================
    async function generateReceipt(paymentId) {
        try {
            showNotification('Generating receipt...', 'info');
            
            const response = await fetch(`/api/payments/${paymentId}/receipt`, {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.success && data.receipt) {
                // Open receipt in new window
                const receiptWindow = window.open('', '_blank');
                receiptWindow.document.write(`
                    <html>
                    <head>
                        <title>Payment Receipt</title>
                        <style>
                            body { font-family: Arial; padding: 40px; }
                            .receipt { max-width: 800px; margin: 0 auto; border: 1px solid #ddd; padding: 30px; }
                            .header { text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 20px; margin-bottom: 20px; }
                            .details { margin: 20px 0; }
                            .row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
                            .total { font-size: 1.2rem; font-weight: bold; color: #27ae60; margin-top: 20px; }
                            .footer { text-align: center; margin-top: 40px; color: #7f8c8d; }
                        </style>
                    </head>
                    <body>
                        <div class="receipt">
                            <div class="header">
                                <h1>Alhudha Haj Travel</h1>
                                <h3>Payment Receipt</h3>
                                <p>Receipt #: ${data.receipt.receipt_number}</p>
                                <p>Date: ${new Date(data.receipt.receipt_date).toLocaleDateString()}</p>
                            </div>
                            <div class="details">
                                <div class="row"><strong>Traveler:</strong> <span>${data.receipt.first_name} ${data.receipt.last_name}</span></div>
                                <div class="row"><strong>Passport:</strong> <span>${data.receipt.passport_no}</span></div>
                                <div class="row"><strong>Batch:</strong> <span>${data.receipt.batch_name}</span></div>
                                <div class="row"><strong>Amount:</strong> <span>₹${data.receipt.amount.toLocaleString()}</span></div>
                                <div class="row"><strong>Payment Method:</strong> <span>${data.receipt.payment_method}</span></div>
                                <div class="row"><strong>Transaction ID:</strong> <span>${data.receipt.transaction_id || 'N/A'}</span></div>
                                <div class="row total"><strong>Total Paid:</strong> <span>₹${data.receipt.amount.toLocaleString()}</span></div>
                            </div>
                            <div class="footer">
                                <p>Thank you for your payment. May Allah accept your journey.</p>
                                <p>This is a computer generated receipt - no signature required.</p>
                            </div>
                        </div>
                    </body>
                    </html>
                `);
                receiptWindow.document.close();
                receiptWindow.print();
            } else {
                showNotification('Receipt not found', 'error');
            }
        } catch (error) {
            console.error('Error generating receipt:', error);
            showNotification('Error generating receipt', 'error');
        }
    }'''
    
content = content.replace('</script>', receipt_function + '\n</script>')
print("   ✅ Receipt generation function added")

# ============================================================
# FIX 5: Add Refund Function
# ============================================================
print("\n🔧 Adding refund functionality...")

refund_function = '''

    // ==================== REFUND/REVERSE PAYMENT ====================
    async function reversePayment(paymentId) {
        if (!confirm('⚠️ Are you sure you want to reverse/refund this payment? This action cannot be undone.')) {
            return;
        }
        
        const reason = prompt('Please enter reason for refund/reversal:');
        if (!reason) return;
        
        try {
            showNotification('Processing refund...', 'info');
            
            const response = await fetch(`/api/payments/${paymentId}/reverse`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ reason: reason })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showNotification('Payment reversed successfully!', 'success');
                loadPayments();
            } else {
                showNotification('Error: ' + (data.error || 'Could not reverse payment'), 'error');
            }
        } catch (error) {
            console.error('Error reversing payment:', error);
            showNotification('Error processing refund', 'error');
        }
    }'''
    
content = content.replace('</script>', refund_function + '\n</script>')
print("   ✅ Refund function added")

# ============================================================
# FIX 6: Add Refund Button to Actions
# ============================================================
print("\n🔧 Adding refund button to actions...")

if 'reversePayment' in content and 'fa-undo' not in content:
    refund_button = '''
                            <button class="icon-btn" onclick="reversePayment(${payment.id})" title="Reverse/Refund Payment">
                                <i class="fas fa-undo"></i>
                            </button>'''
    
    # Add before delete button
    content = content.replace(
        'fa-trash" onclick="deletePayment',
        'fa-undo" onclick="reversePayment' + refund_button + 'fa-trash" onclick="deletePayment'
    )
    print("   ✅ Refund button added")

# ============================================================
# FIX 7: Add Payment Reminder Function
# ============================================================
print("\n🔧 Adding payment reminder function...")

reminder_function = '''

    // ==================== SEND PAYMENT REMINDER ====================
    async function sendPaymentReminder(paymentId, travelerId, travelerName) {
        if (!confirm(`Send payment reminder to ${travelerName}?`)) {
            return;
        }
        
        try {
            showNotification('Sending reminder...', 'info');
            
            // Get traveler contact info
            const travelerRes = await fetch(`/api/travelers/${travelerId}`, {
                credentials: 'include'
            });
            const travelerData = await travelerRes.json();
            const traveler = travelerData.traveler;
            
            // Get payment details
            const paymentRes = await fetch(`/api/payments/${paymentId}`, {
                credentials: 'include'
            });
            const paymentData = await paymentRes.json();
            const payment = paymentData.payment;
            
            // Create reminder message
            const message = `Dear ${traveler.first_name},\\n\\nThis is a reminder that your payment of ₹${payment.amount} is due on ${new Date(payment.due_date).toLocaleDateString()}.\\n\\nPlease make the payment at your earliest convenience.\\n\\nJazakAllah Khair,\\nAlhudha Haj Travel Team`;
            
            // Open in WhatsApp if mobile number exists
            if (traveler.mobile) {
                const whatsappUrl = `https://wa.me/${traveler.mobile.replace(/\\D/g, '')}?text=${encodeURIComponent(message)}`;
                window.open(whatsappUrl, '_blank');
                showNotification('Reminder opened in WhatsApp', 'success');
            } else {
                // Fallback to email
                const mailtoUrl = `mailto:${traveler.email}?subject=Payment Reminder&body=${encodeURIComponent(message)}`;
                window.open(mailtoUrl, '_blank');
                showNotification('Reminder opened in email', 'success');
            }
        } catch (error) {
            console.error('Error sending reminder:', error);
            showNotification('Error sending reminder', 'error');
        }
    }'''
    
content = content.replace('</script>', reminder_function + '\n</script>')
print("   ✅ Payment reminder function added")

# ============================================================
# FIX 8: Add Reminder Button
# ============================================================
print("\n🔧 Adding reminder button...")

reminder_button = '''
                            <button class="icon-btn" onclick="sendPaymentReminder(${payment.id}, ${payment.traveler_id}, '${payment.first_name} ${payment.last_name}')" title="Send Reminder">
                                <i class="fas fa-bell"></i>
                            </button>'''
    
# Add after view button
content = content.replace(
    'fa-eye" onclick="viewPayment',
    'fa-eye" onclick="viewPayment' + reminder_button
)
print("   ✅ Reminder button added")

# ============================================================
# Write the file
# ============================================================
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "=" * 60)
print("✅ payments.html FIX COMPLETE!")
print("=" * 60)
print(f"\n📁 Backup saved: {backup_path}")
print("\n📋 FIXES APPLIED:")
print("   1. ✅ Receipt generation button added")
print("   2. ✅ Pagination HTML added")
print("   3. ✅ Pagination JavaScript added")
print("   4. ✅ Receipt generation function added")
print("   5. ✅ Refund function added")
print("   6. ✅ Refund button added")
print("   7. ✅ Payment reminder function added")
print("   8. ✅ Reminder button added")
print("\n⚠️ MANUAL CHECKS NEEDED:")
print("   - Verify receipt generation works")
print("   - Test refund functionality")
print("   - Check pagination")
print("   - Test payment reminders")
print("\n🚀 NEXT STEPS:")
print("   1. Test payments.html in browser")
print("   2. If issues, restore from backup")
print("   3. Run: git add public/admin/payments.html")
print("   4. Run: git commit -m \"Add pagination, receipts, refunds and reminders to payments page\"")
print("   5. Run: git push origin main")