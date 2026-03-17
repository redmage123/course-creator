# Authentication Setup Documentation

## Status: ✅ Authentication Working

**Date**: 2025-11-05
**Version**: 1.0

## Summary

Authentication is fully functional with test users created in the database. The auth API on port 8000 successfully validates credentials and issues JWT tokens.

## Test Users Created

All test users have password: `password123`

| Email | Username | Role | Status |
|-------|----------|------|--------|
| instructor.test@example.com | instructor_test | instructor | ✅ Working |
| student.test@example.com | student_test | student | ✅ Working |
| orgadmin.test@example.com | orgadmin_test | organization_admin | ✅ Working |

## Database Schema

Users are stored in `course_creator.users` table (PostgreSQL schema: `course_creator`):

```sql
Table: course_creator.users
- id: UUID (primary key)
- email: VARCHAR(255) UNIQUE
- username: VARCHAR(50) UNIQUE
- hashed_password: VARCHAR(255) -- bcrypt hashed
- role: VARCHAR(50) -- student, instructor, organization_admin, site_admin
- organization_id: UUID (nullable)
- is_active: BOOLEAN
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

## Authentication Flow

1. **Login Request**: POST `/auth/login`
   ```json
   {
     "username": "instructor.test@example.com",
     "password": "password123"
   }
   ```

2. **Successful Response**: HTTP 200
   ```json
   {
     "access_token": "eyJhbGci...",
     "token_type": "bearer",
     "expires_in": 3600,
     "user": {
       "id": "b53be6bb-7cf4-4bb7-ab61-fe3ae14675dc",
       "email": "instructor.test@example.com",
       "username": "instructor_test",
       "role": "instructor",
       ...
     }
   }
   ```

3. **Token Usage**: Include in Authorization header
   ```
   Authorization: Bearer eyJhbGci...
   ```

## Scripts for User Management

### Create Test Users
```bash
python3 /tmp/create_all_test_users.py
```

### Verify Users
```bash
docker exec course-creator_postgres_1 psql -U postgres -d course_creator \
  -c "SELECT username, email, role FROM course_creator.users WHERE email LIKE '%.test@%';"
```

### Test Authentication
```bash
curl -k -X POST https://176.9.99.103/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"instructor.test@example.com","password":"password123"}'
```

## Known Issues

### E2E Test Routing Mismatch
**Issue**: E2E tests expect React routing (`/dashboard/instructor`) but HTML frontend uses file-based routing (`instructor-dashboard.html`).

**Impact**: E2E tests time out after successful login waiting for React-style URL.

**Solution Options**:
1. Deploy React frontend (recommended - React components are ready)
2. Update E2E tests to match HTML frontend URLs
3. Configure nginx to rewrite HTML frontend URLs to match React patterns

### Frontend Deployment Status
- **HTML Frontend**: ✅ Active at https://176.9.99.103:3000
- **React Frontend**: 📦 Ready but not deployed
  - Location: `/home/bbrelin/course-creator/frontend-react/`
  - Components: Login, Auth hooks, Redux slices all implemented
  - Routing: Uses React Router with `/dashboard/*` patterns

## Next Steps

1. ✅ **Authentication**: COMPLETE - Working with test users
2. ⏳ **Frontend Deployment**: Deploy React frontend OR update test expectations
3. ⏳ **E2E Tests**: Update to match deployed frontend routing
4. ⏳ **Integration**: Full workflow testing once routing resolved

## API Endpoints

### User Management Service (Port 8000)
- `POST /auth/login` - Authenticate user
- `POST /auth/register` - Register new user (defaults to organization_admin role)
- `POST /auth/logout` - Invalidate session
- `POST /auth/refresh` - Refresh JWT token
- `GET /users/me` - Get current user profile

**Registration Example:**
```bash
curl -k -X POST https://176.9.99.103/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "neworg@example.com",
    "username": "neworg",
    "password": "SecurePass123!",
    "full_name": "New Organization Admin"
  }'
```

**Response:**
```json
{
  "id": "uuid",
  "email": "neworg@example.com",
  "role": "organization_admin",
  "status": "active"
}
```

**Important:** New users automatically receive the `organization_admin` role. See [USER_ROLE_ASSIGNMENT.md](USER_ROLE_ASSIGNMENT.md) for complete role assignment rules.

### Frontend (Port 3000)
- Nginx routes `/auth/*` to user-management service (port 8000)
- HTML pages served from `/home/bbrelin/course-creator/frontend/html/`
- Static assets served from `/home/bbrelin/course-creator/frontend/`

## Security Notes

- Passwords hashed with bcrypt (cost factor 12)
- JWT tokens expire after 1 hour
- HTTPS required for all authentication endpoints
- Token refresh available for active sessions
- User accounts can be disabled via `is_active` flag

## Troubleshooting

### "Invalid credentials" Error
1. Verify user exists in `course_creator.users` (NOT `public.users`)
2. Check password is correct (test users use "password123")
3. Verify user `is_active` flag is true
4. Check user-management service logs:
   ```bash
   docker logs course-creator_user-management_1 2>&1 | grep "LOGIN ATTEMPT"
   ```

### Database Connection Issues
- User-management service connects to: `postgres:5432` (internal Docker network)
- External access via: `localhost:5433` (port mapping)
- Database name: `course_creator`
- Schema: `course_creator` (users table must be in this schema)

### Token Validation Failures
- Check token hasn't expired (1 hour lifetime)
- Verify JWT secret matches between services
- Ensure Authorization header format: `Bearer <token>`
