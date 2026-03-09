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
                # Check for print without parentheses (Python 2 style)
                if re.search(r'print\s+[^(]', line) and 'print(' not in line:
                    self.add_issue('high', filepath, "Print statement without parentheses", i)
                    issues += 1
                
                # Check for undefined variables (simple check)
                if '= undefined' in line or '= undefined;' in line:
                    self.add_issue('medium', filepath, "Possible undefined variable", i)
                    issues += 1
                
                # Check for too long lines (> 100 chars)
                if len(line) > 100:
                    self.add_issue('low', filepath, f"Line too long ({len(line)} chars)", i)
                    issues += 1
                
                # Check for TODO comments
                if 'TODO' in line or 'FIXME' in line:
                    self.add_issue('warnings', filepath, "TODO/FIXME comment", i)
                    issues += 1
            
            # Check imports
            import_lines = re.findall(r'^import \w+|^from \w+ import', content, re.MULTILINE)
            if not import_lines and 'Flask' not in content:
                self.add_issue('low', filepath, "No imports found", None)
                issues += 1
            
            return issues
            
        except UnicodeDecodeError:
            self.add_issue('medium', filepath, "Cannot read file (encoding issue)", None)
            return 1
        except Exception as e:
            self.add_issue('high', filepath, f"Error scanning: {e}", None)
            return 1

    def scan_html_file(self, filepath):
        """Scan HTML file for errors"""
        issues = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Check for basic HTML structure
            if '<!DOCTYPE html>' not in content.upper():
                self.add_issue('high', filepath, "Missing DOCTYPE declaration", None)
                issues += 1
            
            if '<html' not in content.lower():
                self.add_issue('high', filepath, "Missing <html> tag", None)
                issues += 1
            
            if '<head>' not in content.lower():
                self.add_issue('medium', filepath, "Missing <head> section", None)
                issues += 1
            
            if '<body>' not in content.lower():
                self.add_issue('medium', filepath, "Missing <body> tag", None)
                issues += 1
            
            # Check for unclosed tags (simple check)
            tags = re.findall(r'<(\w+)[^>]*>', content)
            closing_tags = re.findall(r'</(\w+)>', content)
            
            from collections import Counter
            tag_count = Counter(tags)
            closing_count = Counter(closing_tags)
            
            for tag, count in tag_count.items():
                if tag not in ['br', 'img', 'input', 'meta', 'link']:  # Self-closing tags
                    if closing_count[tag] != count:
                        self.add_issue('medium', filepath, f"Possible unclosed <{tag}> tag", None)
                        issues += 1
            
            # Check for missing alt attributes on images
            img_tags = re.findall(r'<img[^>]+>', content)
            for img in img_tags:
                if 'alt=' not in img:
                    self.add_issue('medium', filepath, "Image missing alt attribute", None)
                    issues += 1
            
            # Check for inline styles
            if 'style="' in content:
                self.add_issue('low', filepath, "Contains inline styles", None)
                issues += 1
            
            return issues
            
        except UnicodeDecodeError:
            self.add_issue('medium', filepath, "Cannot read file (encoding issue)", None)
            return 1
        except Exception as e:
            self.add_issue('high', filepath, f"Error scanning: {e}", None)
            return 1

    def scan_json_file(self, filepath):
        """Scan JSON file for errors"""
        issues = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            import json
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                self.add_issue('critical', filepath, f"Invalid JSON: {e}", None)
                issues += 1
            
            # Check for merge conflict markers
            if '<<<<<<<' in content or '=======' in content or '>>>>>>>' in content:
                self.add_issue('critical', filepath, "Contains merge conflict markers", None)
                issues += 1
            
            return issues
            
        except UnicodeDecodeError:
            self.add_issue('medium', filepath, "Cannot read file (encoding issue)", None)
            return 1
        except Exception as e:
            self.add_issue('high', filepath, f"Error scanning: {e}", None)
            return 1

    def scan_js_file(self, filepath):
        """Scan JavaScript file for errors"""
        issues = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Check for console.log statements
            if 'console.log' in content:
                self.add_issue('low', filepath, "Contains console.log statements", None)
                issues += 1
            
            # Check for missing semicolons (basic check)
            for i, line in enumerate(lines, 1):
                if line.strip() and not line.strip().endswith(';') and not line.strip().endswith('{') and not line.strip().endswith('}') and not line.strip().startswith('//'):
                    if not re.search(r'if|for|while|function|return', line):
                        self.add_issue('low', filepath, "Possible missing semicolon", i)
                        issues += 1
            
            return issues
            
        except UnicodeDecodeError:
            self.add_issue('medium', filepath, "Cannot read file (encoding issue)", None)
            return 1
        except Exception as e:
            self.add_issue('high', filepath, f"Error scanning: {e}", None)
            return 1

    def scan_css_file(self, filepath):
        """Scan CSS file for errors"""
        issues = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for unclosed braces
            open_braces = content.count('{')
            close_braces = content.count('}')
            
            if open_braces != close_braces:
                self.add_issue('high', filepath, f"Unclosed braces: {open_braces} vs {close_braces}", None)
                issues += 1
            
            return issues
            
        except UnicodeDecodeError:
            self.add_issue('medium', filepath, "Cannot read file (encoding issue)", None)
            return 1
        except Exception as e:
            self.add_issue('high', filepath, f"Error scanning: {e}", None)
            return 1

    def scan_file(self, filepath):
        """Scan file based on extension"""
        ext = os.path.splitext(filepath)[1].lower()
        
        # Update stats
        self.results['total_files'] += 1
        if ext in self.results['file_types']:
            self.results['file_types'][ext]['count'] += 1
        else:
            self.results['file_types']['other']['count'] += 1
        
        # Scan based on extension
        if ext == '.py':
            return self.scan_python_file(filepath)
        elif ext == '.html':
            return self.scan_html_file(filepath)
        elif ext == '.json':
            return self.scan_json_file(filepath)
        elif ext == '.js':
            return self.scan_js_file(filepath)
        elif ext == '.css':
            return self.scan_css_file(filepath)
        else:
            # Check important files even without extension
            filename = os.path.basename(filepath)
            important_files = ['Procfile', 'Dockerfile', 'requirements.txt', '.env.example']
            if filename in important_files:
                return self.scan_text_file(filepath)
            return 0

    def scan_text_file(self, filepath):
        """Scan text files (Procfile, requirements.txt, etc.)"""
        issues = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if '<<<<<<<' in content or '=======' in content or '>>>>>>>' in content:
                self.add_issue('critical', filepath, "Contains merge conflict markers", None)
                issues += 1
            
            return issues
            
        except Exception as e:
            self.add_issue('medium', filepath, f"Error scanning: {e}", None)
            return 1

    def scan_directory(self, path='.'):
        """Scan entire directory recursively"""
        self.print_header(f"🔍 SCANNING DIRECTORY: {os.path.abspath(path)}")
        
        exclude_dirs = ['venv', '__pycache__', '.git', 'node_modules', 'backup', 'backup_']
        
        for root, dirs, files in os.walk(path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(ex in d for ex in exclude_dirs)]
            
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    issues = self.scan_file(filepath)
                except Exception as e:
                    print(f"{Colors.FAIL}❌ Error scanning {filepath}: {e}{Colors.ENDC}")

    def print_summary(self):
        """Print detailed summary"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        self.print_header("📊 SCAN SUMMARY")
        
        # File statistics
        print(f"\n{Colors.BOLD}📁 Files Scanned: {self.results['total_files']}{Colors.ENDC}")
        print(f"{Colors.BOLD}⏱️  Time: {elapsed:.2f} seconds{Colors.ENDC}\n")
        
        print(f"{Colors.BOLD}File Type Breakdown:{Colors.ENDC}")
        for ext, stats in self.results['file_types'].items():
            if stats['count'] > 0:
                print(f"  {ext:6} : {stats['count']:3} files, {stats['issues']:3} issues")
        
        # Issues by severity
        total_issues = sum(len(v) for v in self.results['issues'].values())
        print(f"\n{Colors.BOLD}📊 Issues Found: {total_issues}{Colors.ENDC}\n")
        
        severity_colors = {
            'critical': Colors.FAIL,
            'high': Colors.WARNING,
            'medium': Colors.OKCYAN,
            'low': Colors.OKBLUE,
            'warnings': Colors.WARNING
        }
        
        for severity, issues in self.results['issues'].items():
            if issues:
                color = severity_colors[severity]
                icon = '❌' if severity == 'critical' else '⚠️' if severity in ['high', 'warnings'] else '🔍'
                print(f"{color}{icon} {severity.upper()}: {len(issues)} issues{Colors.ENDC}")
                
                # Show first 5 issues as examples
                for issue in issues[:5]:
                    print(f"     • {issue}")
                if len(issues) > 5:
                    print(f"     ... and {len(issues)-5} more")
                print()
        
        # Overall score
        if total_issues == 0:
            score = 100
            grade = "EXCELLENT"
            color = Colors.OKGREEN
        elif total_issues < 10:
            score = 90
            grade = "GOOD"
            color = Colors.OKGREEN
        elif total_issues < 30:
            score = 75
            grade = "FAIR"
            color = Colors.WARNING
        elif total_issues < 60:
            score = 50
            grade = "POOR"
            color = Colors.FAIL
        else:
            score = 25
            grade = "CRITICAL"
            color = Colors.FAIL
        
        print(f"\n{color}{Colors.BOLD}System Health Score: {score}% - {grade}{Colors.ENDC}")
        
        # Recommendations
        if self.results['issues']['critical']:
            print(f"\n{Colors.FAIL}{Colors.BOLD}🔴 CRITICAL: Fix critical issues first!{Colors.ENDC}")
        elif self.results['issues']['high']:
            print(f"\n{Colors.WARNING}{Colors.BOLD}🟡 HIGH: Address high-priority issues{Colors.ENDC}")
        elif self.results['issues']['medium']:
            print(f"\n{Colors.OKCYAN}{Colors.BOLD}🔵 MEDIUM: Review medium issues{Colors.ENDC}")
        else:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}✅ No critical issues found!{Colors.ENDC}")

if __name__ == "__main__":
    scanner = CodeScanner()
    
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}")
    print("╔" + "═"*68 + "╗")
    print("║     🔍 COMPLETE CODE QUALITY SCANNER 🔍                ║")
    print("║     Scanning all .html, .py, .js, .css, .json files    ║")
    print("╚" + "═"*68 + "╝")
    print(Colors.ENDC)
    
    try:
        scanner.scan_directory()
        scanner.print_summary()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Scan interrupted by user{Colors.ENDC}")
        sys.exit(1)