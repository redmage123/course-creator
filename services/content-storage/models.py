from datetime import datetime
import uuid
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
import enum

class Base(DeclarativeBase):
    pass

class StorageType(enum.Enum):
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"
    AZURE = "azure"

class ContentFile(Base):
    __tablename__ = "content_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(127), nullable=False)
    hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    storage_metadata_id = Column(UUID(as_uuid=True), ForeignKey("storage_metadata.id"))
    storage_metadata = relationship("StorageMetadata", back_populates="content_files")
    
    media_assets = relationship("MediaAsset", back_populates="content_file")

    __table_args__ = (
        {"postgresql_partition_by": "LIST (storage_metadata_id)"}
    )

    def __repr__(self):
        return f"<ContentFile(id={self.id}, filename={self.filename})>"

class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    content_file_id = Column(UUID(as_uuid=True), ForeignKey("content_files.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    content_file = relationship("ContentFile", back_populates="media_assets")

    __table_args__ = (
        {"postgresql_partition_by": "LIST (content_file_id)"}
    )

    def __repr__(self):
        return f"<MediaAsset(id={self.id}, name={self.name})>"

class StorageMetadata(Base):
    __tablename__ = "storage_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storage_type = Column(Enum(StorageType), nullable=False)
    bucket_name = Column(String(255), nullable=True)
    base_url = Column(String(512), nullable=False)
    credentials = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    content_files = relationship("ContentFile", back_populates="storage_metadata")

    def __repr__(self):
        return f"<StorageMetadata(id={self.id}, storage_type={self.storage_type})>"