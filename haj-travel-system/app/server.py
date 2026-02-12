from flask import Flask, send_from_directory
from flask_cors import CORS
from app.database import init_db
import os

app = Flask(__name__, 
            static_folder='../public',
            template_folder='../public')
CORS(app)

# Serve index.html at root
@app.route('/')
def serve_index():
    return send_from_directory('../public', 'index.html')

# Serve admin.html at /admin
@app.route('/admin')
def serve_admin():
    return send_from_directory('../public', 'admin.html')

# Serve all static files (CSS, JS, images)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../public', path)

# API endpoint
@app.route('/api')
def api():
    return {
        "name": "Haj Travel System",
        "status": "active",
        "fields": 33
    }

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
