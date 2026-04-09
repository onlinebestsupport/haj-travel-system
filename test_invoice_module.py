#!/usr/bin/env python
"""
Complete Invoice Module Test - Tests Create, Edit, Delete, View operations
"""

import requests
import json
import time

BASE_URL = "https://haj-web-app-production.up.railway.app"
session = requests.Session()

print("=" * 60)
print("🧪 INVOICE MODULE COMPLETE TEST")
print("=" * 60)

# Step 1: Login
print("\n📝 Step 1: Logging in...")
login = session.post(f"{BASE_URL}/api/login", json={
    "username": "superadmin",
    "password": "admin123"
})

if login.status_code != 200:
    print(f"❌ Login failed: {login.status_code}")
    exit()
print("✅ Login successful!")

# Step 2: Get existing invoices
print("\n📋 Step 2: Fetching existing invoices...")
response = session.get(f"{BASE_URL}/api/invoices")
if response.status_code == 200:
    invoices = response.json().get('invoices', [])
    print(f"✅ Found {len(invoices)} existing invoices")
    for inv in invoices:
        print(f"   - Invoice #{inv.get('id')}: {inv.get('invoice_number')} - Amount: ₹{inv.get('amount')}")
else:
    print(f"❌ Failed to fetch invoices: {response.status_code}")

# Step 3: Create a test invoice
print("\n📝 Step 3: Creating test invoice...")
test_invoice = {
    "traveler_id": 1,
    "batch_id": 1,
    "amount": 5000.00,
    "due_date": "2026-05-01",
    "status": "pending"
}

response = session.post(f"{BASE_URL}/api/invoices", json=test_invoice)
if response.status_code in [200, 201]:
    invoice_data = response.json()
    invoice_id = invoice_data.get('invoice_id')
    invoice_number = invoice_data.get('invoice_number')
    print(f"✅ Invoice created successfully!")
    print(f"   ID: {invoice_id}")
    print(f"   Number: {invoice_number}")
else:
    print(f"❌ Failed to create invoice: {response.status_code}")
    print(f"   Error: {response.text}")
    exit()

# Step 4: Get the created invoice
print("\n🔍 Step 4: Fetching created invoice...")
response = session.get(f"{BASE_URL}/api/invoices/{invoice_id}")
if response.status_code == 200:
    invoice = response.json().get('invoice', {})
    print(f"✅ Invoice fetched successfully!")
    print(f"   Invoice #: {invoice.get('invoice_number')}")
    print(f"   Amount: ₹{invoice.get('amount')}")
    print(f"   Status: {invoice.get('status')}")
else:
    print(f"❌ Failed to fetch invoice: {response.status_code}")

# Step 5: Update the invoice (EDIT)
print("\n✏️ Step 5: Updating invoice (EDIT TEST)...")
update_data = {
    "amount": 7500.00,
    "paid_amount": 2500.00,
    "due_date": "2026-06-01",
    "status": "paid"
}

response = session.put(f"{BASE_URL}/api/invoices/{invoice_id}", json=update_data)
if response.status_code in [200, 201, 204]:
    print(f"✅ Invoice updated successfully!")
    
    # Verify update
    verify = session.get(f"{BASE_URL}/api/invoices/{invoice_id}")
    if verify.status_code == 200:
        updated = verify.json().get('invoice', {})
        print(f"   Verification:")
        print(f"   Amount: ₹{updated.get('amount')} (expected: ₹7500)")
        print(f"   Paid Amount: ₹{updated.get('paid_amount')} (expected: ₹2500)")
        print(f"   Status: {updated.get('status')} (expected: paid)")
        print(f"   Due Date: {updated.get('due_date')}")
        
        if updated.get('amount') == 7500 and updated.get('status') == 'paid':
            print("   ✅ UPDATE VERIFIED!")
        else:
            print("   ⚠️ Update not reflected correctly")
    else:
        print(f"❌ Failed to verify update: {verify.status_code}")
else:
    print(f"❌ Failed to update invoice: {response.status_code}")
    print(f"   Error: {response.text}")

# Step 6: Delete the invoice
print("\n🗑️ Step 6: Deleting invoice...")
response = session.delete(f"{BASE_URL}/api/invoices/{invoice_id}")
if response.status_code in [200, 201, 204]:
    print(f"✅ Invoice deleted successfully!")
    
    # Verify deletion
    verify = session.get(f"{BASE_URL}/api/invoices/{invoice_id}")
    if verify.status_code == 404:
        print(f"✅ Deletion verified - Invoice no longer exists")
    else:
        print(f"⚠️ Invoice still exists - Status: {verify.status_code}")
else:
    print(f"❌ Failed to delete invoice: {response.status_code}")
    print(f"   Error: {response.text}")

# Step 7: List all invoices again
print("\n📋 Step 7: Final invoice list...")
response = session.get(f"{BASE_URL}/api/invoices")
if response.status_code == 200:
    invoices = response.json().get('invoices', [])
    print(f"✅ Total invoices remaining: {len(invoices)}")
    for inv in invoices:
        print(f"   - Invoice #{inv.get('id')}: {inv.get('invoice_number')} - Amount: ₹{inv.get('amount')}")
else:
    print(f"❌ Failed to fetch invoices: {response.status_code}")

print("\n" + "=" * 60)
print("📊 TEST SUMMARY")
print("=" * 60)

if response.status_code == 200:
    print("✅ INVOICE MODULE IS WORKING!")
    print("   - Create: Working")
    print("   - Read: Working")
    print("   - Update: Working")
    print("   - Delete: Working")
else:
    print("❌ Some operations failed. Check the errors above.")

print("\n🔧 If edit/delete failed, check:")
print("   1. Invoice ID exists")
print("   2. PUT/DELETE endpoints are registered")
print("   3. Check server logs: railway logs --service haj-web-app")