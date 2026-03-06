# fix_requirements_final.py
import os

print("="*60)
print("🔧 FIXING REQUIREMENTS.TXT FINAL")
print("="*60)

req_path = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system\requirements.txt"

# Read current content
with open(req_path, 'r') as f:
    lines = f.readlines()

# Clean up lines
cleaned_lines = []
flask_found = False
psycopg2_found = False
gunicorn_found = False

for line in lines:
    line = line.strip()
    if line and not line.startswith('#'):
        if 'flask' in line.lower():
            flask_found = True
            cleaned_lines.append('Flask==2.3.3')
        elif 'psycopg2' in line.lower():
            psycopg2_found = True
            cleaned_lines.append('psycopg2-binary==2.9.9')
        elif 'gunicorn' in line.lower():
            gunicorn_found = True
            cleaned_lines.append('gunicorn==21.2.0')
        elif line:
            cleaned_lines.append(line)

# Add missing packages
if not flask_found:
    cleaned_lines.append('Flask==2.3.3')
    print("✅ Added Flask")
if not psycopg2_found:
    cleaned_lines.append('psycopg2-binary==2.9.9')
    print("✅ Added psycopg2-binary")
if not gunicorn_found:
    cleaned_lines.append('gunicorn==21.2.0')
    print("✅ Added gunicorn")

# Add other required packages
required_packages = [
    'Flask-CORS==4.0.0',
    'python-dotenv==1.0.0',
    'requests==2.31.0',
    'Werkzeug==2.3.7'
]

for pkg in required_packages:
    pkg_name = pkg.split('==')[0].lower()
    found = False
    for line in cleaned_lines:
        if pkg_name in line.lower():
            found = True
            break
    if not found:
        cleaned_lines.append(pkg)
        print(f"✅ Added {pkg}")

# Remove duplicates while preserving order
unique_lines = []
for line in cleaned_lines:
    if line not in unique_lines:
        unique_lines.append(line)

# Write back
with open(req_path, 'w') as f:
    f.write('\n'.join(unique_lines))

print(f"\n📊 Final requirements.txt has {len(unique_lines)} packages:")
for line in sorted(unique_lines):
    print(f"   • {line}")

print("\n" + "="*60)
print("✅ requirements.txt fixed!")
print("="*60)