"""
Root conftest.py for Course Creator Platform

CRITICAL: This file MUST be at project root to ensure service paths
are added to sys.path BEFORE pytest imports test modules.
"""

import os
import sys

# Add ALL services to path for imports
# This runs at module import time, before pytest loads test files
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
    'organization-management',
    'rag-service',
    'user-management'
]

for service in service_paths:
    service_path = os.path.abspath(os.path.join(os.path.dirname(__file__), f'services/{service}'))
    if os.path.exists(service_path) and service_path not in sys.path:
        sys.path.insert(0, service_path)
