from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, constr

# Base Models
class BaseSchema(BaseModel):
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

class UserLogin(BaseModel):
    email: EmailStr
    password: str

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