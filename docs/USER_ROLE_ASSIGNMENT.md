# User Role Assignment Business Rules

## Overview

The Course Creator Platform implements a hierarchical role-based access control (RBAC) system with specific business rules for role assignment during registration and organizational management.

## Role Hierarchy

```
site_admin (platform-wide administration)
    ↓
organization_admin (organization management)
    ↓
instructor (teaching & content creation)
    ↓
student (learning)
```

## Business Rules

### 1. New User Registration (Self-Service)

**Rule**: All new users who self-register receive the `organization_admin` role by default.

**Rationale**:
- New users are typically organizations setting up their training programs
- Organization admins can then create and manage instructors within their organization
- Students are created through bulk enrollment or instructor assignment (not self-registration)

**Implementation**:
- File: `services/user-management/user_management/application/services/user_service.py:191`
- Default role: `organization_admin`

**Code**:
```python
'role': UserRole(user_data.get('role', 'organization_admin'))
```

### 2. Returning Users

**Rule**: Returning users authenticate with their existing role (organization_admin or instructor).

**User Types**:
- **Organization Admins**:
  - Created via self-registration
  - Manage their organization's training programs
  - Create and assign instructors
  - Manage tracks, locations, and schedules

- **Instructors**:
  - Created by organization admins
  - Assigned to specific organizations
  - Create courses and training content
  - Manage student enrollments

**Authentication**:
- All returning users use email/username + password
- Role is retrieved from database during login
- JWT token includes role for authorization

### 3. Instructor Assignment

**Rule**: Instructors must be assigned to an organization.

**Process**:
1. Organization admin creates instructor account
2. Instructor is linked to the org admin's organization
3. Instructor can only access courses within their assigned organization

**Database Fields**:
- `users.role` = 'instructor'
- `users.organization_id` = UUID of organization
- Foreign key relationship ensures data integrity

**Implementation Points**:
- Instructors cannot be created without an organization_id
- Instructors inherit organization context for all operations
- Organization admins can manage instructors within their organization

### 4. Student Creation

**Rule**: Students are not self-registered. They are created through:

1. **Bulk Enrollment**: Organization admin or instructor uploads spreadsheet
2. **Individual Assignment**: Instructor adds students to courses
3. **API Integration**: External systems create student accounts

**Student Properties**:
- `role` = 'student'
- Linked to course enrollments (not directly to organizations)
- Access controlled via course instance permissions

### 5. Site Admin Role

**Rule**: Site admins are created manually via database or special admin tools.

**Characteristics**:
- Platform-wide administrative access
- Can manage all organizations
- Cannot be created through public registration
- Should be limited to platform operators

## Registration Flow

### New Organization Signup

```
1. User visits registration page
2. Fills out: email, username, password, organization name
3. System creates:
   - User account with role='organization_admin'
   - Organization record
   - Links user to organization
4. User can immediately:
   - Create instructors
   - Set up training programs
   - Configure organizational settings
```

### Instructor Creation by Org Admin

```
1. Org admin logs in to dashboard
2. Navigates to "Manage Instructors"
3. Clicks "Add Instructor"
4. Fills out: email, username, password, full name
5. System creates:
   - User account with role='instructor'
   - Links to org admin's organization_id
   - Instructor can access org's courses
```

### Student Enrollment

```
1. Instructor creates course instance
2. Uploads enrollment spreadsheet OR adds students manually
3. System creates:
   - User accounts with role='student'
   - Course enrollment records
   - Access credentials (sent via email)
```

## Database Schema

### Users Table

```sql
CREATE TABLE course_creator.users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN (
        'student',
        'instructor',
        'organization_admin',
        'site_admin'
    )),
    organization_id UUID REFERENCES organizations(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Role Constraints

- **organization_admin**: organization_id should be set (owns the organization)
- **instructor**: organization_id MUST be set (assigned to organization)
- **student**: organization_id is NULL (access via course enrollments)
- **site_admin**: organization_id is NULL (platform-wide access)

## API Endpoints

### Registration (Public)
```
POST /auth/register
Body: {
  "email": "admin@company.com",
  "username": "admin",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "organization_name": "Acme Corp"  // Optional - creates org if provided
}
Response: {
  "user": {
    "id": "uuid",
    "email": "admin@company.com",
    "role": "organization_admin",  // Default for new users
    "organization_id": "org-uuid"
  }
}
```

### Login (Returning Users)
```
POST /auth/login
Body: {
  "username": "instructor@company.com",
  "password": "password123"
}
Response: {
  "access_token": "jwt-token",
  "user": {
    "role": "instructor",  // Retrieved from database
    "organization_id": "org-uuid"
  }
}
```

## Frontend Implications

### Registration Page
- Default assumption: User is creating an organization
- Form should include organization name field
- Success message: "Welcome! You can now add instructors and create courses."

### Login Page
- Works for all user types (org admins, instructors)
- Redirects based on role:
  - `organization_admin` → Org Admin Dashboard
  - `instructor` → Instructor Dashboard
  - `site_admin` → Site Admin Dashboard

### Dashboard Features by Role

**Organization Admin Dashboard**:
- Manage Instructors
- Manage Training Programs/Tracks
- View Organization Analytics
- Configure Settings

**Instructor Dashboard**:
- Create Courses
- Manage Students
- View Course Analytics
- Generate Content

**Site Admin Dashboard**:
- Manage All Organizations
- Platform Configuration
- System Monitoring

## Security Considerations

1. **Role Elevation Prevention**: Users cannot self-elevate their role
2. **Organization Isolation**: Instructors cannot access other organizations
3. **Audit Trail**: Role changes are logged with timestamps and actor
4. **Token Validation**: JWT tokens include role for every request
5. **Permission Checks**: Backend validates role for every protected operation

## Testing

### Test Users Created

Current test users (password: `password123`):
- `instructor.test@example.com` - Role: instructor
- `orgadmin.test@example.com` - Role: organization_admin
- `student.test@example.com` - Role: student

### Testing New Registration

```bash
# Test registration creates organization_admin
curl -k -X POST https://176.9.99.103/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "neworg@example.com",
    "username": "neworg",
    "password": "SecurePass123!",
    "full_name": "New Organization Admin"
  }'

# Verify role in response
# Expected: "role": "organization_admin"
```

## Migration Notes

**Previous Default**: Students were the default role for new registrations.

**Change Reason**: Business requirement clarification - new signups are organizations, not individual students.

**Impact**:
- ✅ Existing users unchanged
- ✅ New registrations get organization_admin role
- ✅ Student accounts still created via enrollment workflows
- ✅ No database migration needed (role stored as string)

## Related Documentation

- [Authentication Setup](AUTHENTICATION_SETUP.md) - Login and JWT token details
- [RBAC System](../services/organization-management/docs/RBAC.md) - Permission system
- [Organization Management](../services/organization-management/README.md) - Org structure
