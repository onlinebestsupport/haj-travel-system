"""
Configuration and environment validator
Run this script to validate your project setup

Usage:
    python config_validator.py
"""

import os
import sys
from pathlib import Path

class ConfigValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.base_dir = Path(__file__).parent
    
    def check_directories(self):
        """Check if required directories exist"""
        print("\n" + "="*60)
        print("📁 CHECKING DIRECTORIES")
        print("="*60)
        
        required_dirs = {
            'public': self.base_dir / 'public',
            'public/admin': self.base_dir / 'public' / 'admin',
            'app': self.base_dir / 'app',
            'app/routes': self.base_dir / 'app' / 'routes',
            'uploads': self.base_dir / 'uploads',
        }
        
        for name, path in required_dirs.items():
            if path.exists():
                print(f"✅ {name}: EXISTS")
            else:
                print(f"❌ {name}: MISSING - {path}")
                self.errors.append(f"Missing directory: {name}")
    
    def check_files(self):
        """Check if required files exist"""
        print("\n" + "="*60)
        print("📄 CHECKING FILES")
        print("="*60)
        
        required_files = {
            'public/index.html': self.base_dir / 'public' / 'index.html',
            'public/admin.login.html': self.base_dir / 'public' / 'admin.login.html',
            'public/traveler_login.html': self.base_dir / 'public' / 'traveler_login.html',
            'public/traveler_dashboard.html': self.base_dir / 'public' / 'traveler_dashboard.html',
            'public/admin/dashboard.html': self.base_dir / 'public' / 'admin' / 'dashboard.html',
            'public/style.css': self.base_dir / 'public' / 'style.css',
            'app/server.py': self.base_dir / 'app' / 'server.py',
            'app/database.py': self.base_dir / 'app' / 'database.py',
        }
        
        for name, path in required_files.items():
            if path.exists():
                print(f"✅ {name}")
            else:
                print(f"❌ {name}: NOT FOUND")
                self.errors.append(f"Missing file: {name}")
    
    def check_environment(self):
        """Check environment variables"""
        print("\n" + "="*60)
        print("🔐 CHECKING ENVIRONMENT VARIABLES")
        print("="*60)
        
        env_vars = ['DATABASE_URL', 'SECRET_KEY', 'PORT']
        
        for var in env_vars:
            if var in os.environ:
                value = os.environ[var]
                masked = value[:5] + '***' if len(value) > 5 else '***'
                print(f"✅ {var}: SET ({masked})")
            else:
                print(f"⚠️  {var}: NOT SET (using default)")
                self.warnings.append(f"Environment variable not set: {var}")
    
    def check_imports(self):
        """Check if required Python packages are installed"""
        print("\n" + "="*60)
        print("📦 CHECKING PYTHON PACKAGES")
        print("="*60)
        
        packages = {
            'flask': 'Flask',
            'flask_cors': 'Flask-CORS',
            'psycopg2': 'psycopg2-binary',
            'dotenv': 'python-dotenv',
            'requests': 'requests'
        }
        
        for module, package_name in packages.items():
            try:
                __import__(module)
                print(f"✅ {package_name}")
            except ImportError:
                print(f"❌ {package_name}: NOT INSTALLED")
                self.errors.append(f"Missing package: {package_name} (pip install {package_name})")
    
    def run(self):
        """Run all validations"""
        print("\n" + "🔍 CONFIGURATION VALIDATOR")
        print("Alhudha Haj Travel System Setup Check\n")
        
        self.check_directories()
        self.check_files()
        self.check_environment()
        self.check_imports()
        
        # Summary
        print("\n" + "="*60)
        print("📊 VALIDATION SUMMARY")
        print("="*60)
        
        if not self.errors and not self.warnings:
            print("✅ ALL CHECKS PASSED! Your setup is ready.")
            print("🚀 You can now start the server:\n")
            print("   Local:   python app/server.py")
            print("   Gunicorn: gunicorn app.server:app")
            print("   Script:  ./start.sh")
            return 0
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if self.errors:
            print(f"\n❌ ERRORS FOUND ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
            print("\n🔧 FIX THESE ERRORS BEFORE RUNNING THE SERVER")
            return 1
        
        return 0

if __name__ == '__main__':
    validator = ConfigValidator()
    sys.exit(validator.run())
