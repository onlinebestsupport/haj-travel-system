from app import create_app
from app.database import init_db
from flask import send_from_directory
import os

app = create_app()

@app.route('/')
def serve_index():
    return send_from_directory('../public', 'index.html')

@app.route('/admin')
def serve_admin():
    return send_from_directory('../public', 'admin.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../public', path)

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
