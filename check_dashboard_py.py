import os
import re

def scan_dashboard_related_py():
    print("=" * 70)
    print("🔍 SCANNING PYTHON FILES RELATED TO DASHBOARD MODULE")
    print("=" * 70)
    
    dashboard_files = []
    dashboard_routes = []
    dashboard_apis = []
    dashboard_functions = []
    
    patterns = {
        'files': [
            r'.*dashboard.*\.py$',
        ],
        'routes': [
            r'@.*route.*dashboard',
            r'url.*dashboard',
            r'endpoint.*dashboard',
        ],
        'apis': [
            r'/api/admin/dashboard',
            r'dashboard.*stats',
            r'dashboard.*data',
        ],
        'functions': [
            r'def.*dashboard',
            r'get_dashboard',
            r'load_dashboard',
        ]
    }
    
    for root, dirs, files in os.walk('.'):
        if 'venv' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                
                # Check filename
                if re.search(patterns['files'][0], filepath, re.IGNORECASE):
                    dashboard_files.append(filepath)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                        # Check routes
                        for pattern in patterns['routes']:
                            for i, line in enumerate(lines):
                                if re.search(pattern, line, re.IGNORECASE):
                                    dashboard_routes.append({
                                        'file': filepath,
                                        'line': i+1,
                                        'code': line.strip()
                                    })
                        
                        # Check APIs
                        for pattern in patterns['apis']:
                            for i, line in enumerate(lines):
                                if re.search(pattern, line, re.IGNORECASE):
                                    dashboard_apis.append({
                                        'file': filepath,
                                        'line': i+1,
                                        'code': line.strip()
                                    })
                        
                        # Check functions
                        for pattern in patterns['functions']:
                            for i, line in enumerate(lines):
                                if re.search(pattern, line, re.IGNORECASE):
                                    dashboard_functions.append({
                                        'file': filepath,
                                        'line': i+1,
                                        'code': line.strip()
                                    })
                                
                except Exception as e:
                    print(f"❌ Error reading {filepath}: {e}")
    
    # Print results
    print("\n📁 PYTHON FILES WITH 'DASHBOARD' IN NAME:")
    if dashboard_files:
        for f in dashboard_files:
            print(f"   ✅ {f}")
    else:
        print("   ❌ None found")
    
    print("\n🛣️  DASHBOARD ROUTES FOUND:")
    if dashboard_routes:
        for r in dashboard_routes:
            print(f"   📍 {r['file']}:{r['line']}")
            print(f"      {r['code']}")
    else:
        print("   ❌ None found")
    
    print("\n📡 DASHBOARD API ENDPOINTS:")
    if dashboard_apis:
        for a in dashboard_apis:
            print(f"   📍 {a['file']}:{a['line']}")
            print(f"      {a['code']}")
    else:
        print("   ❌ None found")
    
    print("\n⚙️  DASHBOARD FUNCTIONS:")
    if dashboard_functions:
        for f in dashboard_functions:
            print(f"   📍 {f['file']}:{f['line']}")
            print(f"      {f['code']}")
    else:
        print("   ❌ None found")
    
    print("\n" + "=" * 70)
    print(f"📊 SUMMARY: Found {len(dashboard_files)} dashboard files, {len(dashboard_routes)} routes, {len(dashboard_apis)} APIs, {len(dashboard_functions)} functions")
    print("=" * 70)

if __name__ == "__main__":
    scan_dashboard_related_py()