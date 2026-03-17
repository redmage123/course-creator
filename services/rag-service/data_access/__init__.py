"""
RAG Data Access Layer

This package implements the Data Access Object (DAO) pattern for the RAG service,
centralizing all ChromaDB vector database interactions and operations.

Business Context:
The RAG data access layer provides centralized management of all vector database operations
including document embedding storage, similarity search, and knowledge base maintenance.
This service is the foundation of AI-enhanced features across the Course Creator Platform,
enabling contextually aware content generation, personalized learning assistance, and
intelligent educational recommendations. The DAO pattern ensures:
- Single source of truth for all vector database operations
- Enhanced data consistency for RAG knowledge base management
- Improved maintainability and testing capabilities for vector operations
- Clear separation between RAG business logic and data access concerns
- Better performance through optimized vector storage and retrieval patterns

Technical Architecture:
- RAGDAO: Centralized ChromaDB operations for all vector database interactions
- Vector optimization: Efficient embedding storage and similarity search
- Transaction support: Ensures data consistency for complex RAG operations
- Exception handling: Standardized error handling using shared platform exceptions
- Connection management: Optimized ChromaDB resource usage and connection pooling

RAG Capabilities:
- Document ingestion: Vector embedding generation and storage
- Semantic search: Intelligent context retrieval with metadata filtering
- Knowledge management: Collection organization and maintenance
- Performance optimization: Batch operations and caching integration
- Health monitoring: System reliability and performance tracking
- Analytics support: Usage metrics and knowledge base insights
"""

from .rag_dao import RAGDAO

__all__ = ['RAGDAO']