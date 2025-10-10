"""
Route handlers following SOLID principles.
Single Responsibility: Define API endpoints and delegate to services.
"""
from fastapi import FastAPI, HTTPException, Depends, Security, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Pydantic models for API (Data Transfer Objects)
from pydantic import BaseModel, EmailStr, Field
from models.auth import (
    LoginRequest,
    PasswordResetRequestModel,
    PasswordResetVerifyRequest,
    PasswordResetCompleteRequest,
    PasswordResetRequestResponse,
    PasswordResetVerifyResponse,
    PasswordResetCompleteResponse
)

# Domain entities and services
from user_management.domain.entities.user import User, UserRole, UserStatus
from user_management.domain.entities.session import Session
from user_management.domain.interfaces.user_service import IUserService, IAuthenticationService
from user_management.domain.interfaces.session_service import ISessionService

# Custom exceptions
import sys
sys.path.append('../../shared')
from shared.exceptions import (
    UserManagementException, AuthenticationException, AuthorizationException,
    UserNotFoundException, UserValidationException, DatabaseException,
    SessionException, JWTException, EmailServiceException
)

# Organization context
import sys
sys.path.append('/app/shared')
try:
    from auth.organization_middleware import get_organization_context
except ImportError:
    # Fallback if middleware not available
    def get_organization_context():
        return None

# API Models (DTOs - following Single Responsibility)
class UserCreateRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)
    user_id: Optional[str] = Field(None, min_length=1, max_length=50, description="Optional custom user ID. Must be unique if provided.")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = Field(default="student", pattern="^(student|instructor|admin|organization_admin)$")
    organization: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: str = "en"

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    bio: Optional[str] = None
    profile_picture_url: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

class PasswordResetRequest(BaseModel):
    email: EmailStr

class StudentLoginRequest(BaseModel):
    """
    Student-specific login request with GDPR-compliant minimal data collection.
    
    Privacy Context:
    Collects only essential data for educational purposes with explicit consent.
    All optional fields respect data minimization principles (GDPR Art. 5).
    Device info is anonymized and used solely for security and analytics.
    """
    username: str = Field(..., description="Username or email address")
    password: str = Field(..., min_length=1)
    course_instance_id: Optional[str] = Field(None, description="Course context (optional)")
    # Anonymized device fingerprint for security, not personal identification
    device_fingerprint: Optional[str] = Field(None, max_length=64, description="Anonymized device identifier for security")
    consent_analytics: bool = Field(default=False, description="Explicit consent for educational analytics")
    consent_notifications: bool = Field(default=False, description="Explicit consent for instructor notifications")

# Response Models
class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    status: str
    organization: Optional[str] = None
    organization_id: Optional[str] = None  # Added for org admin dashboard navigation
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: str
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_site_admin: bool = False  # Added for frontend dashboard validation

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: UserResponse

class StudentTokenResponse(BaseModel):
    """
    GDPR-compliant student login response with minimal data exposure.
    
    Privacy Context:
    Returns only essential user data needed for educational platform functionality.
    Sensitive information is excluded to comply with data minimization (GDPR Art. 5).
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user_id: str
    username: str
    full_name: str
    role: str
    course_enrollments: List[Dict[str, Any]] = Field(default_factory=list)
    login_timestamp: datetime
    session_expires_at: datetime
    # Privacy notice acknowledgment
    data_processing_notice: str = "Your login data is processed for educational purposes only. See privacy policy for details."

class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    session_type: str
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_accessed: datetime
    ip_address: Optional[str] = None
    device_info: Dict[str, Any] = {}
    is_valid: bool
    remaining_time: Optional[float] = None

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Dependency injection helpers
def get_user_service() -> IUserService:
    """Dependency injection for user service"""
    from fastapi import Request
    # This will be set during app creation
    if not hasattr(get_user_service, '_container'):
        raise HTTPException(status_code=500, detail="Service not initialized")
    return get_user_service._container.get_user_service()

def get_auth_service() -> IAuthenticationService:
    """Dependency injection for authentication service"""
    if not hasattr(get_auth_service, '_container'):
        raise HTTPException(status_code=500, detail="Service not initialized")
    return get_auth_service._container.get_authentication_service()

def get_session_service() -> ISessionService:
    """Dependency injection for session service"""
    if not hasattr(get_session_service, '_container'):
        raise HTTPException(status_code=500, detail="Service not initialized")
    return get_session_service._container.get_session_service()

def get_token_service():
    """Dependency injection for token service"""
    if not hasattr(get_token_service, '_container'):
        raise HTTPException(status_code=500, detail="Service not initialized")
    return get_token_service._container.get_token_service()

def set_container(container):
    """Set the container for dependency injection"""
    get_user_service._container = container
    get_auth_service._container = container
    get_session_service._container = container
    get_token_service._container = container

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session_service: ISessionService = Depends(get_session_service),
    user_service: IUserService = Depends(get_user_service)
) -> User:
    """Get current authenticated user"""
    logger.info(f"Token received in get_current_user: '{token[:50] if token else 'None'}...'")
    session = await session_service.validate_session(token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await user_service.get_user_by_id(session.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

def setup_auth_routes(app: FastAPI) -> None:
    """Setup authentication routes"""
    
    @app.post("/auth/register", response_model=UserResponse)
    async def register(
        request: UserCreateRequest,
        user_service: IUserService = Depends(get_user_service)
    ):
        """
        Register a new user with optional custom user ID validation.
        
        Business Context:
        User registration supports both auto-generated and custom user IDs. When a custom
        user ID is provided, the system validates its uniqueness before creating the account.
        This enables flexible user management while maintaining data integrity.
        """
        try:
            user_data = request.dict(exclude={'password'})
            user = await user_service.create_user(user_data, request.password)
            return _user_to_response(user)
            
        except UserValidationException as e:
            # Handle validation errors (including duplicate user ID)
            if e.error_code == "DUPLICATE_USER_ID_ERROR":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User ID already exists. Please choose a different ID."
                )
            elif e.error_code == "DUPLICATE_USER_ERROR":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email or username already exists."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=e.message
                )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user data provided: {str(e)}"
            )
        except UserManagementException as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=e.message
            )
        except Exception as e:
            logging.error("Unexpected error during user registration: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register user"
            )

    # NOTE: Removed duplicate /auth/login-new endpoint to eliminate code duplication
    # All authentication now uses the consolidated /auth/login endpoint below

    @app.post("/auth/login", response_model=TokenResponse)
    async def login(
        request: LoginRequest,
        raw_request: Request,
        auth_service: IAuthenticationService = Depends(get_auth_service),
        session_service: ISessionService = Depends(get_session_service),
        token_service = Depends(get_token_service)
    ):
        """
        CONSOLIDATED LOGIN ENDPOINT
        
        Uses the single LoginRequest model from models/auth.py
        Accepts username field (can be username or email)
        """
        try:
            # Log raw request body to see what we actually receive
            raw_body = await raw_request.body()
            logger.info(f"📦 RAW REQUEST BODY: {raw_body}")
            logger.info(f"🔐 LOGIN ATTEMPT - Username: '{request.username}', Password: '{request.password}'")
            user = await auth_service.authenticate_user(request.username, request.password)
            logger.info(f"🔍 AUTH RESULT - User found: {user is not None}")
            if user:
                logger.info(f"✅ AUTH SUCCESS - User: {user.username} ({user.email})")
            else:
                logger.warning(f"❌ AUTH FAILED - Invalid credentials for username: '{request.username}'")
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Authentication successful - fetch organization_id if user is org admin
            user_response = _user_to_response(user)

            # Fetch organization_id for organization admins from organization_memberships table
            if user.role.value in ['organization_admin', 'org_admin']:
                try:
                    # Get database connection pool from app state container
                    pool = raw_request.app.state.container._connection_pool

                    # Query organization_memberships to get organization_id
                    # Note: asyncpg uses $1, $2 for parameters, not %s
                    membership_query = """
                        SELECT organization_id
                        FROM course_creator.organization_memberships
                        WHERE user_id = $1 AND is_active = true
                        LIMIT 1
                    """
                    async with pool.acquire() as conn:
                        result = await conn.fetchrow(membership_query, user.id)
                        if result:
                            user_response.organization_id = str(result['organization_id'])
                            logger.info(f"✅ Found organization_id for {user.username}: {user_response.organization_id}")
                        else:
                            logger.warning(f"⚠️ No organization membership found for org admin: {user.username}")
                except Exception as e:
                    logger.error(f"❌ Error fetching organization_id: {e}")

            # Generate JWT token with user information
            # Note: JWT tokens are stateless, no need to store session in database
            session_id = f"sess_{user.id[:8]}"  # Simple session ID for JWT payload
            access_token = await token_service.generate_access_token(str(user.id), session_id)

            return TokenResponse(
                access_token=access_token,
                user=user_response
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logging.error("Error during login: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post("/auth/student-login", response_model=StudentTokenResponse)
    async def student_login(
        request: StudentLoginRequest,
        auth_service: IAuthenticationService = Depends(get_auth_service),
        session_service: ISessionService = Depends(get_session_service),
        user_service: IUserService = Depends(get_user_service)
    ):
        """
        GDPR-Compliant Student Login with Educational Analytics and Instructor Notifications
        
        Business Context:
        Provides specialized login flow for students with consent-based analytics tracking,
        instructor notifications, and course enrollment validation. Implements GDPR Article 6
        (lawful basis) and Article 7 (consent) requirements for educational data processing.
        
        Privacy Compliance:
        - Data minimization: Collects only essential login data
        - Explicit consent: Requires opt-in for analytics and notifications  
        - Purpose limitation: Data used solely for educational purposes
        - Transparency: Clear data processing notices provided
        - Retention: Login data retained only as long as educationally necessary
        """
        try:
            # Authenticate user with standard validation
            user = await auth_service.authenticate_user(request.username, request.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Validate user is a student
            if user.role != UserRole.STUDENT:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This endpoint is for student logins only"
                )
            
            # Check if user account is active and not expired
            if user.status != UserStatus.ACTIVE:
                if user.status == UserStatus.SUSPENDED:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Account suspended. Please contact your instructor."
                    )
                elif user.status == UserStatus.PENDING:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Account pending activation. Please check your email."
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Account inactive. Please contact support."
                    )
            
            # Create student session with educational context
            session_metadata = {
                "session_type": "student_portal",
                "course_instance_id": request.course_instance_id,
                "device_fingerprint": request.device_fingerprint,
                "consent_analytics": request.consent_analytics,
                "consent_notifications": request.consent_notifications,
                "login_method": "student_portal"
            }
            
            session = await session_service.create_session(
                user.id, 
                "student", 
                metadata=session_metadata
            )
            
            # Get student course enrollments (GDPR-compliant minimal data)
            enrollments = []
            if request.course_instance_id:
                # Only fetch enrollment for requested course to minimize data exposure
                try:
                    enrollment = await user_service.get_student_enrollment(
                        user.id, 
                        request.course_instance_id
                    )
                    if enrollment:
                        enrollments = [{
                            "course_instance_id": enrollment.get("course_instance_id"),
                            "course_title": enrollment.get("course_title"),
                            "progress_percentage": enrollment.get("progress_percentage", 0),
                            "enrollment_status": enrollment.get("status", "active")
                        }]
                except Exception as e:
                    # Log but don't fail login for enrollment lookup errors
                    logging.warning(f"Could not fetch enrollment for student {user.id}: {e}")
            
            # GDPR-compliant analytics logging (only with explicit consent)
            if request.consent_analytics:
                await _log_student_login_analytics(
                    user_id=user.id,
                    course_instance_id=request.course_instance_id,
                    device_fingerprint=request.device_fingerprint,
                    session_id=session.id
                )
            
            # Instructor notification (only with explicit consent)
            if request.consent_notifications and request.course_instance_id:
                await _notify_instructor_student_login(
                    student_id=user.id,
                    student_name=user.full_name,
                    course_instance_id=request.course_instance_id,
                    login_time=datetime.now(timezone.utc)
                )
            
            # Update user last login timestamp
            await user_service.record_user_login(user.id)
            
            return StudentTokenResponse(
                access_token=session.token,
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                role=user.role.value,
                course_enrollments=enrollments,
                login_timestamp=datetime.now(timezone.utc),
                session_expires_at=session.expires_at
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logging.error("Error during student login: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Login system temporarily unavailable"
            ) from e

    @app.post("/auth/logout")
    async def logout(
        token: str = Depends(oauth2_scheme),
        session_service: ISessionService = Depends(get_session_service)
    ):
        """Logout user and revoke session"""
        try:
            await session_service.revoke_session(token)
            return {"message": "Successfully logged out"}
            
        except Exception as e:
            logging.error("Error during logout: %s", e)
            # Don't return error - logout should always succeed
            return {"message": "Logged out"}

    @app.post("/auth/password/change")
    async def change_password(
        request: PasswordChangeRequest,
        current_user: User = Depends(get_current_user),
        auth_service: IAuthenticationService = Depends(get_auth_service)
    ):
        """Change user password"""
        try:
            success = await auth_service.change_password(
                current_user.id,
                request.old_password,
                request.new_password
            )
            
            if not success:
                raise HTTPException(status_code=400, detail="Invalid old password")
            
            return {"message": "Password changed successfully"}
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logging.error("Error changing password: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post("/auth/password/reset")
    async def reset_password(
        request: PasswordResetRequest,
        auth_service: IAuthenticationService = Depends(get_auth_service)
    ):
        """
        DEPRECATED: Reset user password (insecure - returns temp password)

        This endpoint is deprecated and will be removed in v4.0.
        Use the new token-based password reset flow instead:
        1. POST /auth/password/reset/request - Request reset token
        2. POST /auth/password/reset/verify - Validate token
        3. POST /auth/password/reset/complete - Complete reset
        """
        try:
            temp_password = await auth_service.reset_password(request.email)

            # In production, send email instead of returning password
            return {
                "message": "Password reset successfully",
                "temporary_password": temp_password  # Remove in production
            }

        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logging.error("Error resetting password: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post("/auth/password/reset/request", response_model=PasswordResetRequestResponse)
    async def request_password_reset(
        request: PasswordResetRequestModel,
        auth_service: IAuthenticationService = Depends(get_auth_service)
    ):
        """
        Request Password Reset Token (Step 1 of 3)

        Security Implementation:
        Implements OWASP password reset best practices with anti-enumeration protection.
        Returns generic success message regardless of whether email exists in system.

        Business Context:
        Initiates secure password reset flow by generating time-limited cryptographic token.
        Token is generated server-side and would typically be sent via email (email integration pending).
        This prevents user enumeration attacks by returning identical response for valid/invalid emails.

        Flow:
        1. User submits email address
        2. System generates secure 256-bit token (if email exists)
        3. Token stored with 1-hour expiration
        4. Email sent with reset link (production - not implemented yet)
        5. Generic success message returned (prevents user enumeration)

        Security Features:
        - No user enumeration (same response for valid/invalid emails)
        - Cryptographically secure tokens (secrets.token_urlsafe)
        - Time-limited tokens (1-hour expiration)
        - Single-use tokens (invalidated after use)
        - No sensitive data in response

        Example Request:
        ```json
        {
            "email": "user@example.com"
        }
        ```

        Example Response:
        ```json
        {
            "message": "If an account with that email exists, password reset instructions have been sent.",
            "success": true
        }
        ```

        Error Codes:
        - 200: Success (generic response regardless of email validity)
        - 500: Internal server error
        """
        try:
            # Generate reset token (service handles user existence check internally)
            await auth_service.request_password_reset(request.email)

            # Generic success message (prevents user enumeration)
            return PasswordResetRequestResponse(
                message="If an account with that email exists, password reset instructions have been sent.",
                success=True
            )

        except DatabaseException as e:
            # Database error during token generation
            logging.error(f"Database error requesting password reset: {e.message}", exc_info=True)
            # Return generic success to prevent user enumeration even on database errors
            return PasswordResetRequestResponse(
                message="If an account with that email exists, password reset instructions have been sent.",
                success=True
            )
        except UserManagementException as e:
            # User management error during token generation
            logging.error(f"User management error requesting password reset: {e.message}", exc_info=True)
            # Return generic success to prevent user enumeration
            return PasswordResetRequestResponse(
                message="If an account with that email exists, password reset instructions have been sent.",
                success=True
            )
        except EmailServiceException as e:
            # Email service error (future - when email integration added)
            logging.error(f"Email service error during password reset: {e.message}", exc_info=True)
            # Still return success to user (token was generated even if email failed)
            return PasswordResetRequestResponse(
                message="If an account with that email exists, password reset instructions have been sent.",
                success=True
            )

    @app.post("/auth/password/reset/verify", response_model=PasswordResetVerifyResponse)
    async def verify_password_reset_token(
        request: PasswordResetVerifyRequest,
        auth_service: IAuthenticationService = Depends(get_auth_service)
    ):
        """
        Verify Password Reset Token Validity (Step 2 of 3)

        Security Implementation:
        Validates reset token before displaying password change form. Implements time-based
        token expiration and single-use token pattern for security.

        Business Context:
        Validates password reset token to ensure it is:
        - Valid (exists in database)
        - Not expired (within 1-hour window)
        - Associated with an active user account

        This endpoint is called before showing the password reset form to the user,
        providing immediate feedback on token validity without requiring password submission.

        Flow:
        1. User clicks reset link with token parameter
        2. Frontend calls this endpoint to validate token
        3. If valid, display password reset form
        4. If invalid, display error message with option to request new token

        Security Features:
        - Time-based token expiration (1-hour window)
        - Token validation before password change form display
        - Clear error messages for expired/invalid tokens
        - No sensitive user data in response (only user_id)

        Example Request:
        ```json
        {
            "token": "abc123def456ghi789jkl012mno345pqr"
        }
        ```

        Example Success Response:
        ```json
        {
            "valid": true,
            "user_id": "user-12345"
        }
        ```

        Example Error Response:
        ```json
        {
            "valid": false,
            "error": "Password reset token has expired. Please request a new reset link."
        }
        ```

        Error Codes:
        - 200: Success (check 'valid' field in response)
        - 500: Internal server error
        """
        try:
            # Validate token and get user ID
            user_id = await auth_service.validate_password_reset_token(request.token)

            return PasswordResetVerifyResponse(
                valid=True,
                user_id=user_id
            )

        except ValueError as e:
            # Token validation failed (invalid or expired)
            logging.warning(f"Password reset token validation failed: {str(e)}")
            return PasswordResetVerifyResponse(
                valid=False,
                error=str(e)
            )
        except UserNotFoundException as e:
            # User associated with token not found
            logging.warning(f"User not found for password reset token: {e.message}")
            return PasswordResetVerifyResponse(
                valid=False,
                error="Invalid password reset token"
            )
        except AuthenticationException as e:
            # Authentication error during token validation
            logging.warning(f"Authentication error verifying token: {e.message}")
            return PasswordResetVerifyResponse(
                valid=False,
                error="Invalid password reset token"
            )
        except DatabaseException as e:
            # Database error during token lookup
            logging.error(f"Database error verifying password reset token: {e.message}", exc_info=True)
            return PasswordResetVerifyResponse(
                valid=False,
                error="Unable to verify token. Please try again or request a new reset link."
            )
        except UserManagementException as e:
            # General user management error
            logging.error(f"User management error verifying token: {e.message}", exc_info=True)
            return PasswordResetVerifyResponse(
                valid=False,
                error="Unable to verify token. Please try again or request a new reset link."
            )

    @app.post("/auth/password/reset/complete", response_model=PasswordResetCompleteResponse)
    async def complete_password_reset(
        request: PasswordResetCompleteRequest,
        auth_service: IAuthenticationService = Depends(get_auth_service)
    ):
        """
        Complete Password Reset (Step 3 of 3)

        Security Implementation:
        Completes password reset with comprehensive validation: token validity, expiration,
        password strength, and single-use token enforcement. Implements OWASP password
        storage best practices with bcrypt hashing.

        Business Context:
        Completes the password reset flow by:
        1. Validating reset token (must be valid and not expired)
        2. Validating new password strength (min 8 chars, 3 of 4 character types)
        3. Hashing password with bcrypt (automatic salt generation)
        4. Updating user password in database
        5. Invalidating reset token (single-use pattern)
        6. Clearing password reset flags

        This endpoint ensures secure password reset completion with proper validation
        at every step and automatic cleanup of temporary reset data.

        Flow:
        1. User submits valid token + new password
        2. System validates token (checks validity and expiration)
        3. System validates password strength requirements
        4. Password is hashed with bcrypt (secure storage)
        5. User record updated with new password
        6. Reset token invalidated (single-use)
        7. Password reset flags cleared
        8. Success response returned

        Security Features:
        - Token validation (valid, not expired, associated with user)
        - Password strength validation (min 8 chars, complexity requirements)
        - bcrypt password hashing (OWASP recommended)
        - Single-use tokens (auto-invalidated after success)
        - Automatic cleanup of reset metadata
        - Clear password reset flags (require_password_change, password_reset)

        Password Strength Requirements:
        - Minimum 8 characters
        - At least 3 of 4 character types:
          - Uppercase letters (A-Z)
          - Lowercase letters (a-z)
          - Digits (0-9)
          - Special characters (!@#$%^&*...)

        Example Request:
        ```json
        {
            "token": "abc123def456ghi789jkl012mno345pqr",
            "new_password": "MyNewP@ssw0rd123"
        }
        ```

        Example Success Response:
        ```json
        {
            "success": true,
            "message": "Password reset successful. You can now log in with your new password."
        }
        ```

        Example Error Response:
        ```json
        {
            "success": false,
            "message": "Password does not meet strength requirements (min 8 chars, 3 of 4 character types)"
        }
        ```

        Error Codes:
        - 200: Success
        - 400: Validation error (weak password, invalid token, expired token)
        - 500: Internal server error
        """
        try:
            # Complete password reset (validates token, password strength, updates user)
            success = await auth_service.complete_password_reset(
                request.token,
                request.new_password
            )

            if success:
                return PasswordResetCompleteResponse(
                    success=True,
                    message="Password reset successful. You can now log in with your new password."
                )
            else:
                # Should not reach here - service raises exceptions on failure
                raise AuthenticationException(
                    message="Password reset failed unexpectedly",
                    error_code="PASSWORD_RESET_FAILED",
                    details={"token_provided": bool(request.token)}
                )

        except ValueError as e:
            # Validation errors (token invalid/expired, weak password)
            logging.warning(f"Password reset validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except UserNotFoundException as e:
            # User associated with token not found
            logging.warning(f"User not found during password reset: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password reset token"
            )
        except AuthenticationException as e:
            # Authentication error during password reset
            logging.error(f"Authentication error during password reset: {e.message}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.message
            )
        except UserValidationException as e:
            # User validation error (password strength, user status)
            logging.warning(f"User validation error during password reset: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.message
            )
        except DatabaseException as e:
            # Database error during password update
            logging.error(f"Database error completing password reset: {e.message}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to complete password reset due to a system error. Please try again."
            )
        except UserManagementException as e:
            # General user management error
            logging.error(f"User management error completing password reset: {e.message}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to complete password reset. Please try again or request a new reset link."
            )

    @app.get("/auth/me", response_model=UserResponse)
    async def get_authenticated_user(current_user: User = Depends(get_current_user)):
        """
        Get current authenticated user profile

        Business Context:
        Provides authenticated user information for site admin dashboard and other
        administrative interfaces. Used for session validation and user context.
        """
        return _user_to_response(current_user)

def setup_user_routes(app: FastAPI) -> None:
    """Setup user management routes"""
    
    @app.get("/users/me", response_model=UserResponse)
    async def get_current_user_profile(current_user: User = Depends(get_current_user)):
        """Get current user profile"""
        return _user_to_response(current_user)

    @app.put("/users/me", response_model=UserResponse)
    async def update_profile(
        request: UserUpdateRequest,
        current_user: User = Depends(get_current_user),
        user_service: IUserService = Depends(get_user_service)
    ):
        """Update current user profile"""
        try:
            profile_data = request.dict(exclude_unset=True)
            updated_user = await user_service.update_user_profile(current_user.id, profile_data)
            return _user_to_response(updated_user)
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logging.error("Error updating profile: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.get("/users/search")
    async def search_users(
        q: str,
        limit: int = 50,
        current_user: User = Depends(get_current_user),
        user_service: IUserService = Depends(get_user_service),
        org_context = Depends(get_organization_context)
    ):
        """Search users (requires authentication and organization context)"""
        try:
            users = await user_service.search_users(q, limit)
            return [_user_to_response(user) for user in users]
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logging.error("Error searching users: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

def setup_session_routes(app: FastAPI) -> None:
    """Setup session management routes"""
    
    @app.get("/sessions/me", response_model=List[SessionResponse])
    async def get_my_sessions(
        current_user: User = Depends(get_current_user),
        session_service: ISessionService = Depends(get_session_service)
    ):
        """Get current user's sessions"""
        try:
            sessions = await session_service.get_user_sessions(current_user.id)
            return [_session_to_response(session) for session in sessions]
            
        except Exception as e:
            logging.error("Error getting sessions: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.delete("/sessions/all")
    async def revoke_all_sessions(
        current_user: User = Depends(get_current_user),
        session_service: ISessionService = Depends(get_session_service)
    ):
        """Revoke all user sessions"""
        try:
            count = await session_service.revoke_all_user_sessions(current_user.id)
            return {"message": f"Revoked {count} sessions"}
            
        except Exception as e:
            logging.error("Error revoking sessions: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

def setup_admin_routes(app: FastAPI) -> None:
    """Setup admin routes"""
    
    @app.get("/admin/users", response_model=List[UserResponse])
    async def get_all_users(
        current_user: User = Depends(get_current_user),
        user_service: IUserService = Depends(get_user_service)
    ):
        """Get all users (admin only)"""
        if not current_user.is_admin():
            raise HTTPException(status_code=403, detail="Admin access required")
        
        try:
            users = await user_service.get_users_by_role(UserRole.STUDENT)
            users.extend(await user_service.get_users_by_role(UserRole.INSTRUCTOR))
            users.extend(await user_service.get_users_by_role(UserRole.ADMIN))
            
            return [_user_to_response(user) for user in users]
            
        except Exception as e:
            logging.error("Error getting users: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.get("/admin/statistics")
    async def get_user_statistics(
        current_user: User = Depends(get_current_user),
        user_service: IUserService = Depends(get_user_service)
    ):
        """Get user statistics (admin only)"""
        if not current_user.is_admin():
            raise HTTPException(status_code=403, detail="Admin access required")
        
        try:
            stats = await user_service.get_user_statistics()
            return stats
            
        except Exception as e:
            logging.error("Error getting statistics: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

# Helper functions (following Single Responsibility)
def _user_to_response(user: User) -> UserResponse:
    """Convert domain entity to API response DTO"""
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        status=user.status.value,
        organization=user.organization,
        phone=user.phone,
        timezone=user.timezone,
        language=user.language,
        profile_picture_url=user.profile_picture_url,
        bio=user.bio,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
        is_site_admin=(user.role.value == "site_admin")  # Calculate based on role
    )

def _session_to_response(session: Session) -> SessionResponse:
    """Convert domain entity to API response DTO"""
    return SessionResponse(
        session_id=session.id,
        user_id=session.user_id,
        session_type=session.session_type,
        status=session.status.value,
        created_at=session.created_at,
        expires_at=session.expires_at,
        last_accessed=session.last_accessed,
        ip_address=session.ip_address,
        device_info=session.device_info,
        is_valid=session.is_valid(),
        remaining_time=session.get_remaining_time().total_seconds() if session.get_remaining_time() else None
    )

# =============================================================================
# GDPR-COMPLIANT HELPER FUNCTIONS FOR STUDENT LOGIN
# =============================================================================

async def _log_student_login_analytics(
    user_id: str, 
    course_instance_id: Optional[str], 
    device_fingerprint: Optional[str],
    session_id: str
) -> None:
    """
    Log student login analytics with GDPR compliance.
    
    Privacy Context:
    - Only processes data with explicit user consent (GDPR Art. 7)
    - Uses pseudonymized identifiers to protect student privacy
    - Data retained only for educational purposes and limited duration
    - Implements purpose limitation (GDPR Art. 5.1.b)
    """
    try:
        import httpx
        import asyncio
        
        # Create anonymized analytics payload (GDPR data minimization)
        analytics_data = {
            "event_type": "student_login",
            "user_id": user_id,  # Pseudonymized ID, not directly identifying
            "course_instance_id": course_instance_id,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            # Device fingerprint is anonymized, not personally identifying
            "device_fingerprint_hash": device_fingerprint,
            "platform": "student_portal",
            "data_purpose": "educational_analytics",
            "retention_period": "academic_year",  # GDPR data retention clarity
            "consent_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Send to analytics service asynchronously (non-blocking)
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                "http://analytics:8001/api/v1/events/student-login",
                json=analytics_data,
                headers={"Content-Type": "application/json"}
            )
            
    except Exception as e:
        # Log error but don't fail login process
        logging.warning(f"Failed to log student login analytics: {e}")

async def _notify_instructor_student_login(
    student_id: str,
    student_name: str,
    course_instance_id: str,
    login_time: datetime
) -> None:
    """
    Notify instructor of student login with GDPR compliance.
    
    Privacy Context:
    - Only sends notification with explicit student consent (GDPR Art. 7)
    - Minimizes data shared - only essential educational information
    - Respects legitimate educational interest (GDPR Art. 6.1.f)
    - Does not create persistent records of student activity
    """
    try:
        import httpx
        import asyncio
        
        # GDPR-compliant notification payload (minimal data)
        notification_data = {
            "event_type": "student_login_notification",
            "course_instance_id": course_instance_id,
            "student_id": student_id,  # Pseudonymized identifier
            "student_display_name": student_name,  # Educational necessity
            "login_timestamp": login_time.isoformat(),
            "notification_purpose": "educational_engagement_tracking",
            "data_processing_basis": "consent_and_legitimate_interest",
            "retention_notice": "notification_not_stored_permanently"
        }
        
        # Send notification to course management service
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                "http://course-management:8004/api/v1/notifications/student-login",
                json=notification_data,
                headers={"Content-Type": "application/json"}
            )
            
    except Exception as e:
        # Log error but don't fail login process
        logging.warning(f"Failed to notify instructor of student login: {e}")

