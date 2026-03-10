from flask import Flask
import os
import sys

"""
Alhudha Haj Travel System - Application Factory
This module initializes the Flask application and exports it for use in server.py
"""

def create_app(config=None):
    """
    Application factory function for creating Flask app instances

    Args:
        config (dict, optional): Configuration dictionary

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)

    # Default configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'alhudha-haj-secret-key-2026')
    app.config['SESSION_TYPE'] = 'filesystem'

    # Apply additional config if provided
    if config:
        app.config.update(config)

    return app

# This file makes the app directory a Python package
__all__ = ['create_app']
