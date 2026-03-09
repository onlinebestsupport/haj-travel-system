#!/usr/bin/env python3
"""
Front Page Display Test - Verifies all front page content appears correctly
Run: python test_frontpage_display.py
"""

import requests
import re
from datetime import datetime
import sys

# Configuration
BASE_URL = "https://haj-web-app-production.up.railway.app"
TIMEOUT = 10

# Expected content patterns
EXPECTED_CONTENT = {
    'headings': [
        r'Your Journey to the Holy Land',
        r'Why Choose Alhudha?',
        r'Our Haj & Umrah Packages',
        r'About Alhudha Haj Travel',
        r'Contact Us'
    ],
    'stats': [
        r'25\+\s*Years Experience',
        r'10k\+\s*Happy Pilgrims',
        r'50\+\s*Expert Guides',
        r'100%\s*Satisfaction'
    ],
    'package_names': [
        r'Haj Platinum 2026',
        r'Haj Gold 2026',
        r'Haj Silver 2026',
        r'Umrah Winter 2026',
        r'Umrah Ramadhan 2026'
    ],
    'prices': [
        r'₹\s*850,?000',
        r'₹\s*550,?000',
        r'₹\s*350,?000',
        r'₹\s*145,?000',
        r'₹\s*125,?000'
    ],
    'dates': [
        r'Departure:.*2026',
        r'Duration:.*\d+\s*days'
    ],
    'contact': [
        r'123, Haj House',
        r'Mumbai.*400001',
        r'\+91 \d{5} \d{5}',
        r'accounts@alhudha\.com'
    ]
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

class FrontPageTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'details': []
        }

    def print_header(self, text):
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

    def print_test(self, name, passed, details=""):
        if passed:
            status = f"{Colors.OKGREEN}✅ PASS{Colors.ENDC}"
            self.test_results['passed'] += 1
        else:
            status = f"{Colors.FAIL}❌ FAIL{Colors.ENDC}"
            self.test_results['failed'] += 1
        
        print(f"{status} | {name}")
        if details:
            print(f"   └─ {Colors.OKCYAN}{details}{Colors.ENDC}")

    def print_warning(self, name, details=""):
        status = f"{Colors.WARNING}⚠️ WARN{Colors.ENDC}"
        self.test_results['warnings'] += 1
        print(f"{status} | {name}")
        if details:
            print(f"   └─ {Colors.OKCYAN}{details}{Colors.ENDC}")

    def test_page_load(self):
        """Test if front page loads successfully"""
        self.print_header("📄 PAGE LOAD TEST")
        
        try:
            response = self.session.get(BASE_URL, timeout=TIMEOUT)
            passed = response.status_code == 200
            self.print_test(
                "Front page loads", 
                passed, 
                f"HTTP {response.status_code} - {len(response.content)} bytes"
            )
            return response.text if passed else None
        except Exception as e:
            self.print_test("Front page loads", False, str(e))
            return None

    def test_content_presence(self, html):
        """Test if all expected content appears"""
        self.print_header("📝 CONTENT PRESENCE TEST")
        
        if not html:
            self.print_test("Content check skipped", False, "Page didn't load")
            return
        
        # Test headings
        self.print_header("📌 Headings")
        for pattern in EXPECTED_CONTENT['headings']:
            found = re.search(pattern, html, re.IGNORECASE)
            self.print_test(f"Heading: {pattern[:30]}...", bool(found))
        
        # Test stats
        self.print_header("📊 Statistics")
        for pattern in EXPECTED_CONTENT['stats']:
            found = re.search(pattern, html, re.IGNORECASE)
            self.print_test(f"Stat: {pattern[:30]}...", bool(found))
        
        # Test packages
        self.print_header("📦 Haj/Umrah Packages")
        for pattern in EXPECTED_CONTENT['package_names']:
            found = re.search(pattern, html, re.IGNORECASE)
            self.print_test(f"Package: {pattern}", bool(found))
        
        # Test prices
        self.print_header("💰 Prices")
        for pattern in EXPECTED_CONTENT['prices']:
            found = re.search(pattern, html, re.IGNORECASE)
            self.print_test(f"Price: {pattern[:20]}...", bool(found))

    def test_dynamic_data(self):
        """Test if dynamic data from API is displayed"""
        self.print_header("🔄 DYNAMIC DATA TEST")
        
        try:
            # Fetch batches from API
            response = self.session.get(f"{BASE_URL}/api/batches", timeout=TIMEOUT)
            if response.status_code != 200:
                self.print_test("API batches", False, f"HTTP {response.status_code}")
                return
            
            data = response.json()
            if not data.get('success') or not data.get('batches'):
                self.print_test("API batches", False, "No batches data")
                return
            
            # Fetch front page HTML
            html_response = self.session.get(BASE_URL, timeout=TIMEOUT)
            html = html_response.text
            
            api_batches = data['batches']
            displayed_count = 0
            
            for batch in api_batches[:5]:  # Check first 5 batches
                name = batch.get('batch_name', '')
                price = batch.get('price', '0')
                
                # Clean price for comparison
                price_str = f"₹{float(price):,.0f}".replace(',', '')
                
                # Check if batch appears on front page
                if name and name in html:
                    displayed_count += 1
                    self.print_test(f"Batch '{name[:20]}...' appears", True)
                else:
                    self.print_test(f"Batch '{name[:20]}...' appears", False)
            
            self.print_test(
                f"Batches displayed", 
                displayed_count > 0,
                f"{displayed_count} batches found on front page"
            )
            
        except Exception as e:
            self.print_test("Dynamic data check", False, str(e))

    def test_structure(self, html):
        """Test HTML structure"""
        self.print_header("🏗️  HTML STRUCTURE TEST")
        
        checks = [
            ('<!DOCTYPE html>', 'DOCTYPE declaration'),
            ('<html', 'HTML tag'),
            ('<head', 'Head section'),
            ('<body', 'Body section'),
            ('<title', 'Title tag'),
            ('<meta charset', 'Charset meta'),
            ('<link', 'CSS links'),
            ('<script', 'JavaScript tags')
        ]
        
        for pattern, desc in checks:
            found = pattern in html
            self.print_test(desc, found)

    def test_performance(self):
        """Test page load performance"""
        self.print_header("⚡ PERFORMANCE TEST")
        
        times = []
        for i in range(3):
            start = datetime.now()
            try:
                self.session.get(BASE_URL, timeout=TIMEOUT)
                elapsed = (datetime.now() - start).total_seconds() * 1000
                times.append(elapsed)
            except:
                pass
        
        if times:
            avg_time = sum(times) / len(times)
            passed = avg_time < 2000  # Should load in under 2 seconds
            self.print_test(
                "Page load time",
                passed,
                f"Average: {avg_time:.2f}ms"
            )
        else:
            self.print_test("Page load time", False, "Could not measure")

    def test_mobile_responsiveness(self, html):
        """Check for mobile-friendly elements"""
        self.print_header("📱 MOBILE RESPONSIVENESS")
        
        checks = [
            ('viewport', 'Viewport meta tag present'),
            ('@media', 'Media queries present'),
            ('flex', 'Flexbox/grid layout'),
            ('max-width', 'Responsive max-width')
        ]
        
        for pattern, desc in checks:
            found = pattern in html
            if found:
                self.print_test(desc, True)
            else:
                self.print_warning(desc, f"'{pattern}' not found")

    def test_images(self, html):
        """Check for images and alt text"""
        self.print_header("🖼️  IMAGES TEST")
        
        img_tags = re.findall(r'<img[^>]+>', html)
        self.print_test(f"Images found", len(img_tags) > 0, f"{len(img_tags)} images")
        
        # Check for alt text
        alts = re.findall(r'alt="([^"]*)"', html)
        missing_alt = len(img_tags) - len(alts)
        if missing_alt == 0:
            self.print_test("All images have alt text", True)
        else:
            self.print_warning("Alt text", f"{missing_alt} images missing alt text")

    def run_all_tests(self):
        """Run all front page tests"""
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}")
        print("╔══════════════════════════════════════════════════════════╗")
        print("║     🏠 FRONT PAGE DISPLAY VERIFICATION TEST 🏠          ║")
        print("║        Checking if all content appears correctly        ║")
        print("╚══════════════════════════════════════════════════════════╝")
        print(Colors.ENDC)
        
        print(f"🎯 Testing: {Colors.BOLD}{BASE_URL}{Colors.ENDC}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Run tests
        html = self.test_page_load()
        
        if html:
            self.test_structure(html)
            self.test_content_presence(html)
            self.test_dynamic_data()
            self.test_images(html)
            self.test_mobile_responsiveness(html)
            self.test_performance()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        total = self.test_results['passed'] + self.test_results['failed']
        pass_rate = (self.test_results['passed'] / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}📊 TEST SUMMARY{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
        
        print(f"✅ Passed:  {Colors.OKGREEN}{self.test_results['passed']}{Colors.ENDC}")
        print(f"❌ Failed:  {Colors.FAIL}{self.test_results['failed']}{Colors.ENDC}")
        print(f"⚠️ Warnings: {Colors.WARNING}{self.test_results['warnings']}{Colors.ENDC}")
        print(f"📈 Pass Rate: {Colors.OKBLUE}{pass_rate:.1f}%{Colors.ENDC}\n")
        
        if pass_rate >= 90:
            print(f"{Colors.OKGREEN}{Colors.BOLD}✅ Front page is displaying correctly!{Colors.ENDC}")
        elif pass_rate >= 70:
            print(f"{Colors.WARNING}{Colors.BOLD}⚠️ Minor issues found - fix warnings{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}❌ Major display issues - fix required{Colors.ENDC}")
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

if __name__ == "__main__":
    tester = FrontPageTester()
    try:
        tester.run_all_tests()
        sys.exit(0 if tester.test_results['failed'] == 0 else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Tests interrupted by user{Colors.ENDC}")
        sys.exit(1)