"""
MetadataService - Business Logic Layer

BUSINESS REQUIREMENT:
Orchestrates metadata operations, enforces business rules, handles validation,
and coordinates between DAO and domain entities. Provides high-level API for
metadata management including search, enrichment, and bulk operations.

DESIGN PATTERN:
Service Layer pattern - encapsulates business logic and coordinates domain operations
"""

from typing import List, Optional, Dict, Any, Set
from uuid import UUID
import re
import asyncio

from metadata_service.domain.entities.metadata import Metadata, MetadataValidationError as EntityValidationError
from data_access.metadata_dao import (
    MetadataDAO,
    MetadataAlreadyExistsError,
    MetadataNotFoundError,
    MetadataDAOError
)


# Custom Exceptions
class MetadataServiceError(Exception):
    """Base exception for MetadataService errors"""
    pass


class MetadataValidationError(MetadataServiceError):
    """Raised when metadata validation fails"""
    pass


class BulkOperationError(MetadataServiceError):
    """Raised when bulk operation fails"""
    def __init__(self, message: str, successful_count: int, total_count: int):
        super().__init__(message)
        self.successful_count = successful_count
        self.total_count = total_count


class MetadataService:
    """
    Service layer for metadata operations

    RESPONSIBILITIES:
    - Orchestrate metadata CRUD operations
    - Enforce business rules and validation
    - Auto-extract tags and keywords
    - Enrich metadata with AI/NLP
    - Handle bulk operations
    - Coordinate search operations
    - Manage metadata lifecycle

    BUSINESS RULES:
    - Certain entity types require titles (content, course, track)
    - Tags are normalized to lowercase
    - Metadata dict must conform to schema for specific entity types
    - Search results are ranked by relevance
    """

    def __init__(self, metadata_dao: MetadataDAO):
        """
        Initialize MetadataService with DAO

        Args:
            metadata_dao: Data access object for metadata operations
        """
        self.dao = metadata_dao

        # Common keywords to extract as tags
        self.common_keywords = {
            'python', 'javascript', 'java', 'ruby', 'go', 'rust', 'typescript',
            'react', 'vue', 'angular', 'django', 'flask', 'fastapi', 'nodejs',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'linux', 'windows',
            'sql', 'nosql', 'mongodb', 'postgresql', 'redis', 'elasticsearch',
            'api', 'rest', 'graphql', 'microservices', 'devops', 'cicd',
            'machine learning', 'ai', 'deep learning', 'data science',
            'beginner', 'intermediate', 'advanced', 'expert',
            'web development', 'mobile', 'backend', 'frontend', 'fullstack'
        }

    async def create_metadata(
        self,
        metadata: Metadata,
        auto_extract_tags: bool = False,
        require_title: bool = False,
        connection=None
    ) -> Metadata:
        """
        Create new metadata record

        BUSINESS LOGIC:
        - Validates metadata entity
        - Optionally auto-extracts tags from title/description
        - Enforces business rules (e.g., title requirements)
        - Delegates to DAO for persistence

        Args:
            metadata: Metadata entity to create
            auto_extract_tags: Whether to auto-extract tags from text
            require_title: Whether title is required
            connection: Optional database connection for transactions

        Returns:
            Created metadata with generated ID

        Raises:
            MetadataValidationError: If validation fails
            MetadataServiceError: If metadata already exists
        """
        # Validate business rules
        if require_title and not metadata.title:
            raise MetadataValidationError(
                f"Title is required for entity_type '{metadata.entity_type}'"
            )

        # Auto-extract tags if requested
        if auto_extract_tags:
            extracted_tags = await self.extract_tags(
                f"{metadata.title or ''} {metadata.description or ''}"
            )
            # Merge with existing tags
            existing_tags = set(metadata.tags)
            all_tags = existing_tags.union(set(extracted_tags))
            metadata.tags = list(all_tags)

        # Delegate to DAO
        try:
            return await self.dao.create(metadata, connection=connection)
        except MetadataAlreadyExistsError as e:
            raise MetadataServiceError(
                f"Metadata already exists for entity_id={metadata.entity_id}, "
                f"entity_type={metadata.entity_type}"
            ) from e
        except MetadataDAOError as e:
            raise MetadataServiceError(f"Failed to create metadata: {str(e)}") from e

    async def get_metadata_by_id(self, metadata_id: UUID) -> Optional[Metadata]:
        """
        Retrieve metadata by ID

        Args:
            metadata_id: Metadata UUID

        Returns:
            Metadata entity or None if not found
        """
        return await self.dao.get_by_id(metadata_id)

    async def get_metadata_by_entity(
        self,
        entity_id: UUID,
        entity_type: str
    ) -> Optional[Metadata]:
        """
        Retrieve metadata by entity_id and entity_type

        PRIMARY USE CASE:
        Get metadata for specific entity (course, content, etc.)

        Args:
            entity_id: Entity UUID
            entity_type: Entity type

        Returns:
            Metadata entity or None if not found
        """
        return await self.dao.get_by_entity(entity_id, entity_type)

    async def get_or_create_metadata(
        self,
        entity_id: UUID,
        entity_type: str,
        defaults: Optional[Dict[str, Any]] = None
    ) -> Metadata:
        """
        Get existing metadata or create if doesn't exist

        COMMON PATTERN:
        Ensure metadata exists for entity

        Args:
            entity_id: Entity UUID
            entity_type: Entity type
            defaults: Default values for creation

        Returns:
            Existing or newly created metadata
        """
        # Try to get existing
        existing = await self.dao.get_by_entity(entity_id, entity_type)
        if existing:
            return existing

        # Create new with defaults
        metadata_dict = defaults or {}
        metadata = Metadata(
            entity_id=entity_id,
            entity_type=entity_type,
            **metadata_dict
        )

        return await self.dao.create(metadata)

    async def list_metadata_by_type(
        self,
        entity_type: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Metadata]:
        """
        List all metadata for entity type

        Args:
            entity_type: Entity type to filter by
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of metadata entities
        """
        return await self.dao.list_by_entity_type(entity_type, limit=limit, offset=offset)

    async def update_metadata(
        self,
        metadata: Metadata,
        validate_title: bool = False,
        connection=None
    ) -> Metadata:
        """
        Update existing metadata

        BUSINESS LOGIC:
        - Validates business rules before update
        - Ensures updated_at is refreshed
        - Delegates to DAO

        Args:
            metadata: Metadata entity with updates
            validate_title: Whether to validate title is not empty
            connection: Optional database connection

        Returns:
            Updated metadata

        Raises:
            MetadataValidationError: If validation fails
            MetadataServiceError: If update fails
        """
        # Validate business rules
        if validate_title and not metadata.title:
            raise MetadataValidationError("Title cannot be empty")

        # Delegate to DAO
        try:
            return await self.dao.update(metadata, connection=connection)
        except MetadataNotFoundError as e:
            raise MetadataServiceError(f"Metadata not found: {str(e)}") from e
        except MetadataDAOError as e:
            raise MetadataServiceError(f"Failed to update metadata: {str(e)}") from e

    async def partial_update_metadata(
        self,
        metadata_id: UUID,
        updates: Dict[str, Any]
    ) -> Metadata:
        """
        Partially update metadata fields

        BUSINESS LOGIC:
        Update only specified fields, preserve others

        Args:
            metadata_id: Metadata UUID
            updates: Dictionary of fields to update

        Returns:
            Updated metadata

        Raises:
            MetadataServiceError: If metadata not found
        """
        # Get existing metadata
        metadata = await self.dao.get_by_id(metadata_id)
        if not metadata:
            raise MetadataServiceError(f"Metadata not found with id={metadata_id}")

        # Apply updates
        metadata.update(**updates)

        # Save
        return await self.dao.update(metadata)

    async def delete_metadata(self, metadata_id: UUID) -> bool:
        """
        Delete metadata by ID

        Args:
            metadata_id: Metadata UUID

        Returns:
            True if deleted, False if not found
        """
        return await self.dao.delete(metadata_id)

    async def search_metadata(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        required_tags: Optional[List[str]] = None,
        limit: int = 20,
        rank_by_relevance: bool = True
    ) -> List[Metadata]:
        """
        Full-text search on metadata

        SEARCH STRATEGY:
        1. Perform database full-text search
        2. Optionally filter by required tags
        3. Return ranked results

        Args:
            query: Search query text
            entity_types: Optional entity type filter
            required_tags: Optional required tags filter
            limit: Maximum results
            rank_by_relevance: Whether to rank by relevance (already done by DB)

        Returns:
            List of matching metadata ranked by relevance
        """
        # Perform full-text search
        results = await self.dao.search(query, entity_types=entity_types, limit=limit)

        # Filter by required tags if specified
        if required_tags:
            results = [
                r for r in results
                if all(tag in r.tags for tag in required_tags)
            ]

        return results

    async def get_by_tags(
        self,
        tags: List[str],
        entity_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Metadata]:
        """
        Retrieve metadata by tags

        Args:
            tags: List of tags (must have all)
            entity_type: Optional entity type filter
            limit: Maximum results

        Returns:
            List of metadata with matching tags
        """
        return await self.dao.get_by_tags(tags, entity_type=entity_type, limit=limit)

    async def bulk_create_metadata(
        self,
        metadata_list: List[Metadata],
        stop_on_error: bool = False
    ) -> List[Metadata]:
        """
        Create multiple metadata records

        BULK OPERATION:
        Efficient batch creation with error handling

        Args:
            metadata_list: List of metadata to create
            stop_on_error: Whether to stop on first error

        Returns:
            List of successfully created metadata

        Raises:
            BulkOperationError: If any creation fails and stop_on_error=True
        """
        created = []
        errors = []

        for i, metadata in enumerate(metadata_list):
            try:
                result = await self.dao.create(metadata)
                created.append(result)
            except Exception as e:
                errors.append((i, str(e)))
                if stop_on_error:
                    raise BulkOperationError(
                        f"Bulk create failed at index {i}: {str(e)}. "
                        f"Created {len(created)} of {len(metadata_list)} records.",
                        successful_count=len(created),
                        total_count=len(metadata_list)
                    ) from e

        # If not stopping on error, still raise if all failed
        if errors and not created:
            raise BulkOperationError(
                f"All {len(metadata_list)} bulk create operations failed",
                successful_count=0,
                total_count=len(metadata_list)
            )

        return created

    async def extract_tags(self, text: str, max_tags: int = 10) -> List[str]:
        """
        Extract tags from text using keyword matching

        AUTO-TAGGING:
        Simple keyword extraction (can be enhanced with NLP/AI)

        Args:
            text: Text to extract tags from
            max_tags: Maximum number of tags

        Returns:
            List of extracted tags
        """
        if not text:
            return []

        # Normalize text
        text_lower = text.lower()

        # Find matching keywords
        found_tags = []
        for keyword in self.common_keywords:
            if keyword in text_lower:
                found_tags.append(keyword.replace(' ', '-'))

        # Return up to max_tags
        return found_tags[:max_tags]

    async def enrich_metadata(self, metadata: Metadata) -> Metadata:
        """
        Enrich metadata with extracted information

        ENRICHMENT:
        Extract topics, keywords, difficulty from content
        (Placeholder for AI/NLP integration)

        Args:
            metadata: Metadata to enrich

        Returns:
            Enriched metadata
        """
        # Auto-extract tags if not present
        if not metadata.tags and (metadata.title or metadata.description):
            text = f"{metadata.title or ''} {metadata.description or ''}"
            metadata.tags = await self.extract_tags(text)

        # Update in database
        if metadata.id:
            return await self.dao.update(metadata)

        return metadata

    async def validate_metadata_schema(
        self,
        metadata: Metadata,
        strict: bool = False
    ) -> bool:
        """
        Validate metadata schema

        VALIDATION:
        Ensure metadata dict conforms to expected schema

        Args:
            metadata: Metadata to validate
            strict: Whether to enforce strict validation

        Returns:
            True if valid

        Raises:
            MetadataValidationError: If strict=True and validation fails
        """
        # Check educational metadata structure
        if 'educational' in metadata.metadata:
            educational = metadata.metadata['educational']

            # Validate difficulty level
            if 'difficulty' in educational:
                valid_levels = ['beginner', 'intermediate', 'advanced', 'expert']
                if educational['difficulty'] not in valid_levels:
                    if strict:
                        raise MetadataValidationError(
                            f"Invalid difficulty level: {educational['difficulty']}. "
                            f"Must be one of: {', '.join(valid_levels)}"
                        )
                    return False

            # Validate topics is a list
            if 'topics' in educational:
                if not isinstance(educational['topics'], list):
                    if strict:
                        raise MetadataValidationError("Topics must be a list")
                    return False

        return True
