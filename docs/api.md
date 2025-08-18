# Course Creator Platform - API Documentation

**Version**: 3.0.0 - Password Management & Enhanced UI Features  
**Last Updated**: 2025-08-11

## Overview

The Course Creator Platform provides a comprehensive RESTful API for managing courses, users, and content. The API is built using FastAPI and follows REST conventions with a microservices architecture.

**Version 3.0 Highlights:**
- ✨ **Password Management System**: Self-service password changes with JWT authentication
- 🏢 **Enhanced Organization Registration**: Automatic admin account creation with password setup
- 🔐 **Professional Email Validation**: Business-only email enforcement with detailed error handling
- 📝 **Comprehensive Form Validation**: Real-time validation with specific error messages

## Microservices Architecture

The platform consists of 8 core backend services including the Enhanced RBAC System:

1. **User Management Service** (Port 8000) - Authentication, user profiles, basic RBAC, **password management system**
2. **Course Generator Service** (Port 8001) - AI-powered content generation
3. **Content Storage Service** (Port 8003) - File storage and versioning
4. **Course Management Service** (Port 8004) - Course CRUD operations and bi-directional feedback
5. **Content Management Service** (Port 8005) - Upload/download and multi-format export
6. **Lab Container Manager Service** (Port 8006) - Individual student Docker container management with multi-IDE support
7. **Analytics Service** (Port 8007) - Student analytics, progress tracking, and learning insights
8. **Organization Management Service** (Port 8008) - Enhanced RBAC System with multi-tenant organization management and **automatic admin account creation with password management**

## Base URLs

- **User Management**: `http://localhost:8000`
- **Course Generator**: `http://localhost:8001`
- **Content Storage**: `http://localhost:8003`
- **Course Management**: `http://localhost:8004`
- **Content Management**: `http://localhost:8005`
- **Lab Container Manager**: `http://localhost:8006`
- **Analytics Service**: `http://localhost:8007`
- **Organization Management (RBAC)**: `http://localhost:8008`
- **Production**: `https://your-domain.com/api`

## Authentication

All protected endpoints require JWT authentication. Include the token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Getting a Token

```http
POST http://localhost:8000/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "your-password"
}
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user-id",
    "username": "user@example.com",
    "role": "instructor",
    "full_name": "John Doe"
  }
}
```

## Security Considerations (v3.0)

### Password Security
- **Minimum Requirements**: 8 characters minimum, complexity scoring based on character types
- **Professional Email Enforcement**: Business-only emails required for organization registration (blocks Gmail, Yahoo, etc.)
- **Current Password Verification**: Password changes require current password validation
- **JWT Token Authentication**: All password operations require valid JWT tokens
- **Secure Transmission**: Use HTTPS in production for all password-related operations

### Professional Organization Validation
- **Email Domain Filtering**: Automatic rejection of personal email providers
- **Phone Number Validation**: Professional contact numbers required with international format support
- **Address Requirements**: Complete physical addresses required (minimum 10 characters)
- **Slug Uniqueness**: Organization identifiers must be unique across the platform

### Rate Limiting and Security Headers
- **Rate Limiting**: Password change attempts are rate-limited per user
- **CORS Headers**: Proper CORS configuration for browser-based clients
- **Content Security Policy**: Strict CSP headers for frontend security
- **Authentication Timeouts**: JWT tokens have configurable expiration times

## Core Endpoints

### Health Check

Check if services are running and healthy.

```http
GET http://localhost:8000/health
GET http://localhost:8001/health
GET http://localhost:8003/health
GET http://localhost:8004/health
GET http://localhost:8005/health
GET http://localhost:8006/health
GET http://localhost:8007/health
GET http://localhost:8008/health
```

Response:
```json
{
  "status": "healthy",
  "service": "user-management",
  "version": "1.0.0",
  "timestamp": "2025-07-16T10:30:00Z"
}
```

## User Management Service (Port 8000)

### Register User

Create a new user account.

```http
POST http://localhost:8000/auth/register
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "secure-password",
  "full_name": "John Doe",
  "role": "student"
}
```

Response:
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "user-123",
    "username": "user@example.com",
    "full_name": "John Doe",
    "role": "student",
    "created_at": "2025-07-16T10:30:00Z"
  }
}
```

### Login

Authenticate user and get access token.

```http
POST http://localhost:8000/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "secure-password"
}
```

### Get Current User

Get the current authenticated user's information.

```http
GET http://localhost:8000/auth/profile
Authorization: Bearer <token>
```

Response:
```json
{
  "id": "user-123",
  "username": "user@example.com",
  "full_name": "John Doe",
  "role": "student",
  "created_at": "2025-07-16T10:30:00Z"
}
```

### Password Management (v3.0)

Change the current user's password. Requires authentication.

```http
POST http://localhost:8000/auth/password/change
Authorization: Bearer <token>
Content-Type: application/json

{
  "old_password": "current-password",
  "new_password": "new-secure-password"
}
```

**Request Parameters:**
- `old_password` (string, required): Current password for verification
- `new_password` (string, required): New password (minimum 8 characters)

**Success Response:**
```json
{
  "message": "Password changed successfully"
}
```

**Error Responses:**
```json
// Invalid old password
{
  "detail": "Invalid old password"
}

// Validation error
{
  "detail": "New password must be at least 8 characters long"
}

// Authentication required
{
  "detail": "Authentication required"
}
```

### Password Reset

Request a password reset (sends reset email).

```http
POST http://localhost:8000/auth/password/reset
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Success Response:**
```json
{
  "message": "Password reset email sent"
}
```

### User Management

List and manage users (admin only).

```http
GET http://localhost:8000/users
Authorization: Bearer <admin-token>
```

Response:
```json
{
  "users": [
    {
      "id": "user-123",
      "username": "student@example.com",
      "full_name": "Jane Student",
      "role": "student",
      "created_at": "2025-07-16T10:30:00Z"
    }
  ]
}
```

## Course Generator Service (Port 8001)

### Generate Syllabus

Generate a course syllabus using AI.

```http
POST http://localhost:8001/generate/syllabus
Authorization: Bearer <instructor-token>
Content-Type: application/json

{
  "course_title": "Introduction to Python Programming",
  "course_description": "A comprehensive course covering Python fundamentals",
  "target_audience": "beginner",
  "duration_hours": 40
}
```

Response:
```json
{
  "syllabus": {
    "course_id": "course-123",
    "title": "Introduction to Python Programming",
    "overview": "This course provides a comprehensive introduction to Python programming...",
    "modules": [
      {
        "module_number": 1,
        "title": "Python Basics",
        "topics": ["Variables", "Data Types", "Control Flow"],
        "duration_hours": 8
      }
    ]
  }
}
```

### Generate Slides

Generate presentation slides from syllabus.

```http
POST http://localhost:8001/generate/slides
Authorization: Bearer <instructor-token>
Content-Type: application/json

{
  "course_id": "course-123",
  "syllabus_content": "...",
  "slide_count": 20
}
```

### Generate Exercises

Generate interactive exercises for a course.

```http
POST http://localhost:8001/exercises/generate
Authorization: Bearer <instructor-token>
Content-Type: application/json

{
  "course_id": "course-123",
  "difficulty": "beginner",
  "exercise_count": 10
}
```

Response:
```json
{
  "exercises": [
    {
      "id": "exercise-456",
      "title": "Variable Assignment Exercise",
      "description": "Practice creating and using variables",
      "type": "interactive_lab",
      "difficulty": "beginner",
      "starter_code": "# Your code here",
      "solution": "name = 'Alice'",
      "validation": "assert name == 'Alice'"
    }
  ]
}
```

### Generate Quiz

Generate quizzes for a course.

```http
POST http://localhost:8001/quiz/generate-for-course
Authorization: Bearer <instructor-token>
Content-Type: application/json

{
  "course_id": "course-123",
  "question_count": 15,
  "difficulty": "intermediate"
}
```

Response:
```json
{
  "quiz": {
    "id": "quiz-789",
    "title": "Python Basics Quiz",
    "questions": [
      {
        "question": "What is a variable in Python?",
        "options": ["A storage location", "A function", "A loop", "A condition"],
        "correct_answer": "A storage location",
        "type": "multiple_choice"
      }
    ]
  }
}
```

### Get Course Exercises

Retrieve exercises for a specific course.

```http
GET http://localhost:8001/exercises/{course_id}
Authorization: Bearer <token>
```

### Get Course Quizzes

Retrieve quizzes for a specific course.

```http
GET http://localhost:8001/quiz/course/{course_id}
Authorization: Bearer <token>
```

## Course Management Service (Port 8004)

### List Courses

Get a list of all courses.

```http
GET http://localhost:8004/courses
Authorization: Bearer <token>
```

Response:
```json
{
  "courses": [
    {
      "id": "course-123",
      "title": "Introduction to Python",
      "description": "Learn Python programming from scratch",
      "category": "programming",
      "difficulty_level": "beginner",
      "estimated_duration": 40,
      "instructor_id": "instructor-456",
      "created_at": "2025-07-16T10:30:00Z",
      "updated_at": "2025-07-16T10:30:00Z"
    }
  ]
}
```

### Get Course

Get detailed information about a specific course.

```http
GET http://localhost:8004/courses/{course_id}
Authorization: Bearer <token>
```

Response:
```json
{
  "id": "course-123",
  "title": "Introduction to Python",
  "description": "Learn Python programming from scratch",
  "category": "programming",
  "difficulty_level": "beginner",
  "estimated_duration": 40,
  "instructor_id": "instructor-456",
  "created_at": "2025-07-16T10:30:00Z",
  "updated_at": "2025-07-16T10:30:00Z"
}
```

### Create Course

Create a new course (instructor only).

```http
POST http://localhost:8004/courses
Authorization: Bearer <instructor-token>
Content-Type: application/json

{
  "title": "Advanced JavaScript",
  "description": "Master advanced JavaScript concepts",
  "category": "programming",
  "difficulty_level": "intermediate",
  "estimated_duration": 60
}
```

### Update Course

Update an existing course.

```http
PUT http://localhost:8004/courses/{course_id}
Authorization: Bearer <instructor-token>
Content-Type: application/json

{
  "title": "Updated Course Title",
  "description": "Updated description",
  "estimated_duration": 50
}
```

### Delete Course

Delete a course (instructor or admin only).

```http
DELETE http://localhost:8004/courses/{course_id}
Authorization: Bearer <token>
```

## Content Storage Service (Port 8003)

### Upload File

Upload files for content storage.

```http
POST http://localhost:8003/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <file-data>
```

Response:
```json
{
  "file_id": "file-123",
  "filename": "document.pdf",
  "size": 1024768,
  "content_type": "application/pdf",
  "upload_timestamp": "2025-07-16T10:30:00Z",
  "url": "/files/file-123"
}
```

### Download File

Download or retrieve an uploaded file.

```http
GET http://localhost:8003/download/{file_id}
Authorization: Bearer <token>
```

### Delete File

Delete a file from storage.

```http
DELETE http://localhost:8003/files/{file_id}
Authorization: Bearer <token>
```

## Content Management Service (Port 8005)

### Upload Content

Upload and process content files with AI integration.

```http
POST http://localhost:8005/upload
Authorization: Bearer <instructor-token>
Content-Type: multipart/form-data

file: <file-data>
course_id: course-123
```

Response:
```json
{
  "file_id": "file-456",
  "filename": "course_material.pdf",
  "processed": true,
  "extracted_content": {
    "text": "Course content extracted from PDF...",
    "structure": {
      "chapters": ["Introduction", "Advanced Topics"],
      "topics": ["Variables", "Functions", "Classes"]
    }
  }
}
```

### Export Content

Export course content in multiple formats.

```http
GET http://localhost:8005/export/{format}?course_id=course-123
Authorization: Bearer <instructor-token>
```

Supported formats:
- `powerpoint` - Export as PowerPoint presentation
- `pdf` - Export as PDF document
- `json` - Export as JSON data
- `excel` - Export as Excel spreadsheet
- `zip` - Export as ZIP archive
- `scorm` - Export as SCORM package

### List Files

List all uploaded files for a course.

```http
GET http://localhost:8005/files?course_id=course-123
Authorization: Bearer <token>
```

Response:
```json
{
  "files": [
    {
      "id": "file-123",
      "filename": "lecture_notes.pdf",
      "size": 2048576,
      "upload_date": "2025-07-16T10:30:00Z",
      "processed": true
    }
  ]
}
```

## Lab Container Manager Service (Port 8006)

### Create Lab Container

Create a new lab container with custom configuration.

```http
POST http://localhost:8006/labs
Authorization: Bearer <instructor-token>
Content-Type: application/json

{
  "user_id": "student-123",
  "course_id": "course-456",
  "lab_type": "python",
  "lab_config": {
    "packages": ["numpy", "pandas", "matplotlib"],
    "starter_files": {
      "main.py": "print('Hello, World!')",
      "README.md": "# Lab Instructions\n\nComplete the exercises below."
    }
  },
  "timeout_minutes": 120,
  "instructor_mode": false
}
```

Response:
```json
{
  "lab_id": "lab-student-123-course-456-1234567890",
  "user_id": "student-123",
  "course_id": "course-456",
  "status": "building",
  "created_at": "2025-07-26T10:30:00Z",
  "expires_at": "2025-07-26T12:30:00Z",
  "last_accessed": "2025-07-26T10:30:00Z",
  "instructor_mode": false,
  "storage_path": "/tmp/lab-storage/student-123/course-456",
  "lab_type": "python",
  "container_id": null,
  "port": null,
  "access_url": null
}
```

### Get or Create Student Lab

Get existing lab or create new one for a student.

```http
POST http://localhost:8006/labs/student
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": "student-123",
  "course_id": "course-456"
}
```

Response:
```json
{
  "lab_id": "lab-student-123-course-456-1234567890",
  "user_id": "student-123",
  "course_id": "course-456",
  "status": "running",
  "access_url": "http://localhost:9001",
  "created_at": "2025-07-26T10:30:00Z",
  "expires_at": "2025-07-26T12:30:00Z",
  "last_accessed": "2025-07-26T10:30:00Z",
  "instructor_mode": false,
  "storage_path": "/tmp/lab-storage/student-123/course-456",
  "lab_type": "python",
  "container_id": "container-abc123",
  "port": 9001
}
```

### List All Lab Containers

Get a list of all active lab containers.

```http
GET http://localhost:8006/labs
Authorization: Bearer <token>
```

Optional query parameters:
- `course_id` - Filter by course ID
- `user_id` - Filter by user ID
- `status` - Filter by status (building, running, paused, error)

Response:
```json
{
  "labs": [
    {
      "lab_id": "lab-student-123-course-456-1234567890",
      "user_id": "student-123",
      "course_id": "course-456",
      "status": "running",
      "access_url": "http://localhost:9001",
      "last_accessed": "2025-07-26T10:30:00Z",
      "instructor_mode": false,
      "lab_type": "python"
    }
  ],
  "active_count": 1,
  "max_concurrent": 50
}
```

### Get Lab Details

Get detailed information about a specific lab container.

```http
GET http://localhost:8006/labs/{lab_id}
Authorization: Bearer <token>
```

Response:
```json
{
  "lab_id": "lab-student-123-course-456-1234567890",
  "user_id": "student-123",
  "course_id": "course-456",
  "status": "running",
  "created_at": "2025-07-26T10:30:00Z",
  "expires_at": "2025-07-26T12:30:00Z",
  "last_accessed": "2025-07-26T10:30:00Z",
  "instructor_mode": false,
  "storage_path": "/tmp/lab-storage/student-123/course-456",
  "lab_type": "python",
  "container_id": "container-abc123",
  "port": 9001,
  "access_url": "http://localhost:9001"
}
```

### Pause Lab Container

Pause a running lab container to save resources.

```http
POST http://localhost:8006/labs/{lab_id}/pause
Authorization: Bearer <token>
```

Response:
```json
{
  "message": "Lab paused successfully",
  "lab_id": "lab-student-123-course-456-1234567890",
  "status": "paused"
}
```

### Resume Lab Container

Resume a paused lab container.

```http
POST http://localhost:8006/labs/{lab_id}/resume
Authorization: Bearer <token>
```

Response:
```json
{
  "message": "Lab resumed successfully",
  "lab_id": "lab-student-123-course-456-1234567890",
  "status": "running",
  "access_url": "http://localhost:9001"
}
```

### Stop and Remove Lab Container

Stop and completely remove a lab container.

```http
DELETE http://localhost:8006/labs/{lab_id}
Authorization: Bearer <token>
```

Response:
```json
{
  "message": "Lab stopped successfully",
  "lab_id": "lab-student-123-course-456-1234567890"
}
```

### Instructor Lab Overview

Get overview of all student labs for a course (instructor only).

```http
GET http://localhost:8006/labs/instructor/{course_id}
Authorization: Bearer <instructor-token>
```

Response:
```json
{
  "course_id": "course-456",
  "students": [
    {
      "user_id": "student-123",
      "username": "student1@example.com",
      "lab_status": "running",
      "last_accessed": "2025-07-26T10:30:00Z",
      "lab_id": "lab-student-123-course-456-1234567890"
    },
    {
      "user_id": "student-124",
      "username": "student2@example.com",
      "lab_status": "paused",
      "last_accessed": "2025-07-26T09:15:00Z",
      "lab_id": "lab-student-124-course-456-9876543210"
    }
  ],
  "total_students": 2,
  "active_labs": 1,
  "paused_labs": 1
}
```

### Lab Container Health Check

Check the health of the lab container service.

```http
GET http://localhost:8006/health
```

Response:
```json
{
  "status": "healthy",
  "service": "lab-container-manager",
  "version": "2.0.0",
  "timestamp": "2025-07-26T10:30:00Z",
  "docker_status": "connected",
  "system_resources": {
    "cpu_percent": 25.5,
    "memory_percent": 60.2,
    "disk_percent": 45.8
  },
  "active_containers": 5,
  "max_concurrent": 50
}
```

## Organization Management Service (Port 8008) - Enhanced RBAC System

The Organization Management Service provides comprehensive multi-tenant organization management with granular permissions, JWT authentication, Teams/Zoom integration, and audit logging.

### Authentication & Authorization

All RBAC endpoints require JWT authentication with appropriate role-based permissions:

```http
Authorization: Bearer <your-jwt-token>
```

**Role Hierarchy:**
- **Site Admin**: Full platform access, can manage all organizations
- **Organization Admin**: Manage specific organization, members, tracks, meeting rooms
- **Instructor**: Access assigned projects, create content, manage students
- **Student**: Access enrolled tracks, participate in courses

### Organization Management

#### List Organizations

Get organizations accessible to the authenticated user.

```http
GET http://localhost:8008/api/v1/rbac/organizations
Authorization: Bearer <token>
```

Response:
```json
{
  "organizations": [
    {
      "id": "org-123",
      "name": "University of Technology",
      "slug": "uni-tech",
      "description": "Leading technology education institution",
      "is_active": true,
      "member_count": 150,
      "project_count": 25,
      "track_count": 12,
      "meeting_room_count": 8,
      "created_at": "2025-07-01T10:00:00Z",
      "updated_at": "2025-07-31T15:30:00Z"
    }
  ]
}
```

#### Create Organization with Admin Account (v3.0)

Create a new organization with automatic administrator account creation. This endpoint allows professional organizations to register with complete admin user setup.

```http
POST http://localhost:8008/api/v1/organizations
Content-Type: application/json

{
  "name": "Tech Training Institute",
  "slug": "tech-training",
  "address": "123 Innovation Drive, Silicon Valley, CA 94043",
  "contact_phone": "+14155551234",
  "contact_email": "contact@techtraining.com",
  "description": "Professional technology training and certification",
  "domain": "https://techtraining.com",
  "logo_url": "https://techtraining.com/logo.png",
  "admin_full_name": "Sarah Johnson",
  "admin_email": "sarah.johnson@techtraining.com",
  "admin_phone": "+14155551235",
  "admin_role": "organization_admin",
  "admin_roles": ["organization_admin", "instructor"],
  "admin_password": "SecureAdminPassword123!"
}
```

**Request Parameters:**
- `name` (string, required): Official organization name
- `slug` (string, required): URL-friendly identifier (lowercase, hyphens only)
- `address` (string, required): Complete physical address (min 10 chars)
- `contact_phone` (string, required): Professional contact phone number
- `contact_email` (string, required): Professional email (no personal providers like Gmail)
- `admin_full_name` (string, required): Full name of organization administrator
- `admin_email` (string, required): Administrator email (professional domain required)
- `admin_password` (string, required): Administrator password (min 8 chars)
- `admin_role` (string, required): Primary role (`organization_admin`, `instructor`, or `student`)
- `description` (string, optional): Organization description
- `domain` (string, optional): Organization website domain
- `logo_url` (string, optional): URL to organization logo
- `admin_phone` (string, optional): Administrator phone number
- `admin_roles` (array, optional): All roles assigned to the administrator

**Success Response:**
```json
{
  "id": "org-789",
  "name": "Tech Training Institute",
  "slug": "tech-training",
  "description": "Professional technology training and certification",
  "address": "123 Innovation Drive, Silicon Valley, CA 94043",
  "contact_phone": "+14155551234",
  "contact_email": "contact@techtraining.com",
  "logo_url": "https://techtraining.com/logo.png",
  "domain": "https://techtraining.com",
  "is_active": true,
  "member_count": 1,
  "project_count": 0,
  "created_at": "2025-08-11T16:00:00Z",
  "updated_at": "2025-08-11T16:00:00Z"
}
```

**Error Responses:**
```json
// Professional email validation error
{
  "detail": "Invalid organization data: Personal email provider gmail.com not allowed. Please use a professional business email address."
}

// Password validation error  
{
  "detail": "Invalid organization data: Password must be at least 8 characters long"
}

// Duplicate organization
{
  "detail": "Organization with slug 'tech-training' already exists"
}
```

#### Create Organization with Logo Upload (v3.0)

Create an organization with logo file upload (multipart form data).

```http
POST http://localhost:8008/api/v1/organizations/upload
Content-Type: multipart/form-data

name=Tech Training Institute
slug=tech-training
address=123 Innovation Drive, Silicon Valley, CA 94043
contact_phone=+14155551234
contact_email=contact@techtraining.com
description=Professional technology training
domain=techtraining.com
admin_full_name=Sarah Johnson
admin_email=sarah.johnson@techtraining.com
admin_phone=+14155551235
admin_role=organization_admin
admin_password=SecureAdminPassword123!
logo=@/path/to/logo.png
```

**File Requirements:**
- Logo file: JPG, PNG, or GIF format
- Maximum size: 5MB
- Recommended dimensions: 200x200px or larger

#### Create Organization (RBAC - Site Admin Only)

Create a new organization via RBAC system (Site Admin only).

```http
POST http://localhost:8008/api/v1/rbac/organizations
Authorization: Bearer <site-admin-token>
Content-Type: application/json

{
  "name": "New Educational Institute",
  "slug": "new-edu-institute", 
  "description": "Innovative education platform",
  "settings": {
    "max_members": 500,
    "allow_self_registration": false,
    "require_email_verification": true,
    "enable_teams_integration": true,
    "enable_zoom_integration": false
  }
}
```

Response:
```json
{
  "id": "org-456",
  "name": "New Educational Institute",
  "slug": "new-edu-institute",
  "description": "Innovative education platform", 
  "is_active": true,
  "settings": {
    "max_members": 500,
    "allow_self_registration": false,
    "require_email_verification": true,
    "enable_teams_integration": true,
    "enable_zoom_integration": false
  },
  "created_at": "2025-07-31T16:00:00Z",
  "updated_at": "2025-07-31T16:00:00Z"
}
```

#### Get Organization Details

Get detailed information about a specific organization.

```http
GET http://localhost:8008/api/v1/rbac/organizations/{org_id}
Authorization: Bearer <token>
```

Response:
```json
{
  "id": "org-123",
  "name": "University of Technology",
  "slug": "uni-tech",
  "description": "Leading technology education institution",
  "is_active": true,
  "settings": {
    "max_members": 500,
    "allow_self_registration": false,
    "require_email_verification": true,
    "enable_teams_integration": true,
    "enable_zoom_integration": true
  },
  "statistics": {
    "total_members": 150,
    "member_breakdown": {
      "organization_admin": 3,
      "instructor": 25,
      "student": 122
    },
    "total_projects": 25,
    "total_tracks": 12,
    "total_meeting_rooms": 8,
    "active_meeting_rooms": 6
  },
  "created_at": "2025-07-01T10:00:00Z",
  "updated_at": "2025-07-31T15:30:00Z"
}
```

#### Update Organization

Update organization details.

```http
PUT http://localhost:8008/api/v1/rbac/organizations/{org_id}
Authorization: Bearer <org-admin-token>
Content-Type: application/json

{
  "name": "Updated University Name",
  "description": "Updated description",
  "settings": {
    "max_members": 750,
    "enable_zoom_integration": true
  }
}
```

#### Delete Organization

Delete an organization with full cleanup (Site Admin only).

```http
DELETE http://localhost:8008/api/v1/rbac/organizations/{org_id}
Authorization: Bearer <site-admin-token>
```

Response:
```json
{
  "success": true,
  "organization_name": "University of Technology",
  "deleted_members": 150,
  "deleted_projects": 25,
  "deleted_tracks": 12,
  "deleted_meeting_rooms": 8,
  "cleanup_summary": {
    "users_processed": 150,
    "data_archived": true,
    "notification_sent": true
  }
}
```

### Organization Member Management

#### List Organization Members

Get all members of an organization with filtering options.

```http
GET http://localhost:8008/api/v1/rbac/organizations/{org_id}/members?role_type=instructor&status=active
Authorization: Bearer <org-admin-token>
```

Query Parameters:
- `role_type` - Filter by role (organization_admin, instructor, student)
- `status` - Filter by status (active, inactive, suspended)
- `page` - Page number for pagination
- `limit` - Results per page (default: 50)

Response:
```json
{
  "members": [
    {
      "membership_id": "member-789",
      "user_id": "user-123",
      "name": "Dr. Sarah Johnson",
      "email": "sarah.johnson@uni-tech.edu",
      "role_type": "instructor",
      "status": "active",
      "permissions": [
        "create_courses",
        "manage_students",
        "access_analytics",
        "create_meeting_rooms"
      ],
      "project_access": ["project-101", "project-102"],
      "track_enrollments": [],
      "last_login": "2025-07-31T14:30:00Z",
      "joined_at": "2025-07-15T09:00:00Z",
      "invited_by": "admin-456"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 3,
    "total_members": 150,
    "members_per_page": 50
  }
}
```

#### Add Organization Member

Add a new member to the organization.

```http
POST http://localhost:8008/api/v1/rbac/organizations/{org_id}/members
Authorization: Bearer <org-admin-token>
Content-Type: application/json

{
  "user_email": "new.instructor@uni-tech.edu",
  "role_type": "instructor",
  "project_ids": ["project-101", "project-103"],
  "send_invitation_email": true,
  "custom_message": "Welcome to our Python programming team!"
}
```

Response:
```json
{
  "membership_id": "member-890",
  "user_id": "user-456",
  "user_email": "new.instructor@uni-tech.edu",
  "role_type": "instructor",
  "status": "active",
  "permissions": [
    "create_courses",
    "manage_students",
    "access_analytics",
    "create_meeting_rooms"
  ],
  "project_access": ["project-101", "project-103"],
  "invitation_sent": true,
  "created_at": "2025-07-31T16:15:00Z"
}
```

#### Update Member Role

Update a member's role and permissions.

```http
PUT http://localhost:8008/api/v1/rbac/organizations/{org_id}/members/{member_id}
Authorization: Bearer <org-admin-token>
Content-Type: application/json

{
  "role_type": "organization_admin",
  "project_ids": ["project-101", "project-102", "project-103"],
  "status": "active",
  "send_notification_email": true
}
```

Response:
```json
{
  "membership_id": "member-890",
  "user_id": "user-456",
  "role_type": "organization_admin",
  "status": "active",
  "permissions": [
    "manage_organization",
    "manage_members",
    "create_tracks",
    "manage_meeting_rooms",
    "view_analytics",
    "assign_projects"
  ],
  "project_access": ["project-101", "project-102", "project-103"],
  "updated_at": "2025-07-31T16:20:00Z"
}
```

#### Remove Organization Member

Remove a member from the organization.

```http
DELETE http://localhost:8008/api/v1/rbac/organizations/{org_id}/members/{member_id}
Authorization: Bearer <org-admin-token>
```

Response:
```json
{
  "success": true,
  "removed_member_id": "member-890",
  "user_email": "former.member@uni-tech.edu",
  "cleanup_actions": [
    "removed_project_access",
    "cancelled_track_enrollments",
    "archived_meeting_rooms",
    "sent_departure_notification"
  ]
}
```

### Learning Track Management

#### List Organization Tracks

Get all learning tracks for an organization.

```http
GET http://localhost:8008/api/v1/organizations/{org_id}/tracks?status=active&difficulty_level=intermediate
Authorization: Bearer <token>
```

Query Parameters:
- `status` - Filter by status (active, inactive, draft)
- `difficulty_level` - Filter by difficulty (beginner, intermediate, advanced)
- `auto_enrollment` - Filter by auto-enrollment setting (true, false)

Response:
```json
{
  "tracks": [
    {
      "id": "track-123",
      "name": "Full Stack Web Development",
      "description": "Comprehensive web development track covering frontend and backend",
      "organization_id": "org-123",
      "project_id": "project-101",
      "difficulty_level": "intermediate",
      "duration_weeks": 16,
      "target_audience": ["developers", "students", "career-changers"],
      "prerequisites": ["basic_programming", "html_css_basics"],
      "learning_objectives": [
        "Master React and Node.js development",
        "Build complete web applications",
        "Understand database design and integration",
        "Deploy applications to cloud platforms"
      ],
      "status": "active",
      "auto_enrollment": true,
      "enrollment_count": 45,
      "completion_rate": 78.5,
      "created_by": "instructor-789",
      "created_at": "2025-06-01T10:00:00Z",
      "updated_at": "2025-07-30T14:20:00Z"
    }
  ]
}
```

#### Create Learning Track

Create a new learning track with automatic enrollment capabilities.

```http
POST http://localhost:8008/api/v1/organizations/{org_id}/tracks
Authorization: Bearer <org-admin-token>
Content-Type: application/json

{
  "name": "Machine Learning Fundamentals",
  "description": "Introduction to machine learning concepts and applications",
  "project_id": "project-105",
  "difficulty_level": "intermediate",
  "duration_weeks": 12,
  "target_audience": ["data_scientists", "engineers", "researchers"],
  "prerequisites": ["python_programming", "statistics_basics"],
  "learning_objectives": [
    "Understand core ML algorithms",
    "Implement ML models using Python",
    "Evaluate model performance",
    "Deploy ML solutions"
  ],
  "auto_enrollment": true,
  "enrollment_criteria": {
    "min_experience_months": 6,
    "required_skills": ["python", "mathematics"],
    "exclude_roles": ["student"]
  }
}
```

Response:
```json
{
  "id": "track-456",
  "name": "Machine Learning Fundamentals",
  "description": "Introduction to machine learning concepts and applications",
  "organization_id": "org-123",
  "project_id": "project-105",
  "difficulty_level": "intermediate",
  "duration_weeks": 12,
  "target_audience": ["data_scientists", "engineers", "researchers"],
  "prerequisites": ["python_programming", "statistics_basics"],
  "learning_objectives": [
    "Understand core ML algorithms",
    "Implement ML models using Python",
    "Evaluate model performance",
    "Deploy ML solutions"
  ],
  "status": "active",
  "auto_enrollment": true,
  "enrollment_criteria": {
    "min_experience_months": 6,
    "required_skills": ["python", "mathematics"],
    "exclude_roles": ["student"]
  },
  "created_by": "admin-456",
  "created_at": "2025-07-31T16:30:00Z",
  "updated_at": "2025-07-31T16:30:00Z"
}
```

#### Enroll Student in Track

Enroll a student in a specific learning track.

```http
POST http://localhost:8008/api/v1/tracks/{track_id}/enroll/{student_id}
Authorization: Bearer <instructor-token>
Content-Type: application/json

{
  "enrollment_type": "manual",
  "start_date": "2025-08-01T00:00:00Z",
  "send_notification": true,
  "custom_message": "Welcome to the Machine Learning track!"
}
```

Response:
```json
{
  "enrollment_id": "enrollment-789",
  "student_id": "student-123",
  "track_id": "track-456",
  "enrollment_type": "manual",
  "status": "enrolled",
  "start_date": "2025-08-01T00:00:00Z",
  "expected_completion": "2025-10-24T00:00:00Z",
  "progress_percentage": 0.0,
  "enrolled_by": "instructor-456",
  "enrolled_at": "2025-07-31T16:35:00Z"
}
```

### Meeting Room Management

The Enhanced RBAC System includes integrated meeting room management with Teams and Zoom support.

#### List Organization Meeting Rooms

Get all meeting rooms for an organization.

```http
GET http://localhost:8008/api/v1/rbac/organizations/{org_id}/meeting-rooms?platform=teams&room_type=track_room&status=active
Authorization: Bearer <org-admin-token>
```

Query Parameters:
- `platform` - Filter by platform (teams, zoom)
- `room_type` - Filter by type (organization_room, track_room, project_room)
- `status` - Filter by status (active, inactive, maintenance)

Response:
```json
{
  "meeting_rooms": [
    {
      "id": "room-123",
      "name": "Full Stack Development Track Room",
      "display_name": "Full Stack Dev - Main Room",
      "organization_id": "org-123",
      "platform": "teams",
      "room_type": "track_room",
      "track_id": "track-123",
      "project_id": null,
      "instructor_id": "instructor-789",
      "meeting_id": "19:meeting_abc123@thread.v2",
      "join_url": "https://teams.microsoft.com/l/meetup-join/19%3Ameeting_abc123%40thread.v2/...",
      "settings": {
        "auto_recording": true,
        "waiting_room": false,
        "mute_on_entry": false,
        "allow_screen_sharing": true,
        "max_participants": 50
      },
      "status": "active",
      "participant_count": 0,
      "last_used": "2025-07-30T15:45:00Z",
      "created_by": "admin-456",
      "created_at": "2025-06-15T09:30:00Z",
      "updated_at": "2025-07-30T16:00:00Z"
    }
  ]
}
```

#### Create Meeting Room

Create a new meeting room with Teams or Zoom integration.

```http
POST http://localhost:8008/api/v1/rbac/organizations/{org_id}/meeting-rooms
Authorization: Bearer <org-admin-token>
Content-Type: application/json

{
  "name": "Advanced Python Workshop Room",
  "display_name": "Advanced Python - Workshop Space",
  "platform": "zoom",
  "room_type": "project_room",
  "project_id": "project-102",
  "instructor_id": "instructor-456",
  "settings": {
    "auto_recording": true,
    "waiting_room": true,
    "mute_on_entry": true,
    "allow_screen_sharing": true,
    "max_participants": 25,
    "require_password": true
  }
}
```

Response:
```json
{
  "id": "room-456",
  "name": "Advanced Python Workshop Room",
  "display_name": "Advanced Python - Workshop Space",
  "organization_id": "org-123",
  "platform": "zoom",
  "room_type": "project_room",
  "project_id": "project-102",
  "instructor_id": "instructor-456",
  "meeting_id": "123456789",
  "join_url": "https://zoom.us/j/123456789?pwd=abcdef123456",
  "meeting_password": "SecurePass123",
  "settings": {
    "auto_recording": true,
    "waiting_room": true,
    "mute_on_entry": true,
    "allow_screen_sharing": true,
    "max_participants": 25,
    "require_password": true
  },
  "status": "active",
  "participant_count": 0,
  "created_by": "admin-456",
  "created_at": "2025-07-31T16:40:00Z",
  "updated_at": "2025-07-31T16:40:00Z"
}
```

#### Update Meeting Room

Update meeting room settings and configuration.

```http
PUT http://localhost:8008/api/v1/rbac/organizations/{org_id}/meeting-rooms/{room_id}
Authorization: Bearer <org-admin-token>
Content-Type: application/json

{
  "name": "Updated Workshop Room Name",
  "instructor_id": "instructor-789",
  "settings": {
    "max_participants": 30,
    "waiting_room": false
  },
  "status": "active"
}
```

### Site Administration

Site administrators have access to platform-wide management capabilities.

#### List All Organizations

Get comprehensive list of all organizations with statistics (Site Admin only).

```http
GET http://localhost:8008/api/v1/site-admin/organizations?include_inactive=true&sort_by=created_at&order=desc
Authorization: Bearer <site-admin-token>
```

Query Parameters:
- `include_inactive` - Include inactive organizations (default: false)
- `sort_by` - Sort field (name, created_at, member_count, project_count)
- `order` - Sort order (asc, desc)
- `page` - Page number for pagination
- `limit` - Results per page (default: 20)

Response:
```json
{
  "organizations": [
    {
      "id": "org-123",
      "name": "University of Technology",
      "slug": "uni-tech",
      "is_active": true,
      "total_members": 150,
      "member_breakdown": {
        "organization_admin": 3,
        "instructor": 25,
        "student": 122
      },
      "project_count": 25,
      "track_count": 12,
      "meeting_room_count": 8,
      "storage_usage_mb": 2048,
      "last_activity": "2025-07-31T15:30:00Z",
      "created_at": "2025-07-01T10:00:00Z"
    }
  ],
  "platform_statistics": {
    "total_organizations": 15,
    "total_users": 2500,
    "total_projects": 180,
    "total_tracks": 75,
    "total_meeting_rooms": 120
  },
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_organizations": 15
  }
}
```

#### List All Platform Users

Get comprehensive list of all platform users (Site Admin only).

```http
GET http://localhost:8008/api/v1/site-admin/users?role=instructor&status=active&organization_id=org-123
Authorization: Bearer <site-admin-token>
```

Query Parameters:
- `role` - Filter by role (site_admin, organization_admin, instructor, student)
- `status` - Filter by status (active, inactive, suspended)
- `organization_id` - Filter by organization
- `search` - Search by name or email
- `last_login_days` - Filter by recent login activity

Response:
```json
{
  "users": [
    {
      "id": "user-123",
      "username": "sarah.johnson@uni-tech.edu",
      "full_name": "Dr. Sarah Johnson",
      "email": "sarah.johnson@uni-tech.edu",
      "role": "instructor",
      "is_site_admin": false,
      "is_active": true,
      "organization_id": "org-123",
      "organization_name": "University of Technology",
      "permissions": [
        "create_courses",
        "manage_students",
        "access_analytics"
      ],
      "last_login": "2025-07-31T14:30:00Z",
      "created_at": "2025-07-15T09:00:00Z",
      "profile_completion": 95.5
    }
  ],
  "user_statistics": {
    "total_users": 2500,
    "active_users": 2180,
    "role_breakdown": {
      "site_admin": 2,
      "organization_admin": 45,
      "instructor": 380,
      "student": 2073
    },
    "recent_signups": 25
  }
}
```

#### View Platform Audit Log

Access comprehensive audit log for security and compliance (Site Admin only).

```http
GET http://localhost:8008/api/v1/site-admin/audit-log?action_type=organization_created&date_from=2025-07-01&severity=high
Authorization: Bearer <site-admin-token>
```

Query Parameters:
- `action_type` - Filter by action (organization_created, member_added, role_changed, etc.)
- `user_id` - Filter by user who performed action
- `organization_id` - Filter by affected organization
- `date_from` / `date_to` - Date range filter
- `severity` - Filter by severity (low, medium, high, critical)

Response:
```json
{
  "audit_entries": [
    {
      "id": "audit-123",
      "timestamp": "2025-07-31T16:45:00Z",
      "action_type": "organization_created",
      "severity": "medium",
      "user_id": "admin-456",
      "user_email": "admin@platform.com",
      "organization_id": "org-456",
      "target_resource": "organization",
      "target_id": "org-456",
      "action_details": {
        "organization_name": "New Educational Institute",
        "organization_slug": "new-edu-institute",
        "initial_admin": "admin@newedu.com"
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
      "success": true,
      "error_message": null
    }
  ],
  "audit_summary": {
    "total_entries": 15420,
    "filtered_entries": 25,
    "severity_breakdown": {
      "critical": 2,
      "high": 8,
      "medium": 12,
      "low": 3
    }
  }
}
```

### Permission Management

#### Get User Permissions

Get comprehensive permissions for a specific user.

```http
GET http://localhost:8008/api/v1/rbac/permissions/{user_id}?organization_id=org-123
Authorization: Bearer <token>
```

Response:
```json
{
  "user_id": "user-123",
  "organization_id": "org-123",
  "role": "instructor",
  "permissions": {
    "organization_permissions": [
      "create_courses",
      "manage_students",
      "access_analytics",
      "create_meeting_rooms"
    ],
    "project_permissions": {
      "project-101": ["full_access", "manage_content"],
      "project-102": ["read_only", "comment"]
    },
    "track_permissions": {
      "track-123": ["instructor_access", "grade_students"]
    },
    "system_permissions": [
      "access_lab_containers",
      "view_reports"
    ]
  },
  "permission_context": {
    "organization_role": "instructor",
    "project_count": 2,
    "track_count": 1,
    "effective_since": "2025-07-15T09:00:00Z"
  }
}
```

#### Check Specific Permission

Verify if a user has a specific permission.

```http
POST http://localhost:8008/api/v1/rbac/permissions/check
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": "user-123",
  "organization_id": "org-123",
  "permission": "manage_meeting_rooms",
  "resource_id": "room-456",
  "context": {
    "action": "update_settings",
    "resource_type": "meeting_room"
  }
}
```

Response:
```json
{
  "user_id": "user-123",
  "permission": "manage_meeting_rooms",
  "granted": true,
  "reason": "User has instructor role with meeting room management permissions",
  "context": {
    "organization_id": "org-123",
    "user_role": "instructor",
    "resource_access": "granted"
  },
  "expires_at": null,
  "checked_at": "2025-07-31T16:50:00Z"
}
```

#### List Available Roles

Get all available roles and their permissions.

```http
GET http://localhost:8008/api/v1/rbac/roles?include_system_roles=true
Authorization: Bearer <token>
```

Response:
```json
{
  "roles": [
    {
      "role_name": "site_admin",
      "display_name": "Site Administrator",
      "description": "Full platform administration access",
      "is_system_role": true,
      "permissions": [
        "manage_platform",
        "delete_organizations",
        "manage_site_settings",
        "view_audit_logs",
        "manage_integrations"
      ],
      "restrictions": [],
      "max_users": 5
    },
    {
      "role_name": "organization_admin",
      "display_name": "Organization Administrator",
      "description": "Full organization management access",
      "is_system_role": false,
      "permissions": [
        "manage_organization",
        "manage_members",
        "create_tracks",
        "manage_meeting_rooms",
        "view_analytics",
        "assign_projects"
      ],
      "restrictions": [
        "organization_scope_only"
      ],
      "max_users": null
    },
    {
      "role_name": "instructor",
      "display_name": "Instructor",
      "description": "Course and student management access",
      "is_system_role": false,
      "permissions": [
        "create_courses",
        "manage_students",
        "access_analytics",
        "create_meeting_rooms"
      ],
      "restrictions": [
        "assigned_projects_only"
      ],
      "max_users": null
    },
    {
      "role_name": "student",
      "display_name": "Student",
      "description": "Learning and participation access",
      "is_system_role": false,
      "permissions": [
        "view_courses",
        "submit_assignments",
        "access_labs",
        "take_quizzes"
      ],
      "restrictions": [
        "enrolled_tracks_only"
      ],
      "max_users": null
    }
  ]
}
```

### RBAC Service Health Check

Check the health and status of the Organization Management Service.

```http
GET http://localhost:8008/health
```

Response:
```json
{
  "status": "healthy",
  "service": "organization-management",
  "version": "2.3.0",
  "timestamp": "2025-07-31T17:00:00Z",
  "database_status": "connected",
  "external_integrations": {
    "teams_api": "connected",
    "zoom_api": "connected",
    "email_service": "connected"
  },
  "system_resources": {
    "cpu_percent": 15.2,
    "memory_percent": 35.8,
    "active_connections": 45
  },
  "feature_flags": {
    "auto_enrollment": true,
    "meeting_room_management": true,
    "audit_logging": true,
    "email_notifications": true
  }
}
```

## Analytics Service (Port 8007)

### Track Student Activity

Track individual student activities like logins, lab access, quiz attempts, etc.

```http
POST http://localhost:8007/activities/track
Authorization: Bearer <token>
Content-Type: application/json

{
  "student_id": "student-123",
  "course_id": "course-456",
  "activity_type": "lab_access",
  "activity_data": {
    "lab_id": "lab-789",
    "session_duration": 45
  },
  "session_id": "session-abc123"
}
```

Response:
```json
{
  "message": "Activity tracked successfully",
  "activity_id": "activity-def456",
  "timestamp": "2025-07-26T10:30:00Z"
}
```

### Track Lab Usage

Track detailed lab session metrics including code executions, errors, and completion status.

```http
POST http://localhost:8007/lab-usage/track
Authorization: Bearer <token>
Content-Type: application/json

{
  "student_id": "student-123",
  "course_id": "course-456",
  "lab_id": "lab-789",
  "session_start": "2025-07-26T10:00:00Z",
  "session_end": "2025-07-26T10:45:00Z",
  "actions_performed": 25,
  "code_executions": 12,
  "errors_encountered": 3,
  "completion_status": "completed"
}
```

Response:
```json
{
  "message": "Lab usage tracked successfully",
  "metric_id": "metric-ghi789"
}
```

### Track Quiz Performance

Track quiz attempts and performance metrics.

```http
POST http://localhost:8007/quiz-performance/track
Authorization: Bearer <token>
Content-Type: application/json

{
  "student_id": "student-123",
  "course_id": "course-456",
  "quiz_id": "quiz-789",
  "start_time": "2025-07-26T11:00:00Z",
  "end_time": "2025-07-26T11:15:00Z",
  "questions_total": 10,
  "questions_answered": 10,
  "questions_correct": 8,
  "answers": {
    "q1": "option_a",
    "q2": "option_c"
  },
  "status": "completed"
}
```

Response:
```json
{
  "message": "Quiz performance tracked successfully",
  "performance_id": "perf-jkl012",
  "score_percentage": 80.0
}
```

### Update Student Progress

Update progress for specific content items.

```http
POST http://localhost:8007/progress/update
Authorization: Bearer <token>
Content-Type: application/json

{
  "student_id": "student-123",
  "course_id": "course-456",
  "content_item_id": "lesson-789",
  "content_type": "lesson",
  "status": "completed",
  "progress_percentage": 100.0,
  "time_spent_minutes": 30,
  "last_accessed": "2025-07-26T11:30:00Z",
  "completion_date": "2025-07-26T11:30:00Z",
  "mastery_score": 85.5
}
```

Response:
```json
{
  "message": "Progress updated successfully",
  "progress_id": "prog-mno345",
  "progress_percentage": 100.0
}
```

### Get Student Analytics

Get comprehensive analytics for a specific student.

```http
GET http://localhost:8007/analytics/student/student-123?course_id=course-456&days_back=30
Authorization: Bearer <token>
```

Response:
```json
{
  "student_id": "student-123",
  "course_id": "course-456",
  "analysis_period": {
    "start_date": "2025-06-26T11:30:00Z",
    "end_date": "2025-07-26T11:30:00Z",
    "days": 30
  },
  "activity_summary": {
    "total_activities": 45,
    "daily_activities": [
      {
        "date": "2025-07-26T00:00:00Z",
        "activity_type": "login",
        "count": 2
      }
    ]
  },
  "lab_metrics": {
    "average_session_duration": 35.5,
    "total_actions": 150,
    "total_sessions": 8,
    "average_code_executions": 12.3,
    "average_errors": 2.1
  },
  "quiz_performance": {
    "average_score": 82.5,
    "total_quizzes": 5,
    "average_duration": 12.5,
    "passed_quizzes": 4,
    "pass_rate": 80.0
  },
  "engagement_score": 78.5,
  "recommendations": [
    "Great job! Continue your excellent progress and engagement",
    "Focus on debugging skills to reduce coding errors"
  ]
}
```

### Get Course Analytics

Get comprehensive analytics for an entire course.

```http
GET http://localhost:8007/analytics/course/course-456?days_back=30
Authorization: Bearer <token>
```

Response:
```json
{
  "course_id": "course-456",
  "analysis_period": {
    "start_date": "2025-06-26T11:30:00Z",
    "end_date": "2025-07-26T11:30:00Z",
    "days": 30
  },
  "enrollment": {
    "total_students": 25,
    "active_students": 18
  },
  "lab_completion": {
    "completion_rates": [
      {
        "status": "completed",
        "count": 15,
        "average_duration": 42.3
      },
      {
        "status": "in_progress",
        "count": 8,
        "average_duration": 25.1
      }
    ]
  },
  "quiz_performance": {
    "average_score": 75.2,
    "score_standard_deviation": 12.8,
    "students_attempted": 20,
    "total_attempts": 45
  },
  "progress_distribution": [
    {
      "status": "completed",
      "count": 12,
      "average_progress": 100.0
    },
    {
      "status": "in_progress",
      "count": 13,
      "average_progress": 65.5
    }
  ]
}
```

### Analytics Service Health Check

Check the health of the analytics service.

```http
GET http://localhost:8007/health
```

Response:
```json
{
  "status": "healthy",
  "service": "analytics",
  "version": "2.0.0",
  "timestamp": "2025-07-26T10:30:00Z",
  "database_status": "connected"
}
```

## Interactive Documentation

### Swagger UI

Each service provides interactive API documentation:

- **User Management**: `http://localhost:8000/docs`
- **Course Generator**: `http://localhost:8001/docs`
- **Content Storage**: `http://localhost:8003/docs`
- **Course Management**: `http://localhost:8004/docs`
- **Content Management**: `http://localhost:8005/docs`
- **Lab Container Manager**: `http://localhost:8006/docs`
- **Analytics Service**: `http://localhost:8007/docs`
- **Organization Management (RBAC)**: `http://localhost:8008/docs`

### Example API Workflow

Here's a typical workflow for creating a complete course:

```bash
# 1. Login to get authentication token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "instructor@example.com", "password": "password"}'

# 2. Create a new course
curl -X POST http://localhost:8004/courses \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Python Basics", "description": "Learn Python programming"}'

# 3. Generate syllabus using AI
curl -X POST http://localhost:8001/generate/syllabus \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"course_title": "Python Basics", "target_audience": "beginner"}'

# 4. Generate exercises
curl -X POST http://localhost:8001/exercises/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"course_id": "course-123", "difficulty": "beginner"}'

# 5. Upload course materials
curl -X POST http://localhost:8005/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@course_material.pdf" \
  -F "course_id=course-123"

# 6. Export content in multiple formats
curl -X GET "http://localhost:8005/export/powerpoint?course_id=course-123" \
  -H "Authorization: Bearer <token>" \
  -o course_slides.pptx
```

## Error Handling

### Error Response Format

All services follow a consistent error format:

```json
{
  "detail": "Authentication required",
  "error_code": "AUTHENTICATION_REQUIRED",
  "timestamp": "2025-07-16T10:30:00Z"
}
```

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `204` - No Content
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

### Common Error Codes

- `VALIDATION_ERROR` - Input validation failed
- `AUTHENTICATION_REQUIRED` - No token provided
- `INVALID_TOKEN` - Token is invalid or expired
- `INSUFFICIENT_PERMISSIONS` - User lacks required permissions
- `RESOURCE_NOT_FOUND` - Requested resource doesn't exist
- `INTERNAL_ERROR` - Server error

## Service Health and Monitoring

### Health Check All Services

Use the app-control.sh script to check all services:

```bash
./app-control.sh status
```

### Service Dependencies

Services must be started in dependency order:
1. User Management (8000)
2. Organization Management - RBAC (8008)
3. Course Generator (8001)
4. Course Management (8004)
5. Content Storage (8003)
6. Content Management (8005)
7. Lab Container Manager (8006)
8. Analytics Service (8007)

### MCP Integration

The platform includes a unified MCP server for monitoring:

```bash
# Start MCP server
./mcp-control.sh start

# Check MCP status
./mcp-control.sh status
```

## Testing the API

### Using curl

```bash
# Test authentication
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test@example.com", "password": "password"}'

# Test course creation
curl -X POST http://localhost:8004/courses \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Course", "description": "Test description"}'
```

### Using the Frontend

Access the web interface at:
- **Instructor Dashboard**: `http://localhost:8080/instructor-dashboard.html`
- **Student Dashboard**: `http://localhost:8080/student-dashboard.html`
- **Lab Environment**: `http://localhost:8080/lab.html`

## Platform Status

**Current Version**: 2.3.0 - Enhanced RBAC System with Multi-Tenant Organization Management  
**Last Updated**: 2025-07-31  
**Status**: Production Ready with Enhanced RBAC System and Advanced Lab Container Management

### New in v2.3 - Enhanced RBAC System
- **Multi-Tenant Organization Management** - Comprehensive organization administration with granular permissions
- **JWT Authentication & Authorization** - Secure role-based access control with sophisticated permission management
- **Teams/Zoom Integration** - Automated meeting room creation and management for organizations and learning tracks
- **Comprehensive Audit Logging** - Complete audit trail for all RBAC operations with security monitoring
- **Automated Email Notifications** - Hydra-configured email service for member invitations and role assignments
- **Site Administration** - Platform-wide management with organization oversight and user administration
- **Learning Track Management** - Automatic enrollment capabilities with track-based learning paths
- **Project-Based Access Control** - Granular permissions for project-specific resource access
- **Complete Test Coverage** - 102 RBAC tests with 100% success rate and comprehensive code quality enforcement

### Previous v2.2 - Complete Quiz Management System
- **Course Instance-Specific Quiz Publishing** - Publish/unpublish quizzes per course instance with analytics integration
- **Student Access Control** - Enrollment-based quiz access with attempt limitations and progress tracking

### Previous v2.1 - Bi-Directional Feedback System & Multi-IDE Lab Containers
- **Complete Bi-Directional Feedback System** - Students rate courses, instructors assess students with analytics
- **Multi-IDE Lab Environments** - VSCode Server, JupyterLab, IntelliJ IDEA, and Terminal support with seamless switching

### Previous v2.0 - Individual Lab Container System
- **Individual Docker Lab Containers** - Per-student isolated environments
- **Dynamic Image Building** - Custom lab environments built on-demand
- **Automatic Lab Lifecycle Management** - Login/logout integration with persistence
- **Comprehensive Instructor Lab Controls** - Real-time monitoring and management
- **Full Docker Compose Orchestration** - Production-ready containerized deployment

For detailed implementation information, see [CLAUDE.md](../CLAUDE.md) and [Architecture Documentation](./architecture.md).