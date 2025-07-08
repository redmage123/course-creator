#!/usr/bin/env python3
"""
Content Storage Service - Fixed Hydra Configuration
"""
import logging
import uuid
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from omegaconf import DictConfig
import hydra
from pydantic import BaseModel
from datetime import datetime
import uvicorn
import os

# Models
class ContentMetadata(BaseModel):
    id: str
    filename: str
    size: int
    content_type: str
    uploaded_at: datetime
    path: str

class ContentUploadResponse(BaseModel):
    content_id: str
    filename: str
    size: int
    url: str

@hydra.main(config_path="conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    # Logging setup
    logging.basicConfig(
        level=cfg.log.level,
        format=cfg.log.format
    )
    logger = logging.getLogger(__name__)
    
    # FastAPI app
    app = FastAPI(
        title="Content Storage Service",
        description="API for storing and managing course content",
        version="1.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Ensure storage directory exists
    storage_path = cfg.storage.path
    os.makedirs(storage_path, exist_ok=True)
    
    # In-memory metadata storage for demo
    content_metadata = {}
    
    @app.get("/")
    async def root():
        return {"message": "Content Storage Service"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "timestamp": datetime.now()}
    
    @app.post("/upload", response_model=ContentUploadResponse)
    async def upload_content(file: UploadFile = File(...)):
        logger.info(f"Uploading file: {file.filename}")
        
        # Validate file extension
        if file.filename:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in cfg.storage.allowed_extensions:
                raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")
        
        # Check file size
        content = await file.read()
        if len(content) > cfg.storage.max_file_size:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Generate unique ID and save file
        content_id = str(uuid.uuid4())
        file_path = os.path.join(storage_path, f"{content_id}_{file.filename}")
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Store metadata
        metadata = ContentMetadata(
            id=content_id,
            filename=file.filename or "unknown",
            size=len(content),
            content_type=file.content_type or "application/octet-stream",
            uploaded_at=datetime.now(),
            path=file_path
        )
        content_metadata[content_id] = metadata
        
        return ContentUploadResponse(
            content_id=content_id,
            filename=metadata.filename,
            size=metadata.size,
            url=f"/content/{content_id}"
        )
    
    @app.get("/content/{content_id}")
    async def get_content_info(content_id: str):
        if content_id not in content_metadata:
            raise HTTPException(status_code=404, detail="Content not found")
        return content_metadata[content_id]
    
    @app.get("/content")
    async def list_content():
        return {"content": list(content_metadata.values())}
    
    @app.delete("/content/{content_id}")
    async def delete_content(content_id: str):
        if content_id not in content_metadata:
            raise HTTPException(status_code=404, detail="Content not found")
        
        metadata = content_metadata[content_id]
        if os.path.exists(metadata.path):
            os.remove(metadata.path)
        
        del content_metadata[content_id]
        return {"message": "Content deleted successfully"}
    
    # Error handling
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # Start the server
    uvicorn.run(app, host=cfg.server.host, port=cfg.server.port, reload=cfg.server.reload)

if __name__ == "__main__":
    main()