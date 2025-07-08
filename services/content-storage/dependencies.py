from contextlib import contextmanager
from typing import Generator, Any
import logging
from logging.config import dictConfig
import httpx

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import hydra
from omegaconf import DictConfig

from db.session import SessionLocal
from core.config import Settings
from core.logging_config import LOGGING_CONFIG
from core.security import verify_token
from schemas.auth import TokenData

# Initialize logging
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Initialize Hydra config
@hydra.main(config_path="../config", config_name="config")
def get_config(cfg: DictConfig) -> Settings:
    return Settings(**cfg)

settings = get_config()

# Database dependency
@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session(request: Request) -> Session:
    return request.state.db

# Auth dependencies
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = verify_token(token)
        if token_data is None:
            raise credentials_exception
        return token_data
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise credentials_exception

# HTTP client dependencies
async def get_user_service_client() -> httpx.AsyncClient:
    async with httpx.AsyncClient(base_url=settings.USER_SERVICE_URL) as client:
        yield client

async def get_notification_service_client() -> httpx.AsyncClient:
    async with httpx.AsyncClient(base_url=settings.NOTIFICATION_SERVICE_URL) as client:
        yield client

# Error handling utilities
class ServiceException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def handle_service_error(e: Exception) -> None:
    logger.error(f"Service error occurred: {str(e)}")
    if isinstance(e, ServiceException):
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    raise HTTPException(
        status_code=500,
        detail="Internal server error"
    )

# Configuration dependency
def get_settings() -> Settings:
    return settings

# Logging dependency
def get_logger() -> logging.Logger:
    return logger

# Middleware dependency for request ID
def get_request_id(request: Request) -> str:
    return request.state.request_id

# Combined dependencies
class CommonDependencies:
    def __init__(
        self,
        db: Session = Depends(get_db_session),
        current_user: TokenData = Depends(get_current_user),
        settings: Settings = Depends(get_settings),
        logger: logging.Logger = Depends(get_logger),
        request_id: str = Depends(get_request_id)
    ):
        self.db = db
        self.current_user = current_user
        self.settings = settings
        self.logger = logger
        self.request_id = request_id