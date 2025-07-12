# Course Creator Platform - API Documentation

## Overview

The Course Creator Platform provides a comprehensive RESTful API for managing courses, users, and content. The API is built using FastAPI and follows REST conventions.

## Base URLs

- **Development**: `http://localhost:8001`
- **Production**: `https://your-domain.com/api`

## Authentication

All protected endpoints require JWT authentication. Include the token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Getting a Token

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user-id",
    "email": "user@example.com",
    "role": "instructor"
  }
}
```

## Core Endpoints

### Health Check

Check if the API is running and healthy.

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "message": "Course Creator Platform is running",
  "version": "1.0.0",
  "timestamp": "2025-07-12T10:30:00Z"
}
```

## Authentication Endpoints

### Register User

Create a new user account.

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure-password",
  "full_name": "John Doe",
  "role": "student"
}
```

Response:
```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "id": "user-123",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "student",
    "created_at": "2025-07-12T10:30:00Z"
  }
}
```

### Login

Authenticate user and get access token.

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure-password"
}
```

### Get Current User

Get the current authenticated user's information.

```http
GET /api/auth/me
Authorization: Bearer <token>
```

Response:
```json
{
  "id": "user-123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "student",
  "created_at": "2025-07-12T10:30:00Z",
  "last_login": "2025-07-12T10:30:00Z"
}
```

### Logout

Invalidate the current token.

```http
POST /api/auth/logout
Authorization: Bearer <token>
```

## User Management Endpoints

### List Users

Get a list of all users (admin only).

```http
GET /api/users?page=1&limit=10&role=student
Authorization: Bearer <admin-token>
```

Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "user-123",
      "email": "student@example.com",
      "full_name": "Jane Student",
      "role": "student",
      "created_at": "2025-07-12T10:30:00Z",
      "is_active": true
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 50,
    "pages": 5
  }
}
```

### Get User

Get a specific user by ID.

```http
GET /api/users/{user_id}
Authorization: Bearer <token>
```

### Update User

Update user information.

```http
PUT /api/users/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "Updated Name",
  "email": "new-email@example.com"
}
```

### Delete User

Delete a user account (admin only).

```http
DELETE /api/users/{user_id}
Authorization: Bearer <admin-token>
```

## Course Management Endpoints

### List Courses

Get a list of all courses.

```http
GET /api/courses?page=1&limit=10&category=programming&difficulty=beginner
```

Query Parameters:
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 10)
- `category` (optional): Filter by category
- `difficulty` (optional): Filter by difficulty (beginner, intermediate, advanced)
- `instructor_id` (optional): Filter by instructor
- `published` (optional): Filter by published status

Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "course-123",
      "title": "Introduction to Python",
      "description": "Learn Python programming from scratch",
      "category": "programming",
      "difficulty_level": "beginner",
      "estimated_duration": 40,
      "price": 99.99,
      "instructor": {
        "id": "instructor-456",
        "name": "Dr. Jane Smith"
      },
      "thumbnail_url": "https://example.com/thumb.jpg",
      "is_published": true,
      "created_at": "2025-07-12T10:30:00Z",
      "updated_at": "2025-07-12T10:30:00Z",
      "enrollment_count": 150,
      "rating": 4.8
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25,
    "pages": 3
  }
}
```

### Get Course

Get detailed information about a specific course.

```http
GET /api/courses/{course_id}
```

Response:
```json
{
  "success": true,
  "data": {
    "id": "course-123",
    "title": "Introduction to Python",
    "description": "Learn Python programming from scratch",
    "content": {
      "modules": [
        {
          "id": "module-1",
          "title": "Getting Started",
          "lessons": [
            {
              "id": "lesson-1",
              "title": "Installing Python",
              "content": "...",
              "duration": 15
            }
          ]
        }
      ]
    },
    "lab_environment": {
      "id": "lab-123",
      "name": "Python Basics Lab",
      "exercises": [
        {
          "id": "exercise-1",
          "title": "Hello World",
          "instructions": "Write your first Python program"
        }
      ]
    }
  }
}
```

### Create Course

Create a new course (instructor only).

```http
POST /api/courses
Authorization: Bearer <instructor-token>
Content-Type: application/json

{
  "title": "Advanced JavaScript",
  "description": "Master advanced JavaScript concepts",
  "category": "programming",
  "difficulty_level": "intermediate",
  "estimated_duration": 60,
  "price": 149.99,
  "content": {
    "modules": [...]
  }
}
```

### Update Course

Update an existing course.

```http
PUT /api/courses/{course_id}
Authorization: Bearer <instructor-token>
Content-Type: application/json

{
  "title": "Updated Course Title",
  "description": "Updated description",
  "price": 199.99
}
```

### Delete Course

Delete a course (instructor or admin only).

```http
DELETE /api/courses/{course_id}
Authorization: Bearer <token>
```

### Publish Course

Publish a course to make it available to students.

```http
POST /api/courses/{course_id}/publish
Authorization: Bearer <instructor-token>
```

### Unpublish Course

Unpublish a course.

```http
POST /api/courses/{course_id}/unpublish
Authorization: Bearer <instructor-token>
```

## Enrollment Endpoints

### Enroll in Course

Enroll a student in a course.

```http
POST /api/enrollments
Authorization: Bearer <student-token>
Content-Type: application/json

{
  "course_id": "course-123"
}
```

Response:
```json
{
  "success": true,
  "message": "Successfully enrolled in course",
  "enrollment": {
    "id": "enrollment-456",
    "student_id": "student-123",
    "course_id": "course-123",
    "enrolled_at": "2025-07-12T10:30:00Z",
    "status": "active",
    "progress": 0
  }
}
```

### Get Enrollments

Get enrollments for a user or course.

```http
GET /api/enrollments?student_id=student-123&course_id=course-123
Authorization: Bearer <token>
```

### Update Enrollment Progress

Update student progress in a course.

```http
PUT /api/enrollments/{enrollment_id}/progress
Authorization: Bearer <student-token>
Content-Type: application/json

{
  "lesson_id": "lesson-123",
  "completed": true,
  "score": 95
}
```

### Unenroll from Course

Remove a student from a course.

```http
DELETE /api/enrollments/{enrollment_id}
Authorization: Bearer <token>
```

## Content Generation Endpoints

### Generate Course Content

Generate course content using AI.

```http
POST /api/generate/course
Authorization: Bearer <instructor-token>
Content-Type: application/json

{
  "title": "Machine Learning Basics",
  "topics": ["supervised learning", "neural networks", "data preprocessing"],
  "difficulty": "beginner",
  "duration": 30
}
```

Response:
```json
{
  "success": true,
  "message": "Course content generated successfully",
  "course_id": "course-789",
  "content": {
    "modules": [...],
    "exercises": [...],
    "lab_environment": {...}
  }
}
```

### Generate Module

Generate content for a specific module.

```http
POST /api/generate/module
Authorization: Bearer <instructor-token>
Content-Type: application/json

{
  "course_id": "course-123",
  "title": "Advanced Concepts",
  "topics": ["decorators", "generators", "context managers"]
}
```

### Generate Exercise

Generate a coding exercise.

```http
POST /api/generate/exercise
Authorization: Bearer <instructor-token>
Content-Type: application/json

{
  "course_id": "course-123",
  "module_id": "module-456",
  "topic": "list comprehensions",
  "difficulty": "intermediate"
}
```

## Lab Environment Endpoints

### Get Lab Environment

Get lab environment details for a course.

```http
GET /api/labs/{course_id}
Authorization: Bearer <token>
```

### Create Lab Session

Create a new lab session for a student.

```http
POST /api/labs/{course_id}/sessions
Authorization: Bearer <student-token>
```

Response:
```json
{
  "success": true,
  "session": {
    "id": "session-789",
    "student_id": "student-123",
    "course_id": "course-123",
    "lab_url": "http://lab.example.com/session-789",
    "expires_at": "2025-07-12T14:30:00Z"
  }
}
```

### Submit Exercise

Submit a completed exercise.

```http
POST /api/labs/exercises/{exercise_id}/submit
Authorization: Bearer <student-token>
Content-Type: application/json

{
  "code": "print('Hello, World!')",
  "session_id": "session-789"
}
```

## File Upload Endpoints

### Upload Course Material

Upload files for a course.

```http
POST /api/courses/{course_id}/upload
Authorization: Bearer <instructor-token>
Content-Type: multipart/form-data

file: <file-data>
type: "video" | "document" | "image"
```

### Get File

Download or view an uploaded file.

```http
GET /api/files/{file_id}
Authorization: Bearer <token>
```

## Analytics Endpoints

### Course Analytics

Get analytics for a course (instructor only).

```http
GET /api/analytics/courses/{course_id}
Authorization: Bearer <instructor-token>
```

Response:
```json
{
  "success": true,
  "data": {
    "total_enrollments": 150,
    "active_students": 120,
    "completion_rate": 75.5,
    "average_rating": 4.8,
    "revenue": 14985.00,
    "engagement_metrics": {
      "avg_session_duration": 45,
      "modules_completed": 1200,
      "exercises_completed": 850
    }
  }
}
```

### Student Progress

Get detailed progress for a student.

```http
GET /api/analytics/students/{student_id}/progress
Authorization: Bearer <token>
```

## WebSocket Endpoints

### Real-time Lab Session

Connect to a lab session for real-time updates.

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/lab/{session_id}?token={jwt_token}');

// Listen for messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Lab update:', data);
};

// Send commands
ws.send(JSON.stringify({
  type: 'execute',
  command: 'python hello.py'
}));
```

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    }
  },
  "timestamp": "2025-07-12T10:30:00Z"
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
- `409` - Conflict
- `422` - Validation Error
- `429` - Rate Limited
- `500` - Internal Server Error

### Common Error Codes

- `VALIDATION_ERROR` - Input validation failed
- `AUTHENTICATION_REQUIRED` - No token provided
- `INVALID_TOKEN` - Token is invalid or expired
- `INSUFFICIENT_PERMISSIONS` - User lacks required permissions
- `RESOURCE_NOT_FOUND` - Requested resource doesn't exist
- `RESOURCE_CONFLICT` - Resource already exists
- `RATE_LIMITED` - Too many requests
- `INTERNAL_ERROR` - Server error

## Rate Limiting

API endpoints are rate limited to prevent abuse:

- **Authentication**: 5 requests per minute
- **Course Creation**: 10 requests per hour
- **General API**: 100 requests per minute
- **File Upload**: 20 requests per hour

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1625745600
```

## Pagination

List endpoints support pagination:

```http
GET /api/courses?page=2&limit=20
```

Response includes pagination metadata:

```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": true
  }
}
```

## API Versioning

The API uses URL versioning:

- Current version: `v1`
- Base URL: `/api/v1/`
- Deprecated versions remain available for 6 months

## SDKs and Libraries

### JavaScript/TypeScript

```javascript
import { CourseCreatorAPI } from '@course-creator/api-client';

const api = new CourseCreatorAPI({
  baseURL: 'http://localhost:8001',
  apiKey: 'your-api-key'
});

// Get courses
const courses = await api.courses.list({ category: 'programming' });

// Create course
const newCourse = await api.courses.create({
  title: 'New Course',
  description: 'Course description'
});
```

### Python

```python
from course_creator_client import CourseCreatorClient

client = CourseCreatorClient(
    base_url='http://localhost:8001',
    api_key='your-api-key'
)

# Get courses
courses = client.courses.list(category='programming')

# Create course
new_course = client.courses.create(
    title='New Course',
    description='Course description'
)
```

## Interactive API Documentation

Visit the interactive API documentation at:
- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`

These interfaces allow you to:
- Browse all endpoints
- Try API calls directly
- View request/response schemas
- Download OpenAPI specifications