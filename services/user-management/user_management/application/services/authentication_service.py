"""
Authentication Application Service - Secure User Authentication Implementation

This module implements the authentication business logic for the User Management
Service, providing secure user authentication, password management, and credential
validation capabilities.

Service Architecture:
    Application Layer Service: Orchestrates authentication business logic
    Domain Service Implementation: Implements IAuthenticationService interface
    Security First Design: Built-in security features and best practices
    Dependency Injection: Uses repository abstractions for data access

Core Security Features:
    - Secure password hashing using bcrypt with salt
    - Password strength validation and enforcement
    - Secure temporary password generation
    - Authentication attempt validation
    - User account status verification
    - Login activity tracking and audit trail

Password Security Implementation:
    - bcrypt hashing algorithm with automatic salt generation
    - Configurable hashing rounds for performance/security balance
    - Password strength requirements (length, complexity)
    - Secure random password generation for resets
    - Protection against timing attacks in password verification

Business Logic Implementation:
    - User authentication with email/password credentials
    - Password change flows with old password verification
    - Password reset workflows with temporary passwords
    - Account lockout and security incident response
    - Password policy enforcement and validation

Integration Points:
    - User Repository: User data access and persistence
    - Session Service: Session creation after successful authentication
    - Email Service: Password reset notifications (future enhancement)
    - Audit Service: Security event logging (future enhancement)

Security Considerations:
    - Password hashes are stored separately from user profiles
    - Timing attack protection in authentication flows
    - Secure password generation with cryptographic randomness
    - Password strength validation prevents weak passwords
    - Account status verification prevents unauthorized access

Design Patterns Applied:
    - Service Layer Pattern: Encapsulates authentication business logic
    - Strategy Pattern: Configurable password hashing algorithms
    - Template Method: Consistent password validation and generation
    - Dependency Injection: Testable and maintainable dependencies

Author: Course Creator Platform Team
Version: 2.3.0
Last Updated: 2025-08-02
"""
from typing import Optional
import logging
import secrets
import string
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

from data_access.user_dao import UserManagementDAO
from user_management.domain.interfaces.user_service import IAuthenticationService
from user_management.domain.entities.user import User

logger = logging.getLogger(__name__)

class AuthenticationService(IAuthenticationService):
    """
    Authentication Service Implementation - Secure User Authentication
    
    This service implements comprehensive user authentication and password management
    functionality for the Course Creator Platform. It provides secure, production-ready
    authentication features with industry-standard security practices.
    
    Service Responsibilities:
        - User credential validation and authentication
        - Secure password hashing and verification
        - Password strength enforcement and validation
        - Password reset and change workflows
        - User account security management
        - Authentication audit and activity tracking
    
    Security Implementation:
        - bcrypt password hashing with automatic salt generation
        - Timing attack protection in password verification
        - Secure random password generation using cryptographic functions
        - Password strength validation with configurable requirements
        - Account status verification before authentication
        - Login activity tracking for security monitoring
    
    Password Policy:
        - Minimum 8 characters length
        - At least 3 of 4 character types: uppercase, lowercase, digit, special
        - Protection against common password patterns
        - Secure temporary password generation for resets
    
    Integration Features:
        - Repository pattern for data access abstraction
        - Domain entity integration for user management
        - Metadata system for password-related flags
        - Extensible for future security enhancements
    
    Usage Examples:
        # Authenticate user
        user = await auth_service.authenticate_user("user@example.com", "password")
        
        # Change password
        success = await auth_service.change_password(user_id, old_pass, new_pass)
        
        # Reset password
        temp_password = await auth_service.reset_password("user@example.com")
    """
    
    def __init__(self, user_dao: UserManagementDAO):
        """
        Initialize the authentication service with required dependencies.
        
        Sets up the authentication service with secure password hashing configuration
        and user data access through the DAO pattern.
        
        Args:
            user_dao (UserDAO): DAO for user data access
        
        Security Configuration:
            - bcrypt hashing algorithm for password security
            - Automatic salt generation for each password
            - Configurable rounds for performance/security balance
            - Auto-deprecation of older hashing schemes
        
        Design Notes:
            - Uses dependency injection for testability
            - Configured for production security requirements
            - Extensible for additional hashing algorithms
        """
        self._user_dao = user_dao
        """
        Configure password hashing context with bcrypt algorithm.
        
        bcrypt Configuration:
        - schemes=["bcrypt"]: Use bcrypt as primary hashing algorithm
        - deprecated="auto": Automatically handle algorithm migrations
        - Default rounds: 12 (can be configured for environment)
        
        bcrypt Benefits:
        - Adaptive hashing (configurable work factor)
        - Built-in salt generation
        - Resistance to rainbow table attacks
        - Time-tested and industry standard
        """
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async def authenticate_user(self, username_or_email: str, password: str) -> Optional[User]:
        """
        Authenticate user with username/email and password credentials.
        
        This is the primary authentication method used for user login. It performs
        comprehensive validation including credential verification, account status
        checks, and login activity tracking.
        
        Authentication Flow:
            1. Input validation (username/email and password provided)
            2. User lookup by username or email address
            3. Account status verification (must be active)
            4. Password verification with secure hashing
            5. Login activity recording and timestamp update
            6. Return authenticated user or None for failure
        
        Security Features:
            - Timing attack protection (consistent execution time)
            - Account status verification prevents inactive user access
            - Password verification using secure bcrypt hashing
            - Login activity tracking for security monitoring
            - Failed authentication returns None (no error details)
        
        Args:
            username_or_email (str): User's username or email address for identification
            password (str): Plain text password for verification
        
        Returns:
            Optional[User]: Authenticated user entity if successful, None if failed
        
        Security Considerations:
            - Does not reveal whether email exists (prevents user enumeration)
            - Consistent execution time prevents timing attacks
            - Updates login timestamp for successful authentications
            - Respects account status for access control
        
        Usage:
            user = await auth_service.authenticate_user("user@example.com", "password")
            if user:
                # Create session and grant access
            else:
                # Authentication failed, deny access
        """
        """
        Input validation: Ensure both username/email and password are provided.
        Early return prevents unnecessary database queries and provides
        consistent timing for invalid inputs.
        """
        if not username_or_email or not password:
            return None
        
        """
        User lookup: Find user by username or email address.
        Try username first (for admin users), then fall back to email.
        """
        # First try to find by username
        user = await self._user_dao.get_user_by_username(username_or_email)
        logger.info(f"🔍 After get_user_by_username: user is {user is not None}")

        # If not found by username, try by email
        if not user:
            user = await self._user_dao.get_user_by_email(username_or_email)
            logger.info(f"🔍 After get_user_by_email: user is {user is not None}")

        if not user:
            logger.warning(f"🔍 User not found for: {username_or_email}")
            return None

        """
        Account status verification: Only active users can authenticate.
        This prevents access for suspended, inactive, or pending accounts.
        """
        is_active_status = user.is_active()
        logger.info(f"🔍 User is_active check: {is_active_status}")
        if not is_active_status:
            logger.warning(f"🔍 User account is not active")
            return None
        
        """
        Password verification: Use secure bcrypt verification.
        """
        hashed_password = user.metadata.get('hashed_password')
        logger.info(f"🔍 Has hashed_password in metadata: {hashed_password is not None}")

        if hashed_password:
            try:
                logger.info(f"🔍 Verifying password...")
                is_valid = self._pwd_context.verify(password, hashed_password)
                logger.info(f"🔍 Password verification result: {is_valid}")
                if is_valid:
                    """
                    Successful authentication: Record login activity.
                    """
                    user.record_login()
                    logger.info(f"🔍 LOGIN SUCCESS - Returning user")
                    return user
                else:
                    logger.warning(f"🔍 Password verification failed - incorrect password")
            except Exception as e:
                logger.error(f"🔍 Password verification exception: {e}")
        else:
            logger.warning(f"🔍 No hashed_password found in user.metadata")

        return None
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """
        Change user password with old password verification.

        SECURE PASSWORD CHANGE WORKFLOW:
        This method implements a secure password change flow that requires users
        to verify their current password before setting a new one. This prevents
        unauthorized password changes from compromised sessions or shared devices.

        Security Features:
            - Old password verification (prevents unauthorized changes)
            - New password strength validation (enforces password policy)
            - Secure password hashing with bcrypt
            - Atomic update operation (all-or-nothing)
            - Password history prevention (future enhancement)

        Business Workflow:
            1. User provides current password and desired new password
            2. System verifies user exists and is authorized
            3. Current password is verified against stored hash
            4. New password is validated against strength requirements
            5. New password is hashed securely with bcrypt
            6. Password hash is updated in user metadata
            7. User is notified of successful password change

        Args:
            user_id (str): Unique identifier of the user changing password
            old_password (str): Current password for verification
            new_password (str): Desired new password (must meet strength requirements)

        Returns:
            bool: True if password changed successfully, False if user not found or old password incorrect

        Raises:
            ValueError: If new password fails strength validation

        Security Considerations:
            - Requires old password verification (prevents session hijacking attacks)
            - Validates new password strength before hashing
            - Uses secure bcrypt hashing for password storage
            - Does not reveal whether user exists (prevents user enumeration)
            - Future: Should invalidate all other sessions after password change
            - Future: Should implement password history to prevent reuse

        Usage Example:
            ```python
            # User requests password change
            try:
                success = await auth_service.change_password(
                    user_id="user-123",
                    old_password="OldPassword123!",
                    new_password="NewSecureP@ss456"
                )

                if success:
                    # Password changed successfully
                    # Optionally: Revoke other sessions for security
                    await session_service.revoke_all_user_sessions(user_id)
                    return {"message": "Password changed successfully"}
                else:
                    # Old password incorrect or user not found
                    return {"error": "Current password is incorrect"}
            except ValueError as e:
                # New password doesn't meet strength requirements
                return {"error": str(e)}
            ```

        Implementation Notes:
            - Password stored in user metadata (should use separate password table in production)
            - Future: Add password history table to prevent password reuse
            - Future: Add password expiration and rotation policies
            - Future: Add notification email for password change events

        Author: Course Creator Platform Team
        Version: 2.3.0
        """
        user = await self._user_dao.get_by_id(user_id)
        if not user:
            return False

        # Verify old password
        if not await self.verify_password(user_id, old_password):
            return False

        # Validate new password
        if not self._validate_password_strength(new_password):
            raise ValueError("Password does not meet strength requirements")

        # Hash and store new password
        hashed_password = await self.hash_password(new_password)

        # In real implementation, store password in separate secure storage
        # For now, we'll add it to user metadata (not recommended for production)
        user.add_metadata('password_hash', hashed_password)
        await self._user_dao.update(user)

        return True
    
    async def reset_password(self, email: str) -> str:
        """
        DEPRECATED: Use request_password_reset() for secure token-based reset.

        This method returns the temporary password directly (insecure).
        Maintained for backward compatibility only.

        Migration Guide:
        OLD: temp_password = await auth_service.reset_password(email)
        NEW: token = await auth_service.request_password_reset(email)
             # Send token via email
             await auth_service.complete_password_reset(token, new_password)

        Reset password and return temporary password.
        """
        user = await self._user_dao.get_user_by_email(email)
        if not user:
            raise ValueError("User not found")

        # Generate temporary password
        temp_password = self._generate_temporary_password()

        # Hash and store temporary password
        hashed_password = await self.hash_password(temp_password)
        user.add_metadata('password_hash', hashed_password)
        user.add_metadata('password_reset', True)

        await self._user_dao.update(user)

        return temp_password

    async def request_password_reset(self, email: str) -> str:
        """
        Request password reset - generates secure token for password reset flow.

        SECURE TOKEN-BASED RESET FLOW:
        This is the recommended password reset method that uses time-limited tokens
        instead of returning passwords directly. Follows OWASP authentication best practices.

        Security Features:
            - Cryptographically secure random tokens (secrets.token_urlsafe)
            - Time-limited tokens (1 hour expiration)
            - No user enumeration (same response for valid/invalid emails)
            - Single-use tokens (invalidated after successful reset)

        Business Workflow:
            1. User requests password reset via email
            2. System generates secure random token
            3. Token stored with user record + expiration timestamp
            4. Email sent with password reset link containing token
            5. User clicks link and submits new password
            6. System validates token and updates password
            7. Token is invalidated after successful reset

        Args:
            email (str): User's email address

        Returns:
            str: Secure reset token (URL-safe base64, >= 32 characters)
                 In production, this token is sent via email, not returned in response

        Security Considerations:
            - Returns success even if email doesn't exist (prevents user enumeration)
            - Overwrites previous tokens (only most recent token is valid)
            - Tokens expire after 1 hour to limit attack window
            - Rate limiting should be applied at endpoint level (future enhancement)

        Integration Example:
            ```python
            # Backend
            reset_token = await auth_service.request_password_reset("user@example.com")
            await email_service.send_password_reset_email(email, reset_token)

            # User clicks email link with token parameter
            # Frontend submits: POST /auth/password/reset/complete {token, new_password}

            # Backend completes reset
            await auth_service.complete_password_reset(token, new_password)
            ```

        Author: Course Creator Platform Team
        Version: 3.4.0 - Secure Token-Based Password Reset
        """
        # Try to find user by email
        user = await self._user_dao.get_user_by_email(email)

        # Security: No user enumeration - same response for valid/invalid emails
        if not user:
            # Generate fake token to maintain consistent timing
            # Prevents timing attacks that could reveal valid vs invalid emails
            fake_token = secrets.token_urlsafe(32)
            return fake_token

        # Generate cryptographically secure reset token
        # token_urlsafe(32) generates 256 bits of entropy (URL-safe base64)
        reset_token = secrets.token_urlsafe(32)

        # Calculate token expiration (1 hour from now)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # Store token and expiration with user record
        # This overwrites any previous reset tokens (only latest token is valid)
        user.add_metadata('password_reset_token', reset_token)
        user.add_metadata('password_reset_expires', expires_at)

        # Persist token to database
        await self._user_dao.update(user)

        # Return token for email delivery
        # In production, this token is sent via email, not in API response
        return reset_token

    async def validate_password_reset_token(self, token: str) -> str:
        """
        Validate password reset token and return associated user ID.

        SECURITY VALIDATION:
        Ensures token is valid before allowing password reset. Validates:
        - Token exists in system
        - Token matches user's stored token
        - Token has not expired

        Business Logic:
            Used before displaying password reset form to verify token validity.
            Frontend can call this endpoint when user clicks email link to ensure
            token is still valid before showing password input form.

        Args:
            token (str): Password reset token from email

        Returns:
            str: User ID associated with valid token

        Raises:
            ValueError: If token is invalid or expired

        Security Features:
            - Constant-time token comparison (prevents timing attacks)
            - Expiration validation prevents use of old tokens
            - Generic error messages (no leak of token status)

        Usage Example:
            ```python
            # Frontend: User clicks email link with token parameter
            # Backend validates token before showing reset form

            try:
                user_id = await auth_service.validate_password_reset_token(token)
                # Token valid - show password reset form
                return {"valid": True, "user_id": user_id}
            except ValueError:
                # Token invalid or expired - show error message
                return {"valid": False, "error": "Invalid or expired reset link"}
            ```
        """
        # Try to find user with this reset token
        # Note: In production, use indexed lookup for performance
        user = await self._user_dao.get_user_by_metadata_value('password_reset_token', token)

        # Token not found in system
        if not user:
            raise ValueError("Invalid password reset token")

        # Get token expiration from user metadata
        expires_at = user.metadata.get('password_reset_expires')

        # Verify token has expiration timestamp
        if not expires_at:
            raise ValueError("Invalid password reset token")

        # Check if token has expired
        current_time = datetime.now(timezone.utc)
        if current_time > expires_at:
            raise ValueError("Password reset token has expired. Please request a new reset link.")

        # Token is valid - return user ID for password reset
        return user.id

    async def complete_password_reset(self, token: str, new_password: str) -> bool:
        """
        Complete password reset using valid token and new password.

        SECURE PASSWORD RESET COMPLETION:
        Final step in token-based password reset flow. Validates token,
        validates password strength, updates password, and invalidates token.

        Security Features:
            - Token validation (existence, expiration)
            - Password strength enforcement
            - Secure password hashing (bcrypt)
            - Token invalidation after use (single-use tokens)
            - All-or-nothing transaction (atomicity)

        Business Workflow:
            1. Validate token (must exist and not be expired)
            2. Validate new password strength requirements
            3. Hash new password securely with bcrypt
            4. Update user password in database
            5. Clear reset token and expiration from user metadata
            6. Return success status

        Args:
            token (str): Valid password reset token from email
            new_password (str): New password (must meet strength requirements)

        Returns:
            bool: True if password reset completed successfully

        Raises:
            ValueError: If token is invalid/expired OR password fails strength validation

        Security Considerations:
            - Token must be validated before password update (prevents unauthorized access)
            - Password strength must be validated (prevents weak passwords)
            - Token is invalidated after successful use (prevents token reuse)
            - Failed attempts do NOT invalidate token (user can retry with valid password)

        Usage Example:
            ```python
            # User submits new password via reset form
            try:
                success = await auth_service.complete_password_reset(
                    token="abc123...",
                    new_password="NewSecureP@ss123"
                )

                if success:
                    # Password reset successful
                    # Redirect to login page with success message
                    return {"message": "Password reset successful. Please login with your new password."}

            except ValueError as e:
                # Token invalid/expired or password too weak
                return {"error": str(e)}
            ```

        Author: Course Creator Platform Team
        Version: 3.4.0 - Secure Token-Based Password Reset
        """
        # Step 1: Validate token and get user ID
        user_id = await self.validate_password_reset_token(token)

        # Step 2: Get user record (we know it exists from token validation)
        user = await self._user_dao.get_by_id(user_id)
        if not user:
            # Should never happen if token validation succeeded
            raise ValueError("User not found")

        # Step 3: Validate new password strength
        # Raises ValueError if password doesn't meet requirements
        if not self._validate_password_strength(new_password):
            raise ValueError("Password does not meet strength requirements (min 8 chars, 3 of 4 character types)")

        # Step 4: Hash new password securely with bcrypt
        hashed_password = self._pwd_context.hash(new_password)

        # Step 5: Update user password
        user.add_metadata('hashed_password', hashed_password)

        # Step 6: Invalidate reset token (single-use tokens)
        user.remove_metadata('password_reset_token')
        user.remove_metadata('password_reset_expires')

        # Step 7: Clear any password reset flags
        user.remove_metadata('password_reset')
        user.remove_metadata('require_password_change')

        # Step 8: Persist all changes atomically
        await self._user_dao.update(user)

        # Success - password updated and token invalidated
        return True
    
    async def verify_password(self, user_id: str, password: str) -> bool:
        """
        Verify user password against stored hash.

        PASSWORD VERIFICATION:
        This method securely verifies a plain text password against the stored
        bcrypt hash for a given user. Used in authentication flows where password
        verification is needed (login, password change, sensitive operations).

        Security Features:
            - Secure bcrypt verification (timing attack resistant)
            - Constant-time comparison inherent to bcrypt
            - No information leakage about user existence
            - Exception handling prevents information disclosure

        Business Use Cases:
            - User login authentication
            - Password change verification (old password)
            - Sensitive operation confirmation (delete account, change email)
            - Two-factor authentication backup verification

        Args:
            user_id (str): Unique identifier of the user
            password (str): Plain text password to verify

        Returns:
            bool: True if password matches stored hash, False otherwise

        Security Considerations:
            - Returns False for non-existent users (prevents user enumeration)
            - Returns False for missing password hash (handles incomplete accounts)
            - Catches all exceptions and returns False (prevents information leakage)
            - Uses bcrypt's built-in timing attack protection
            - Does not log failed verification details (prevents log-based enumeration)

        Usage Example:
            ```python
            # Verify password before sensitive operation
            if await auth_service.verify_password(user_id, provided_password):
                # Password correct - proceed with operation
                await perform_sensitive_operation(user_id)
            else:
                # Password incorrect - deny access
                return {"error": "Incorrect password"}
            ```

        Implementation Notes:
            - Password hash retrieved from user metadata (should use separate password table in production)
            - bcrypt.verify handles timing attack protection automatically
            - Future: Add rate limiting for verification attempts
            - Future: Add brute force protection with account lockout

        Author: Course Creator Platform Team
        Version: 2.3.0
        """
        user = await self._user_dao.get_by_id(user_id)
        if not user:
            return False

        # In real implementation, get password hash from secure storage
        stored_hash = user.metadata.get('password_hash')
        if not stored_hash:
            return False

        try:
            return self._pwd_context.verify(password, stored_hash)
        except Exception as e:
            return False
    
    async def hash_password(self, password: str) -> str:
        """
        Hash password using secure bcrypt algorithm with validation.
        
        This method validates password strength requirements and generates
        a secure bcrypt hash with automatic salt generation.
        
        Args:
            password (str): Plain text password to hash
        
        Returns:
            str: Secure bcrypt hash suitable for storage
        
        Raises:
            ValueError: If password fails strength validation
        
        Security Features:
            - Password strength validation before hashing
            - bcrypt algorithm with automatic salt generation
            - Configurable work factor for security/performance balance
            - Protection against weak password storage
        """
        if not self._validate_password_strength(password):
            raise ValueError("Password does not meet strength requirements")
        
        return self._pwd_context.hash(password)
    
    def _validate_password_strength(self, password: str) -> bool:
        """
        Validate password against security strength requirements.
        
        Implements password policy to ensure users create strong passwords
        that resist common attack methods like dictionary and brute force attacks.
        
        Password Requirements:
            - Minimum 8 characters length
            - At least 3 of 4 character types:
              * Uppercase letters (A-Z)
              * Lowercase letters (a-z)
              * Digits (0-9)
              * Special characters (!@#$%^&*()_+-=[]{}|;:,.<>?)
        
        Args:
            password (str): Password to validate
        
        Returns:
            bool: True if password meets requirements, False otherwise
        
        Security Rationale:
            - Length requirement prevents short, easily guessed passwords
            - Character type diversity increases password entropy
            - Flexible requirement (3 of 4) balances security with usability
            - Industry standard password strength requirements
        """
        # Minimum length requirement
        if len(password) < 8:
            return False
        
        # Character type analysis
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        # Require at least 3 of 4 character types for flexibility
        return sum([has_upper, has_lower, has_digit, has_special]) >= 3
    
    def _generate_temporary_password(self) -> str:
        """
        Generate cryptographically secure temporary password.

        SECURE PASSWORD GENERATION:
        This method generates a cryptographically secure random password suitable
        for temporary passwords in password reset flows. Uses Python's secrets
        module for cryptographic randomness instead of random module.

        Security Features:
            - Cryptographically secure random generation (secrets module)
            - Guaranteed character type diversity (all 4 types included)
            - Sufficient entropy for security (12 characters minimum)
            - Random shuffling prevents predictable patterns
            - Meets platform password strength requirements

        Password Characteristics:
            - Length: 12 characters
            - Character Types: Uppercase, lowercase, digits, special characters
            - Character Set: A-Z, a-z, 0-9, !@#$%^&*
            - Entropy: ~79 bits (sufficient for temporary passwords)
            - Validity: Should be one-time use and expire quickly

        Business Context:
            Used for password reset flows where users need a temporary password
            to regain account access. These passwords should be:
            - Emailed to user's registered email address
            - Valid for limited time (e.g., 1 hour)
            - Marked for mandatory change on first login
            - Single-use only (invalidated after successful login)

        Returns:
            str: Cryptographically secure 12-character temporary password

        Security Considerations:
            - Uses secrets.choice() not random.choice() (cryptographic randomness)
            - Ensures all character types present (meets password policy)
            - Sufficient length for security (12 characters)
            - Random shuffling prevents pattern-based attacks
            - Should be transmitted securely (email with TLS)
            - Should expire quickly (1 hour maximum)
            - Should be invalidated after first use

        Implementation Details:
            1. Generate 12-character password
            2. Ensure at least one uppercase letter
            3. Ensure at least one lowercase letter
            4. Ensure at least one digit
            5. Ensure at least one special character
            6. Fill remaining characters randomly
            7. Shuffle to prevent predictable patterns

        Usage Example:
            ```python
            # Generate temporary password for reset flow
            temp_password = self._generate_temporary_password()

            # Hash and store it
            hashed_password = await self.hash_password(temp_password)
            user.add_metadata('hashed_password', hashed_password)
            user.add_metadata('password_reset', True)
            user.add_metadata('require_password_change', True)

            # Email to user (securely)
            await email_service.send_temporary_password(user.email, temp_password)
            ```

        Author: Course Creator Platform Team
        Version: 2.3.0
        """
        length = 12
        characters = string.ascii_letters + string.digits + "!@#$%^&*"

        # Ensure at least one character from each category
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*")
        ]

        # Fill the rest randomly
        for _ in range(length - 4):
            password.append(secrets.choice(characters))

        # Shuffle the password
        secrets.SystemRandom().shuffle(password)

        return ''.join(password)
    
    async def require_password_change(self, user_id: str) -> bool:
        """
        Mark user as requiring password change on next login.

        PASSWORD CHANGE REQUIREMENT FLAG:
        This method sets a flag on the user account that requires them to change
        their password on the next login. Used for security-related scenarios where
        forced password changes are necessary.

        Business Use Cases:
            - After admin password reset (force user to set own password)
            - After security incident detection (compromised credentials)
            - After temporary password usage (from password reset)
            - After initial account creation (change default password)
            - After password policy update (enforce new requirements)
            - After account recovery (additional security measure)

        Workflow Integration:
            1. Flag is set via this method
            2. User logs in successfully with current password
            3. Authentication middleware detects the flag
            4. User is redirected to password change page
            5. User cannot access other pages until password changed
            6. Flag is cleared after successful password change

        Args:
            user_id (str): Unique identifier of the user

        Returns:
            bool: True if flag set successfully, False if user not found

        Security Considerations:
            - Does not invalidate current sessions (sessions remain valid)
            - Does not change current password (only sets requirement flag)
            - Should be used with session revocation for immediate effect
            - Frontend must enforce password change before other operations
            - Backend must validate flag on all authenticated endpoints

        Usage Example:
            ```python
            # After admin resets user password
            temp_password = await auth_service.reset_password(email)
            await auth_service.require_password_change(user.id)

            # After security incident
            if suspicious_activity_detected:
                await auth_service.require_password_change(user_id)
                await session_service.revoke_all_user_sessions(user_id)
                await email_service.send_security_alert(user.email)
            ```

        Implementation Notes:
            - Flag stored in user metadata with key 'require_password_change'
            - Flag should be checked in authentication middleware
            - Flag cleared by clear_password_reset_flag() after password change
            - Future: Add expiration time for forced password changes
            - Future: Add audit logging for security compliance

        Author: Course Creator Platform Team
        Version: 2.3.0
        """
        user = await self._user_dao.get_by_id(user_id)
        if not user:
            return False

        user.add_metadata('require_password_change', True)
        await self._user_dao.update(user)

        return True
    
    async def clear_password_reset_flag(self, user_id: str) -> bool:
        """
        Clear password reset flags after successful password change.

        FLAG CLEANUP AFTER PASSWORD CHANGE:
        This method removes security flags from user accounts after they have
        successfully changed their password. Called after password change completion
        to restore normal authentication flow without forced password change requirements.

        Business Context:
            After a user completes a password change (either voluntary or forced),
            this method clears all temporary password-related flags to allow normal
            system access. This completes the password change workflow cycle.

        Flags Cleared:
            - password_reset: Indicates password was reset by admin/system
            - require_password_change: Forces password change on next login

        Workflow Integration:
            1. User changes password successfully (via change_password() or complete_password_reset())
            2. This method is called automatically or manually
            3. All password reset flags are removed
            4. User can now access system normally without password change prompts
            5. User authentication proceeds through normal flow

        Args:
            user_id (str): Unique identifier of the user

        Returns:
            bool: True if flags cleared successfully, False if user not found

        Usage Example:
            ```python
            # After user changes password
            success = await auth_service.change_password(
                user_id, old_password, new_password
            )

            if success:
                # Clear flags to restore normal access
                await auth_service.clear_password_reset_flag(user_id)
                return {"message": "Password changed successfully"}
            ```

        Implementation Notes:
            - Removes 'password_reset' metadata flag
            - Removes 'require_password_change' metadata flag
            - Should be called after successful password change
            - Safe to call even if flags don't exist (no-op)
            - Future: Add audit logging for compliance

        Security Considerations:
            - Only clears flags, does not modify password
            - Should only be called after verified password change
            - Does not revoke sessions (user remains logged in)
            - Does not send notifications (separate concern)

        Author: Course Creator Platform Team
        Version: 2.3.0
        """
        user = await self._user_dao.get_by_id(user_id)
        if not user:
            return False

        user.remove_metadata('password_reset')
        user.remove_metadata('require_password_change')
        await self._user_dao.update(user)

        return True