"""
Course Management Service Test Configuration

BUSINESS CONTEXT:
Provides fixtures and path setup for course-management service tests.
Ensures proper module imports for DAO and domain entities.
"""

import sys
import os
from pathlib import Path

# Add course-management service root to Python path
service_root = Path(__file__).parent.parent
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))
