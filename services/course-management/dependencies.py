from typing import AsyncGenerator, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
import hydra
from hydra.core.config_store import ConfigStore
from omegaconf import DictConfig
import logging
import httpx
import jwt
from datetime import datetime, timedelta

from db.session import SessionLocal, AsyncSessionLocal
from core.config import Settings
from core.logging import setup_logging
from schemas.user import UserInDB
from core.security import verify_password
from core.errors import ApiError

# Config store setup
cs = ConfigStore.instance()
cs.store(name="config", node=Settings)

# Logging setup
logger = logging.getLogger(__name__)
setup_logging()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database dependencies
def get_db() -> Generator[Session, None, None]:
    """Synchronous database session dependency"""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Asynchronous database session dependency"""
    try:
        async with AsyncSessionLocal() as session:
            yield session
    finally:
        await session.close()

# Configuration dependency
@hydra.main(config_path="../conf", config_name="config")
def get_config(cfg: DictConfig) -> Settings:
    """Configuration dependency using Hydra"""
    return Settings(**cfg)

# HTTP client dependencies
async def get_http_client() -> httpx.AsyncClient:
    """Async HTTP client dependency"""
    async with httpx.AsyncClient() as client:
        yield client

# Authentication dependencies
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    config: Settings = Depends(get_config)
) -> UserInDB:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception

    user = db.query(UserInDB).filter(UserInDB.username == username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserInDB:
    """Get current admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

# Error handling dependency
def handle_errors(error: Exception) -> None:
    """Global error handler"""
    if isinstance(error, ApiError):
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail
        )
    logger.exception("Unhandled error occurred")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )

# Service client dependencies
class ServiceClients:
    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client
        
    async def get_user_service(self) -> httpx.AsyncClient:
        """User service client"""
        return self.http_client
        
    async def get_course_service(self) -> httpx.AsyncClient:
        """Course service client"""
        return self.http_client

async def get_service_clients(
    http_client: httpx.AsyncClient = Depends(get_http_client)
) -> ServiceClients:
    """Service clients dependency"""
    return ServiceClients(http_client)