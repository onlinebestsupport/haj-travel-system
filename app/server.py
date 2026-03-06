from flask import Flask, send_from_directory, jsonify, request, session, make_response
from flask_cors import CORS
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import hashlib
import uuid
import threading
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== ENVIRONMENT CONFIGURATION ====================
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import database
from app.database import get_db, init_db

# Import route blueprints
from app.routes import auth, admin, batches, travelers, payments, company, uploads, reports, invoices, receipts

# ==================== FLASK APP INITIALIZATION ====================
app = Flask(__name__)

# Global flag to track database initialization
_db_initialized = False
_db_init_lock = threading.Lock()

# ==================== APP CONFIGURATION ====================
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'alhudha-haj-secret-key-2026')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# 🔥 CRITICAL SESSION FIXES - UPDATED
app.config['SESSION_COOKIE_NAME'] = 'alhudha_session'
app.config['SESSION_COOKIE_DOMAIN'] = None  # Allow all domains
app.config['SESSION_COOKIE_PATH'] = '/'  # Cookie valid for entire site
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True only with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Changed from 'Strict' to 'Lax'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # 30 minutes default
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_COOKIE_PERSISTENT'] = True  # Keep cookie after browser close

# ==================== DIRECTORY PATHS ====================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
ADMIN_DIR = os.path.join(PUBLIC_DIR, 'admin')
TRAVELER_DIR = os.path.join(PUBLIC_DIR, 'traveler')

print(f"📁 Base directory: {BASE_DIR}")
print(f"📁 Public directory: {PUBLIC_DIR}")
print(f"📁 Admin directory: {ADMIN_DIR}")
print(f"📁 Traveler directory: {TRAVELER_DIR}")
print(f"📁 Uploads directory: {app.config['UPLOAD_FOLDER']}")

# Check if directories exist
print(f"📁 Public exists: {os.path.exists(PUBLIC_DIR)}")
print(f"📁 Admin exists: {os.path.exists(ADMIN_DIR)}")
print(f"📁 Traveler exists: {os.path.exists(TRAVELER_DIR)}")

# List files in public directory for debugging
if os.path.exists(PUBLIC_DIR):
    print(f"📄 Files in public: {os.listdir(PUBLIC_DIR)}")
if os.path.exists(ADMIN_DIR):
    print(f"📄 Files in admin: {os.listdir(ADMIN_DIR)}")

# ==================== CORS CONFIGURATION ====================
# 🔥 UPDATED: More specific CORS for Railway
CORS(app, 
     supports_credentials=True, 
