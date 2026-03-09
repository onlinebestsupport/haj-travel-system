#!/usr/bin/env python3
"""
AUTO-FIX ALL - Complete system repair tool
Run: python auto_fix_all.py
"""

import os
import re
import shutil
from datetime import datetime
import subprocess

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

class AutoFixAll:
    def __init__(self):
        self.fixes_applied = 0
        self.issues_found = 0
        self.backup_created = False
        
    def print_header(self, text):
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")

    def print_success(self, text):
        print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

    def print_warning(self, text):
        print(f"{Colors.WARNING}⚠️ {text}{Colors.ENDC}")

    def print_error(self, text):
        print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

    def print_info(self, text):
        print(f"{Colors.OKCYAN}ℹ️ {text}{Colors.ENDC}")

    def create_backup(self):
        """Create a backup of important files"""
        if not self.backup_created:
            backup_dir = f"backup_auto_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(backup_dir, exist_ok=True)
            
            important_dirs = ['app', 'public', 'routes']
            for d in important_dirs:
                if os.path.exists(d):
                    shutil.copytree(d, os.path.join(backup_dir, d), dirs_exist_ok=True)
            
            for f in ['requirements.txt', 'Procfile', 'railway.json', 'gunicorn.conf.py']:
                if os.path.exists(f):
                    shutil.copy2(f, backup_dir)
            
            self.print_success(f"Backup created in {backup_dir}")
            self.backup_created = True

    def fix_merge_conflicts(self):
        """Remove all merge conflict markers from files"""
        self.print_header("🔧 FIXING MERGE CONFLICTS")
        
        conflict_patterns = [
            (r'<<<<<<< HEAD\n.*?\n=======\n.*?\n>>>>>>> [a-f0-9]+\n', ''),
            (r'<<<<<<< HEAD\n', ''),
            (r'=======\n', ''),
            (r'>>>>>>> [a-f0-9]+\n', '')
        ]
        
        files_fixed = 0
        for root, dirs, files in os.walk('.'):
            if 'venv' in root or '__pycache__' in root or '.git' in root:
                continue
            
            for file in files:
                if file.endswith(('.py', '.html', '.js', '.css', '.txt', '.md', '.json')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        new_content = content
                        for pattern, replacement in conflict_patterns:
                            new_content = re.sub(pattern, replacement, new_content, flags=re.DOTALL)
                        
                        if new_content != content:
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            files_fixed += 1
                            self.print_success(f"Fixed merge conflicts in {filepath}")
                    except Exception as e:
                        pass
        
        self.print_info(f"Fixed {files_fixed} files with merge conflicts")
        self.fixes_applied += files_fixed

    def fix_duplicate_routes(self):
        """Fix duplicate route definitions in Flask files"""
        self.print_header("🔧 FIXING DUPLICATE ROUTES")
        
        route_files = [
            'app/routes/admin.py',
            'app/routes/auth.py',
            'app/routes/travelers.py',
            'app/routes/payments.py',
            'app/routes/invoices.py',
            'app/routes/receipts.py',
            'app/routes/reports.py'
        ]
        
        fixes_applied = 0
        for filepath in route_files:
            if not os.path.exists(filepath):
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Track function names to detect duplicates
                function_names = {}
                new_lines = []
                i = 0
                
                while i < len(lines):
                    line = lines[i]
                    
                    # Check for function definition
                    func_match = re.search(r'def (\w+)\(', line)
                    if func_match:
                        func_name = func_match.group(1)
                        
                        # If we've seen this function before, skip it
                        if func_name in function_names:
                            self.print_warning(f"Removing duplicate function {func_name} in {filepath}")
                            # Skip until we find the next function or end of current function
                            while i < len(lines) and not lines[i].startswith('def ') and not lines[i].startswith('@'):
                                i += 1
                            fixes_applied += 1
                            continue
                        else:
                            function_names[func_name] = True
                    
                    new_lines.append(line)
                    i += 1
                
                if len(new_lines) != len(lines):
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    self.print_success(f"Fixed duplicates in {filepath}")
                    
            except Exception as e:
                self.print_error(f"Error processing {filepath}: {e}")
        
        self.fixes_applied += fixes_applied

    def fix_database_url(self):
        """Ensure DATABASE_URL is properly set"""
        self.print_header("🔧 CHECKING DATABASE_URL")
        
        try:
            # Get current DATABASE_URL from web app
            result = subprocess.run(
                ['railway', 'variables', '--service', 'haj-web-app'],
                capture_output=True,
                text=True
            )
            
            if 'DATABASE_URL' in result.stdout:
                # Extract the URL - might be truncated
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'DATABASE_URL' in line and 'postgresql://' in line:
                        # Check if it's truncated
                        if 'postgresql://' in line and len(line) < 100:
                            self.print_warning("DATABASE_URL may be truncated")
                            
                            # Get correct URL from Postgres service
                            pg_result = subprocess.run(
                                ['railway', 'variables', '--service', 'Postgres'],
                                capture_output=True,
                                text=True
                            )
                            
                            pg_lines = pg_result.stdout.split('\n')
                            for pg_line in pg_lines:
                                if 'DATABASE_URL' in pg_line and 'postgresql://' in pg_line:
                                    # Extract full URL
                                    url_match = re.search(r'(postgresql://[^\s]+)', pg_line)
                                    if url_match:
                                        full_url = url_match.group(1)
                                        # Set it for web app
                                        subprocess.run([
                                            'railway', 'variables', 'set',
                                            f'DATABASE_URL={full_url}',
                                            '--service', 'haj-web-app'
                                        ])
                                        self.print_success("Fixed DATABASE_URL")
                                        self.fixes_applied += 1
                                    break
                            break
                else:
                    self.print_success("DATABASE_URL looks good")
            else:
                self.print_error("DATABASE_URL not found in web app variables")
                
        except Exception as e:
            self.print_error(f"Could not check DATABASE_URL: {e}")

    def fix_railway_json(self):
        """Fix railway.json configuration"""
        self.print_header("🔧 FIXING RAILWAY.JSON")
        
        if not os.path.exists('railway.json'):
            self.print_error("railway.json not found")
            return
        
        try:
            with open('railway.json', 'r') as f:
                content = f.read()
            
            # Remove any merge conflict markers
            content = re.sub(r'<<<<<<< HEAD.*?\n', '', content, flags=re.DOTALL)
            content = re.sub(r'=======\n', '', content)
            content = re.sub(r'>>>>>>> [a-f0-9]+\n', '', content)
            
            # Ensure proper healthcheck settings
            healthcheck_config = {
                "healthcheckPath": "/health",
                "healthcheckTimeout": 30
            }
            
            # Parse JSON and update
            import json
            try:
                config = json.loads(content)
                if 'deploy' not in config:
                    config['deploy'] = {}
                
                config['deploy']['healthcheckPath'] = '/health'
                config['deploy']['healthcheckTimeout'] = 30
                
                # Write back formatted JSON
                with open('railway.json', 'w') as f:
                    json.dump(config, f, indent=2)
                
                self.print_success("Fixed railway.json configuration")
                self.fixes_applied += 1
                
            except json.JSONDecodeError:
                self.print_error("railway.json has invalid JSON")
                
        except Exception as e:
            self.print_error(f"Error fixing railway.json: {e}")

    def fix_procfile(self):
        """Ensure Procfile is correct"""
        self.print_header("🔧 FIXING PROCFILE")
        
        correct_procfile = "web: gunicorn app.server:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1 --threads 2 --log-level debug"
        
        if os.path.exists('Procfile'):
            with open('Procfile', 'r') as f:
                content = f.read().strip()
            
            if content != correct_procfile:
                with open('Procfile', 'w') as f:
                    f.write(correct_procfile + '\n')
                self.print_success("Fixed Procfile")
                self.fixes_applied += 1
            else:
                self.print_success("Procfile is correct")
        else:
            with open('Procfile', 'w') as f:
                f.write(correct_procfile + '\n')
            self.print_success("Created Procfile")
            self.fixes_applied += 1

    def fix_gunicorn_conf(self):
        """Ensure gunicorn.conf.py is correct"""
        self.print_header("🔧 FIXING GUNICORN.CONF.PY")
        
        correct_config = """bind = "0.0.0.0:8080"
workers = 1
threads = 2
timeout = 120
"""
        
        if os.path.exists('gunicorn.conf.py'):
            with open('gunicorn.conf.py', 'r') as f:
                content = f.read()
            
            # Check if binding is correct
            if '0.0.0.0' not in content:
                with open('gunicorn.conf.py', 'w') as f:
                    f.write(correct_config)
                self.print_success("Fixed gunicorn.conf.py")
                self.fixes_applied += 1
            else:
                self.print_success("gunicorn.conf.py is correct")
        else:
            with open('gunicorn.conf.py', 'w') as f:
                f.write(correct_config)
            self.print_success("Created gunicorn.conf.py")
            self.fixes_applied += 1

    def fix_requirements(self):
        """Ensure requirements.txt is clean"""
        self.print_header("🔧 FIXING REQUIREMENTS.TXT")
        
        if os.path.exists('requirements.txt'):
            with open('requirements.txt', 'r') as f:
                content = f.read()
            
            # Remove any merge conflict markers
            content = re.sub(r'<<<<<<< HEAD.*?\n', '', content, flags=re.DOTALL)
            content = re.sub(r'=======\n', '', content)
            content = re.sub(r'>>>>>>> [a-f0-9]+\n', '', content)
            
            # Ensure each package is on its own line
            lines = content.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Split if multiple packages on one line
                    parts = re.split(r'\s+', line)
                    cleaned_lines.extend(parts)
            
            if cleaned_lines:
                with open('requirements.txt', 'w') as f:
                    f.write('\n'.join(cleaned_lines) + '\n')
                self.print_success("Cleaned requirements.txt")
                self.fixes_applied += 1

    def run_all_fixes(self):
        """Run all fix functions"""
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}")
        print("╔" + "═"*68 + "╗")
        print("║     🔧 AUTO-FIX ALL - COMPLETE SYSTEM REPAIR 🔧        ║")
        print("║     Automatically detecting and fixing all issues      ║")
        print("╚" + "═"*68 + "╝")
        print(Colors.ENDC)
        
        # Create backup first
        self.create_backup()
        
        # Run all fixes
        self.fix_merge_conflicts()
        self.fix_duplicate_routes()
        self.fix_railway_json()
        self.fix_procfile()
        self.fix_gunicorn_conf()
        self.fix_requirements()
        self.fix_database_url()
        
        # Summary
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}📊 FIX SUMMARY{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
        
        self.print_success(f"Total fixes applied: {self.fixes_applied}")
        
        if self.fixes_applied > 0:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}✅ System has been repaired!{Colors.ENDC}")
            print(f"{Colors.OKCYAN}Run 'railway up' to deploy the fixes{Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}✅ No fixes needed - system is already clean!{Colors.ENDC}")
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")

if __name__ == "__main__":
    fixer = AutoFixAll()
    try:
        fixer.run_all_fixes()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Auto-fix interrupted by user{Colors.ENDC}")