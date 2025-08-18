"""
Demo Service Data Access Layer

This package implements the Data Access Object (DAO) pattern for the demo service,
centralizing all demo data generation operations and session management.

Business Context:
The demo data access layer provides centralized management of all demonstration data
generation, session lifecycle management, and realistic platform simulation operations.
This service is essential for sales demonstrations, user training, stakeholder presentations,
and development testing, enabling authentic platform experiences without requiring actual
user data or system integrations. The DAO pattern ensures:
- Single source of truth for all demo data generation operations
- Enhanced consistency for demonstration experiences across different user roles
- Improved maintainability and testing capabilities for demo scenarios
- Clear separation between demo business logic and data generation concerns
- Better performance through optimized demo data generation patterns

Technical Architecture:
- DemoDAO: Centralized demo data generation and session management operations
- Session management: Time-limited demo sessions with automatic cleanup
- Role-based generation: Customized demo experiences for different user types
- Exception handling: Standardized error handling using shared platform exceptions
- Memory management: Efficient in-memory session storage with cleanup routines

Demo Capabilities:
- Multi-role experiences: Separate demo flows for instructors, students, and administrators
- Realistic data generation: Authentic educational content, user profiles, and analytics
- Session security: Time-limited access with validation and automatic cleanup
- Feature showcasing: Comprehensive demonstration of all platform capabilities
- Performance simulation: Realistic response times and data volumes for authentic experiences
- Privacy compliance: No real data storage, security-safe demonstration environment
"""

from .demo_dao import DemoDAO

__all__ = ['DemoDAO']