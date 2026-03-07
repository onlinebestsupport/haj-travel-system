#!/usr/bin/env python3
"""
🚀 DEPLOYMENT VERIFICATION SCRIPT
Complete production readiness checks
Run: python verify_deployment.py
"""

import requests
import json
import subprocess
import os
import sys
from datetime import datetime
import time

BASE_URL = "https://haj-web-app-production.up.railway.app"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class DeploymentVerifier:
    def __init__(self):
        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'errors': []
        }
        self.session = requests.Session()
    
    def print_header(self, text):
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    def print_check(self, name, passed, details=""):
        status = f"{Colors.OKGREEN}✅ PASS{Colors.ENDC}" if passed else f"{Colors.FAIL}❌ FAIL{Colors.ENDC}"
        print(f"{status} | {name}")
        if details:
            print(f"   └─ {Colors.OKCYAN}{details}{Colors.ENDC}")
        
        if passed:
            self.results['passed'] += 1
        else:
            self.results['failed'] += 1
            self.results['errors'].append(f"{name}: {details}")
    
    def check_git_status(self):
        """Check git status"""
        self.print_header("📦 GIT STATUS")
        
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
            if result.returncode == 0:
                if result.stdout.strip():
                    self.print_check("Git clean", False, f"Uncommitted changes: {len(result.stdout.splitlines())}")
                else:
                    self.print_check("Git clean", True, "No uncommitted changes")
            else:
                self.print_check("Git status", False, "Git not found")
        except Exception as e:
            self.print_check("Git status", False, str(e))
    
    def check_environment(self):
        """Check environment variables"""
        self.print_header("🌍 ENVIRONMENT VARIABLES")
        
        required_vars = ['DATABASE_URL', 'SECRET_KEY', 'FLASK_ENV']
        
        for var in required_vars:
            value = os.getenv(var)
            if value:
                masked = value[:20] + "..." if len(value) > 20 else value
                self.print_check(f"ENV: {var}", True, f"Set to: {masked}")
            else:
                self.print_check(f"ENV: {var}", False, "Not set")
    
    def check_files_exist(self):
        """Check required files exist"""
        self.print_header("📁 FILE STRUCTURE")
        
        required_files = [
            'app/server.py',
            'app/database.py',
            'app/routes/__init__.py',
            'app/routes/auth.py',
            'requirements.txt',
            'Procfile',
            '.env.example',
        ]
        
        for filepath in required_files:
            exists = os.path.exists(filepath)
            self.print_check(f"File: {filepath}", exists)
    
    def check_connectivity(self):
        """Check server connectivity"""
        self.print_header("🌐 SERVER CONNECTIVITY")
        
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.print_check("Health endpoint", True, f"Status: {data.get('status', 'unknown')}")
            else:
                self.print_check("Health endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_check("Server connection", False, str(e))
    
    def check_api_endpoints(self):
        """Check API endpoints"""
        self.print_header("🔌 API ENDPOINTS")
        
        endpoints = [
            ('GET', '/health', 'Health check'),
            ('GET', '/api/batches', 'Batches (requires auth)'),
            ('POST', '/api/auth/login', 'Login endpoint'),
        ]
        
        for method, endpoint, name in endpoints:
            try:
                url = f"{BASE_URL}{endpoint}"
                if method == 'GET':
                    response = requests.get(url, timeout=10)
                else:
                    response = requests.post(url, json={}, timeout=10)
                
                passed = response.status_code in [200, 400, 401, 405]
                details = f"HTTP {response.status_code}"
                self.print_check(name, passed, details)
            except Exception as e:
                self.print_check(name, False, str(e))
    
    def check_security(self):
        """Check security headers"""
        self.print_header("🛡️ SECURITY HEADERS")
        
        headers_to_check = {
            'X-Frame-Options': 'Clickjacking protection',
            'X-Content-Type-Options': 'MIME sniffing protection',
            'Strict-Transport-Security': 'HSTS',
        }
        
        try:
            response = requests.get(BASE_URL, timeout=10)
            for header, purpose in headers_to_check.items():
                present = header in response.headers
                details = response.headers.get(header, 'Not set')[:40]
                self.print_check(f"Header: {header}", present, details)
        except Exception as e:
            self.print_check("Security check", False, str(e))
    
    def check_dependencies(self):
        """Check Python dependencies"""
        self.print_header("📚 DEPENDENCIES")
        
        required_packages = ['flask', 'psycopg2', 'flask-cors', 'python-dotenv']
        
        try:
            import pkg_resources
            installed = {pkg.key for pkg in pkg_resources.working_set}
            
            for package in required_packages:
                is_installed = package.lower().replace('-', '_') in installed or package in installed
                self.print_check(f"Package: {package}", is_installed)
        except Exception as e:
            self.print_check("Dependency check", False, str(e))
    
    def generate_report(self):
        """Generate final report"""
        total = self.results['passed'] + self.results['failed']
        pass_rate = (self.results['passed'] / total * 100) if total > 0 else 0
        
        self.print_header("📊 DEPLOYMENT VERIFICATION REPORT")
        
        print(f"✅ Passed:  {Colors.OKGREEN}{self.results['passed']}{Colors.ENDC}")
        print(f"❌ Failed:  {Colors.FAIL}{self.results['failed']}{Colors.ENDC}")
        print(f"📈 Rate:    {Colors.OKBLUE}{pass_rate:.1f}%{Colors.ENDC}\n")
        
        if self.results['errors']:
            print(f"{Colors.FAIL}❌ ISSUES:{Colors.ENDC}")
            for error in self.results['errors']:
                print(f"  • {error}")
            print()
        
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        
        if pass_rate >= 90:
            print(f"{Colors.OKGREEN}{Colors.BOLD}✅ DEPLOYMENT VERIFIED - SYSTEM READY{Colors.ENDC}")
        elif pass_rate >= 70:
            print(f"{Colors.WARNING}{Colors.BOLD}⚠️ MOSTLY READY - ADDRESS ISSUES{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}❌ CRITICAL ISSUES DETECTED{Colors.ENDC}")
        
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    def run(self):
        """Run all verification checks"""
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}")
        print("╔══════════════════════════════════════════════════════════════════╗")
        print("║          🚀 DEPLOYMENT VERIFICATION SCRIPT 🚀                    ║")
        print("║                Production Readiness Check                        ║")
        print("╚═════════════════════════════════════════════════════���════════════╝")
        print(Colors.ENDC)
        
        print(f"🎯 Target: {Colors.BOLD}{BASE_URL}{Colors.ENDC}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        self.check_git_status()
        self.check_environment()
        self.check_files_exist()
        self.check_dependencies()
        self.check_connectivity()
        self.check_api_endpoints()
        self.check_security()
        
        self.generate_report()

if __name__ == "__main__":
    verifier = DeploymentVerifier()
    try:
        verifier.run()
        sys.exit(0 if verifier.results['failed'] == 0 else 1)
    except Exception as e:
        print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}")
        sys.exit(1)