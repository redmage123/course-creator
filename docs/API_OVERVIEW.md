# API Overview

This document provides a comprehensive overview of the Course Creator Platform APIs, including service endpoints, authentication flow, request/response formats, and error handling patterns.

## Table of Contents

- [API Design Principles](#api-design-principles)
- [Base URLs](#base-urls)
- [Authentication](#authentication)
- [Common Patterns](#common-patterns)
- [Service APIs](#service-apis)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [API Versioning](#api-versioning)
- [Testing APIs](#testing-apis)

## API Design Principles

The Course Creator Platform APIs follow **RESTful** design principles with these core concepts:

### 1. Resource-Oriented URLs
```
GET    /api/v1/courses          # Collection resource
GET    /api/v1/courses/123      # Individual resource
POST   /api/v1/courses          # Create resource
PUT    /api/v1/courses/123      # Update resource
DELETE /api/v1/courses/123      # Delete resource
```

### 2. HTTP Methods
- **GET** - Retrieve resources (idempotent, no side effects)
- **POST** - Create new resources
- **PUT** - Update entire resource (idempotent)
- **PATCH** - Partial update
- **DELETE** - Remove resource (idempotent)

### 3. Standard HTTP Status Codes
- **200 OK** - Request succeeded
- **201 Created** - Resource created
- **204 No Content** - Request succeeded, no response body
- **400 Bad Request** - Invalid request data
- **401 Unauthorized** - Missing or invalid authentication
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource doesn't exist
- **409 Conflict** - Resource conflict (e.g., duplicate)
- **422 Unprocessable Entity** - Validation error
- **500 Internal Server Error** - Server error

### 4. JSON Request/Response Format
All APIs use **JSON** for request and response bodies:
```json
{
  "id": 123,
  "title": "Introduction to Python",
  "created_at": "2025-11-27T10:30:00Z",
  "metadata": {
    "duration_hours": 40,
    "difficulty": "beginner"
  }
}
```

### 5. Pagination
Large collections use **cursor-based pagination**:
```
GET /api/v1/courses?limit=20&offset=0
```

Response includes pagination metadata:
```json
{
  "data": [...],
  "pagination": {
    "total": 150,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

## Base URLs

### Development Environment
```
User Management:       https://localhost:8000
Course Generator:      https://localhost:8001
NLP Preprocessing:     https://localhost:8002
Content Storage:       https://localhost:8003
Course Management:     https://localhost:8004
Content Management:    https://localhost:8005
Lab Manager:           https://localhost:8006
Analytics:             https://localhost:8007
Organization Mgmt:     https://localhost:8008
RAG Service:           https://localhost:8009
Frontend:              https://localhost:3000
```

### Production Environment
```
API Gateway:           https://api.coursecreator.com
Frontend:              https://app.coursecreator.com
```

**Note**: All APIs use **HTTPS only** - no HTTP endpoints in production.

## Authentication

### JWT Token-Based Authentication

The platform uses **JWT (JSON Web Tokens)** for stateless authentication.

#### 1. User Registration

**Endpoint**: `POST /auth/register`

**Request**:
```json
{
  "email": "john.doe@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "organization_id": 5
}
```

**Response** (201 Created):
```json
{
  "id": 123,
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "role": "student",
  "organization_id": 5,
  "created_at": "2025-11-27T10:30:00Z"
}
```

#### 2. User Login

**Endpoint**: `POST /auth/login`

**Request**:
```json
{
  "email": "john.doe@example.com",
  "password": "SecurePass123!"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": 123,
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "role": "student",
    "organization_id": 5
  }
}
```

#### 3. Using JWT Token

Include token in `Authorization` header for all authenticated requests:

```http
GET /api/v1/courses HTTP/1.1
Host: localhost:8004
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

**curl Example**:
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET "https://localhost:8004/api/v1/courses" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --insecure
```

#### 4. Token Refresh

**Endpoint**: `POST /auth/refresh`

**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

#### 5. Password Management

**Change Password** (requires authentication):

**Endpoint**: `POST /auth/password/change`

**Request**:
```json
{
  "old_password": "CurrentPass123!",
  "new_password": "NewSecurePass456!",
  "confirm_password": "NewSecurePass456!"
}
```

**Response** (200 OK):
```json
{
  "message": "Password changed successfully"
}
```

### JWT Token Structure

**Decoded JWT Payload**:
```json
{
  "sub": "123",                    // User ID
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "role": "instructor",
  "organization_id": 5,
  "exp": 1700000000,               // Expiration (Unix timestamp)
  "iat": 1699996400                // Issued at (Unix timestamp)
}
```

### Role-Based Access Control (RBAC)

**User Roles**:
- `site_admin` - Platform-wide administration
- `org_admin` - Organization management
- `instructor` - Course creation and management
- `student` - Course enrollment and learning

**Permission Checking**:
- Performed at API endpoint level
- Based on JWT token `role` claim
- Organization isolation enforced via `organization_id`

## Common Patterns

### Request Headers

**Required Headers**:
```http
Content-Type: application/json
Authorization: Bearer {token}
```

**Optional Headers**:
```http
Accept: application/json
X-Request-ID: uuid-for-tracing
```

### Response Format

**Success Response**:
```json
{
  "data": {
    "id": 123,
    "title": "Course Title"
  }
}
```

**Error Response**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid course data",
    "details": [
      {
        "field": "title",
        "message": "Title is required"
      }
    ]
  }
}
```

### Query Parameters

**Filtering**:
```
GET /api/v1/courses?organization_id=5&instructor_id=10
```

**Sorting**:
```
GET /api/v1/courses?sort_by=created_at&order=desc
```

**Pagination**:
```
GET /api/v1/courses?limit=20&offset=40
```

**Search**:
```
GET /api/v1/courses?search=python&fields=title,description
```

### Timestamps

All timestamps use **ISO 8601** format in **UTC**:
```json
{
  "created_at": "2025-11-27T10:30:00Z",
  "updated_at": "2025-11-27T15:45:30Z"
}
```

## Service APIs

### 1. User Management API (Port 8000)

#### Authentication Endpoints

**Register User**
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "role": "student",
  "organization_id": 5
}
```

**Login**
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Logout**
```http
POST /auth/logout
Authorization: Bearer {token}
```

**Get Current User**
```http
GET /auth/me
Authorization: Bearer {token}
```

**Change Password**
```http
POST /auth/password/change
Authorization: Bearer {token}
Content-Type: application/json

{
  "old_password": "CurrentPass123!",
  "new_password": "NewPass456!"
}
```

#### User Management Endpoints

**Get User by ID**
```http
GET /users/{user_id}
Authorization: Bearer {token}
```

**Update User**
```http
PUT /users/{user_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "full_name": "John Smith",
  "email": "john.smith@example.com"
}
```

**List Users** (Admin only)
```http
GET /users?organization_id=5&role=student&limit=50
Authorization: Bearer {token}
```

**Delete User** (Admin only)
```http
DELETE /users/{user_id}
Authorization: Bearer {token}
```

### 2. Course Management API (Port 8004)

#### Course Endpoints

**Create Course**
```http
POST /api/v1/courses
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Introduction to Python",
  "description": "Learn Python programming from scratch",
  "organization_id": 5,
  "instructor_id": 10,
  "duration_hours": 40,
  "difficulty": "beginner"
}
```

**Response** (201 Created):
```json
{
  "id": 123,
  "title": "Introduction to Python",
  "description": "Learn Python programming from scratch",
  "organization_id": 5,
  "instructor_id": 10,
  "duration_hours": 40,
  "difficulty": "beginner",
  "created_at": "2025-11-27T10:30:00Z",
  "is_published": false
}
```

**Get Course**
```http
GET /api/v1/courses/{course_id}
Authorization: Bearer {token}
```

**List Courses**
```http
GET /api/v1/courses?organization_id=5&instructor_id=10&limit=20&offset=0
Authorization: Bearer {token}
```

**Update Course**
```http
PUT /api/v1/courses/{course_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Advanced Python Programming",
  "description": "Updated description",
  "is_published": true
}
```

**Delete Course**
```http
DELETE /api/v1/courses/{course_id}
Authorization: Bearer {token}
```

#### Enrollment Endpoints

**Enroll Student**
```http
POST /api/v1/courses/{course_id}/enroll
Authorization: Bearer {token}
Content-Type: application/json

{
  "student_id": 45,
  "course_instance_id": 67
}
```

**Get Enrollments**
```http
GET /api/v1/courses/{course_id}/enrollments
Authorization: Bearer {token}
```

**Unenroll Student**
```http
DELETE /api/v1/enrollments/{enrollment_id}
Authorization: Bearer {token}
```

#### Course Version Endpoints

**Create Version**
```http
POST /api/v1/courses/{course_id}/versions
Authorization: Bearer {token}
Content-Type: application/json

{
  "version_number": "1.1",
  "notes": "Minor updates to content",
  "is_major": false
}
```

**List Versions**
```http
GET /api/v1/courses/{course_id}/versions
Authorization: Bearer {token}
```

**Compare Versions**
```http
GET /api/v1/courses/{course_id}/versions/compare?from=1.0&to=1.1
Authorization: Bearer {token}
```

#### Feedback Endpoints

**Submit Course Feedback** (Student → Course)
```http
POST /feedback/course
Authorization: Bearer {token}
Content-Type: application/json

{
  "course_id": 123,
  "student_id": 45,
  "overall_rating": 4,
  "instructor_rating": 5,
  "content_rating": 4,
  "difficulty_rating": 3,
  "comments": "Great course, very informative!",
  "is_anonymous": false
}
```

**Submit Student Assessment** (Instructor → Student)
```http
POST /feedback/student
Authorization: Bearer {token}
Content-Type: application/json

{
  "student_id": 45,
  "course_id": 123,
  "instructor_id": 10,
  "performance_rating": 4,
  "participation_rating": 5,
  "improvement_areas": "Time management",
  "strengths": "Strong problem-solving skills",
  "recommendations": "Practice more complex algorithms"
}
```

**Get Course Feedback**
```http
GET /feedback/course/{course_id}?include_anonymous=true
Authorization: Bearer {token}
```

**Get Student Feedback History**
```http
GET /feedback/student/{student_id}
Authorization: Bearer {token}
```

### 3. Course Generator API (Port 8001)

#### Content Generation Endpoints

**Generate Syllabus**
```http
POST /generate/syllabus
Authorization: Bearer {token}
Content-Type: application/json

{
  "topic": "Introduction to Machine Learning",
  "duration_hours": 40,
  "difficulty": "intermediate",
  "target_audience": "Software developers",
  "prerequisites": ["Python programming", "Statistics basics"]
}
```

**Response** (200 OK):
```json
{
  "syllabus": {
    "title": "Introduction to Machine Learning",
    "modules": [
      {
        "number": 1,
        "title": "Machine Learning Fundamentals",
        "topics": ["Supervised Learning", "Unsupervised Learning"],
        "duration_hours": 8
      }
    ],
    "total_duration_hours": 40,
    "learning_objectives": [...],
    "assessment_methods": [...]
  },
  "generation_id": "gen_abc123",
  "quality_score": 0.92
}
```

**Generate Slides**
```http
POST /generate/slides
Authorization: Bearer {token}
Content-Type: application/json

{
  "topic": "Python Lists and Tuples",
  "module_id": 5,
  "num_slides": 10,
  "include_examples": true,
  "include_exercises": true
}
```

**Generate Quiz**
```http
POST /generate/quiz
Authorization: Bearer {token}
Content-Type: application/json

{
  "topic": "Python Functions",
  "num_questions": 10,
  "question_types": ["multiple_choice", "code_completion"],
  "difficulty": "medium",
  "include_explanations": true
}
```

**Response** (200 OK):
```json
{
  "quiz": {
    "title": "Python Functions Quiz",
    "questions": [
      {
        "id": 1,
        "type": "multiple_choice",
        "question": "What is a function in Python?",
        "options": [
          "A reusable block of code",
          "A data type",
          "A loop structure",
          "A variable"
        ],
        "correct_answer": 0,
        "explanation": "A function is a reusable block of code that performs a specific task."
      }
    ],
    "total_points": 100,
    "passing_score": 70
  },
  "generation_id": "gen_xyz789"
}
```

**Generate Lab Exercise**
```http
POST /generate/lab
Authorization: Bearer {token}
Content-Type: application/json

{
  "topic": "Python File I/O",
  "difficulty": "intermediate",
  "estimated_time_minutes": 60,
  "include_test_cases": true
}
```

**Regenerate Content**
```http
POST /generate/regenerate
Authorization: Bearer {token}
Content-Type: application/json

{
  "generation_id": "gen_abc123",
  "feedback": "Make it more beginner-friendly",
  "regenerate_sections": ["introduction", "examples"]
}
```

**Get Generation History**
```http
GET /generate/history?course_id=123&type=slides&limit=20
Authorization: Bearer {token}
```

### 4. Lab Manager API (Port 8006)

#### Lab Container Endpoints

**Create Lab Container**
```http
POST /labs
Authorization: Bearer {token}
Content-Type: application/json

{
  "student_id": 45,
  "course_id": 123,
  "packages": ["numpy", "pandas", "matplotlib"],
  "preferred_ide": "vscode",
  "resource_limits": {
    "cpu": 1.5,
    "memory_mb": 2048
  }
}
```

**Response** (201 Created):
```json
{
  "lab_id": "lab_abc123",
  "container_id": "abcdef123456",
  "student_id": 45,
  "status": "running",
  "ides": {
    "terminal": "https://localhost:8080",
    "vscode": "https://localhost:8081",
    "jupyter": "https://localhost:8082"
  },
  "created_at": "2025-11-27T10:30:00Z"
}
```

**Get or Create Student Lab**
```http
POST /labs/student
Authorization: Bearer {token}
Content-Type: application/json

{
  "student_id": 45,
  "course_id": 123
}
```

**List All Labs**
```http
GET /labs?student_id=45&status=running&limit=20
Authorization: Bearer {token}
```

**Get Lab Details**
```http
GET /labs/{lab_id}
Authorization: Bearer {token}
```

**Pause Lab**
```http
POST /labs/{lab_id}/pause
Authorization: Bearer {token}
```

**Resume Lab**
```http
POST /labs/{lab_id}/resume
Authorization: Bearer {token}
```

**Stop and Remove Lab**
```http
DELETE /labs/{lab_id}
Authorization: Bearer {token}
```

#### Multi-IDE Management

**Get Available IDEs**
```http
GET /labs/{lab_id}/ides
Authorization: Bearer {token}
```

**Response** (200 OK):
```json
{
  "ides": [
    {
      "name": "terminal",
      "url": "https://localhost:8080",
      "status": "running",
      "port": 8080
    },
    {
      "name": "vscode",
      "url": "https://localhost:8081",
      "status": "running",
      "port": 8081
    },
    {
      "name": "jupyter",
      "url": "https://localhost:8082",
      "status": "running",
      "port": 8082
    }
  ]
}
```

**Switch IDE**
```http
POST /labs/{lab_id}/ide/switch
Authorization: Bearer {token}
Content-Type: application/json

{
  "ide": "jupyter"
}
```

**Get IDE Status**
```http
GET /labs/{lab_id}/ide/status
Authorization: Bearer {token}
```

### 5. Analytics API (Port 8007)

#### Analytics Endpoints

**Get Student Analytics**
```http
GET /api/v1/analytics/student/{student_id}?timeframe=30d
Authorization: Bearer {token}
```

**Response** (200 OK):
```json
{
  "student_id": 45,
  "overall_progress": 65.5,
  "courses_enrolled": 5,
  "courses_completed": 2,
  "total_time_spent_hours": 120,
  "average_quiz_score": 85.3,
  "engagement_score": 7.8,
  "recent_activity": [
    {
      "type": "quiz_completed",
      "course_id": 123,
      "score": 90,
      "timestamp": "2025-11-27T14:30:00Z"
    }
  ],
  "at_risk": false
}
```

**Get Course Analytics**
```http
GET /api/v1/analytics/course/{course_id}?include_students=true
Authorization: Bearer {token}
```

**Response** (200 OK):
```json
{
  "course_id": 123,
  "total_enrollments": 150,
  "active_students": 120,
  "completion_rate": 68.5,
  "average_progress": 72.3,
  "average_quiz_score": 78.5,
  "total_time_spent_hours": 4500,
  "engagement_metrics": {
    "video_watch_rate": 85.2,
    "quiz_attempt_rate": 92.1,
    "lab_completion_rate": 71.8
  },
  "student_performance": {
    "top_performers": 15,
    "average_performers": 100,
    "struggling_students": 35
  }
}
```

**Get Organization Analytics**
```http
GET /api/v1/analytics/organization/{org_id}?timeframe=90d
Authorization: Bearer {token}
```

**Get Instructor Analytics**
```http
GET /api/v1/analytics/instructor/{instructor_id}
Authorization: Bearer {token}
```

**Generate Report**
```http
POST /api/v1/analytics/report
Authorization: Bearer {token}
Content-Type: application/json

{
  "type": "student_progress",
  "student_id": 45,
  "format": "pdf",
  "include_charts": true,
  "timeframe": "90d"
}
```

**Response** (200 OK):
```json
{
  "report_id": "report_abc123",
  "download_url": "https://localhost:8007/reports/report_abc123.pdf",
  "expires_at": "2025-11-28T10:30:00Z"
}
```

#### Real-Time Analytics (WebSocket)

**Connect to Analytics WebSocket**
```javascript
const ws = new WebSocket('wss://localhost:8007/ws/analytics?token={jwt_token}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Analytics update:', data);
};

// Subscribe to specific analytics
ws.send(JSON.stringify({
  action: 'subscribe',
  resource: 'course',
  resource_id: 123
}));
```

**WebSocket Message Format**:
```json
{
  "type": "analytics_update",
  "resource": "course",
  "resource_id": 123,
  "data": {
    "active_students": 85,
    "average_progress": 73.2,
    "recent_completions": 3
  },
  "timestamp": "2025-11-27T15:30:00Z"
}
```

### 6. Organization Management API (Port 8008)

#### Organization Endpoints

**Create Organization**
```http
POST /api/v1/organizations
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Acme Corporation",
  "slug": "acme-corp",
  "address": "123 Business St, City, State 12345",
  "contact_email": "admin@acme.com",
  "contact_phone": "+15551234567",
  "admin_full_name": "Jane Admin",
  "admin_email": "jane.admin@acme.com",
  "admin_password": "SecureAdminPass123!"
}
```

**Response** (201 Created):
```json
{
  "organization": {
    "id": 5,
    "name": "Acme Corporation",
    "slug": "acme-corp",
    "address": "123 Business St, City, State 12345",
    "contact_email": "admin@acme.com",
    "contact_phone": "+15551234567",
    "created_at": "2025-11-27T10:30:00Z",
    "is_active": true
  },
  "admin_user": {
    "id": 100,
    "email": "jane.admin@acme.com",
    "full_name": "Jane Admin",
    "role": "org_admin",
    "organization_id": 5
  }
}
```

**Get Organization**
```http
GET /api/v1/organizations/{org_id}
Authorization: Bearer {token}
```

**List Organizations** (Site Admin only)
```http
GET /api/v1/organizations?limit=50&offset=0
Authorization: Bearer {token}
```

**Update Organization**
```http
PUT /api/v1/organizations/{org_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Acme Corporation Inc.",
  "contact_email": "contact@acme.com"
}
```

**Delete Organization**
```http
DELETE /api/v1/organizations/{org_id}
Authorization: Bearer {token}
```

#### Member Management Endpoints

**Add Member**
```http
POST /api/v1/organizations/{org_id}/members
Authorization: Bearer {token}
Content-Type: application/json

{
  "email": "member@acme.com",
  "full_name": "John Member",
  "role": "instructor",
  "send_invitation": true
}
```

**List Members**
```http
GET /api/v1/organizations/{org_id}/members?role=instructor&limit=50
Authorization: Bearer {token}
```

**Update Member Role**
```http
PUT /api/v1/organizations/{org_id}/members/{member_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "role": "org_admin"
}
```

**Remove Member**
```http
DELETE /api/v1/organizations/{org_id}/members/{member_id}
Authorization: Bearer {token}
```

#### Learning Track Endpoints

**Create Track**
```http
POST /api/v1/organizations/{org_id}/tracks
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Full Stack Developer Track",
  "description": "Complete path to becoming a full stack developer",
  "duration_weeks": 16,
  "target_roles": ["Software Developer", "Web Developer"]
}
```

**List Tracks**
```http
GET /api/v1/organizations/{org_id}/tracks
Authorization: Bearer {token}
```

**Update Track**
```http
PUT /api/v1/tracks/{track_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Updated Track Name",
  "duration_weeks": 20
}
```

**Delete Track**
```http
DELETE /api/v1/tracks/{track_id}
Authorization: Bearer {token}
```

**Enroll Student in Track**
```http
POST /api/v1/tracks/{track_id}/enroll
Authorization: Bearer {token}
Content-Type: application/json

{
  "student_id": 45,
  "start_date": "2025-12-01"
}
```

### 7. RAG Service API (Port 8009)

#### RAG Knowledge Base Endpoints

**Add Document to Knowledge Base**
```http
POST /api/v1/rag/add-document
Authorization: Bearer {token}
Content-Type: application/json

{
  "collection": "content_generation",
  "document_id": "syllabus_ml_intro",
  "content": "Machine learning is a subset of artificial intelligence...",
  "metadata": {
    "topic": "machine_learning",
    "difficulty": "intermediate",
    "quality_score": 0.92
  }
}
```

**Query Knowledge Base**
```http
POST /api/v1/rag/query
Authorization: Bearer {token}
Content-Type: application/json

{
  "collection": "content_generation",
  "query": "best practices for teaching machine learning",
  "top_k": 5,
  "filters": {
    "difficulty": "intermediate"
  }
}
```

**Response** (200 OK):
```json
{
  "results": [
    {
      "document_id": "syllabus_ml_intro",
      "content": "Machine learning teaching approaches...",
      "similarity_score": 0.89,
      "metadata": {
        "topic": "machine_learning",
        "difficulty": "intermediate"
      }
    }
  ],
  "query_time_ms": 45
}
```

**Learn from Interaction**
```http
POST /api/v1/rag/learn
Authorization: Bearer {token}
Content-Type: application/json

{
  "collection": "content_generation",
  "interaction_type": "syllabus_generation",
  "input": "Generate machine learning syllabus",
  "output": "Generated syllabus content...",
  "quality_score": 0.95,
  "user_feedback": "Excellent structure"
}
```

**Get RAG Statistics**
```http
GET /api/v1/rag/stats?collection=content_generation
Authorization: Bearer {token}
```

## Error Handling

### Standard Error Response Format

All error responses follow this structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": [...],  // Optional additional information
    "request_id": "uuid-for-tracing"
  }
}
```

### Common Error Codes

**Authentication Errors (401)**:
```json
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Authentication credentials were not provided"
  }
}
```

```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "JWT token is invalid or expired"
  }
}
```

**Authorization Errors (403)**:
```json
{
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "You do not have permission to perform this action",
    "details": {
      "required_roles": ["instructor", "org_admin"],
      "user_role": "student"
    }
  }
}
```

```json
{
  "error": {
    "code": "ORGANIZATION_MISMATCH",
    "message": "Resource belongs to a different organization"
  }
}
```

**Validation Errors (422)**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      },
      {
        "field": "password",
        "message": "Password must be at least 8 characters"
      }
    ]
  }
}
```

**Resource Not Found (404)**:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Course with ID 999 not found"
  }
}
```

**Conflict Errors (409)**:
```json
{
  "error": {
    "code": "RESOURCE_ALREADY_EXISTS",
    "message": "User with email user@example.com already exists"
  }
}
```

**Server Errors (500)**:
```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred",
    "request_id": "abc-123-def-456"
  }
}
```

### Error Handling in Client Code

**JavaScript Example**:
```javascript
async function fetchCourses() {
  try {
    const response = await fetch('https://localhost:8004/api/v1/courses', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const error = await response.json();

      if (error.error.code === 'AUTHENTICATION_REQUIRED') {
        // Redirect to login
        window.location.href = '/login';
      } else if (error.error.code === 'VALIDATION_ERROR') {
        // Display validation errors
        error.error.details.forEach(detail => {
          console.error(`${detail.field}: ${detail.message}`);
        });
      } else {
        // Generic error handling
        console.error('API Error:', error.error.message);
      }

      throw new Error(error.error.message);
    }

    return await response.json();
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}
```

**Python Example**:
```python
import httpx
from typing import Dict, Any

async def fetch_courses(token: str) -> Dict[str, Any]:
    """Fetch courses with comprehensive error handling."""
    url = "https://localhost:8004/api/v1/courses"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            response = await client.get(url, headers=headers)

            # Raise exception for HTTP errors
            response.raise_for_status()

            return response.json()

    except httpx.HTTPStatusError as e:
        error_data = e.response.json()
        error_code = error_data.get("error", {}).get("code")

        if error_code == "AUTHENTICATION_REQUIRED":
            # Handle authentication error
            raise AuthenticationError("Please log in again")
        elif error_code == "INSUFFICIENT_PERMISSIONS":
            # Handle permission error
            raise PermissionError("You don't have access to this resource")
        else:
            # Generic HTTP error
            raise APIError(f"API request failed: {e.response.status_code}")

    except httpx.TimeoutException:
        raise APIError("Request timed out")
    except httpx.NetworkError:
        raise APIError("Network error occurred")
```

## Rate Limiting

### Rate Limit Headers

API responses include rate limit information:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1700000000
```

### Rate Limit Response (429)

When rate limit is exceeded:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "retry_after": 60
  }
}
```

### Rate Limits by Role

- **Student**: 1000 requests/hour
- **Instructor**: 5000 requests/hour
- **Org Admin**: 10000 requests/hour
- **Site Admin**: Unlimited

## API Versioning

### URL Versioning

APIs use URL-based versioning:

```
/api/v1/courses     # Version 1
/api/v2/courses     # Version 2 (future)
```

### Version Compatibility

- **v1** - Current stable version
- Legacy versions supported for 12 months after deprecation
- Breaking changes require new major version
- Deprecation warnings sent via `X-API-Deprecated` header

## Testing APIs

### Using Swagger UI

Access interactive API documentation:

```
https://localhost:8000/docs     # User Management
https://localhost:8004/docs     # Course Management
https://localhost:8006/docs     # Lab Manager
https://localhost:8007/docs     # Analytics
https://localhost:8008/docs     # Organization Management
```

### Using curl

**Example: Create Course**
```bash
TOKEN="your-jwt-token"

curl -X POST "https://localhost:8004/api/v1/courses" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Course",
    "description": "A test course",
    "organization_id": 1,
    "instructor_id": 5
  }' \
  --insecure \
  --verbose
```

### Using Postman/Insomnia

**Import OpenAPI Spec**:
1. Access `/docs` endpoint for any service
2. Click "Download OpenAPI spec"
3. Import JSON into Postman/Insomnia
4. Set environment variable for `token`
5. Test endpoints with pre-configured requests

### Automated Testing

**pytest Example**:
```python
import pytest
import httpx

@pytest.mark.asyncio
async def test_create_course(auth_token):
    """Test course creation API."""
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            "https://localhost:8004/api/v1/courses",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "title": "Test Course",
                "description": "Test Description",
                "organization_id": 1,
                "instructor_id": 5
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Course"
        assert "id" in data
```

---

**For more information**:
- [Development Guide](DEVELOPMENT.md) - Local setup and debugging
- [Architecture Overview](ARCHITECTURE.md) - System design
- [Contributing Guide](../CONTRIBUTING.md) - Contribution workflow

**Need help?** Check the [Troubleshooting Guide](../claude.md/10-troubleshooting.md) or create an issue.
