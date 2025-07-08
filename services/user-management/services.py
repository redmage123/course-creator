import logging
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from .models import User, UserRole
from .schemas import UserCreate, UserUpdate, UserResponse
from .database import get_db
from .exceptions import UserNotFoundException, ValidationError
from .messaging import MessageBroker
from .cache import CacheService
from .config import Settings

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(
        self,
        db: Session,
        cache: CacheService,
        message_broker: MessageBroker,
        settings: Settings
    ):
        self.db = db
        self.cache = cache
        self.message_broker = message_broker
        self.settings = settings

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user"""
        try:
            # Validate input data
            await self._validate_user_data(user_data)

            # Hash password
            hashed_password = pwd_context.hash(user_data.password)

            # Create user instance
            user = User(
                id=uuid4(),
                email=user_data.email,
                hashed_password=hashed_password,
                full_name=user_data.full_name,
                role=UserRole.USER,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Save to database
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            # Clear cache
            await self.cache.delete(f"user:{user.id}")

            # Send event
            await self.message_broker.publish(
                "user.created",
                {"user_id": str(user.id)}
            )

            logger.info(f"Created new user with ID: {user.id}")
            return UserResponse.from_orm(user)

        except ValidationError as e:
            logger.error(f"Validation error creating user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def get_user(self, user_id: UUID) -> UserResponse:
        """Get user by ID"""
        try:
            # Check cache first
            cached_user = await self.cache.get(f"user:{user_id}")
            if cached_user:
                return UserResponse.parse_raw(cached_user)

            user = await self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundException(f"User {user_id} not found")

            # Cache the result
            await self.cache.set(
                f"user:{user_id}",
                UserResponse.from_orm(user).json(),
                expire=self.settings.cache_ttl
            )

            return UserResponse.from_orm(user)

        except UserNotFoundException as e:
            logger.error(f"User not found: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def update_user(
        self,
        user_id: UUID,
        user_data: UserUpdate
    ) -> UserResponse:
        """Update existing user"""
        try:
            user = await self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundException(f"User {user_id} not found")

            # Update fields
            update_data = user_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field == "password":
                    setattr(user, "hashed_password",
                           pwd_context.hash(value))
                else:
                    setattr(user, field, value)

            user.updated_at = datetime.utcnow()

            # Save changes
            await self.db.commit()
            await self.db.refresh(user)

            # Clear cache
            await self.cache.delete(f"user:{user_id}")

            # Send event
            await self.message_broker.publish(
                "user.updated",
                {"user_id": str(user_id)}
            )

            logger.info(f"Updated user {user_id}")
            return UserResponse.from_orm(user)

        except UserNotFoundException as e:
            logger.error(f"User not found: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def delete_user(self, user_id: UUID) -> None:
        """Delete user"""
        try:
            user = await self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundException(f"User {user_id} not found")

            # Delete from database
            await self.db.delete(user)
            await self.db.commit()

            # Clear cache
            await self.cache.delete(f"user:{user_id}")

            # Send event
            await self.message_broker.publish(
                "user.deleted",
                {"user_id": str(user_id)}
            )

            logger.info(f"Deleted user {user_id}")

        except UserNotFoundException as e:
            logger.error(f"User not found: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserResponse]:
        """Get list of users with pagination"""
        try:
            users = await self.db.query(User)\
                .offset(skip)\
                .limit(limit)\
                .all()
            return [UserResponse.from_orm(user) for user in users]

        except Exception as e:
            logger.error(f"Error getting users list: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Optional[UserResponse]:
        """Authenticate user with email and password"""
        try:
            user = await self.db.query(User)\
                .filter(User.email == email)\
                .first()

            if not user or not pwd_context.verify(password,
                                                user.hashed_password):
                return None

            return UserResponse.from_orm(user)

        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def _validate_user_data(self, user_data: UserCreate) -> None:
        """Validate user input data"""
        if len(user_data.password) < 8:
            raise ValidationError("Password must be at least 8 characters")

        # Check if email already exists
        existing_user = await self.db.query(User)\
            .filter(User.email == user_data.email)\
            .first()
        if existing_user:
            raise ValidationError("Email already registered")

        # Additional validation rules can be added here