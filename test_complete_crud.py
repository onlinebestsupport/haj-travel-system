#!/usr/bin/env python3
"""
COMPLETE CRUD + FRONTEND INTEGRATION TEST
Tests all database tables for CRUD operations and frontend loading
Run: python test_complete_crud.py
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import random
import string

# Configuration
BASE_URL = "https://haj-web-app-production.up.railway.app"
TIMEOUT = 15

# Test Credentials
TEST_USERS = [
    {"username": "admin1", "password": "admin123", "role": "admin"},
    {"username": "superadmin", "password": "admin123", "role": "superadmin"}
]

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'  # Added missing UNDERLINE

# Database tables with their CRUD endpoints and test data
DATABASE_TABLES = [
    {
        'table': 'users',
        'endpoints': {
            'list': '/api/admin/users',
            'get': '/api/admin/users/{}',
            'create': '/api/admin/users',
            'update': '/api/admin/users/{}',
            'delete': '/api/admin/users/{}'
        },
        'frontend': '/admin/users.html',
        'test_data': {
            'username': 'testuser_' + ''.join(random.choices(string.digits, k=4)),
            'password': 'Test@123',
            'name': 'Test User',
            'role': 'staff',
            'email': 'test@example.com'
        },
        'required_fields': ['id', 'username', 'role'],
        'description': 'System users'
    },
    {
        'table': 'travelers',
        'endpoints': {
            'list': '/api/travelers',
            'get': '/api/travelers/{}',
            'create': '/api/travelers',
            'update': '/api/travelers/{}',
            'delete': '/api/travelers/{}'
        },
        'frontend': '/admin/travelers.html',
        'test_data': {
            'first_name': 'Test',
            'last_name': 'Traveler',
            'passport_no': 'TST' + ''.join(random.choices(string.digits, k=7)),
            'mobile': '98765' + ''.join(random.choices(string.digits, k=5)),
            'email': 'test.traveler@example.com',
            'gender': 'Male',
            'dob': '1990-01-01'
        },
        'required_fields': ['id', 'first_name', 'last_name', 'passport_no'],
        'description': 'Pilgrim information'
    },
    {
        'table': 'batches',
        'endpoints': {
            'list': '/api/batches',
            'get': '/api/batches/{}',
            'create': '/api/batches',
            'update': '/api/batches/{}',
            'delete': '/api/batches/{}'
        },
        'frontend': '/admin/batches.html',
        'test_data': {
            'batch_name': 'Test Batch ' + datetime.now().strftime('%Y%m%d%H%M%S'),
            'total_seats': 50,
            'price': 500000.00,
            'departure_date': '2026-12-01',
            'return_date': '2026-12-20',
            'status': 'Open',
            'description': 'Test batch for CRUD testing'
        },
        'required_fields': ['id', 'batch_name', 'price', 'status'],
        'description': 'Haj/Umrah packages'
    },
    {
        'table': 'payments',
        'endpoints': {
            'list': '/api/payments',
            'get': '/api/payments/{}',
            'create': '/api/payments',
            'update': '/api/payments/{}',
            'delete': '/api/payments/{}',
            'reverse': '/api/payments/{}/reverse'
        },
        'frontend': '/admin/payments.html',
        'test_data': {
            'amount': 25000.00,
            'payment_method': 'Bank Transfer',
            'payment_date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'completed',
            'remarks': 'Test payment'
        },
        'required_fields': ['id', 'amount', 'status'],
        'description': 'Payment records'
    },
    {
        'table': 'invoices',
        'endpoints': {
            'list': '/api/invoices',
            'get': '/api/invoices/{}',
            'create': '/api/invoices',
            'update': '/api/invoices/{}',
            'delete': '/api/invoices/{}'
        },
        'frontend': '/admin/invoices.html',
        'test_data': {
            'invoice_number': 'INV-TST-' + ''.join(random.choices(string.digits, k=6)),
            'base_amount': 500000.00,
            'gst_percent': 5,
            'tcs_percent': 1,
            'status': 'draft'
        },
        'required_fields': ['id', 'invoice_number', 'total_amount'],
        'description': 'Invoice data'
    },
    {
        'table': 'receipts',
        'endpoints': {
            'list': '/api/receipts',
            'get': '/api/receipts/{}',
            'create': '/api/receipts',
            'delete': '/api/receipts/{}',
            'print': '/api/receipts/{}/print'
        },
        'frontend': '/admin/receipts.html',
        'test_data': {
            'receipt_number': 'RCP-TST-' + ''.join(random.choices(string.digits, k=6)),
            'receipt_type': 'payment',
            'remarks': 'Test receipt'
        },
        'required_fields': ['id', 'receipt_number', 'amount'],
        'description': 'Receipt data'
    },
    {
        'table': 'company_settings',
        'endpoints': {
            'get': '/api/company/settings',
            'update': '/api/company/settings',
            'details': '/api/company/details',
            'bank': '/api/company/bank-details',
            'tax': '/api/company/tax-details',
            'contact': '/api/company/contact-details'
        },
        'frontend': '/admin/settings.html',
        'test_data': {
            'legal_name': 'Alhudha Haj Travel Test',
            'email': 'test@alhudha.com',
            'phone': '+91 9876543210',
            'gstin': '27ABCDE1234F1Z5',
            'pan': 'ABCDE1234F'
        },
        'required_fields': ['legal_name', 'email', 'phone'],
        'description': 'Company configuration'
    },
    {
        'table': 'frontpage_settings',
        'endpoints': {
            'get': '/api/frontpage/settings',
            'update': '/api/frontpage/settings',
            'hero': '/api/frontpage/hero',
            'packages': '/api/frontpage/packages',
            'features': '/api/frontpage/features'
        },
        'frontend': '/',
        'test_data': {
            'hero_heading': 'Test Hero Heading',
            'hero_subheading': 'Test Subheading',
            'packages_title': 'Our Test Packages',
            'alert_enabled': False
        },
        'required_fields': ['hero_heading'],
        'description': 'Front page content'
    },
    {
        'table': 'whatsapp_settings',
        'endpoints': {
            'get': '/api/whatsapp/settings',
            'update': '/api/whatsapp/settings',
            'test': '/api/whatsapp/test'
        },
        'frontend': '/admin/whatsapp.html',
        'test_data': {
            'number': '919876543210',
            'message_template': 'Test template {name}',
            'enabled': False
        },
        'required_fields': ['number', 'enabled'],
        'description': 'WhatsApp configuration'
    },
    {
        'table': 'email_settings',
        'endpoints': {
            'get': '/api/email/settings',
            'update': '/api/email/settings',
            'test': '/api/email/test'
        },
        'frontend': '/admin/email.html',
        'test_data': {
            'from_email': 'test@alhudha.com',
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True
        },
        'required_fields': ['from_email', 'smtp_server'],
        'description': 'Email configuration'
    },
    {
        'table': 'backup_history',
        'endpoints': {
            'list': '/api/admin/backups',
            'create': '/api/admin/backup/create',
            'download': '/api/admin/backup/{}/download',
            'delete': '/api/admin/backup/{}'
        },
        'frontend': '/admin/backup.html',
        'required_fields': ['id', 'backup_name', 'created_at'],
        'description': 'Backup records'
    },
    {
        'table': 'activity_log',
        'endpoints': {
            'list': '/api/admin/activity',
            'recent': '/api/admin/recent-activity'
        },
        'frontend': '/admin/dashboard.html',
        'required_fields': ['id', 'action', 'created_at'],
        'description': 'Activity logs'
    }
]

class CRUDTester:
    def __init__(self):
        self.session = requests.Session()
        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'details': []
        }
        self.created_ids = {}  # Store created IDs for cleanup
        self.start_time = datetime.now()

    def print_header(self, text):
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")

    def print_test(self, name, passed, details=""):
        if passed:
            status = f"{Colors.OKGREEN}✅ PASS{Colors.ENDC}"
            self.results['passed'] += 1
        else:
            status = f"{Colors.FAIL}❌ FAIL{Colors.ENDC}"
            self.results['failed'] += 1
        
        print(f"{status} | {name}")
        if details:
            print(f"   └─ {Colors.OKCYAN}{details}{Colors.ENDC}")
        self.results['details'].append(f"{name}: {'PASS' if passed else 'FAIL'}")

    def print_warning(self, name, details=""):
        status = f"{Colors.WARNING}⚠️ WARN{Colors.ENDC}"
        self.results['warnings'] += 1
        print(f"{status} | {name}")
        if details:
            print(f"   └─ {Colors.OKCYAN}{details}{Colors.ENDC}")

    def login(self):
        """Login to get session"""
        print(f"\n{Colors.BOLD}🔐 LOGGING IN...{Colors.ENDC}")
        
        for user in TEST_USERS:
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/login",
                    json={"username": user["username"], "password": user["password"]},
                    headers={'Content-Type': 'application/json'},
                    timeout=TIMEOUT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('authenticated'):
                        print(f"   ✅ Logged in as {user['username']} ({user['role']})")
                        return True
            except:
                continue
        
        print(f"   {Colors.FAIL}❌ Login failed{Colors.ENDC}")
        return False

    def test_frontend_page(self, table):
        """Test if frontend page loads"""
        try:
            response = self.session.get(
                f"{BASE_URL}{table['frontend']}",
                timeout=TIMEOUT
            )
            
            passed = response.status_code == 200
            details = f"HTTP {response.status_code} - {len(response.content)} bytes"
            
            # Check for essential HTML elements
            html = response.text.lower()
            checks = [
                ('<!doctype html' in html, 'DOCTYPE'),
                ('<html' in html, 'HTML tag'),
                ('<head' in html, 'Head section'),
                ('<body' in html, 'Body section')
            ]
            
            score = sum(1 for check, _ in checks if check)
            details += f" - HTML structure: {score}/4"
            
            self.print_test(
                f"{table['table']} frontend page",
                passed,
                details
            )
            return passed, html
            
        except Exception as e:
            self.print_test(f"{table['table']} frontend page", False, str(e))
            return False, ""

    def test_list_endpoint(self, table):
        """Test LIST/GET all endpoint"""
        if 'list' not in table['endpoints']:
            self.print_warning(f"{table['table']} LIST", "Endpoint not defined")
            return True
        
        try:
            response = self.session.get(
                f"{BASE_URL}{table['endpoints']['list']}",
                timeout=TIMEOUT
            )
            
            passed = response.status_code == 200
            details = f"HTTP {response.status_code}"
            
            if passed:
                data = response.json()
                if data.get('success'):
                    if 'data' in data:
                        count = len(data['data']) if isinstance(data['data'], list) else 1
                    elif table['table'] in data:
                        count = len(data[table['table']]) if isinstance(data[table['table']], list) else 1
                    else:
                        count = 'N/A'
                    details += f" - Success, records: {count}"
            
            self.print_test(f"{table['table']} LIST endpoint", passed, details)
            return passed
            
        except Exception as e:
            self.print_test(f"{table['table']} LIST endpoint", False, str(e))
            return False

    def test_create_endpoint(self, table):
        """Test CREATE endpoint"""
        if 'create' not in table['endpoints'] or 'test_data' not in table:
            self.print_warning(f"{table['table']} CREATE", "Skipped - no test data")
            return None
        
        try:
            # Prepare test data
            test_data = table['test_data'].copy()
            
            # Add required foreign keys if needed
            if table['table'] == 'payments':
                # Need a traveler and batch
                if not hasattr(self, 'test_traveler_id'):
                    # Create a test traveler
                    traveler_data = {
                        'first_name': 'Test',
                        'last_name': 'Traveler',
                        'passport_no': 'TST' + ''.join(random.choices(string.digits, k=7)),
                        'mobile': '9876543210',
                        'batch_id': 5  # Use existing batch
                    }
                    t_resp = self.session.post(
                        f"{BASE_URL}/api/travelers",
                        json=traveler_data,
                        timeout=TIMEOUT
                    )
                    if t_resp.status_code == 200:
                        t_data = t_resp.json()
                        self.test_traveler_id = t_data.get('traveler', {}).get('id')
                
                test_data['traveler_id'] = getattr(self, 'test_traveler_id', 5)
                test_data['batch_id'] = 5
                
            elif table['table'] == 'invoices':
                test_data['traveler_id'] = 5
                test_data['batch_id'] = 5
                
            elif table['table'] == 'receipts':
                test_data['payment_id'] = 1  # Use existing payment
            
            response = self.session.post(
                f"{BASE_URL}{table['endpoints']['create']}",
                json=test_data,
                timeout=TIMEOUT
            )
            
            passed = response.status_code in [200, 201]
            details = f"HTTP {response.status_code}"
            
            if passed:
                data = response.json()
                if data.get('success'):
                    # Store created ID for later tests
                    if table['table'] == 'users' and 'user' in data:
                        self.created_ids[table['table']] = data['user'].get('id')
                    elif table['table'] == 'travelers' and 'traveler' in data:
                        self.created_ids[table['table']] = data['traveler'].get('id')
                    elif 'id' in data:
                        self.created_ids[table['table']] = data['id']
                    details += f" - Created successfully"
            
            self.print_test(f"{table['table']} CREATE endpoint", passed, details)
            return passed
            
        except Exception as e:
            self.print_test(f"{table['table']} CREATE endpoint", False, str(e))
            return False

    def test_get_endpoint(self, table):
        """Test GET single record endpoint"""
        if 'get' not in table['endpoints'] or table['table'] not in self.created_ids:
            return True
        
        try:
            record_id = self.created_ids[table['table']]
            response = self.session.get(
                f"{BASE_URL}{table['endpoints']['get'].format(record_id)}",
                timeout=TIMEOUT
            )
            
            passed = response.status_code == 200
            details = f"HTTP {response.status_code}"
            
            if passed:
                data = response.json()
                if data.get('success'):
                    details += f" - Retrieved ID {record_id}"
            
            self.print_test(f"{table['table']} GET endpoint", passed, details)
            return passed
            
        except Exception as e:
            self.print_test(f"{table['table']} GET endpoint", False, str(e))
            return False

    def test_update_endpoint(self, table):
        """Test UPDATE endpoint"""
        if 'update' not in table['endpoints'] or table['table'] not in self.created_ids:
            return True
        
        try:
            record_id = self.created_ids[table['table']]
            update_data = {'status': 'updated'} if table['table'] == 'users' else {'remarks': 'Updated via test'}
            
            response = self.session.put(
                f"{BASE_URL}{table['endpoints']['update'].format(record_id)}",
                json=update_data,
                timeout=TIMEOUT
            )
            
            passed = response.status_code == 200
            details = f"HTTP {response.status_code}"
            
            if passed:
                data = response.json()
                if data.get('success'):
                    details += f" - Updated ID {record_id}"
            
            self.print_test(f"{table['table']} UPDATE endpoint", passed, details)
            return passed
            
        except Exception as e:
            self.print_test(f"{table['table']} UPDATE endpoint", False, str(e))
            return False

    def test_delete_endpoint(self, table):
        """Test DELETE endpoint"""
        if 'delete' not in table['endpoints'] or table['table'] not in self.created_ids:
            return True
        
        try:
            record_id = self.created_ids[table['table']]
            response = self.session.delete(
                f"{BASE_URL}{table['endpoints']['delete'].format(record_id)}",
                timeout=TIMEOUT
            )
            
            passed = response.status_code in [200, 204]
            details = f"HTTP {response.status_code}"
            
            if passed:
                details += f" - Deleted ID {record_id}"
                del self.created_ids[table['table']]
            
            self.print_test(f"{table['table']} DELETE endpoint", passed, details)
            return passed
            
        except Exception as e:
            self.print_test(f"{table['table']} DELETE endpoint", False, str(e))
            return False

    def test_api_security(self, table):
        """Test API security - unauthorized access"""
        try:
            # Create anonymous session
            anon = requests.Session()
            
            if 'list' in table['endpoints']:
                response = anon.get(
                    f"{BASE_URL}{table['endpoints']['list']}",
                    timeout=TIMEOUT
                )
                
                is_protected = table['table'] not in ['batches', 'frontpage_settings']
                if is_protected:
                    passed = response.status_code == 401
                    self.print_test(
                        f"{table['table']} security",
                        passed,
                        f"Unauthorized access returns {response.status_code}"
                    )
                else:
                    passed = response.status_code == 200
                    self.print_test(
                        f"{table['table']} public access",
                        passed,
                        f"Public endpoint returns {response.status_code}"
                    )
                    
        except Exception as e:
            self.print_warning(f"{table['table']} security test", str(e))

    def test_frontend_data_display(self, table, html):
        """Test if frontend has elements to display data"""
        if not html:
            return
        
        indicators = [
            ('table', 'Data table'),
            ('tbody', 'Table body'),
            ('card', 'Card layout'),
            ('list', 'List view'),
            ('grid', 'Grid layout')
        ]
        
        found = []
        for indicator, desc in indicators:
            if indicator in html.lower():
                found.append(desc)
        
        if found:
            self.print_test(
                f"{table['table']} display elements",
                True,
                f"Found: {', '.join(found)}"
            )
        else:
            self.print_warning(
                f"{table['table']} display elements",
                "No obvious data containers found"
            )

    def run_all_tests(self):
        """Run all CRUD and frontend tests"""
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}")
        print("╔" + "═"*78 + "╗")
        print("║     🔄 COMPLETE CRUD + FRONTEND INTEGRATION TEST 🔄       ║")
        print("║     Testing Create, Read, Update, Delete operations       ║")
        print("║        and frontend data display for all tables           ║")
        print("╚" + "═"*78 + "╝")
        print(Colors.ENDC)
        
        print(f"🎯 Testing: {Colors.BOLD}{BASE_URL}{Colors.ENDC}")
        print(f"⏰ Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Tables to test: {Colors.BOLD}{len(DATABASE_TABLES)}{Colors.ENDC}\n")
        
        # Login
        if not self.login():
            print(f"\n{Colors.FAIL}❌ Cannot proceed without login{Colors.ENDC}")
            return
        
        # Test each table
        for table in DATABASE_TABLES:
            print(f"\n{Colors.BOLD}{Colors.UNDERLINE}Testing {table['table']}{Colors.ENDC} - {table['description']}")
            
            # 1. Test frontend page load
            page_ok, html = self.test_frontend_page(table)
            
            # 2. Test frontend display elements
            if page_ok and html:
                self.test_frontend_data_display(table, html)
            
            # 3. Test LIST endpoint
            self.test_list_endpoint(table)
            
            # 4. Test CREATE endpoint
            self.test_create_endpoint(table)
            
            # 5. Test GET endpoint (if we created something)
            self.test_get_endpoint(table)
            
            # 6. Test UPDATE endpoint
            self.test_update_endpoint(table)
            
            # 7. Test DELETE endpoint
            self.test_delete_endpoint(table)
            
            # 8. Test security
            self.test_api_security(table)
            
            time.sleep(0.5)  # Small delay
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        total = self.results['passed'] + self.results['failed']
        pass_rate = (self.results['passed'] / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}📊 FINAL TEST SUMMARY{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
        
        print(f"✅ Passed:  {Colors.OKGREEN}{self.results['passed']}{Colors.ENDC}")
        print(f"❌ Failed:  {Colors.FAIL}{self.results['failed']}{Colors.ENDC}")
        print(f"⚠️ Warnings: {Colors.WARNING}{self.results['warnings']}{Colors.ENDC}")
        print(f"📈 Pass Rate: {Colors.OKBLUE}{pass_rate:.1f}%{Colors.ENDC}")
        print(f"⏱️  Time: {elapsed:.1f} seconds\n")
        
        # Overall verdict
        if pass_rate >= 90:
            print(f"{Colors.OKGREEN}{Colors.BOLD}✅ ALL SYSTEMS OPERATIONAL!{Colors.ENDC}")
            print(f"{Colors.OKGREEN}   Database CRUD and frontend integration working correctly{Colors.ENDC}")
        elif pass_rate >= 75:
            print(f"{Colors.WARNING}{Colors.BOLD}⚠️ MOSTLY OPERATIONAL{Colors.ENDC}")
            print(f"{Colors.WARNING}   Some issues need attention{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}❌ CRITICAL ISSUES FOUND{Colors.ENDC}")
            print(f"{Colors.FAIL}   System needs immediate attention{Colors.ENDC}")
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")

if __name__ == "__main__":
    tester = CRUDTester()
    try:
        tester.run_all_tests()
        sys.exit(0 if tester.results['failed'] == 0 else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Tests interrupted by user{Colors.ENDC}")
        sys.exit(1)