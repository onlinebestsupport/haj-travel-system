# gunicorn.conf.py
import os

# Get port from Railway (they set PORT environment variable)
port = os.environ.get('PORT', 8080)

bind = f"0.0.0.0:{port}"
workers = 4
timeout = 120
worker_class = 'gthread'
threads = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'