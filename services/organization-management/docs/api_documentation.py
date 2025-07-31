"""
Enhanced RBAC API Documentation
Comprehensive OpenAPI schemas and documentation for all Enhanced RBAC endpoints
"""
from fastapi import FastAPI
from typing import Dict, List, Any

# Enhanced OpenAPI documentation configuration
ENHANCED_RBAC_API_DOCS = {
    "title": "Enhanced RBAC System API",
    "description": """
# Course Creator Platform - Enhanced RBAC System

A comprehensive Role-Based Access Control system for multi-tenant course creation platform with:

## Key Features
- **Organization Management**: Multi-tenant organization administration
- **Enhanced Roles**: Granular permission system with 20+ specific permissions
- **Meeting Room Integration**: MS Teams and Zoom room creation and management
- **Track Management**: Learning path creation with automatic enrollment
- **Site Administration**: Platform-wide management and organization deletion
- **Student Assignment**: Track-based enrollment with instructor assignments

## Authentication
All endpoints require JWT Bearer token authentication:
```
Authorization: Bearer <your-jwt-token>
```

## Permission System
The system uses a granular permission model with the following role hierarchy:
- **Site Admin**: Full platform control including organization deletion
- **Organization Admin**: Manage organization members, tracks, and meeting rooms
- **Instructor**: Access to assigned tracks and teaching materials
- **Student**: Access to enrolled tracks and learning content

## Rate Limiting
API endpoints are rate-limited to prevent abuse:
- **Authentication endpoints**: 10 requests per minute
- **CRUD operations**: 100 requests per minute
- **Bulk operations**: 10 requests per minute

## Error Handling
All endpoints return standardized error responses:
```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2025-07-31T12:00:00Z"
}
```

## Pagination
List endpoints support cursor-based pagination:
```
GET /api/v1/organizations?skip=0&limit=50
```
""",
    "version": "2.0.0",
    "contact": {
        "name": "Course Creator Platform Support",
        "email": "support@coursecreator.dev",
        "url": "https://docs.coursecreator.dev"
    },
    "license": {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    "servers": [
        {
            "url": "https://api.coursecreator.dev",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.coursecreator.dev",
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8008",
            "description": "Development server"
        }
    ]
}

# OpenAPI Tag definitions
API_TAGS = [
    {
        "name": "Authentication",
        "description": "User authentication and authorization operations"
    },
    {
        "name": "Organizations",
        "description": "Organization management operations"
    },
    {
        "name": "RBAC",
        "description": "Role-Based Access Control operations including member management"
    },
    {
        "name": "Tracks",
        "description": "Learning track management and enrollment operations"
    },
    {
        "name": "Meeting Rooms",
        "description": "MS Teams and Zoom meeting room integration"
    },
    {
        "name": "Site Admin",
        "description": "Platform-wide administrative operations"
    },
    {
        "name": "Analytics",
        "description": "Platform and organization analytics"
    },
    {
        "name": "Health",
        "description": "Service health and monitoring endpoints"
    }
]

# Common response schemas
COMMON_RESPONSES = {
    400: {
        "description": "Bad Request",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string"},
                        "error_code": {"type": "string"},
                        "validation_errors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "field": {"type": "string"},
                                    "message": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "example": {
                    "detail": "Validation error",
                    "error_code": "VALIDATION_ERROR",
                    "validation_errors": [
                        {
                            "field": "email",
                            "message": "Invalid email format"
                        }
                    ]
                }
            }
        }
    },
    401: {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string"},
                        "error_code": {"type": "string"}
                    }
                },
                "example": {
                    "detail": "Invalid authentication credentials",
                    "error_code": "INVALID_TOKEN"
                }
            }
        }
    },
    403: {
        "description": "Forbidden",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string"},
                        "error_code": {"type": "string"},
                        "required_permission": {"type": "string"}
                    }
                },
                "example": {
                    "detail": "Insufficient permissions",
                    "error_code": "PERMISSION_DENIED",
                    "required_permission": "ADD_ORGANIZATION_ADMINS"
                }
            }
        }
    },
    404: {
        "description": "Not Found",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string"},
                        "error_code": {"type": "string"}
                    }
                },
                "example": {
                    "detail": "Resource not found",
                    "error_code": "NOT_FOUND"
                }
            }
        }
    },
    429: {
        "description": "Too Many Requests",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string"},
                        "error_code": {"type": "string"},
                        "retry_after": {"type": "integer"}
                    }
                },
                "example": {
                    "detail": "Rate limit exceeded",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": 60
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string"},
                        "error_code": {"type": "string"},
                        "request_id": {"type": "string"}
                    }
                },
                "example": {
                    "detail": "Internal server error",
                    "error_code": "INTERNAL_ERROR",
                    "request_id": "req_12345"
                }
            }
        }
    }
}

# Enhanced schema definitions
ENHANCED_SCHEMAS = {
    "Permission": {
        "type": "string",
        "enum": [
            "DELETE_ANY_ORGANIZATION",
            "ADD_ORGANIZATION_ADMINS",
            "REMOVE_ORGANIZATION_ADMINS",
            "ADD_INSTRUCTORS_TO_ORG",
            "REMOVE_INSTRUCTORS_FROM_ORG",
            "ADD_STUDENTS_TO_PROJECT",
            "REMOVE_STUDENTS_FROM_PROJECT",
            "CREATE_TRACKS",
            "MANAGE_TRACKS",
            "PUBLISH_TRACKS",
            "ASSIGN_INSTRUCTORS_TO_TRACKS",
            "REMOVE_INSTRUCTORS_FROM_TRACKS",
            "CREATE_TEAMS_ROOMS",
            "CREATE_ZOOM_ROOMS",
            "MANAGE_MEETING_ROOMS",
            "DELETE_MEETING_ROOMS",
            "SEND_MEETING_INVITATIONS",
            "MANAGE_ORGANIZATION",
            "VIEW_ANALYTICS",
            "EXPORT_DATA"
        ],
        "description": "Granular permission system for RBAC"
    },

    "RoleType": {
        "type": "string",
        "enum": [
            "site_admin",
            "organization_admin",
            "instructor",
            "student"
        ],
        "description": "User role types in the system"
    },

    "MeetingPlatform": {
        "type": "string",
        "enum": ["teams", "zoom"],
        "description": "Supported meeting platforms"
    },

    "RoomType": {
        "type": "string",
        "enum": [
            "organization_room",
            "project_room",
            "track_room",
            "instructor_room"
        ],
        "description": "Types of meeting rooms"
    },

    "TrackStatus": {
        "type": "string",
        "enum": ["draft", "published", "archived"],
        "description": "Track publication status"
    },

    "DifficultyLevel": {
        "type": "string",
        "enum": ["beginner", "intermediate", "advanced"],
        "description": "Track difficulty levels"
    },

    "EnhancedRole": {
        "type": "object",
        "properties": {
            "role_type": {"$ref": "#/components/schemas/RoleType"},
            "organization_id": {
                "type": "string",
                "format": "uuid",
                "description": "Organization ID for role scope"
            },
            "permissions": {
                "type": "array",
                "items": {"$ref": "#/components/schemas/Permission"},
                "description": "Specific permissions granted to this role"
            },
            "project_ids": {
                "type": "array",
                "items": {
                    "type": "string",
                    "format": "uuid"
                },
                "description": "Project IDs this role has access to"
            }
        },
        "required": ["role_type", "organization_id"],
        "description": "Enhanced role with granular permissions"
    },

    "MemberResponse": {
        "type": "object",
        "properties": {
            "membership_id": {
                "type": "string",
                "format": "uuid",
                "description": "Unique membership identifier"
            },
            "user_id": {
                "type": "string",
                "format": "uuid",
                "description": "User identifier"
            },
            "email": {
                "type": "string",
                "format": "email",
                "description": "User email address"
            },
            "name": {
                "type": "string",
                "description": "User display name"
            },
            "role_type": {"$ref": "#/components/schemas/RoleType"},
            "permissions": {
                "type": "array",
                "items": {"$ref": "#/components/schemas/Permission"},
                "description": "Active permissions for this member"
            },
            "project_ids": {
                "type": "array",
                "items": {
                    "type": "string",
                    "format": "uuid"
                },
                "description": "Projects this member has access to"
            },
            "track_ids": {
                "type": "array",
                "items": {
                    "type": "string",
                    "format": "uuid"
                },
                "description": "Tracks this member is assigned to"
            },
            "status": {
                "type": "string",
                "enum": ["active", "pending", "inactive"],
                "description": "Member status"
            },
            "invited_at": {
                "type": "string",
                "format": "date-time",
                "description": "When the member was invited"
            },
            "accepted_at": {
                "type": "string",
                "format": "date-time",
                "nullable": True,
                "description": "When the member accepted the invitation"
            }
        },
        "required": ["membership_id", "user_id", "email", "role_type", "status"],
        "description": "Organization member information"
    },

    "MeetingRoomResponse": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "format": "uuid",
                "description": "Meeting room identifier"
            },
            "name": {
                "type": "string",
                "description": "Room name"
            },
            "display_name": {
                "type": "string",
                "description": "Formatted display name"
            },
            "platform": {"$ref": "#/components/schemas/MeetingPlatform"},
            "room_type": {"$ref": "#/components/schemas/RoomType"},
            "join_url": {
                "type": "string",
                "format": "uri",
                "nullable": True,
                "description": "URL to join the meeting"
            },
            "host_url": {
                "type": "string",
                "format": "uri",
                "nullable": True,
                "description": "URL for meeting host"
            },
            "meeting_id": {
                "type": "string",
                "nullable": True,
                "description": "Platform-specific meeting ID"
            },
            "status": {
                "type": "string",
                "enum": ["active", "scheduled", "ended"],
                "description": "Meeting status"
            },
            "created_at": {
                "type": "string",
                "format": "date-time",
                "description": "When the room was created"
            }
        },
        "required": ["id", "name", "platform", "room_type", "status"],
        "description": "Meeting room information"
    },

    "TrackResponse": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "format": "uuid",
                "description": "Track identifier"
            },
            "name": {
                "type": "string",
                "description": "Track name"
            },
            "description": {
                "type": "string",
                "nullable": True,
                "description": "Track description"
            },
            "project_id": {
                "type": "string",
                "format": "uuid",
                "description": "Parent project ID"
            },
            "organization_id": {
                "type": "string",
                "format": "uuid",
                "description": "Organization ID"
            },
            "target_audience": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Target audience for this track"
            },
            "prerequisites": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Prerequisites for enrollment"
            },
            "learning_objectives": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Learning objectives"
            },
            "duration_weeks": {
                "type": "integer",
                "minimum": 1,
                "maximum": 52,
                "nullable": True,
                "description": "Track duration in weeks"
            },
            "difficulty_level": {"$ref": "#/components/schemas/DifficultyLevel"},
            "max_students": {
                "type": "integer",
                "minimum": 1,
                "nullable": True,
                "description": "Maximum number of students"
            },
            "status": {"$ref": "#/components/schemas/TrackStatus"},
            "enrollment_count": {
                "type": "integer",
                "description": "Current enrollment count"
            },
            "instructor_count": {
                "type": "integer",
                "description": "Number of assigned instructors"
            },
            "created_at": {
                "type": "string",
                "format": "date-time",
                "description": "Track creation timestamp"
            },
            "updated_at": {
                "type": "string",
                "format": "date-time",
                "description": "Last update timestamp"
            }
        },
        "required": ["id", "name", "project_id", "organization_id", "difficulty_level", "status"],
        "description": "Learning track information"
    }
}

# Example API usage documentation
API_EXAMPLES = {
    "add_member": {
        "summary": "Add Organization Member",
        "description": "Add a new admin or instructor to an organization",
        "request_body": {
            "user_email": "instructor@example.com",
            "role_type": "instructor",
            "project_ids": ["proj-123", "proj-456"]
        },
        "response": {
            "membership_id": "mem-789",
            "user_id": "user-123",
            "email": "instructor@example.com",
            "name": "John Instructor",
            "role_type": "instructor",
            "permissions": ["CREATE_TRACKS", "MANAGE_TRACKS"],
            "status": "active"
        }
    },

    "create_meeting_room": {
        "summary": "Create Meeting Room",
        "description": "Create a Teams or Zoom meeting room for a track, instructor, or project",
        "request_body": {
            "name": "App Development Track Room",
            "platform": "teams",
            "room_type": "track_room",
            "track_id": "track-123",
            "settings": {
                "auto_recording": True,
                "waiting_room": True,
                "mute_on_entry": True,
                "allow_screen_sharing": True
            }
        },
        "response": {
            "id": "room-456",
            "name": "App Development Track Room",
            "platform": "teams",
            "room_type": "track_room",
            "join_url": "https://teams.microsoft.com/l/meetup-join/...",
            "status": "active"
        }
    },

    "create_track": {
        "summary": "Create Learning Track",
        "description": "Create a new learning track with automatic enrollment capabilities",
        "request_body": {
            "name": "Mobile App Development",
            "description": "Comprehensive mobile app development track",
            "project_id": "proj-123",
            "target_audience": ["developers", "students"],
            "prerequisites": ["Basic programming knowledge"],
            "learning_objectives": [
                "Build native mobile applications",
                "Understand mobile UI/UX principles",
                "Deploy apps to app stores"
            ],
            "duration_weeks": 12,
            "difficulty_level": "intermediate",
            "max_students": 50
        },
        "response": {
            "id": "track-789",
            "name": "Mobile App Development",
            "status": "draft",
            "enrollment_count": 0,
            "instructor_count": 0
        }
    }
}


def configure_enhanced_api_docs(app: FastAPI) -> None:
    """Configure enhanced API documentation for FastAPI app"""

    # Update OpenAPI info
    app.openapi_info = ENHANCED_RBAC_API_DOCS

    # Add tags
    app.openapi_tags = API_TAGS

    # Add common responses to all routes
    for route in app.routes:
        if hasattr(route, 'responses'):
            route.responses.update(COMMON_RESPONSES)

    # Add security scheme
    app.openapi_components = {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT Bearer token authentication"
            }
        },
        "schemas": ENHANCED_SCHEMAS
    }

    # Add global security requirement
    app.openapi_security = [{"bearerAuth": []}]


def get_api_examples() -> Dict[str, Any]:
    """Get comprehensive API usage examples"""
    return API_EXAMPLES