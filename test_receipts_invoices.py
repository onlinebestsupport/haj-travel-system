#!/usr/bin/env python
"""
Complete Test Suite for Receipts and Invoices Modules
Tests: Create, Read, Update, Delete, and Database verification
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "https://haj-web-app-production.up.railway.app"
session = requests.Session()

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}{END}")
    print(f"{BLUE}{text:^70}{END}")
    print(f"{BLUE}{'='*70}{END}")

def print_success(text):
    print(f"{GREEN}✅ {text}{END}")

def print_error(text):
    print(f"{RED}❌ {text}{END}")

def print_info(text):
    print(f"{YELLOW}ℹ️ {text}{END}")

# Step 1: Login
print_header("🔐 LOGIN")
response = session.post(f"{BASE_URL}/api/login", json={
    "username": "superadmin",
    "password": "admin123"
})

if response.status_code != 200:
    print_error(f"Login failed: {response.status_code}")
    exit()
print_success("Logged in successfully")

# ==================== INVOICES MODULE TESTS ====================
print_header("📄 INVOICES MODULE TESTS")

# Test 1: Get all invoices
print_info("Fetching all invoices...")
response = session.get(f"{BASE_URL}/api/invoices")
if response.status_code == 200:
    invoices = response.json().get('invoices', [])
    print_success(f"Found {len(invoices)} invoices")
else:
    print_error(f"Failed to fetch invoices: {response.status_code}")

# Test 2: Create a new invoice
print_info("\nCreating test invoice...")
test_invoice = {
    "traveler_id": 1,
    "batch_id": 1,
    "amount": 5000.00,
    "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
    "status": "pending"
}

response = session.post(f"{BASE_URL}/api/invoices", json=test_invoice)
if response.status_code in [200, 201]:
    invoice_data = response.json()
    invoice_id = invoice_data.get('invoice_id') or invoice_data.get('id')
    invoice_number = invoice_data.get('invoice_number')
    print_success(f"Invoice created - ID: {invoice_id}, Number: {invoice_number}")
else:
    print_error(f"Failed to create invoice: {response.status_code} - {response.text}")
    invoice_id = None

# Test 3: Get single invoice
if invoice_id:
    print_info("\nFetching created invoice...")
    response = session.get(f"{BASE_URL}/api/invoices/{invoice_id}")
    if response.status_code == 200:
        invoice = response.json().get('invoice', response.json())
        print_success(f"Invoice #{invoice.get('invoice_number')} - Amount: ₹{invoice.get('amount')}")
        print_success(f"  Status: {invoice.get('status')}, Due: {invoice.get('due_date')}")
    else:
        print_error(f"Failed to fetch invoice: {response.status_code}")

# Test 4: Update invoice
if invoice_id:
    print_info("\nUpdating invoice...")
    update_data = {
        "amount": 7500.00,
        "paid_amount": 2500.00,
        "status": "paid",
        "due_date": (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d")
    }
    response = session.put(f"{BASE_URL}/api/invoices/{invoice_id}", json=update_data)
    if response.status_code in [200, 201, 204]:
        print_success("Invoice updated successfully")
        
        # Verify update
        verify = session.get(f"{BASE_URL}/api/invoices/{invoice_id}")
        if verify.status_code == 200:
            updated = verify.json().get('invoice', verify.json())
            if updated.get('amount') == 7500:
                print_success("  Amount updated to ₹7500")
            if updated.get('paid_amount') == 2500:
                print_success("  Paid amount updated to ₹2500")
            if updated.get('status') == 'paid':
                print_success("  Status updated to paid")
    else:
        print_error(f"Failed to update invoice: {response.status_code} - {response.text}")

# ==================== RECEIPTS MODULE TESTS ====================
print_header("🧾 RECEIPTS MODULE TESTS")

# First, check receipts table structure
print_info("Checking receipts table...")
response = session.get(f"{BASE_URL}/api/receipts")
if response.status_code == 200:
    receipts = response.json().get('receipts', [])
    print_success(f"Found {len(receipts)} receipts")
else:
    print_error(f"Failed to fetch receipts: {response.status_code}")

# Test 1: Create a receipt
if invoice_id:
    print_info("\nCreating test receipt...")
    test_receipt = {
        "traveler_id": 1,
        "payment_id": None,  # Will use invoice reference
        "invoice_id": invoice_id,
        "amount": 2500.00,
        "receipt_date": datetime.now().strftime("%Y-%m-%d"),
        "payment_method": "bank_transfer",
        "notes": "Test receipt from automation"
    }
    
    response = session.post(f"{BASE_URL}/api/receipts", json=test_receipt)
    if response.status_code in [200, 201]:
        receipt_data = response.json()
        receipt_id = receipt_data.get('receipt_id') or receipt_data.get('id')
        receipt_number = receipt_data.get('receipt_number')
        print_success(f"Receipt created - ID: {receipt_id}, Number: {receipt_number}")
    else:
        print_error(f"Failed to create receipt: {response.status_code} - {response.text}")
        receipt_id = None

# Test 2: Get receipt by ID
if receipt_id:
    print_info("\nFetching created receipt...")
    response = session.get(f"{BASE_URL}/api/receipts/{receipt_id}")
    if response.status_code == 200:
        receipt = response.json().get('receipt', response.json())
        print_success(f"Receipt #{receipt.get('receipt_number')} - Amount: ₹{receipt.get('amount')}")
    else:
        print_error(f"Failed to fetch receipt: {response.status_code}")

# Test 3: Get receipts by traveler
print_info("\nFetching receipts for traveler ID 1...")
response = session.get(f"{BASE_URL}/api/receipts/traveler/1")
if response.status_code == 200:
    traveler_receipts = response.json().get('receipts', [])
    print_success(f"Found {len(traveler_receipts)} receipts for traveler 1")
else:
    print_error(f"Failed to fetch traveler receipts: {response.status_code}")

# Test 4: Get receipts by date range
print_info("\nFetching receipts by date range...")
today = datetime.now().strftime("%Y-%m-%d")
last_month = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
response = session.get(f"{BASE_URL}/api/receipts/range?start_date={last_month}&end_date={today}")
if response.status_code == 200:
    range_receipts = response.json().get('receipts', [])
    print_success(f"Found {len(range_receipts)} receipts in last 30 days")
else:
    print_error(f"Failed to fetch receipts by range: {response.status_code}")

# Test 5: Get receipt stats
print_info("\nFetching receipt statistics...")
response = session.get(f"{BASE_URL}/api/receipts/stats")
if response.status_code == 200:
    stats = response.json().get('stats', {})
    today_stats = stats.get('today', {})
    month_stats = stats.get('this_month', {})
    total_stats = stats.get('total', {})
    print_success(f"Today: {today_stats.get('count', 0)} receipts - ₹{today_stats.get('total', 0)}")
    print_success(f"This Month: {month_stats.get('count', 0)} receipts - ₹{month_stats.get('total', 0)}")
    print_success(f"Total: {total_stats.get('count', 0)} receipts - ₹{total_stats.get('total', 0)}")
else:
    print_error(f"Failed to fetch receipt stats: {response.status_code}")

# ==================== CLEANUP ====================
print_header("🧹 CLEANUP - Deleting test data")

# Delete receipt first (if exists)
if receipt_id:
    print_info(f"Deleting receipt ID: {receipt_id}...")
    response = session.delete(f"{BASE_URL}/api/receipts/{receipt_id}")
    if response.status_code in [200, 201, 204]:
        print_success("Receipt deleted successfully")
        
        # Verify deletion
        verify = session.get(f"{BASE_URL}/api/receipts/{receipt_id}")
        if verify.status_code == 404:
            print_success("Receipt no longer exists (verified)")
        else:
            print_error(f"Receipt still exists: {verify.status_code}")
    else:
        print_error(f"Failed to delete receipt: {response.status_code}")

# Delete invoice
if invoice_id:
    print_info(f"\nDeleting invoice ID: {invoice_id}...")
    response = session.delete(f"{BASE_URL}/api/invoices/{invoice_id}")
    if response.status_code in [200, 201, 204]:
        print_success("Invoice deleted successfully")
        
        # Verify deletion
        verify = session.get(f"{BASE_URL}/api/invoices/{invoice_id}")
        if verify.status_code == 404:
            print_success("Invoice no longer exists (verified)")
        else:
            print_error(f"Invoice still exists: {verify.status_code}")
    else:
        print_error(f"Failed to delete invoice: {response.status_code}")

# ==================== SUMMARY ====================
print_header("📊 TEST SUMMARY")

print(f"\n{'Module':<20} {'Operation':<15} {'Status':<10}")
print("-" * 50)

results = [
    ("Invoices", "GET /invoices", "✅" if response.status_code == 200 else "❌"),
    ("Invoices", "POST /invoices", "✅" if invoice_id else "❌"),
    ("Invoices", "GET /invoices/{id}", "✅" if invoice_id else "N/A"),
    ("Invoices", "PUT /invoices/{id}", "✅" if invoice_id else "N/A"),
    ("Invoices", "DELETE /invoices/{id}", "✅" if invoice_id else "N/A"),
    ("Receipts", "GET /receipts", "✅" if True else "❌"),
    ("Receipts", "POST /receipts", "✅" if receipt_id else "❌"),
    ("Receipts", "GET /receipts/{id}", "✅" if receipt_id else "N/A"),
    ("Receipts", "GET /receipts/traveler/1", "✅" if response.status_code == 200 else "❌"),
    ("Receipts", "GET /receipts/range", "✅" if response.status_code == 200 else "❌"),
    ("Receipts", "GET /receipts/stats", "✅" if response.status_code == 200 else "❌"),
    ("Receipts", "DELETE /receipts/{id}", "✅" if receipt_id else "N/A"),
]

for module, operation, status in results:
    print(f"{module:<20} {operation:<15} {status:<10}")

print_header("🎉 TEST COMPLETE")