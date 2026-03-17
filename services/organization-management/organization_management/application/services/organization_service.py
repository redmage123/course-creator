"""
Organization Service - Business Logic Orchestration
Single Responsibility: Organization business operations
Open/Closed: Extensible through dependency injection
Dependency Inversion: Depends on repository abstractions

Enhanced to automatically create organization administrators during org registration
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
import httpx
import os
import sys

# Add shared module to path for SSL config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'shared'))
from security.ssl_config import create_secure_client_kwargs

from organization_management.domain.entities.organization import Organization
from organization_management.data_access.organization_dao import OrganizationManagementDAO
from organization_management.exceptions import (
    OrganizationNotFoundException,
    OrganizationValidationException,
    OrganizationException,
    DatabaseException
)


class OrganizationService:
    """
    Service class for organization business operations with integrated user management.

    BUSINESS PURPOSE:
    Manages complete organization lifecycle including registration, configuration, and administration.
    Orchestrates organization creation with automatic administrator user provisioning for seamless onboarding.

    CORE RESPONSIBILITIES:
    - Organization CRUD operations (create, read, update, delete)
    - Automatic organization administrator user creation during registration
    - Organization validation and uniqueness enforcement (slug, domain)
    - Multi-tenant organization isolation and security
    - Organization search, filtering, and statistics
    - Inter-service communication with user-management for admin user creation

    MULTI-TENANT ARCHITECTURE:
    This service implements organization-level multi-tenancy:
    - Each organization has unique slug and domain for identification
    - Organizations are completely isolated from each other
    - Organization admins can only access their own organization
    - Site admin has cross-organization access for platform management

    INTEGRATION POINTS:
    - user-management service: Creates organization admin users via REST API
    - Database: Stores organization entities and metadata
    - Authentication: Validates organization access permissions

    DESIGN PATTERNS:
    - Single Responsibility: Handles organization business logic only
    - Dependency Inversion: Depends on DAO abstraction, not concrete implementation
    - Service Layer: Orchestrates between domain entities and infrastructure

    Args:
        dao: Data access object for organization persistence operations
    """

    def __init__(self, dao: OrganizationManagementDAO):
        """
        Initialize organization service with data access object.

        Args:
            dao: OrganizationManagementDAO for database operations
        """
        self._dao = dao
        self._logger = logging.getLogger(__name__)

        # HTTP client configuration for user management service with environment-aware SSL
        self._user_management_url = os.getenv('USER_MANAGEMENT_URL') or os.getenv('USER_SERVICE_URL', 'http://user-management:8000')
        # Use shared SSL config for secure inter-service communication
        self._http_client = httpx.AsyncClient(**create_secure_client_kwargs())

    async def _create_organization_admin_user(self, admin_full_name: str, admin_email: str, 
                                              admin_phone: str = None, admin_roles: List[str] = None,
                                              organization_slug: str = None, admin_password: str = None,
                                              admin_username: str = None) -> Dict[str, Any]:
        """
        Create organization administrator user in user management service
        
        PURPOSE: Automatically create the organization admin user when registering organization
        WHY: Organizations need an administrative user to manage the organization
        BUSINESS REQUIREMENT: Every organization must have at least one administrator
        
        Args:
            admin_full_name: Full name of the administrator
            admin_email: Email address for the administrator
            admin_phone: Phone number (optional)
            admin_roles: List of roles to assign to the admin
            organization_slug: Organization identifier for linking
            admin_password: Password set by admin during registration
            admin_username: Username/ID provided during registration (optional)
            
        Returns:
            Dict containing the created user information
            
        Raises:
            Exception: If user creation fails
        """
        try:
            # Debug admin_username parameter
            print(f"=== DEBUG admin_username: '{admin_username}' (type: {type(admin_username)}, is None: {admin_username is None})")
            self._logger.info(f"DEBUG admin_username: '{admin_username}' (type: {type(admin_username)}, is None: {admin_username is None})")
            
            # Use provided username or generate from email as fallback
            if admin_username and admin_username.strip():
                # Use provided admin username/ID
                username = admin_username.lower().strip()
                self._logger.info(f"Using provided admin username: '{username}'")
                # Validate username format (letters, numbers, underscore, hyphen only)
                if not username or not all(c.isalnum() or c in '_-' for c in username):
                    raise ValueError("Invalid username format. Only letters, numbers, underscores, and hyphens are allowed.")
                if len(username) < 3 or len(username) > 30:
                    raise ValueError("Username must be between 3 and 30 characters.")
            else:
                self._logger.info(f"No admin username provided (value: '{admin_username}'), generating from email: '{admin_email}'")
                # Fallback: Generate valid username from email by sanitizing special characters
                # Extract local part of email and replace invalid characters with underscores
                email_local = admin_email.split('@')[0].lower()
                # Replace dots, hyphens, and other invalid characters with underscores
                username = ''.join(c if c.isalnum() else '_' for c in email_local)
                # Ensure no consecutive underscores and trim to valid length
                username = '_'.join(filter(None, username.split('_')))[:24]  # Leave room for suffix
                # Ensure minimum length of 3 characters
                if len(username) < 3:
                    username = username + '_user'
                
                # Add timestamp suffix to ensure global uniqueness
                import time
                timestamp_suffix = str(int(time.time()))[-4:]  # Last 4 digits of timestamp
                # Combine with org prefix for readability and uniqueness (sanitize org slug)
                org_prefix = organization_slug[:6] if len(organization_slug) >= 3 else organization_slug
                org_prefix = ''.join(c if c.isalnum() else '_' for c in org_prefix)  # Sanitize org prefix
                username = f"{username}_{org_prefix}_{timestamp_suffix}"[:30]
                # Final cleanup to ensure only valid characters
                username = ''.join(c if (c.isalnum() or c == '_') else '_' for c in username)
                
                self._logger.info(f"Generated unique username: '{username}' from email: '{admin_email}' and org: '{organization_slug}'")
            
            # Use provided credential or generate temporary one
            if admin_password:
                password_to_use = admin_password
                is_temp_password = False
                self._logger.info(f"Using admin-provided credential for user: {admin_email}")
            else:
                # Generate a temporary credential (should be reset by admin on first login)
                import secrets
                import string
                password_to_use = ''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(12))
                is_temp_password = True
                self._logger.info(f"Generated temporary credential for user: {admin_email}")
            
            # Default role is organization admin (using organization_admin to match user-management validation)
            primary_role = "organization_admin" if "organization_admin" in (admin_roles or []) else "organization_admin"
            
            # Prepare user registration request
            user_registration_data = {
                "email": admin_email,
                "username": username,
                "full_name": admin_full_name,
                "password": password_to_use,
                "role": primary_role,
                "organization": organization_slug,
                "phone": admin_phone,
                "language": "en"
            }
            
            # Make HTTP request to user management service
            response = await self._http_client.post(
                f"{self._user_management_url}/auth/register",
                json=user_registration_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self._logger.info(f"Organization admin user created successfully: {admin_email}")
                
                # Return user info including password status for organization setup
                return {
                    "user_id": user_data.get("id"),
                    "username": user_data.get("username"),
                    "email": user_data.get("email"),
                    "full_name": user_data.get("full_name"),
                    "role": user_data.get("role"),
                    "password_status": "temporary" if is_temp_password else "user_provided",
                    "temp_password": password_to_use if is_temp_password else None,  # Only include temp password if generated
                    "organization": organization_slug
                }
            else:
                error_detail = response.text
                self._logger.error(f"Failed to create organization admin user: {response.status_code} - {error_detail}")
                raise Exception(f"User creation failed: {error_detail}")
                
        except httpx.RequestError as e:
            self._logger.error(f"HTTP request failed when creating admin user: {str(e)}")
            raise Exception(f"Failed to communicate with user management service: {str(e)}")
        except Exception as e:
            self._logger.error(f"Error creating organization admin user: {str(e)}")
            raise

    async def create_organization(self, name: str, slug: str,
                                  contact_phone: str, contact_email: str, description: str = None,
                                  logo_url: str = None, domain: str = None,
                                  # Subdivided address fields
                                  street_address: str = None, city: str = None,
                                  state_province: str = None, postal_code: str = None,
                                  country: str = 'US',
                                  # Legacy address field (optional for backwards compatibility)
                                  address: str = None,
                                  settings: Dict[str, Any] = None,
                                  # Organization admin parameters
                                  admin_full_name: str = None, admin_email: str = None,
                                  admin_phone: str = None, admin_roles: List[str] = None,
                                  admin_password: str = None, admin_username: str = None) -> Dict[str, Any]:
        """
        Create a new organization with automatic administrator user creation
        
        PURPOSE: Complete organization registration including admin user setup
        WHY: Organizations need both entity and administrative user for full functionality
        BUSINESS REQUIREMENT: Every organization must have an administrator
        
        Returns:
            Dict containing organization and admin user information
        """
        try:
            print(f"=== SERVICE DEBUG: Starting create_organization")
            print(f"=== SERVICE PARAMS: name='{name}', slug='{slug}', admin_email='{admin_email}'")
            self._logger.info(f"SERVICE DEBUG: Starting create_organization with name='{name}', slug='{slug}'")
            
            # Validate admin information is provided
            print(f"=== SERVICE DEBUG: Validating admin information")
            if not admin_full_name or not admin_email:
                print(f"=== SERVICE ERROR: Missing admin info - admin_full_name: {admin_full_name}, admin_email: {admin_email}")
                raise ValueError("Organization administrator information (full name and email) is required")
            
            # Check if slug already exists
            print(f"=== SERVICE DEBUG: Checking if slug exists: {slug}")
            slug_exists = await self._dao.exists_by_slug(slug)
            print(f"=== SERVICE DEBUG: Slug exists result: {slug_exists}")
            if slug_exists:
                print(f"=== SERVICE ERROR: Slug already exists: {slug}")
                raise ValueError(f"Organization with slug '{slug}' already exists")

            # Check if domain already exists (if provided)
            if domain:
                print(f"=== SERVICE DEBUG: Checking if domain exists: {domain}")
                domain_exists = await self._dao.exists_by_domain(domain)
                print(f"=== SERVICE DEBUG: Domain exists result: {domain_exists}")
                if domain_exists:
                    print(f"=== SERVICE ERROR: Domain already exists: {domain}")
                    raise ValueError(f"Organization with domain '{domain}' already exists")

            # Step 1: Create organization administrator user first
            print(f"=== SERVICE DEBUG: About to create organization administrator")
            self._logger.info(f"Creating organization administrator: {admin_email}")
            admin_user_info = await self._create_organization_admin_user(
                admin_full_name=admin_full_name,
                admin_email=admin_email,
                admin_phone=admin_phone,
                admin_roles=admin_roles,
                organization_slug=slug,
                admin_password=admin_password,
                admin_username=admin_username
            )
            
            print(f"=== SERVICE DEBUG: Admin user creation completed successfully")
            self._logger.info(f"SERVICE DEBUG: Admin user creation completed successfully")

            # Step 2: Create organization entity
            print(f"=== SERVICE DEBUG: About to create organization entity")
            print(f"=== CREATING ORGANIZATION ENTITY with name='{name}', slug='{slug}', domain='{domain}'")
            self._logger.info(f"CREATING ORGANIZATION ENTITY with name='{name}', slug='{slug}', domain='{domain}'")
            try:
                organization = Organization(
                    name=name,
                    slug=slug,
                    contact_phone=contact_phone,
                    contact_email=contact_email,
                    street_address=street_address,
                    city=city,
                    state_province=state_province,
                    postal_code=postal_code,
                    country=country,
                    address=address,  # Legacy field
                    description=description,
                    logo_url=logo_url,
                    domain=domain,
                    settings=settings or {}
                )
                print(f"=== ORGANIZATION ENTITY CREATED SUCCESSFULLY")
                self._logger.info("ORGANIZATION ENTITY CREATED SUCCESSFULLY")
            except Exception as org_creation_error:
                print(f"=== ERROR CREATING ORGANIZATION ENTITY: {org_creation_error}")
                self._logger.error(f"ERROR CREATING ORGANIZATION ENTITY: {org_creation_error}")
                raise

            # Validate organization with detailed debugging
            try:
                print(f"=== VALIDATION DEBUG: Starting validation for organization: {organization.name}")
                self._logger.info(f"VALIDATION DEBUG: Starting validation for organization: {organization.name}")
                
                required_fields = organization.validate_required_fields()
                print(f"=== VALIDATION DEBUG: Required fields valid: {required_fields}")
                self._logger.info(f"VALIDATION DEBUG: Required fields valid: {required_fields}")
                
                slug_valid = organization.validate_slug()
                print(f"=== VALIDATION DEBUG: Slug valid: {slug_valid}")
                self._logger.info(f"VALIDATION DEBUG: Slug valid: {slug_valid}")
                
                domain_valid = organization.validate_domain()
                print(f"=== VALIDATION DEBUG: Domain valid: {domain_valid}")
                self._logger.info(f"VALIDATION DEBUG: Domain valid: {domain_valid}")
                
                email_valid = organization.validate_contact_email()
                print(f"=== VALIDATION DEBUG: Email valid: {email_valid}")
                self._logger.info(f"VALIDATION DEBUG: Email valid: {email_valid}")
                
                is_valid = organization.is_valid()
                print(f"=== VALIDATION DEBUG: Overall valid: {is_valid}")
                self._logger.info(f"VALIDATION DEBUG: Overall valid: {is_valid}")
                
                if not is_valid:
                    # Create detailed error message with validation results
                    failed_validations = []
                    if not required_fields:
                        failed_validations.append("required_fields")
                    if not slug_valid:
                        failed_validations.append("slug")
                    if not domain_valid:
                        failed_validations.append("domain")
                    if not email_valid:
                        failed_validations.append("email")
                    
                    error_details = f"Failed validations: {', '.join(failed_validations)}"
                    # Force detailed error message to appear
                    print(f"=== RAISING DETAILED ERROR: Invalid organization data - {error_details}")
                    self._logger.error(f"RAISING DETAILED ERROR: Invalid organization data - {error_details}")
                    raise ValueError(f"Invalid organization data - {error_details}")
            except Exception as e:
                # Debug which validation is failing with exception details
                try:
                    required_fields = organization.validate_required_fields()
                    slug_valid = organization.validate_slug()
                    domain_valid = organization.validate_domain()
                    email_valid = organization.validate_contact_email()
                    
                    print(f"=== EXCEPTION VALIDATION DEBUG - Required: {required_fields}, Slug: {slug_valid}, Domain: {domain_valid}, Email: {email_valid}")
                    print(f"=== EXCEPTION ORG DATA - Name: '{organization.name}', Slug: '{organization.slug}', Address len: {len(organization.address) if organization.address else 0}, Email: '{organization.contact_email}', Domain: '{organization.domain}'")
                except Exception as validation_error:
                    print(f"=== ERROR DURING VALIDATION DEBUG: {validation_error}")
                
                self._logger.error(f"EXCEPTION during validation: {type(e).__name__}: {e}")
                import traceback
                self._logger.error(f"TRACEBACK: {traceback.format_exc()}")
                raise ValueError("Invalid organization data")

            # Persist organization
            print(f"=== SERVICE DEBUG: About to persist organization to database")
            print(f"=== SERVICE DEBUG: Preparing organization data dictionary")
            org_data = {
                'id': organization.id,
                'name': organization.name,
                'slug': organization.slug,
                'description': organization.description,
                'domain': organization.domain,
                'address': organization.address,
                'street_address': organization.street_address,
                'city': organization.city,
                'state_province': organization.state_province,
                'postal_code': organization.postal_code,
                'country': organization.country,
                'contact_email': organization.contact_email,
                'contact_phone': organization.contact_phone,
                'logo_url': organization.logo_url,
                'settings': organization.settings,
                'is_active': organization.is_active
            }
            print(f"=== SERVICE DEBUG: Organization data prepared, calling DAO.create_organization")
            self._logger.info(f"SERVICE DEBUG: About to call DAO.create_organization")
            org_id = await self._dao.create_organization(org_data)
            print(f"=== SERVICE DEBUG: DAO.create_organization completed, returned ID: {org_id}")
            self._logger.info(f"SERVICE DEBUG: DAO.create_organization completed, returned ID: {org_id}")
            # Get the created organization back
            created_organization = organization  # We already have the entity

            # Step 3: Update admin user with organization_id (now that organization exists)
            print(f"=== SERVICE DEBUG: Updating admin user with organization_id: {created_organization.id}")
            self._logger.info(f"Updating admin user {admin_user_info['user_id']} with organization_id: {created_organization.id}")
            try:
                update_response = await self._http_client.patch(
                    f"{self._user_management_url}/users/{admin_user_info['user_id']}",
                    json={"organization_id": str(created_organization.id)},
                    headers={"Content-Type": "application/json"}
                )

                if update_response.status_code == 200:
                    print(f"=== SERVICE DEBUG: Admin user updated successfully with organization_id")
                    self._logger.info(f"Admin user updated successfully with organization_id")
                else:
                    print(f"=== SERVICE WARNING: Failed to update user organization_id: {update_response.status_code}")
                    self._logger.warning(f"Failed to update user organization_id: {update_response.status_code} - {update_response.text}")
            except Exception as update_error:
                print(f"=== SERVICE WARNING: Exception updating user organization_id: {update_error}")
                self._logger.warning(f"Non-critical error updating user organization_id: {update_error}")
                # Don't fail the entire registration if user update fails - organization is already created

            # Step 4: Create organization membership for admin user
            print(f"=== SERVICE DEBUG: Creating organization membership for admin user")
            self._logger.info(f"Creating organization membership for admin user {admin_user_info['user_id']}")
            try:
                import uuid
                from datetime import datetime, timezone

                membership_data = {
                    'id': str(uuid.uuid4()),
                    'user_id': admin_user_info['user_id'],
                    'organization_id': str(created_organization.id),
                    'role': 'organization_admin',
                    'is_active': True,
                    'joined_at': datetime.now(timezone.utc),
                    'updated_at': datetime.now(timezone.utc)
                }

                membership_id = await self._dao.create_membership(membership_data)
                print(f"=== SERVICE DEBUG: Organization membership created successfully: {membership_id}")
                self._logger.info(f"Organization membership created successfully: {membership_id}")
            except Exception as membership_error:
                print(f"=== SERVICE ERROR: Failed to create organization membership: {membership_error}")
                self._logger.error(f"Failed to create organization membership: {membership_error}")
                # This is critical - membership is required for permission checks
                raise ValueError(f"Failed to create organization membership: {membership_error}")

            print(f"=== SERVICE DEBUG: About to build return data")
            self._logger.info(f"Organization created successfully: {created_organization.slug}")
            
            # Return comprehensive information including admin user details
            print(f"=== SERVICE DEBUG: Building final return dictionary")
            return {
                "organization": {
                    "id": str(created_organization.id),
                    "name": created_organization.name,
                    "slug": created_organization.slug,
                    "description": created_organization.description,
                    "address": created_organization.address,
                    "contact_phone": created_organization.contact_phone,
                    "contact_email": created_organization.contact_email,
                    "logo_url": created_organization.logo_url,
                    "domain": created_organization.domain,
                    "is_active": created_organization.is_active,
                    "created_at": created_organization.created_at.isoformat() if created_organization.created_at else None,
                    "updated_at": created_organization.updated_at.isoformat() if created_organization.updated_at else None
                },
                "admin_user": admin_user_info,
                "success": True,
                "message": f"Organization '{name}' and administrator account created successfully"
            }

        except Exception as e:
            print(f"=== SERVICE ERROR: Exception in create_organization: {type(e).__name__}: {str(e)}")
            self._logger.error(f"Error creating organization: {str(e)}")
            import traceback
            print(f"=== SERVICE ERROR TRACEBACK: {traceback.format_exc()}")
            self._logger.error(f"SERVICE ERROR TRACEBACK: {traceback.format_exc()}")
            # Re-raise with original message to preserve details
            if isinstance(e, ValueError):
                raise e
            else:
                raise
    
    async def __aenter__(self):
        """
        Async context manager entry for resource management.

        WHAT: Enables 'async with' syntax for service lifecycle management
        WHY: Ensures proper cleanup of HTTP client and database connections

        Returns:
            Self for context manager use
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit for cleanup of HTTP client resources.

        WHAT: Closes HTTP client connection to user-management service
        WHY: Prevents resource leaks and ensures graceful shutdown

        Args:
            exc_type: Exception type if exception occurred
            exc_val: Exception value if exception occurred
            exc_tb: Exception traceback if exception occurred
        """
        if hasattr(self, '_http_client'):
            await self._http_client.aclose()

    async def get_all_organizations(self) -> list[Organization]:
        """
        Retrieve all organizations from the system.

        WHAT: Fetches complete list of all organizations regardless of status
        WHY: Site admin needs to view and manage all organizations on the platform

        BUSINESS CONTEXT:
        This operation is typically restricted to site administrators for platform-wide
        visibility. Organization admins should only see their own organization.

        SECURITY NOTE:
        Should be protected by site admin authorization in the API layer.

        Returns:
            List of Organization entities with complete metadata

        Raises:
            Exception: If database query fails
        """
        try:
            org_dicts = await self._dao.get_all_organizations()
            organizations = []
            for org_dict in org_dicts:
                org = Organization(
                    name=org_dict['name'],
                    slug=org_dict['slug'],
                    contact_phone=org_dict.get('contact_phone'),
                    contact_email=org_dict.get('contact_email'),
                    street_address=org_dict.get('street_address'),
                    city=org_dict.get('city'),
                    state_province=org_dict.get('state_province'),
                    postal_code=org_dict.get('postal_code'),
                    country=org_dict.get('country', 'US'),
                    address=org_dict.get('address'),
                    domain=org_dict.get('domain'),
                    description=org_dict.get('description'),
                    logo_url=org_dict.get('logo_url'),
                    settings=org_dict.get('settings', {}),
                    is_active=org_dict.get('is_active', True)
                )
                org.id = UUID(org_dict['id']) if isinstance(org_dict['id'], str) else org_dict['id']
                org.created_at = org_dict.get('created_at')
                org.updated_at = org_dict.get('updated_at')
                organizations.append(org)
            return organizations
        except Exception as e:
            self._logger.error(f"Error getting all organizations: {str(e)}")
            raise

    async def get_organization_projects(self, organization_id: UUID) -> list:
        """
        Get all projects for an organization.

        WHAT: Retrieves all projects owned by the specified organization
        WHY: Organization admins need to view and manage their organization's projects

        BUSINESS CONTEXT:
        Projects are the top-level content organization structure within an organization.
        Each organization can have multiple projects (e.g., "Python Bootcamp", "Data Science Track").

        NOTE: Projects table schema not yet implemented - returns empty list as placeholder.

        Args:
            organization_id: UUID of the organization

        Returns:
            List of project dicts (currently empty - future implementation)
        """
        # Projects table doesn't exist yet, return empty list
        return []

    async def get_organization(self, organization_id: UUID) -> Optional[Organization]:
        """
        Get organization by ID with complete metadata.

        WHAT: Retrieves single organization entity by UUID
        WHY: Needed for organization detail views, settings pages, and validation

        BUSINESS CONTEXT:
        This is the primary method for retrieving organization information. Used by:
        - Organization dashboard to display org details
        - Settings pages for configuration
        - Authorization checks for organization access

        Args:
            organization_id: UUID of the organization to retrieve

        Returns:
            Organization entity if found, None if not found

        Raises:
            Exception: If database query fails
        """
        try:
            org_dict = await self._dao.get_organization_by_id(str(organization_id))
            if not org_dict:
                return None
            org = Organization(
                name=org_dict['name'],
                slug=org_dict['slug'],
                contact_phone=org_dict.get('contact_phone'),
                contact_email=org_dict.get('contact_email'),
                street_address=org_dict.get('street_address'),
                city=org_dict.get('city'),
                state_province=org_dict.get('state_province'),
                postal_code=org_dict.get('postal_code'),
                country=org_dict.get('country', 'US'),
                address=org_dict.get('address'),
                domain=org_dict.get('domain'),
                description=org_dict.get('description'),
                logo_url=org_dict.get('logo_url'),
                settings=org_dict.get('settings', {}),
                is_active=org_dict.get('is_active', True)
            )
            org.id = UUID(org_dict['id']) if isinstance(org_dict['id'], str) else org_dict['id']
            org.created_at = org_dict.get('created_at')
            org.updated_at = org_dict.get('updated_at')
            return org
        except Exception as e:
            self._logger.error(f"Error getting organization {organization_id}: {str(e)}")
            raise

    async def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        """
        Get organization by unique slug identifier.

        WHAT: Retrieves organization using human-readable slug
        WHY: Slugs provide user-friendly URLs (e.g., /orgs/acme-corp)

        BUSINESS CONTEXT:
        Slugs are unique, URL-safe identifiers used for:
        - Organization login pages (/login/acme-corp)
        - Public organization profiles
        - URL routing and navigation

        Args:
            slug: Unique slug identifier (e.g., 'acme-corp', 'google-edu')

        Returns:
            Organization entity if found, None if not found

        Raises:
            Exception: If database query fails
        """
        try:
            return await self._dao.get_by_slug(slug)
        except Exception as e:
            self._logger.error(f"Error getting organization by slug {slug}: {str(e)}")
            raise

    async def get_organization_by_domain(self, domain: str) -> Optional[Organization]:
        """
        Get organization by registered domain name.

        WHAT: Retrieves organization using email domain for auto-enrollment
        WHY: Enables automatic organization assignment based on user email domain

        BUSINESS CONTEXT:
        Domain-based organization lookup enables:
        - Auto-enrollment: Users with @acme.com email automatically join Acme org
        - Organization discovery during registration
        - Single sign-on (SSO) routing

        EXAMPLE:
        User registers with email 'alice@acme.com' → System finds organization
        with domain 'acme.com' → Auto-enrolls user in Acme organization

        Args:
            domain: Email domain (e.g., 'acme.com', 'google.com')

        Returns:
            Organization entity if found, None if not found

        Raises:
            Exception: If database query fails
        """
        try:
            return await self._dao.get_by_domain(domain)
        except Exception as e:
            self._logger.error(f"Error getting organization by domain {domain}: {str(e)}")
            raise

    async def update_organization(self, organization_id: UUID, name: str = None,
                                  description: str = None, logo_url: str = None,
                                  domain: str = None, address: str = None,
                                  contact_phone: str = None, contact_email: str = None,
                                  settings: Dict[str, Any] = None,
                                  is_active: bool = None) -> Organization:
        """
        Update organization details.

        Business Context:
        Organization admins can update organization profile, contact information,
        branding, and settings. Domain uniqueness is enforced across all organizations.

        Technical Implementation:
        Uses custom exceptions for proper error handling and validation.
        Only updates fields that are explicitly provided (non-None).

        Args:
            organization_id: UUID of organization to update
            name: Updated organization name
            description: Updated description
            logo_url: Updated logo URL
            domain: Updated domain (must be unique)
            address: Updated street address
            contact_phone: Updated contact phone
            contact_email: Updated contact email
            settings: Updated settings dictionary
            is_active: Updated active status

        Returns:
            Updated organization dict

        Raises:
            OrganizationNotFoundException: If organization_id not found
            OrganizationValidationException: If domain conflicts with existing org
            DatabaseException: If database operation fails
        """
        # Get existing organization
        existing_org = await self._dao.get_organization_by_id(str(organization_id))
        if not existing_org:
            raise OrganizationNotFoundException(
                message=f"Organization with ID {organization_id} not found",
                error_code="ORGANIZATION_NOT_FOUND",
                details={"organization_id": str(organization_id)}
            )

        # Check domain uniqueness if being changed
        if domain and domain != existing_org.get('domain'):
            if await self._dao.exists_by_domain(domain):
                raise OrganizationValidationException(
                    message=f"Organization with domain '{domain}' already exists",
                    error_code="DUPLICATE_DOMAIN",
                    details={"domain": domain, "organization_id": str(organization_id)}
                )

        # Build update data dict - only include non-None values
        update_data = {}
        if name is not None:
            update_data['name'] = name
        if description is not None:
            update_data['description'] = description
        if logo_url is not None:
            update_data['logo_url'] = logo_url
        if domain is not None:
            update_data['domain'] = domain
        if address is not None:
            update_data['address'] = address
        if contact_phone is not None:
            update_data['contact_phone'] = contact_phone
        if contact_email is not None:
            update_data['contact_email'] = contact_email
        if settings is not None:
            update_data['settings'] = settings
        if is_active is not None:
            update_data['is_active'] = is_active

        # Persist changes using DAO's update method
        try:
            updated_organization = await self._dao.update_organization(str(organization_id), update_data)
            self._logger.info(f"Organization updated successfully: {organization_id}")
            return updated_organization
        except DatabaseException:
            # Re-raise DatabaseException from DAO
            raise
        except (OrganizationNotFoundException, OrganizationValidationException):
            # Re-raise validation exceptions
            raise
        except Exception as e:
            # Wrap any other unexpected exceptions
            self._logger.error(f"Unexpected error updating organization {organization_id}: {str(e)}")
            raise OrganizationException(
                message=f"Failed to update organization",
                error_code="ORGANIZATION_UPDATE_ERROR",
                details={"organization_id": str(organization_id)},
                original_exception=e
            )

    async def delete_organization(self, organization_id: UUID) -> bool:
        """
        Delete organization and all associated data.

        WHAT: Permanently removes organization from the system
        WHY: Site admin may need to remove inactive or test organizations

        BUSINESS CONTEXT:
        Organization deletion is a DESTRUCTIVE operation that removes:
        - Organization entity and metadata
        - Organization members and roles (handled by foreign key cascade)
        - Projects, tracks, and courses (handled by foreign key cascade)
        - Meeting rooms and notifications

        SECURITY WARNING:
        This operation should be restricted to site administrators only.
        Consider implementing soft delete (is_active=false) instead of hard delete
        to preserve audit trails and prevent data loss.

        Args:
            organization_id: UUID of organization to delete

        Returns:
            True if deletion successful, False if organization not found

        Raises:
            ValueError: If organization doesn't exist
            Exception: If database operation fails
        """
        try:
            # Check if organization exists
            organization = await self._dao.get_by_id(organization_id)
            if not organization:
                raise ValueError(f"Organization with ID {organization_id} not found")

            # Delete organization
            result = await self._dao.delete(organization_id)

            if result:
                self._logger.info(f"Organization deleted successfully: {organization.slug}")

            return result

        except Exception as e:
            self._logger.error(f"Error deleting organization {organization_id}: {str(e)}")
            raise

    async def list_organizations(self, limit: int = 100, offset: int = 0) -> List[Organization]:
        """
        List all organizations with pagination support.

        WHAT: Retrieves paginated list of organizations
        WHY: Site admin needs to browse all organizations with performance optimization

        BUSINESS CONTEXT:
        Used by site admin dashboard to display organization directory.
        Pagination prevents performance issues with large organization counts.

        Args:
            limit: Maximum number of organizations to return (default: 100)
            offset: Number of organizations to skip for pagination (default: 0)

        Returns:
            List of Organization entities (up to limit count)

        Raises:
            Exception: If database query fails
        """
        try:
            return await self._dao.get_all(limit, offset)
        except Exception as e:
            self._logger.error(f"Error listing organizations: {str(e)}")
            raise

    async def list_active_organizations(self) -> List[Organization]:
        """
        List all active organizations.

        WHAT: Retrieves only organizations with is_active=True
        WHY: Filter out deactivated/suspended organizations from listings

        BUSINESS CONTEXT:
        Active organizations are those currently using the platform.
        Inactive organizations may be suspended, deleted, or in setup phase.

        Returns:
            List of active Organization entities

        Raises:
            Exception: If database query fails
        """
        try:
            return await self._dao.get_active()
        except Exception as e:
            self._logger.error(f"Error listing active organizations: {str(e)}")
            raise

    async def search_organizations(self, query: str, limit: int = 50) -> List[Organization]:
        """
        Search organizations by name, slug, or domain.

        WHAT: Full-text search across organization attributes
        WHY: Site admin needs to quickly find specific organizations

        BUSINESS CONTEXT:
        Search functionality supports:
        - Finding organization by partial name match
        - Looking up by slug or domain
        - Discovery for support and administration tasks

        Args:
            query: Search query string (searches name, slug, domain)
            limit: Maximum results to return (default: 50)

        Returns:
            List of matching Organization entities

        Raises:
            Exception: If database query fails
        """
        try:
            return await self._dao.search(query, limit)
        except Exception as e:
            self._logger.error(f"Error searching organizations: {str(e)}")
            raise

    async def get_organization_stats(self, organization_id: UUID) -> Dict[str, Any]:
        """
        Get organization statistics and metadata summary.

        WHAT: Retrieves key statistics and metadata for an organization
        WHY: Organization dashboard needs summary statistics

        BUSINESS CONTEXT:
        Provides overview information for organization dashboard including:
        - Basic metadata (name, slug, creation date)
        - Active status
        - Future: Member count, project count, usage metrics

        Args:
            organization_id: UUID of organization

        Returns:
            Dict with organization statistics

        Raises:
            ValueError: If organization doesn't exist
            Exception: If database query fails
        """
        try:
            organization = await self._dao.get_by_id(organization_id)
            if not organization:
                raise ValueError(f"Organization with ID {organization_id} not found")

            # Basic stats for now - could be extended with project counts, member counts, etc.
            return {
                "id": str(organization.id),
                "name": organization.name,
                "slug": organization.slug,
                "is_active": organization.is_active,
                "created_at": organization.created_at.isoformat() if organization.created_at else None,
                "updated_at": organization.updated_at.isoformat() if organization.updated_at else None
            }

        except Exception as e:
            self._logger.error(f"Error getting organization stats {organization_id}: {str(e)}")
            raise
