# fix_requirements.py
import os

req_path = r"C:\Users\Masood\Desktop\haj-travel-system\haj-travel-system\requirements.txt"

with open(req_path, 'r') as f:
    content = f.read()

if 'flask' not in content.lower():
    with open(req_path, 'a') as f:
        f.write('\nflask==2.3.3\n')
    print("✅ Added flask to requirements.txt")
else:
    print("✅ flask already in requirements.txt")