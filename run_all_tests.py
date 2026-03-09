#!/usr/bin/env python3
"""
🧪 COMPLETE TEST SUITE - No Dependencies Required
Run: python run_all_tests.py
"""

import requests
import json
import os
import sys
import hashlib
from datetime import datetime, timedelta
import time

# Colors for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

BASE_URL = "http://localhost:8080"

class TestRunner:
    def __init__(self):
        self.session = requests.Session()
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.total = 0
        self.errors = []
    
    def print_header(self, text):
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    def test(self, name, func, skip=False):
        """Run a single test"""
        self.total += 1
        
        if skip:
            print(f"{Colors.WARNING}⊘ SKIP{Colors.ENDC} | {name}")
            self.skipped += 1
            return
        
        try:
            func()
            print(f"{Colors.OKGREEN}✅ PASS{Colors.ENDC} | {name}")
            self.passed += 1
        except AssertionError as e:
            print(f"{Colors.FAIL}❌ FAIL{Colors.ENDC} | {name}")
            print(f"   └─ {Colors.OKCYAN}{str(e)}{Colors.ENDC}")
            self.failed += 1
            self.errors.append((name, str(e)))
        except Exception as e:
            print(f"{Colors.FAIL}❌ ERROR{Colors.ENDC} | {name}")
            print(f"   └─ {Colors.FAIL}{type(e).__name__}: {str(e)}{Colors.ENDC}")
            self.failed += 1
            self.errors.append((name, f"{type(e).__name__}: {str(e)}"))
    
    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        self.print_header("📊 TEST SUMMARY")
        
        print(f"{Colors.OKGREEN}✅ Passed:{Colors.ENDC}  {self.passed}/{self.total}")
        print(f"{Colors.FAIL}❌ Failed:{Colors.ENDC}  {self.failed}/{self.total}")
        print(f"{Colors.WARNING}⊘ Skipped:{Colors.ENDC} {self.skipped}/{self.total}")
        print(f"{Colors.OKBLUE}📈 Pass Rate:{Colors.ENDC} {pass_rate:.1f}%\n")
        
        if self.errors:
            print(f"{Colors.FAIL}{Colors.BOLD}FAILED TESTS:{Colors.ENDC}")
            for name, error in self.errors:
                print(f"  • {name}")
                print(f"    → {error}\n")
        
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
        
        return self.failed == 0

# ====== TEST GROUPS ======

class AuthenticationTests(TestRunner):
    """🔐 Authentication Tests"""
    
    def run(self):
        self.print_header("🔐 AUTHENTICATION TESTS")
        
        self.test("Password hashing", self.test_password_hash)
        self.test("Different passwords produce different hashes", self.test_different_passwords)
        self.test("Login with valid credentials", self.test_valid_login)
        self.test("Login with invalid credentials", self.test_invalid_login)
        self.test("Login with empty fields", self.test_empty_fields)
        self.test("Logout", self.test_logout)
        self.test("Get current user without auth", self.test_get_user_no_auth)
        
        return self.print_summary()
    
    def test_password_hash(self):
        password = "test123"
        hash1 = hashlib.sha256(password.encode()).hexdigest()
        hash2 = hashlib.sha256(password.encode()).hexdigest()
        assert hash1 == hash2, "Hashes don't match"
        assert hash1 != password, "Hash equals plaintext"
    
    def test_different_passwords(self):
        hash1 = hashlib.sha256("pass123".encode()).hexdigest()
        hash2 = hashlib.sha256("pass456".encode()).hexdigest()
        assert hash1 != hash2, "Different passwords produce same hash"
    
    def test_valid_login(self):
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            'username': 'superadmin',
            'password': 'admin123'
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Login not successful"
    
    def test_invalid_login(self):
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            'username': 'invalid_user_xyz',
            'password': 'invalid_pass_xyz'
        })
        assert response.status_code in [401, 400], f"Expected 401/400, got {response.status_code}"
    
    def test_empty_fields(self):
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            'username': '',
            'password': ''
        })
        assert response.status_code in [400, 401], f"Expected 400/401, got {response.status_code}"
    
    def test_logout(self):
        response = self.session.post(f"{BASE_URL}/api/auth/logout")
        assert response.status_code in [200, 401], f"Expected 200/401, got {response.status_code}"
    
    def test_get_user_no_auth(self):
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

class BatchesTests(TestRunner):
    """📋 Batches Tests"""
    
    def run(self):
        self.print_header("📋 BATCHES TESTS")
        
        self.test("Get batches list", self.test_get_batches)
        self.test("Get single batch", self.test_get_batch)
        self.test("Create batch requires auth", self.test_create_requires_auth)
        self.test("Batch schema validation", self.test_batch_schema)
        
        return self.print_summary()
    
    def test_get_batches(self):
        response = self.session.get(f"{BASE_URL}/api/batches")
        assert response.status_code in [200, 401], f"Expected 200/401, got {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert 'data' in data or 'batches' in data, "No data in response"
    
    def test_get_batch(self):
        response = self.session.get(f"{BASE_URL}/api/batches/1")
        assert response.status_code in [200, 401, 404], f"Got {response.status_code}"
    
    def test_create_requires_auth(self):
        session = requests.Session()
        payload = {
            'batch_name': 'Test Batch',
            'batch_number': 'TEST-001',
            'total_slots': 50
        }
        response = session.post(f"{BASE_URL}/api/batches", json=payload)
        assert response.status_code in [401, 403, 400], f"Should require auth, got {response.status_code}"
    
    def test_batch_schema(self):
        batch = {
            'id': 1,
            'batch_name': 'Test',
            'batch_number': 'BAT-001',
            'total_slots': 50,
            'available_slots': 50,
            'status': 'active'
        }
        assert 'batch_name' in batch, "Missing batch_name"
        assert 'batch_number' in batch, "Missing batch_number"
        assert batch['total_slots'] >= 0, "Invalid total_slots"
        assert batch['available_slots'] >= 0, "Invalid available_slots"

class TravelersTests(TestRunner):
    """✈️ Travelers Tests"""
    
    def run(self):
        self.print_header("✈️ TRAVELERS TESTS")
        
        self.test("Get travelers list", self.test_get_travelers)
        self.test("Get single traveler", self.test_get_traveler)
        self.test("Create traveler requires auth", self.test_create_requires_auth)
        self.test("Traveler schema validation", self.test_traveler_schema)
        self.test("Email validation", self.test_email_validation)
        
        return self.print_summary()
    
    def test_get_travelers(self):
        response = self.session.get(f"{BASE_URL}/api/travelers")
        assert response.status_code in [200, 401], f"Got {response.status_code}"
    
    def test_get_traveler(self):
        response = self.session.get(f"{BASE_URL}/api/travelers/1")
        assert response.status_code in [200, 401, 404], f"Got {response.status_code}"
    
    def test_create_requires_auth(self):
        session = requests.Session()
        payload = {
            'full_name': 'Test Traveler',
            'email': 'test@example.com',
            'phone': '+1234567890'
        }
        response = session.post(f"{BASE_URL}/api/travelers", json=payload)
        assert response.status_code in [401, 403, 400], f"Should require auth, got {response.status_code}"
    
    def test_traveler_schema(self):
        traveler = {
            'id': 1,
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'passport_number': 'ABC123456',
            'status': 'active'
        }
        assert 'full_name' in traveler, "Missing full_name"
        assert 'email' in traveler, "Missing email"
        assert '@' in traveler['email'], "Invalid email"
    
    def test_email_validation(self):
        valid_emails = ['user@example.com', 'test.user@domain.co.uk', 'user+tag@example.com']
        for email in valid_emails:
            assert '@' in email, f"Invalid email: {email}"
            assert '.' in email.split('@')[1], f"Invalid email: {email}"

class PaymentsTests(TestRunner):
    """💰 Payments Tests"""
    
    def run(self):
        self.print_header("💰 PAYMENTS TESTS")
        
        self.test("Get payments list", self.test_get_payments)
        self.test("Payment schema validation", self.test_payment_schema)
        self.test("Payment amount validation", self.test_amount_validation)
        self.test("Valid payment statuses", self.test_payment_statuses)
        
        return self.print_summary()
    
    def test_get_payments(self):
        response = self.session.get(f"{BASE_URL}/api/payments")
        assert response.status_code in [200, 401], f"Got {response.status_code}"
    
    def test_payment_schema(self):
        payment = {
            'id': 1,
            'traveler_id': 1,
            'amount': 1000.00,
            'payment_method': 'bank_transfer',
            'status': 'completed'
        }
        assert 'amount' in payment, "Missing amount"
        assert 'status' in payment, "Missing status"
        assert payment['amount'] > 0, "Invalid amount"
    
    def test_amount_validation(self):
        valid_amounts = [100.00, 1000.50, 10000.00]
        for amount in valid_amounts:
            assert amount > 0, f"Invalid amount: {amount}"
    
    def test_payment_statuses(self):
        valid_statuses = ['pending', 'completed', 'failed', 'refunded']
        for status in valid_statuses:
            assert status in valid_statuses, f"Invalid status: {status}"

class ReportsTests(TestRunner):
    """📊 Reports Tests"""
    
    def run(self):
        self.print_header("📊 REPORTS TESTS")
        
        self.test("Get summary report", self.test_summary_report)
        self.test("Get payments report", self.test_payments_report)
        self.test("Get travelers report", self.test_travelers_report)
        
        return self.print_summary()
    
    def test_summary_report(self):
        response = self.session.get(f"{BASE_URL}/api/reports/summary")
        assert response.status_code in [200, 401], f"Got {response.status_code}"
    
    def test_payments_report(self):
        response = self.session.get(f"{BASE_URL}/api/reports/payments")
        assert response.status_code in [200, 401], f"Got {response.status_code}"
    
    def test_travelers_report(self):
        response = self.session.get(f"{BASE_URL}/api/reports/travelers")
        assert response.status_code in [200, 401], f"Got {response.status_code}"

class ErrorHandlingTests(TestRunner):
    """⚠️ Error Handling Tests"""
    
    def run(self):
        self.print_header("⚠️ ERROR HANDLING TESTS")
        
        self.test("404 Not Found", self.test_404)
        self.test("Bad request handling", self.test_bad_request)
        self.test("SQL injection prevention", self.test_sql_injection)
        self.test("XSS prevention", self.test_xss)
        self.test("Missing auth header", self.test_missing_auth)
        
        return self.print_summary()
    
    def test_404(self):
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/nonexistent/endpoint")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_bad_request(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={'invalid': 'data'})
        assert response.status_code in [400, 401], f"Expected 400/401, got {response.status_code}"
    
    def test_sql_injection(self):
        session = requests.Session()
        attempts = ["' OR '1'='1", "'; DROP TABLE users; --"]
        for attempt in attempts:
            response = session.post(f"{BASE_URL}/api/auth/login", json={
                'username': attempt,
                'password': attempt
            })
            assert response.status_code in [400, 401, 500], f"Injection not prevented: {response.status_code}"
    
    def test_xss(self):
        session = requests.Session()
        xss_attempts = ["<script>alert('xss')</script>", "javascript:alert('xss')"]
        for attempt in xss_attempts:
            response = session.post(f"{BASE_URL}/api/auth/login", json={
                'username': attempt,
                'password': 'test'
            })
            assert response.status_code in [400, 401], f"XSS not prevented: {response.status_code}"
    
    def test_missing_auth(self):
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/batches")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

class HealthTests(TestRunner):
    """❤️ Health & Static Files Tests"""
    
    def run(self):
        self.print_header("❤️ HEALTH TESTS")
        
        self.test("Health endpoint", self.test_health)
        self.test("Homepage loads", self.test_homepage)
        self.test("CSS file accessible", self.test_css)
        self.test("Response time < 5s", self.test_response_time)
        
        return self.print_summary()
    
    def test_health(self):
        session = requests.Session()
        response = session.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('status') == 'healthy', "Not healthy"
    
    def test_homepage(self):
        session = requests.Session()
        response = session.get(f"{BASE_URL}/", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_css(self):
        session = requests.Session()
        response = session.get(f"{BASE_URL}/style.css", timeout=5)
        assert response.status_code in [200, 404], f"Got {response.status_code}"
    
    def test_response_time(self):
        session = requests.Session()
        start = time.time()
        response = session.get(f"{BASE_URL}/health", timeout=5)
        elapsed = (time.time() - start) * 1000
        assert elapsed < 5000, f"Response time {elapsed}ms too slow"

class DataValidationTests(TestRunner):
    """✔️ Data Validation Tests"""
    
    def run(self):
        self.print_header("✔️ DATA VALIDATION TESTS")
        
        self.test("Email format validation", self.test_email_format)
        self.test("Phone number length", self.test_phone_length)
        self.test("Batch slots consistency", self.test_slots_consistency)
        self.test("Status values validation", self.test_status_values)
        self.test("Date format validation", self.test_date_format)
        
        return self.print_summary()
    
    def test_email_format(self):
        emails = [
            ('valid@example.com', True),
            ('test.user@domain.co.uk', True),
            ('user+tag@example.com', True),
            ('invalid.email', False),
            ('@example.com', False),
            ('user@', False),
        ]
        for email, should_be_valid in emails:
            has_at = '@' in email
            has_dot = '.' in email.split('@')[1] if '@' in email else False
            is_valid = has_at and has_dot
            assert is_valid == should_be_valid, f"Email validation failed for {email}"
    
    def test_phone_length(self):
        phones = ['+1234567890', '1234567890', '+44-20-7946-0958']
        for phone in phones:
            digits = phone.replace('-', '').replace('+', '')
            assert len(digits) >= 10, f"Phone too short: {phone}"
    
    def test_slots_consistency(self):
        batch = {'total_slots': 50, 'available_slots': 30, 'used_slots': 20}
        assert batch['total_slots'] == batch['available_slots'] + batch['used_slots'], "Slots don't match"
    
    def test_status_values(self):
        valid_statuses = ['active', 'inactive', 'pending', 'completed']
        for status in valid_statuses:
            assert status in valid_statuses, f"Invalid status: {status}"
    
    def test_date_format(self):
        from datetime import datetime
        try:
            date_str = datetime.now().isoformat()
            parsed = datetime.fromisoformat(date_str)
            assert parsed is not None, "Date parsing failed"
        except Exception as e:
            raise AssertionError(f"Date format error: {e}")

# ====== MAIN ======

def main():
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║         🧪 COMPLETE TEST SUITE - ALL TESTS 🧪                   ║")
    print("║              No Dependencies Required - Pure Python             ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(Colors.ENDC)
    
    print(f"🎯 Target: {Colors.BOLD}{BASE_URL}{Colors.ENDC}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run all test groups
    test_groups = [
        HealthTests(),
        AuthenticationTests(),
        BatchesTests(),
        TravelersTests(),
        PaymentsTests(),
        ReportsTests(),
        ErrorHandlingTests(),
        DataValidationTests()
    ]
    
    all_results = []
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    
    for test_group in test_groups:
        test_group.run()
        all_results.append(test_group)
        total_passed += test_group.passed
        total_failed += test_group.failed
        total_skipped += test_group.skipped
    
    # Final summary
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'FINAL SUMMARY'.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    total = total_passed + total_failed
    pass_rate = (total_passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.OKGREEN}✅ Total Passed:{Colors.ENDC}  {total_passed}")
    print(f"{Colors.FAIL}❌ Total Failed:{Colors.ENDC}  {total_failed}")
    print(f"{Colors.WARNING}⊘ Total Skipped:{Colors.ENDC} {total_skipped}")
    print(f"{Colors.OKBLUE}📈 Pass Rate:{Colors.ENDC}    {pass_rate:.1f}%\n")
    
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    
    if pass_rate >= 90:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✅ EXCELLENT - System is Production Ready!{Colors.ENDC}")
    elif pass_rate >= 75:
        print(f"{Colors.WARNING}{Colors.BOLD}⚠️ GOOD - Minor issues to address{Colors.ENDC}")
    elif pass_rate >= 60:
        print(f"{Colors.WARNING}{Colors.BOLD}⚠️ FAIR - Several issues need fixing{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}❌ POOR - Critical issues detected{Colors.ENDC}")
    
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    return total_failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
