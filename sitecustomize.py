"""
sitecustomize.py - Python startup customization

CRITICAL: This file is automatically loaded by Python on startup (before any imports).

BUSINESS CONTEXT:
Tests import from microservices using absolute imports. This file ensures all service
directories are in sys.path BEFORE any test modules try to import them.

TECHNICAL APPROACH:
Python automatically imports sitecustomize.py from the current directory at startup.
This happens BEFORE pytest tries to import test modules, solving the import timing issue.

WHY THIS WORKS:
- Python loads sitecustomize.py automatically (if it exists in current dir or PYTHONPATH)
- This happens at the VERY START of Python interpreter initialization
- Therefore paths are set BEFORE pytest imports anything

USAGE:
Just run pytest from project root - this file loads automatically.
"""

import os
import sys

# Get project root (where this file is located)
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# Service directories to add to Python path
SERVICES = [
    'analytics',
    'content-management',
    'content-storage',
    'course-generator',
    'course-management',
    'demo-service',
    'knowledge-graph-service',
    'lab-manager',
    'metadata-service',
    'nlp-preprocessing',
    'organization-management',
    'rag-service',
    'user-management'
]

# Add all service paths to sys.path
for service in SERVICES:
    service_path = os.path.join(PROJECT_ROOT, 'services', service)
    if os.path.exists(service_path) and service_path not in sys.path:
        sys.path.insert(0, service_path)

# Also add project root
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
