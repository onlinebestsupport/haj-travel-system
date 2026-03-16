#!/usr/bin/env python
"""
Complete Structure Checker for Haj Travel System
Checks all files, imports, routes, and potential issues
"""

import os
import ast
import sys
from pathlib import Path
from datetime import datetime

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

class StructureChecker:
    def __init__(self, project_path='.'):
        self.project_path = Path(project_path)
        self.structure = {
            'directories': [],
            'python_files': [],
            'html_files': [],
            'js_files': [],
            'css_files': [],
            'other_files': []
        }
        self.issues = []
        self.imports_map = {}
        self.route_map = {}
        
    def print_header(self, text):
        print(f"\n{Colors.HEADER}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text:^80}{Colors.END}")
        print(f"{Colors.HEADER}{'='*80}{Colors.END}\n")

    def scan_directory(self):
        """Scan entire project directory structure"""
        self.print_header("📁 PROJECT STRUCTURE SCAN")
        
        for root, dirs, files in os.walk(self.project_path):
            # Skip virtual environments and hidden directories
            if any(skip in root for skip in ['venv', 'env', '.git', '__pycache__', 'backup']):
                continue
            
            rel_root = os.path.relpath(root, self.project_path)
            if rel_root == '.':
                rel_root = 'root'
            
            dir_count = 0
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.project_path)
                
                if file.endswith('.py'):
                    self.structure['python_files'].append(rel_path)
                elif file.endswith('.html'):
                    self.structure['html_files'].append(rel_path)
                elif file.endswith('.js'):
                    self.structure['js_files'].append(rel_path)
                elif file.endswith('.css'):
                    self.structure['css_files'].append(rel_path)
                else:
                    self.structure['other_files'].append(rel_path)
            
            if dirs or files:
                self.structure['directories'].append(rel_root)
        
        # Print summary
        print(f"\n{Colors.BOLD}Directory Structure:{Colors.END}")
        for d in sorted(self.structure['directories']):
            print(f"  📁 {d}")
        
        print(f"\n{Colors.BOLD}File Counts:{Colors.END}")
        print(f"  🐍 Python files: {len(self.structure['python_files'])}")
        print(f"  🌐 HTML files: {len(self.structure['html_files'])}")
        print(f"  📜 JS files: {len(self.structure['js_files'])}")
        print(f"  🎨 CSS files: {len(self.structure['css_files'])}")
        print(f"  📄 Other files: {len(self.structure['other_files'])}")
        print(f"\n{Colors.GREEN}✅ Total files: {sum(len(v) for v in self.structure.values() if isinstance(v, list))}{Colors.END}")

    def check_imports(self):
        """Check imports in all Python files"""
        self.print_header("🔍 IMPORT ANALYSIS")
        
        for py_file in self.structure['python_files']:
            full_path = os.path.join(self.project_path, py_file)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                imports = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ''
                        for alias in node.names:
                            imports.append(f"{module}.{alias.name}")
                
                self.imports_map[py_file] = imports
                
                # Check for common missing imports
                if 'release_db' in content and 'release_db' not in str(imports):
                    if 'from app.database import release_db' not in content:
                        self.issues.append({
                            'file': py_file,
                            'type': 'MISSING_IMPORT',
                            'message': 'release_db used but not imported',
                            'fix': 'Add: from app.database import release_db'
                        })
                
                if 'get_db' in content and 'get_db' not in str(imports):
                    if 'from app.database import get_db' not in content:
                        self.issues.append({
                            'file': py_file,
                            'type': 'MISSING_IMPORT',
                            'message': 'get_db used but not imported',
                            'fix': 'Add: from app.database import get_db'
                        })
                
            except Exception as e:
                self.issues.append({
                    'file': py_file,
                    'type': 'PARSE_ERROR',
                    'message': f"Error parsing file: {str(e)}"
                })
        
        # Print import summary
        print(f"\n{Colors.BOLD}Import Analysis by File:{Colors.END}")
        for py_file, imports in sorted(self.imports_map.items()):
            if imports:
                print(f"\n  📄 {py_file}")
                for imp in imports[:5]:  # Show first 5 imports
                    print(f"    📥 {imp}")
                if len(imports) > 5:
                    print(f"    ... and {len(imports)-5} more")

    def check_routes(self):
        """Extract and analyze Flask routes"""
        self.print_header("🛣️  ROUTE ANALYSIS")
        
        route_patterns = ['@app.route', '@bp.route']
        all_routes = []
        
        for py_file in self.structure['python_files']:
            full_path = os.path.join(self.project_path, py_file)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                file_routes = []
                for i, line in enumerate(lines, 1):
                    for pattern in route_patterns:
                        if pattern in line:
                            # Extract the route
                            route_start = line.find("'")
                            if route_start == -1:
                                route_start = line.find('"')
                            if route_start != -1:
                                route_end = line.find("'", route_start + 1)
                                if route_end == -1:
                                    route_end = line.find('"', route_start + 1)
                                if route_end != -1:
                                    route = line[route_start+1:route_end]
                                    file_routes.append({
                                        'route': route,
                                        'line': i,
                                        'file': py_file
                                    })
                                    all_routes.append({
                                        'route': route,
                                        'file': py_file,
                                        'line': i
                                    })
                
                if file_routes:
                    self.route_map[py_file] = file_routes
                    
            except Exception as e:
                pass
        
        # Print route summary
        print(f"\n{Colors.BOLD}Routes by File:{Colors.END}")
        for py_file, routes in sorted(self.route_map.items()):
            if routes:
                print(f"\n  📄 {py_file}")
                for route in routes[:5]:
                    print(f"    🛣️  {route['route']} (line {route['line']})")
                if len(routes) > 5:
                    print(f"    ... and {len(routes)-5} more")
        
        print(f"\n{Colors.GREEN}✅ Total routes found: {len(all_routes)}{Colors.END}")

    def check_database_helpers(self):
        """Check database helper usage"""
        self.print_header("🗄️  DATABASE HELPER ANALYSIS")
        
        db_issues = []
        for py_file in self.structure['python_files']:
            full_path = os.path.join(self.project_path, py_file)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                # Check for get_db() without release_db()
                if 'get_db()' in content:
                    has_release = 'release_db' in content
                    has_finally = 'finally:' in content
                    
                    if not has_release and not has_finally:
                        db_issues.append({
                            'file': py_file,
                            'issue': 'get_db() used but no release_db or finally block found',
                            'severity': 'HIGH'
                        })
                
                # Check for direct cursor.close() without release_db
                if 'cursor.close()' in content and 'release_db' not in content:
                    if 'app/database.py' not in py_file:  # Skip database.py itself
                        db_issues.append({
                            'file': py_file,
                            'issue': 'Using cursor.close() directly - consider using release_db',
                            'severity': 'MEDIUM'
                        })
                        
            except Exception as e:
                pass
        
        if db_issues:
            print(f"\n{Colors.RED}Database Issues Found:{Colors.END}")
            for issue in db_issues:
                severity_color = Colors.RED if issue['severity'] == 'HIGH' else Colors.YELLOW
                print(f"  {severity_color}{issue['severity']}{Colors.END}: {issue['file']}")
                print(f"    {issue['issue']}")
        else:
            print(f"\n{Colors.GREEN}✅ No database helper issues found{Colors.END}")

    def check_templates(self):
        """Check HTML templates for common issues"""
        self.print_header("📄 TEMPLATE ANALYSIS")
        
        template_issues = []
        for html_file in self.structure['html_files']:
            full_path = os.path.join(self.project_path, html_file)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for session manager
                if 'session-manager.js' not in content:
                    template_issues.append({
                        'file': html_file,
                        'issue': 'Missing session-manager.js',
                        'fix': 'Add <script src="/admin/js/session-manager.js"></script> in head'
                    })
                
                # Check for logout function
                if 'logout()' not in content:
                    template_issues.append({
                        'file': html_file,
                        'issue': 'Missing logout function',
                        'fix': 'Add logout button/function'
                    })
                
                # Check for CSRF token (if used)
                if 'csrf_token' in content and '{{ csrf_token() }}' not in content:
                    if '{% csrf_token %}' not in content:
                        template_issues.append({
                            'file': html_file,
                            'issue': 'CSRF token mentioned but not implemented',
                            'fix': 'Add {{ csrf_token() }} in forms'
                        })
                        
            except Exception as e:
                pass
        
        if template_issues:
            print(f"\n{Colors.YELLOW}Template Issues:{Colors.END}")
            for issue in template_issues[:10]:
                print(f"  📄 {issue['file']}")
                print(f"    ⚠️  {issue['issue']}")
                print(f"    ✅ Fix: {issue['fix']}")
        else:
            print(f"\n{Colors.GREEN}✅ No template issues found{Colors.END}")

    def check_api_endpoints(self):
        """Check if all expected API endpoints exist"""
        self.print_header("🌐 API ENDPOINT CHECK")
        
        expected_endpoints = [
            '/api/login',
            '/api/logout',
            '/api/check-session',
            '/api/travelers',
            '/api/batches',
            '/api/payments',
            '/api/invoices',
            '/api/receipts',
            '/api/users',
            '/api/admin/users',
            '/api/backup/settings',
            '/api/company/settings',
            '/api/uploads',
            '/api/reports/summary'
        ]
        
        found_endpoints = []
        for py_file, routes in self.route_map.items():
            for route in routes:
                found_endpoints.append(route['route'])
        
        missing = []
        for expected in expected_endpoints:
            found = False
            for endpoint in found_endpoints:
                if expected in endpoint:
                    found = True
                    break
            if not found:
                missing.append(expected)
        
        if missing:
            print(f"\n{Colors.YELLOW}Missing Expected Endpoints:{Colors.END}")
            for m in missing:
                print(f"  ⚠️  {m}")
        else:
            print(f"\n{Colors.GREEN}✅ All expected endpoints found{Colors.END}")

    def generate_report(self):
        """Generate comprehensive report"""
        self.print_header("📊 COMPREHENSIVE STRUCTURE REPORT")
        
        print(f"\n{Colors.BOLD}Project Summary:{Colors.END}")
        print(f"  📁 Project Root: {self.project_path.absolute()}")
        print(f"  🕒 Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n  📊 Statistics:")
        print(f"    • Python Files: {len(self.structure['python_files'])}")
        print(f"    • HTML Files: {len(self.structure['html_files'])}")
        print(f"    • JS Files: {len(self.structure['js_files'])}")
        print(f"    • CSS Files: {len(self.structure['css_files'])}")
        print(f"    • Routes Found: {sum(len(v) for v in self.route_map.values())}")
        print(f"    • Imports Analyzed: {len(self.imports_map)}")
        
        # Issues summary
        if self.issues:
            print(f"\n{Colors.RED}Issues Found: {len(self.issues)}{Colors.END}")
            for issue in self.issues[:5]:
                print(f"  ❌ {issue['file']}: {issue['message']}")
                if 'fix' in issue:
                    print(f"     ✅ {issue['fix']}")
        
        print(f"\n{Colors.GREEN}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}✅ STRUCTURE CHECK COMPLETE{Colors.END}")
        print(f"{Colors.GREEN}{'='*80}{Colors.END}")

    def run_all_checks(self):
        """Run all structure checks"""
        self.scan_directory()
        self.check_imports()
        self.check_routes()
        self.check_database_helpers()
        self.check_templates()
        self.check_api_endpoints()
        self.generate_report()
        
        # Save report to file
        self.save_report()

    def save_report(self):
        """Save report to file"""
        report_file = f"structure_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write("HAJ TRAVEL SYSTEM - STRUCTURE REPORT\n")
            f.write("="*60 + "\n\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Python Files: {len(self.structure['python_files'])}\n")
            f.write(f"HTML Files: {len(self.structure['html_files'])}\n")
            f.write(f"JS Files: {len(self.structure['js_files'])}\n")
            f.write(f"CSS Files: {len(self.structure['css_files'])}\n")
            f.write(f"Routes: {sum(len(v) for v in self.route_map.values())}\n")
            
            if self.issues:
                f.write(f"\nIssues Found: {len(self.issues)}\n")
                for issue in self.issues:
                    f.write(f"- {issue['file']}: {issue['message']}\n")
        
        print(f"\n{Colors.GREEN}✅ Report saved to: {report_file}{Colors.END}")

def main():
    checker = StructureChecker()
    checker.run_all_checks()

if __name__ == "__main__":
    main()