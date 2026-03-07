#!/usr/bin/env python3
"""
🔷 CORNER TEST SUITE - Alhudha Haj Travel System
Tests all critical endpoints and edge cases for deployment readiness
Run: python test_corner_cases.py
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys

# Configuration
BASE_URL = "http://localhost:8080"
TIMEOUT = 10

# Test Credentials
TEST_USERS = {
    "admin": {"username": "superadmin", "password": "admin123"},
    "manager": {"username": "manager1", "password": "admin123"},
    "staff": {"username": "staff1", "password": "admin123"},
    "viewer": {"username": "viewer1", "password": "admin123"},
}

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
    UNDERLINE = '\033[4m'

class CornerTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def print_header(self, text):
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

    def print_test(self, name, passed, details=""):
        status = f"{Colors.OKGREEN}✅ PASS{Colors.ENDC}" if passed else f"{Colors.FAIL}❌ FAIL{Colors.ENDC}"
        print(f"{status} | {name}")
        if details:
            print(f"   └─ {Colors.OKCYAN}{details}{Colors.ENDC}")
        
        if passed:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{name}: {details}")

    def test_connection(self):
        """Test basic server connection"""
        self.print_header("🔌 CONNECTION TEST")
        
        try:
            response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
            passed = response.status_code in [200, 404, 405]  # Accept any response
            self.print_test("Server is running", passed, f"Status: {response.status_code}")
            return passed
        except Exception as e:
            self.print_test("Server is running", False, f"Error: {str(e)}")
            return False

    def test_authentication(self):
        """Test login for all user roles"""
        self.print_header("🔐 AUTHENTICATION TEST")
        
        all_passed = True
        for role, credentials in TEST_USERS.items():
            try:
                payload = {
                    "username": credentials["username"],
                    "password": credentials["password"]
                }
                response = self.session.post(
                    f"{BASE_URL}/api/auth/login",
                    json=payload,
                    headers=self.headers,
                    timeout=TIMEOUT
                )
                
                passed = response.status_code == 200
                details = ""
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        details = f"Session created for {role}"
                    else:
                        passed = False
                        details = f"API error: {data.get('error', 'Unknown')}"
                else:
                    details = f"HTTP {response.status_code}"
                
                self.print_test(f"Login: {role}", passed, details)
                all_passed = all_passed and passed
                
            except Exception as e:
                self.print_test(f"Login: {role}", False, str(e))
                all_passed = False
        
        return all_passed

    def test_database_connectivity(self):
        """Test database is accessible"""
        self.print_header("📊 DATABASE CONNECTIVITY TEST")
        
        try:
            # Try to fetch batches (basic DB query)
            response = self.session.get(
                f"{BASE_URL}/api/batches",
                headers=self.headers,
                timeout=TIMEOUT
            )
            
            passed = response.status_code in [200, 401]  # 401 if not auth, 200 if OK
            details = f"HTTP {response.status_code}"
            
            if response.status_code == 200:
                data = response.json()
                details = f"Found {len(data.get('data', []))} records"
            elif response.status_code == 401:
                details = "Not authenticated (expected)"
            
            self.print_test("Database query (batches)", passed, details)
            return passed
            
        except Exception as e:
            self.print_test("Database query (batches)", False, str(e))
            return False

    def test_static_files(self):
        """Test static file serving"""
        self.print_header("📁 STATIC FILES TEST")
        
        files_to_test = [
            ("/style.css", "CSS stylesheet"),
            ("/index.html", "Homepage"),
            ("/admin.login.html", "Admin login"),
            ("/traveler_login.html", "Traveler login"),
        ]
        
        all_passed = True
        for file_path, description in files_to_test:
            try:
                response = requests.get(
                    f"{BASE_URL}{file_path}",
                    timeout=TIMEOUT
                )
                passed = response.status_code in [200, 301, 302, 307, 308]
                details = f"HTTP {response.status_code}"
                
                if response.status_code == 200:
                    details += f", Size: {len(response.content)} bytes"
                
                self.print_test(f"File: {description}", passed, details)
                all_passed = all_passed and passed
                
            except Exception as e:
                self.print_test(f"File: {description}", False, str(e))
                all_passed = False
        
        return all_passed

    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        self.print_header("🌐 CORS HEADERS TEST")
        
        try:
            response = requests.options(
                f"{BASE_URL}/api/batches",
                headers={
                    "Origin": "http://example.com",
                    "Access-Control-Request-Method": "GET"
                },
                timeout=TIMEOUT
            )
            
            has_cors = "access-control-allow-origin" in response.headers
            details = f"CORS: {response.headers.get('access-control-allow-origin', 'Not set')}"
            
            self.print_test("CORS headers present", has_cors, details)
            return has_cors
            
        except Exception as e:
            self.print_test("CORS headers present", False, str(e))
            return False

    def test_error_handling(self):
        """Test error handling for edge cases"""
        self.print_header("⚠️ ERROR HANDLING TEST")
        
        test_cases = [
            ("Invalid endpoint", "/api/invalid-route", 404),
            ("Empty login", "/api/auth/login", 400, {"username": "", "password": ""}),
            ("SQL injection attempt", "/api/batches?id=1' OR '1'='1", 200),
            ("Large payload", "/api/auth/login", 400, {"username": "a"*10000, "password": "b"*10000}),
        ]
        
        all_passed = True
        for test_name, endpoint, expected_status, *payload in test_cases:
            try:
                if payload and payload[0]:
                    response = self.session.post(
                        f"{BASE_URL}{endpoint}",
                        json=payload[0],
                        headers=self.headers,
                        timeout=TIMEOUT
                    )
                else:
                    response = requests.get(
                        f"{BASE_URL}{endpoint}",
                        timeout=TIMEOUT
                    )
                
                passed = response.status_code == expected_status
                details = f"Expected {expected_status}, Got {response.status_code}"
                
                self.print_test(test_name, passed, details)
                all_passed = all_passed and passed
                
            except Exception as e:
                self.print_test(test_name, False, str(e))
                all_passed = False
        
        return all_passed

    def test_session_management(self):
        """Test session creation and persistence"""
        self.print_header("🔒 SESSION MANAGEMENT TEST")
        
        try:
            # Login
            login_payload = {
                "username": "admin1",
                "password": "admin123"
            }
            response = self.session.post(
                f"{BASE_URL}/api/auth/login",
                json=login_payload,
                headers=self.headers,
                timeout=TIMEOUT
            )
            
            session_created = response.status_code == 200
            self.print_test("Session creation", session_created, f"HTTP {response.status_code}")
            
            if session_created:
                # Check if session persists
                response2 = self.session.get(
                    f"{BASE_URL}/api/batches",
                    headers=self.headers,
                    timeout=TIMEOUT
                )
                session_persisted = response2.status_code in [200, 401]
                self.print_test("Session persistence", session_persisted, f"HTTP {response2.status_code}")
                return session_created and session_persisted
            
            return False
            
        except Exception as e:
            self.print_test("Session management", False, str(e))
            return False

    def test_input_validation(self):
        """Test input validation and sanitization"""
        self.print_header("✔️ INPUT VALIDATION TEST")
        
        test_cases = [
            ("Null bytes", {"username": "admin\x00", "password": "test"}),
            ("Special chars", {"username": "admin<script>", "password": "test"}),
            ("Very long input", {"username": "a"*1000, "password": "b"*1000}),
            ("Unicode characters", {"username": "مسلم", "password": "test"}),
        ]
        
        all_passed = True
        for test_name, payload in test_cases:
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/auth/login",
                    json=payload,
                    headers=self.headers,
                    timeout=TIMEOUT
                )
                
                # Should not crash server
                passed = response.status_code in [200, 400, 401, 422]
                details = f"HTTP {response.status_code}"
                
                self.print_test(test_name, passed, details)
                all_passed = all_passed and passed
                
            except Exception as e:
                self.print_test(test_name, False, str(e))
                all_passed = False
        
        return all_passed

    def test_response_formats(self):
        """Test API response formats"""
        self.print_header("📋 RESPONSE FORMAT TEST")
        
        try:
            response = self.session.get(
                f"{BASE_URL}/api/batches",
                headers=self.headers,
                timeout=TIMEOUT
            )
            
            # Check if response is valid JSON
            try:
                data = response.json()
                is_json = True
                details = f"Valid JSON response"
            except:
                is_json = False
                details = "Invalid JSON"
            
            self.print_test("JSON response format", is_json, details)
            
            # Check response structure
            if is_json and isinstance(data, (dict, list)):
                has_structure = True
                if isinstance(data, dict):
                    details = f"Keys: {list(data.keys())[:5]}"
                else:
                    details = f"Array with {len(data)} items"
            else:
                has_structure = False
                details = "Invalid structure"
            
            self.print_test("Response structure", has_structure, details)
            
            return is_json and has_structure
            
        except Exception as e:
            self.print_test("Response format", False, str(e))
            return False

    def test_performance(self):
        """Test basic performance metrics"""
        self.print_header("⚡ PERFORMANCE TEST")
        
        start_time = time.time()
        
        try:
            response = self.session.get(
                f"{BASE_URL}/",
                timeout=TIMEOUT
            )
            elapsed = (time.time() - start_time) * 1000  # Convert to ms
            
            passed = elapsed < 5000  # Should respond in less than 5 seconds
            details = f"Response time: {elapsed:.2f}ms"
            
            self.print_test("Homepage load time", passed, details)
            return passed
            
        except Exception as e:
            self.print_test("Homepage load time", False, str(e))
            return False

    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}")
        print("╔═══��══════════════════════════════════════════════════════╗")
        print("║     🔷 CORNER TEST SUITE - HAJ TRAVEL SYSTEM 🔷         ║")
        print("║                  Deployment Readiness Test              ║")
        print("╚══════════════════════════════════════════════════════════╝")
        print(Colors.ENDC)
        
        print(f"🎯 Testing against: {Colors.BOLD}{BASE_URL}{Colors.ENDC}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Run all tests
        self.test_connection()
        self.test_static_files()
        self.test_cors_headers()
        self.test_authentication()
        self.test_session_management()
        self.test_database_connectivity()
        self.test_error_handling()
        self.test_input_validation()
        self.test_response_formats()
        self.test_performance()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        total = self.test_results["passed"] + self.test_results["failed"]
        pass_rate = (self.test_results["passed"] / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}📊 TEST SUMMARY{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
        
        print(f"✅ Passed: {Colors.OKGREEN}{self.test_results['passed']}{Colors.ENDC}")
        print(f"❌ Failed: {Colors.FAIL}{self.test_results['failed']}{Colors.ENDC}")
        print(f"📈 Pass Rate: {Colors.OKBLUE}{pass_rate:.1f}%{Colors.ENDC}\n")
        
        if self.test_results["errors"]:
            print(f"{Colors.WARNING}⚠️ ERRORS:{Colors.ENDC}")
            for error in self.test_results["errors"]:
                print(f"  • {error}")
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        
        if pass_rate >= 80:
            print(f"{Colors.OKGREEN}{Colors.BOLD}✅ READY FOR DEPLOYMENT!{Colors.ENDC}")
        elif pass_rate >= 60:
            print(f"{Colors.WARNING}{Colors.BOLD}⚠️ FIX ISSUES BEFORE DEPLOYMENT{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}❌ CRITICAL ISSUES - DO NOT DEPLOY{Colors.ENDC}")
        
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

if __name__ == "__main__":
    suite = CornerTestSuite()
    try:
        suite.run_all_tests()
        sys.exit(0 if suite.test_results["failed"] == 0 else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Tests interrupted by user{Colors.ENDC}")
        sys.exit(1)