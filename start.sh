#!/bin/bash
# Alhudha Haj Travel System - Server Startup Script
# Standardized for both local and Railway deployment

set -e  # Exit on error

# Get port from environment or use default
PORT=${PORT:-8080}

# Validate Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    exit 1
fi

echo "🚀 Starting Alhudha Haj Travel System..."
echo "📡 Port: $PORT"
echo "⚙️  Gunicorn: 2 workers, 2 threads, 120s timeout"

# Use gunicorn with optimized settings for Railway
exec gunicorn \
    app.server:app \
    --bind 0.0.0.0:${PORT} \
    --workers 2 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level debug
