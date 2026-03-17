# CRITICAL: Path setup MUST happen BEFORE any other imports
# This runs at the absolute earliest point when conftest.py is loaded

import os
import sys

# Get project root directory IMMEDIATELY
_PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# DEBUG: Print to stderr so we can see if this runs
import sys as _sys
print(f"[CONFTEST] Loading from {_PROJECT_ROOT}", file=_sys.stderr)

# Add ALL services to sys.path RIGHT NOW (before pytest does anything else)
_SERVICE_PATHS = [
    'analytics', 'content-management', 'content-storage', 'course-generator',
    'course-management', 'demo-service', 'knowledge-graph-service', 'lab-manager',
    'metadata-service', 'nlp-preprocessing', 'organization-management',
    'rag-service', 'user-management'
]

for _service in _SERVICE_PATHS:
    _service_path = os.path.join(_PROJECT_ROOT, 'services', _service)
    if os.path.exists(_service_path) and _service_path not in sys.path:
        sys.path.insert(0, _service_path)
        print(f"[CONFTEST] Added to sys.path: {_service_path}", file=_sys.stderr)

if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
    print(f"[CONFTEST] Added project root to sys.path", file=_sys.stderr)

_service_paths_in_syspath = [p for p in sys.path if 'services' in p]
print(f"[CONFTEST] Setup complete. Total paths: {len(_service_paths_in_syspath)}", file=_sys.stderr)
if 'metadata-service' in str(_service_paths_in_syspath):
    print(f"[CONFTEST] ✓ metadata-service IS in sys.path", file=_sys.stderr)
else:
    print(f"[CONFTEST] ✗ metadata-service NOT in sys.path!", file=_sys.stderr)

# NOW we can import pytest and other modules
import pytest

"""
Root conftest.py for Course Creator Platform

CRITICAL: This file MUST be at project root to ensure service paths
are added to sys.path BEFORE pytest imports test modules.

BUSINESS CONTEXT:
Tests need to import from multiple microservices without relative imports.
This conftest adds all service directories to Python path at module load time.

TECHNICAL APPROACH:
- Adds paths at MODULE IMPORT TIME (BEFORE any other imports)
- Path setup code runs FIRST, before even importing pytest
- Enables tests to use: "from domain.entities.X import Y"
"""

# Get project root directory
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# Add ALL services to path for imports - AT MODULE IMPORT TIME
# This MUST run before pytest tries to import test files
service_paths = [
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

# Add each service to Python path IMMEDIATELY
for service in service_paths:
    service_path = os.path.join(PROJECT_ROOT, 'services', service)
    if os.path.exists(service_path):
        # Insert at beginning to prioritize over system packages
        if service_path not in sys.path:
            sys.path.insert(0, service_path)

# Also add project root for top-level imports
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def pytest_configure(config):
    """
    Pytest hook: Called before test collection starts.

    This is the EARLIEST point where we can modify sys.path to ensure
    imports work when pytest loads test modules.
    """
    # Add ALL services to path for imports
    service_paths = [
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

    # Add each service to Python path
    for service in service_paths:
        service_path = os.path.join(PROJECT_ROOT, 'services', service)
        if os.path.exists(service_path):
            # Insert at beginning to prioritize over system packages
            if service_path not in sys.path:
                sys.path.insert(0, service_path)

    # Also add project root for top-level imports
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
