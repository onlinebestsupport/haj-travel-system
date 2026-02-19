#!/usr/bin/env python
"""
Entry point for running the application directly.
For production, use: gunicorn app:app
"""

import os
from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Server starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
