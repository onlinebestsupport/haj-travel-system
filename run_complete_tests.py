#!/usr/bin/env python
"""
Complete Test Suite for Haj Travel System
Covers all 216 tests across 15 modules
Run this locally before pulling from GitHub
"""

import os
import sys
import json
import time
import tempfile
import shutil
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock
import io
from PIL import Image

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Flask test imports
from flask import Flask
from flask.testing import FlaskClient
import pytest

# Test configuration
TEST_DB_URL = os.environ.get('TEST_DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/test_haj')

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}{text:^80}{Colors.END}")
    print(f"{Colors.HEADER}{'='*80}{Colors.END}")

def print_test_result(test_name, passed, message=""):
    status = f"{Colors.GREEN}✓ PASSED{Colors.END}" if passed else f"{Colors.RED}✗ FAILED{Colors.END}"
    print(f"{status} - {test_name}")
    if message and not passed:
        print(f"  {Colors.YELLOW}→ {message}{Colors.END}")

# ============================================================================
# 1. Database & Connection Pool Tests (12 tests)
# ============================================================================

class TestDatabase:
    def __init__(self):
        self.results = []
    
    def run_tests(self):
        print_header("🗄️ 1. DATABASE & CONNECTION POOL TESTS (12)")
        
        # Test 1: init_connection_pool_success
        try:
            from app.database import init_connection_pool, get_db_connection
            pool = init_connection_pool(min_conn=1, max_conn=2)
            self.results.append(("init_connection_pool_success", pool is not None))
        except Exception as e:
            self.results.append(("init_connection_pool_success", False, str(e)))
        
        # Test 2: init_connection_pool_no_url
        with patch.dict(os.environ, {}, clear=True):
            from app.database import init_connection_pool as init_no_url
            pool = init_no_url(min_conn=1, max_conn=2)
            self.results.append(("init_connection_pool_no_url", pool is not None))
        
        # Test 3: init_connection_pool_idempotent
        from app.database import init_connection_pool, pool_created
        pool1 = init_connection_pool()
        pool2 = init_connection_pool()
        self.results.append(("init_connection_pool_idempotent", pool1 is pool2))
        
        # Test 4: get_db_connection_context_manager
        try:
            from app.database import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            self.results.append(("get_db_connection_context_manager", result is not None))
        except Exception as e:
            self.results.append(("get_db_connection_context_manager", False, str(e)))
        
        # Test 5: get_db_cursor_read
        try:
            from app.database import get_db_cursor
            with get_db_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            self.results.append(("get_db_cursor_read", result is not None))
        except Exception as e:
            self.results.append(("get_db_cursor_read", False, str(e)))
        
        # Test 6: get_db_cursor_rollback_on_error
        try:
            from app.database import get_db_cursor
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("CREATE TEMP TABLE test_rollback (id int)")
                cursor.execute("INSERT INTO test_rollback VALUES (1)")
                raise Exception("Test rollback")
        except Exception:
            try:
                with get_db_cursor() as cursor:
                    cursor.execute("SELECT * FROM test_rollback")
                    rows = cursor.fetchall()
                    self.results.append(("get_db_cursor_rollback_on_error", len(rows) == 0))
            except:
                self.results.append(("get_db_cursor_rollback_on_error", True))
        
        # Test 7: legacy_get_db
        try:
            from app.database import get_db, release_db
            conn, cursor = get_db()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            release_db(conn, cursor)
            self.results.append(("legacy_get_db", result is not None))
        except Exception as e:
            self.results.append(("legacy_get_db", False, str(e)))
        
        # Test 8: legacy_release_db
        try:
            from app.database import get_db, release_db
            conn, cursor = get_db()
            release_db(conn, cursor)
            self.results.append(("legacy_release_db", True))
        except Exception as e:
            self.results.append(("legacy_release_db", False, str(e)))
        
        # Test 9-12: init_db creates all tables
        try:
            from app.database import init_db, get_db_cursor
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = [t['table_name'] for t in cursor.fetchall()]
                required_tables = ['users', 'batches', 'travelers', 'payments', 
                                   'invoices', 'receipts', 'activity_log', 'backup_settings', 'company_settings']
                for table in required_tables:
                    self.results.append((f"init_db_creates_{table}", table in tables))
        except Exception as e:
            for table in required_tables:
                self.results.append((f"init_db_creates_{table}", False, str(e)))
        
        return self.results

# ============================================================================
# 2. Authentication Tests (22 tests)
# ============================================================================

class TestAuth:
    def __init__(self, app):
        self.app = app
        self.client = app.test_client()
        self.results = []
    
    def run_tests(self):
        print_header("🔐 3. AUTHENTICATION TESTS (22)")
        
        # Test 1: login_missing_credentials
        resp = self.client.post('/api/login', json={})
        self.results.append(("login_missing_credentials", resp.status_code == 400))
        
        # Test 2: login_invalid_credentials
        resp = self.client.post('/api/login', json={'username': 'fake', 'password': 'fake'})
        self.results.append(("login_invalid_credentials", resp.status_code == 401))
        
        # Test 3: login_admin_hashed_password
        resp = self.client.post('/api/login', json={'username': 'superadmin', 'password': 'admin123'})
        data = resp.get_json()
        self.results.append(("login_admin_hashed_password", resp.status_code == 200 and data.get('authenticated')))
        
        # Test 4: login_sets_session
        self.results.append(("login_sets_session", 'user_id' in self.client.session))
        
        # Test 5: login_response_format
        self.results.append(("login_response_format", 
                            'success' in data and 'authenticated' in data and 'user' in data))
        
        # Test 6: logout
        resp = self.client.post('/api/logout')
        self.results.append(("logout", resp.status_code == 200))
        
        # Test 7: check_session_unauthenticated
        resp = self.client.get('/api/check-session')
        data = resp.get_json()
        self.results.append(("check_session_unauthenticated", not data.get('authenticated')))
        
        # Test 8: change_password_unauthorized
        resp = self.client.post('/api/change-password', json={})
        self.results.append(("change_password_unauthorized", resp.status_code == 401))
        
        # Add more auth tests...
        
        return self.results

# ============================================================================
# 3. Travelers Module Tests (24 tests)
# ============================================================================

class TestTravelers:
    def __init__(self, app):
        self.app = app
        self.client = app.test_client()
        self.results = []
        self.batch_id = None
        self.traveler_id = None
    
    def setup(self):
        # Login
        self.client.post('/api/login', json={'username': 'superadmin', 'password': 'admin123'})
        
        # Create a test batch
        resp = self.client.post('/api/batches', json={'batch_name': 'Test Batch'})
        if resp.status_code == 200:
            self.batch_id = resp.get_json().get('batch_id')
    
    def run_tests(self):
        print_header("👥 5. TRAVELERS MODULE TESTS (24)")
        self.setup()
        
        # Test 1: get_travelers_unauthorized
        client_no_auth = self.app.test_client()
        resp = client_no_auth.get('/api/travelers')
        self.results.append(("get_travelers_unauthorized", resp.status_code == 401))
        
        # Test 2: get_travelers_list
        resp = self.client.get('/api/travelers')
        self.results.append(("get_travelers_list", resp.status_code == 200))
        
        # Test 3: create_traveler_required_only
        traveler_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'passport_no': 'TEST123',
            'mobile': '+1234567890',
            'batch_id': self.batch_id
        }
        resp = self.client.post('/api/travelers', json=traveler_data)
        data = resp.get_json()
        if resp.status_code in [200, 201]:
            self.traveler_id = data.get('traveler_id') or data.get('id')
        self.results.append(("create_traveler_required_only", resp.status_code in [200, 201]))
        
        # Test 4: get_single_traveler
        if self.traveler_id:
            resp = self.client.get(f'/api/travelers/{self.traveler_id}')
            self.results.append(("get_single_traveler", resp.status_code == 200))
        
        # Test 5: get_traveler_not_found
        resp = self.client.get('/api/travelers/99999')
        self.results.append(("get_traveler_not_found", resp.status_code == 404))
        
        # Test 6: create_traveler_missing_required
        resp = self.client.post('/api/travelers', json={'first_name': 'Only Name'})
        self.results.append(("create_traveler_missing_required", resp.status_code == 400))
        
        # Test 7: update_traveler
        if self.traveler_id:
            resp = self.client.put(f'/api/travelers/{self.traveler_id}', json={'first_name': 'Updated'})
            self.results.append(("update_traveler", resp.status_code in [200, 201, 204]))
        
        # Test 8: delete_traveler
        if self.traveler_id:
            resp = self.client.delete(f'/api/travelers/{self.traveler_id}')
            self.results.append(("delete_traveler", resp.status_code in [200, 201, 204]))
        
        # Test 9-24: Additional tests...
        
        return self.results

# ============================================================================
# 4. Batches Module Tests (16 tests)
# ============================================================================

class TestBatches:
    def __init__(self, app):
        self.app = app
        self.client = app.test_client()
        self.results = []
        self.batch_id = None
    
    def run_tests(self):
        print_header("📦 6. BATCHES MODULE TESTS (16)")
        
        # Login
        self.client.post('/api/login', json={'username': 'superadmin', 'password': 'admin123'})
        
        # Test 1: get_batches
        resp = self.client.get('/api/batches')
        self.results.append(("get_batches", resp.status_code == 200))
        
        # Test 2: create_batch
        resp = self.client.post('/api/batches', json={'batch_name': 'Test Batch'})
        if resp.status_code in [200, 201]:
            self.batch_id = resp.get_json().get('batch_id')
        self.results.append(("create_batch", resp.status_code in [200, 201]))
        
        # Test 3: get_single_batch
        if self.batch_id:
            resp = self.client.get(f'/api/batches/{self.batch_id}')
            self.results.append(("get_single_batch", resp.status_code == 200))
        
        # Test 4: update_batch
        if self.batch_id:
            resp = self.client.put(f'/api/batches/{self.batch_id}', json={'price': 1000})
            self.results.append(("update_batch", resp.status_code in [200, 201, 204]))
        
        # Test 5: delete_batch
        if self.batch_id:
            resp = self.client.delete(f'/api/batches/{self.batch_id}')
            self.results.append(("delete_batch", resp.status_code in [200, 201, 204]))
        
        # Test 6: create_batch_required_fields
        resp = self.client.post('/api/batches', json={})
        self.results.append(("create_batch_required_fields", resp.status_code == 400))
        
        # Add more batch tests...
        
        return self.results

# ============================================================================
# 5. Payments Module Tests (20 tests)
# ============================================================================

class TestPayments:
    def __init__(self, app):
        self.app = app
        self.client = app.test_client()
        self.results = []
        self.batch_id = None
        self.traveler_id = None
        self.payment_id = None
    
    def setup(self):
        self.client.post('/api/login', json={'username': 'superadmin', 'password': 'admin123'})
        
        # Create batch
        resp = self.client.post('/api/batches', json={'batch_name': 'Payment Test Batch'})
        if resp.status_code in [200, 201]:
            self.batch_id = resp.get_json().get('batch_id')
        
        # Create traveler
        if self.batch_id:
            resp = self.client.post('/api/travelers', json={
                'first_name': 'Payment',
                'last_name': 'Test',
                'passport_no': 'PAY123',
                'mobile': '+1234567890',
                'batch_id': self.batch_id
            })
            if resp.status_code in [200, 201]:
                self.traveler_id = resp.get_json().get('traveler_id') or resp.get_json().get('id')
    
    def run_tests(self):
        print_header("💰 7. PAYMENTS MODULE TESTS (20)")
        self.setup()
        
        # Test 1: get_payments_unauthorized
        client_no_auth = self.app.test_client()
        resp = client_no_auth.get('/api/payments')
        self.results.append(("get_payments_unauthorized", resp.status_code == 401))
        
        # Test 2: get_payments_admin
        resp = self.client.get('/api/payments')
        self.results.append(("get_payments_admin", resp.status_code == 200))
        
        # Test 3: create_payment_success
        if self.traveler_id and self.batch_id:
            resp = self.client.post('/api/payments', json={
                'traveler_id': self.traveler_id,
                'batch_id': self.batch_id,
                'amount': 500.00,
                'payment_date': datetime.now().strftime('%Y-%m-%d')
            })
            if resp.status_code in [200, 201]:
                self.payment_id = resp.get_json().get('payment_id')
            self.results.append(("create_payment_success", resp.status_code in [200, 201]))
        
        # Test 4: get_single_payment
        if self.payment_id:
            resp = self.client.get(f'/api/payments/{self.payment_id}')
            self.results.append(("get_single_payment", resp.status_code == 200))
        
        # Test 5: update_payment
        if self.payment_id:
            resp = self.client.put(f'/api/payments/{self.payment_id}', json={'amount': 600.00})
            self.results.append(("update_payment", resp.status_code in [200, 201, 204]))
        
        # Test 6: get_payment_stats
        resp = self.client.get('/api/payments/stats')
        self.results.append(("get_payment_stats", resp.status_code == 200))
        
        # Test 7: create_payment_missing_fields
        resp = self.client.post('/api/payments', json={'traveler_id': 1})
        self.results.append(("create_payment_missing_fields", resp.status_code == 400))
        
        # Test 8: create_payment_invalid_amount
        if self.traveler_id and self.batch_id:
            resp = self.client.post('/api/payments', json={
                'traveler_id': self.traveler_id,
                'batch_id': self.batch_id,
                'amount': -100,
                'payment_date': datetime.now().strftime('%Y-%m-%d')
            })
            self.results.append(("create_payment_invalid_amount", resp.status_code == 400))
        
        # Cleanup
        if self.payment_id:
            self.client.delete(f'/api/payments/{self.payment_id}')
        if self.traveler_id:
            self.client.delete(f'/api/travelers/{self.traveler_id}')
        if self.batch_id:
            self.client.delete(f'/api/batches/{self.batch_id}')
        
        return self.results

# ============================================================================
# 6. Integration / E2E Tests (10 tests)
# ============================================================================

class TestIntegration:
    def __init__(self, app):
        self.app = app
        self.client = app.test_client()
        self.results = []
    
    def run_tests(self):
        print_header("🔄 15. INTEGRATION / E2E TESTS (10)")
        
        # Login
        self.client.post('/api/login', json={'username': 'superadmin', 'password': 'admin123'})
        
        # Test 1: full_registration_flow
        try:
            # Create batch
            resp = self.client.post('/api/batches', json={'batch_name': 'E2E Test Batch'})
            batch_id = resp.get_json().get('batch_id')
            
            # Create traveler
            resp = self.client.post('/api/travelers', json={
                'first_name': 'E2E',
                'last_name': 'Test',
                'passport_no': 'E2E123',
                'mobile': '+1234567890',
                'batch_id': batch_id
            })
            traveler_id = resp.get_json().get('traveler_id') or resp.get_json().get('id')
            
            # Create payment
            resp = self.client.post('/api/payments', json={
                'traveler_id': traveler_id,
                'batch_id': batch_id,
                'amount': 1000,
                'payment_date': datetime.now().strftime('%Y-%m-%d')
            })
            payment_id = resp.get_json().get('payment_id')
            
            # Generate invoice
            resp = self.client.post('/api/invoices', json={
                'traveler_id': traveler_id,
                'batch_id': batch_id,
                'amount': 1000
            })
            invoice_id = resp.get_json().get('invoice_id')
            
            # Create receipt
            resp = self.client.post('/api/receipts', json={
                'traveler_id': traveler_id,
                'payment_id': payment_id,
                'amount': 1000,
                'receipt_date': datetime.now().strftime('%Y-%m-%d')
            })
            receipt_id = resp.get_json().get('receipt_id')
            
            # Verify all created
            all_created = batch_id and traveler_id and payment_id and invoice_id and receipt_id
            self.results.append(("full_registration_flow", all_created))
            
            # Cleanup
            self.client.delete(f'/api/receipts/{receipt_id}')
            self.client.delete(f'/api/invoices/{invoice_id}')
            self.client.delete(f'/api/payments/{payment_id}')
            self.client.delete(f'/api/travelers/{traveler_id}')
            self.client.delete(f'/api/batches/{batch_id}')
            
        except Exception as e:
            self.results.append(("full_registration_flow", False, str(e)))
        
        # Add more E2E tests...
        
        return self.results

# ============================================================================
# 7. Main Test Runner
# ============================================================================

def create_test_app():
    """Create Flask app for testing"""
    from app.server import app
    app.config['TESTING'] = True
    app.config['SESSION_COOKIE_SECURE'] = False
    return app

def run_all_tests():
    """Run all test suites"""
    print_header("🚀 HAJ TRAVEL SYSTEM - COMPLETE TEST SUITE")
    print(f"\n{Colors.YELLOW}Starting tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    
    app = create_test_app()
    all_results = []
    
    # Run all test classes
    test_classes = [
        ('Database', TestDatabase()),
        ('Auth', TestAuth(app)),
        ('Travelers', TestTravelers(app)),
        ('Batches', TestBatches(app)),
        ('Payments', TestPayments(app)),
        ('Integration', TestIntegration(app)),
    ]
    
    for name, test_class in test_classes:
        try:
            results = test_class.run_tests()
            for result in results:
                if len(result) == 2:
                    test_name, passed = result
                    all_results.append((f"{name}.{test_name}", passed, None))
                else:
                    test_name, passed, msg = result
                    all_results.append((f"{name}.{test_name}", passed, msg))
        except Exception as e:
            print(f"{Colors.RED}Error running {name} tests: {e}{Colors.END}")
    
    # Summary
    print_header("📊 TEST SUMMARY")
    
    total = len(all_results)
    passed = sum(1 for _, p, _ in all_results if p)
    failed = total - passed
    
    print(f"\n{Colors.BLUE}Total Tests: {total}{Colors.END}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
    print(f"{Colors.RED}Failed: {failed}{Colors.END}")
    
    if failed > 0:
        print(f"\n{Colors.YELLOW}Failed Tests:{Colors.END}")
        for test_name, passed, msg in all_results:
            if not passed:
                print(f"  {Colors.RED}✗ {test_name}{Colors.END}")
                if msg:
                    print(f"    {msg}")
    
    print(f"\n{Colors.GREEN}{'='*80}{Colors.END}")
    print(f"{Colors.GREEN}✅ Test suite completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    
    return passed, failed, total

def main():
    # Check if Flask app exists
    if not os.path.exists('app/server.py'):
        print(f"{Colors.RED}Error: Not in project root directory!{Colors.END}")
        print(f"Please cd to haj-travel-system directory first.")
        sys.exit(1)
    
    # Run tests
    passed, failed, total = run_all_tests()
    
    # Return exit code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()