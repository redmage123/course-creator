# Course Creator Platform - API Documentation

## Overview

The Course Creator Platform provides a comprehensive RESTful API for managing courses, users, and content. The API is built using FastAPI and follows REST conventions with a microservices architecture.

## Microservices Architecture

The platform consists of 5 core backend services:

1. **User Management Service** (Port 8000) - Authentication, user profiles, RBAC
2. **Course Generator Service** (Port 8001) - AI-powered content generation
3. **Content Storage Service** (Port 8003) - File storage and versioning
4. **Course Management Service** (Port 8004) - Course CRUD operations
5. **Content Management Service** (Port 8005) - Upload/download and multi-format export

## Base URLs

- **User Management**: `http://localhost:8000`
- **Course Generator**: `http://localhost:8001`
- **Content Storage**: `http://localhost:8003`
- **Course Management**: `http://localhost:8004`
- **Content Management**: `http://localhost:8005`
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

## Core Endpoints

### Health Check

Check if services are running and healthy.

```http
GET http://localhost:8000/health
GET http://localhost:8001/health
GET http://localhost:8003/health
GET http://localhost:8004/health
GET http://localhost:8005/health
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

## Interactive Documentation

### Swagger UI

Each service provides interactive API documentation:

- **User Management**: `http://localhost:8000/docs`
- **Course Generator**: `http://localhost:8001/docs`
- **Content Storage**: `http://localhost:8003/docs`
- **Course Management**: `http://localhost:8004/docs`
- **Content Management**: `http://localhost:8005/docs`

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
2. Course Generator (8001)
3. Course Management (8004)
4. Content Storage (8003)
5. Content Management (8005)

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

**Current Version**: 1.0.0  
**Last Updated**: 2025-07-16  
**Status**: Active Development

For detailed implementation information, see [CLAUDE.md](../CLAUDE.md) and [Architecture Documentation](./architecture.md).