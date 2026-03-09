# test_admin_css.py
import os

print("="*60)
print("🔍 ADMIN CSS COMPLETE TEST")
print("="*60)

css_path = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system\public\admin\admin-style.css"

if not os.path.exists(css_path):
    print(f"❌ ERROR: admin-style.css not found at {css_path}")
    exit(1)

print(f"📁 Testing: {css_path}")
file_size = os.path.getsize(css_path)
print(f"📏 File size: {file_size:,} bytes")

with open(css_path, 'r', encoding='utf-8') as f:
    css_content = f.read()

# ====== TEST CATEGORIES ======
tests = {
    "RESET & BASE STYLES": [
        "* {", 
        "body {", 
        ":root {",
        "--primary-color",
        "--secondary-color"
    ],
    "LAYOUT & CONTAINER": [
        ".container {",
        ".container-fluid",
        ".row {",
        ".col {"
    ],
    "GRID SYSTEMS": [
        ".grid-2 {",
        ".grid-3 {",
        ".grid-4 {",
        ".grid-auto {"
    ],
    "SIDEBAR STYLES": [
        ".sidebar {",
        ".sidebar-header",
        ".user-info",
        ".user-avatar",
        ".nav-menu",
        ".nav-item",
        ".nav-item.active",
        ".nav-section-title"
    ],
    "HEADER STYLES": [
        ".admin-header {",
        ".header-content",
        ".logo-area",
        ".role-badge",
        ".logout-btn"
    ],
    "TOP HEADER": [
        ".top-header {",
        ".header-left",
        ".header-right",
        ".notification-badge",
        ".date-time"
    ],
    "BUTTON STYLES": [
        ".action-btn {",
        ".btn-primary",
        ".btn-success",
        ".btn-warning",
        ".btn-danger",
        ".btn-info",
        ".btn-secondary",
        ".btn-purple",
        ".btn-whatsapp",
        ".btn-outline-primary",
        ".btn-sm",
        ".btn-lg"
    ],
    "QUICK ACTIONS": [
        ".quick-actions {",
        ".quick-action-btn"
    ],
    "TABS": [
        ".tabs-container",
        ".tabs",
        ".tab-btn",
        ".tab-btn.active"
    ],
    "STATS CARDS": [
        ".stats-grid",
        ".stat-card {",
        ".stat-number",
        ".stat-trend",
        ".trend-up",
        ".trend-down"
    ],
    "MODULE GRID": [
        ".module-grid",
        ".module-card",
        ".module-stats"
    ],
    "FORMS": [
        ".form-container",
        ".form-grid",
        ".form-group",
        ".form-actions",
        "input:focus",
        "select:focus"
    ],
    "TABLES": [
        ".table-container",
        "th {",
        "td {",
        "tr:hover"
    ],
    "STATUS BADGES": [
        ".status-badge",
        ".status-active",
        ".status-pending",
        ".status-inactive",
        ".status-warning"
    ],
    "ROLE BADGES": [
        ".role-badge",
        ".role-super_admin",
        ".role-admin",
        ".role-manager",
        ".role-staff",
        ".role-viewer"
    ],
    "ICON BUTTONS": [
        ".icon-btn",
        ".icon-btn:hover"
    ],
    "MODALS (CRITICAL)": [
        ".modal {",
        ".modal-overlay",
        ".modal-header",
        ".modal-body",
        ".modal-footer",
        ".modal-close",
        "transform: translate(-50%, -50%)",
        "animation: modalFadeIn"
    ],
    "DETAIL GRID": [
        ".detail-grid",
        ".detail-item"
    ],
    "DOCUMENT STYLES": [
        ".document-grid",
        ".document-card",
        ".document-upload",
        ".document-preview"
    ],
    "COMPANY DETAILS": [
        ".company-details",
        ".tax-info-grid",
        ".bank-details"
    ],
    "TOGGLE SWITCH": [
        ".toggle-switch",
        ".toggle-slider"
    ],
    "CALCULATION BOX": [
        ".calculation-box",
        ".calculation-row",
        ".amount-display"
    ],
    "INVOICE/RECEIPT TEMPLATES": [
        ".invoice-print-template",
        ".receipt-print-template",
        ".invoice-header",
        ".invoice-meta",
        ".invoice-items",
        ".invoice-summary",
        ".amount-in-words"
    ],
    "BACKUP STYLES": [
        ".backup-stats",
        ".backup-list",
        ".backup-item",
        ".backup-icon"
    ],
    "PAGINATION": [
        ".pagination",
        ".page-link"
    ],
    "NOTIFICATION": [
        ".notification {",
        ".notification-success",
        ".notification-error",
        "@keyframes slideIn"
    ],
    "SESSION WARNING": [
        "#sessionWarning",
        "@keyframes slideDown"
    ],
    "LOADING SPINNER": [
        ".loading",
        "@keyframes spin"
    ],
    "UTILITIES": [
        ".text-center",
        ".text-muted",
        ".d-flex",
        ".flex-wrap",
        ".justify-between",
        ".gap-1",
        ".w-100",
        ".mt-1",
        ".mb-1",
        ".p-1"
    ],
    "RESPONSIVE DESIGN": [
        "@media (max-width: 1200px)",
        "@media (max-width: 992px)",
        "@media (max-width: 768px)",
        "@media (max-width: 576px)"
    ],
    "PRINT STYLES": [
        "@media print"
    ],
    "ANIMATIONS": [
        "@keyframes fadeInUp",
        "@keyframes slideInLeft",
        "@keyframes slideInRight",
        ".fadeInUp"
    ],
    "SKELETON LOADING": [
        ".skeleton",
        "@keyframes loading"
    ]
}

# Run tests
print("\n" + "="*60)
print("📊 TESTING CSS SECTIONS")
print("="*60)

passed = 0
failed = 0
missing_sections = []

for category, selectors in tests.items():
    print(f"\n🔍 {category}:")
    category_passed = True
    
    for selector in selectors:
        if selector in css_content:
            print(f"  ✅ {selector:30} ✓ Found")
        else:
            print(f"  ❌ {selector:30} ✗ MISSING")
            category_passed = False
            missing_sections.append(f"{category} - {selector}")
    
    if category_passed:
        passed += 1
    else:
        failed += 1

# ====== SPECIAL CHECKS ======
print("\n" + "="*60)
print("🔍 SPECIAL CHECKS")
print("="*60)

# Check for duplicate modal definitions
modal_count = css_content.count('.modal {')
if modal_count == 1:
    print(f"✅ Modal defined exactly once: {modal_count}")
else:
    print(f"⚠️  Modal defined {modal_count} times - should be exactly 1")

# Check for critical modal positioning
if 'transform: translate(-50%, -50%)' in css_content:
    print("✅ Modal has correct centering: transform: translate(-50%, -50%)")
else:
    print("❌ Modal missing critical centering property")

# Check for both CSS files (public vs admin)
if '--primary-color' in css_content and '--secondary-color' in css_content:
    print("✅ CSS variables defined")
else:
    print("⚠️  CSS variables missing")

# Check for Font Awesome integration
if 'fa-' in css_content:
    print("✅ Font Awesome icons supported")
else:
    print("⚠️  No Font Awesome icon styles found")

# ====== SUMMARY ======
print("\n" + "="*60)
print("📊 FINAL SUMMARY")
print("="*60)
print(f"✅ Categories fully passed: {passed}/{len(tests)}")
print(f"❌ Categories with missing items: {failed}/{len(tests)}")

if missing_sections:
    print("\n🔧 MISSING ITEMS TO FIX:")
    for item in missing_sections[:10]:  # Show first 10
        print(f"  • {item}")
    if len(missing_sections) > 10:
        print(f"  ... and {len(missing_sections) - 10} more")

# File size recommendation
print("\n📏 FILE SIZE ANALYSIS:")
if file_size > 70000:
    print(f"✅ Good size: {file_size:,} bytes (comprehensive)")
elif file_size > 50000:
    print(f"⚠️  Medium size: {file_size:,} bytes")
else:
    print(f"⚠️  Small size: {file_size:,} bytes - might be missing styles")

print("\n" + "="*60)
if failed == 0:
    print("✅ YOUR ADMIN CSS IS COMPLETE AND PERFECT!")
else:
    print("⚠️  Some CSS sections need attention. Check missing items above.")
print("="*60)
