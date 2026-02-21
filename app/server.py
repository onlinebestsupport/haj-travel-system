from flask import Flask, send_from_directory
from flask_cors import CORS
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import init_db
from app.routes import auth, batches, travelers

# Initialize Flask app
app = Flask(__name__, 
            static_folder='../public',
            static_url_path='')

# Enable CORS
CORS(app, supports_credentials=True)

# Secret key for sessions
app.secret_key = 'alhudha-haj-secret-key-2026'

# Initialize database
init_db()

# Register blueprints
app.register_blueprint(auth.bp)
app.register_blueprint(batches.bp)
app.register_blueprint(travelers.bp)

# Serve static files
@app.route('/')
def serve_index():
    return send_from_directory('../public', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../public', path)

@app.route('/admin/<path:path>')
def serve_admin(path):
    return send_from_directory('../public/admin', path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
