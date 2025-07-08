from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, HttpUrl, Field, constr

# Base Models
class BaseSchema(BaseModel):
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

# ContentFile Models
class ContentFileBase(BaseSchema):
    filename: str = Field(..., min_length=1, max_length=255)
    mime_type: str = Field(..., min_length=1, max_length=127)
    file_size: int = Field(..., gt=0)
    storage_path: str = Field(..., min_length=1)

class ContentFileCreate(ContentFileBase):
    pass

class ContentFileUpdate(BaseSchema):
    filename: Optional[str] = Field(None, min_length=1, max_length=255)
    mime_type: Optional[str] = Field(None, min_length=1, max_length=127)
    file_size: Optional[int] = Field(None, gt=0)
    storage_path: Optional[str] = Field(None, min_length=1)

class ContentFileResponse(ContentFileBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

# MediaAsset Models
class MediaAssetBase(BaseSchema):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    url: HttpUrl
    content_file_id: UUID
    metadata: Optional[dict] = None

class MediaAssetCreate(MediaAssetBase):
    pass

class MediaAssetUpdate(BaseSchema):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    url: Optional[HttpUrl] = None
    metadata: Optional[dict] = None

class MediaAssetResponse(MediaAssetBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

# StorageMetadata Models
class StorageMetadataBase(BaseSchema):
    storage_type: str = Field(..., min_length=1, max_length=50)
    bucket_name: str = Field(..., min_length=1, max_length=255)
    region: str = Field(..., min_length=1, max_length=50)
    access_key: constr(min_length=1, max_length=255)
    status: str = Field(..., min_length=1, max_length=20)

class StorageMetadataCreate(StorageMetadataBase):
    secret_key: constr(min_length=1, max_length=255)

class StorageMetadataUpdate(BaseSchema):
    storage_type: Optional[str] = Field(None, min_length=1, max_length=50)
    bucket_name: Optional[str] = Field(None, min_length=1, max_length=255)
    region: Optional[str] = Field(None, min_length=1, max_length=50)
    access_key: Optional[constr(min_length=1, max_length=255)] = None
    secret_key: Optional[constr(min_length=1, max_length=255)] = None
    status: Optional[str] = Field(None, min_length=1, max_length=20)

class StorageMetadataResponse(StorageMetadataBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

# List Response Models
class ContentFileList(BaseSchema):
    items: List[ContentFileResponse]
    total: int

class MediaAssetList(BaseSchema):
    items: List[MediaAssetResponse]
    total: int

class StorageMetadataList(BaseSchema):
    items: List[StorageMetadataResponse]
    total: int