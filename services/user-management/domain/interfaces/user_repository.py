"""
User Repository Interface - Data Access Layer Abstraction

This module defines the abstract interface for user data access operations
within the User Management Service. It follows the Repository pattern to
abstract database operations and enable clean architecture principles.

Architectural Benefits:
    Interface Segregation: Focused interface specifically for user data access
    Dependency Inversion: Business logic depends on this abstraction, not concrete DB
    Testability: Enables easy mocking and testing of business logic
    Database Agnostic: Concrete implementations can use any storage technology
    Clean Architecture: Separates domain logic from infrastructure concerns

Repository Pattern Benefits:
    - Centralizes data access logic for user entities
    - Provides consistent API for user operations across the application
    - Enables caching strategies to be implemented transparently
    - Supports complex queries without exposing SQL to business logic
    - Facilitates data access optimization without affecting business rules

Interface Design Principles:
    - All methods are async to support modern async/await patterns
    - Methods return domain entities (User), not database records
    - Clear separation between existence checks and data retrieval
    - Bulk operations support for performance-critical scenarios
    - Pagination support for large datasets
    - Search capabilities for user discovery features

Implementation Notes:
    Concrete implementations should:
    - Handle database connection management
    - Implement proper error handling and logging
    - Support transaction management where appropriate
    - Include appropriate indexes for performance
    - Validate input parameters and sanitize queries

Author: Course Creator Platform Team
Version: 2.3.0
Last Updated: 2025-08-02
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.entities.user import User, UserRole, UserStatus

class IUserRepository(ABC):
    """
    Abstract base class defining the contract for user data access operations.
    
    This interface defines all the methods required for user data persistence
    and retrieval within the User Management Service. It serves as the boundary
    between the domain layer and the infrastructure layer, ensuring that business
    logic remains independent of specific database implementations.
    
    Design Principles:
        - All operations are async to support high-concurrency scenarios
        - Methods operate on domain entities, not database-specific types
        - Clear naming convention follows domain language
        - Comprehensive CRUD operations with additional query methods
        - Support for common administrative and analytical operations
    
    Usage:
        This interface should be implemented by concrete repository classes
        such as PostgreSQLUserRepository, and injected into service classes
        via dependency injection.
    
    Thread Safety:
        Implementations should be thread-safe and support concurrent access
        patterns common in async web applications.
    """
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """
        Create a new user in the data store.
        
        This method persists a new user entity to the database and returns
        the created user with any database-generated fields populated
        (such as ID, timestamps, etc.).
        
        Business Rules Enforced:
            - Email addresses must be unique across all users
            - Usernames must be unique across all users
            - Password must be hashed before storage
            - Created timestamp should be automatically set
            - Default user status should be applied if not specified
        
        Args:
            user (User): User entity to create. Should contain all required
                        fields except database-generated ones (ID, timestamps).
                        
        Returns:
            User: The created user entity with database-generated fields
                  populated (ID, created_at, updated_at).
                  
        Raises:
            DuplicateEmailError: If email already exists in the system
            DuplicateUsernameError: If username already exists in the system
            ValidationError: If user data fails validation rules
            DatabaseError: If database operation fails
            
        Implementation Notes:
            - Should validate email format and uniqueness
            - Should validate username format and uniqueness
            - Should handle password hashing if not already done
            - Should set appropriate default values for optional fields
            - Should return the complete user object including generated ID
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by their unique identifier.
        
        This is the primary method for user lookup when the user ID is known.
        It's commonly used for:
        - Session validation (matching JWT user_id to database record)
        - Profile retrieval for authenticated users
        - User detail lookups in administrative interfaces
        - Cross-service user information requests
        
        Args:
            user_id (str): Unique identifier for the user. Should be a valid
                          UUID string or other unique identifier format used
                          by the system.
                          
        Returns:
            Optional[User]: User entity if found, None if no user exists
                           with the given ID. Returns complete user object
                           including all profile information.
                           
        Raises:
            ValidationError: If user_id format is invalid
            DatabaseError: If database query fails
            
        Performance Notes:
            - This should be optimized as it's called frequently
            - Should use primary key index for fast lookup
            - Consider caching for frequently accessed users
            - Should not perform joins unless necessary for user entity
        """
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.
        
        This method is primarily used during authentication flows where
        users log in with their email address. It's also used for:
        - Password reset flows (finding user by email)
        - User registration (checking for existing email)
        - Email-based user lookup in administrative tools
        - Integration with external systems that identify users by email
        
        Args:
            email (str): Email address to search for. Should be normalized
                        (lowercased) before the search to ensure case-insensitive
                        matching.
                        
        Returns:
            Optional[User]: User entity if found, None if no user exists
                           with the given email address.
                           
        Raises:
            ValidationError: If email format is invalid
            DatabaseError: If database query fails
            
        Implementation Notes:
            - Email comparison should be case-insensitive
            - Should use unique index on email field for performance
            - Consider normalizing email input (lowercase, trim whitespace)
            - Email should be the primary login credential
        """
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve a user by their username.
        
        Username lookup is used as an alternative authentication method
        and for user discovery features. Common use cases include:
        - Alternative login method (username instead of email)
        - User profile lookups by username
        - User mention features (@username)
        - Public user directory searches
        
        Args:
            username (str): Username to search for. Should be case-sensitive
                           as usernames are typically case-sensitive identifiers.
                           
        Returns:
            Optional[User]: User entity if found, None if no user exists
                           with the given username.
                           
        Raises:
            ValidationError: If username format is invalid
            DatabaseError: If database query fails
            
        Implementation Notes:
            - Username comparison should be case-sensitive
            - Should use unique index on username field for performance
            - Username should follow platform naming conventions
            - Consider character restrictions (alphanumeric, underscores, etc.)
        """
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """
        Update an existing user's information in the data store.
        
        This method modifies an existing user record with new information.
        It's used for:
        - Profile updates (name, email, preferences)
        - Status changes (active/inactive/suspended)
        - Role modifications (admin operations)
        - Password changes
        - Last login timestamp updates
        
        Args:
            user (User): User entity with updated information. Must include
                        the user ID to identify which record to update.
                        
        Returns:
            User: The updated user entity with current timestamp in updated_at
                  field and any other database-computed fields.
                  
        Raises:
            UserNotFoundError: If user with given ID doesn't exist
            DuplicateEmailError: If email change conflicts with existing user
            DuplicateUsernameError: If username change conflicts with existing user
            ValidationError: If updated data fails validation rules
            DatabaseError: If database operation fails
            
        Implementation Notes:
            - Should validate uniqueness constraints on email/username changes
            - Should update the updated_at timestamp automatically
            - Should preserve fields that weren't explicitly changed
            - Should handle concurrent modification scenarios
            - Should validate that required fields remain populated
        """
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """
        Delete a user from the data store.
        
        This method permanently removes a user record from the database.
        Use with caution as this operation is typically irreversible.
        Common scenarios include:
        - Account termination requests
        - Administrative user removal
        - Cleanup of test/invalid accounts
        - GDPR compliance (right to be forgotten)
        
        Args:
            user_id (str): Unique identifier of the user to delete.
                          
        Returns:
            bool: True if user was successfully deleted, False if user
                  was not found or deletion failed.
                  
        Raises:
            DatabaseError: If database operation fails
            ForeignKeyConstraintError: If user has related data that prevents deletion
            
        Implementation Notes:
            - Consider soft delete (status marking) instead of hard delete
            - Should handle foreign key constraints gracefully
            - May need to cascade delete or nullify related records
            - Should log deletion operations for audit purposes
            - Consider data retention policies and legal requirements
            
        Security Considerations:
            - Should verify authorization before allowing deletion
            - Should not allow users to delete themselves in most cases
            - Should require admin privileges for user deletion
        """
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """
        Check if a user exists with the given email address.
        
        This method provides a lightweight way to verify email uniqueness
        without retrieving the full user object. Commonly used for:
        - Registration flow email validation
        - Preventing duplicate account creation
        - Email availability checks
        - Quick existence verification before expensive operations
        
        Args:
            email (str): Email address to check for existence.
                        Should be normalized for consistent checking.
                        
        Returns:
            bool: True if a user exists with this email, False otherwise.
            
        Raises:
            ValidationError: If email format is invalid
            DatabaseError: If database query fails
            
        Performance Notes:
            - Should be optimized for speed (index-only lookup)
            - More efficient than get_by_email when only existence matters
            - Should use the same normalization as get_by_email
            - Consider caching for frequently checked emails
        """
        pass
    
    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """
        Check if a user exists with the given username.
        
        This method provides a lightweight way to verify username uniqueness
        without retrieving the full user object. Commonly used for:
        - Registration flow username validation
        - Preventing duplicate username selection
        - Username availability checks
        - Quick existence verification for user mentions
        
        Args:
            username (str): Username to check for existence.
                           Case-sensitive check should match get_by_username behavior.
                           
        Returns:
            bool: True if a user exists with this username, False otherwise.
            
        Raises:
            ValidationError: If username format is invalid
            DatabaseError: If database query fails
            
        Performance Notes:
            - Should be optimized for speed (index-only lookup)
            - More efficient than get_by_username when only existence matters
            - Should use the same case sensitivity as get_by_username
            - Consider caching for frequently checked usernames
        """
        pass
    
    @abstractmethod
    async def get_by_role(self, role: UserRole) -> List[User]:
        """
        Retrieve all users with a specific role.
        
        This method is used for administrative operations and role-based
        user management. Common use cases include:
        - Listing all administrators for security purposes
        - Finding all instructors for course assignment
        - Gathering students for bulk operations
        - Role-based reporting and analytics
        
        Args:
            role (UserRole): The role to filter users by. Should be one of
                           the defined UserRole enum values.
                           
        Returns:
            List[User]: List of all users with the specified role.
                       Returns empty list if no users have this role.
                       
        Raises:
            ValidationError: If role is not a valid UserRole value
            DatabaseError: If database query fails
            
        Performance Notes:
            - Should use index on role field for efficient filtering
            - Consider pagination for roles with many users
            - May return large result sets for common roles like 'student'
            - Consider implementing pagination in future versions
            
        Implementation Notes:
            - Should preserve user privacy by only returning necessary fields
            - Consider access control - who can see what roles
            - Should handle role hierarchy if applicable
        """
        pass
    
    @abstractmethod
    async def get_by_status(self, status: UserStatus) -> List[User]:
        """
        Retrieve all users with a specific status.
        
        User status filtering is essential for administrative operations
        and user lifecycle management. Common use cases include:
        - Finding inactive users for cleanup operations
        - Listing suspended users for review
        - Identifying pending activations
        - Status-based reporting and compliance
        
        Args:
            status (UserStatus): The status to filter users by. Should be one
                               of the defined UserStatus enum values (active,
                               inactive, suspended, pending, etc.).
                               
        Returns:
            List[User]: List of all users with the specified status.
                       Returns empty list if no users have this status.
                       
        Raises:
            ValidationError: If status is not a valid UserStatus value
            DatabaseError: If database query fails
            
        Performance Notes:
            - Should use index on status field for efficient filtering
            - Consider pagination for statuses with many users
            - Most queries will be for 'active' status which may be large
            - Consider implementing pagination for large result sets
            
        Security Notes:
            - Should respect access controls for sensitive status types
            - Consider filtering out sensitive user information
            - Suspended user information may need special handling
        """
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 50) -> List[User]:
        """
        Search for users across multiple fields using a query string.
        
        This method provides fuzzy search capabilities across user fields
        to support user discovery and administrative search functions.
        Search is performed across:
        - Full name (first name + last name)
        - Email address
        - Username
        - Display name (if different from full name)
        
        Args:
            query (str): Search term to match against user fields.
                        Should support partial matches and be case-insensitive.
            limit (int): Maximum number of results to return. Defaults to 50
                        to prevent performance issues with large result sets.
                        
        Returns:
            List[User]: List of users matching the search query, ordered by
                       relevance or alphabetically. Limited to specified count.
                       
        Raises:
            ValidationError: If query is empty or contains invalid characters
            DatabaseError: If database query fails
            
        Implementation Notes:
            - Should support partial matches (LIKE '%query%' or similar)
            - Should be case-insensitive for better user experience
            - Should sanitize input to prevent SQL injection
            - Consider full-text search capabilities for better performance
            - Should respect user privacy settings
            - Consider highlighting matching terms in results
            
        Performance Considerations:
            - Limit result sets to prevent performance degradation
            - Consider using database full-text search features
            - May benefit from search indexes on commonly searched fields
            - Consider caching for common search terms
        """
        pass
    
    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        Retrieve all users with pagination support.
        
        This method provides access to the complete user list with pagination
        to handle large datasets efficiently. Used for:
        - Administrative user management interfaces
        - User export operations
        - Bulk operations across all users
        - User directory displays
        
        Args:
            limit (int): Maximum number of users to return in this page.
                        Defaults to 100. Should have reasonable upper bound
                        to prevent memory/performance issues.
            offset (int): Number of users to skip before starting to return
                         results. Used for pagination. Defaults to 0.
                         
        Returns:
            List[User]: List of users starting from offset position,
                       limited to specified count. Ordered consistently
                       (typically by creation date or username).
                       
        Raises:
            ValidationError: If limit or offset values are invalid
            DatabaseError: If database query fails
            
        Implementation Notes:
            - Should enforce reasonable limits to prevent resource exhaustion
            - Should use consistent ordering for predictable pagination
            - Consider using cursor-based pagination for better performance
            - Should include total count information if needed by callers
            - Should respect user privacy and access control settings
            
        Performance Considerations:
            - Use database-level pagination (LIMIT/OFFSET)
            - Consider using indexes for consistent ordering
            - Large offset values may perform poorly
            - Consider cursor-based pagination for large datasets
        """
        pass
    
    @abstractmethod
    async def count_by_role(self, role: UserRole) -> int:
        """
        Count the number of users with a specific role.
        
        This method provides efficient counting for analytics and reporting
        without retrieving full user objects. Used for:
        - Dashboard statistics and metrics
        - Role distribution analysis
        - Capacity planning (how many instructors vs students)
        - Access control decisions
        - Billing calculations based on user types
        
        Args:
            role (UserRole): The role to count users for.
                           
        Returns:
            int: Number of users with the specified role.
                 Returns 0 if no users have this role.
                 
        Raises:
            ValidationError: If role is not a valid UserRole value
            DatabaseError: If database query fails
            
        Performance Notes:
            - Should use database COUNT() function for efficiency
            - Should use index on role field for fast counting
            - Much more efficient than len(get_by_role()) for large datasets
            - Consider caching counts for frequently requested roles
            
        Implementation Notes:
            - Should be atomic and consistent with get_by_role results
            - Should handle concurrent modifications gracefully
            - Consider whether to count only active users or all users
        """
        pass
    
    @abstractmethod
    async def count_by_status(self, status: UserStatus) -> int:
        """
        Count the number of users with a specific status.
        
        This method provides efficient status-based counting for monitoring
        and administrative purposes. Used for:
        - System health monitoring (active vs inactive users)
        - Compliance reporting (suspended users, pending activations)
        - User lifecycle analytics
        - Cleanup operation planning
        - Dashboard status indicators
        
        Args:
            status (UserStatus): The status to count users for.
                               
        Returns:
            int: Number of users with the specified status.
                 Returns 0 if no users have this status.
                 
        Raises:
            ValidationError: If status is not a valid UserStatus value
            DatabaseError: If database query fails
            
        Performance Notes:
            - Should use database COUNT() function for efficiency
            - Should use index on status field for fast counting
            - Much more efficient than len(get_by_status()) for large datasets
            - Consider caching counts for frequently requested statuses
            
        Implementation Notes:
            - Should be atomic and consistent with get_by_status results
            - Should handle concurrent status changes gracefully
            - Consider real-time vs eventually consistent counting needs
        """
        pass
    
    @abstractmethod
    async def get_recently_created(self, days: int = 7) -> List[User]:
        """
        Retrieve users created within the specified number of days.
        
        This method helps track user growth and identify recent registrations
        for various purposes:
        - Welcome email campaigns for new users
        - User onboarding flow management
        - Registration trend analysis
        - New user support and engagement
        - Administrative review of recent sign-ups
        
        Args:
            days (int): Number of days back from current time to include
                       users. Defaults to 7 days. Should be positive integer.
                       
        Returns:
            List[User]: List of users created within the specified timeframe,
                       typically ordered by creation date (newest first).
                       
        Raises:
            ValidationError: If days parameter is invalid (negative or zero)
            DatabaseError: If database query fails
            
        Implementation Notes:
            - Should use created_at timestamp for filtering
            - Should handle timezone considerations appropriately
            - Consider using database date functions for accurate filtering
            - Should order results by creation date for consistency
            - Consider pagination for large time ranges
            
        Performance Considerations:
            - Should use index on created_at field
            - Consider limiting result set size for performance
            - May benefit from date-partitioned tables in large systems
        """
        pass
    
    @abstractmethod
    async def get_inactive_users(self, days: int = 30) -> List[User]:
        """
        Retrieve users who haven't logged in for the specified number of days.
        
        This method identifies inactive users for engagement campaigns,
        cleanup operations, and user retention analysis:
        - Re-engagement email campaigns
        - Account cleanup and archival processes
        - User activity analytics and reporting
        - License optimization (removing unused accounts)
        - Identifying users who may need support
        
        Args:
            days (int): Number of days since last login to consider a user
                       inactive. Defaults to 30 days. Should be positive.
                       
        Returns:
            List[User]: List of users who haven't logged in within the
                       specified timeframe, ordered by last login date
                       (oldest first).
                       
        Raises:
            ValidationError: If days parameter is invalid
            DatabaseError: If database query fails
            
        Implementation Notes:
            - Should use last_login_at timestamp for filtering
            - Should handle users who have never logged in appropriately
            - Should consider timezone handling for accurate calculations
            - Should exclude already inactive/suspended users if appropriate
            - Consider different inactivity thresholds for different user roles
            
        Performance Considerations:
            - Should use index on last_login_at field
            - May return large result sets - consider pagination
            - Consider caching for frequently used time periods
            - Should handle null last_login_at values efficiently
        """
        pass
    
    @abstractmethod
    async def bulk_update_status(self, user_ids: List[str], status: UserStatus) -> int:
        """
        Update the status of multiple users in a single operation.
        
        This method provides efficient bulk status updates for administrative
        operations that need to affect many users simultaneously:
        - Bulk user activation/deactivation
        - Mass suspension operations
        - Status cleanup operations
        - Emergency user lockout procedures
        - Batch processing of user lifecycle changes
        
        Args:
            user_ids (List[str]): List of user IDs to update. Should contain
                                 valid user identifiers.
            status (UserStatus): New status to apply to all specified users.
                               
        Returns:
            int: Number of users actually updated. May be less than the
                 number of IDs provided if some users don't exist or
                 updates fail.
                 
        Raises:
            ValidationError: If user_ids list is empty or status is invalid
            DatabaseError: If database operation fails
            
        Implementation Notes:
            - Should use database bulk update operations for efficiency
            - Should update updated_at timestamp for all affected users
            - Should handle non-existent user IDs gracefully
            - Should be atomic - either all updates succeed or none do
            - Should validate that status transitions are allowed
            - Should log bulk operations for audit purposes
            
        Performance Considerations:
            - Use database bulk update features (UPDATE ... WHERE id IN ...)
            - Consider batch size limits to prevent timeout issues
            - Should use transaction for atomicity
            - Much more efficient than individual update calls
            
        Security Considerations:
            - Should verify authorization for bulk operations
            - Should validate that all user IDs belong to authorized scope
            - Should log who performed bulk operations and when
        """
        pass