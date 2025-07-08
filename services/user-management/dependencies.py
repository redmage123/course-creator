from typing import Generator, Optional
from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import logging
import hydra
from omegaconf import DictConfig
import httpx
from jose import JWTError, jwt

from .database import SessionLocal
from .models import User
from .schemas import TokenData
from .config import Settings

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load config with Hydra
@hydra.main(config_path="../config", config_name="config")
def get_config(cfg: DictConfig) -> Settings:
    return Settings(**cfg)

config = get_config()

# Database dependency
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Authentication dependencies
async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            config.SECRET_KEY, 
            algorithms=[config.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# HTTP client dependencies
async def get_auth_service_client() -> httpx.AsyncClient:
    async with httpx.AsyncClient(base_url=config.AUTH_SERVICE_URL) as client:
        yield client

async def get_notification_service_client() -> httpx.AsyncClient:
    async with httpx.AsyncClient(base_url=config.NOTIFICATION_SERVICE_URL) as client:
        yield client

# Error handling utility
class ErrorHandler:
    @staticmethod
    def handle_exception(e: Exception) -> dict:
        logger.error(f"Error occurred: {str(e)}")
        if isinstance(e, HTTPException):
            return {"error": e.detail, "status_code": e.status_code}
        return {
            "error": "Internal server error",
            "status_code": 500,
            "details": str(e)
        }

# Config dependency
def get_settings() -> Settings:
    return config

# Logging dependency
def get_logger() -> logging.Logger:
    return logger

# Permission checker dependency
def check_permissions(required_permissions: list[str]):
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> bool:
        user_permissions = set(current_user.permissions)
        if not all(perm in user_permissions for perm in required_permissions):
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions"
            )
        return True
    return permission_checker