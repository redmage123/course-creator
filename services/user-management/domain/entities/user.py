"""
User Domain Entity - Core Business Model
  
This module defines the User domain entity, which serves as the central business
model for user management within the Course Creator Platform. It encapsulates
all user-related business logic, validation rules, and behavioral operations.

Domain-Driven Design Principles:
    - Entity Pattern: User has a unique identity (ID) and lifecycle
    - Rich Domain Model: Contains business logic and behavior, not just data
    - Encapsulation: Internal validation and state management
    - Value Objects: UserRole and UserStatus as immutable values
    - Invariants: Enforces business rules through validation

Business Context:
    The User entity represents any person who interacts with the Course Creator
    Platform, including students, instructors, and administrators. It manages:
    - Authentication credentials and identity
    - Role-based permissions and capabilities
    - Profile information and personalization
    - Status lifecycle (active, inactive, suspended, pending)
    - Metadata for extensibility and customization

Architectural Benefits:
    - Single Responsibility: Focuses solely on user domain concerns
    - Business Logic Centralization: All user rules in one place
    - Immutable Enums: UserRole and UserStatus prevent invalid states
    - Defensive Programming: Comprehensive validation and error handling
    - Rich API: Business-meaningful methods beyond simple getters/setters

Security Considerations:
    - Email validation prevents malformed addresses
    - Username validation enforces consistent naming conventions
    - Phone validation ensures proper format for notifications
    - No password storage (handled by authentication service)
    - Metadata system for extensible user attributes

Author: Course Creator Platform Team
Version: 2.3.0
Last Updated: 2025-08-02
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
import re

class UserRole(Enum):
    """
    User Role Enumeration - Defines Role-Based Access Control Levels
    
    This enumeration defines the primary roles within the Course Creator
    Platform, establishing a clear hierarchy of permissions and capabilities.
    
    Role Hierarchy (ascending privilege order):
        1. STUDENT: Basic user with course consumption privileges
        2. INSTRUCTOR: Content creator with course management privileges
        3. ORGANIZATION_ADMIN: Organization-level administrator with org management privileges
        4. SITE_ADMIN: Platform-wide system administrator with full privileges
    
    Design Rationale:
        - Enum provides type safety and prevents invalid role values
        - String values enable database storage and API serialization
        - Clear hierarchy enables role-based authorization decisions
        - Limited set prevents role proliferation and complexity
    
    Integration Notes:
        - Enhanced RBAC system (organization-management service) provides
          more granular permissions within these basic role categories
        - This service handles basic role assignment and validation
        - Cross-service authorization uses these roles as base permissions
    
    Usage Examples:
        user.role = UserRole.INSTRUCTOR
        if user.role == UserRole.ADMIN:
            # Admin-specific operations
    """
    STUDENT = "student"                    # Basic users who consume course content
    INSTRUCTOR = "instructor"              # Content creators and course managers
    ORGANIZATION_ADMIN = "organization_admin"  # Organization-level administrators
    SITE_ADMIN = "site_admin"              # Platform-wide system administrators

class UserStatus(Enum):
    """
    User Status Enumeration - Defines User Account Lifecycle States
    
    This enumeration manages the lifecycle of user accounts within the platform,
    controlling access permissions and account availability. Each status represents
    a distinct state in the user account lifecycle with specific implications.
    
    Status Definitions:
        ACTIVE: User account is fully operational and accessible
            - Can log in and access all authorized features
            - Receives notifications and communications
            - Full participation in platform activities
            
        INACTIVE: User account is temporarily disabled or dormant
            - Cannot log in or access platform features
            - Used for voluntary account deactivation
            - Can be reactivated by user or admin
            
        SUSPENDED: User account is administratively restricted
            - Cannot log in due to policy violations or security concerns
            - Requires admin intervention to restore access
            - More serious than inactive status
            
        PENDING: User account is awaiting activation or verification
            - New registrations pending email verification
            - Accounts awaiting admin approval
            - Temporary state during onboarding process
    
    Business Rules:
        - Only ACTIVE users can authenticate and use the platform
        - Status transitions should be logged for audit purposes
        - Some operations (like password reset) may work for non-ACTIVE users
        - Status changes should trigger appropriate notifications
    
    Security Implications:
        - SUSPENDED status used for security incident response
        - INACTIVE allows users to voluntarily limit their exposure
        - PENDING prevents unauthorized account usage
        - Status checks are critical for authorization decisions
    """
    ACTIVE = "active"        # Fully operational user account
    INACTIVE = "inactive"    # Temporarily disabled user account
    SUSPENDED = "suspended"  # Administratively restricted account
    PENDING = "pending"      # Awaiting activation or verification

@dataclass
class User:
    """
    User Domain Entity - Rich Business Model with Behavior and Validation
    
    This class represents a user within the Course Creator Platform, implementing
    the Entity pattern from Domain-Driven Design. It encapsulates user identity,
    profile information, business rules, and behavioral operations.
    
    Design Patterns Applied:
        - Entity Pattern: Has unique identity (ID) and tracks lifecycle
        - Rich Domain Model: Contains business logic, not just data storage
        - Value Objects: Uses UserRole and UserStatus enums for type safety
        - Builder Pattern: Flexible initialization with default values
        - Template Method: Consistent validation and update patterns
    
    Core Responsibilities:
        - User identity management (ID, email, username)
        - Profile information storage and validation
        - Role and permission management
        - Status lifecycle management
        - Business rule enforcement
        - Metadata and extensibility support
    
    Business Rules Enforced:
        1. Email addresses must be unique and properly formatted
        2. Usernames must be unique and follow naming conventions
        3. All users must have a display name (full_name)
        4. Role changes must be validated and logged
        5. Status changes affect platform access permissions
        6. Profile updates must maintain data integrity
    
    Validation Strategy:
        - Constructor validation ensures object invariants
        - Method-level validation for state changes
        - Regular expression patterns for format validation
        - Type checking for enum values
        - Business rule validation for complex constraints
    
    Performance Considerations:
        - Immutable after creation patterns for thread safety
        - Lazy validation to avoid unnecessary processing
        - Efficient dictionary serialization for API responses
        - Minimal memory footprint through optional fields
    
    Security Features:
        - No password storage (delegated to authentication service)
        - Email and phone format validation
        - Username sanitization and constraints
        - Metadata system for secure additional attributes
        - Audit trail through updated_at timestamps
    
    Integration Points:
        - Authentication Service: Uses email/username for login
        - Authorization Service: Role and status for permissions
        - Profile Service: Full profile information management
        - Analytics Service: User activity and metadata tracking
        - Organization Service: Enhanced RBAC integration
    
    Usage Examples:
        # Create new user
        user = User(
            email="john@example.com",
            username="johndoe",
            full_name="John Doe",
            role=UserRole.STUDENT
        )
        
        # Update profile
        user.update_profile(timezone="America/New_York", bio="Student")
        
        # Change role
        user.change_role(UserRole.INSTRUCTOR)
        
        # Check permissions
        if user.can_create_courses():
            # Allow course creation
    """
    email: str
    username: str
    full_name: str
    role: UserRole = UserRole.STUDENT
    status: UserStatus = UserStatus.ACTIVE
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: str = "en"
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """
        Post-initialization hook for dataclass validation and setup.
        
        This method is automatically called after the dataclass __init__ method
        completes. It ensures that the User object is in a valid state immediately
        after creation, preventing invalid User instances from existing.
        
        Operations Performed:
            1. Validate all user data against business rules
            2. Auto-generate full_name from first_name and last_name if needed
            3. Ensure updated_at timestamp is current
            4. Apply any default business logic
        
        Why Post-Init Validation:
            - Ensures object invariants are maintained from creation
            - Prevents invalid objects from being constructed
            - Centralizes validation logic in one place
            - Supports dataclass initialization patterns
        
        Auto-Generation Logic:
            - If full_name is empty but first_name and last_name exist,
              automatically constructs full_name as "first_name last_name"
            - This supports flexible user creation patterns
            - Maintains consistency in display name availability
        
        Raises:
            ValueError: If any validation rule fails during initialization
        """
        self.validate()
        
        """
        Auto-generate full_name if not provided but component names exist.
        This supports user creation workflows where individual name components
        are provided separately but we need a unified display name.
        """
        if not self.full_name and self.first_name and self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}"
    
    def validate(self) -> None:
        """
        Comprehensive validation of user data against business rules.
        
        This method enforces all business rules and data integrity constraints
        for user entities. It's called during initialization and after any
        modification to ensure the user object remains in a valid state.
        
        Validation Rules Enforced:
            1. Email: Required, properly formatted, suitable for authentication
            2. Username: Required, 3-30 chars, alphanumeric + underscores only
            3. Full Name: Required, minimum 2 characters for meaningful identity
            4. Phone: Optional, but if provided must be international format
        
        Why These Rules:
            - Email validation prevents authentication failures
            - Username constraints ensure URL-safe and database-friendly identifiers
            - Full name requirement ensures users have meaningful display names
            - Phone validation enables reliable SMS notifications
        
        Validation Strategy:
            - Fail fast: Stop at first validation error
            - Clear error messages: Help users understand what's wrong
            - Regular expressions: Consistent format validation
            - Optional field handling: Only validate if provided
        
        Raises:
            ValueError: Specific error message indicating which validation failed
                       and what the correct format should be
        
        Design Notes:
            - Uses private helper methods for specific format validation
            - Separates required field validation from format validation
            - Provides actionable error messages for user feedback
        """
        """
        Required field validation - these fields are essential for user identity
        and platform functionality
        """
        if not self.email:
            raise ValueError("Email is required")
        
        if not self._is_valid_email(self.email):
            raise ValueError("Invalid email format")
        
        if not self.username:
            raise ValueError("Username is required")
        
        if not self._is_valid_username(self.username):
            raise ValueError("Username must be 3-30 characters, alphanumeric and underscores only")
        
        if not self.full_name:
            raise ValueError("Full name is required")
        
        if len(self.full_name) < 2:
            raise ValueError("Full name must be at least 2 characters")
        
        """
        Optional field validation - only validate if the field has a value
        This allows users to have incomplete profiles while ensuring
        that provided information is properly formatted
        """
        if self.phone and not self._is_valid_phone(self.phone):
            raise ValueError("Invalid phone number format")
    
    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email address format using RFC-compliant regex pattern.
        
        This method validates email addresses against a practical regex pattern
        that balances RFC compliance with real-world usability. It's designed to
        accept most valid email addresses while rejecting obvious malformed ones.
        
        Pattern Breakdown:
            - ^[a-zA-Z0-9._%+-]+: Local part (before @) with common characters
            - @: Required @ symbol separator
            - [a-zA-Z0-9.-]+: Domain name with alphanumeric and common symbols
            - \.: Required dot separator before TLD
            - [a-zA-Z]{2,}$: Top-level domain (minimum 2 characters)
        
        Args:
            email (str): Email address to validate
            
        Returns:
            bool: True if email format is valid, False otherwise
            
        Design Considerations:
            - Practical validation vs strict RFC compliance
            - Accepts most common email formats used in practice
            - Rejects obviously malformed addresses
            - Fast regex-based validation for performance
            - Does not validate email deliverability (that's not this layer's job)
        
        Limitations:
            - Does not support all RFC 5322 edge cases
            - Does not validate domain existence or deliverability
            - May reject some technically valid but unusual email formats
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_username(self, username: str) -> bool:
        """
        Validate username format for platform consistency and security.
        
        Enforces username constraints that ensure usernames are:
        - URL-safe for use in web routes and APIs
        - Database-friendly for indexing and queries
        - Human-readable and memorable
        - Consistent across the platform
        
        Validation Rules:
            - Length: 3-30 characters (readable but not unwieldy)
            - Characters: Letters (a-z, A-Z), numbers (0-9), underscores (_)
            - Case: Case-sensitive (JohnDoe != johndoe)
            - No spaces or special characters (URL safety)
        
        Pattern Breakdown:
            - ^: Start of string anchor
            - [a-zA-Z0-9_]: Allowed character set
            - {3,30}: Length constraint (minimum 3, maximum 30)
            - $: End of string anchor
        
        Args:
            username (str): Username to validate
            
        Returns:
            bool: True if username format is valid, False otherwise
            
        Security Benefits:
            - Prevents injection attacks through usernames
            - Ensures usernames are suitable for URLs and file systems
            - Maintains consistent naming conventions
            - Avoids problematic characters that could cause parsing issues
        
        Business Rationale:
            - 3 char minimum prevents overly short, non-meaningful usernames
            - 30 char maximum keeps usernames manageable and display-friendly
            - Alphanumeric + underscore balances flexibility with safety
        """
        pattern = r'^[a-zA-Z0-9_]{3,30}$'
        return re.match(pattern, username) is not None
    
    def _is_valid_phone(self, phone: str) -> bool:
        """
        Validate phone number format for international compatibility.
        
        This method validates phone numbers using E.164 international format
        guidelines, which ensures compatibility with SMS services, calling
        systems, and international number portability.
        
        Validation Rules:
            - Optional leading + for international format
            - Must start with country code (1-9, no leading zeros)
            - Total length: 2-15 digits after country code
            - Only numeric digits allowed (no spaces, dashes, parentheses)
        
        Pattern Breakdown:
            - ^: Start of string
            - \+?: Optional plus sign for international format
            - [1-9]: Country code first digit (1-9, excludes 0)
            - \d{1,14}: Remaining digits (1-14 more for total max 15)
            - $: End of string
        
        Args:
            phone (str): Phone number to validate
            
        Returns:
            bool: True if phone format is valid, False otherwise
            
        Examples of Valid Numbers:
            - +1234567890 (US number with country code)
            - 1234567890 (US number without + prefix)
            - +441234567890 (UK number)
        
        Examples of Invalid Numbers:
            - 01234567890 (starts with 0)
            - +123456789012345678 (too long)
            - +1-234-567-8900 (contains formatting)
            - phone (non-numeric)
        
        Integration Notes:
            - Compatible with SMS notification services
            - Suitable for international calling systems
            - Can be used directly with telecommunications APIs
            - Standardized format for database storage
        """
        pattern = r'^\+?[1-9]\d{1,14}$'
        return re.match(pattern, phone) is not None
    
    def update_profile(self, **kwargs) -> None:
        """
        Update user profile information with validation and audit trail.
        
        This method provides a controlled way to update user profile information
        while maintaining data integrity and security. It only allows updates to
        specific whitelisted fields and ensures validation is performed.
        
        Allowed Profile Fields:
            - full_name: User's display name
            - first_name: Given name
            - last_name: Family name
            - organization: Company or institution affiliation
            - phone: Contact phone number
            - timezone: User's timezone for scheduling
            - language: Preferred interface language
            - bio: User biography or description
            - profile_picture_url: Avatar image URL
        
        Security Features:
            - Whitelist approach: Only specified fields can be updated
            - Validation enforcement: All changes are validated
            - Audit trail: updated_at timestamp is automatically set
            - Type safety: Uses hasattr to verify field existence
        
        Args:
            **kwargs: Field-value pairs to update. Only whitelisted fields
                     will be processed; others are silently ignored.
        
        Returns:
            None: Method modifies the object in place
        
        Raises:
            ValueError: If updated values fail validation rules
        
        Usage Examples:
            user.update_profile(
                full_name="John Smith",
                timezone="America/New_York",
                bio="Software Engineer"
            )
        
        Design Rationale:
            - Whitelist prevents accidental updates to sensitive fields
            - Validation ensures data integrity is maintained
            - Flexible kwargs interface supports partial updates
            - Audit trail supports compliance and debugging
        """
        """
        Define allowed fields for profile updates. This whitelist approach
        prevents accidental or malicious updates to sensitive fields like
        ID, role, status, created_at, etc.
        """
        allowed_fields = {
            'full_name', 'first_name', 'last_name', 'organization', 
            'phone', 'timezone', 'language', 'bio', 'profile_picture_url'
        }
        
        """
        Apply updates only to whitelisted fields that actually exist on the object.
        This prevents both security issues and attribute errors.
        """
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(self, field):
                setattr(self, field, value)
        
        """
        Update timestamp and validate to ensure object remains in valid state.
        The validation catches any constraint violations introduced by updates.
        """
        self.updated_at = datetime.utcnow()
        self.validate()
    
    def change_role(self, new_role: UserRole) -> None:
        """
        Change user role with validation and audit trail.
        
        This method handles role changes for users, which is a critical operation
        that affects authorization and access control throughout the platform.
        Role changes should be rare and carefully controlled.
        
        Business Rules:
            - Only valid UserRole enum values are accepted
            - Role changes are immediately effective
            - Timestamp is updated for audit purposes
            - No authorization check (handled by calling service)
        
        Security Implications:
            - Role changes affect permissions across all platform services
            - Should be logged by calling services for security auditing
            - Immediate effect means user gains/loses access instantly
            - Role transitions should follow principle of least privilege
        
        Args:
            new_role (UserRole): The new role to assign to the user.
                                Must be a valid UserRole enum value.
        
        Returns:
            None: Method modifies the object in place
        
        Raises:
            ValueError: If new_role is not a valid UserRole enum value
        
        Usage Examples:
            # Promote student to instructor
            user.change_role(UserRole.INSTRUCTOR)
            
            # Grant admin privileges
            user.change_role(UserRole.ADMIN)
        
        Integration Notes:
            - Calling services should log role changes for auditing
            - May trigger cache invalidation in authorization services
            - Should be accompanied by notifications to affected users
            - Consider permission migration for role transitions
        """
        if not isinstance(new_role, UserRole):
            raise ValueError("Invalid role type")
        
        self.role = new_role
        self.updated_at = datetime.utcnow()
    
    def change_status(self, new_status: UserStatus) -> None:
        """
        Change user account status with validation and audit trail.
        
        This method manages the user account lifecycle by transitioning between
        different status states. Status changes have immediate effects on user
        access and should be handled carefully.
        
        Business Impact:
            - ACTIVE: User gains full platform access
            - INACTIVE: User loses all platform access
            - SUSPENDED: User is locked out, requires admin intervention
            - PENDING: User awaits activation or verification
        
        Status Transition Rules:
            - Any status can transition to any other status
            - No business logic validation at entity level
            - Calling services should implement transition rules
            - Audit trail maintained through updated_at
        
        Security Considerations:
            - Status changes affect authentication and authorization
            - SUSPENDED status should be used for security incidents
            - INACTIVE allows voluntary account deactivation
            - Immediate effect means access is granted/revoked instantly
        
        Args:
            new_status (UserStatus): The new status to assign to the user.
                                   Must be a valid UserStatus enum value.
        
        Returns:
            None: Method modifies the object in place
        
        Raises:
            ValueError: If new_status is not a valid UserStatus enum value
        
        Usage Examples:
            # Activate pending user
            user.change_status(UserStatus.ACTIVE)
            
            # Suspend user for policy violation
            user.change_status(UserStatus.SUSPENDED)
            
            # Deactivate account voluntarily
            user.change_status(UserStatus.INACTIVE)
        
        Integration Notes:
            - Authentication services should check status before login
            - Status changes should trigger appropriate notifications
            - Consider session invalidation for restrictive status changes
            - Audit logs should capture who made status changes
        """
        if not isinstance(new_status, UserStatus):
            raise ValueError("Invalid status type")
        
        self.status = new_status
        self.updated_at = datetime.utcnow()
    
    def record_login(self) -> None:
        """
        Record user login timestamp for activity tracking and analytics.
        
        This method updates the user's last login timestamp whenever they
        successfully authenticate. This information is used for:
        - User activity analytics and reporting
        - Inactive user identification for cleanup
        - Security monitoring for unusual login patterns
        - User engagement metrics and insights
        
        Timing Considerations:
            - Should be called after successful authentication
            - Uses UTC timezone for consistency across deployments
            - Updates both last_login and updated_at timestamps
            - Provides data for inactivity-based operations
        
        Privacy Notes:
            - Login tracking is standard security practice
            - Timestamp data helps identify compromised accounts
            - Supports compliance with activity monitoring requirements
            - Used for legitimate business analytics
        
        Returns:
            None: Method modifies the object in place
        
        Usage Examples:
            # Called by authentication service after login
            user.record_login()
            
            # Check how recently user was active
            if user.last_login and user.last_login > cutoff_date:
                # User is recently active
        
        Performance Notes:
            - Lightweight operation suitable for every login
            - UTC timestamps avoid timezone conversion overhead
            - Database updates should be batched if possible
            - Consider async updates for high-frequency logins
        """
        self.last_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def is_active(self) -> bool:
        """
        Check if user account is in active status.
        
        This is a fundamental authorization check used throughout the platform
        to determine if a user should have access to platform features.
        
        Business Logic:
            - Only users with ACTIVE status are considered active
            - All other statuses (INACTIVE, SUSPENDED, PENDING) are not active
            - Used as primary gate for platform access control
        
        Returns:
            bool: True if user status is ACTIVE, False otherwise
        
        Usage Examples:
            if user.is_active():
                # Allow platform access
            else:
                # Deny access, redirect to activation
        
        Integration Points:
            - Authentication middleware checks this before granting access
            - Authorization decorators use this for endpoint protection
            - Feature flags may depend on active status
            - Analytics services track active vs inactive users
        """
        return self.status == UserStatus.ACTIVE
    
    def is_instructor(self) -> bool:
        """
        Check if user has instructor-level privileges.
        
        This method determines if a user has permissions to perform instructor
        functions such as creating courses, managing students, and accessing
        instructor-specific features.
        
        Role Hierarchy Logic:
            - INSTRUCTOR role: Has instructor privileges
            - ORGANIZATION_ADMIN role: Has instructor privileges (plus org admin privileges)
            - ADMIN role: Has instructor privileges (plus system admin privileges)
            - STUDENT role: Does not have instructor privileges
        
        Business Rationale:
            - Admins and Organization Admins can perform all instructor functions
            - Instructors focus on content creation and delivery
            - Clear separation between content consumers and creators
        
        Returns:
            bool: True if user has instructor-level access, False otherwise
        
        Usage Examples:
            if user.is_instructor():
                # Show course creation tools
                # Allow student management
                # Enable grading features
        
        Integration Notes:
            - Course management service uses this for access control
            - UI components conditionally render based on this check
            - API endpoints protect instructor features with this validation
        """
        return self.role in [UserRole.INSTRUCTOR, UserRole.ORGANIZATION_ADMIN, UserRole.ADMIN]
    
    def is_admin(self) -> bool:
        """
        Check if user has administrative privileges.
        
        This method determines if a user has the highest level of platform
        access, including system administration, user management, and
        platform configuration capabilities.
        
        Administrative Capabilities:
            - User management (create, update, delete users)
            - System configuration and settings
            - Platform-wide analytics and reporting
            - Service administration and monitoring
            - Security and compliance management
        
        Security Implications:
            - Admins have elevated privileges across all platform services
            - Admin actions should be logged for audit purposes
            - Admin access should be restricted to necessary personnel only
            - Regular review of admin privileges is recommended
        
        Returns:
            bool: True if user has admin role, False otherwise
        
        Usage Examples:
            if user.is_admin():
                # Show admin dashboard
                # Allow user management
                # Enable system configuration
        
        Authorization Pattern:
            - Most restrictive check - only true admins pass
            - Used for platform-wide administrative functions
            - Should be combined with active status check for security
        """
        return self.role == UserRole.ADMIN
    
    def can_create_courses(self) -> bool:
        """
        Check if user can create and manage courses.
        
        This method combines role and status checks to determine if a user
        should have access to course creation and management features.
        
        Requirements:
            1. Must have instructor-level role (INSTRUCTOR or ADMIN)
            2. Must have active account status
        
        Business Logic:
            - Only active instructors can create courses
            - Inactive/suspended instructors lose course creation privileges
            - Students cannot create courses regardless of status
            - Combines authorization (role) with access control (status)
        
        Returns:
            bool: True if user can create courses, False otherwise
        
        Usage Examples:
            if user.can_create_courses():
                # Show course creation interface
                # Allow access to course management tools
                # Enable curriculum development features
        
        Security Benefits:
            - Prevents inactive accounts from creating content
            - Ensures only authorized roles have content creation access
            - Provides single point of control for course creation permissions
        """
        return self.is_instructor() and self.is_active()
    
    def can_manage_users(self) -> bool:
        """
        Check if user can manage other user accounts.
        
        This method determines if a user has permission to perform user
        management operations such as creating, updating, or deleting
        other user accounts.
        
        Requirements:
            1. Must have admin role (highest privilege level)
            2. Must have active account status
        
        User Management Capabilities:
            - Create new user accounts
            - Update user profiles and settings
            - Change user roles and permissions
            - Suspend or deactivate user accounts
            - View user analytics and reports
            - Manage user access and authentication
        
        Security Considerations:
            - Most privileged operation in the system
            - Should be logged and audited extensively
            - Requires active status to prevent compromised accounts
            - Limited to admin role only for security
        
        Returns:
            bool: True if user can manage other users, False otherwise
        
        Usage Examples:
            if user.can_manage_users():
                # Show user administration panel
                # Allow user creation/modification
                # Enable user analytics dashboard
        
        Authorization Pattern:
            - Highest security requirement in the system
            - Used for platform administration interfaces
            - Should trigger additional security logging
        """
        return self.is_admin() and self.is_active()
    
    def get_display_name(self) -> str:
        """
        Get the best available display name for the user.
        
        This method provides a consistent way to get a human-readable
        display name for users across the platform interface.
        
        Display Name Priority:
            1. full_name: Preferred display name if available
            2. username: Fallback if full_name is not set
        
        Business Logic:
            - Always returns a non-empty string
            - Prefers human-readable full name over technical username
            - Provides consistent display across all UI components
        
        Returns:
            str: Display name for the user, never empty
        
        Usage Examples:
            # In templates or UI components
            welcome_message = f"Welcome, {user.get_display_name()}!"
            
            # In notifications
            notification_text = f"{user.get_display_name()} has joined the course"
        
        Design Rationale:
            - Users may not always have full names set during registration
            - Username is always required so it's a reliable fallback
            - Consistent display improves user experience
            - Centralized logic prevents inconsistent display patterns
        """
        return self.full_name or self.username
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add custom metadata to the user for extensibility.
        
        The metadata system provides a flexible way to store additional
        user attributes without modifying the core schema. This supports
        platform evolution and customization.
        
        Use Cases:
            - Custom user attributes for specific deployments
            - Integration data from external systems
            - Feature flags and user preferences
            - Analytics tracking parameters
            - Temporary data for workflows
        
        Args:
            key (str): Metadata key identifier. Should be descriptive
                      and follow naming conventions.
            value (Any): Metadata value. Should be JSON-serializable
                        for database storage.
        
        Returns:
            None: Method modifies the object in place
        
        Usage Examples:
            # Store integration ID
            user.add_metadata('external_id', 'xyz123')
            
            # Track user preferences
            user.add_metadata('theme_preference', 'dark')
            
            # Store workflow state
            user.add_metadata('onboarding_step', 3)
        
        Implementation Notes:
            - Overwrites existing values for the same key
            - Updates timestamp for audit trail
            - No validation on metadata content (caller responsibility)
            - Should be JSON-serializable for database persistence
        """
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
    
    def remove_metadata(self, key: str) -> None:
        """
        Remove custom metadata from the user.
        
        This method provides a safe way to remove metadata entries
        while maintaining audit trail through timestamp updates.
        
        Behavior:
            - Removes the specified key if it exists
            - Silently ignores removal of non-existent keys
            - Updates timestamp when actual removal occurs
            - Maintains metadata dictionary integrity
        
        Args:
            key (str): Metadata key to remove
        
        Returns:
            None: Method modifies the object in place
        
        Usage Examples:
            # Clean up temporary workflow data
            user.remove_metadata('onboarding_step')
            
            # Remove deprecated attributes
            user.remove_metadata('old_preference')
        
        Design Considerations:
            - Safe operation - doesn't fail on missing keys
            - Only updates timestamp when actual change occurs
            - Preserves other metadata entries
            - Supports cleanup and privacy compliance operations
        """
        if key in self.metadata:
            del self.metadata[key]
            self.updated_at = datetime.utcnow()
    
    def get(self, key: str, default=None):
        """
        Dictionary-style access to user attributes for backward compatibility.
        
        This method allows the User object to be used like a dictionary,
        maintaining compatibility with existing code that expects dictionary access.
        
        Args:
            key: Attribute name to retrieve
            default: Default value if attribute doesn't exist
            
        Returns:
            Attribute value or default
        """
        # Special handling for hashed_password which is stored in metadata
        if key == 'hashed_password':
            return self.metadata.get('hashed_password', default)
            
        if hasattr(self, key):
            value = getattr(self, key)
            # Convert enum values to strings for compatibility
            if hasattr(value, 'value'):
                return value.value
            return value
        return default
    
    def __getitem__(self, key: str):
        """
        Dictionary-style bracket access for backward compatibility.
        
        Args:
            key: Attribute name to retrieve
            
        Returns:
            Attribute value
            
        Raises:
            KeyError: If attribute doesn't exist
        """
        # Special handling for hashed_password which is stored in metadata
        if key == 'hashed_password':
            if 'hashed_password' in self.metadata:
                return self.metadata['hashed_password']
            raise KeyError(key)
            
        if hasattr(self, key):
            value = getattr(self, key)
            # Convert enum values to strings for compatibility
            if hasattr(value, 'value'):
                return value.value
            return value
        raise KeyError(key)
    
    def __setitem__(self, key: str, value):
        """
        Dictionary-style bracket assignment for backward compatibility.
        
        Args:
            key: Attribute name to set
            value: Value to set
        """
        setattr(self, key, value)
    
    def __contains__(self, key: str) -> bool:
        """
        Dictionary-style 'in' operator support.
        
        Args:
            key: Attribute name to check
            
        Returns:
            True if attribute exists, False otherwise
        """
        return hasattr(self, key)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert user entity to dictionary for serialization and API responses.
        
        This method provides a standardized way to serialize user entities
        for JSON APIs, database storage, logging, and inter-service communication.
        
        Serialization Features:
            - Converts enum values to string representations
            - Handles datetime objects with ISO format
            - Preserves None values for optional fields
            - Includes all user attributes for complete representation
            - JSON-compatible output for API responses
        
        Datetime Handling:
            - ISO 8601 format for timestamps (YYYY-MM-DDTHH:MM:SS.microseconds)
            - UTC timezone for consistency
            - Null handling for optional last_login
        
        Returns:
            Dict[str, Any]: Dictionary representation of the user with
                           all fields converted to JSON-compatible types
        
        Usage Examples:
            # For API responses
            return JsonResponse(user.to_dict())
            
            # For logging
            logger.info("User updated", extra=user.to_dict())
            
            # For inter-service communication
            payload = {'user': user.to_dict()}
        
        Security Considerations:
            - Does not include password (which isn't stored in this entity)
            - Includes all profile information (caller should filter sensitive data)
            - Metadata may contain sensitive information (review before exposure)
            - Consider field filtering for different API contexts
        
        Performance Notes:
            - Creates new dictionary on each call
            - Datetime conversion has minimal overhead
            - Suitable for occasional serialization, not high-frequency calls
        """
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role.value,
            'status': self.status.value,
            'organization': self.organization,
            'phone': self.phone,
            'timezone': self.timezone,
            'language': self.language,
            'profile_picture_url': self.profile_picture_url,
            'bio': self.bio,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }