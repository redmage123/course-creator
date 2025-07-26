# Course Creator Platform - API Documentation

## Overview

The Course Creator Platform provides a comprehensive RESTful API for managing courses, users, and content. The API is built using FastAPI and follows REST conventions with a microservices architecture.

## Microservices Architecture

The platform consists of 7 core backend services:

1. **User Management Service** (Port 8000) - Authentication, user profiles, RBAC
2. **Course Generator Service** (Port 8001) - AI-powered content generation
3. **Content Storage Service** (Port 8003) - File storage and versioning
4. **Course Management Service** (Port 8004) - Course CRUD operations
5. **Content Management Service** (Port 8005) - Upload/download and multi-format export
6. **Lab Container Manager Service** (Port 8006) - Individual student Docker container management
7. **Analytics Service** (Port 8007) - Student analytics, progress tracking, and learning insights

## Base URLs

- **User Management**: `http://localhost:8000`
- **Course Generator**: `http://localhost:8001`
- **Content Storage**: `http://localhost:8003`
- **Course Management**: `http://localhost:8004`
- **Content Management**: `http://localhost:8005`
- **Lab Container Manager**: `http://localhost:8006`
- **Analytics Service**: `http://localhost:8007`
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
GET http://localhost:8006/health
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
6. Lab Container Manager (8006)

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

**Current Version**: 2.0.0 - Enhanced with Individual Lab Container System  
**Last Updated**: 2025-07-26  
**Status**: Production Ready with Advanced Lab Container Management

### New in v2.0
- **Individual Docker Lab Containers** - Per-student isolated environments
- **Dynamic Image Building** - Custom lab environments built on-demand
- **Automatic Lab Lifecycle Management** - Login/logout integration with persistence
- **Comprehensive Instructor Lab Controls** - Real-time monitoring and management
- **Full Docker Compose Orchestration** - Production-ready containerized deployment

For detailed implementation information, see [CLAUDE.md](../CLAUDE.md) and [Architecture Documentation](./architecture.md).