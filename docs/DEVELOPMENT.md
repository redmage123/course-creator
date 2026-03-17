# Development Guide

This guide provides comprehensive information for setting up a local development environment, debugging, and daily development workflows for the Course Creator Platform.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Environment Setup](#development-environment-setup)
- [Running the Platform](#running-the-platform)
- [Development Workflows](#development-workflows)
- [Debugging Guide](#debugging-guide)
- [Database Management](#database-management)
- [Testing During Development](#testing-during-development)
- [Common Development Tasks](#common-development-tasks)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

## Quick Start

Get the platform running in under 5 minutes:

```bash
# Clone repository
git clone https://github.com/yourusername/course-creator.git
cd course-creator

# Start all services with Docker
docker-compose up -d

# Verify all services are healthy
./scripts/app-control.sh status

# Access the platform
# Frontend: https://localhost:3000
# API Docs: https://localhost:8000/docs
```

## Development Environment Setup

### System Requirements

**Minimum Requirements:**
- CPU: 4 cores (8 recommended for multi-IDE lab support)
- RAM: 8GB (16GB recommended)
- Disk: 20GB free space
- OS: Ubuntu 20.04+, macOS 12+, or Windows 10/11 with WSL2

**Required Software:**
- Docker 24.0+ and Docker Compose v2.20+
- Python 3.12+
- Node.js 18+ and npm 9+
- Git 2.30+

### Python Development Environment

1. **Create Virtual Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate  # Windows
   ```

2. **Install Dependencies**
   ```bash
   # Production dependencies
   pip install -r requirements.txt

   # Development dependencies (includes testing, linting, etc.)
   pip install -r requirements-dev.txt
   ```

3. **Verify Installation**
   ```bash
   python --version  # Should be 3.12+
   pip list | grep fastapi
   pip list | grep pytest
   ```

### Node.js/React Development Environment

1. **Install Frontend Dependencies**
   ```bash
   cd frontend-react
   npm install
   ```

2. **Verify Installation**
   ```bash
   node --version  # Should be 18+
   npm --version   # Should be 9+
   npm list react  # Verify React 19.1.1
   ```

### Docker Development Environment

1. **Verify Docker Installation**
   ```bash
   docker --version
   docker-compose --version  # or: docker compose version
   docker ps  # Verify Docker daemon is running
   ```

2. **Configure Docker Resources**

   For optimal development experience, allocate adequate resources:

   **Docker Desktop Settings:**
   - CPUs: 4-6 cores
   - Memory: 8-12 GB
   - Swap: 2 GB
   - Disk: 60 GB

3. **Build Base Image**
   ```bash
   # Build shared base image (speeds up subsequent builds)
   docker-compose build base-image
   ```

### Environment Configuration

1. **Copy Environment Template**
   ```bash
   cp .env.example .cc_env
   ```

2. **Configure Environment Variables**

   Edit `.cc_env` with your settings:

   ```bash
   # Database Configuration
   DATABASE_URL=postgresql://postgres:postgres_password@postgres:5432/course_creator
   DB_HOST=postgres
   DB_PORT=5432
   DB_USER=postgres
   DB_PASSWORD=postgres_password
   DB_NAME=course_creator

   # Redis Configuration
   REDIS_URL=redis://redis:6379

   # JWT Authentication
   JWT_SECRET_KEY=your-development-secret-key-change-in-production
   JWT_ALGORITHM=HS256
   JWT_EXPIRATION_MINUTES=60

   # AI Services (Optional - for course generation)
   ANTHROPIC_API_KEY=your-anthropic-api-key
   OPENAI_API_KEY=your-openai-api-key

   # Environment
   ENVIRONMENT=development
   DEBUG=true
   LOG_LEVEL=DEBUG

   # Docker Configuration
   DOCKER_CONTAINER=true
   PYTHONPATH=/app:/app/.venv/lib/python3.12/site-packages
   VIRTUAL_ENV=/app/.venv
   ```

### IDE Configuration

#### VS Code Setup

1. **Install Recommended Extensions**
   ```json
   {
     "recommendations": [
       "ms-python.python",
       "ms-python.vscode-pylance",
       "ms-python.black-formatter",
       "esbenp.prettier-vscode",
       "dbaeumer.vscode-eslint",
       "bradlc.vscode-tailwindcss",
       "ms-azuretools.vscode-docker"
     ]
   }
   ```

2. **Workspace Settings** (`.vscode/settings.json`)
   ```json
   {
     "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
     "python.formatting.provider": "black",
     "python.linting.enabled": true,
     "python.linting.flake8Enabled": true,
     "python.testing.pytestEnabled": true,
     "python.testing.pytestArgs": ["tests"],
     "editor.formatOnSave": true,
     "editor.codeActionsOnSave": {
       "source.organizeImports": true
     },
     "[typescript]": {
       "editor.defaultFormatter": "esbenp.prettier-vscode"
     },
     "[typescriptreact]": {
       "editor.defaultFormatter": "esbenp.prettier-vscode"
     }
   }
   ```

#### PyCharm Setup

1. **Configure Python Interpreter**
   - File → Settings → Project → Python Interpreter
   - Add Interpreter → Existing Environment
   - Select `.venv/bin/python`

2. **Enable pytest**
   - File → Settings → Tools → Python Integrated Tools
   - Default test runner: pytest

3. **Configure Docker**
   - View → Tool Windows → Services
   - Add Docker connection

## Running the Platform

### Docker Deployment (Recommended)

Docker deployment includes all services, database, and dependencies:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f user-management

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up -d --build --force-recreate

# Clean rebuild (no cache)
docker-compose build --no-cache
docker-compose up -d
```

### App Control Script

Use the `app-control.sh` script for easy service management:

```bash
# Start all services
./scripts/app-control.sh start

# Check service status
./scripts/app-control.sh status

# Stop all services
./scripts/app-control.sh stop

# Restart services
./scripts/app-control.sh restart

# View logs
./scripts/app-control.sh logs user-management

# Health check
./scripts/app-control.sh health-check
```

### Native Python Development (Individual Services)

For debugging specific services without Docker:

```bash
# Ensure PostgreSQL and Redis are running (via Docker)
docker-compose up -d postgres redis

# Activate virtual environment
source .venv/bin/activate

# Run individual service
cd services/user-management
python main.py  # Starts on port 8000

# In another terminal
cd services/course-generator
python main.py  # Starts on port 8001
```

### Frontend Development

#### React Development Server (Vite)

```bash
cd frontend-react
npm run dev  # Starts on http://localhost:5173

# With specific port
npm run dev -- --port 5174

# With host binding
npm run dev -- --host 0.0.0.0
```

#### Production Build

```bash
cd frontend-react
npm run build  # Creates optimized build in dist/

# Preview production build
npm run preview  # Serves production build
```

## Development Workflows

### Hot Reload Development

#### Backend Services (FastAPI)

FastAPI includes automatic reload during development:

```python
# main.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        reload_dirs=["./"]
    )
```

**Note**: Code changes automatically restart the service.

#### Frontend (Vite)

Vite provides instant hot module replacement (HMR):

```bash
npm run dev  # Changes reflect instantly without full reload
```

### Working with Multiple Services

When developing features that span multiple services:

1. **Start Required Services**
   ```bash
   # Start only services you need
   docker-compose up -d postgres redis

   # Run services locally for debugging
   cd services/user-management && python main.py &
   cd services/course-management && python main.py &
   cd services/organization-management && python main.py &
   ```

2. **Use Service Mocks**
   ```python
   # For testing without dependencies
   from unittest.mock import Mock, patch

   @patch('services.course_service.CourseService')
   def test_enrollment(mock_course_service):
       mock_course_service.get_course.return_value = test_course
       # Your test here
   ```

### Database Schema Changes

1. **Create Migration Script**
   ```bash
   # Create new migration file
   touch migrations/$(date +%Y%m%d)_add_course_versions_table.sql
   ```

2. **Write Migration SQL**
   ```sql
   -- migrations/20251127_add_course_versions_table.sql
   BEGIN;

   CREATE TABLE course_versions (
       id SERIAL PRIMARY KEY,
       course_id INTEGER NOT NULL REFERENCES courses(id),
       version_number VARCHAR(20) NOT NULL,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       created_by INTEGER REFERENCES users(id)
   );

   CREATE INDEX idx_course_versions_course_id ON course_versions(course_id);

   COMMIT;
   ```

3. **Test Migration**
   ```bash
   # Run migration
   psql -h localhost -p 5433 -U postgres -d course_creator -f migrations/20251127_add_course_versions_table.sql

   # Verify changes
   psql -h localhost -p 5433 -U postgres -d course_creator -c "\d course_versions"
   ```

4. **Create Rollback Script**
   ```sql
   -- migrations/20251127_rollback_course_versions.sql
   BEGIN;
   DROP TABLE IF EXISTS course_versions;
   COMMIT;
   ```

## Debugging Guide

### Python Service Debugging

#### Using Python Debugger (pdb)

```python
# Add breakpoint in your code
import pdb; pdb.set_trace()

# Or use built-in breakpoint() (Python 3.7+)
breakpoint()

# Common pdb commands:
# n - next line
# s - step into function
# c - continue execution
# p variable_name - print variable
# l - list code around current line
# q - quit debugger
```

#### VS Code Debugging

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "main:app",
        "--reload",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": false,
      "env": {
        "DATABASE_URL": "postgresql://postgres:postgres_password@localhost:5433/course_creator"
      }
    }
  ]
}
```

#### Docker Container Debugging

```bash
# Attach to running container
docker exec -it course-creator-user-management-1 /bin/bash

# View container logs in real-time
docker logs -f course-creator-user-management-1

# Inspect container configuration
docker inspect course-creator-user-management-1

# Run Python shell in container
docker exec -it course-creator-user-management-1 python
```

### Frontend Debugging

#### Chrome DevTools

1. **React DevTools Extension**
   - Install React Developer Tools extension
   - Inspect component hierarchy
   - View props and state
   - Profile component renders

2. **Network Debugging**
   - Open DevTools (F12)
   - Network tab → Filter by XHR
   - Inspect API requests/responses
   - Monitor WebSocket connections

3. **Console Debugging**
   ```typescript
   // Add console logs strategically
   console.log('User data:', user);
   console.table(courses);  // Pretty table format
   console.group('API Call');
   console.log('Request:', requestData);
   console.log('Response:', responseData);
   console.groupEnd();
   ```

#### Redux DevTools

```bash
# Install Redux DevTools extension
# Access: Chrome DevTools → Redux tab

# View state changes
# Time-travel debugging
# Dispatch actions manually
# Export/import state
```

### Database Debugging

```bash
# Connect to PostgreSQL
docker exec -it course-creator-postgres-1 psql -U postgres -d course_creator

# Useful queries
\dt                          -- List tables
\d table_name                -- Describe table
\d+ table_name               -- Detailed table info
\l                           -- List databases
\dn                          -- List schemas
\du                          -- List users

# Query execution plan
EXPLAIN ANALYZE SELECT * FROM courses WHERE organization_id = 1;

# Find slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

# View active connections
SELECT * FROM pg_stat_activity;

# View table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### API Debugging

#### Using FastAPI Swagger UI

```bash
# Access Swagger documentation
https://localhost:8000/docs          # User Management
https://localhost:8001/docs          # Course Generator
https://localhost:8004/docs          # Course Management
https://localhost:8008/docs          # Organization Management

# Test endpoints directly
# View request/response schemas
# Try out authentication flows
```

#### Using curl

```bash
# Test user registration
curl -X POST "https://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User"
  }' \
  --insecure

# Test with authentication
TOKEN="your-jwt-token"
curl -X GET "https://localhost:8000/users/me" \
  -H "Authorization: Bearer $TOKEN" \
  --insecure

# Test course creation
curl -X POST "https://localhost:8004/api/v1/courses" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Course",
    "description": "Test Description",
    "organization_id": 1
  }' \
  --insecure
```

#### Using Postman/Insomnia

1. **Import OpenAPI Spec**
   - Download from `/docs` endpoint
   - Import into Postman/Insomnia
   - Auto-generates all endpoints

2. **Set Up Environment**
   ```json
   {
     "base_url": "https://localhost:8000",
     "token": "{{auth_token}}"
   }
   ```

## Database Management

### Local Database Access

```bash
# Connect via Docker
docker exec -it course-creator-postgres-1 psql -U postgres -d course_creator

# Connect via local client
psql -h localhost -p 5433 -U postgres -d course_creator

# Using environment variable
export PGPASSWORD=postgres_password
psql -h localhost -p 5433 -U postgres -d course_creator
```

### Database Backup and Restore

```bash
# Backup database
docker exec course-creator-postgres-1 pg_dump -U postgres course_creator > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
docker exec -i course-creator-postgres-1 psql -U postgres course_creator < backup_20251127_120000.sql

# Backup specific tables
docker exec course-creator-postgres-1 pg_dump -U postgres -t courses -t enrollments course_creator > courses_backup.sql
```

### Database Reset

```bash
# WARNING: This deletes all data!

# Stop services
docker-compose down

# Remove database volume
docker volume rm course-creator_postgres_data

# Restart and re-initialize
docker-compose up -d postgres
python deploy/setup-database.py
python scripts/setup-dev-data.py
```

### Creating Test Data

```bash
# Run development data setup script
python scripts/setup-dev-data.py

# This creates:
# - 3 organizations
# - 10 users (2 site admins, 3 org admins, 3 instructors, 2 students)
# - 5 courses
# - 20 course enrollments
# - Sample quizzes and feedback
```

## Testing During Development

### Running Tests Incrementally

```bash
# Run specific test file
pytest tests/unit/test_user_service.py -v

# Run specific test class
pytest tests/unit/test_user_service.py::TestUserService -v

# Run specific test method
pytest tests/unit/test_user_service.py::TestUserService::test_create_user -v

# Run tests matching pattern
pytest tests/ -k "user" -v  # All tests with "user" in name

# Run tests with coverage
pytest tests/unit/ --cov=services.user_management --cov-report=html

# Run failed tests only
pytest --lf  # Last failed
pytest --ff  # Failed first, then others
```

### Frontend Testing

```bash
cd frontend-react

# Run tests in watch mode (recommended for development)
npm test

# Run specific test file
npm test -- CourseCard.test.tsx

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

### Test-Driven Development Workflow

```bash
# 1. Write failing test
# tests/unit/test_course_versioning.py
def test_create_course_version():
    course = create_test_course()
    version = course_service.create_version(course.id, "1.1", "Minor updates")
    assert version.version_number == "1.1"

# 2. Run test (should fail - RED)
pytest tests/unit/test_course_versioning.py::test_create_course_version -v

# 3. Implement minimal code to pass
# services/course_management/application/services/course_service.py
def create_version(self, course_id, version_number, notes):
    return CourseVersion(course_id=course_id, version_number=version_number, notes=notes)

# 4. Run test (should pass - GREEN)
pytest tests/unit/test_course_versioning.py::test_create_course_version -v

# 5. Refactor while keeping tests green
```

## Common Development Tasks

### Adding a New API Endpoint

1. **Define Data Models**
   ```python
   # services/course-management/course_management/domain/entities/course_version.py
   from dataclasses import dataclass
   from datetime import datetime

   @dataclass
   class CourseVersion:
       """Domain entity for course version."""
       id: int
       course_id: int
       version_number: str
       notes: str
       created_at: datetime
       created_by: int
   ```

2. **Create Repository**
   ```python
   # services/course-management/course_management/infrastructure/repositories/version_repository.py
   from course_management.domain.entities.course_version import CourseVersion

   class CourseVersionRepository:
       """Repository for course version persistence."""

       async def create_version(self, version: CourseVersion) -> CourseVersion:
           """Create new course version."""
           # Implementation
   ```

3. **Implement Service**
   ```python
   # services/course-management/course_management/application/services/version_service.py
   class CourseVersionService:
       """Service for course version management."""

       def __init__(self, version_repository: CourseVersionRepository):
           self.version_repository = version_repository

       async def create_version(self, course_id: int, version_number: str, notes: str) -> CourseVersion:
           """Create new course version with validation."""
           # Business logic
   ```

4. **Add API Endpoint**
   ```python
   # services/course-management/api/version_endpoints.py
   from fastapi import APIRouter, Depends
   from course_management.application.services.version_service import CourseVersionService

   router = APIRouter(prefix="/api/v1/versions", tags=["versions"])

   @router.post("/")
   async def create_version(
       course_id: int,
       version_number: str,
       notes: str,
       version_service: CourseVersionService = Depends(get_version_service)
   ):
       """Create new course version."""
       version = await version_service.create_version(course_id, version_number, notes)
       return version
   ```

5. **Write Tests**
   ```python
   # tests/unit/test_version_service.py
   class TestVersionService:
       async def test_create_version(self):
           service = CourseVersionService(mock_repository)
           version = await service.create_version(1, "1.1", "Minor updates")
           assert version.version_number == "1.1"
   ```

### Adding Environment Variables

1. **Add to `.cc_env`**
   ```bash
   # New feature configuration
   FEATURE_COURSE_VERSIONING=true
   MAX_VERSIONS_PER_COURSE=10
   ```

2. **Update Docker Compose**
   ```yaml
   # docker-compose.yml
   services:
     course-management:
       environment:
         - FEATURE_COURSE_VERSIONING=${FEATURE_COURSE_VERSIONING}
         - MAX_VERSIONS_PER_COURSE=${MAX_VERSIONS_PER_COURSE}
   ```

3. **Access in Code**
   ```python
   import os

   FEATURE_VERSIONING = os.getenv("FEATURE_COURSE_VERSIONING", "false").lower() == "true"
   MAX_VERSIONS = int(os.getenv("MAX_VERSIONS_PER_COURSE", "5"))
   ```

### Updating Dependencies

#### Python Dependencies

```bash
# Update requirements.txt
pip install package_name==version
pip freeze | grep package_name >> requirements.txt

# Update all packages (carefully!)
pip list --outdated
pip install --upgrade package_name

# Update in virtual environment
source .venv/bin/activate
pip install --upgrade -r requirements.txt
```

#### Node.js Dependencies

```bash
cd frontend-react

# Update specific package
npm install package_name@latest

# Check for outdated packages
npm outdated

# Update all packages (carefully!)
npm update

# Update package.json and package-lock.json
npm install package_name@latest --save
```

## Performance Optimization

### Python Service Optimization

#### Database Query Optimization

```python
# ❌ BAD - N+1 query problem
courses = await course_repo.get_all()
for course in courses:
    instructor = await user_repo.get_by_id(course.instructor_id)  # N queries

# ✅ GOOD - Single query with join
courses_with_instructors = await course_repo.get_all_with_instructors()  # 1 query
```

#### Caching with Redis

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

async def get_course_with_cache(course_id: int):
    """Get course with Redis caching."""
    cache_key = f"course:{course_id}"

    # Try cache first
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Fetch from database
    course = await course_repo.get_by_id(course_id)

    # Store in cache (expire in 5 minutes)
    redis_client.setex(cache_key, 300, json.dumps(course.dict()))

    return course
```

### Frontend Optimization

#### React Performance

```typescript
// Use React.memo for expensive components
export const CourseCard = React.memo(({ course }: CourseCardProps) => {
  return <div>{course.title}</div>;
});

// Use useMemo for expensive calculations
const sortedCourses = useMemo(
  () => courses.sort((a, b) => a.title.localeCompare(b.title)),
  [courses]
);

// Use useCallback for event handlers
const handleEnroll = useCallback(
  (courseId: string) => {
    enrollInCourse(courseId);
  },
  [enrollInCourse]
);
```

#### Code Splitting

```typescript
// Lazy load routes
import { lazy, Suspense } from 'react';

const StudentDashboard = lazy(() => import('./features/dashboard/pages/StudentDashboard'));
const InstructorDashboard = lazy(() => import('./features/dashboard/pages/InstructorDashboard'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/student" element={<StudentDashboard />} />
        <Route path="/instructor" element={<InstructorDashboard />} />
      </Routes>
    </Suspense>
  );
}
```

## Troubleshooting

### Service Won't Start

```bash
# Check Docker container logs
docker logs course-creator-user-management-1

# Check for port conflicts
lsof -i :8000  # On macOS/Linux
netstat -ano | findstr :8000  # On Windows

# Rebuild container
docker-compose up -d --build --force-recreate user-management

# Check environment variables
docker exec course-creator-user-management-1 env | grep DATABASE
```

### Database Connection Issues

```bash
# Verify PostgreSQL is running
docker ps | grep postgres

# Check PostgreSQL logs
docker logs course-creator-postgres-1

# Test connection
docker exec -it course-creator-postgres-1 psql -U postgres -c "SELECT 1"

# Check database exists
docker exec -it course-creator-postgres-1 psql -U postgres -c "\l"
```

### Import Errors in Python

```bash
# Verify PYTHONPATH
echo $PYTHONPATH

# Check if package is installed
pip list | grep package_name

# Reinstall in development mode
pip install -e services/user-management/

# Check for circular imports
python -c "import services.user_management.main"
```

### Frontend Build Issues

```bash
# Clear cache and reinstall
cd frontend-react
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run type-check

# Build with verbose output
npm run build -- --debug
```

### Docker Compose Issues

```bash
# Validate compose file
docker-compose config

# Rebuild all images
docker-compose build --no-cache

# Clean up Docker resources
docker system prune -a --volumes  # WARNING: Removes all unused data

# Check Docker disk usage
docker system df
```

## Additional Resources

- **[Architecture Overview](ARCHITECTURE.md)** - System design and patterns
- **[API Documentation](API_OVERVIEW.md)** - Service endpoints
- **[Contributing Guide](../CONTRIBUTING.md)** - Contribution workflow
- **[Testing Strategy](../claude.md/08-testing-strategy.md)** - Comprehensive testing

---

**Happy Developing!** If you encounter issues not covered here, check the [Troubleshooting Guide](../claude.md/10-troubleshooting.md) or create an issue.
