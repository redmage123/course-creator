"""
Lab Manager API Endpoints

This package contains modular API router implementations following SOLID principles.
Each router module focuses on a specific domain of lab container management.

Modules:
- lab_lifecycle_endpoints: Lab creation, management, and lifecycle operations
- rag_assistant_endpoints: RAG-enhanced programming assistance for labs
- jupyter_proxy_endpoints: Jupyter notebook content access for AI integration

Architecture:
Following the Single Responsibility Principle, each router module handles
a specific domain of lab management, promoting clean separation of concerns
and maintainable code organization.
"""

from .lab_lifecycle_endpoints import router as lab_lifecycle_router
from .rag_assistant_endpoints import router as rag_assistant_router
from .jupyter_proxy_endpoints import router as jupyter_proxy_router

__all__ = ['lab_lifecycle_router', 'rag_assistant_router', 'jupyter_proxy_router']
