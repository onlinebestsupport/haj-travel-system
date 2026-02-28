# gunicorn.conf.py
import multiprocessing
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"
workers = 1  # Start with 1 worker to reduce memory
threads = 4
timeout = 120  # 2 minutes timeout
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
worker_class = 'gthread'
worker_connections = 1000
accesslog = '-'
errorlog = '-'
loglevel = 'debug'
capture_output = True
enable_stdio_inheritance = True
