import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError

from .models import Content, ContentMetadata
from .schemas import ContentCreate, ContentUpdate, ContentResponse
from .database import get_db
from .config import Settings
from .utils import validate_file_type, compress_image, generate_thumbnails
from .exceptions import ContentStorageError, ValidationError

logger = logging.getLogger(__name__)

class ContentStorageService:
    def __init__(
        self,
        db: AsyncSession,
        settings: Settings,
        blob_client: BlobServiceClient
    ):
        self.db = db
        self.settings = settings
        self.blob_client = blob_client
        
    async def create_content(
        self, 
        content_data: ContentCreate,
        file_data: bytes
    ) -> ContentResponse:
        """Create new content entry with file upload"""
        try:
            # Validate incoming data
            if not validate_file_type(content_data.file_type):
                raise ValidationError("Invalid file type")
                
            # Generate unique ID
            content_id = str(uuid4())
            
            # Process file based on type
            processed_file = await self._process_file(
                file_data,
                content_data.file_type
            )
            
            # Upload to blob storage
            blob_path = await self._upload_to_storage(
                processed_file,
                content_id,
                content_data.file_type
            )
            
            # Create DB record
            content = Content(
                id=content_id,
                title=content_data.title,
                description=content_data.description,
                file_type=content_data.file_type,
                blob_path=blob_path,
                metadata=ContentMetadata(
                    size=len(processed_file),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            
            self.db.add(content)
            await self.db.commit()
            await self.db.refresh(content)
            
            return ContentResponse.from_orm(content)
            
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except AzureError as e:
            logger.error(f"Storage error: {str(e)}")
            raise ContentStorageError("Failed to upload file")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def get_content(
        self,
        content_id: str
    ) -> Optional[ContentResponse]:
        """Get content by ID"""
        try:
            content = await self.db.get(Content, content_id)
            if not content:
                return None
            return ContentResponse.from_orm(content)
        except Exception as e:
            logger.error(f"Error getting content: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get content"
            )

    async def update_content(
        self,
        content_id: str,
        content_data: ContentUpdate
    ) -> Optional[ContentResponse]:
        """Update content metadata"""
        try:
            content = await self.db.get(Content, content_id)
            if not content:
                return None
                
            # Update fields
            for field, value in content_data.dict(exclude_unset=True).items():
                setattr(content, field, value)
                
            content.metadata.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(content)
            
            return ContentResponse.from_orm(content)
            
        except Exception as e:
            logger.error(f"Error updating content: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update content"
            )

    async def delete_content(self, content_id: str) -> bool:
        """Delete content and associated files"""
        try:
            content = await self.db.get(Content, content_id)
            if not content:
                return False
                
            # Delete from storage
            await self._delete_from_storage(content.blob_path)
            
            # Delete from DB
            await self.db.delete(content)
            await self.db.commit()
            
            return True
            
        except AzureError as e:
            logger.error(f"Storage error: {str(e)}")
            raise ContentStorageError("Failed to delete file")
        except Exception as e:
            logger.error(f"Error deleting content: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete content"
            )

    async def list_contents(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Dict[str, Any] = None
    ) -> List[ContentResponse]:
        """List contents with pagination and filtering"""
        try:
            query = self.db.query(Content)
            
            if filters:
                for field, value in filters.items():
                    query = query.filter(getattr(Content, field) == value)
                    
            contents = await query.offset(skip).limit(limit).all()
            
            return [ContentResponse.from_orm(c) for c in contents]
            
        except Exception as e:
            logger.error(f"Error listing contents: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list contents"
            )

    async def _process_file(
        self,
        file_data: bytes,
        file_type: str
    ) -> bytes:
        """Process uploaded file based on type"""
        if file_type.startswith('image/'):
            # Compress images
            file_data = await compress_image(file_data)
            
            # Generate thumbnails
            await generate_thumbnails(file_data)
            
        return file_data

    async def _upload_to_storage(
        self,
        file_data: bytes,
        content_id: str,
        file_type: str
    ) -> str:
        """Upload file to blob storage"""
        try:
            container = self.blob_client.get_container_client(
                self.settings.storage_container
            )
            
            blob_path = f"{content_id}/{file_type}"
            blob = container.get_blob_client(blob_path)
            
            await blob.upload_blob(file_data)
            
            return blob_path
            
        except AzureError as e:
            logger.error(f"Storage upload error: {str(e)}")
            raise ContentStorageError("Failed to upload to storage")

    async def _delete_from_storage(self, blob_path: str):
        """Delete file from blob storage"""
        try:
            container = self.blob_client.get_container_client(
                self.settings.storage_container
            )
            
            blob = container.get_blob_client(blob_path)
            await blob.delete_blob()
            
        except AzureError as e:
            logger.error(f"Storage delete error: {str(e)}")
            raise ContentStorageError("Failed to delete from storage")