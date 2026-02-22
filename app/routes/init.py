"""
Alhudha Haj Travel System - Routes Package Initialization
This file makes the routes directory a Python package and exposes all route blueprints.
"""

from . import auth
from . import admin
from . import batches
from . import travelers
from . import payments
from . import company
from . import uploads

# You can optionally create a list of all blueprints for easier importing
__all__ = [
    'auth',
    'admin', 
    'batches',
    'travelers',
    'payments',
    'company',
    'uploads'
]

# Optional: Version info for the routes package
__version__ = '2.0.0'
__author__ = 'Alhudha Haj Travel System'
__description__ = 'Route handlers for Alhudha Haj Travel System API'
