# Contributing to Course Creator Platform

Thank you for your interest in contributing to the Course Creator Platform! This document provides guidelines for developers who want to contribute to this educational technology system.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Code Review Process](#code-review-process)

## Getting Started

### Prerequisites

Before contributing, ensure you have the following installed:

- **Docker 24.0+** and **Docker Compose v2.20+** (required)
- **Python 3.12+** (for local development)
- **Node.js 18+** and **npm 9+** (for frontend development)
- **Git 2.30+**
- **PostgreSQL 15+** (included in Docker setup)
- **Redis 7+** (included in Docker setup)

### Initial Setup

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/course-creator.git
   cd course-creator
   ```

2. **Set Up Python Virtual Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. **Configure Environment Variables**
   ```bash
   cp .env.example .cc_env
   # Edit .cc_env with your local configuration
   nano .cc_env
   ```

4. **Start the Platform with Docker**
   ```bash
   # Build and start all services
   docker-compose up -d --build

   # Verify all services are healthy
   ./scripts/app-control.sh status
   ```

5. **Set Up Development Database**
   ```bash
   # Run database migrations
   python deploy/setup-database.py

   # Create test data
   python scripts/setup-dev-data.py
   ```

### Frontend React Development Setup

```bash
cd frontend-react
npm install
npm run dev  # Start Vite development server on http://localhost:5173
```

## Development Workflow

### Branch Strategy

We use a Git Flow-inspired branching strategy:

- **`master`** - Production-ready code
- **`develop`** - Integration branch for features
- **`feature/*`** - Feature branches (e.g., `feature/rag-assistant`)
- **`bugfix/*`** - Bug fix branches (e.g., `bugfix/auth-redirect`)
- **`hotfix/*`** - Critical production fixes

### Creating a New Feature

1. **Create a feature branch from `develop`**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes following code style guidelines**

3. **Write tests for your changes** (see Testing Requirements)

4. **Run all tests locally**
   ```bash
   # Python tests
   pytest tests/ -v

   # Frontend tests
   cd frontend-react
   npm test
   npm run test:e2e

   # Docker infrastructure tests
   ./scripts/app-control.sh status 2>&1 | grep "✅"
   ```

5. **Commit your changes** (see Commit Message Guidelines)

6. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style Guidelines

### Python Code Style

**CRITICAL**: The platform enforces strict Python coding standards.

#### 1. Absolute Imports Only

**NEVER use relative imports**. All imports must be absolute using service-specific namespaces.

```python
# ❌ WRONG - Relative imports
from ..domain.entities.user import User
from ...application.services.auth_service import AuthService

# ✅ CORRECT - Absolute imports with service namespace
from user_management.domain.entities.user import User
from user_management.application.services.auth_service import AuthService
```

#### 2. Service-Specific Namespaces

Each service uses its own namespace to prevent collisions:

```
services/user-management/
├── user_management/           # ← Service namespace package
│   ├── __init__.py
│   ├── domain/
│   │   └── entities/
│   ├── application/
│   │   └── services/
│   └── infrastructure/
│       └── repositories/
├── api/                       # ← API endpoints
├── data_access/               # ← DAOs
└── main.py
```

**Import Examples:**
```python
# User Management Service
from user_management.domain.entities.user import User
from user_management.application.services.user_service import UserService

# Course Management Service
from course_management.domain.entities.course import Course
from course_management.application.services.course_service import CourseService

# Organization Management Service
from organization_management.domain.entities.organization import Organization
```

#### 3. Custom Exception Handling

**NEVER use generic exception handlers**. Use structured custom exceptions with f-strings.

```python
# ❌ WRONG - Generic exception handling
try:
    result = process_data()
except Exception as e:
    print(f"Error: {e}")

# ✅ CORRECT - Custom exceptions
from user_management.domain.exceptions import (
    UserNotFoundException,
    InvalidCredentialsException
)

try:
    user = user_service.get_user(user_id)
except UserNotFoundException as e:
    raise HTTPException(
        status_code=404,
        detail=f"User {user_id} not found: {str(e)}"
    )
```

#### 4. Comprehensive Documentation

All code must include multiline docstrings explaining business context and technical rationale.

```python
def create_course(
    self,
    title: str,
    organization_id: int,
    instructor_id: int
) -> Course:
    """
    Create a new course within an organization's boundary.

    Business Context:
    - Courses are organization-specific and cannot be accessed across organizations
    - Instructor must belong to the same organization
    - Course creation triggers automatic track enrollment for relevant students

    Technical Implementation:
    - Validates organization membership
    - Creates course entity with UUID identifier
    - Publishes course_created event for track enrollment
    - Stores in PostgreSQL with organization_id for data isolation

    Args:
        title: Course title (max 200 characters)
        organization_id: Organization boundary for this course
        instructor_id: User ID of instructor (must be in same organization)

    Returns:
        Course: Newly created course entity

    Raises:
        OrganizationMismatchException: Instructor not in specified organization
        ValidationException: Invalid course parameters
    """
    # Implementation
```

#### 5. Python Formatting

Use standard Python formatting tools:

```bash
# Code formatting
black services/ --line-length 88

# Import sorting
isort services/ --profile black

# Linting
flake8 services/ --max-line-length 88 --extend-ignore=E203,W503

# Type checking
mypy services/ --strict
```

### TypeScript/React Code Style

#### 1. TypeScript Configuration

Follow strict TypeScript settings:

```typescript
// ✅ CORRECT - Typed React components
interface CourseCardProps {
  course: Course;
  onEnroll: (courseId: string) => void;
}

export const CourseCard: React.FC<CourseCardProps> = ({ course, onEnroll }) => {
  return (
    <div className="course-card">
      <h3>{course.title}</h3>
      <button onClick={() => onEnroll(course.id)}>Enroll</button>
    </div>
  );
};

// ❌ WRONG - No type annotations
export const CourseCard = ({ course, onEnroll }) => {
  // Missing types
};
```

#### 2. Component Structure

Use functional components with hooks:

```typescript
// ✅ CORRECT - Functional component with hooks
export const StudentDashboard: React.FC = () => {
  const { user } = useAuth();
  const { data: courses, isLoading } = useQuery(['courses'], fetchCourses);

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="dashboard">
      <h1>Welcome, {user.name}</h1>
      <CourseList courses={courses} />
    </div>
  );
};
```

#### 3. State Management

Use Redux Toolkit for global state, React Query for server state:

```typescript
// Redux Toolkit slice
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface AuthState {
  user: User | null;
  token: string | null;
}

const authSlice = createSlice({
  name: 'auth',
  initialState: { user: null, token: null } as AuthState,
  reducers: {
    setAuth: (state, action: PayloadAction<AuthState>) => {
      state.user = action.payload.user;
      state.token = action.payload.token;
    },
  },
});
```

#### 4. React Formatting

```bash
# Code formatting
npm run format

# Linting
npm run lint
npm run lint:fix

# Type checking
npm run type-check
```

### CSS/Styling Guidelines

Use CSS Modules for component-specific styles:

```typescript
// Component.module.css
import styles from './Component.module.css';

export const Component = () => {
  return <div className={styles.container}>Content</div>;
};
```

## Testing Requirements

### CRITICAL: Mandatory Testing Before PR

**Before submitting any Pull Request, ALL of the following tests MUST pass:**

#### 1. Docker Infrastructure Tests (MANDATORY)

```bash
# ALL 16 services must be healthy
./scripts/app-control.sh status 2>&1 | grep "✅"
# Expected: 16 services showing "✅ Healthy"
```

#### 2. Python Unit and Integration Tests

```bash
# Run all Python tests
pytest tests/ -v --cov=services --cov-report=html

# Minimum coverage: 80% for new code
# Check coverage report in htmlcov/index.html
```

#### 3. Frontend Tests

```bash
cd frontend-react

# Unit tests (Vitest)
npm test

# E2E tests (Cypress)
npm run test:e2e

# All critical user journeys must pass
npm run test:e2e:critical
```

#### 4. Comprehensive E2E Testing (HIGHEST PRIORITY)

**ALL user roles must have complete E2E test coverage:**

```bash
# Priority 0 tests - ALL must pass
pytest tests/e2e/critical_user_journeys/test_student_complete_journey.py -v
pytest tests/e2e/critical_user_journeys/test_instructor_complete_journey.py -v
pytest tests/e2e/critical_user_journeys/test_org_admin_complete_journey.py -v
pytest tests/e2e/critical_user_journeys/test_site_admin_complete_journey.py -v
pytest tests/e2e/critical_user_journeys/test_guest_complete_journey.py -v
```

### Test-Driven Development (TDD)

We follow **Red-Green-Refactor** approach:

1. **Red**: Write a failing test
2. **Green**: Write minimal code to make it pass
3. **Refactor**: Clean up while keeping tests green

```python
# Example TDD workflow
class TestCourseCreation:
    """Test course creation following TDD approach."""

    def test_create_course_with_valid_data(self):
        """RED: Test fails initially (no implementation)."""
        course_service = CourseService()
        course = course_service.create_course(
            title="Introduction to Python",
            organization_id=1,
            instructor_id=5
        )

        assert course.id is not None
        assert course.title == "Introduction to Python"
        assert course.organization_id == 1

    def test_create_course_with_invalid_instructor(self):
        """Test validation - instructor must be in organization."""
        course_service = CourseService()

        with pytest.raises(OrganizationMismatchException):
            course_service.create_course(
                title="Test Course",
                organization_id=1,
                instructor_id=999  # Not in organization 1
            )
```

### Writing Good Tests

**Good Test Characteristics:**
- **Isolated**: Each test runs independently
- **Repeatable**: Same result every time
- **Fast**: Tests should run quickly
- **Clear**: Easy to understand what's being tested
- **Comprehensive**: Test happy path, edge cases, and error conditions

```python
# ✅ GOOD - Clear, isolated, comprehensive
class TestPasswordValidation:
    """Test password validation rules."""

    def test_password_meets_minimum_length(self):
        """Password must be at least 8 characters."""
        validator = PasswordValidator()
        assert validator.validate("Short1!") is False
        assert validator.validate("LongPass1!") is True

    def test_password_requires_special_character(self):
        """Password must contain at least one special character."""
        validator = PasswordValidator()
        assert validator.validate("NoSpecial123") is False
        assert validator.validate("HasSpecial123!") is True

    def test_password_strength_scoring(self):
        """Password strength score calculated correctly."""
        validator = PasswordValidator()
        assert validator.calculate_strength("weak") == 1
        assert validator.calculate_strength("Medium123") == 3
        assert validator.calculate_strength("Str0ng!Pass123") == 5
```

## Pull Request Process

### Before Creating a PR

1. **Run all tests locally** (see Testing Requirements)
2. **Update documentation** for any API changes
3. **Add tests** for new features
4. **Update CHANGELOG.md** with your changes
5. **Ensure all Docker services are healthy**

### PR Checklist

Your PR must include:

- [ ] **Descriptive title** following commit message guidelines
- [ ] **Detailed description** of changes and motivation
- [ ] **Test results** showing all tests pass
- [ ] **Screenshots/videos** for UI changes
- [ ] **Updated documentation** for API/feature changes
- [ ] **Migration scripts** for database schema changes
- [ ] **Breaking changes** clearly documented
- [ ] **Security implications** reviewed and documented
- [ ] **Performance impact** considered and documented

### PR Template

```markdown
## Description
Brief description of changes and why they were made.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing Performed
- [ ] All Docker services healthy
- [ ] Python unit tests pass (coverage: X%)
- [ ] Frontend tests pass
- [ ] E2E tests for all user roles pass
- [ ] Manual testing completed

## Test Results
```
pytest tests/ -v
PASSED tests/... (127 tests)
Coverage: 85%
```

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added for new features
- [ ] All tests pass locally
- [ ] Dependent changes merged

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Additional Context
[Any additional information about the PR]
```

## Commit Message Guidelines

We follow **Conventional Commits** specification:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring (no feature change)
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Build process, tooling changes
- **ci**: CI/CD configuration changes

### Scope

The scope should be the service or component name:
- `user-management`
- `course-generator`
- `frontend-react`
- `docker`
- `testing`
- `docs`

### Examples

```bash
# Feature addition
feat(course-management): add course versioning system

Implement major/minor version tracking for courses with student migration
support and version comparison features.

- Add version entity and repository
- Implement version creation API endpoints
- Add student migration to new versions
- Include version comparison UI

Closes #123

# Bug fix
fix(auth): resolve JWT token expiration handling

Tokens were not being refreshed correctly, causing users to be logged out
prematurely. Updated refresh token logic to check expiration before making
requests.

Fixes #456

# Breaking change
feat(rbac)!: implement organization-based data isolation

BREAKING CHANGE: All API endpoints now require organization_id parameter.
Clients must update to include organization context in all requests.

Migration guide: docs/MIGRATION_V3.md

# Documentation
docs(api): update authentication flow documentation

Add detailed documentation for OAuth2 flow and JWT token refresh mechanism
with code examples and sequence diagrams.
```

### Commit Message Best Practices

1. **Use imperative mood**: "Add feature" not "Added feature"
2. **Keep subject line under 50 characters**
3. **Separate subject from body with blank line**
4. **Wrap body at 72 characters**
5. **Explain what and why, not how**
6. **Reference issues and PRs**

## Code Review Process

### Submitting Code for Review

1. **Self-review your code** first
2. **Respond to all review comments** promptly
3. **Push updates** to the same branch
4. **Request re-review** after addressing feedback

### Code Review Guidelines

Reviewers will check for:

#### Architecture & Design
- [ ] Follows service-specific namespace pattern
- [ ] Uses absolute imports only
- [ ] Proper separation of concerns (domain/application/infrastructure)
- [ ] Consistent with existing architecture

#### Code Quality
- [ ] No code duplication
- [ ] Functions are single-purpose
- [ ] Clear variable and function names
- [ ] Appropriate error handling
- [ ] Comprehensive docstrings

#### Security
- [ ] No security vulnerabilities
- [ ] Proper input validation
- [ ] No hardcoded secrets
- [ ] Organization data isolation maintained
- [ ] Authentication/authorization properly implemented

#### Testing
- [ ] Adequate test coverage (80%+ for new code)
- [ ] Tests are clear and maintainable
- [ ] All test categories pass
- [ ] E2E tests for user-facing changes

#### Performance
- [ ] No obvious performance issues
- [ ] Database queries optimized
- [ ] Appropriate caching used
- [ ] Resource cleanup handled

#### Documentation
- [ ] Code is well-documented
- [ ] API changes documented
- [ ] README updated if needed
- [ ] Migration guide for breaking changes

### Review Response Time

- **Critical fixes**: 24 hours
- **New features**: 2-3 business days
- **Documentation**: 3-5 business days

## Additional Resources

- **[Development Guide](docs/DEVELOPMENT.md)** - Local setup and debugging
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System design and patterns
- **[API Documentation](docs/API_OVERVIEW.md)** - Service endpoints and contracts
- **[Testing Strategy](claude.md/08-testing-strategy.md)** - Comprehensive testing approach
- **[Troubleshooting](claude.md/10-troubleshooting.md)** - Common issues and solutions

## Questions?

If you have questions about contributing:

1. Check existing documentation
2. Search closed issues and PRs
3. Ask in discussions or create an issue
4. Contact maintainers

Thank you for contributing to Course Creator Platform!
