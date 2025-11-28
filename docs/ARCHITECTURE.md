# Architecture Overview

This document provides a comprehensive overview of the Course Creator Platform architecture, including microservices structure, data access patterns, design decisions, and architectural patterns.

## Table of Contents

- [System Architecture](#system-architecture)
- [Microservices Overview](#microservices-overview)
- [Clean Architecture Pattern](#clean-architecture-pattern)
- [Data Access Layer (DAO Pattern)](#data-access-layer-dao-pattern)
- [Service Communication](#service-communication)
- [Database Architecture](#database-architecture)
- [Security Architecture](#security-architecture)
- [Container Architecture](#container-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Key Design Decisions](#key-design-decisions)
- [Scalability Considerations](#scalability-considerations)

## System Architecture

The Course Creator Platform follows a **microservices architecture** with clear service boundaries, independent deployment, and technology flexibility.

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                              │
│  ┌──────────────────────┐           ┌──────────────────────┐       │
│  │   React Frontend     │           │   Legacy Frontend    │       │
│  │   (Vite + TypeScript)│           │   (HTML/CSS/JS)      │       │
│  │   Port: 5173         │           │   Port: 3000 (HTTPS) │       │
│  └──────────────────────┘           └──────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                            │  HTTPS/REST API
┌─────────────────────────────────────────────────────────────────────┐
│                      API Gateway / Load Balancer                    │
│                     (NGINX - Port 3000/3001)                        │
└─────────────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────────────┐
│                       Microservices Layer                           │
│                                                                      │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
│  │ User Mgmt     │  │ Course Gen    │  │ Course Mgmt   │          │
│  │ Port: 8000    │  │ Port: 8001    │  │ Port: 8004    │          │
│  └───────────────┘  └───────────────┘  └───────────────┘          │
│                                                                      │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
│  │ Content Mgmt  │  │ Analytics     │  │ Lab Manager   │          │
│  │ Port: 8005    │  │ Port: 8007    │  │ Port: 8006    │          │
│  └───────────────┘  └───────────────┘  └───────────────┘          │
│                                                                      │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
│  │ Org Mgmt      │  │ RAG Service   │  │ NLP Service   │          │
│  │ Port: 8008    │  │ Port: 8009    │  │ Port: 8002    │          │
│  └───────────────┘  └───────────────┘  └───────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────────────┐
│                        Data Layer                                   │
│                                                                      │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
│  │ PostgreSQL    │  │ Redis Cache   │  │ ChromaDB      │          │
│  │ Port: 5433    │  │ Internal      │  │ (Vector DB)   │          │
│  └───────────────┘  └───────────────┘  └───────────────┘          │
│                                                                      │
│  ┌───────────────────────────────────────────────────┐             │
│  │          Docker Volume Storage                     │             │
│  │  - Student Lab Containers                         │             │
│  │  - Course Content Files                           │             │
│  │  - User Uploads                                   │             │
│  └───────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

### Architecture Principles

1. **Service Independence**: Each microservice can be developed, deployed, and scaled independently
2. **Single Responsibility**: Each service has a well-defined bounded context
3. **Data Isolation**: Services own their data and expose it through APIs only
4. **Technology Flexibility**: Services can use different tech stacks (all Python/FastAPI currently)
5. **Failure Isolation**: Service failures don't cascade to other services
6. **Scalability**: Individual services can be scaled based on demand

## Microservices Overview

### 1. User Management Service (Port 8000)

**Responsibility**: Authentication, user profiles, session management, password management

**Technology Stack**:
- FastAPI (async web framework)
- PostgreSQL (user data, sessions)
- Redis (session caching)
- JWT (authentication tokens)
- bcrypt (password hashing)

**Key Features**:
- User registration and authentication
- JWT token generation and validation
- Session management with Redis
- Password change functionality
- Role-based access control (RBAC) integration
- Multi-tenant user isolation by organization

**API Endpoints**:
```
POST   /auth/register           # User registration
POST   /auth/login              # User login
POST   /auth/logout             # User logout
GET    /auth/me                 # Get current user
POST   /auth/password/change    # Change password
POST   /auth/refresh            # Refresh JWT token
GET    /users/{id}              # Get user by ID
PUT    /users/{id}              # Update user
DELETE /users/{id}              # Delete user
```

**Database Tables**:
- `users` - User accounts and profiles
- `sessions` - Active user sessions
- `user_roles` - User role assignments
- `audit_logs` - User activity tracking

### 2. Course Generator Service (Port 8001)

**Responsibility**: AI-powered course content generation using LLMs

**Technology Stack**:
- FastAPI
- Anthropic Claude API / OpenAI API
- ChromaDB (RAG vector database)
- PostgreSQL (generated content storage)

**Key Features**:
- AI-powered syllabus generation
- Slide content generation from topics
- Quiz question generation with multiple formats
- Lab exercise creation with test cases
- RAG-enhanced content using knowledge base
- Progressive learning from previous generations

**API Endpoints**:
```
POST   /generate/syllabus       # Generate course syllabus
POST   /generate/slides         # Generate slide content
POST   /generate/quiz           # Generate quiz questions
POST   /generate/lab            # Generate lab exercises
POST   /generate/regenerate     # Regenerate specific content
GET    /generate/history        # Generation history
```

**RAG Integration**:
- Queries knowledge base for relevant educational patterns
- Learns from successful content generations
- Improves quality through accumulated experience

### 3. Course Management Service (Port 8004)

**Responsibility**: Course lifecycle, enrollment, versioning, feedback

**Technology Stack**:
- FastAPI
- PostgreSQL (course data)
- Redis (caching)

**Key Features**:
- Course CRUD operations
- Course versioning (major/minor versions)
- Student enrollment management
- Course instance management
- Bi-directional feedback system
- Quiz publication management
- Prerequisites and learning paths

**API Endpoints**:
```
POST   /api/v1/courses                    # Create course
GET    /api/v1/courses                    # List courses
GET    /api/v1/courses/{id}               # Get course details
PUT    /api/v1/courses/{id}               # Update course
DELETE /api/v1/courses/{id}               # Delete course
POST   /api/v1/courses/{id}/enroll        # Enroll student
POST   /api/v1/courses/{id}/versions      # Create version
GET    /api/v1/courses/{id}/feedback      # Get course feedback
POST   /feedback/course                   # Submit course feedback
POST   /feedback/student                  # Submit student assessment
```

**Database Tables**:
- `courses` - Course definitions
- `course_versions` - Course version tracking
- `course_instances` - Specific course sessions
- `enrollments` - Student enrollments
- `course_feedback` - Student→Course feedback
- `student_feedback` - Instructor→Student feedback

### 4. Content Management Service (Port 8005)

**Responsibility**: File storage, content versioning, multi-format export

**Technology Stack**:
- FastAPI
- File system storage
- PostgreSQL (metadata)
- Pillow (image processing)
- ReportLab (PDF generation)

**Key Features**:
- File upload/download
- Content versioning
- Multi-format export (PDF, SCORM, HTML)
- Image optimization
- Virus scanning integration
- Access control by organization

**API Endpoints**:
```
POST   /api/v1/files/upload              # Upload file
GET    /api/v1/files/{id}                # Download file
DELETE /api/v1/files/{id}                # Delete file
POST   /api/v1/export/pdf                # Export as PDF
POST   /api/v1/export/scorm              # Export as SCORM
GET    /api/v1/files/course/{course_id}  # List course files
```

### 5. Lab Manager Service (Port 8006)

**Responsibility**: Docker container management for student lab environments

**Technology Stack**:
- FastAPI
- Docker SDK for Python
- Docker-in-Docker (DinD)
- VSCode Server, JupyterLab (IDEs)

**Key Features**:
- Individual Docker containers per student
- Multi-IDE support (Terminal, VSCode, Jupyter, IntelliJ)
- Dynamic image building with custom packages
- Persistent storage across sessions
- Resource limits (CPU/memory)
- Automatic lifecycle management
- Health monitoring

**API Endpoints**:
```
POST   /labs                      # Create lab container
POST   /labs/student              # Get or create student lab
GET    /labs                      # List all labs
GET    /labs/{id}                 # Get lab details
POST   /labs/{id}/pause           # Pause lab
POST   /labs/{id}/resume          # Resume lab
DELETE /labs/{id}                 # Stop and remove lab
GET    /labs/{id}/ides            # Get available IDEs
POST   /labs/{id}/ide/switch      # Switch IDE
```

**Container Architecture**:
```
Student Lab Container (Ubuntu 20.04)
├── Terminal (xterm.js) - Port 8080
├── VSCode Server - Port 8081
├── JupyterLab - Port 8082
├── IntelliJ (optional) - Port 8083
└── Persistent Volume: /home/student/work
```

### 6. Analytics Service (Port 8007)

**Responsibility**: Student analytics, progress tracking, reporting

**Technology Stack**:
- FastAPI
- PostgreSQL (analytics data)
- Pandas (data processing)
- Matplotlib/Plotly (visualization)
- ReportLab (PDF reports)

**Key Features**:
- Real-time analytics calculations
- Student progress tracking
- Course completion rates
- Quiz performance metrics
- Video watch time tracking
- Engagement scoring
- PDF report generation
- WebSocket for real-time updates

**API Endpoints**:
```
GET    /api/v1/analytics/student/{id}           # Student analytics
GET    /api/v1/analytics/course/{id}            # Course analytics
GET    /api/v1/analytics/organization/{id}      # Organization analytics
GET    /api/v1/analytics/instructor/{id}        # Instructor analytics
POST   /api/v1/analytics/report                 # Generate report
WS     /ws/analytics                            # WebSocket updates
```

**Metrics Calculated**:
- Course completion percentage
- Time spent on content
- Quiz scores and attempts
- Lab exercise completion
- Engagement scores
- At-risk student identification

### 7. Organization Management Service (Port 8008)

**Responsibility**: Multi-tenant organization management, RBAC, tracks

**Technology Stack**:
- FastAPI
- PostgreSQL (organization data)
- MS Teams/Zoom APIs (meeting integration)

**Key Features**:
- Organization CRUD operations
- Member management
- Learning track creation
- Meeting room integration (Teams/Zoom)
- Organization data isolation
- Admin account creation
- Professional email validation

**API Endpoints**:
```
POST   /api/v1/organizations                    # Create organization
GET    /api/v1/organizations                    # List organizations
GET    /api/v1/organizations/{id}               # Get organization
PUT    /api/v1/organizations/{id}               # Update organization
DELETE /api/v1/organizations/{id}               # Delete organization
POST   /api/v1/organizations/{id}/members       # Add member
GET    /api/v1/organizations/{id}/members       # List members
POST   /api/v1/organizations/{id}/tracks        # Create track
GET    /api/v1/organizations/{id}/meeting-rooms # List meeting rooms
```

**Database Tables**:
- `organizations` - Organization definitions
- `organization_members` - Member associations
- `learning_tracks` - Track definitions
- `track_courses` - Track-course associations
- `meeting_rooms` - Virtual meeting spaces

### 8. RAG Service (Port 8009)

**Responsibility**: Retrieval-Augmented Generation for AI enhancement

**Technology Stack**:
- FastAPI
- ChromaDB (vector database)
- Sentence Transformers (embeddings)
- PostgreSQL (metadata)

**Key Features**:
- Vector database management
- Document embedding and indexing
- Semantic search
- Knowledge base querying
- Progressive learning
- Quality scoring

**API Endpoints**:
```
POST   /api/v1/rag/add-document   # Add to knowledge base
POST   /api/v1/rag/query          # Query for relevant context
POST   /api/v1/rag/learn          # Learn from interaction
GET    /api/v1/rag/stats          # Usage statistics
```

**ChromaDB Collections**:
- `content_generation` - Educational content patterns
- `lab_assistance` - Programming help knowledge
- `user_interactions` - Successful interaction patterns
- `course_knowledge` - Course-specific knowledge

### 9. NLP Preprocessing Service (Port 8002)

**Responsibility**: Natural language processing for AI assistant

**Technology Stack**:
- FastAPI
- spaCy (NLP)
- NLTK (text processing)

**Key Features**:
- Text tokenization
- Entity recognition
- Sentiment analysis
- Intent classification
- Query understanding

## Clean Architecture Pattern

All microservices follow **Clean Architecture** (Hexagonal Architecture) with clear layer separation.

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer                                │
│  - FastAPI endpoints                                         │
│  - Request/response models (Pydantic)                        │
│  - HTTP exception handling                                   │
│  - Dependency injection                                      │
└─────────────────────────────────────────────────────────────┘
                         │ calls
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                           │
│  - Business logic services                                   │
│  - Use case implementations                                  │
│  - Cross-cutting concerns (logging, validation)              │
│  - Service orchestration                                     │
└─────────────────────────────────────────────────────────────┘
                         │ uses
┌─────────────────────────────────────────────────────────────┐
│                    Domain Layer                              │
│  - Business entities (dataclasses)                           │
│  - Domain exceptions                                         │
│  - Business rules and logic                                  │
│  - Repository interfaces (abstractions)                      │
└─────────────────────────────────────────────────────────────┘
                         │ implemented by
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer                          │
│  - Repository implementations (PostgreSQL)                   │
│  - External service integrations                             │
│  - Database connections                                      │
│  - File system operations                                    │
└─────────────────────────────────────────────────────────────┘
```

### Service-Specific Namespacing

**CRITICAL**: All services use service-specific namespaces to prevent import collisions.

**Directory Structure**:
```
services/user-management/
├── user_management/              # ← Service namespace package
│   ├── __init__.py
│   ├── domain/                   # ← Domain layer
│   │   ├── entities/
│   │   │   └── user.py
│   │   ├── exceptions/
│   │   │   └── user_exceptions.py
│   │   └── interfaces/
│   │       └── user_repository.py
│   ├── application/              # ← Application layer
│   │   └── services/
│   │       ├── user_service.py
│   │       └── authentication_service.py
│   └── infrastructure/           # ← Infrastructure layer
│       └── repositories/
│           └── postgresql_user_repository.py
├── api/                          # ← API layer (not in namespace)
│   └── user_endpoints.py
├── data_access/                  # ← DAOs (not in namespace)
│   └── user_dao.py
└── main.py                       # ← Service entry point
```

**Import Examples**:
```python
# Domain layer imports
from user_management.domain.entities.user import User
from user_management.domain.exceptions.user_exceptions import UserNotFoundException

# Application layer imports
from user_management.application.services.user_service import UserService
from user_management.application.services.authentication_service import AuthenticationService

# Infrastructure layer imports
from user_management.infrastructure.repositories.postgresql_user_repository import PostgreSQLUserRepository

# ❌ NEVER use relative imports
# from ..domain.entities.user import User  # WRONG
# from ...application.services.user_service import UserService  # WRONG
```

### Example: User Creation Flow

```python
# 1. API Layer (api/user_endpoints.py)
from fastapi import APIRouter, Depends, HTTPException
from user_management.application.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/")
async def create_user(
    user_data: UserCreateRequest,
    user_service: UserService = Depends(get_user_service)
):
    """API endpoint for user creation."""
    try:
        user = await user_service.create_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        return user
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=409, detail=str(e))

# 2. Application Layer (application/services/user_service.py)
from user_management.domain.entities.user import User
from user_management.domain.interfaces.user_repository import IUserRepository
from user_management.domain.exceptions.user_exceptions import UserAlreadyExistsException

class UserService:
    """Business logic for user management."""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    async def create_user(self, email: str, password: str, full_name: str) -> User:
        """
        Create new user with validation and password hashing.

        Business Rules:
        - Email must be unique
        - Password must meet strength requirements
        - Professional email for organization members
        """
        # Check if user exists
        existing = await self.user_repository.find_by_email(email)
        if existing:
            raise UserAlreadyExistsException(f"User with email {email} already exists")

        # Validate password strength
        self._validate_password_strength(password)

        # Hash password
        hashed_password = self._hash_password(password)

        # Create user entity
        user = User(
            email=email,
            password_hash=hashed_password,
            full_name=full_name
        )

        # Persist user
        return await self.user_repository.create(user)

# 3. Domain Layer (domain/entities/user.py)
from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    """Domain entity representing a user."""
    id: int | None = None
    email: str
    password_hash: str
    full_name: str
    role: str = "student"
    organization_id: int | None = None
    created_at: datetime | None = None
    is_active: bool = True

# 4. Infrastructure Layer (infrastructure/repositories/postgresql_user_repository.py)
from user_management.domain.entities.user import User
from user_management.domain.interfaces.user_repository import IUserRepository
import asyncpg

class PostgreSQLUserRepository(IUserRepository):
    """PostgreSQL implementation of user repository."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def create(self, user: User) -> User:
        """Persist user to PostgreSQL."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (email, password_hash, full_name, role, organization_id)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, email, full_name, role, organization_id, created_at, is_active
                """,
                user.email, user.password_hash, user.full_name, user.role, user.organization_id
            )
            return User(**dict(row))

    async def find_by_email(self, email: str) -> User | None:
        """Find user by email."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1",
                email
            )
            return User(**dict(row)) if row else None
```

## Data Access Layer (DAO Pattern)

### DAO vs Repository Pattern

The platform uses **both patterns** for different purposes:

**Data Access Objects (DAOs)**:
- Located in `data_access/` directory (not in service namespace)
- Direct database operations
- SQL-focused, minimal business logic
- Shared across services if needed
- Example: `user_dao.py`, `course_dao.py`

**Repository Pattern**:
- Located in `infrastructure/repositories/` (within service namespace)
- Implements domain interfaces
- Business-oriented operations
- Service-specific
- Example: `postgresql_user_repository.py`

### DAO Example

```python
# services/course-management/data_access/course_dao.py
"""
Data Access Object for course database operations.

Direct SQL operations without business logic.
"""
import asyncpg
from typing import List, Optional, Dict, Any

class CourseDAO:
    """Direct database operations for courses."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def insert_course(self, course_data: Dict[str, Any]) -> int:
        """Insert course record and return ID."""
        async with self.db_pool.acquire() as conn:
            course_id = await conn.fetchval(
                """
                INSERT INTO courses (
                    title, description, organization_id, instructor_id,
                    created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, NOW(), NOW())
                RETURNING id
                """,
                course_data['title'],
                course_data['description'],
                course_data['organization_id'],
                course_data['instructor_id']
            )
            return course_id

    async def get_course_by_id(self, course_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve course by ID."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM courses WHERE id = $1",
                course_id
            )
            return dict(row) if row else None

    async def list_courses_by_organization(
        self,
        organization_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List courses for an organization with pagination."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM courses
                WHERE organization_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                organization_id, limit, offset
            )
            return [dict(row) for row in rows]

    async def update_course(self, course_id: int, updates: Dict[str, Any]) -> bool:
        """Update course fields."""
        set_clauses = ", ".join([f"{key} = ${i+2}" for i, key in enumerate(updates.keys())])
        query = f"UPDATE courses SET {set_clauses}, updated_at = NOW() WHERE id = $1"

        async with self.db_pool.acquire() as conn:
            result = await conn.execute(query, course_id, *updates.values())
            return result == "UPDATE 1"

    async def delete_course(self, course_id: int) -> bool:
        """Delete course record."""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM courses WHERE id = $1",
                course_id
            )
            return result == "DELETE 1"

    async def get_courses_with_instructors(
        self,
        organization_id: int
    ) -> List[Dict[str, Any]]:
        """Get courses with instructor details (JOIN query)."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    c.*,
                    u.full_name as instructor_name,
                    u.email as instructor_email
                FROM courses c
                JOIN users u ON c.instructor_id = u.id
                WHERE c.organization_id = $1
                ORDER BY c.created_at DESC
                """,
                organization_id
            )
            return [dict(row) for row in rows]
```

### Database Connection Pool Management

```python
# services/user-management/main.py
import asyncpg
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Global database pool
db_pool: asyncpg.Pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global db_pool

    # Startup: Create connection pool
    db_pool = await asyncpg.create_pool(
        host=os.getenv("DB_HOST", "postgres"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "course_creator"),
        min_size=5,
        max_size=20,
        command_timeout=60
    )

    yield

    # Shutdown: Close pool
    await db_pool.close()

app = FastAPI(lifespan=lifespan)

def get_db_pool() -> asyncpg.Pool:
    """Dependency injection for database pool."""
    return db_pool
```

## Service Communication

### HTTP/REST Communication

Services communicate via REST APIs with **HTTPS only** (no HTTP in production).

```python
# Example: Organization service calling User Management service
import httpx

class OrganizationService:
    """Organization management with user service integration."""

    async def create_organization_with_admin(
        self,
        org_name: str,
        admin_email: str,
        admin_password: str
    ):
        """Create organization and admin user account."""

        # 1. Create organization
        org = await self.org_repository.create(org_name)

        # 2. Call User Management service to create admin user
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                "https://user-management:8000/auth/register",
                json={
                    "email": admin_email,
                    "password": admin_password,
                    "full_name": f"{org_name} Administrator",
                    "role": "org_admin",
                    "organization_id": org.id
                },
                timeout=30.0
            )

            if response.status_code != 200:
                # Rollback organization creation
                await self.org_repository.delete(org.id)
                raise Exception(f"Failed to create admin user: {response.text}")

            admin_user = response.json()

        return org, admin_user
```

### Error Handling in Service Communication

```python
from fastapi import HTTPException
import httpx

async def call_external_service(url: str, data: dict):
    """Call external service with comprehensive error handling."""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            response = await client.post(url, json=data)

            # Handle HTTP errors
            if response.status_code >= 400:
                error_detail = response.json().get("detail", "Unknown error")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"External service error: {error_detail}"
                )

            return response.json()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="External service timeout"
        )
    except httpx.NetworkError:
        raise HTTPException(
            status_code=503,
            detail="External service unavailable"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error calling external service: {str(e)}"
        )
```

## Database Architecture

### PostgreSQL Schema Design

**Multi-Tenant Schema** with organization-based isolation:

```sql
-- Organizations (root entity for multi-tenancy)
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    address TEXT,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Users (scoped to organizations)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    role VARCHAR(50) NOT NULL,
    organization_id INTEGER REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Courses (scoped to organizations)
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    instructor_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_published BOOLEAN DEFAULT FALSE
);

-- Indexes for performance
CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_courses_organization_id ON courses(organization_id);
CREATE INDEX idx_courses_instructor_id ON courses(instructor_id);
```

### Data Isolation

**CRITICAL**: All queries must enforce organization-based isolation:

```python
# ✅ CORRECT - Organization isolation enforced
async def get_courses(organization_id: int) -> List[Course]:
    """Get courses for specific organization only."""
    return await course_dao.list_courses_by_organization(organization_id)

# ❌ WRONG - No organization filtering (security vulnerability)
async def get_courses() -> List[Course]:
    """Get all courses - WRONG! Leaks cross-organization data."""
    return await course_dao.list_all_courses()  # Don't do this!
```

### Database Connection Patterns

```python
# Pattern 1: Connection Pool (recommended for FastAPI)
db_pool = await asyncpg.create_pool(...)

async with db_pool.acquire() as conn:
    result = await conn.fetch("SELECT * FROM courses")

# Pattern 2: Context Manager
async with asyncpg.create_pool(...) as pool:
    async with pool.acquire() as conn:
        result = await conn.fetch("SELECT * FROM users")

# Pattern 3: Transaction
async with conn.transaction():
    await conn.execute("INSERT INTO courses ...")
    await conn.execute("INSERT INTO enrollments ...")
    # Automatically commits on success, rolls back on exception
```

## Security Architecture

### Authentication Flow

```
┌─────────┐                ┌──────────────────┐              ┌────────────┐
│  Client │                │ User Management  │              │ PostgreSQL │
└─────────┘                └──────────────────┘              └────────────┘
     │                              │                                │
     │  POST /auth/login            │                                │
     ├─────────────────────────────>│                                │
     │  { email, password }         │                                │
     │                              │                                │
     │                              │  Query user by email           │
     │                              ├───────────────────────────────>│
     │                              │                                │
     │                              │  User record                   │
     │                              │<───────────────────────────────┤
     │                              │                                │
     │                              │  Verify password (bcrypt)      │
     │                              │                                │
     │                              │  Generate JWT token            │
     │                              │  (expires in 60 minutes)       │
     │                              │                                │
     │  200 OK                      │                                │
     │  { token, user }             │                                │
     │<─────────────────────────────┤                                │
     │                              │                                │
     │  GET /courses                │                                │
     │  Authorization: Bearer {jwt} │                                │
     ├─────────────────────────────>│                                │
     │                              │                                │
     │                              │  Verify JWT signature          │
     │                              │  Extract user_id, org_id       │
     │                              │                                │
     │                              │  Query courses (org isolated)  │
     │                              ├───────────────────────────────>│
     │                              │                                │
     │  200 OK                      │                                │
     │  { courses }                 │                                │
     │<─────────────────────────────┤                                │
```

### JWT Token Structure

```python
{
    "sub": "123",               # User ID
    "email": "user@example.com",
    "role": "instructor",
    "organization_id": 5,
    "exp": 1700000000,          # Expiration timestamp
    "iat": 1699996400           # Issued at timestamp
}
```

### Role-Based Access Control (RBAC)

```python
from fastapi import Depends, HTTPException
from typing import List

def require_roles(allowed_roles: List[str]):
    """Dependency for role-based access control."""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker

# Usage in endpoints
@router.post("/courses")
async def create_course(
    course_data: CourseCreateRequest,
    current_user: User = Depends(require_roles(["instructor", "org_admin"]))
):
    """Only instructors and org admins can create courses."""
    # Implementation
```

## Container Architecture

### Docker-in-Docker for Lab Containers

The Lab Manager service uses **Docker-in-Docker (DinD)** to create isolated student lab environments:

```yaml
# docker-compose.yml
services:
  lab-manager:
    image: course-creator-lab-manager
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Docker socket
      - lab_volumes:/var/lib/docker/volumes        # Persistent storage
    environment:
      - DOCKER_HOST=unix:///var/run/docker.sock
```

### Student Lab Container Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                  Lab Container Lifecycle                     │
└─────────────────────────────────────────────────────────────┘

Student Login
     │
     ▼
┌─────────────────┐
│ Check Existing  │──Yes──> Resume Container
│   Container     │
└─────────────────┘
     │ No
     ▼
┌─────────────────┐
│ Build Custom    │  (with student-specific packages)
│ Docker Image    │
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Create Container│
│ - Terminal      │  Port 8080
│ - VSCode        │  Port 8081
│ - JupyterLab    │  Port 8082
│ - Persistent    │  /home/student/work
│   Volume        │
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Student Works   │
│ in Lab          │
└─────────────────┘
     │
     ▼
Student Logout
     │
     ▼
┌─────────────────┐
│ Pause Container │  (saves state, reduces resources)
└─────────────────┘
     │
     ▼
After 7 days inactive
     │
     ▼
┌─────────────────┐
│ Archive & Stop  │  (backup work, remove container)
└─────────────────┘
```

## Frontend Architecture

### React Component Structure

```
frontend-react/src/
├── features/                    # Feature-based organization
│   ├── auth/
│   │   ├── components/
│   │   ├── pages/
│   │   └── hooks/
│   ├── courses/
│   │   ├── components/
│   │   │   ├── CourseCard/
│   │   │   ├── CourseList/
│   │   │   └── EnrollButton/
│   │   ├── pages/
│   │   │   ├── CourseListPage.tsx
│   │   │   └── CourseDetailPage.tsx
│   │   └── hooks/
│   │       └── useCourses.ts
│   └── dashboard/
├── components/                  # Shared components
│   ├── ui/                     # UI primitives
│   ├── layout/
│   └── routing/
├── hooks/                       # Shared hooks
├── services/                    # API clients
│   ├── authService.ts
│   ├── courseService.ts
│   └── organizationService.ts
├── store/                       # Redux store
│   ├── index.ts
│   └── slices/
│       ├── authSlice.ts
│       └── courseSlice.ts
└── utils/                       # Utility functions
```

### State Management Strategy

```typescript
// Global State (Redux): Auth, user preferences
const authSlice = createSlice({
  name: 'auth',
  initialState: { user: null, token: null },
  reducers: { /* ... */ }
});

// Server State (React Query): API data
const { data: courses } = useQuery(['courses'], fetchCourses);

// Local State (useState): UI state
const [isModalOpen, setIsModalOpen] = useState(false);

// URL State (React Router): Navigation
const [searchParams] = useSearchParams();
const page = searchParams.get('page') ?? '1';
```

## Key Design Decisions

### 1. Microservices vs Monolith

**Decision**: Microservices architecture

**Rationale**:
- Independent scaling of compute-intensive services (AI generation, lab management)
- Technology flexibility for specialized services
- Team independence for parallel development
- Fault isolation (one service failure doesn't bring down platform)

**Trade-offs**:
- Increased operational complexity
- Distributed system challenges (network latency, data consistency)
- More complex debugging and testing

### 2. Clean Architecture with Service Namespaces

**Decision**: Clean Architecture with service-specific Python namespaces

**Rationale**:
- Prevents import collision between services
- Clear dependency direction (outer layers depend on inner)
- Domain logic independent of frameworks and databases
- Testability through dependency inversion

**Implementation**:
- Service namespace prevents `from domain.entities` conflicts
- Repository pattern for data access abstraction
- Domain entities are framework-agnostic dataclasses

### 3. PostgreSQL for All Services

**Decision**: Shared PostgreSQL database with schema isolation

**Rationale**:
- ACID transactions for data consistency
- Powerful query capabilities (JOINs, aggregations)
- Mature tooling and ecosystem
- Multi-tenancy support with organization_id

**Trade-offs**:
- Potential bottleneck if not properly scaled
- Schema changes require coordination
- Not ideal for unstructured data (using ChromaDB for vectors)

### 4. Docker-in-Docker for Labs

**Decision**: Docker-in-Docker for student lab containers

**Rationale**:
- Complete isolation between student environments
- Persistent storage for student work
- Multi-IDE support (Terminal, VSCode, Jupyter)
- Resource limits to prevent abuse

**Trade-offs**:
- Increased resource usage
- Security considerations (Docker socket access)
- Complexity in container lifecycle management

### 5. JWT for Authentication

**Decision**: JWT tokens for stateless authentication

**Rationale**:
- Stateless (no server-side session storage)
- Scalable across multiple service instances
- Contains user metadata (role, organization)
- Industry standard with good library support

**Trade-offs**:
- Cannot revoke tokens before expiration
- Larger payload than session IDs
- Need careful key management

### 6. FastAPI for All Services

**Decision**: FastAPI for all microservices

**Rationale**:
- Async/await support for high concurrency
- Automatic OpenAPI documentation
- Type hints and Pydantic validation
- High performance (comparable to Node.js)

**Benefits**:
- Consistent codebase across services
- Easy onboarding for developers
- Built-in API documentation

## Scalability Considerations

### Horizontal Scaling

**Services that scale independently**:
- Lab Manager (most resource-intensive)
- Course Generator (compute-intensive AI operations)
- Analytics (complex calculations)

```yaml
# Scale specific services
docker-compose up -d --scale lab-manager=3 --scale course-generator=2
```

### Database Scaling

**Current**: Single PostgreSQL instance
**Future**: Read replicas for analytics queries

```
┌──────────────┐
│   Primary    │◄─────── Writes (all services)
│  PostgreSQL  │
└──────────────┘
        │
        │ Replication
        ▼
┌──────────────┐
│  Read Replica│◄─────── Reads (analytics service)
│  PostgreSQL  │
└──────────────┘
```

### Caching Strategy

**Redis for**:
- User sessions
- Frequently accessed course data
- API rate limiting
- Real-time analytics calculations

**Pattern**:
```python
# Cache-aside pattern
async def get_course(course_id: int):
    # 1. Check cache
    cached = redis_client.get(f"course:{course_id}")
    if cached:
        return json.loads(cached)

    # 2. Fetch from database
    course = await course_dao.get_course_by_id(course_id)

    # 3. Store in cache
    redis_client.setex(f"course:{course_id}", 300, json.dumps(course))

    return course
```

### Load Balancing

**NGINX** handles load balancing for frontend and API gateway:

```nginx
upstream backend_services {
    server user-management:8000;
    server course-generator:8001;
    server course-management:8004;
}

server {
    listen 443 ssl;
    location /api/ {
        proxy_pass https://backend_services;
        proxy_next_upstream error timeout http_502;
    }
}
```

---

**For more information**:
- [Development Guide](DEVELOPMENT.md) - Local setup and debugging
- [API Documentation](API_OVERVIEW.md) - Service endpoints
- [Contributing Guide](../CONTRIBUTING.md) - Contribution workflow
