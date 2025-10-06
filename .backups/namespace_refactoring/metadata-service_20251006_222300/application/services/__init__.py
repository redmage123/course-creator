"""
Services for Metadata Management

Provides high-level business logic for metadata operations.
"""

from application.services.metadata_service import (
    MetadataService,
    MetadataServiceError,
    MetadataValidationError,
    BulkOperationError
)

__all__ = [
    'MetadataService',
    'MetadataServiceError',
    'MetadataValidationError',
    'BulkOperationError'
]
