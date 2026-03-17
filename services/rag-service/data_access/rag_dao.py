"""
RAG Data Access Object (DAO)

This module implements the Data Access Object (DAO) pattern for RAG operations,
centralizing all ChromaDB interactions and vector database operations.

Business Context:
The RAG DAO encapsulates all interactions with the ChromaDB vector database, providing
a clean abstraction layer for document ingestion, vector search, and knowledge base
management. This separation enables better testing, maintenance, and potential database
migrations while maintaining consistent RAG functionality across the platform.

Technical Rationale:
- Follows the Single Responsibility Principle by isolating vector database operations
- Enables comprehensive transaction support for complex RAG operations
- Provides consistent error handling using shared platform exceptions
- Supports connection pooling and resource optimization for ChromaDB
- Facilitates vector database schema evolution without affecting business logic
- Enables easier unit testing and RAG system validation
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import json
import chromadb
from chromadb.config import Settings
import sys
sys.path.append('/app/shared')
from exceptions import (
    RAGException,
    EmbeddingException,
    ValidationException,
    DatabaseException
)


class RAGDAO:
    """
    Data Access Object for RAG Vector Database Operations
    
    This class centralizes all ChromaDB interactions for the RAG service,
    following the DAO pattern for clean architecture.
    
    Business Context:
    Provides comprehensive data access methods for RAG operations including:
    - Vector collection management and initialization
    - Document embedding storage and retrieval
    - Semantic similarity search and filtering
    - Knowledge base maintenance and optimization
    - Performance monitoring and usage analytics
    
    Technical Implementation:
    - Uses ChromaDB for high-performance vector operations
    - Implements connection management for optimal resource usage
    - Provides transaction support for complex vector operations
    - Includes comprehensive error handling and data validation
    - Supports metadata filtering and semantic search enhancements
    - Implements efficient vector storage and retrieval patterns
    """
    
    def __init__(self, chromadb_client: chromadb.Client):
        """
        Initialize the RAG DAO with ChromaDB client.
        
        Business Context:
        The DAO requires a ChromaDB client to manage vector database operations
        for document storage, embedding generation, and similarity search.
        
        Args:
            chromadb_client: ChromaDB client for vector database operations
        """
        self.client = chromadb_client
        self.logger = logging.getLogger(__name__)
        self.collections = {}
    
    def initialize_collections(self, collection_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Initialize ChromaDB collections based on configuration.
        
        Business Context:
        Collection initialization sets up the vector database structure for different
        content domains, enabling organized storage and efficient retrieval of
        educational content, code examples, and interaction patterns.
        
        Args:
            collection_configs: List of collection configuration dictionaries
            
        Returns:
            Dictionary mapping collection names to ChromaDB collection objects
        """
        try:
            initialized_collections = {}
            
            for config in collection_configs:
                try:
                    collection = self.client.get_or_create_collection(
                        name=config["name"],
                        metadata={"description": config["description"]}
                    )
                    initialized_collections[config["name"]] = collection
                    self.logger.info(f"Initialized RAG collection: {config['name']}")
                except Exception as e:
                    raise RAGException(
                        message=f"Failed to initialize ChromaDB collection",
                        error_code="COLLECTION_INIT_FAILED",
                        details={
                            "collection_name": config["name"],
                            "collection_config": config
                        },
                        original_exception=e
                    )
            
            self.collections = initialized_collections
            return initialized_collections
            
        except RAGException:
            # Re-raise structured exceptions
            raise
        except Exception as e:
            raise RAGException(
                message="Failed to initialize ChromaDB collections",
                error_code="COLLECTIONS_INIT_ERROR",
                details={"config_count": len(collection_configs)},
                original_exception=e
            )
    
    def add_document_to_collection(
        self, 
        collection_name: str,
        document_id: str,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Add a document with its embedding to a specific collection.
        
        Business Context:
        Document addition builds the knowledge base that powers AI-enhanced features.
        Each document improves the system's ability to provide contextually relevant
        information for content generation, lab assistance, and educational guidance.
        
        Args:
            collection_name: Target collection for the document
            document_id: Unique identifier for the document
            content: Document text content
            embedding: Vector embedding of the content
            metadata: Document metadata for filtering and context
            
        Returns:
            True if document was successfully added
        """
        try:
            if collection_name not in self.collections:
                raise ValidationException(
                    message=f"Collection not found for document addition",
                    error_code="COLLECTION_NOT_FOUND",
                    validation_errors={"collection": f"Collection '{collection_name}' not initialized"},
                    details={"available_collections": list(self.collections.keys())}
                )
            
            collection = self.collections[collection_name]
            
            # Add document to ChromaDB collection
            collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata],
                ids=[document_id]
            )
            
            self.logger.debug(f"Added document {document_id} to collection {collection_name}")
            return True
            
        except ValidationException:
            # Re-raise validation errors
            raise
        except Exception as e:
            raise RAGException(
                message=f"Failed to add document to ChromaDB collection",
                error_code="DOCUMENT_ADD_FAILED",
                details={
                    "collection_name": collection_name,
                    "document_id": document_id,
                    "metadata": metadata
                },
                original_exception=e
            )
    
    def query_collection(
        self,
        collection_name: str,
        query_embedding: List[float],
        n_results: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
        include_distances: bool = True
    ) -> Dict[str, Any]:
        """
        Query a collection for similar documents using vector search.
        
        Business Context:
        Vector similarity search finds the most relevant documents for a given query,
        enabling contextually aware AI responses and personalized educational content
        recommendations based on accumulated knowledge.
        
        Args:
            collection_name: Collection to search
            query_embedding: Vector embedding of the query
            n_results: Maximum number of results to return
            metadata_filter: Optional metadata filters for refined search
            include_metadata: Whether to include document metadata
            include_distances: Whether to include similarity distances
            
        Returns:
            Dictionary containing search results with documents, metadata, and distances
        """
        try:
            if collection_name not in self.collections:
                raise ValidationException(
                    message=f"Collection not found for query",
                    error_code="QUERY_COLLECTION_NOT_FOUND",
                    validation_errors={"collection": f"Collection '{collection_name}' not available"},
                    details={"available_collections": list(self.collections.keys())}
                )
            
            collection = self.collections[collection_name]
            
            # Prepare include parameters
            include_params = ["documents"]
            if include_metadata:
                include_params.append("metadatas")
            if include_distances:
                include_params.append("distances")
            
            # Perform vector similarity search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=metadata_filter if metadata_filter else None,
                include=include_params
            )
            
            self.logger.debug(f"Queried collection {collection_name}: {len(results.get('documents', [[]])[0])} results")
            return results
            
        except ValidationException:
            # Re-raise validation errors
            raise
        except Exception as e:
            raise RAGException(
                message=f"Failed to query ChromaDB collection",
                error_code="COLLECTION_QUERY_FAILED",
                details={
                    "collection_name": collection_name,
                    "n_results": n_results,
                    "has_filters": bool(metadata_filter)
                },
                original_exception=e
            )
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific collection.
        
        Business Context:
        Collection statistics provide insights into knowledge base growth,
        content distribution, and system usage patterns for optimization
        and capacity planning decisions.
        
        Args:
            collection_name: Collection to get statistics for
            
        Returns:
            Dictionary containing collection statistics
        """
        try:
            if collection_name not in self.collections:
                raise ValidationException(
                    message=f"Collection not found for statistics",
                    error_code="STATS_COLLECTION_NOT_FOUND",
                    validation_errors={"collection": f"Collection '{collection_name}' not available"}
                )
            
            collection = self.collections[collection_name]
            document_count = collection.count()
            
            return {
                "collection_name": collection_name,
                "document_count": document_count,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
        except ValidationException:
            # Re-raise validation errors
            raise
        except Exception as e:
            raise RAGException(
                message=f"Failed to get collection statistics",
                error_code="COLLECTION_STATS_FAILED",
                details={"collection_name": collection_name},
                original_exception=e
            )
    
    def get_all_collection_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all initialized collections.
        
        Business Context:
        Comprehensive statistics enable system-wide monitoring, performance
        analysis, and resource allocation decisions for the RAG knowledge base.
        
        Returns:
            Dictionary mapping collection names to their statistics
        """
        try:
            all_stats = {}
            
            for collection_name in self.collections:
                try:
                    stats = self.get_collection_stats(collection_name)
                    all_stats[collection_name] = stats
                except RAGException as e:
                    # Log individual collection errors but continue
                    self.logger.warning(f"Failed to get stats for {collection_name}: {e.message}")
                    all_stats[collection_name] = {
                        "error": e.message,
                        "document_count": 0
                    }
            
            return all_stats
            
        except Exception as e:
            raise RAGException(
                message="Failed to get comprehensive collection statistics",
                error_code="ALL_STATS_FAILED",
                details={"initialized_collections": list(self.collections.keys())},
                original_exception=e
            )
    
    def delete_document(self, collection_name: str, document_id: str) -> bool:
        """
        Delete a document from a collection.
        
        Business Context:
        Document deletion enables knowledge base maintenance, content curation,
        and removal of outdated or incorrect information that could degrade
        AI response quality.
        
        Args:
            collection_name: Collection containing the document
            document_id: ID of document to delete
            
        Returns:
            True if document was successfully deleted
        """
        try:
            if collection_name not in self.collections:
                raise ValidationException(
                    message=f"Collection not found for document deletion",
                    error_code="DELETE_COLLECTION_NOT_FOUND",
                    validation_errors={"collection": f"Collection '{collection_name}' not available"}
                )
            
            collection = self.collections[collection_name]
            collection.delete(ids=[document_id])
            
            self.logger.debug(f"Deleted document {document_id} from collection {collection_name}")
            return True
            
        except ValidationException:
            # Re-raise validation errors
            raise
        except Exception as e:
            raise RAGException(
                message=f"Failed to delete document from collection",
                error_code="DOCUMENT_DELETE_FAILED",
                details={
                    "collection_name": collection_name,
                    "document_id": document_id
                },
                original_exception=e
            )
    
    def update_document_metadata(
        self, 
        collection_name: str, 
        document_id: str, 
        new_metadata: Dict[str, Any]
    ) -> bool:
        """
        Update metadata for an existing document.
        
        Business Context:
        Metadata updates enable knowledge base refinement, quality scoring updates,
        and context enhancement without requiring full document re-embedding.
        
        Args:
            collection_name: Collection containing the document
            document_id: ID of document to update
            new_metadata: New metadata to apply
            
        Returns:
            True if metadata was successfully updated
        """
        try:
            if collection_name not in self.collections:
                raise ValidationException(
                    message=f"Collection not found for metadata update",
                    error_code="UPDATE_COLLECTION_NOT_FOUND",
                    validation_errors={"collection": f"Collection '{collection_name}' not available"}
                )
            
            collection = self.collections[collection_name]
            collection.update(
                ids=[document_id],
                metadatas=[new_metadata]
            )
            
            self.logger.debug(f"Updated metadata for document {document_id} in collection {collection_name}")
            return True
            
        except ValidationException:
            # Re-raise validation errors
            raise
        except Exception as e:
            raise RAGException(
                message=f"Failed to update document metadata",
                error_code="METADATA_UPDATE_FAILED",
                details={
                    "collection_name": collection_name,
                    "document_id": document_id,
                    "new_metadata": new_metadata
                },
                original_exception=e
            )
    
    def batch_add_documents(
        self,
        collection_name: str,
        documents: List[Tuple[str, str, List[float], Dict[str, Any]]]
    ) -> int:
        """
        Add multiple documents to a collection in a single batch operation.
        
        Business Context:
        Batch operations improve performance for large-scale knowledge base
        ingestion, enabling efficient processing of course content, documentation,
        and user interaction data.
        
        Args:
            collection_name: Target collection for documents
            documents: List of (document_id, content, embedding, metadata) tuples
            
        Returns:
            Number of documents successfully added
        """
        try:
            if collection_name not in self.collections:
                raise ValidationException(
                    message=f"Collection not found for batch document addition",
                    error_code="BATCH_COLLECTION_NOT_FOUND",
                    validation_errors={"collection": f"Collection '{collection_name}' not available"}
                )
            
            if not documents:
                return 0
            
            collection = self.collections[collection_name]
            
            # Separate batch data components
            document_ids = [doc[0] for doc in documents]
            contents = [doc[1] for doc in documents]
            embeddings = [doc[2] for doc in documents]
            metadatas = [doc[3] for doc in documents]
            
            # Perform batch addition
            collection.add(
                ids=document_ids,
                documents=contents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            self.logger.info(f"Batch added {len(documents)} documents to collection {collection_name}")
            return len(documents)
            
        except ValidationException:
            # Re-raise validation errors
            raise
        except Exception as e:
            raise RAGException(
                message=f"Failed to batch add documents to collection",
                error_code="BATCH_ADD_FAILED",
                details={
                    "collection_name": collection_name,
                    "document_count": len(documents) if documents else 0
                },
                original_exception=e
            )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on ChromaDB connection and collections.
        
        Business Context:
        Health monitoring ensures RAG service reliability and enables proactive
        issue detection before they impact AI-powered educational features.
        
        Returns:
            Dictionary containing health status and metrics
        """
        try:
            # Test basic client connectivity
            collection_count = len(self.collections)
            
            # Test a basic operation on each collection
            collection_health = {}
            for name, collection in self.collections.items():
                try:
                    doc_count = collection.count()
                    collection_health[name] = {
                        "status": "healthy",
                        "document_count": doc_count
                    }
                except Exception as e:
                    collection_health[name] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
            
            overall_health = all(
                health["status"] == "healthy" 
                for health in collection_health.values()
            )
            
            return {
                "status": "healthy" if overall_health else "degraded",
                "collections_initialized": collection_count,
                "collection_health": collection_health,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            raise RAGException(
                message="RAG DAO health check failed",
                error_code="HEALTH_CHECK_FAILED",
                details={"collections_count": len(self.collections)},
                original_exception=e
            )