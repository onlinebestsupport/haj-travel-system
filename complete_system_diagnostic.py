#!/usr/bin/env python3
"""
COMPLETE SYSTEM DIAGNOSTIC - Finds all errors, mismatches, and conflicts
Run: python complete_system_diagnostic.py
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

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

class SystemDiagnostic:
    def __init__(self):
        self.issues = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'warnings': []
        }
        self.stats = {
            'files_checked': 0,
            'issues_found': 0
        }

    def print_header(self, text):
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")

    def print_issue(self, severity, message, details=""):
        color_map = {
            'critical': Colors.FAIL,
            'high': Colors.WARNING,
            'medium': Colors.OKCYAN,
            'low': Colors.OKBLUE,
            'warnings': Colors.WARNING
        }
        
        icon_map = {
            'critical': '❌',
            'high': '⚠️',
            'medium': '🔍',
            'low': 'ℹ️',
            'warnings': '⚠️'
        }
        
        print(f"{color_map[severity]}{icon_map[severity]} {message}{Colors.ENDC}")
        if details:
            print(f"   └─ {Colors.OKCYAN}{details}{Colors.ENDC}")
        
        self.issues[severity].append(f"{message}: {details}")
        self.stats['issues_found'] += 1

    def check_merge_conflicts(self):
        """Check all files for merge conflict markers"""
        self.print_header("🔍 CHECKING FOR MERGE CONFLICT MARKERS")
        
        conflict_patterns = [
            r'',
            r'',
            r'>>>>>>> [a-f0-9]+'
        ]
        
        for root, dirs, files in os.walk('.'):
            if 'venv' in root or '__pycache__' in root or '.git' in root:
                continue
            
            for file in files:
                if file.endswith(('.py', '.html', '.js', '.css', '.json', '.txt', '.md')):
                    filepath = os.path.join(root, file)
                    self.stats['files_checked'] += 1
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for pattern in conflict_patterns:
                            if re.search(pattern, content):
                                self.print_issue(
                                    'critical',
                                    f"Merge conflict found in {filepath}",
                                    f"Contains {pattern}"
                                )
                                break
                    except Exception as e:
                        pass

    def check_file_permissions(self):
        """Check for incorrect file permissions"""
        self.print_header("🔐 CHECKING FILE PERMISSIONS")
        
        for root, dirs, files in os.walk('.'):
            if 'venv' in root or '__pycache__' in root or '.git' in root:
                continue
            
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    # Check if file is readable
                    with open(filepath, 'r') as f:
                        f.read(1)
                except PermissionError:
                    self.print_issue('high', f"Permission denied: {filepath}", "File cannot be read")
                except Exception:
                    pass

    def check_import_errors(self):
        """Check Python files for import errors"""
        self.print_header("📦 CHECKING IMPORT ERRORS")
        
        for root, dirs, files in os.walk('app'):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        result = subprocess.run(
                            ['python', '-m', 'py_compile', filepath],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode != 0:
                            self.print_issue('high', f"Import error in {filepath}", result.stderr)
                    except Exception as e:
                        self.print_issue('medium', f"Could not check {filepath}", str(e))

    def check_syntax_errors(self):
        """Check Python files for syntax errors"""
        self.print_header("🔧 CHECKING SYNTAX ERRORS")
        
        for root, dirs, files in os.walk('.'):
            if 'venv' in root or '__pycache__' in root:
                continue
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            compile(f.read(), filepath, 'exec')
                    except SyntaxError as e:
                        self.print_issue('critical', f"Syntax error in {filepath}", str(e))
                    except Exception:
                        pass

    def check_css_paths(self):
        """Check CSS paths in HTML files"""
        self.print_header("🎨 CHECKING CSS PATH MISMATCHES")
        
        css_files = set()
        for root, dirs, files in os.walk('public'):
            for file in files:
                if file.endswith('.css'):
                    rel_path = os.path.relpath(os.path.join(root, file), 'public').replace('\\', '/')
                    css_files.add(rel_path)
        
        print(f"Found CSS files: {sorted(css_files)}")
        
        # Check HTML files for correct CSS references
        for root, dirs, files in os.walk('public'):
            for file in files:
                if file.endswith('.html'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Find all CSS references
                        css_refs = re.findall(r'href=[\'"]([^\'"]+\.css)[\'"]', content)
                        
                        for ref in css_refs:
                            if ref.startswith('/'):
                                expected = ref[1:]  # Remove leading /
                            else:
                                expected = ref
                            
                            if expected not in css_files and 'http' not in ref:
                                self.print_issue(
                                    'medium',
                                    f"CSS path mismatch in {filepath}",
                                    f"References '{ref}' but file not found"
                                )
                    except Exception as e:
                        pass

    def check_api_endpoints(self):
        """Check for API endpoint inconsistencies"""
        self.print_header("🌐 CHECKING API ENDPOINTS")
        
        # Find all Flask routes
        route_pattern = r'@(app|bp)\.route\([\'"]([^\'"]+)[\'"]'
        endpoints = set()
        
        for root, dirs, files in os.walk('app'):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            matches = re.findall(route_pattern, content)
                            for match in matches:
                                endpoints.add(match[1])
                    except Exception:
                        pass
        
        print(f"Found {len(endpoints)} API endpoints")
        
        # Check if frontend HTML files reference these endpoints
        missing_endpoints = set()
        for root, dirs, files in os.walk('public'):
            for file in files:
                if file.endswith('.html'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # Find API calls in JavaScript
                            api_calls = re.findall(r'[\'"](/api/[^\'"]+)[\'"]', content)
                            for call in api_calls:
                                if call not in endpoints and '/api/' in call:
                                    missing_endpoints.add(call)
                    except Exception:
                        pass
        
        for endpoint in missing_endpoints:
            self.print_issue(
                'high',
                f"API endpoint referenced but not found",
                f"Frontend calls '{endpoint}' but no route defined"
            )

    def check_missing_files(self):
        """Check for files that should exist but don't"""
        self.print_header("📁 CHECKING MISSING FILES")
        
        expected_files = [
            'app/__init__.py',
            'app/server.py',
            'app/database.py',
            'app/routes/__init__.py',
            'app/routes/auth.py',
            'app/routes/admin.py',
            'app/routes/travelers.py',
            'app/routes/batches.py',
            'app/routes/payments.py',
            'app/routes/invoices.py',
            'app/routes/receipts.py',
            'app/routes/reports.py',
            'requirements.txt',
            'Procfile',
            'railway.json',
            'public/index.html',
            'public/admin/login.html',
            'public/admin/dashboard.html',
            'public/admin/travelers.html',
            'public/admin/batches.html',
            'public/admin/payments.html',
            'public/admin/invoices.html',
            'public/admin/receipts.html',
            'public/admin/users.html',
            'public/admin/reports.html',
            'public/admin/whatsapp.html',
            'public/admin/email.html',
            'public/admin/backup.html',
            'public/style.css',
            'public/admin/admin-style.css'
        ]
        
        for expected in expected_files:
            if not os.path.exists(expected):
                self.print_issue('medium', f"Missing file: {expected}", "This file should exist")

    def check_database_consistency(self):
        """Check database table consistency with code"""
        self.print_header("🗄️  CHECKING DATABASE CONSISTENCY")
        
        # Try to connect to database via Railway CLI
        try:
            result = subprocess.run(
                ['railway', 'connect', 'Postgres', '-c', "\\dt"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout
                tables = re.findall(r'public \| (\w+)', output)
                print(f"Database tables found: {tables}")
                
                # Check if tables referenced in code exist
                py_files_with_tables = set()
                for root, dirs, files in os.walk('app'):
                    for file in files:
                        if file.endswith('.py'):
                            filepath = os.path.join(root, file)
                            try:
                                with open(filepath, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    for table in tables:
                                        if table in content:
                                            py_files_with_tables.add(table)
                            except Exception:
                                pass
            else:
                self.print_issue('warnings', "Could not connect to database", "Run from project directory")
                
        except Exception as e:
            self.print_issue('warnings', "Database check skipped", str(e))

    def check_environment_variables(self):
        """Check for required environment variables"""
        self.print_header("🔑 CHECKING ENVIRONMENT VARIABLES")
        
        try:
            result = subprocess.run(
                ['railway', 'variables'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout
                required_vars = ['DATABASE_URL', 'SECRET_KEY']
                for var in required_vars:
                    if var not in output:
                        self.print_issue('critical', f"Missing environment variable: {var}", "Required for application")
            else:
                self.print_issue('warnings', "Could not fetch environment variables", "Run 'railway link' first")
                
        except Exception as e:
            self.print_issue('warnings', "Environment check skipped", str(e))

    def check_git_status(self):
        """Check git status for uncommitted changes"""
        self.print_header("📦 CHECKING GIT STATUS")
        
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                modified = len([l for l in result.stdout.split('\n') if l])
                self.print_issue(
                    'low',
                    f"Uncommitted changes: {modified} files",
                    "Run 'git status' to see details"
                )
            else:
                print(f"{Colors.OKGREEN}✅ Working directory clean{Colors.ENDC}")
                
        except Exception as e:
            self.print_issue('warnings', "Git check failed", str(e))

    def run_diagnostic(self):
        """Run all diagnostic checks"""
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}")
        print("╔" + "═"*78 + "╗")
        print("║     🔍 COMPLETE SYSTEM DIAGNOSTIC TOOL 🔍               ║")
        print("║     Finding all errors, mismatches, and conflicts       ║")
        print("╚" + "═"*78 + "╝")
        print(Colors.ENDC)
        
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Run all checks
        self.check_merge_conflicts()
        self.check_file_permissions()
        self.check_syntax_errors()
        self.check_import_errors()
        self.check_css_paths()
        self.check_api_endpoints()
        self.check_missing_files()
        self.check_database_consistency()
        self.check_environment_variables()
        self.check_git_status()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print diagnostic summary"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}📊 DIAGNOSTIC SUMMARY{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
        
        print(f"📁 Files checked: {self.stats['files_checked']}")
        print(f"🔍 Issues found: {self.stats['issues_found']}\n")
        
        if self.issues['critical']:
            print(f"{Colors.FAIL}{Colors.BOLD}❌ CRITICAL ISSUES ({len(self.issues['critical'])}):{Colors.ENDC}")
            for issue in self.issues['critical'][:5]:
                print(f"   • {issue}")
            if len(self.issues['critical']) > 5:
                print(f"   ... and {len(self.issues['critical'])-5} more")
            print()
        
        if self.issues['high']:
            print(f"{Colors.WARNING}{Colors.BOLD}⚠️ HIGH PRIORITY ({len(self.issues['high'])}):{Colors.ENDC}")
            for issue in self.issues['high'][:5]:
                print(f"   • {issue}")
            if len(self.issues['high']) > 5:
                print(f"   ... and {len(self.issues['high'])-5} more")
            print()
        
        if self.issues['medium']:
            print(f"{Colors.OKCYAN}{Colors.BOLD}🔍 MEDIUM PRIORITY ({len(self.issues['medium'])}):{Colors.ENDC}")
            for issue in self.issues['medium'][:5]:
                print(f"   • {issue}")
            if len(self.issues['medium']) > 5:
                print(f"   ... and {len(self.issues['medium'])-5} more")
            print()
        
        if self.issues['warnings']:
            print(f"{Colors.WARNING}{Colors.BOLD}⚠️ WARNINGS ({len(self.issues['warnings'])}):{Colors.ENDC}")
            for issue in self.issues['warnings'][:5]:
                print(f"   • {issue}")
            if len(self.issues['warnings']) > 5:
                print(f"   ... and {len(self.issues['warnings'])-5} more")
            print()
        
        # Overall health score
        total_issues = len(self.issues['critical']) * 10 + len(self.issues['high']) * 5 + len(self.issues['medium']) * 2 + len(self.issues['warnings'])
        health_score = max(0, 100 - total_issues)
        
        print(f"{Colors.BOLD}System Health Score: ", end="")
        if health_score >= 90:
            print(f"{Colors.OKGREEN}{health_score}% - EXCELLENT{Colors.ENDC}")
        elif health_score >= 70:
            print(f"{Colors.OKCYAN}{health_score}% - GOOD{Colors.ENDC}")
        elif health_score >= 50:
            print(f"{Colors.WARNING}{health_score}% - FAIR{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}{health_score}% - POOR{Colors.ENDC}")
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")

if __name__ == "__main__":
    diagnostic = SystemDiagnostic()
    try:
        diagnostic.run_diagnostic()
        sys.exit(0 if diagnostic.stats['issues_found'] == 0 else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Diagnostic interrupted by user{Colors.ENDC}")
        sys.exit(1)
