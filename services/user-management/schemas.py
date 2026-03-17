"""
Pydantic Schema Definitions for User Management Service API.

This module defines all Data Transfer Objects (DTOs) used for API request validation
and response serialization in the User Management Service. Schemas provide type safety,
automatic validation, and API documentation through FastAPI's integration with Pydantic.

Business Context:
Schemas serve as the contract between the API and clients, ensuring data integrity
and validation at the API boundary. They separate external API representation from
internal domain models, following the Interface Segregation Principle.

Technical Rationale:
- Uses Pydantic for automatic validation and serialization
- Separates request/response models for API versioning flexibility
- Provides clear validation rules (min/max length, email format, etc.)
- Generates OpenAPI/Swagger documentation automatically
- Supports partial updates through optional fields

Why Pydantic:
- Runtime type validation with detailed error messages
- Automatic JSON serialization/deserialization
- Integration with FastAPI for API docs generation
- Immutable models prevent accidental modification
- Excellent performance through Rust-based validation (pydantic v2)

Schema Organization:
- Base schemas: Common fields and configurations
- Create schemas: Required fields for resource creation
- Update schemas: Optional fields for partial updates
- Response schemas: Complete resource representation with metadata

Author: Course Creator Platform Team
Version: 2.3.0
Last Updated: 2025-08-02
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, constr

# Base Models
class BaseSchema(BaseModel):
    """
    Base schema with common timestamp fields.

    Business Context:
    Provides audit trail timestamps for all resources, enabling temporal queries
    and compliance with data retention policies (GDPR Article 17).

    Attributes:
        created_at (datetime): Resource creation timestamp (UTC)
        updated_at (datetime): Last modification timestamp (UTC)

    Configuration:
        orm_mode: Enables compatibility with SQLAlchemy ORM models
    """
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True

# Permission Schemas
class PermissionBase(BaseModel):
    name: constr(min_length=1, max_length=50)
    description: Optional[str]

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=50)]
    description: Optional[str]

class Permission(PermissionBase, BaseSchema):
    id: UUID
    
# Role Schemas
class RoleBase(BaseModel):
    name: constr(min_length=1, max_length=50)
    description: Optional[str]

class RoleCreate(RoleBase):
    permission_ids: Optional[List[UUID]]

class RoleUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=50)]
    description: Optional[str]
    permission_ids: Optional[List[UUID]]

class Role(RoleBase, BaseSchema):
    id: UUID
    permissions: List[Permission]

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: constr(min_length=3, max_length=50)
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool = True

class UserCreate(UserBase):
    password: constr(min_length=8)
    role_ids: Optional[List[UUID]]

class UserUpdate(BaseModel):
    email: Optional[EmailStr]
    username: Optional[constr(min_length=3, max_length=50)]
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: Optional[bool]
    role_ids: Optional[List[UUID]]

class UserResponse(UserBase, BaseSchema):
    id: UUID
    roles: List[Role]

# UserLogin model removed - use models/auth.py LoginRequest instead

# User Session Schemas
class UserSessionBase(BaseModel):
    user_id: UUID
    ip_address: Optional[str]
    user_agent: Optional[str]
    expires_at: datetime

class UserSessionCreate(UserSessionBase):
    token: str

class UserSessionUpdate(BaseModel):
    expires_at: Optional[datetime]
    is_active: Optional[bool]

class UserSession(UserSessionBase, BaseSchema):
    id: UUID
    token: str
    is_active: bool = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: UUID
    email: Optional[str] = None
    expires_at: datetime

# Password Reset Schemas
class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: constr(min_length=8)

# Error Responses
class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str]

class ValidationError(BaseModel):
    field: str
    message: str

class ErrorResponseWithValidation(ErrorResponse):
    validation_errors: Optional[List[ValidationError]]