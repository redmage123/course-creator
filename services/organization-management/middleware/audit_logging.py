"""
Comprehensive Audit Logging Middleware
Tracks all RBAC operations, security events, and system actions
"""
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from organization_management.domain.entities.enhanced_role import Permission, RoleType


class AuditEventType(Enum):
    """Types of audit events"""

    # Authentication Events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"

    # Authorization Events
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"

    # Organization Management
    ORGANIZATION_CREATED = "organization_created"
    ORGANIZATION_UPDATED = "organization_updated"
    ORGANIZATION_DELETED = "organization_deleted"
    ORGANIZATION_ACTIVATED = "organization_activated"
    ORGANIZATION_DEACTIVATED = "organization_deactivated"

    # Member Management
    MEMBER_ADDED = "member_added"
    MEMBER_REMOVED = "member_removed"
    MEMBER_UPDATED = "member_updated"
    MEMBER_ACTIVATED = "member_activated"
    MEMBER_DEACTIVATED = "member_deactivated"

    # Track Management
    TRACK_CREATED = "track_created"
    TRACK_UPDATED = "track_updated"
    TRACK_DELETED = "track_deleted"
    TRACK_PUBLISHED = "track_published"
    TRACK_UNPUBLISHED = "track_unpublished"
    TRACK_DUPLICATED = "track_duplicated"

    # Enrollment Events
    STUDENT_ENROLLED = "student_enrolled"
    STUDENT_UNENROLLED = "student_unenrolled"
    BULK_ENROLLMENT = "bulk_enrollment"
    INSTRUCTOR_ASSIGNED = "instructor_assigned"
    INSTRUCTOR_UNASSIGNED = "instructor_unassigned"

    # Meeting Room Events
    MEETING_ROOM_CREATED = "meeting_room_created"
    MEETING_ROOM_UPDATED = "meeting_room_updated"
    MEETING_ROOM_DELETED = "meeting_room_deleted"
    MEETING_INVITATION_SENT = "meeting_invitation_sent"

    # Integration Events
    TEAMS_INTEGRATION_SUCCESS = "teams_integration_success"
    TEAMS_INTEGRATION_FAILURE = "teams_integration_failure"
    ZOOM_INTEGRATION_SUCCESS = "zoom_integration_success"
    ZOOM_INTEGRATION_FAILURE = "zoom_integration_failure"

    # Data Export Events
    DATA_EXPORTED = "data_exported"
    REPORT_GENERATED = "report_generated"
    ANALYTICS_ACCESSED = "analytics_accessed"

    # Security Events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

    # System Events
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    DATABASE_CONNECTION_ERROR = "database_connection_error"
    CONFIGURATION_CHANGED = "configuration_changed"


class AuditEventSeverity(Enum):
    """Severity levels for audit events"""

    LOW = "low"           # Routine operations
    MEDIUM = "medium"     # Important business operations
    HIGH = "high"         # Critical security events
    CRITICAL = "critical" # System-threatening events


class AuditEvent:
    """Structured audit event"""

    def __init__(
        self,
        event_type: AuditEventType,
        severity: AuditEventSeverity,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        self.event_id = str(UUID.uuid4())
        self.event_type = event_type
        self.severity = severity
        self.timestamp = datetime.utcnow()
        self.user_id = user_id
        self.organization_id = organization_id
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.details = details or {}
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.request_id = request_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_id": self.request_id
        }

    def to_log_message(self) -> str:
        """Convert to human-readable log message"""
        message_parts = [
            f"[{self.severity.value.upper()}]",
            f"{self.event_type.value}:"
        ]

        if self.user_id:
            message_parts.append(f"user={self.user_id}")

        if self.organization_id:
            message_parts.append(f"org={self.organization_id}")

        if self.resource_type and self.resource_id:
            message_parts.append(f"{self.resource_type}={self.resource_id}")

        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            message_parts.append(f"details=({detail_str})")

        return " ".join(message_parts)


class AuditLogger:
    """Centralized audit logging service"""

    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)

        # Create audit-specific handler if not exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_event(self, event: AuditEvent):
        """Log an audit event"""

        # Determine log level based on severity
        log_level = {
            AuditEventSeverity.LOW: logging.INFO,
            AuditEventSeverity.MEDIUM: logging.INFO,
            AuditEventSeverity.HIGH: logging.WARNING,
            AuditEventSeverity.CRITICAL: logging.ERROR
        }.get(event.severity, logging.INFO)

        # Log with structured data
        self.logger.log(
            log_level,
            event.to_log_message(),
            extra={
                "audit_event": event.to_dict(),
                "event_type": event.event_type.value,
                "severity": event.severity.value,
                "user_id": event.user_id,
                "organization_id": event.organization_id,
                "request_id": event.request_id
            }
        )

    def log_authentication(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """Log authentication events"""

        severity = AuditEventSeverity.MEDIUM if success else AuditEventSeverity.HIGH

        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            details=details,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            request_id=getattr(request.state, 'request_id', None) if request else None
        )

        self.log_event(event)

    def log_authorization(
        self,
        permission: Permission,
        user_id: str,
        organization_id: str,
        granted: bool,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None
    ):
        """Log authorization events"""

        event_type = AuditEventType.PERMISSION_GRANTED if granted else AuditEventType.PERMISSION_DENIED
        severity = AuditEventSeverity.MEDIUM if granted else AuditEventSeverity.HIGH

        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            organization_id=organization_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details={"permission": permission.value},
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            request_id=getattr(request.state, 'request_id', None) if request else None
        )

        self.log_event(event)

    def log_organization_event(
        self,
        event_type: AuditEventType,
        organization_id: str,
        user_id: str,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """Log organization management events"""

        # Determine severity based on event type
        severity_map = {
            AuditEventType.ORGANIZATION_CREATED: AuditEventSeverity.MEDIUM,
            AuditEventType.ORGANIZATION_UPDATED: AuditEventSeverity.LOW,
            AuditEventType.ORGANIZATION_DELETED: AuditEventSeverity.CRITICAL,
            AuditEventType.ORGANIZATION_DEACTIVATED: AuditEventSeverity.HIGH
        }
        severity = severity_map.get(event_type, AuditEventSeverity.MEDIUM)

        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            organization_id=organization_id,
            resource_type="organization",
            resource_id=organization_id,
            details=details,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            request_id=getattr(request.state, 'request_id', None) if request else None
        )

        self.log_event(event)

    def log_member_event(
        self,
        event_type: AuditEventType,
        organization_id: str,
        target_user_id: str,
        acting_user_id: str,
        role_type: Optional[RoleType] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """Log member management events"""

        severity = AuditEventSeverity.MEDIUM
        if event_type in [AuditEventType.MEMBER_REMOVED, AuditEventType.ROLE_REMOVED]:
            severity = AuditEventSeverity.HIGH

        event_details = details or {}
        if role_type:
            event_details["role_type"] = role_type.value
        event_details["target_user_id"] = target_user_id

        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=acting_user_id,
            organization_id=organization_id,
            resource_type="membership",
            resource_id=target_user_id,
            details=event_details,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            request_id=getattr(request.state, 'request_id', None) if request else None
        )

        self.log_event(event)

    def log_track_event(
        self,
        event_type: AuditEventType,
        track_id: str,
        organization_id: str,
        user_id: str,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """Log track management events"""

        severity_map = {
            AuditEventType.TRACK_CREATED: AuditEventSeverity.MEDIUM,
            AuditEventType.TRACK_UPDATED: AuditEventSeverity.LOW,
            AuditEventType.TRACK_DELETED: AuditEventSeverity.HIGH,
            AuditEventType.TRACK_PUBLISHED: AuditEventSeverity.MEDIUM,
            AuditEventType.TRACK_UNPUBLISHED: AuditEventSeverity.MEDIUM
        }
        severity = severity_map.get(event_type, AuditEventSeverity.MEDIUM)

        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            organization_id=organization_id,
            resource_type="track",
            resource_id=track_id,
            details=details,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            request_id=getattr(request.state, 'request_id', None) if request else None
        )

        self.log_event(event)

    def log_enrollment_event(
        self,
        event_type: AuditEventType,
        track_id: str,
        organization_id: str,
        acting_user_id: str,
        student_ids: List[str],
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """Log enrollment events"""

        event_details = details or {}
        event_details["student_count"] = len(student_ids)
        event_details["student_ids"] = student_ids

        event = AuditEvent(
            event_type=event_type,
            severity=AuditEventSeverity.MEDIUM,
            user_id=acting_user_id,
            organization_id=organization_id,
            resource_type="track",
            resource_id=track_id,
            details=event_details,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            request_id=getattr(request.state, 'request_id', None) if request else None
        )

        self.log_event(event)

    def log_meeting_room_event(
        self,
        event_type: AuditEventType,
        room_id: str,
        organization_id: str,
        user_id: str,
        platform: str,
        room_type: str,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """Log meeting room events"""

        event_details = details or {}
        event_details["platform"] = platform
        event_details["room_type"] = room_type

        severity = AuditEventSeverity.MEDIUM
        if event_type == AuditEventType.MEETING_ROOM_DELETED:
            severity = AuditEventSeverity.HIGH

        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            organization_id=organization_id,
            resource_type="meeting_room",
            resource_id=room_id,
            details=event_details,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            request_id=getattr(request.state, 'request_id', None) if request else None
        )

        self.log_event(event)

    def log_integration_event(
        self,
        event_type: AuditEventType,
        platform: str,
        success: bool,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """Log integration events"""

        severity = AuditEventSeverity.MEDIUM if success else AuditEventSeverity.HIGH

        event_details = details or {}
        event_details["platform"] = platform
        event_details["success"] = success

        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            organization_id=organization_id,
            resource_type="integration",
            resource_id=platform,
            details=event_details,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            request_id=getattr(request.state, 'request_id', None) if request else None
        )

        self.log_event(event)

    def log_security_event(
        self,
        event_type: AuditEventType,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        request: Optional[Request] = None
    ):
        """Log security events"""

        event = AuditEvent(
            event_type=event_type,
            severity=AuditEventSeverity.CRITICAL,
            user_id=user_id,
            organization_id=organization_id,
            details=details,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            request_id=getattr(request.state, 'request_id', None) if request else None
        )

        self.log_event(event)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically log API requests"""

    def __init__(self, app, audit_logger: Optional[AuditLogger] = None):
        super().__init__(app)
        self.audit_logger = audit_logger or AuditLogger()

        # Paths that should be audited
        self.audit_paths = {
            # Organization management
            "/api/v1/organizations": "organization",
            "/api/v1/site-admin/organizations": "organization",

            # Member management
            "/api/v1/rbac/organizations": "membership",

            # Track management
            "/api/v1/tracks": "track",

            # Meeting rooms
            "/api/v1/rbac/meeting-rooms": "meeting_room",

            # Authentication
            "/api/v1/auth": "authentication"
        }

    async def dispatch(self, request: Request, call_next):
        # Process the request
        response = await call_next(request)

        # Log successful operations
        if self._should_audit_request(request, response):
            await self._log_api_request(request, response)

        return response

    def _should_audit_request(self, request: Request, response: Response) -> bool:
        """Determine if request should be audited"""

        # Skip GET requests (read operations) unless they failed
        if request.method == "GET" and response.status_code < 400:
            return False

        # Audit all non-GET operations
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            return True

        # Audit failed requests
        if response.status_code >= 400:
            return True

        return False

    async def _log_api_request(self, request: Request, response: Response):
        """Log API request as audit event"""

        # Extract user information from request
        user_id = getattr(request.state, 'user_id', None)
        organization_id = getattr(request.state, 'organization_id', None)
        request_id = getattr(request.state, 'request_id', None)

        # Determine event type based on path and method
        event_type = self._determine_event_type(request.url.path, request.method)

        # Determine severity based on response status
        if response.status_code >= 500:
            severity = AuditEventSeverity.CRITICAL
        elif response.status_code >= 400:
            severity = AuditEventSeverity.HIGH
        else:
            severity = AuditEventSeverity.MEDIUM

        # Create audit event
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            organization_id=organization_id,
            details={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "query_params": dict(request.query_params)
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_id=request_id
        )

        self.audit_logger.log_event(event)

    def _determine_event_type(self, path: str, method: str) -> AuditEventType:
        """Determine audit event type from request path and method"""

        # Default to suspicious activity for unknown patterns
        default_event = AuditEventType.SUSPICIOUS_ACTIVITY

        # Map common patterns
        if "/organizations" in path:
            if method == "POST":
                return AuditEventType.ORGANIZATION_CREATED
            elif method == "PUT":
                return AuditEventType.ORGANIZATION_UPDATED
            elif method == "DELETE":
                return AuditEventType.ORGANIZATION_DELETED

        elif "/members" in path:
            if method == "POST":
                return AuditEventType.MEMBER_ADDED
            elif method == "DELETE":
                return AuditEventType.MEMBER_REMOVED

        elif "/tracks" in path:
            if method == "POST":
                return AuditEventType.TRACK_CREATED
            elif method == "PUT":
                return AuditEventType.TRACK_UPDATED
            elif method == "DELETE":
                return AuditEventType.TRACK_DELETED

        elif "/meeting-rooms" in path:
            if method == "POST":
                return AuditEventType.MEETING_ROOM_CREATED
            elif method == "DELETE":
                return AuditEventType.MEETING_ROOM_DELETED

        return default_event

# Global audit logger instance
audit_logger = AuditLogger()