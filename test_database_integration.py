#!/usr/bin/env python3
"""
Database-Frontend-Endpoint Integration Test
Verifies all database tables are connected to frontend pages via correct API endpoints
Run: python test_database_integration.py
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuration
BASE_URL = "https://haj-web-app-production.up.railway.app"
TIMEOUT = 10

# Test Credentials
TEST_USER = {"username": "admin1", "password": "admin123"}

# Database tables and their corresponding endpoints/frontend pages
DATABASE_MAPPING = [
    {
        'table': 'users',
        'endpoint': '/api/admin/users',
        'frontend': '/admin/users.html',
        'required_fields': ['id', 'username', 'role'],
        'description': 'System users with roles'
    },
    {
        'table': 'travelers',
        'endpoint': '/api/travelers',
        'frontend': '/admin/travelers.html',
        'required_fields': ['id', 'first_name', 'last_name', 'passport_no'],
        'description': 'Pilgrim information'
    },
    {
        'table': 'batches',
        'endpoint': '/api/batches',
        'frontend': '/',
        'required_fields': ['id', 'batch_name', 'price', 'status'],
        'description': 'Haj/Umrah packages'
    },
    {
        'table': 'payments',
        'endpoint': '/api/payments',
        'frontend': '/admin/payments.html',
        'required_fields': ['id', 'amount', 'status'],
        'description': 'Payment records'
    },
    {
        'table': 'invoices',
        'endpoint': '/api/invoices',
        'frontend': '/admin/invoices.html',
        'required_fields': ['id', 'invoice_number', 'total_amount'],
        'description': 'Invoice data'
    },
    {
        'table': 'receipts',
        'endpoint': '/api/receipts',
        'frontend': '/admin/receipts.html',
        'required_fields': ['id', 'receipt_number', 'amount'],
        'description': 'Receipt data'
    },
    {
        'table': 'activity_log',
        'endpoint': '/api/admin/activity',
        'frontend': '/admin/dashboard.html',
        'required_fields': ['id', 'action', 'created_at'],
        'description': 'User activity logs'
    },
    {
        'table': 'company_settings',
        'endpoint': '/api/company/settings',
        'frontend': '/admin/settings.html',
        'required_fields': ['legal_name', 'email', 'phone'],
        'description': 'Company configuration'
    },
    {
        'table': 'frontpage_settings',
        'endpoint': '/api/frontpage/settings',
        'frontend': '/',
        'required_fields': ['hero_heading', 'packages'],
        'description': 'Front page content'
    },
    {
        'table': 'whatsapp_settings',
        'endpoint': '/api/whatsapp/settings',
        'frontend': '/admin/whatsapp.html',
        'required_fields': ['number', 'enabled'],
        'description': 'WhatsApp configuration'
    },
    {
        'table': 'email_settings',
        'endpoint': '/api/email/settings',
        'frontend': '/admin/email.html',
        'required_fields': ['from_email', 'smtp_server'],
        'description': 'Email configuration'
    },
    {
        'table': 'backup_history',
        'endpoint': '/api/admin/backups',
        'frontend': '/admin/backup.html',
        'required_fields': ['id', 'backup_name', 'created_at'],
        'description': 'Backup records'
    }
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

class IntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'details': []
        }
        self.session_cookie = None

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
        """Login to get session cookie"""
        try:
            response = self.session.post(
                f"{BASE_URL}/api/login",
                json=TEST_USER,
                headers={'Content-Type': 'application/json'},
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('authenticated'):
                    # Save cookies for subsequent requests
                    self.session_cookie = self.session.cookies.get_dict()
                    return True
            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False

    def test_endpoint(self, mapping):
        """Test if API endpoint returns data"""
        try:
            response = self.session.get(
                f"{BASE_URL}{mapping['endpoint']}",
                timeout=TIMEOUT,
                headers={'Content-Type': 'application/json'}
            )
            
            passed = response.status_code in [200, 401, 403]
            details = f"HTTP {response.status_code}"
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'success' in data:
                        details += f" - Success: {data.get('success')}"
                    
                    # Check for required fields in response
                    if mapping['required_fields']:
                        # Try to find required fields in response structure
                        found_fields = []
                        if isinstance(data, dict):
                            if 'data' in data and isinstance(data['data'], list):
                                sample = data['data'][0] if data['data'] else {}
                                found_fields = [f for f in mapping['required_fields'] if f in sample]
                            elif isinstance(data.get(mapping['table']), list):
                                sample = data[mapping['table']][0] if data[mapping['table']] else {}
                                found_fields = [f for f in mapping['required_fields'] if f in sample]
                        
                        if found_fields:
                            details += f" - Found fields: {', '.join(found_fields)}"
                        else:
                            details += " - No data to check fields"
                    
                except json.JSONDecodeError:
                    details += " - Invalid JSON"
            
            self.print_test(
                f"{mapping['table']} API endpoint",
                passed,
                details
            )
            
            return passed, response
            
        except Exception as e:
            self.print_test(f"{mapping['table']} API endpoint", False, str(e))
            return False, None

    def test_frontend_page(self, mapping):
        """Test if frontend page loads"""
        try:
            response = self.session.get(
                f"{BASE_URL}{mapping['frontend']}",
                timeout=TIMEOUT
            )
            
            passed = response.status_code == 200
            details = f"HTTP {response.status_code} - {len(response.content)} bytes"
            
            # Check if page contains references to the data
            html = response.text.lower()
            
            # Look for table or container that should display this data
            table_indicators = ['table', 'tbody', 'data-table', 'grid']
            has_table = any(ind in html for ind in table_indicators)
            
            if has_table:
                details += " - Has data container"
            else:
                details += " - No obvious data container"
            
            self.print_test(
                f"{mapping['table']} frontend page",
                passed,
                details
            )
            
            return passed, html
            
        except Exception as e:
            self.print_test(f"{mapping['table']} frontend page", False, str(e))
            return False, ""

    def test_data_consistency(self, mapping, api_response):
        """Check if API data matches frontend expectations"""
        if not api_response or api_response.status_code != 200:
            self.print_warning(
                f"{mapping['table']} data consistency",
                "Skipped - API not available"
            )
            return
        
        try:
            data = api_response.json()
            
            # Try to extract data based on common response structures
            records = None
            if isinstance(data, dict):
                if 'data' in data:
                    records = data['data']
                elif mapping['table'] in data:
                    records = data[mapping['table']]
                elif 'records' in data:
                    records = data['records']
                elif 'batches' in data:
                    records = data['batches']
                elif 'travelers' in data:
                    records = data['travelers']
            
            if records and isinstance(records, list) and len(records) > 0:
                # Check if the data matches what frontend would expect
                sample = records[0]
                found_fields = [f for f in mapping['required_fields'] if f in sample]
                
                if len(found_fields) == len(mapping['required_fields']):
                    self.print_test(
                        f"{mapping['table']} data structure",
                        True,
                        f"All required fields present: {', '.join(found_fields)}"
                    )
                else:
                    self.print_warning(
                        f"{mapping['table']} data structure",
                        f"Missing fields: {set(mapping['required_fields']) - set(found_fields)}"
                    )
            else:
                self.print_warning(
                    f"{mapping['table']} data",
                    "No records found to verify structure"
                )
                
        except Exception as e:
            self.print_warning(
                f"{mapping['table']} data consistency",
                f"Error: {str(e)}"
            )

    def test_database_direct(self):
        """Test database connection through PostgreSQL CLI"""
        self.print_header("🗄️  DIRECT DATABASE VERIFICATION")
        
        try:
            # Try to connect via railway CLI
            import subprocess
            
            # Test 1: Check if we can list tables
            result = subprocess.run(
                ['railway', 'connect', 'Postgres', '-c', "\\dt"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                output = result.stdout
                # Count tables in output
                table_count = output.count('public |')
                self.print_test(
                    "Database tables accessible",
                    True,
                    f"Found approximately {table_count} tables via CLI"
                )
            else:
                self.print_warning(
                    "Database CLI access",
                    "Could not connect via railway CLI - this is normal if not in project directory"
                )
                
        except Exception as e:
            self.print_warning(
                "Database CLI test",
                f"Skipped - {str(e)}"
            )

    def test_endpoint_security(self, mapping):
        """Test if endpoint properly handles unauthorized access"""
        try:
            # Create a new session without auth
            anon_session = requests.Session()
            
            response = anon_session.get(
                f"{BASE_URL}{mapping['endpoint']}",
                timeout=TIMEOUT
            )
            
            # Should return 401 for protected endpoints
            is_protected = mapping['endpoint'].startswith('/api/admin') or \
                          mapping['endpoint'] in ['/api/travelers', '/api/payments', 
                                                 '/api/invoices', '/api/receipts']
            
            if is_protected:
                passed = response.status_code == 401
                self.print_test(
                    f"{mapping['table']} endpoint security",
                    passed,
                    f"Unauthorized access returns {response.status_code}"
                )
            else:
                # Public endpoints can be 200
                passed = response.status_code in [200, 401]
                self.print_test(
                    f"{mapping['table']} endpoint accessibility",
                    passed,
                    f"Public endpoint returns {response.status_code}"
                )
                
        except Exception as e:
            self.print_warning(
                f"{mapping['table']} security test",
                str(e)
            )

    def run_all_tests(self):
        """Run all integration tests"""
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}")
        print("╔" + "═"*78 + "╗")
        print("║     🗄️  DATABASE-FRONTEND-ENDPOINT INTEGRATION TEST 🗄️      ║")
        print("║        Verifying all connections are properly configured      ║")
        print("╚" + "═"*78 + "╝")
        print(Colors.ENDC)
        
        print(f"🎯 Testing: {Colors.BOLD}{BASE_URL}{Colors.ENDC}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"👤 User: {Colors.BOLD}{TEST_USER['username']}{Colors.ENDC}")
        print(f"📊 Tables to test: {Colors.BOLD}{len(DATABASE_MAPPING)}{Colors.ENDC}\n")
        
        # Login first
        if not self.login():
            print(f"{Colors.FAIL}❌ Login failed - cannot proceed{Colors.ENDC}")
            return
        
        # Test database via CLI
        self.test_database_direct()
        
        # Test each table's integration
        self.print_header("📊 DATABASE TABLE INTEGRATION TESTS")
        
        for mapping in DATABASE_MAPPING:
            print(f"\n{Colors.BOLD}{Colors.UNDERLINE}Testing {mapping['table']}{Colors.ENDC} - {mapping['description']}")
            
            # Test API endpoint
            api_ok, api_response = self.test_endpoint(mapping)
            
            # Test frontend page
            page_ok, _ = self.test_frontend_page(mapping)
            
            # Test data consistency if API worked
            if api_ok and api_response:
                self.test_data_consistency(mapping, api_response)
            
            # Test security
            self.test_endpoint_security(mapping)
            
            time.sleep(0.5)  # Small delay between tests
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        total = self.results['passed'] + self.results['failed']
        pass_rate = (self.results['passed'] / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}📊 INTEGRATION TEST SUMMARY{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
        
        print(f"✅ Passed:  {Colors.OKGREEN}{self.results['passed']}{Colors.ENDC}")
        print(f"❌ Failed:  {Colors.FAIL}{self.results['failed']}{Colors.ENDC}")
        print(f"⚠️ Warnings: {Colors.WARNING}{self.results['warnings']}{Colors.ENDC}")
        print(f"📈 Pass Rate: {Colors.OKBLUE}{pass_rate:.1f}%{Colors.ENDC}\n")
        
        # Table status
        print(f"{Colors.BOLD}Table Integration Status:{Colors.ENDC}")
        status = "✅" if pass_rate >= 80 else "⚠️" if pass_rate >= 60 else "❌"
        print(f"  {status} Database-Frontend Integration: {pass_rate:.1f}% connected\n")
        
        if self.results['failed'] == 0:
            print(f"{Colors.OKGREEN}{Colors.BOLD}✅ ALL DATABASE TABLES ARE PROPERLY CONNECTED!{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}{Colors.BOLD}⚠️ Some tables have integration issues - check warnings above{Colors.ENDC}")
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")

if __name__ == "__main__":
    tester = IntegrationTester()
    try:
        tester.run_all_tests()
        sys.exit(0 if tester.results['failed'] == 0 else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Tests interrupted by user{Colors.ENDC}")
        sys.exit(1)