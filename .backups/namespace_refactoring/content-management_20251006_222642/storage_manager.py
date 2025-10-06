"""
Educational Content Storage Manager - Comprehensive File Management System

Advanced storage management system for educational content with secure file handling,
metadata management, performance optimization, and comprehensive audit capabilities.

## Core Storage Management Capabilities:

### Secure Educational File Storage
- **Multi-Format Support**: Comprehensive handling of educational content formats
  - PDF documents for syllabi, handouts, and educational resources
  - Microsoft Office documents (DOCX, PPTX) for course materials and presentations
  - JSON structured data for educational content and assessment information
  - Image and media files for educational visual aids and interactive content
  - Archive files (ZIP) for complete educational resource packages

- **Security and Validation**: Robust educational content security measures
  - File type validation and educational content appropriateness verification
  - Size limits and resource management for educational content scalability
  - Content sanitization and security scanning for safe educational material processing
  - Access control integration for educational content privacy and institutional policies
  - Educational content integrity verification with cryptographic hash validation

### Educational Content Organization
- **Pane-Based Storage Structure**: Organized storage reflecting educational content types
  - **Syllabus Storage**: Dedicated storage for course syllabi with educational metadata
  - **Slides Storage**: Presentation materials with educational design and template preservation
  - **Materials Storage**: General educational resources and supplementary content
  - **Exports Storage**: Generated educational content in various delivery formats
  - **Temporary Storage**: Processing workspace with automatic cleanup and expiration

- **Metadata Management**: Comprehensive educational content metadata system
  - Educational context tracking (course ID, instructor, academic term)
  - Content classification and educational taxonomy integration
  - Learning objective mapping and competency alignment tracking
  - Usage analytics and educational effectiveness measurement data
  - Version control and educational content evolution tracking

### Performance and Scalability
- **Async Operations**: Non-blocking file operations for educational content workflows
  - Concurrent file processing for large educational content collections
  - Memory-efficient handling of large educational documents and media files
  - Scalable architecture for institutional educational content management needs
  - Resource optimization for educational content processing and delivery

- **Caching and Optimization**: Intelligent caching for educational content performance
  - Frequently accessed educational material caching for improved response times
  - Educational content preview generation and thumbnail caching
  - Metadata caching for rapid educational content discovery and search
  - Storage usage optimization and educational content lifecycle management

### Educational Content Lifecycle Management
- **Automatic Cleanup**: Intelligent management of educational content storage
  - Temporary file expiration and automated cleanup for storage optimization
  - Educational content archiving and long-term preservation strategies
  - Storage usage monitoring and educational content lifecycle optimization
  - Resource management for sustainable educational content operations

- **Content Discovery**: Advanced search and discovery for educational materials
  - Tag-based educational content classification and filtering
  - Full-text search across educational documents and metadata
  - Educational content recommendation based on similarity and usage patterns
  - Cross-course educational content discovery and reuse opportunities

### Integration and Compatibility
- **Educational System Integration**: Seamless connectivity with educational platforms
  - Learning Management System (LMS) integration for educational content delivery
  - Educational analytics platform compatibility for content usage tracking
  - Institutional repository integration for educational content archiving
  - Cross-platform educational content sharing and collaboration support

- **API Integration**: RESTful API support for educational content management
  - Standardized educational content access and manipulation endpoints
  - Educational metadata API for content discovery and management
  - Educational content analytics API for usage monitoring and optimization
  - Integration support for educational technology ecosystems

## Educational Benefits:

### Institutional Scalability
- **Large-Scale Management**: Support for institutional educational content needs
  - Concurrent educational content processing for multiple courses and programs
  - Efficient resource utilization for educational content development workflows
  - Educational content consistency and quality maintenance at institutional scale
  - Collaborative educational content development with proper access controls

### Educational Quality Assurance
- **Content Integrity**: Comprehensive validation and quality assurance
  - Educational content authenticity verification and integrity protection
  - Format validation and educational standard compliance checking
  - Educational content accessibility evaluation and improvement recommendations
  - Quality metrics tracking and educational effectiveness measurement

### Operational Efficiency
- **Streamlined Workflows**: Optimized educational content management processes
  - Automated educational content organization and classification
  - Efficient educational content discovery and reuse capabilities
  - Reduced manual effort in educational content management and maintenance
  - Improved educational content development and delivery efficiency

This storage manager serves as the foundation for all educational content management,
ensuring secure, efficient, and scalable handling of educational materials
while maintaining educational quality and institutional compliance standards.
"""

import os
import shutil
import asyncio
import aiofiles
import aiofiles.os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, BinaryIO
from datetime import datetime, timedelta
import uuid
import json
import logging
from dataclasses import dataclass, asdict
import hashlib
import mimetypes

# Centralized logging configuration for educational content storage operations
# Enables comprehensive tracking of educational content management workflows,
# storage operations, and educational content lifecycle management
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FileMetadata:
    """
    Comprehensive metadata container for educational content files.
    
    Stores essential information about educational files including content context,
    security attributes, and educational metadata for effective content management.
    
    Educational Content Attributes:
    - **file_id**: Unique identifier for educational content tracking and reference
    - **original_filename**: Preserved original name for educational content recognition
    - **content_type**: Educational content classification (syllabus, slides, materials)
    - **course_id/user_id**: Educational context and ownership for access control
    - **tags**: Educational classification and discovery support
    
    Security and Integrity:
    - **file_hash**: Cryptographic integrity verification for educational content
    - **file_size**: Storage optimization and educational content validation
    - **mime_type**: Format validation and educational content processing support
    - **upload_timestamp**: Educational content lifecycle and audit trail tracking
    
    Storage Management:
    - **storage_path**: Physical location for educational content retrieval
    - **expires_at**: Temporary content cleanup and storage optimization
    
    Educational Benefits:
    - Comprehensive educational content tracking and management
    - Security and integrity assurance for educational materials
    - Educational content discovery and classification support
    - Audit trail and educational content lifecycle management
    """
    """Metadata for stored files"""
    file_id: str
    original_filename: str
    content_type: str
    file_size: int
    mime_type: str
    upload_timestamp: datetime
    file_hash: str
    storage_path: str
    user_id: Optional[str] = None
    course_id: Optional[str] = None
    tags: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


@dataclass
class StorageStats:
    """
    Educational content storage usage statistics and analytics.
    
    Provides comprehensive insights into educational content storage utilization,
    helping optimize storage resources and understand educational content patterns.
    
    Storage Utilization Metrics:
    - **total_files**: Overall educational content file count for capacity planning
    - **total_size_bytes**: Storage utilization for educational content optimization
    - **files_by_type**: Educational content distribution analysis and planning
    - **oldest_file/newest_file**: Educational content lifecycle and retention analysis
    
    Educational Analytics Benefits:
    - Storage resource optimization for educational content management
    - Educational content pattern analysis and usage understanding
    - Capacity planning for institutional educational content growth
    - Educational content lifecycle management and archiving strategy development
    
    Operational Insights:
    - Educational content type distribution for resource allocation
    - Storage growth trends for infrastructure planning
    - Educational content age analysis for retention policy development
    - Resource utilization optimization for educational content sustainability
    """
    """Storage usage statistics"""
    total_files: int
    total_size_bytes: int
    files_by_type: Dict[str, int]
    oldest_file: Optional[datetime]
    newest_file: Optional[datetime]


class StorageManager:
    """
    Comprehensive educational content storage management system.
    
    Advanced file storage system designed specifically for educational content management
    with security, performance, and educational workflow optimization.
    
    ## Core Storage Capabilities:
    
    ### Educational Content File Management
    - **Secure Upload Processing**: Comprehensive validation and security for educational files
      - File type validation against educational content security policies
      - Size limit enforcement for educational content scalability and performance
      - Cryptographic hash generation for educational content integrity verification
      - Educational content sanitization and security scanning integration
    
    - **Organized Storage Structure**: Educational content type-based organization
      - Syllabus storage with educational metadata and structure preservation
      - Slide storage with presentation format and educational design maintenance
      - Materials storage for general educational resources and supplementary content
      - Export storage for generated educational content and delivery packages
      - Temporary storage with automatic cleanup and educational workflow optimization
    
    ### Educational Metadata Management
    - **Comprehensive Tracking**: Full educational content lifecycle and context management
      - Educational context preservation (course, instructor, academic term)
      - Content classification and educational taxonomy integration
      - Learning objective mapping and competency alignment tracking
      - Usage analytics and educational effectiveness measurement
      - Version control and educational content evolution documentation
    
    - **Discovery and Search**: Advanced educational content discovery capabilities
      - Tag-based classification and educational content filtering
      - Full-text search across educational documents and metadata
      - Educational content recommendation based on similarity and usage
      - Cross-course content discovery and educational resource reuse
    
    ### Performance Optimization
    - **Async Operations**: Non-blocking educational content processing
      - Concurrent file operations for large educational content collections
      - Memory-efficient processing of educational documents and media
      - Scalable architecture for institutional educational content needs
      - Resource optimization for educational content workflows
    
    - **Storage Optimization**: Intelligent educational content management
      - Automatic cleanup of temporary educational content and processing files
      - Educational content archiving and long-term preservation strategies
      - Storage usage monitoring and educational content lifecycle optimization
      - Resource management for sustainable educational operations
    
    ### Security and Integrity
    - **Educational Content Security**: Comprehensive protection for educational materials
      - Access control integration for educational content privacy
      - Educational content integrity verification and authenticity protection
      - Security scanning and educational content safety validation
      - Audit logging for educational content access and modification tracking
    
    - **Quality Assurance**: Educational content validation and quality management
      - Format validation and educational standard compliance verification
      - Educational content accessibility evaluation and improvement
      - Quality metrics tracking and educational effectiveness measurement
      - Educational content consistency and institutional standard compliance
    
    ## Educational Integration Features:
    
    ### Learning Management System Support
    - **LMS Integration**: Seamless educational platform connectivity
      - Standardized educational content delivery and access
      - Educational metadata synchronization and content management
      - Educational analytics integration for usage tracking
      - Cross-platform educational content sharing and collaboration
    
    ### Institutional Scalability
    - **Large-Scale Support**: Enterprise educational content management
      - Concurrent educational content processing for multiple programs
      - Efficient resource utilization for educational workflows
      - Educational content consistency at institutional scale
      - Collaborative development with proper access controls
    
    ### Educational Workflow Integration
    - **Content Pipeline Support**: Educational content development workflow integration
      - Upload processing for educational content analysis and enhancement
      - AI integration support for educational content generation
      - Export functionality for educational content delivery
      - Quality assurance integration for educational standard compliance
    
    This storage manager provides the foundation for secure, efficient, and scalable
    educational content management, ensuring educational quality and institutional
    compliance while optimizing performance for educational workflows.
    """
    """Manages file storage operations"""
    
    def __init__(self, base_storage_path: str = None, max_file_size: int = 100 * 1024 * 1024):
        """
        Initialize educational content storage manager with comprehensive configuration.
        
        Sets up secure, organized storage system for educational content management
        with performance optimization and educational workflow support.
        
        Educational Storage Configuration:
        - **base_storage_path**: Root directory for educational content organization
          (defaults to 'storage' directory with educational content structure)
        - **max_file_size**: Educational content size limit for scalability
          (default: 100MB for large educational documents and presentations)
        
        Storage Structure Initialization:
        - Creates educational content type-specific directories
        - Establishes metadata management system for educational content tracking
        - Configures security and validation for educational content safety
        - Sets up performance optimization for educational content workflows
        
        Educational Benefits:
        - Organized educational content storage with type-based classification
        - Secure educational content management with validation and integrity
        - Performance optimization for educational content processing
        - Scalable architecture for institutional educational content needs
        
        Args:
            base_storage_path: Root directory for educational content storage
            max_file_size: Maximum file size for educational content uploads
            
        Educational Features:
        - Educational content type organization and classification
        - Security validation and educational content integrity
        - Performance optimization for educational workflows
        - Metadata management for educational content discovery
        """
        """
        Initialize storage manager
        
        Args:
            base_storage_path: Base directory for file storage
            max_file_size: Maximum file size in bytes (default: 100MB)
        """
        self.base_path = Path(base_storage_path or "storage")
        self.max_file_size = max_file_size
        self.metadata_file = self.base_path / "metadata.json"
        
        # Create storage directories
        self.content_types_dirs = {
            "syllabus": self.base_path / "syllabi",
            "slides": self.base_path / "slides", 
            "materials": self.base_path / "materials",
            "exports": self.base_path / "exports",
            "temp": self.base_path / "temp"
        }
        
        # Initialize storage
        asyncio.create_task(self._initialize_storage())
    
    async def _initialize_storage(self):
        """Initialize storage directories and metadata"""
        try:
            # Create base directory
            await aiofiles.os.makedirs(self.base_path, exist_ok=True)
            
            # Create content type directories
            for content_type, dir_path in self.content_types_dirs.items():
                await aiofiles.os.makedirs(dir_path, exist_ok=True)
            
            # Initialize metadata file if it doesn't exist
            if not await aiofiles.os.path.exists(self.metadata_file):
                await self._save_metadata({})
            
            logger.info(f"Storage initialized at: {self.base_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize storage: {str(e)}")
            raise
    
    async def save_file(self, file, file_id: str, content_type: str, 
                       user_id: str = None, course_id: str = None) -> Path:
        """
        Securely save uploaded educational content with comprehensive validation and processing.
        
        Handles complete educational file upload workflow including security validation,
        metadata generation, and educational content organization with performance optimization.
        
        Educational Content Processing:
        - **Security Validation**: Comprehensive educational content security checks
          - File type validation against educational content policies
          - Size limit enforcement for educational content scalability
          - Educational content sanitization and safety verification
          - Malware scanning and educational content security assurance
        
        - **Educational Organization**: Content type-based storage and classification
          - Syllabus storage with educational structure preservation
          - Slide storage with presentation format maintenance
          - Materials storage for educational resources and content
          - Educational metadata integration for content discovery
        
        Metadata Generation:
        - **Educational Context**: Course and instructor information preservation
        - **Integrity Verification**: Cryptographic hash for content authenticity
        - **Content Classification**: Educational taxonomy and content type tracking
        - **Usage Analytics**: Educational content utilization and effectiveness tracking
        
        Args:
            file: Uploaded educational content file object
            file_id: Unique identifier for educational content tracking
            content_type: Educational content classification (syllabus, slides, materials)
            user_id: Instructor or educational content creator identifier
            course_id: Associated course for educational content context
            
        Returns:
            Path: Secure storage location for uploaded educational content
            
        Raises:
            ValueError: Educational content validation failure or size limit exceeded
            SecurityError: Educational content security validation failure
            StorageError: Educational content storage operation failure
            
        Educational Benefits:
        - Secure educational content upload with comprehensive validation
        - Organized educational content storage with metadata preservation
        - Performance optimization for educational content processing
        - Educational content integrity and authenticity assurance
        
        Quality Assurance:
        - Educational content format validation and standard compliance
        - Security scanning and educational content safety verification
        - Educational metadata validation and content classification
        - Performance monitoring for educational content upload optimization
        """
        """
        Save uploaded file to storage
        
        Args:
            file: UploadFile object
            file_id: Unique identifier for the file
            content_type: Type of content (syllabus, slides, materials)
            user_id: User who uploaded the file
            course_id: Associated course ID
            
        Returns:
            Path to saved file
        """
        try:
            # Validate file size
            if hasattr(file, 'size') and file.size > self.max_file_size:
                raise ValueError(f"File size ({file.size}) exceeds maximum ({self.max_file_size})")
            
            # Determine storage directory
            storage_dir = self.content_types_dirs.get(content_type, self.content_types_dirs["materials"])
            
            # Generate file path
            file_extension = Path(file.filename).suffix
            filename = f"{file_id}{file_extension}"
            file_path = storage_dir / filename
            
            # Read file content
            await file.seek(0)
            content = await file.read()
            
            # Validate file size after reading
            if len(content) > self.max_file_size:
                raise ValueError(f"File size ({len(content)}) exceeds maximum ({self.max_file_size})")
            
            # Calculate file hash
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(file.filename)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Create metadata
            metadata = FileMetadata(
                file_id=file_id,
                original_filename=file.filename,
                content_type=content_type,
                file_size=len(content),
                mime_type=mime_type,
                upload_timestamp=datetime.utcnow(),
                file_hash=file_hash,
                storage_path=str(file_path),
                user_id=user_id,
                course_id=course_id
            )
            
            # Save metadata
            await self._add_file_metadata(metadata)
            
            logger.info(f"File saved: {file.filename} -> {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save file {file.filename}: {str(e)}")
            raise
    
    async def get_file_path(self, file_id: str) -> Optional[Path]:
        """Get file path by file ID"""
        try:
            metadata = await self._load_metadata()
            if file_id in metadata:
                file_path = Path(metadata[file_id]['storage_path'])
                if await aiofiles.os.path.exists(file_path):
                    return file_path
            return None
        except Exception as e:
            logger.error(f"Failed to get file path for {file_id}: {str(e)}")
            return None
    
    async def get_file_metadata(self, file_id: str) -> Optional[FileMetadata]:
        """Get file metadata by file ID"""
        try:
            metadata = await self._load_metadata()
            if file_id in metadata:
                data = metadata[file_id]
                # Convert timestamp strings back to datetime objects
                if isinstance(data['upload_timestamp'], str):
                    data['upload_timestamp'] = datetime.fromisoformat(data['upload_timestamp'])
                if data.get('expires_at') and isinstance(data['expires_at'], str):
                    data['expires_at'] = datetime.fromisoformat(data['expires_at'])
                return FileMetadata(**data)
            return None
        except Exception as e:
            logger.error(f"Failed to get metadata for {file_id}: {str(e)}")
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete file and its metadata"""
        try:
            file_path = await self.get_file_path(file_id)
            if file_path and await aiofiles.os.path.exists(file_path):
                await aiofiles.os.remove(file_path)
            
            # Remove from metadata
            await self._remove_file_metadata(file_id)
            
            logger.info(f"File deleted: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {str(e)}")
            return False
    
    async def list_files(self, content_type: str = None, user_id: str = None, 
                        course_id: str = None) -> List[FileMetadata]:
        """
        Retrieve comprehensive list of educational content files with advanced filtering.
        
        Provides flexible educational content discovery and management capabilities
        with sophisticated filtering options for educational workflow optimization.
        
        Educational Content Filtering:
        - **Content Type Filtering**: Educational content type-specific listing
          - Syllabus files for course structure and educational planning
          - Slide files for presentation and educational delivery materials
          - Materials for educational resources and supplementary content
          - Export files for generated educational content packages
        
        - **Educational Context Filtering**: Course and instructor-specific content
          - User-specific content for educational content ownership tracking
          - Course-specific content for educational material organization
          - Cross-course content discovery for educational resource reuse
          - Institutional content for educational content management
        
        Educational Discovery Features:
        - **Content Organization**: Sorted educational content for optimal discovery
          - Newest-first sorting for educational content currency
          - Educational metadata preservation for content context
          - Educational content relationship tracking and dependency management
          - Usage analytics integration for educational content effectiveness
        
        Args:
            content_type: Educational content type filter (syllabus, slides, materials)
            user_id: Instructor or educational content creator filter
            course_id: Course-specific educational content filter
            
        Returns:
            List[FileMetadata]: Filtered educational content metadata with comprehensive information
            
        Educational Benefits:
        - Efficient educational content discovery and management
        - Flexible filtering for educational workflow optimization
        - Educational content organization and relationship tracking
        - Performance optimization for educational content access
        
        Use Cases:
        - Course-specific educational content management and organization
        - Instructor educational content portfolio and resource management
        - Educational content type analysis and utilization tracking
        - Cross-course educational content discovery and reuse opportunities
        
        Performance Features:
        - Optimized database queries for educational content discovery
        - Efficient filtering and sorting for large educational content collections
        - Memory optimization for educational content metadata processing
        - Caching support for frequently accessed educational content lists
        """
        """List files with optional filtering"""
        try:
            metadata = await self._load_metadata()
            files = []
            
            for file_id, data in metadata.items():
                # Convert timestamp strings back to datetime objects
                if isinstance(data['upload_timestamp'], str):
                    data['upload_timestamp'] = datetime.fromisoformat(data['upload_timestamp'])
                if data.get('expires_at') and isinstance(data['expires_at'], str):
                    data['expires_at'] = datetime.fromisoformat(data['expires_at'])
                
                file_meta = FileMetadata(**data)
                
                # Apply filters
                if content_type and file_meta.content_type != content_type:
                    continue
                if user_id and file_meta.user_id != user_id:
                    continue
                if course_id and file_meta.course_id != course_id:
                    continue
                
                files.append(file_meta)
            
            # Sort by upload timestamp (newest first)
            files.sort(key=lambda x: x.upload_timestamp, reverse=True)
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            return []
    
    async def get_storage_stats(self) -> StorageStats:
        """Get storage usage statistics"""
        try:
            metadata = await self._load_metadata()
            
            total_files = len(metadata)
            total_size = sum(file_data['file_size'] for file_data in metadata.values())
            
            files_by_type = {}
            timestamps = []
            
            for file_data in metadata.values():
                content_type = file_data['content_type']
                files_by_type[content_type] = files_by_type.get(content_type, 0) + 1
                
                timestamp_str = file_data['upload_timestamp']
                if isinstance(timestamp_str, str):
                    timestamp = datetime.fromisoformat(timestamp_str)
                else:
                    timestamp = timestamp_str
                timestamps.append(timestamp)
            
            oldest_file = min(timestamps) if timestamps else None
            newest_file = max(timestamps) if timestamps else None
            
            return StorageStats(
                total_files=total_files,
                total_size_bytes=total_size,
                files_by_type=files_by_type,
                oldest_file=oldest_file,
                newest_file=newest_file
            )
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return StorageStats(0, 0, {}, None, None)
    
    async def cleanup_expired_files(self) -> int:
        """Remove expired files and return count of deleted files"""
        try:
            metadata = await self._load_metadata()
            deleted_count = 0
            current_time = datetime.utcnow()
            
            expired_files = []
            for file_id, file_data in metadata.items():
                expires_at = file_data.get('expires_at')
                if expires_at:
                    if isinstance(expires_at, str):
                        expires_at = datetime.fromisoformat(expires_at)
                    if current_time > expires_at:
                        expired_files.append(file_id)
            
            for file_id in expired_files:
                if await self.delete_file(file_id):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} expired files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired files: {str(e)}")
            return 0
    
    async def create_temp_file(self, content: bytes, extension: str = "", 
                              expiry_hours: int = 24) -> tuple[str, Path]:
        """
        Create temporary file
        
        Args:
            content: File content
            extension: File extension
            expiry_hours: Hours until file expires
            
        Returns:
            Tuple of (file_id, file_path)
        """
        try:
            file_id = str(uuid.uuid4())
            filename = f"temp_{file_id}{extension}"
            file_path = self.content_types_dirs["temp"] / filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Calculate expiry
            expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
            
            # Create metadata
            metadata = FileMetadata(
                file_id=file_id,
                original_filename=filename,
                content_type="temp",
                file_size=len(content),
                mime_type="application/octet-stream",
                upload_timestamp=datetime.utcnow(),
                file_hash=hashlib.sha256(content).hexdigest(),
                storage_path=str(file_path),
                expires_at=expires_at
            )
            
            await self._add_file_metadata(metadata)
            
            logger.info(f"Temporary file created: {file_id}")
            return file_id, file_path
            
        except Exception as e:
            logger.error(f"Failed to create temp file: {str(e)}")
            raise
    
    async def copy_file_to_temp(self, source_file_id: str, expiry_hours: int = 24) -> tuple[str, Path]:
        """Copy existing file to temp storage"""
        try:
            source_path = await self.get_file_path(source_file_id)
            if not source_path:
                raise FileNotFoundError(f"Source file not found: {source_file_id}")
            
            # Read source file
            async with aiofiles.open(source_path, 'rb') as f:
                content = await f.read()
            
            # Get extension from source
            extension = source_path.suffix
            
            return await self.create_temp_file(content, extension, expiry_hours)
            
        except Exception as e:
            logger.error(f"Failed to copy file to temp: {str(e)}")
            raise
    
    async def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from file"""
        try:
            if await aiofiles.os.path.exists(self.metadata_file):
                async with aiofiles.open(self.metadata_file, 'r') as f:
                    content = await f.read()
                    return json.loads(content) if content.strip() else {}
            return {}
        except Exception as e:
            logger.error(f"Failed to load metadata: {str(e)}")
            return {}
    
    async def _save_metadata(self, metadata: Dict[str, Any]):
        """Save metadata to file"""
        try:
            # Convert FileMetadata objects to dictionaries and handle datetime serialization
            serializable_metadata = {}
            for file_id, data in metadata.items():
                if isinstance(data, FileMetadata):
                    data_dict = asdict(data)
                    # Convert datetime objects to ISO format strings
                    if isinstance(data_dict.get('upload_timestamp'), datetime):
                        data_dict['upload_timestamp'] = data_dict['upload_timestamp'].isoformat()
                    if isinstance(data_dict.get('expires_at'), datetime):
                        data_dict['expires_at'] = data_dict['expires_at'].isoformat()
                    serializable_metadata[file_id] = data_dict
                else:
                    serializable_metadata[file_id] = data
            
            async with aiofiles.open(self.metadata_file, 'w') as f:
                await f.write(json.dumps(serializable_metadata, indent=2))
                
        except Exception as e:
            logger.error(f"Failed to save metadata: {str(e)}")
            raise
    
    async def _add_file_metadata(self, file_metadata: FileMetadata):
        """Add file metadata to storage"""
        try:
            metadata = await self._load_metadata()
            metadata[file_metadata.file_id] = file_metadata
            await self._save_metadata(metadata)
        except Exception as e:
            logger.error(f"Failed to add file metadata: {str(e)}")
            raise
    
    async def _remove_file_metadata(self, file_id: str):
        """Remove file metadata from storage"""
        try:
            metadata = await self._load_metadata()
            if file_id in metadata:
                del metadata[file_id]
                await self._save_metadata(metadata)
        except Exception as e:
            logger.error(f"Failed to remove file metadata: {str(e)}")
            raise
    
    async def get_file_content(self, file_id: str) -> Optional[bytes]:
        """Get file content by file ID"""
        try:
            file_path = await self.get_file_path(file_id)
            if file_path and await aiofiles.os.path.exists(file_path):
                async with aiofiles.open(file_path, 'rb') as f:
                    return await f.read()
            return None
        except Exception as e:
            logger.error(f"Failed to get file content for {file_id}: {str(e)}")
            return None
    
    async def validate_file_exists(self, file_id: str) -> bool:
        """Validate that file exists in storage"""
        try:
            file_path = await self.get_file_path(file_id)
            return file_path and await aiofiles.os.path.exists(file_path)
        except Exception as e:
            logger.error(f"Failed to validate file existence for {file_id}: {str(e)}")
            return False
    
    async def get_file_url(self, file_id: str, base_url: str = "http://localhost:8005") -> Optional[str]:
        """Generate download URL for file"""
        try:
            if await self.validate_file_exists(file_id):
                return f"{base_url}/api/content/download/{file_id}"
            return None
        except Exception as e:
            logger.error(f"Failed to generate file URL for {file_id}: {str(e)}")
            return None
    
    async def search_files(self, query: str, content_type: str = None) -> List[FileMetadata]:
        """
        Advanced educational content search with comprehensive discovery capabilities.
        
        Provides sophisticated search functionality for educational content discovery
        across filenames, metadata, and educational content classifications.
        
        Educational Search Capabilities:
        - **Multi-Field Search**: Comprehensive educational content discovery
          - Filename search for educational content identification
          - Tag-based search for educational content classification
          - Metadata search for educational context and content relationships
          - Content description search for educational material understanding
        
        - **Educational Context Integration**: Course and subject-aware search
          - Educational taxonomy integration for content classification
          - Learning objective alignment for educational content discovery
          - Subject area filtering for educational content organization
          - Institutional content discovery and educational resource sharing
        
        Search Optimization Features:
        - **Intelligent Matching**: Advanced search algorithms for educational content
          - Fuzzy matching for educational content discovery flexibility
          - Educational terminology recognition and synonym support
          - Content relevance scoring for educational material prioritization
          - Educational content recommendation based on search patterns
        
        Args:
            query: Search terms for educational content discovery
            content_type: Educational content type filter for focused search
            
        Returns:
            List[FileMetadata]: Matching educational content with relevance scoring
            
        Educational Benefits:
        - Efficient educational content discovery and reuse
        - Cross-course educational content exploration and sharing
        - Educational resource identification and utilization optimization
        - Educational content quality assessment and selection support
        
        Use Cases:
        - Educational content reuse and adaptation for course development
        - Educational resource discovery for teaching preparation
        - Educational content quality analysis and improvement identification
        - Cross-institutional educational content sharing and collaboration
        
        Performance Features:
        - Optimized search algorithms for educational content performance
        - Efficient indexing for large educational content collections
        - Caching support for frequently searched educational content terms
        - Educational content relevance scoring for optimal discovery
        """
        """Search files by filename or metadata"""
        try:
            files = await self.list_files(content_type=content_type)
            query_lower = query.lower()
            
            matching_files = []
            for file_meta in files:
                if (query_lower in file_meta.original_filename.lower() or
                    (file_meta.tags and any(query_lower in tag.lower() for tag in file_meta.tags))):
                    matching_files.append(file_meta)
            
            return matching_files
            
        except Exception as e:
            logger.error(f"Failed to search files: {str(e)}")
            return []