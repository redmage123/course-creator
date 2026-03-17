"""
Pytest Plugin: Early Path Setup

CRITICAL: Loads service paths into sys.path BEFORE pytest imports test modules.

BUSINESS CONTEXT:
Tests import from microservices using absolute imports (e.g., "from domain.entities.metadata import Metadata").
Without adding service paths to sys.path FIRST, these imports fail with ModuleNotFoundError.

TECHNICAL APPROACH:
This is a pytest plugin that runs at the EARLIEST possible point (module import time)
to ensure all service paths are available before pytest starts loading test files.

WHY NOT conftest.py:
- conftest.py loads AFTER pytest tries to import test modules
- pytest.ini pythonpath loads too late (known pytest limitation)
- This plugin approach ensures paths are set FIRST

USAGE:
Automatically loaded by pytest if placed in pytest_plugins/ or registered in pytest.ini
"""

import os
import sys

# Get project root (parent of pytest_plugins directory)
PLUGIN_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(PLUGIN_DIR, '..'))

# Add ALL service paths to sys.path IMMEDIATELY (at module import time)
SERVICE_PATHS = [
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

# Insert service paths at the BEGINNING of sys.path
for service in SERVICE_PATHS:
    service_path = os.path.join(PROJECT_ROOT, 'services', service)
    if os.path.exists(service_path) and service_path not in sys.path:
        sys.path.insert(0, service_path)

# Also add project root
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
