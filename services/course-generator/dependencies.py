from typing import Generator, Any
import logging
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import httpx
from hydra import initialize, compose

from db.session import SessionLocal
from core.config import Settings
from core.auth import verify_access_token
from core.logging import setup_logging

# Initialize Hydra config
initialize(config_path="../conf")
cfg = compose(config_name="config")

# Setup logging
logger = setup_logging()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database dependency
def get_db() -> Generator[Session, Any, None]:
    """Database session dependency"""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# Settings dependency
@lru_cache()
def get_settings() -> Settings:
    """Application settings dependency"""
    return Settings()

# Authentication dependency
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        user = verify_access_token(token)
        if user is None:
            raise credentials_exception
        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise credentials_exception

# HTTP client dependencies
async def get_openai_client() -> httpx.AsyncClient:
    """OpenAI API client dependency"""
    async with httpx.AsyncClient(
        base_url="https://api.openai.com/v1",
        headers={"Authorization": f"Bearer {cfg.openai.api_key}"},
        timeout=30.0
    ) as client:
        yield client

async def get_user_service_client() -> httpx.AsyncClient:
    """User service HTTP client dependency"""
    async with httpx.AsyncClient(
        base_url=cfg.services.user_service_url,
        timeout=5.0
    ) as client:
        yield client

# Error handler
def handle_exceptions(func):
    """Decorator for consistent error handling"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    return wrapper

# Logging dependency
def get_logger():
    """Logger dependency"""
    return logger