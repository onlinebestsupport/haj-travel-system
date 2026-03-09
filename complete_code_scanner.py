#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Code Quality Scanner - Checks all files for errors
Run: python complete_code_scanner.py
"""

import os
import re
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

class CodeScanner:
    def __init__(self):
        self.results = {
            'total_files': 0,
            'issues': {
                'critical': [],
                'high': [],
                'medium': [],
                'low': [],
                'warnings': []
            },
            'file_types': {
                '.py': {'count': 0, 'issues': 0},
                '.html': {'count': 0, 'issues': 0},
                '.js': {'count': 0, 'issues': 0},
                '.css': {'count': 0, 'issues': 0},
                '.json': {'count': 0, 'issues': 0},
                'other': {'count': 0, 'issues': 0}
            }
        }
        self.start_time = datetime.now()

    def print_header(self, text):
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")

    def add_issue(self, severity, filepath, message, line=None):
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
        
        location = f":{line}" if line else ""
        issue_msg = f"{filepath}{location} - {message}"
        
        self.results['issues'][severity].append(issue_msg)
        
        # Update file type stats
        ext = os.path.splitext(filepath)[1].lower()
        if ext in self.results['file_types']:
            self.results['file_types'][ext]['issues'] += 1
        else:
            self.results['file_types']['other']['issues'] += 1
        
        print(f"{color_map[severity]}{icon_map[severity]} {issue_msg}{Colors.ENDC}")

    def scan_python_file(self, filepath):
        """Scan Python file for errors"""
        issues = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Check for syntax errors by compiling
            try:
                compile(content, filepath, 'exec')
            except SyntaxError as e:
                self.add_issue('critical', filepath, f"Syntax error: {e}", e.lineno)
                issues += 1
            
            # Check for common issues
            for i, line in enumerate(lines, 1):
                # Print statements without parentheses (Python 2 vs 3)
                if re.match(r'^\s*print\s+["\']', line) and 'print(' not in line:
                    self.add_issue('high', filepath, 'Print statement without parentheses', i)
                    issues += 1
                
                # TODO/FIXME comments
                if 'TODO' in line or 'FIXME' in line:
                    self.add_issue('warnings', filepath, 'TODO/FIXME comment', i)
                
                # Line too long (PEP 8: max 79 chars, warning at 80+)
                if len(line) > 100:
                    self.add_issue('low', filepath, f'Line too long ({len(line)} chars)', i)
                    issues += 1
            
            return issues
        except Exception as e:
            print(f"Error scanning {filepath}: {e}")
            return issues

    def scan_html_file(self, filepath):
        """Scan HTML file for errors"""
        issues = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for DOCTYPE
            if '<!DOCTYPE' not in content and '<!doctype' not in content:
                self.add_issue('high', filepath, 'Missing DOCTYPE declaration')
                issues += 1
            
            # Check for html tag
            if '<html' not in content.lower():
                self.add_issue('high', filepath, 'Missing <html> tag')
                issues += 1
            
            # Check for head section
            if '<head' not in content.lower():
                self.add_issue('medium', filepath, 'Missing <head> section')
                issues += 1
            
            # Check for body tag
            if '<body' not in content.lower():
                self.add_issue('high', filepath, 'Missing <body> tag')
                issues += 1
            
            return issues
        except Exception as e:
            print(f"Error scanning {filepath}: {e}")
            return issues

    def scan_js_file(self, filepath):
        """Scan JavaScript file for common errors"""
        issues = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                # Undefined variables pattern
                if re.search(r'if\s+\(\s*\w+\s*[!=<>]+', line):
                    # Simple check - could be improved
                    pass
                
                # Line length check
                if len(line) > 100:
                    self.add_issue('low', filepath, f'Line too long ({len(line)} chars)', i)
                    issues += 1
            
            return issues
        except Exception as e:
            print(f"Error scanning {filepath}: {e}")
            return issues

    def run(self):
        """Run the complete scan"""
        self.print_header("📊 COMPLETE CODE QUALITY SCAN")
        
        # Scan all files
        for root, dirs, files in os.walk('.'):
            # Skip backup and venv directories
            dirs[:] = [d for d in dirs if d not in ['backup', 'venv', '.venv', '__pycache__', '.git', 'node_modules']]
            
            for file in files:
                filepath = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                # Track file types
                if ext in self.results['file_types']:
                    self.results['file_types'][ext]['count'] += 1
                else:
                    self.results['file_types']['other']['count'] += 1
                
                self.results['total_files'] += 1
                
                # Scan based on file type
                if ext == '.py':
                    self.scan_python_file(filepath)
                elif ext == '.html':
                    self.scan_html_file(filepath)
                elif ext == '.js':
                    self.scan_js_file(filepath)
        
        # Print summary
        self.print_header("📊 SCAN SUMMARY")
        
        print(f"\n{Colors.BOLD}📁 Files Scanned: {self.results['total_files']}{Colors.ENDC}")
        print(f"{Colors.BOLD}⏱️  Time: {(datetime.now() - self.start_time).total_seconds():.2f} seconds{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}File Type Breakdown:{Colors.ENDC}")
        total_issues = sum(sum(issues) for issues in 
                          [self.results['issues'][sev] for sev in self.results['issues']])
        
        for ext, data in self.results['file_types'].items():
            if data['count'] > 0:
                print(f"  {ext:6} : {data['count']:3} files, {data['issues']:3} issues")
        
        print(f"\n{Colors.BOLD}📊 Issues Found: {total_issues}{Colors.ENDC}\n")
        
        # Print issues by severity
        for sev in ['critical', 'high', 'medium', 'low', 'warnings']:
            issues = self.results['issues'][sev]
            if issues:
                if sev == 'critical':
                    print(f"{Colors.FAIL}❌ CRITICAL: {len(issues)} issues{Colors.ENDC}")
                elif sev == 'high':
                    print(f"{Colors.WARNING}⚠️ HIGH: {len(issues)} issues{Colors.ENDC}")
                elif sev == 'medium':
                    print(f"{Colors.OKCYAN}🔍 MEDIUM: {len(issues)} issues{Colors.ENDC}")
                elif sev == 'low':
                    print(f"{Colors.OKBLUE}🔍 LOW: {len(issues)} issues{Colors.ENDC}")
                else:
                    print(f"{Colors.WARNING}⚠️ WARNINGS: {len(issues)} issues{Colors.ENDC}")
                
                for issue in issues[:5]:
                    print(f"     • {issue}")
                
                if len(issues) > 5:
                    print(f"     ... and {len(issues) - 5} more")
                print()

if __name__ == '__main__':
    scanner = CodeScanner()
    scanner.run()
