#!/bin/bash
exec gunicorn app:app --bind 0.0.0.0:${PORT:-8080} --workers 4 --threads 2 --timeout 60
