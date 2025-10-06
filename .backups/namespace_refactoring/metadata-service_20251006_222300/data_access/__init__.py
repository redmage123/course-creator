"""
Data Access Layer for Metadata Service

Provides database access objects (DAOs) for metadata operations.
"""

from data_access.metadata_dao import (
    MetadataDAO,
    MetadataDAOError,
    MetadataAlreadyExistsError,
    MetadataNotFoundError
)

__all__ = [
    'MetadataDAO',
    'MetadataDAOError',
    'MetadataAlreadyExistsError',
    'MetadataNotFoundError'
]
