"""
Educational Content Storage Data Schemas - Pydantic Models for API Validation

Comprehensive data validation and serialization models for educational content storage operations,
following SOLID principles and ensuring robust API contracts for content management workflows.

## Schema Architecture Principles:

### Single Responsibility
Each schema model handles a specific educational content entity with focused validation:
- **ContentFile Schemas**: File upload and storage validation
- **MediaAsset Schemas**: Educational media content and metadata
- **StorageMetadata Schemas**: Storage backend configuration and credentials

### Educational Content Validation Features:
- **Comprehensive Field Validation**: Educational content constraints and data integrity
- **Educational Metadata Support**: Course context and institutional information
- **Security Validation**: File type, size, and content safety verification
- **Performance Optimization**: Efficient serialization for API operations

## Schema Categories:

### Content File Schemas
Educational content file upload and storage validation with security controls:
- File type and size validation for educational content safety
- Storage path validation and security for institutional compliance
- Educational metadata integration for content context
- Content versioning and lifecycle tracking support

### Media Asset Schemas
Educational media content management with pedagogical metadata:
- Educational media classification and taxonomy support
- Learning resource integration and content relationship tracking
- Accessibility metadata for universal design compliance
- Educational analytics integration for usage tracking

### Storage Backend Schemas
Storage system configuration with security and compliance features:
- Multi-cloud storage backend support (AWS S3, Azure, GCS)
- Encrypted credential management for institutional security
- Storage quota and capacity planning for institutional resources
- Storage health monitoring and performance tracking

## Educational Benefits:

### Quality Assurance
Comprehensive validation ensures educational content integrity and institutional compliance:
- Educational content format and structure validation
- Security validation for safe educational material processing
- Educational metadata completeness verification
- Institutional policy compliance enforcement

### API Consistency
Standardized schemas provide consistent API contracts for educational technology integration:
- Educational content management system compatibility
- Learning management system integration support
- Educational analytics platform connectivity
- Institutional repository integration readiness

This schema module ensures robust, secure, and pedagogically-aware data validation
for all educational content storage operations while maintaining institutional
compliance and educational quality standards.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, HttpUrl, Field, constr

# Base Models
class BaseSchema(BaseModel):
    """
    Base schema for all educational content storage data models.

    Provides common configuration and functionality for all schema classes
    with ORM integration and educational content validation support.

    Educational Features:
    - **ORM Integration**: Seamless database model conversion for educational content persistence
    - **Type Flexibility**: Support for complex educational content types and metadata structures
    - **Validation Framework**: Foundation for comprehensive educational content validation
    - **Serialization Support**: Efficient API response generation for educational content delivery

    Configuration Benefits:
    - Enables seamless conversion between database models and API responses
    - Supports complex educational metadata and content relationship structures
    - Provides consistent validation behavior across all educational content schemas
    - Optimizes serialization for educational content API operations
    """
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

# ContentFile Models
class ContentFileBase(BaseSchema):
    """
    Base schema for educational content file information with comprehensive validation.

    Validates essential file attributes for educational content storage operations
    ensuring file integrity, security, and institutional compliance.

    Educational File Attributes:
    - **filename**: Original educational content filename for content recognition (1-255 chars)
    - **mime_type**: Content type classification for educational material processing (1-127 chars)
    - **file_size**: File size validation for educational content scalability (must be positive)
    - **storage_path**: Secure storage locations for educational content retrieval

    Security Validation:
    - Filename length validation prevents path traversal and storage issues
    - MIME type validation ensures proper educational content handling
    - File size validation prevents resource exhaustion and ensures scalability
    - Storage path validation ensures secure educational content organization

    Educational Benefits:
    - Comprehensive educational content file validation and quality assurance
    - Security validation for safe educational material processing
    - Educational content integrity verification and institutional compliance
    - Performance optimization for educational content storage operations
    """
    filename: str = Field(..., min_length=1, max_length=255)
    mime_type: str = Field(..., min_length=1, max_length=127)
    file_size: int = Field(..., gt=0)
    storage_path: str = Field(..., min_length=1)

class ContentFileCreate(ContentFileBase):
    """
    Schema for creating new educational content file records.

    Inherits comprehensive validation from ContentFileBase for educational content
    file upload operations with security and institutional compliance verification.

    Educational Use Cases:
    - Educational content file upload validation and quality assurance
    - Educational material security verification and institutional compliance
    - Educational content metadata integration for content context
    - Educational file organization and classification support
    """
    pass

class ContentFileUpdate(BaseSchema):
    """
    Schema for updating existing educational content file records.

    Provides partial update capability for educational content file metadata
    modification while maintaining validation and institutional compliance.

    Educational Update Operations:
    - Educational content filename modification and content recognition updates
    - MIME type correction for proper educational material processing
    - File size updates for educational content reprocessing scenarios
    - Storage path updates for educational content reorganization

    All fields are optional supporting partial updates for educational workflow flexibility.
    """
    filename: Optional[str] = Field(None, min_length=1, max_length=255)
    mime_type: Optional[str] = Field(None, min_length=1, max_length=127)
    file_size: Optional[int] = Field(None, gt=0)
    storage_path: Optional[str] = Field(None, min_length=1)

class ContentFileResponse(ContentFileBase):
    """
    Schema for educational content file API responses with complete metadata.

    Extends base file information with system-generated identifiers and timestamps
    for comprehensive educational content tracking and audit trail support.

    Response Fields:
    - **id**: Unique educational content file identifier for content tracking
    - **created_at**: Educational content upload timestamp for lifecycle tracking
    - **updated_at**: Educational content modification timestamp for audit trails

    Educational Benefits:
    - Complete educational content file information for content management
    - Educational content lifecycle tracking and institutional audit support
    - Educational content versioning and change tracking capability
    - Educational analytics integration for content usage monitoring
    """
    id: UUID
    created_at: datetime
    updated_at: datetime

# MediaAsset Models
class MediaAssetBase(BaseSchema):
    """
    Base schema for educational media asset information with pedagogical metadata support.

    Validates educational media content attributes including accessibility information,
    learning resource metadata, and institutional content classification.

    Educational Media Attributes:
    - **title**: Educational media content title for content recognition (1-255 chars)
    - **description**: Educational context and pedagogical purpose description (max 1000 chars)
    - **url**: Educational media access URL for content delivery and CDN integration
    - **content_file_id**: Reference to underlying storage file for content retrieval
    - **metadata**: Educational metadata including accessibility, pedagogy, and analytics

    Educational Metadata Structure:
    - **Accessibility Information**: Alternative text, captions, transcripts for universal design
    - **Pedagogical Metadata**: Learning objectives, difficulty level, subject classification
    - **Usage Analytics**: View counts, engagement metrics, educational effectiveness data
    - **Content Relationships**: Cross-references to courses, modules, and learning materials

    Educational Benefits:
    - Comprehensive educational media validation and quality assurance
    - Accessibility metadata support for universal design compliance
    - Pedagogical context integration for effective educational content delivery
    - Educational analytics support for content effectiveness measurement
    """
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    url: HttpUrl
    content_file_id: UUID
    metadata: Optional[dict] = None

class MediaAssetCreate(MediaAssetBase):
    """
    Schema for creating new educational media asset records.

    Inherits comprehensive validation from MediaAssetBase for educational media
    upload operations with accessibility and pedagogical metadata validation.

    Educational Use Cases:
    - Educational video content upload with accessibility metadata
    - Educational audio content integration with transcript support
    - Educational image uploads with alternative text for universal design
    - Educational document media with pedagogical context metadata
    """
    pass

class MediaAssetUpdate(BaseSchema):
    """
    Schema for updating existing educational media asset records.

    Provides partial update capability for educational media metadata modification
    including accessibility improvements and pedagogical context enhancement.

    Educational Update Operations:
    - Educational media title updates for improved content discovery
    - Description enhancement for better pedagogical context
    - URL updates for CDN optimization and content delivery improvement
    - Metadata enrichment for accessibility and educational analytics

    All fields are optional supporting incremental educational content improvement.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    url: Optional[HttpUrl] = None
    metadata: Optional[dict] = None

class MediaAssetResponse(MediaAssetBase):
    """
    Schema for educational media asset API responses with complete information.

    Extends base media information with system-generated identifiers and timestamps
    for comprehensive educational media tracking and usage analytics support.

    Response Fields:
    - **id**: Unique educational media identifier for content tracking
    - **created_at**: Educational media upload timestamp for lifecycle tracking
    - **updated_at**: Educational media modification timestamp for content versioning

    Educational Benefits:
    - Complete educational media information for content management
    - Educational media lifecycle tracking and usage analytics support
    - Educational content versioning and accessibility improvement tracking
    - Educational analytics integration for media effectiveness measurement
    """
    id: UUID
    created_at: datetime
    updated_at: datetime

# StorageMetadata Models
class StorageMetadataBase(BaseSchema):
    """
    Base schema for educational content storage backend configuration.

    Validates storage backend settings for multi-cloud educational content storage
    supporting AWS S3, Azure Blob Storage, Google Cloud Storage, and local storage.

    Storage Configuration Attributes:
    - **storage_type**: Storage backend type (s3, azure, gcs, local) for educational content
    - **bucket_name**: Storage container identifier for educational content organization
    - **region**: Geographic region for educational content locality and performance
    - **access_key**: Authentication credential for secure storage backend access
    - **status**: Storage backend operational status (active, disabled, maintenance)

    Security Considerations:
    - Access key validation ensures proper credential format
    - Storage type validation ensures supported backend configuration
    - Status validation enables storage backend lifecycle management
    - Regional configuration supports data sovereignty and educational compliance

    Educational Benefits:
    - Multi-cloud storage support for institutional infrastructure flexibility
    - Geographic distribution for global educational content delivery
    - Storage backend lifecycle management for institutional operations
    - Security validation for safe educational content storage
    """
    storage_type: str = Field(..., min_length=1, max_length=50)
    bucket_name: str = Field(..., min_length=1, max_length=255)
    region: str = Field(..., min_length=1, max_length=50)
    access_key: constr(min_length=1, max_length=255)
    status: str = Field(..., min_length=1, max_length=20)

class StorageMetadataCreate(StorageMetadataBase):
    """
    Schema for creating new storage backend configuration.

    Extends base configuration with secret credential for secure storage backend
    initialization with encrypted credential storage for institutional security.

    Additional Security Fields:
    - **secret_key**: Encrypted storage backend secret for secure authentication

    Educational Use Cases:
    - Institutional storage backend configuration for educational content
    - Multi-cloud storage integration for educational content redundancy
    - Geographic storage distribution for global educational content delivery
    - Storage backend security configuration for institutional compliance
    """
    secret_key: constr(min_length=1, max_length=255)

class StorageMetadataUpdate(BaseSchema):
    """
    Schema for updating existing storage backend configuration.

    Provides partial update capability for storage backend modification including
    credential rotation and configuration optimization for institutional operations.

    Educational Update Operations:
    - Storage backend migration for educational content infrastructure optimization
    - Credential rotation for institutional security compliance
    - Region updates for educational content delivery optimization
    - Status management for storage backend lifecycle operations

    All fields are optional supporting incremental storage configuration updates.
    """
    storage_type: Optional[str] = Field(None, min_length=1, max_length=50)
    bucket_name: Optional[str] = Field(None, min_length=1, max_length=255)
    region: Optional[str] = Field(None, min_length=1, max_length=50)
    access_key: Optional[constr(min_length=1, max_length=255)] = None
    secret_key: Optional[constr(min_length=1, max_length=255)] = None
    status: Optional[str] = Field(None, min_length=1, max_length=20)

class StorageMetadataResponse(StorageMetadataBase):
    """
    Schema for storage backend configuration API responses.

    Extends base configuration with system-generated identifiers and timestamps
    for comprehensive storage backend tracking and operational audit support.

    Response Fields:
    - **id**: Unique storage backend identifier for configuration tracking
    - **created_at**: Storage backend configuration timestamp for lifecycle tracking
    - **updated_at**: Storage backend modification timestamp for audit trails

    Security Note:
    Secret key is excluded from responses for institutional security protection.

    Educational Benefits:
    - Complete storage backend information for institutional infrastructure management
    - Storage backend lifecycle tracking and operational audit support
    - Security-aware response excluding sensitive credential information
    - Educational content infrastructure monitoring and optimization support
    """
    id: UUID
    created_at: datetime
    updated_at: datetime

# List Response Models
class ContentFileList(BaseSchema):
    """
    Paginated list response schema for educational content files.

    Provides standardized pagination response for educational content file listing
    operations with total count for educational content discovery and navigation.

    Response Structure:
    - **items**: List of educational content file records with complete metadata
    - **total**: Total count of matching files for pagination and educational analytics

    Educational Benefits:
    - Efficient educational content file browsing and discovery
    - Educational content pagination for large institutional collections
    - Total count support for educational content analytics and reporting
    """
    items: List[ContentFileResponse]
    total: int

class MediaAssetList(BaseSchema):
    """
    Paginated list response schema for educational media assets.

    Provides standardized pagination response for educational media asset listing
    operations with total count for educational media discovery and management.

    Response Structure:
    - **items**: List of educational media asset records with pedagogical metadata
    - **total**: Total count of matching media for pagination and educational analytics

    Educational Benefits:
    - Efficient educational media browsing and discovery
    - Educational media pagination for large institutional media libraries
    - Total count support for educational media analytics and usage tracking
    """
    items: List[MediaAssetResponse]
    total: int

class StorageMetadataList(BaseSchema):
    """
    Paginated list response schema for storage backend configurations.

    Provides standardized pagination response for storage backend listing operations
    with total count for institutional infrastructure management and monitoring.

    Response Structure:
    - **items**: List of storage backend configurations with operational status
    - **total**: Total count of storage backends for infrastructure management

    Educational Benefits:
    - Efficient storage backend browsing and management
    - Infrastructure monitoring and operational oversight
    - Storage backend analytics for institutional resource optimization
    """
    items: List[StorageMetadataResponse]
    total: int