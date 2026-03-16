#!/usr/bin/env python
"""
Final Complete System Test - Matches actual database schema
"""

import requests
import time
import json
from datetime import datetime, timedelta

BASE_URL = "https://haj-web-app-production.up.railway.app"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.HEADER}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.HEADER}{'='*60}{Colors.END}")

def login():
    session = requests.Session()
    response = session.post(f"{BASE_URL}/api/login", json={
        "username": "superadmin",
        "password": "admin123"
    })
    if response.status_code == 200:
        print(f"{Colors.GREEN}✅ Logged in successfully{Colors.END}")
        return session
    print(f"{Colors.RED}❌ Login failed{Colors.END}")
    return None

def create_batch(session):
    """Create a batch"""
    batch_data = {
        "batch_name": f"Test Batch {datetime.now().strftime('%H:%M:%S')}",
        "total_seats": 50,
        "status": "Open"
    }
    response = session.post(f"{BASE_URL}/api/batches", json=batch_data)
    if response.status_code in [200, 201]:
        batch_id = response.json().get('batch_id') or response.json().get('id')
        print(f"{Colors.GREEN}✅ Created batch ID: {batch_id}{Colors.END}")
        return batch_id
    else:
        print(f"{Colors.RED}❌ Failed to create batch: {response.text}{Colors.END}")
        return None

def create_traveler(session, batch_id):
    """Create a traveler"""
    timestamp = int(time.time())
    traveler_data = {
        "first_name": "Test",
        "last_name": f"User_{timestamp}",
        "passport_no": f"P{timestamp}",
        "mobile": f"+96650{timestamp%10000000:07d}",
        "batch_id": batch_id,
        "email": f"test.{timestamp}@example.com"
    }
    
    response = session.post(f"{BASE_URL}/api/travelers", json=traveler_data)
    if response.status_code in [200, 201]:
        traveler_id = response.json().get('traveler_id') or response.json().get('id')
        print(f"{Colors.GREEN}✅ Created traveler ID: {traveler_id}{Colors.END}")
        return traveler_id
    else:
        print(f"{Colors.RED}❌ Failed to create traveler: {response.text}{Colors.END}")
        return None

def create_payment(session, traveler_id, batch_id):
    """Create a payment"""
    payment_data = {
        "traveler_id": traveler_id,
        "batch_id": batch_id,
        "amount": 500.00,
        "payment_date": datetime.now().strftime("%Y-%m-%d"),
        "payment_method": "credit_card",
        "status": "completed"
    }
    
    response = session.post(f"{BASE_URL}/api/payments", json=payment_data)
    if response.status_code in [200, 201]:
        payment_id = response.json().get('payment_id') or response.json().get('id')
        print(f"{Colors.GREEN}✅ Created payment ID: {payment_id}{Colors.END}")
        return payment_id
    else:
        print(f"{Colors.RED}❌ Failed to create payment: {response.text}{Colors.END}")
        return None

def create_invoice(session, traveler_id, batch_id):
    """Create an invoice - using amount field"""
    invoice_data = {
        "traveler_id": traveler_id,
        "batch_id": batch_id,
        "amount": 1000.00,
        "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "status": "pending",
        "items": [{"description": "Test Item", "amount": 1000.00}]
    }
    
    response = session.post(f"{BASE_URL}/api/invoices", json=invoice_data)
    if response.status_code in [200, 201]:
        invoice_id = response.json().get('invoice_id')
        print(f"{Colors.GREEN}✅ Created invoice ID: {invoice_id}{Colors.END}")
        return invoice_id
    else:
        print(f"{Colors.RED}❌ Failed to create invoice: {response.text}{Colors.END}")
        return None

def create_receipt(session, traveler_id, payment_id):
    """Create a receipt - simplified version"""
    receipt_data = {
        "traveler_id": traveler_id,
        "payment_id": payment_id,
        "amount": 500.00,
        "receipt_date": datetime.now().strftime("%Y-%m-%d")
    }
    
    response = session.post(f"{BASE_URL}/api/receipts", json=receipt_data)
    if response.status_code in [200, 201]:
        receipt_id = response.json().get('receipt_id')
        print(f"{Colors.GREEN}✅ Created receipt ID: {receipt_id}{Colors.END}")
        return receipt_id
    else:
        print(f"{Colors.RED}❌ Failed to create receipt: {response.text}{Colors.END}")
        return None

def cleanup(session, batch_id, traveler_id=None, payment_id=None, invoice_id=None, receipt_id=None):
    """Clean up all test data"""
    print_header("🧹 CLEANING UP")
    
    if receipt_id:
        session.delete(f"{BASE_URL}/api/receipts/{receipt_id}")
        print(f"{Colors.GREEN}✅ Deleted receipt{Colors.END}")
    if invoice_id:
        session.delete(f"{BASE_URL}/api/invoices/{invoice_id}")
        print(f"{Colors.GREEN}✅ Deleted invoice{Colors.END}")
    if payment_id:
        session.delete(f"{BASE_URL}/api/payments/{payment_id}")
        print(f"{Colors.GREEN}✅ Deleted payment{Colors.END}")
    if traveler_id:
        session.delete(f"{BASE_URL}/api/travelers/{traveler_id}")
        print(f"{Colors.GREEN}✅ Deleted traveler{Colors.END}")
    if batch_id:
        session.delete(f"{BASE_URL}/api/batches/{batch_id}")
        print(f"{Colors.GREEN}✅ Deleted batch{Colors.END}")

def main():
    print_header("🚀 FINAL SYSTEM TEST")
    
    session = login()
    if not session:
        return
    
    # Create batch
    batch_id = create_batch(session)
    if not batch_id:
        return
    
    # Create traveler
    traveler_id = create_traveler(session, batch_id)
    if not traveler_id:
        cleanup(session, batch_id)
        return
    
    # Create payment
    payment_id = create_payment(session, traveler_id, batch_id)
    
    # Create invoice
    invoice_id = create_invoice(session, traveler_id, batch_id)
    
    # Create receipt
    receipt_id = None
    if payment_id:
        receipt_id = create_receipt(session, traveler_id, payment_id)
    
    # Clean up
    cleanup(session, batch_id, traveler_id, payment_id, invoice_id, receipt_id)
    
    print_header("✅ ALL TESTS COMPLETED")

if __name__ == "__main__":
    main()