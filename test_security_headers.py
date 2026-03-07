#!/usr/bin/env python3
"""
🛡️ Security Headers Verification
Tests security headers added to app/server.py
"""

import requests

BASE_URL = "https://haj-web-app-production.up.railway.app"

security_headers = {
    'X-Frame-Options': {
        'expected': 'SAMEORIGIN',
        'purpose': '🔐 Clickjacking protection'
    },
    'X-Content-Type-Options': {
        'expected': 'nosniff',
        'purpose': '🔐 MIME type sniffing protection'
    },
    'Strict-Transport-Security': {
        'expected': 'max-age=31536000',
        'purpose': '🔐 HTTPS enforcement (HSTS)'
    },
    'Content-Security-Policy': {
        'expected': 'default-src',
        'purpose': '🔐 XSS protection (CSP)'
    },
    'X-XSS-Protection': {
        'expected': '1; mode=block',
        'purpose': '🔐 XSS attack prevention'
    },
    'Referrer-Policy': {
        'expected': 'strict-origin',
        'purpose': '🔐 Referrer information control'
    }
}

print("\n" + "="*70)
print("🛡️  SECURITY HEADERS VERIFICATION".center(70))
print("="*70 + "\n")

try:
    response = requests.get(BASE_URL, timeout=10)
    
    print(f"Testing: {BASE_URL}\n")
    
    passed = 0
    failed = 0
    
    for header, config in security_headers.items():
        value = response.headers.get(header)
        
        if value:
            expected = config['expected']
            if expected in value:
                print(f"✅ {header}")
                print(f"   └─ {config['purpose']}")
                print(f"   └─ Value: {value[:60]}\n")
                passed += 1
            else:
                print(f"⚠️  {header}")
                print(f"   └─ Expected: {expected}")
                print(f"   └─ Got: {value[:60]}\n")
                failed += 1
        else:
            print(f"❌ {header}")
            print(f"   └─ {config['purpose']}")
            print(f"   └─ Not set\n")
            failed += 1
    
    print("="*70)
    print(f"✅ Passed: {passed} | ❌ Failed: {failed}")
    print("="*70 + "\n")

except Exception as e:
    print(f"❌ Error: {e}\n")