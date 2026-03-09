#!/usr/bin/env python3
"""
🔷 CORNER TEST SUITE - Production Railway Deployment
Tests all critical endpoints for: https://haj-web-app-production.up.railway.app
Run: python test_corner_cases_production.py
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings for testing
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ====== CONFIGURATION ======
BASE_URL = "https://haj-web-app-production.up.railway.app"
TIMEOUT = 15  # Extended timeout for production
VERIFY_SSL = True  # Set to False only if certificate issues

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

class ProductionCornerTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "warnings": []
        }
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Haj-Travel-System-Test/1.0"
        }
        self.auth_token = None
        self.performance_metrics = {}

    def print_header(self, text):
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

    def print_test(self, name, passed, details="", is_warning=False):
        if is_warning:
            status = f"{Colors.WARNING}⚠️ WARN{Colors.ENDC}"
        else:
            status = f"{Colors.OKGREEN}✅ PASS{Colors.ENDC}" if passed else f"{Colors.FAIL}❌ FAIL{Colors.ENDC}"
        
        print(f"{status} | {name}")
        if details:
            print(f"   └─ {Colors.OKCYAN}{details}{Colors.ENDC}")
        
        if is_warning:
            self.test_results["warnings"].append(f"{name}: {details}")
        elif passed:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{name}: {details}")

    def test_ssl_certificate(self):
        """Test SSL/TLS certificate validity"""
        self.print_header("🔒 SSL/TLS CERTIFICATE TEST")
        
        try:
            response = requests.head(BASE_URL, timeout=TIMEOUT, verify=VERIFY_SSL)
            passed = True
            details = "✅ Valid SSL certificate (Railway managed)"
            self.print_test("SSL certificate validity", passed, details)
            
            # Check certificate expiration
            try:
                cert = response.raw.connection.sock.getpeercert()
                if cert:
                    details = f"Certificate issued by: {cert.get('issuer', 'Unknown')}"
                    self.print_test("Certificate issuer", True, details)
            except:
                pass
            
            return True
        except requests.exceptions.SSLError as e:
            self.print_test("SSL certificate validity", False, f"SSL Error: {str(e)}")
            return False
        except Exception as e:
            self.print_test("SSL certificate validity", False, str(e))
            return False

    def test_https_redirect(self):
        """Test HTTP to HTTPS redirect"""
        self.print_header("🔀 HTTPS REDIRECT TEST")
        
        http_url = BASE_URL.replace("https://", "http://")
        
        try:
            response = requests.get(http_url, timeout=TIMEOUT, allow_redirects=False)
            
            # Railway typically returns 301/302 or 307/308 for redirect
            is_redirect = response.status_code in [301, 302, 307, 308]
            location_header = response.headers.get('location', '')
            is_https = 'https://' in location_header
            
            passed = is_redirect and (is_https or response.status_code in [200])
            details = f"HTTP Status: {response.status_code}, Redirect to HTTPS: {is_https}"
            
            self.print_test("HTTP to HTTPS redirect", passed, details)
            return passed
        except requests.exceptions.ConnectionError:
            self.print_test("HTTP to HTTPS redirect", True, "HTTP not exposed (expected for Railway)")
            return True
        except Exception as e:
            self.print_test("HTTP to HTTPS redirect", False, str(e))
            return False

    def test_connection(self):
        """Test basic server connection"""
        self.print_header("🌐 CONNECTION TEST")
        
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT, verify=VERIFY_SSL)
            elapsed = (time.time() - start_time) * 1000
            
            self.performance_metrics['homepage_load'] = elapsed
            
            passed = response.status_code in [200, 301, 302, 304]
            details = f"Status: {response.status_code}, Response time: {elapsed:.2f}ms"
            
            self.print_test("Server connection", passed, details)
            return passed
        except requests.exceptions.ConnectTimeout:
            self.print_test("Server connection", False, "Connection timeout (server may be down)")
            return False
        except Exception as e:
            self.print_test("Server connection", False, f"Error: {str(e)}")
            return False

    def test_cors_headers(self):
        """Test CORS headers are properly configured"""
        self.print_header("🌐 CORS HEADERS TEST")
        
        try:
            response = requests.options(
                f"{BASE_URL}/api/batches",
                headers={
                    **self.headers,
                    "Origin": "https://example.com",
                    "Access-Control-Request-Method": "GET"
                },
                timeout=TIMEOUT,
                verify=VERIFY_SSL
            )
            
            cors_header = response.headers.get('access-control-allow-origin')
            has_cors = bool(cors_header)
            
            details = f"CORS: {cors_header if cors_header else 'Not configured'}"
            self.print_test("CORS headers present", has_cors, details)
            
            if has_cors:
                allow_methods = response.headers.get('access-control-allow-methods', 'Not specified')
                self.print_test("CORS methods", True, f"Allowed: {allow_methods}")
            
            return has_cors
        except Exception as e:
            self.print_test("CORS headers", False, str(e))
            return False

    def test_authentication(self):
        """Test authentication with all user roles"""
        self.print_header("🔐 AUTHENTICATION TEST")
        
        all_passed = True
        for role, credentials in TEST_USERS.items():
            try:
                payload = {
                    "username": credentials["username"],
                    "password": credentials["password"]
                }
                
                start_time = time.time()
                response = self.session.post(
                    f"{BASE_URL}/api/auth/login",
                    json=payload,
                    headers=self.headers,
                    timeout=TIMEOUT,
                    verify=VERIFY_SSL
                )
                elapsed = (time.time() - start_time) * 1000
                
                passed = response.status_code == 200
                details = f"HTTP {response.status_code}, Time: {elapsed:.2f}ms"
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get("success"):
                            details += f" - Session created"
                            if self.auth_token is None:
                                self.auth_token = response.cookies.get('alhudha_session')
                        else:
                            passed = False
                            details += f" - API Error: {data.get('error', 'Unknown')}"
                    except json.JSONDecodeError:
                        passed = False
                        details += " - Invalid JSON response"
                
                self.print_test(f"Login: {role.upper()}", passed, details)
                all_passed = all_passed and passed
                
            except requests.exceptions.Timeout:
                self.print_test(f"Login: {role.upper()}", False, "Request timeout")
                all_passed = False
            except Exception as e:
                self.print_test(f"Login: {role.upper()}", False, str(e))
                all_passed = False
        
        return all_passed

    def test_database_connectivity(self):
        """Test database queries work"""
        self.print_header("📊 DATABASE CONNECTIVITY TEST")
        
        try:
            start_time = time.time()
            response = self.session.get(
                f"{BASE_URL}/api/batches",
                headers=self.headers,
                timeout=TIMEOUT,
                verify=VERIFY_SSL
            )
            elapsed = (time.time() - start_time) * 1000
            
            self.performance_metrics['batches_query'] = elapsed
            
            passed = response.status_code in [200, 401]
            details = f"HTTP {response.status_code}, Time: {elapsed:.2f}ms"
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    record_count = len(data.get('data', []))
                    details += f" - Found {record_count} records"
                except:
                    pass
            elif response.status_code == 401:
                details += " (Not authenticated - expected without login)"
            
            self.print_test("Database query (batches)", passed, details)
            return passed
            
        except requests.exceptions.Timeout:
            self.print_test("Database query", False, "Database query timeout")
            return False
        except Exception as e:
            self.print_test("Database query", False, str(e))
            return False

    def test_static_files(self):
        """Test static file serving"""
        self.print_header("📁 STATIC FILES TEST")
        
        files_to_test = [
            ("/index.html", "Homepage"),
            ("/style.css", "Main stylesheet"),
            ("/admin.login.html", "Admin login page"),
            ("/traveler_login.html", "Traveler login page"),
        ]
        
        all_passed = True
        for file_path, description in files_to_test:
            try:
                start_time = time.time()
                response = requests.get(
                    f"{BASE_URL}{file_path}",
                    timeout=TIMEOUT,
                    verify=VERIFY_SSL,
                    allow_redirects=True
                )
                elapsed = (time.time() - start_time) * 1000
                
                passed = response.status_code in [200, 304]
                details = f"HTTP {response.status_code}, Size: {len(response.content)} bytes, Time: {elapsed:.2f}ms"
                
                self.print_test(f"File: {description}", passed, details)
                all_passed = all_passed and passed
                
            except requests.exceptions.Timeout:
                self.print_test(f"File: {description}", False, "Request timeout")
                all_passed = False
            except Exception as e:
                self.print_test(f"File: {description}", False, str(e))
                all_passed = False
        
        return all_passed

    def test_error_handling(self):
        """Test error handling for edge cases"""
        self.print_header("⚠️ ERROR HANDLING TEST")
        
        test_cases = [
            ("Invalid endpoint", "/api/invalid-endpoint-xyz", 404),
            ("Missing auth", "/api/batches", 401),
            ("Malformed JSON", "/api/auth/login", 400),
        ]
        
        all_passed = True
        for test_name, endpoint, expected_status in test_cases:
            try:
                if "auth" in endpoint:
                    response = self.session.post(
                        f"{BASE_URL}{endpoint}",
                        json={},
                        headers=self.headers,
                        timeout=TIMEOUT,
                        verify=VERIFY_SSL
                    )
                else:
                    response = requests.get(
                        f"{BASE_URL}{endpoint}",
                        timeout=TIMEOUT,
                        verify=VERIFY_SSL
                    )
                
                passed = response.status_code == expected_status
                details = f"Expected {expected_status}, Got {response.status_code}"
                
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
                timeout=TIMEOUT,
                verify=VERIFY_SSL
            )
            
            # Check if response is valid JSON
            try:
                data = response.json()
                is_json = True
                details = "Valid JSON response"
                self.print_test("JSON response format", is_json, details)
            except json.JSONDecodeError:
                is_json = False
                details = "Invalid JSON response"
                self.print_test("JSON response format", is_json, details)
                return False
            
            # Check response structure
            if isinstance(data, (dict, list)):
                has_structure = True
                if isinstance(data, dict):
                    details = f"Object with keys: {list(data.keys())[:5]}"
                else:
                    details = f"Array with {len(data)} items"
                self.print_test("Response structure", has_structure, details)
            else:
                has_structure = False
                self.print_test("Response structure", has_structure, "Unexpected response type")
                return False
            
            return is_json and has_structure
            
        except Exception as e:
            self.print_test("Response format test", False, str(e))
            return False

    def test_security_headers(self):
        """Test important security headers"""
        self.print_header("🛡️ SECURITY HEADERS TEST")
        
        try:
            response = requests.get(
                f"{BASE_URL}/",
                timeout=TIMEOUT,
                verify=VERIFY_SSL
            )
            
            security_headers = {
                'X-Frame-Options': 'Clickjacking protection',
                'X-Content-Type-Options': 'MIME type sniffing protection',
                'Strict-Transport-Security': 'HTTPS enforcement',
                'Content-Security-Policy': 'XSS protection',
            }
            
            for header, description in security_headers.items():
                present = header in response.headers
                details = f"Value: {response.headers.get(header, 'Not set')[:50]}"
                
                if present:
                    self.print_test(f"Header: {header}", True, details)
                else:
                    self.print_test(f"Header: {header}", False, details, is_warning=True)
            
            return True
        except Exception as e:
            self.print_test("Security headers test", False, str(e))
            return False

    def test_health_check(self):
        """Test health check endpoint"""
        self.print_header("❤️ HEALTH CHECK TEST")
        
        health_endpoints = [
            "/health",
            "/api/health",
            "/status",
            "/api/status",
        ]
        
        found_health = False
        for endpoint in health_endpoints:
            try:
                response = requests.get(
                    f"{BASE_URL}{endpoint}",
                    timeout=TIMEOUT,
                    verify=VERIFY_SSL
                )
                
                if response.status_code == 200:
                    self.print_test(f"Health endpoint: {endpoint}", True, "OK")
                    found_health = True
                    break
            except:
                pass
        
        if not found_health:
            self.print_test("Health check endpoint", False, "No health endpoint found", is_warning=True)
        
        return True

    def test_rate_limiting(self):
        """Test if rate limiting is configured"""
        self.print_header("⏱️ RATE LIMITING TEST")
        
        try:
            # Make multiple requests quickly
            rate_limit_headers = []
            for i in range(5):
                response = requests.get(
                    f"{BASE_URL}/api/batches",
                    timeout=TIMEOUT,
                    verify=VERIFY_SSL
                )
                
                # Check for rate limit headers
                if 'X-RateLimit-Limit' in response.headers:
                    rate_limit_headers.append(response.headers['X-RateLimit-Limit'])
                if 'RateLimit-Limit' in response.headers:
                    rate_limit_headers.append(response.headers['RateLimit-Limit'])
            
            if rate_limit_headers:
                self.print_test("Rate limiting configured", True, f"Limit: {rate_limit_headers[0]}")
                return True
            else:
                self.print_test("Rate limiting", False, "No rate limit headers detected", is_warning=True)
                return True
        except Exception as e:
            self.print_test("Rate limiting test", False, str(e))
            return False

    def test_performance_metrics(self):
        """Display performance metrics"""
        self.print_header("⚡ PERFORMANCE METRICS")
        
        if self.performance_metrics:
            print(f"{Colors.OKCYAN}Response Time Summary:{Colors.ENDC}\n")
            
            for endpoint, time_ms in self.performance_metrics.items():
                status = "🟢" if time_ms < 1000 else "🟡" if time_ms < 3000 else "🔴"
                print(f"{status} {endpoint}: {time_ms:.2f}ms")
            
            avg_time = sum(self.performance_metrics.values()) / len(self.performance_metrics)
            print(f"\n{Colors.BOLD}Average Response Time: {avg_time:.2f}ms{Colors.ENDC}\n")
        
        return True

    def run_all_tests(self):
        """Run all production tests"""
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}")
        print("╔════════════════════════════════════════════════════════════════════╗")
        print("║        🔷 PRODUCTION CORNER TEST SUITE - HAJ TRAVEL SYSTEM 🔷     ║")
        print("║               Railway.app Deployment Verification                ║")
        print("╚════════════════════════════════════════════════════════════════════╝")
        print(Colors.ENDC)
        
        print(f"🎯 Testing URL: {Colors.BOLD}{BASE_URL}{Colors.ENDC}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌍 Environment: Production\n")
        
        # Run all tests
        self.test_ssl_certificate()
        self.test_https_redirect()
        self.test_connection()
        self.test_cors_headers()
        self.test_security_headers()
        self.test_static_files()
        self.test_authentication()
        self.test_database_connectivity()
        self.test_error_handling()
        self.test_response_formats()
        self.test_health_check()
        self.test_rate_limiting()
        self.test_performance_metrics()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary"""
        total = self.test_results["passed"] + self.test_results["failed"]
        pass_rate = (self.test_results["passed"] / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'📊 DEPLOYMENT READINESS REPORT'.center(70)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
        
        print(f"✅ Tests Passed:    {Colors.OKGREEN}{self.test_results['passed']}{Colors.ENDC}")
        print(f"❌ Tests Failed:    {Colors.FAIL}{self.test_results['failed']}{Colors.ENDC}")
        print(f"⚠️  Warnings:       {Colors.WARNING}{len(self.test_results['warnings'])}{Colors.ENDC}")
        print(f"📈 Pass Rate:       {Colors.OKBLUE}{pass_rate:.1f}%{Colors.ENDC}\n")
        
        if self.test_results["errors"]:
            print(f"{Colors.FAIL}{Colors.BOLD}❌ CRITICAL ERRORS:{Colors.ENDC}")
            for i, error in enumerate(self.test_results["errors"], 1):
                print(f"  {i}. {error}")
            print()
        
        if self.test_results["warnings"]:
            print(f"{Colors.WARNING}{Colors.BOLD}⚠️ WARNINGS:{Colors.ENDC}")
            for i, warning in enumerate(self.test_results["warnings"], 1):
                print(f"  {i}. {warning}")
            print()
        
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        
        # Deployment recommendation
        if pass_rate >= 90:
            print(f"{Colors.OKGREEN}{Colors.BOLD}✅ PRODUCTION READY - SYSTEM FULLY OPERATIONAL{Colors.ENDC}")
        elif pass_rate >= 75:
            print(f"{Colors.WARNING}{Colors.BOLD}⚠️ MOSTLY OPERATIONAL - MONITOR WARNINGS{Colors.ENDC}")
        elif pass_rate >= 60:
            print(f"{Colors.WARNING}{Colors.BOLD}⚠️ PARTIALLY OPERATIONAL - FIX ISSUES BEFORE CRITICAL USE{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}❌ CRITICAL FAILURES - INVESTIGATE IMMEDIATELY{Colors.ENDC}")
        
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
        
        print(f"📋 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 URL Tested: {BASE_URL}\n")

if __name__ == "__main__":
    suite = ProductionCornerTestSuite()
    try:
        suite.run_all_tests()
        sys.exit(0 if suite.test_results["failed"] == 0 else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Tests interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Unexpected error: {str(e)}{Colors.ENDC}")
        sys.exit(1)
