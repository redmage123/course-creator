# Backend API Reference

This document provides a quick reference for the backend microservices APIs used by the React frontend.

## 🌐 Microservices Overview

| Service | Port | Base URL | Purpose |
|---------|------|----------|---------|
| user-management | 8000 | https://localhost:8000 | Authentication, user profiles, sessions |
| course-management | 8001 | https://localhost:8001 | Courses/training programs, enrollments, feedback |
| content-management | 8002 | https://localhost:8002 | Course content, materials, labs |
| course-generator | 8003 | https://localhost:8003 | AI-powered content generation |
| analytics | 8004 | https://localhost:8004 | Learning analytics, reports, metrics |
| organization-management | 8005 | https://localhost:8005 | Organizations, trainers, RBAC |
| knowledge-graph-service | 8006 | https://localhost:8006 | Knowledge graphs, prerequisites |
| metadata-service | 8007 | https://localhost:8007 | Metadata, search, tagging |
| nlp-preprocessing | 8008 | https://localhost:8008 | NLP, text processing |
| demo-service | 8010 | https://localhost:8010 | Demo data generation |

---

## 🔐 Authentication & Users (port 8000)

### Authentication Endpoints
- `POST /login` - User login (returns JWT token)
- `POST /logout` - User logout
- `POST /register` - User registration
- `POST /password-reset-request` - Request password reset
- `POST /password-reset-verify` - Verify reset token
- `POST /password-reset-complete` - Complete password reset

### User Profile Endpoints
- `GET /users/{user_id}` - Get user profile
- `GET /users/me` - Get current user profile
- `PUT /users/{user_id}` - Update user profile
- `POST /users/{user_id}/change-password` - Change password

---

## 📚 Training Programs & Enrollment (port 8001)

### Course/Training Program Endpoints
- `POST /courses` - Create training program
- `GET /courses/{course_id}` - Get training program details
- `GET /courses` - List training programs (with filters)
- `PUT /courses/{course_id}` - Update training program
- `POST /courses/{course_id}/publish` - Publish training program
- `POST /courses/{course_id}/unpublish` - Unpublish training program
- `DELETE /courses/{course_id}` - Delete training program

### Enrollment Endpoints
- `POST /enrollments` - Enroll single student
- `POST /courses/{course_id}/bulk-enroll` - Bulk enroll students in course
- `POST /tracks/{track_id}/bulk-enroll` - Bulk enroll students in track

### Feedback Endpoints
- `POST /feedback/course` - Submit course feedback
- `POST /feedback/student` - Submit student feedback
- `GET /feedback/course/{course_id}` - Get course feedback
- `GET /feedback/student/{student_id}` - Get student feedback

---

## 📊 Analytics & Reports (port 8004)

### Analytics Endpoints
- `GET /analytics/student/{student_id}` - Get student analytics
- `GET /analytics/course/{course_id}` - Get course analytics
- `GET /analytics/organization/{org_id}` - Get organization analytics
- `GET /analytics/instructor/{instructor_id}` - Get instructor analytics

---

## 🏢 Organizations & Trainers (port 8005)

### Organization Endpoints
- `POST /organizations` - Create organization
- `GET /organizations/{org_id}` - Get organization details
- `GET /organizations` - List organizations
- `PUT /organizations/{org_id}` - Update organization
- `DELETE /organizations/{org_id}` - Delete organization

### Member/Trainer Management
- `POST /organizations/{org_id}/members` - Add member (trainer/admin)
- `GET /organizations/{org_id}/members` - List organization members
- `DELETE /organizations/{org_id}/members/{user_id}` - Remove member

---

## 🤖 AI Content Generation (port 8003)

### Content Generation Endpoints
- `POST /generate/quiz` - Generate quiz with AI
- `POST /generate/slides` - Generate slides with AI
- `POST /generate/syllabus` - Generate syllabus with AI
- `POST /generate/exercise` - Generate exercise with AI

---

## 🔍 Common Query Parameters

### Pagination
- `?page=1` - Page number (default: 1)
- `?limit=20` - Results per page (default: 20)

### Filtering (Training Programs)
- `?organization_id={org_id}` - Filter by organization
- `?project_id={project_id}` - Filter by project
- `?track_id={track_id}` - Filter by track
- `?instructor_id={instructor_id}` - Filter by instructor
- `?difficulty_level=beginner|intermediate|advanced` - Filter by difficulty
- `?published=true|false` - Filter by publication status

---

## 📦 Common Response Formats

### Success Response
```json
{
  "data": { ... },
  "message": "Success message",
  "status": "success"
}
```

### Error Response
```json
{
  "detail": "Error message",
  "status": "error",
  "error_code": "ERROR_CODE"
}
```

### List Response
```json
{
  "data": [ ... ],
  "total": 100,
  "page": 1,
  "limit": 20,
  "pages": 5
}
```

---

## 🔑 Authentication

All protected endpoints require JWT token in header:
```
Authorization: Bearer {jwt_token}
```

Token is returned from `/login` endpoint and should be stored in Redux auth slice.

---

## 📝 Notes for Frontend Integration

1. **Base URLs**: All services use HTTPS on localhost in development
2. **CORS**: Backend services are configured to accept requests from frontend ports
3. **Error Handling**: All services use consistent error response format
4. **Organization Context**: Many endpoints automatically filter by user's organization
5. **B2B Model**: Students only see assigned courses (no browsing endpoints for students)
6. **Bulk Operations**: Prioritize bulk enrollment endpoints for enterprise features
