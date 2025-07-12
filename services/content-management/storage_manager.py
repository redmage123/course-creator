"""
Storage Manager Module
Handles file storage, retrieval, and management for the content management service
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FileMetadata:
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
    """Storage usage statistics"""
    total_files: int
    total_size_bytes: int
    files_by_type: Dict[str, int]
    oldest_file: Optional[datetime]
    newest_file: Optional[datetime]


class StorageManager:
    """Manages file storage operations"""
    
    def __init__(self, base_storage_path: str = None, max_file_size: int = 100 * 1024 * 1024):
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