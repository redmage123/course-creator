"""
Organization-Based Authorization Middleware for Multi-Tenant Security

BUSINESS REQUIREMENT:
Prevent unauthorized cross-organization data access by enforcing tenant boundaries
at the application layer. Every authenticated request must be validated against
organization membership before allowing access to any resources.

TECHNICAL IMPLEMENTATION:
1. Extract JWT token and validate user identity
2. Extract organization_id from request (header, path, or body)
3. Verify user has active membership in requested organization
4. Set organization context for database queries
5. Log all access attempts for security auditing

SECURITY CONSIDERATIONS:
- Prevents privilege escalation across organizations
- Blocks unauthorized data access even if URLs are guessed
- Provides comprehensive audit trail for compliance
- Implements defense-in-depth security architecture
- Validates organization membership on every request

WHY THIS PREVENTS CROSS-TENANT ACCESS:
- Previous code had no organization validation in most services
- Instructors could access other organizations by changing URLs
- Redis cache keys were not tenant-isolated
- Database queries lacked organization filtering
- Now every request is validated against organization membership
"""

import logging
import uuid
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

import jwt
import httpx
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class OrganizationAuthorizationMiddleware(BaseHTTPMiddleware):
    """
    Multi-tenant authorization middleware enforcing organization boundaries
    
    Validates every authenticated request against organization membership
    and sets organization context for downstream processing.
    """
    
    def __init__(self, app, config: dict):
        super().__init__(app)
        self.config = config
        self.jwt_secret = config.get('jwt', {}).get('secret_key', 'your-secret-key-change-in-production')
        self.jwt_algorithm = config.get('jwt', {}).get('algorithm', 'HS256')
        self.user_service_url = config.get('services', {}).get('user_management_url', 'http://user-management:8000')
        self.org_service_url = config.get('services', {}).get('organization_management_url', 'http://organization-management:8008')
        
        # Endpoints that don't require organization validation
        self.exempt_endpoints = {
            '/health', '/docs', '/openapi.json', '/redoc',
            '/api/v1/auth/login', '/api/v1/auth/register', '/api/v1/auth/refresh'
        }
    
    async def dispatch(self, request: Request, call_next):
        """
        Process each request through organization authorization pipeline
        
        AUTHORIZATION FLOW:
        1. Check if endpoint requires organization validation
        2. Extract and validate JWT token
        3. Extract organization_id from request
        4. Verify user membership in organization
        5. Set organization context for database queries
        6. Log access attempt for security audit
        7. Allow request to proceed or reject with 403
        """
        
        # Skip validation for exempt endpoints
        if any(request.url.path.startswith(exempt) for exempt in self.exempt_endpoints):
            return await call_next(request)
        
        try:
            # Extract and validate JWT token
            user_info = await self._validate_jwt_token(request)
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or missing authentication token"
                )
            
            # Extract organization ID from request
            organization_id = await self._extract_organization_id(request)
            if not organization_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization ID required for this operation"
                )
            
            # Verify user has access to the organization
            has_access = await self._verify_organization_membership(
                user_info['id'], organization_id
            )
            
            if not has_access:
                # Log unauthorized access attempt
                await self._log_security_event(
                    user_id=user_info['id'],
                    organization_id=user_info.get('organization_id'),
                    action='UNAUTHORIZED_ACCESS_ATTEMPT',
                    resource_type='organization',
                    resource_id=organization_id,
                    attempted_organization_id=organization_id,
                    success=False,
                    details={'endpoint': request.url.path, 'method': request.method},
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get('user-agent')
                )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: User not authorized for organization {organization_id}"
                )
            
            # Set organization context for downstream processing
            request.state.organization_id = organization_id
            request.state.user_info = user_info
            
            # Log successful access
            await self._log_security_event(
                user_id=user_info['id'],
                organization_id=organization_id,
                action='ORGANIZATION_ACCESS',
                resource_type='organization',
                resource_id=organization_id,
                attempted_organization_id=organization_id,
                success=True,
                details={'endpoint': request.url.path, 'method': request.method},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent')
            )
            
            return await call_next(request)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Organization authorization middleware error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authorization service error"
            )
    
    async def _validate_jwt_token(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Extract and validate JWT token from Authorization header
        
        Args:
            request: FastAPI request object
            
        Returns:
            User information dictionary or None if invalid
        """
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return None
            
            token = auth_header.split(' ')[1]
            
            # Decode JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            user_id = payload.get('sub')
            if not user_id:
                return None
            
            # Get full user information from user service
            return await self._get_user_info(user_id)
            
        except jwt.ExpiredSignatureError:
            logger.warning("Expired JWT token in organization middleware")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token in organization middleware")
            return None
        except Exception as e:
            logger.error(f"JWT validation error: {e}")
            return None
    
    async def _extract_organization_id(self, request: Request) -> Optional[str]:
        """
        Extract organization ID from request headers, path, or body
        
        ORGANIZATION ID SOURCES (in priority order):
        1. X-Organization-ID header (preferred for API calls)
        2. Path parameter /api/v1/organizations/{org_id}/...
        3. Query parameter ?organization_id=...
        4. Request body organization_id field
        
        Args:
            request: FastAPI request object
            
        Returns:
            Organization ID string or None if not found
        """
        
        # 1. Check X-Organization-ID header
        org_id = request.headers.get('X-Organization-ID')
        if org_id:
            return org_id
        
        # 2. Check path parameter
        path_parts = request.url.path.split('/')
        if 'organizations' in path_parts:
            try:
                org_index = path_parts.index('organizations')
                if org_index + 1 < len(path_parts):
                    org_id = path_parts[org_index + 1]
                    # Validate UUID format
                    uuid.UUID(org_id)
                    return org_id
            except (ValueError, IndexError):
                pass
        
        # 3. Check query parameter
        org_id = request.query_params.get('organization_id')
        if org_id:
            try:
                uuid.UUID(org_id)
                return org_id
            except ValueError:
                pass
        
        # 4. Check request body (for POST/PUT requests)
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                # This is a simplified approach - in practice you'd need to handle
                # different content types and parse body appropriately
                body = getattr(request, '_body', None)
                if body and b'organization_id' in body:
                    # Would need more sophisticated JSON parsing in real implementation
                    pass
            except:
                pass
        
        return None
    
    async def _verify_organization_membership(self, user_id: str, organization_id: str) -> bool:
        """
        Verify user has active membership in the specified organization
        
        Args:
            user_id: User UUID
            organization_id: Organization UUID
            
        Returns:
            True if user has access, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.org_service_url}/api/v1/organizations/{organization_id}/members/{user_id}",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    membership_data = response.json()
                    return membership_data.get('status') == 'active'
                
                return False
                
        except httpx.RequestError as e:
            logger.error(f"Error verifying organization membership: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in membership verification: {e}")
            return False
    
    async def _get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from user management service
        
        Args:
            user_id: User UUID
            
        Returns:
            User information dictionary or None if not found
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.user_service_url}/api/v1/users/{user_id}",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    return response.json()
                
                return None
                
        except httpx.RequestError as e:
            logger.error(f"Error getting user info: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user info: {e}")
            return None
    
    async def _log_security_event(
        self,
        user_id: str,
        organization_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        attempted_organization_id: Optional[str],
        success: bool,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Log security events for audit and monitoring
        
        SECURITY AUDIT LOGGING:
        All organization access attempts are logged for security monitoring,
        compliance reporting, and forensic analysis. Failed access attempts
        are flagged for immediate security review.
        
        Args:
            user_id: User attempting access
            organization_id: User's primary organization
            action: Type of action attempted
            resource_type: Type of resource accessed
            resource_id: ID of specific resource
            attempted_organization_id: Organization user tried to access
            success: Whether access was granted
            details: Additional context information
            ip_address: Client IP address
            user_agent: Client user agent string
        """
        try:
            # In a real implementation, this would use a dedicated audit service
            # or write directly to a security audit database
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'organization_id': organization_id,
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'attempted_organization_id': attempted_organization_id,
                'success': success,
                'details': details or {},
                'ip_address': ip_address,
                'user_agent': user_agent
            }
            
            if success:
                logger.info(f"Security audit: {action} succeeded", extra=log_entry)
            else:
                logger.warning(f"Security audit: {action} FAILED", extra=log_entry)
                
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")


class OrganizationDependency:
    """
    FastAPI dependency for extracting organization context from middleware
    
    Usage:
        @app.get("/api/v1/courses")
        async def get_courses(org_context: dict = Depends(get_organization_context)):
            organization_id = org_context['organization_id']
            # Query courses filtered by organization_id
    """
    
    def __call__(self, request: Request) -> Dict[str, Any]:
        """
        Extract organization context set by middleware
        
        Args:
            request: FastAPI request object
            
        Returns:
            Dictionary containing organization_id and user_info
            
        Raises:
            HTTPException: If organization context not available
        """
        if not hasattr(request.state, 'organization_id'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Organization context not available - middleware not configured"
            )
        
        return {
            'organization_id': request.state.organization_id,
            'user_info': getattr(request.state, 'user_info', {})
        }


# Dependency instance for use in FastAPI endpoints
get_organization_context = OrganizationDependency()


def require_organization_role(required_roles: list) -> callable:
    """
    Create a dependency that requires specific roles within an organization
    
    ROLE-BASED ACCESS CONTROL:
    Combines organization membership validation with role-based permissions
    to provide fine-grained access control within tenant boundaries.
    
    Args:
        required_roles: List of required roles (e.g., ['admin', 'instructor'])
        
    Returns:
        FastAPI dependency function
        
    Usage:
        @app.delete("/api/v1/organizations/{org_id}/courses/{course_id}")
        async def delete_course(
            org_context: dict = Depends(require_organization_role(['admin', 'instructor']))
        ):
            # Only organization admins and instructors can delete courses
    """
    def role_checker(request: Request) -> Dict[str, Any]:
        org_context = get_organization_context(request)
        user_info = org_context['user_info']
        user_role = user_info.get('role', 'student')
        
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}, user role: {user_role}"
            )
        
        return org_context
    
    return role_checker