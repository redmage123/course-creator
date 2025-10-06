"""
User Management Data Access Object (DAO)

This module implements the Data Access Object (DAO) pattern for user management operations,
centralizing all SQL queries and database interactions in a single, maintainable location.

Business Context:
The User Management service is the cornerstone of the Course Creator Platform's authentication
and authorization system. It handles user registration, authentication, session management,
and role-based access control. By centralizing all SQL operations in this DAO, we achieve:
- Single source of truth for all user-related database queries
- Enhanced security through consistent data access patterns
- Improved maintainability and testing capabilities
- Clear separation between business logic and data access concerns
- Better performance through optimized query patterns

Technical Rationale:
- Follows the Single Responsibility Principle by isolating data access concerns
- Enables comprehensive transaction support for complex user operations
- Provides consistent error handling using shared platform exceptions
- Supports connection pooling for optimal database resource utilization
- Facilitates database schema evolution without affecting business logic
- Enables easier unit testing through clear interface boundaries
"""

import asyncpg
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
# Use local service exceptions
from exceptions import UserManagementException as CourseCreatorBaseException
# Import domain entities
from domain.entities.user import User, UserRole, UserStatus


class UserManagementDAO:
    """
    Data Access Object for User Management Operations
    
    This class centralizes all SQL queries and database operations for the user
    management service, following the DAO pattern for clean architecture.
    
    Business Context:
    Provides comprehensive data access methods for user lifecycle management including:
    - User registration, authentication, and profile management
    - Session creation, validation, and cleanup
    - Role-based access control and permission management
    - Student enrollment and access token management
    - Password management and security operations
    - User analytics and activity tracking
    
    Technical Implementation:
    - Uses asyncpg for high-performance PostgreSQL operations
    - Implements connection pooling for optimal resource usage
    - Provides transaction support for complex multi-table operations
    - Includes comprehensive error handling and security logging
    - Supports prepared statements for performance optimization
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize the User Management DAO with database connection pool.
        
        Business Context:
        The DAO requires a connection pool to efficiently manage database connections
        across the user management service's operations.
        
        Args:
            db_pool: AsyncPG connection pool for database operations
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)
    
    def _row_to_user(self, row: Dict[str, Any]) -> User:
        """
        Convert database row to User domain object.
        
        Business Context:
        This method encapsulates the conversion from database representation to
        domain objects, ensuring consistent object creation across all DAO methods.
        
        Args:
            row: Database row as dictionary
            
        Returns:
            User domain object
        """
        if not row:
            return None
            
        return User(
            id=str(row['id']),
            email=row['email'],
            username=row['username'],
            full_name=row['full_name'],
            first_name=row.get('first_name'),
            last_name=row.get('last_name'),
            role=UserRole(row['role']),
            status=UserStatus(row.get('status', 'active')),
            organization=row.get('organization'),
            phone=row.get('phone'),
            timezone=row.get('timezone'),
            language=row.get('language', 'en'),
            profile_picture_url=row.get('profile_picture_url'),
            bio=row.get('bio'),
            last_login=row.get('last_login'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            metadata={'hashed_password': row.get('hashed_password')} if row.get('hashed_password') else {}
        )
    
    # ================================================================
    # USER REGISTRATION AND AUTHENTICATION QUERIES
    # ================================================================
    
    async def check_user_id_exists(self, user_id: str) -> bool:
        """
        Check if a user ID already exists in the database.
        
        Business Context:
        User ID uniqueness validation is critical for maintaining data integrity and
        preventing registration conflicts when users specify custom IDs. This check
        ensures no duplicate user IDs are created in the system.
        
        Args:
            user_id: User ID to check for existence
            
        Returns:
            True if user ID exists, False otherwise
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM course_creator.users WHERE id = $1)",
                    user_id
                )
                return bool(result)
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to check user ID existence",
                error_code="USER_ID_CHECK_ERROR",
                details={"user_id": user_id},
                original_exception=e
            )
    
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """
        Create a new user account with comprehensive validation and security.
        
        Business Context:
        User registration is the entry point for all platform interactions. This operation
        creates the foundational user record with proper security attributes, role assignment,
        and initial status configuration. Supports both auto-generated and custom user IDs
        with uniqueness validation.
        
        Technical Implementation:
        - Validates email and username uniqueness before creation
        - Validates custom user ID uniqueness if provided
        - Stores hashed password (never plaintext)
        - Sets initial user status and timestamps
        - Assigns default role if not specified
        - Generates unique user ID or uses provided custom ID
        
        Args:
            user_data: Dictionary containing user registration information
                - email: User's email address (unique identifier)
                - username: Platform username (unique identifier)  
                - full_name: User's display name
                - hashed_password: Pre-hashed password for security
                - role: User role (student, instructor, org_admin, admin)
                - organization: Optional organization association
                - user_id: Optional custom user ID (will be validated for uniqueness)
                
        Returns:
            Created User object
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Check if custom user ID is provided and validate uniqueness
                if 'user_id' in user_data and user_data['user_id']:
                    custom_id = user_data['user_id']
                    id_exists = await self.check_user_id_exists(custom_id)
                    if id_exists:
                        raise CourseCreatorBaseException(
                            message="User ID already exists",
                            error_code="DUPLICATE_USER_ID_ERROR",
                            validation_errors={"user_id": "This user ID is already taken"},
                            original_exception=None
                        )
                    
                    # Use custom ID in INSERT
                    user_row = await conn.fetchrow(
                        """INSERT INTO course_creator.users (
                            id, email, username, full_name, hashed_password, role, 
                            organization, status, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) 
                        RETURNING id, email, username, full_name, role, organization, status, created_at, updated_at""",
                        custom_id,
                        user_data['email'],
                        user_data['username'],
                        user_data['full_name'],
                        user_data['hashed_password'],
                        user_data.get('role', 'student'),
                        user_data.get('organization'),
                        user_data.get('status', 'active'),
                        datetime.utcnow(),
                        datetime.utcnow()
                    )
                else:
                    # Use auto-generated ID
                    user_row = await conn.fetchrow(
                        """INSERT INTO course_creator.users (
                            email, username, full_name, hashed_password, role, 
                            organization, status, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) 
                        RETURNING id, email, username, full_name, role, organization, status, created_at, updated_at""",
                        user_data['email'],
                        user_data['username'],
                        user_data['full_name'],
                        user_data['hashed_password'],
                        user_data.get('role', 'student'),
                        user_data.get('organization'),
                        user_data.get('status', 'active'),
                        datetime.utcnow(),
                        datetime.utcnow()
                    )
                
                # Convert row to User object and include hashed password in metadata
                user_dict = dict(user_row)
                user_dict['hashed_password'] = user_data['hashed_password']
                return self._row_to_user(user_dict)
        except CourseCreatorBaseException:
            # Re-raise validation exceptions
            raise
        except asyncpg.UniqueViolationError as e:
            # Handle duplicate email/username gracefully
            raise CourseCreatorBaseException(
                message="User with this email or username already exists",
                error_code="DUPLICATE_USER_ERROR",
                validation_errors={"email": "Email already registered"},
                original_exception=e
            )
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to create user account",
                error_code="USER_CREATION_ERROR",
                details={
                    "email": user_data.get('email'),
                    "username": user_data.get('username'),
                    "role": user_data.get('role')
                },
                original_exception=e
            )
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve user information by email address for authentication.
        
        Business Context:
        Email-based user lookup is the primary method for user authentication
        and account recovery operations. This query supports login processes
        and administrative user management tasks.
        
        Args:
            email: User's email address
            
        Returns:
            User object or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                user = await conn.fetchrow(
                    """SELECT id, email, username, full_name, hashed_password, role, 
                              organization, status, created_at, updated_at, last_login
                       FROM course_creator.users WHERE email = $1""",
                    email
                )
                return self._row_to_user(dict(user)) if user else None
        except Exception as e:
            raise CourseCreatorBaseException(
                message=f"Failed to retrieve user by email",
                error_code="USER_LOOKUP_ERROR",
                details={"has_email": bool(email)},  # Don't log actual email for privacy
                original_exception=e
            )
    
    async def exists_by_email(self, email: str) -> bool:
        """
        Check if a user exists with the given email address.
        
        Business Context:
        Email existence checking is crucial for user registration validation
        and preventing duplicate account creation.
        
        Args:
            email: Email address to check
            
        Returns:
            bool: True if user exists, False otherwise
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM course_creator.users WHERE email = $1)",
                    email
                )
                return bool(result)
        except Exception as e:
            raise CourseCreatorBaseException(
                message=f"Failed to check user existence by email",
                error_code="USER_EXISTS_CHECK_ERROR",
                details={"has_email": bool(email)},  # Don't log actual email for privacy
                original_exception=e
            )
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve user information by username for authentication.
        
        Business Context:
        Username-based lookup supports flexible authentication allowing users
        to login with either email or username, improving user experience.
        
        Args:
            username: User's platform username
            
        Returns:
            User object or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                user = await conn.fetchrow(
                    """SELECT id, email, username, full_name, hashed_password, role,
                              organization, status, created_at, updated_at, last_login
                       FROM course_creator.users WHERE username = $1""",
                    username
                )
                self.logger.info(f"🔍 DB QUERY RESULT for username '{username}': {user is not None}")
                if user:
                    self.logger.info(f"🔍 User data: username={user['username']}, email={user['email']}, role={user['role']}")
                return self._row_to_user(dict(user)) if user else None
        except Exception as e:
            raise CourseCreatorBaseException(
                message=f"Failed to retrieve user by username",
                error_code="USER_LOOKUP_ERROR", 
                details={"has_username": bool(username)},  # Don't log actual username for privacy
                original_exception=e
            )
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve user information by unique user ID.
        
        Business Context:
        ID-based user lookup is used for session validation, API operations,
        and administrative tasks where the user ID is already known.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            User object or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                user = await conn.fetchrow(
                    """SELECT id, email, username, full_name, hashed_password, role, 
                              organization, status, created_at, updated_at, last_login
                       FROM course_creator.users WHERE id = $1""",
                    user_id
                )
                return self._row_to_user(dict(user)) if user else None
        except Exception as e:
            raise CourseCreatorBaseException(
                message=f"Failed to retrieve user by ID",
                error_code="USER_LOOKUP_ERROR",
                details={"user_id": user_id},
                original_exception=e
            )
    
    async def update_user_password(self, user_id: str, new_hashed_password: str) -> bool:
        """
        Update user password with security validation.
        
        Business Context:
        Password updates are critical security operations that require careful
        handling to maintain account security and audit trails.
        
        Args:
            user_id: User to update password for
            new_hashed_password: Pre-hashed new password
            
        Returns:
            True if password was updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE course_creator.users 
                       SET hashed_password = $1, updated_at = $2 
                       WHERE id = $3""",
                    new_hashed_password,
                    datetime.utcnow(),
                    user_id
                )
                # Check if any rows were affected
                return result.split()[-1] == '1'
        except Exception as e:
            raise CourseCreatorBaseException(
                message=f"Failed to update user password",
                error_code="PASSWORD_UPDATE_ERROR",
                details={"user_id": user_id},
                original_exception=e
            )
    
    async def update_user_last_login(self, user_id: str) -> bool:
        """
        Update user's last login timestamp for analytics and security.
        
        Business Context:
        Last login tracking supports security monitoring, inactive account
        identification, and user engagement analytics.
        
        Args:
            user_id: User to update last login for
            
        Returns:
            True if timestamp was updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE course_creator.users 
                       SET last_login = $1, updated_at = $2 
                       WHERE id = $3""",
                    datetime.utcnow(),
                    datetime.utcnow(),
                    user_id
                )
                return result.split()[-1] == '1'
        except Exception as e:
            raise CourseCreatorBaseException(
                message=f"Failed to update user last login",
                error_code="LOGIN_UPDATE_ERROR",
                details={"user_id": user_id},
                original_exception=e
            )
    
    # ================================================================
    # SESSION MANAGEMENT QUERIES
    # ================================================================
    
    async def create_session(self, session_data: Dict[str, Any]) -> str:
        """
        Create a new user session with token and expiration.
        
        Business Context:
        Sessions provide secure, time-limited access to platform resources.
        Each session includes authentication tokens, expiration times, and
        tracking information for security and analytics.
        
        Args:
            session_data: Dictionary containing session information
                - user_id: User the session belongs to
                - session_token: Unique session token
                - expires_at: Session expiration timestamp
                - session_type: Type of session (web, api, mobile)
                - ip_address: Optional IP address for security
                - device_info: Optional device information
                
        Returns:
            Created session ID as string
        """
        try:
            async with self.db_pool.acquire() as conn:
                session_id = await conn.fetchval(
                    """INSERT INTO sessions (
                        user_id, session_token, expires_at, session_type,
                        ip_address, device_info, created_at, last_accessed
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) 
                    RETURNING id""",
                    session_data['user_id'],
                    session_data['session_token'],
                    session_data['expires_at'],
                    session_data.get('session_type', 'web'),
                    session_data.get('ip_address'),
                    session_data.get('device_info', {}),
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                return str(session_id)
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to create user session",
                error_code="SESSION_CREATION_ERROR",
                details={"user_id": session_data.get('user_id')},
                original_exception=e
            )
    
    async def get_session_by_token(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session information by token for validation.
        
        Business Context:
        Session token validation is performed on every authenticated request
        to verify user identity and session validity.
        
        Args:
            session_token: Session token to look up
            
        Returns:
            Session record with user information or None if invalid
        """
        try:
            async with self.db_pool.acquire() as conn:
                session = await conn.fetchrow(
                    """SELECT s.*, u.email, u.username, u.role, u.status
                       FROM sessions s
                       JOIN users u ON s.user_id = u.id
                       WHERE s.session_token = $1""",
                    session_token
                )
                return dict(session) if session else None
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to retrieve session by token",
                error_code="SESSION_LOOKUP_ERROR",
                details={"has_token": bool(session_token)},  # Don't log actual token
                original_exception=e
            )
    
    async def update_session_last_accessed(self, session_token: str) -> bool:
        """
        Update session last accessed timestamp for activity tracking.
        
        Business Context:
        Session activity tracking supports timeout management and security
        monitoring by maintaining accurate last access times.
        
        Args:
            session_token: Session token to update
            
        Returns:
            True if session was updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE sessions 
                       SET last_accessed = $1 
                       WHERE session_token = $2""",
                    datetime.utcnow(),
                    session_token
                )
                return result.split()[-1] == '1'
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to update session activity",
                error_code="SESSION_UPDATE_ERROR",
                details={"has_token": bool(session_token)},
                original_exception=e
            )
    
    async def delete_session(self, session_token: str) -> bool:
        """
        Delete a specific session (logout operation).
        
        Business Context:
        Session deletion is performed during user logout to invalidate
        authentication tokens and prevent further access.
        
        Args:
            session_token: Session token to delete
            
        Returns:
            True if session was deleted successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM sessions WHERE session_token = $1",
                    session_token
                )
                return result.split()[-1] == '1'
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to delete user session",
                error_code="SESSION_DELETE_ERROR",
                details={"has_token": bool(session_token)},
                original_exception=e
            )
    
    async def delete_user_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for a specific user.
        
        Business Context:
        Bulk session deletion supports security operations like forced
        logout, account suspension, or password reset scenarios.
        
        Args:
            user_id: User to delete all sessions for
            
        Returns:
            Number of sessions deleted
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM sessions WHERE user_id = $1",
                    user_id
                )
                return int(result.split()[-1]) if result else 0
        except Exception as e:
            raise CourseCreatorBaseException(
                message=f"Failed to delete user sessions",
                error_code="BULK_SESSION_DELETE_ERROR",
                details={"user_id": user_id},
                original_exception=e
            )
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions from the database.
        
        Business Context:
        Session cleanup is a maintenance operation that removes expired
        sessions to maintain database performance and security hygiene.
        
        Returns:
            Number of expired sessions removed
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM sessions WHERE expires_at < $1",
                    datetime.utcnow()
                )
                return int(result.split()[-1]) if result else 0
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to cleanup expired sessions",
                error_code="SESSION_CLEANUP_ERROR",
                details={"cleanup_time": datetime.utcnow().isoformat()},
                original_exception=e
            )
    
    # ================================================================
    # STUDENT ACCESS MANAGEMENT QUERIES
    # ================================================================
    
    async def get_student_enrollments_by_token(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Retrieve student course enrollments by access token.
        
        Business Context:
        Students access courses using unique access tokens. This query
        retrieves all course enrollments associated with a specific token
        for course access and progress tracking.
        
        Args:
            access_token: Student's unique course access token
            
        Returns:
            List of enrollment records with course information
        """
        try:
            async with self.db_pool.acquire() as conn:
                enrollments = await conn.fetch(
                    """SELECT sce.*, c.title as course_title, c.description as course_description,
                              ci.name as instance_name, ci.start_datetime, ci.end_datetime
                       FROM student_course_enrollments sce
                       JOIN course_instances ci ON sce.course_instance_id = ci.id
                       JOIN courses c ON ci.course_id = c.id
                       WHERE sce.access_token = $1""",
                    access_token
                )
                return [dict(enrollment) for enrollment in enrollments]
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to retrieve student enrollments",
                error_code="ENROLLMENT_LOOKUP_ERROR",
                details={"has_token": bool(access_token)},
                original_exception=e
            )
    
    async def update_student_progress(self, enrollment_id: str, progress_data: Dict[str, Any]) -> bool:
        """
        Update student progress tracking information.
        
        Business Context:
        Progress tracking enables personalized learning experiences and
        analytics by recording student advancement through course materials.
        
        Args:
            enrollment_id: Enrollment record to update
            progress_data: Dictionary containing progress information
                - progress_percentage: Completion percentage (0-100)
                - last_accessed: Timestamp of last course access
                - current_module: Current learning module/section
                
        Returns:
            True if progress was updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE student_course_enrollments 
                       SET progress_percentage = $1, last_accessed = $2, 
                           current_module = $3, updated_at = $4
                       WHERE id = $5""",
                    progress_data.get('progress_percentage', 0),
                    progress_data.get('last_accessed', datetime.utcnow()),
                    progress_data.get('current_module'),
                    datetime.utcnow(),
                    enrollment_id
                )
                return result.split()[-1] == '1'
        except Exception as e:
            raise CourseCreatorBaseException(
                message=f"Failed to update student progress",
                error_code="PROGRESS_UPDATE_ERROR",
                details={"enrollment_id": enrollment_id},
                original_exception=e
            )
    
    # ================================================================
    # USER ANALYTICS AND REPORTING QUERIES
    # ================================================================
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        Retrieve comprehensive user statistics for administrative reporting.
        
        Business Context:
        User statistics support administrative decision making, resource
        planning, and platform growth analysis by providing key metrics.
        
        Returns:
            Dictionary containing user statistics and metrics
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Get basic user counts by role
                role_counts = await conn.fetch(
                    """SELECT role, COUNT(*) as count 
                       FROM course_creator.users 
                       WHERE status = 'active' 
                       GROUP BY role"""
                )
                
                # Get total active users
                total_active = await conn.fetchval(
                    "SELECT COUNT(*) FROM course_creator.users WHERE status = 'active'"
                )
                
                # Get recent user registrations (last 30 days)
                recent_registrations = await conn.fetchval(
                    """SELECT COUNT(*) FROM course_creator.users 
                       WHERE created_at > $1""",
                    datetime.utcnow() - timedelta(days=30)
                )
                
                # Get active sessions count
                active_sessions = await conn.fetchval(
                    """SELECT COUNT(*) FROM sessions 
                       WHERE expires_at > $1""",
                    datetime.utcnow()
                )
                
                return {
                    "total_active_users": total_active or 0,
                    "role_distribution": {row['role']: row['count'] for row in role_counts},
                    "recent_registrations": recent_registrations or 0,
                    "active_sessions": active_sessions or 0
                }
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to retrieve user statistics",
                error_code="STATS_QUERY_ERROR",
                details={"query_time": datetime.utcnow().isoformat()},
                original_exception=e
            )
    
    async def get_users_by_role(self, role: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve users by role with pagination support.
        
        Business Context:
        Role-based user queries support administrative tasks like user
        management, communication, and role-specific operations.
        
        Args:
            role: User role to filter by
            limit: Maximum number of users to return
            offset: Number of users to skip (for pagination)
            
        Returns:
            List of user records matching the specified role
        """
        try:
            async with self.db_pool.acquire() as conn:
                users = await conn.fetch(
                    """SELECT id, email, username, full_name, role, organization, 
                              status, created_at, last_login
                       FROM course_creator.users 
                       WHERE role = $1 AND status = 'active'
                       ORDER BY created_at DESC
                       LIMIT $2 OFFSET $3""",
                    role, limit, offset
                )
                return [dict(user) for user in users]
        except Exception as e:
            raise CourseCreatorBaseException(
                message=f"Failed to retrieve users by role {role}",
                error_code="USER_ROLE_QUERY_ERROR",
                details={"role": role, "limit": limit, "offset": offset},
                original_exception=e
            )
    
    # ================================================================
    # TRANSACTION SUPPORT AND BATCH OPERATIONS
    # ================================================================
    
    async def execute_user_transaction(self, operations: List[tuple]) -> List[Any]:
        """
        Execute multiple user-related database operations within a single transaction.
        
        Business Context:
        Complex user operations often require multiple database changes that must
        succeed or fail together to maintain data consistency and integrity.
        
        Args:
            operations: List of (query, params) tuples to execute
            
        Returns:
            List of operation results
        """
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    results = []
                    for query, params in operations:
                        if params:
                            result = await conn.execute(query, *params)
                        else:
                            result = await conn.execute(query)
                        results.append(result)
                    return results
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to execute user transaction operations",
                error_code="USER_TRANSACTION_ERROR",
                details={"operation_count": len(operations)},
                original_exception=e
            )

    # ================================================================
    # ALIAS METHODS FOR SERVICE COMPATIBILITY
    # ================================================================
    
    async def exists_by_username(self, username: str) -> bool:
        """Check if a user exists with the given username."""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM course_creator.users WHERE username = $1)",
                    username
                )
                return bool(result)
        except Exception as e:
            raise CourseCreatorBaseException(
                message=f"Failed to check user existence by username",
                error_code="USER_EXISTS_CHECK_ERROR",
                details={"has_username": bool(username)},
                original_exception=e
            )
    
    async def exists_by_id(self, user_id: str) -> bool:
        """Alias for check_user_id_exists"""
        return await self.check_user_id_exists(user_id)
    
    async def get_by_id(self, user_id: str):
        """Alias for get_user_by_id"""
        return await self.get_user_by_id(user_id)
    
    async def get_by_email(self, email: str):
        """Alias for get_user_by_email"""
        return await self.get_user_by_email(email)
    
    async def get_by_username(self, username: str):
        """Alias for get_user_by_username"""
        return await self.get_user_by_username(username)
    
    async def get_by_role(self, role: str):
        """Alias for get_users_by_role"""
        return await self.get_users_by_role(role)
    
    async def create(self, user_data):
        """Alias for create_user"""
        return await self.create_user(user_data)
    
    async def get_user_id_by_prefix(self, prefix: str) -> Optional[str]:
        """Get full user ID by matching prefix"""
        async with self.db_pool.acquire() as connection:
            try:
                result = await connection.fetchval(
                    "SELECT id FROM users WHERE id::text LIKE $1 LIMIT 1",
                    f"{prefix}%"
                )
                return result
            except Exception as e:
                self.logger.error(f"Error fetching user by prefix: {e}")
                return None
    
    async def update(self, user_data):
        """Update user with new data"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE course_creator.users 
                       SET email = $2, username = $3, full_name = $4, role = $5, 
                           organization = $6, status = $7, updated_at = CURRENT_TIMESTAMP
                       WHERE id = $1""",
                    user_data['id'], user_data.get('email'), user_data.get('username'),
                    user_data.get('full_name'), user_data.get('role'), 
                    user_data.get('organization'), user_data.get('status')
                )
                return user_data
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to update user",
                error_code="USER_UPDATE_ERROR",
                details={"user_id": user_data.get('id')},
                original_exception=e
            )
    
    async def delete(self, user_id: str) -> bool:
        """Delete user by ID"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM course_creator.users WHERE id = $1",
                    user_id
                )
                return True
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to delete user",
                error_code="USER_DELETE_ERROR",
                details={"user_id": user_id},
                original_exception=e
            )
    
    async def get_all(self):
        """Get all users"""
        try:
            async with self.db_pool.acquire() as conn:
                users = await conn.fetch("SELECT * FROM course_creator.users")
                return [dict(user) for user in users]
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to get all users",
                error_code="USER_LIST_ERROR",
                original_exception=e
            )
    
    async def count_by_role(self, role: str) -> int:
        """Count users by role"""
        try:
            async with self.db_pool.acquire() as conn:
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM course_creator.users WHERE role = $1",
                    role
                )
                return int(count)
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to count users by role",
                error_code="USER_COUNT_ERROR",
                details={"role": role},
                original_exception=e
            )
    
    async def count_by_status(self, status: str) -> int:
        """Count users by status"""
        try:
            async with self.db_pool.acquire() as conn:
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM course_creator.users WHERE status = $1",
                    status
                )
                return int(count)
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to count users by status",
                error_code="USER_COUNT_ERROR",
                details={"status": status},
                original_exception=e
            )
    
    async def get_inactive_users(self, days: int):
        """Get users inactive for specified days"""
        try:
            async with self.db_pool.acquire() as conn:
                users = await conn.fetch(
                    """SELECT * FROM course_creator.users 
                       WHERE last_login < CURRENT_TIMESTAMP - INTERVAL '%s days'""",
                    days
                )
                return [dict(user) for user in users]
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to get inactive users",
                error_code="USER_QUERY_ERROR",
                details={"days": days},
                original_exception=e
            )
    
    async def get_recently_created(self, days: int):
        """Get users created within specified days"""
        try:
            async with self.db_pool.acquire() as conn:
                users = await conn.fetch(
                    """SELECT * FROM course_creator.users 
                       WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '%s days'""",
                    days
                )
                return [dict(user) for user in users]
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to get recently created users",
                error_code="USER_QUERY_ERROR",
                details={"days": days},
                original_exception=e
            )
    
    async def search(self, query: str, limit: int = 50):
        """Search users by name or email"""
        try:
            async with self.db_pool.acquire() as conn:
                users = await conn.fetch(
                    """SELECT * FROM course_creator.users 
                       WHERE full_name ILIKE $1 OR email ILIKE $1 OR username ILIKE $1
                       LIMIT $2""",
                    f"%{query}%", limit
                )
                return [dict(user) for user in users]
        except Exception as e:
            raise CourseCreatorBaseException(
                message="Failed to search users",
                error_code="USER_SEARCH_ERROR",
                details={"query": query, "limit": limit},
                original_exception=e
            )