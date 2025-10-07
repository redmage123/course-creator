"""
API Routes Module for Analytics Service

This package contains all FastAPI route handlers organized by domain.

BUSINESS CONTEXT:
Each route module focuses on a specific aspect of educational analytics,
following the Single Responsibility Principle.

ARCHITECTURE:
- activity_routes: Student learning activity tracking
- lab_routes: Hands-on coding lab analytics
- quiz_routes: Assessment and quiz performance
- progress_routes: Learning progress and mastery tracking
- analytics_routes: Comprehensive learning analytics
- reporting_routes: Report generation and export

SOLID PRINCIPLES:
- Single Responsibility: Each module handles one analytics domain
- Open/Closed: New routes can be added without modifying existing
- Dependency Inversion: Routes depend on service interfaces
"""

# Import router from parent routes.py module
import sys
from pathlib import Path

# Add parent directory to import the sibling routes.py file
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from routes import router

__all__ = ['router']
