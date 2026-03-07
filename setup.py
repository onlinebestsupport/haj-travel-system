# setup.py
import subprocess
import sys

print("Installing Flask-CORS explicitly...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "Flask-CORS"])
print("Done!")