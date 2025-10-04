# Course Creator Platform - System Architecture

> **Comprehensive technical architecture documentation for the Course Creator Platform**

**Version**: 3.1.0
**Last Updated**: 2025-10-04
**Audience**: Architects, Senior Engineers, Technical Leaders

---

## Table of Contents

- [Overview](#overview)
- [System Design](#system-design)
- [Microservices Architecture](#microservices-architecture)
- [Data Architecture](#data-architecture)
- [Security Architecture](#security-architecture)
- [Lab Container System](#lab-container-system)
- [Frontend Architecture](#frontend-architecture)
- [Integration Patterns](#integration-patterns)
- [Scalability & Performance](#scalability--performance)
- [Design Decisions](#design-decisions)

---

## Overview

### Architecture Principles

The Course Creator Platform is built on the following architectural principles:

1. **Microservices Architecture**: Independent, loosely-coupled services
2. **Domain-Driven Design**: Services organized around business domains
3. **Event-Driven Communication**: Asynchronous messaging where appropriate
4. **API-First Design**: Well-defined REST APIs for all services
5. **Container-First**: Docker-based deployment and orchestration
6. **Security by Design**: Authentication, authorization, and encryption at all layers
7. **Observability**: Comprehensive logging, monitoring, and tracing

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                           Client Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │   Browser    │  │  Mobile App  │  │   Desktop    │                 │
│  │   (HTML/JS)  │  │   (Future)   │  │   (Future)   │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Load Balancer / CDN                              │
│                         (Nginx / Cloudflare)                            │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      API Gateway / Reverse Proxy                        │
│                            (Nginx)                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  - SSL/TLS Termination                                          │   │
│  │  - Request Routing                                              │   │
│  │  - Rate Limiting                                                │   │
│  │  - CORS Headers                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Application Layer                                │
│                      (Microservices - FastAPI)                          │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │    User     │  │   Course    │  │   Course    │  │   Content   │  │
│  │ Management  │  │  Generator  │  │ Management  │  │  Management │  │
│  │  :8000      │  │   :8001     │  │   :8004     │  │   :8005     │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │     Lab     │  │  Analytics  │  │Organization │  │   Content   │  │
│  │   Manager   │  │   Service   │  │ Management  │  │   Storage   │  │
│  │   :8006     │  │   :8007     │  │   :8008     │  │   :8003     │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          Data Layer                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ PostgreSQL  │  │    Redis    │  │    File     │  │   Object    │  │
│  │  Database   │  │    Cache    │  │   System    │  │   Storage   │  │
│  │   :5432     │  │   :6379     │  │             │  │   (S3/Minio)│  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    Container Orchestration Layer                        │
│                      (Docker / Kubernetes)                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │           Dynamic Student Lab Containers                        │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
│  │  │ Student  │  │ Student  │  │ Student  │  │    ...   │       │   │
│  │  │  Lab 1   │  │  Lab 2   │  │  Lab 3   │  │          │       │   │
│  │  │ VSCode   │  │ Jupyter  │  │ IntelliJ │  │          │       │   │
│  │  │ Terminal │  │ Terminal │  │ Terminal │  │          │       │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## System Design

### Design Patterns

#### 1. Microservices Pattern

Each service is:
- **Independently deployable**: Services can be updated without affecting others
- **Loosely coupled**: Services communicate via well-defined APIs
- **Single responsibility**: Each service handles one business domain
- **Technology agnostic**: Services can use different technologies if needed

#### 2. API Gateway Pattern

The Nginx reverse proxy serves as an API gateway:
- Routes requests to appropriate services
- Handles SSL/TLS termination
- Implements rate limiting
- Manages CORS policies
- Provides centralized authentication

#### 3. CQRS (Command Query Responsibility Segregation)

Separates read and write operations:
- **Commands**: Modify state (POST, PUT, DELETE)
- **Queries**: Read state (GET)
- Allows independent optimization of each path

#### 4. Repository Pattern

Data access abstraction:
```python
# Example: UserRepository
class UserRepository:
    async def create(self, user: User) -> User:
        """Create new user"""

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve user by ID"""

    async def update(self, user_id: str, updates: dict) -> User:
        """Update user"""

    async def delete(self, user_id: str) -> bool:
        """Delete user"""
```

#### 5. Dependency Injection

Services use dependency injection for testability:
```python
class UserService:
    def __init__(
        self,
        repository: UserRepository,
        auth_service: AuthService,
        email_service: EmailService
    ):
        self.repository = repository
        self.auth = auth_service
        self.email = email_service
```

#### 6. Circuit Breaker Pattern

Prevents cascade failures in service communication:
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
```

---

## Microservices Architecture

### Service Catalog

| Service | Port | Domain | Responsibilities |
|---------|------|--------|------------------|
| **User Management** | 8000 | Authentication & Authorization | User accounts, JWT tokens, sessions, password management |
| **Course Generator** | 8001 | AI Content Creation | AI-powered syllabus, slides, exercises, quizzes generation |
| **Content Storage** | 8003 | File Management | File upload/download, versioning, metadata |
| **Course Management** | 8004 | Course Lifecycle | CRUD operations, publishing, enrollment, feedback |
| **Content Management** | 8005 | Content Processing | Content upload, export (PDF, PowerPoint, SCORM) |
| **Lab Manager** | 8006 | Lab Orchestration | Docker container management, multi-IDE support |
| **Analytics** | 8007 | Data Analytics | Student metrics, engagement tracking, reporting |
| **Organization Management** | 8008 | RBAC & Multi-Tenancy | Organizations, roles, permissions, audit logs |

### Service Details

#### User Management Service (Port 8000)

**Purpose**: Authentication, authorization, and user lifecycle management

**Technology Stack**:
- FastAPI with async/await
- PostgreSQL for user data
- Redis for session storage
- JWT for stateless authentication
- bcrypt for password hashing

**Key Components**:
```
user-management/
├── domain/
│   ├── entities/user.py           # User entity model
│   └── value_objects/email.py     # Email validation
├── application/
│   ├── services/
│   │   ├── auth_service.py        # Authentication logic
│   │   ├── user_service.py        # User operations
│   │   └── session_service.py     # Session management
│   └── use_cases/
│       ├── login.py               # Login use case
│       └── register.py            # Registration use case
├── infrastructure/
│   ├── repositories/
│   │   └── user_repository.py     # Database operations
│   └── external/
│       └── email_client.py        # Email notifications
└── api/
    └── routes.py                   # FastAPI endpoints
```

**API Endpoints**:
```python
@app.post("/auth/register")
async def register(user_data: UserCreate) -> UserResponse

@app.post("/auth/login")
async def login(credentials: LoginRequest) -> TokenResponse

@app.post("/auth/password/change")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user)
) -> MessageResponse

@app.get("/auth/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserResponse
```

**Database Schema**:
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL,  -- student, instructor, admin
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

#### Course Generator Service (Port 8001)

**Purpose**: AI-powered content generation using Anthropic Claude

**Technology Stack**:
- FastAPI
- Anthropic Claude API
- Redis for caching (24-hour TTL)
- PostgreSQL for generation history

**Key Components**:
```
course-generator/
├── ai/
│   ├── clients/
│   │   ├── anthropic_client.py    # Claude API wrapper
│   │   └── openai_client.py       # OpenAI fallback
│   ├── generators/
│   │   ├── syllabus_generator.py  # Syllabus creation
│   │   ├── slide_generator.py     # Slide content
│   │   ├── exercise_generator.py  # Coding exercises
│   │   └── quiz_generator.py      # Quiz questions
│   └── prompts/
│       └── templates.py            # Prompt templates
├── caching/
│   └── redis_cache.py              # Caching layer
└── api/
    └── endpoints.py                 # API routes
```

**Generation Flow**:
```
User Request
    ↓
API Endpoint
    ↓
Check Cache (Redis)
    ↓
[Cache Miss] → AI Client → Claude API → Process Response → Cache Result
    ↓
[Cache Hit] → Return Cached Result
    ↓
Response to User
```

**Prompt Engineering**:
```python
SYLLABUS_PROMPT = """
You are an expert curriculum designer. Create a comprehensive course syllabus.

Course Title: {title}
Target Audience: {audience}
Duration: {duration} weeks
Difficulty: {difficulty}

Generate a structured syllabus with:
1. Course overview and learning objectives
2. Week-by-week breakdown
3. Key topics and subtopics
4. Prerequisites
5. Assessment methods

Format the output as JSON with this structure:
{{
    "title": "...",
    "overview": "...",
    "learning_objectives": [...],
    "modules": [
        {{
            "week": 1,
            "title": "...",
            "topics": [...],
            "duration_hours": 8
        }}
    ],
    "prerequisites": [...],
    "assessments": [...]
}}
"""
```

#### Lab Manager Service (Port 8006)

**Purpose**: Orchestrate Docker containers for student lab environments

**Technology Stack**:
- FastAPI
- Docker SDK for Python
- Docker-in-Docker (DinD)
- asyncio for concurrent operations
- PostgreSQL for lab metadata

**Container Lifecycle**:
```
Lab Creation Request
    ↓
Validate Request
    ↓
Build/Pull Docker Image
    ↓
Create Container with Config:
    - Volume mounts (persistent storage)
    - Network configuration
    - Resource limits (CPU, memory)
    - Environment variables
    ↓
Start Container
    ↓
Health Check Loop
    ↓
[Idle Timeout] → Pause Container
    ↓
[Resume Request] → Unpause Container
    ↓
[Logout/Cleanup] → Stop & Remove Container
```

**Multi-IDE Architecture**:
```
Student Lab Container
┌──────────────────────────────────────────┐
│  Base OS (Ubuntu 22.04)                  │
│  ┌────────────────────────────────────┐  │
│  │  IDE Services                      │  │
│  │  ┌──────────────┐  ┌────────────┐ │  │
│  │  │  VSCode      │  │ JupyterLab │ │  │
│  │  │  Server      │  │            │ │  │
│  │  │  :8080       │  │  :8081     │ │  │
│  │  └──────────────┘  └────────────┘ │  │
│  │  ┌──────────────┐  ┌────────────┐ │  │
│  │  │  IntelliJ    │  │  Terminal  │ │  │
│  │  │  Projector   │  │  (xterm.js)│ │  │
│  │  │  :8082       │  │  :8083     │ │  │
│  │  └──────────────┘  └────────────┘ │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  Shared File System                │  │
│  │  /workspace (mounted volume)       │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  Development Tools                 │  │
│  │  - Python, Node.js, Java           │  │
│  │  - Git, Docker CLI                 │  │
│  │  - Build tools (pip, npm, maven)   │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

**Resource Management**:
```python
RESOURCE_LIMITS = {
    "memory": "2g",
    "cpu_quota": 150000,  # 1.5 CPU cores
    "cpu_period": 100000,
    "pids_limit": 512,
    "disk_quota": "5g"
}

PORT_MAPPING = {
    "vscode": 8080,
    "jupyter": 8081,
    "intellij": 8082,
    "terminal": 8083
}
```

#### Analytics Service (Port 8007)

**Purpose**: Track student activity, engagement, and performance

**Technology Stack**:
- FastAPI
- PostgreSQL (time-series data)
- Redis (real-time aggregation)
- pandas (data analysis)
- matplotlib/plotly (visualization)

**Data Collection**:
```
Event → Validation → Enrichment → Storage → Aggregation → Reporting
   ↓
Activity Tracking:
- Login/logout events
- Page views
- Lab session start/end
- Quiz attempts
- Content downloads

Lab Usage:
- Code executions
- Errors encountered
- Time spent
- IDE switches

Quiz Performance:
- Question attempts
- Correct/incorrect answers
- Time per question
- Completion status
```

**Analytics Pipeline**:
```python
class AnalyticsPipeline:
    async def track_activity(self, event: ActivityEvent):
        # 1. Validate event data
        await self.validator.validate(event)

        # 2. Enrich with context
        enriched = await self.enricher.enrich(event)

        # 3. Store raw event
        await self.repository.save_event(enriched)

        # 4. Update aggregations (Redis)
        await self.aggregator.update(enriched)

        # 5. Check for triggers (e.g., at-risk student)
        await self.alert_engine.evaluate(enriched)

    async def generate_report(self, student_id: str, course_id: str):
        # Aggregate data from multiple sources
        activities = await self.get_activities(student_id, course_id)
        lab_usage = await self.get_lab_metrics(student_id, course_id)
        quiz_performance = await self.get_quiz_results(student_id, course_id)

        # Calculate derived metrics
        engagement_score = self.calc_engagement(activities)
        proficiency_score = self.calc_proficiency(lab_usage)
        risk_level = self.calc_risk(engagement_score, proficiency_score)

        return AnalyticsReport(
            engagement=engagement_score,
            proficiency=proficiency_score,
            risk_level=risk_level,
            recommendations=self.generate_recommendations(risk_level)
        )
```

---

## Data Architecture

### Database Design

#### Entity-Relationship Diagram

```
┌─────────────────┐         ┌─────────────────┐
│     Users       │         │ Organizations   │
├─────────────────┤         ├─────────────────┤
│ • id (PK)       │────┐    │ • id (PK)       │
│ • email         │    │    │ • name          │
│ • password_hash │    │    │ • slug          │
│ • role          │    │    │ • created_at    │
│ • created_at    │    │    └─────────────────┘
└─────────────────┘    │             │
         │             │             │
         │             │    ┌────────┴────────┐
         │             └────│  Memberships    │
         │                  ├─────────────────┤
         │                  │ • id (PK)       │
         │                  │ • user_id (FK)  │
         │                  │ • org_id (FK)   │
         │                  │ • role_type     │
         │                  └─────────────────┘
         │                           │
         ├───────────────────────────┘
         │
         │   ┌─────────────────┐
         └───│    Courses      │
             ├─────────────────┤
             │ • id (PK)       │
             │ • title         │
             │ • instructor_id │
             │ • created_at    │
             └─────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
┌────────▼──────┐ ┌──▼──────────┐ ┌▼────────────┐
│  Enrollments  │ │   Quizzes   │ │  Exercises  │
├───────────────┤ ├─────────────┤ ├─────────────┤
│ • id (PK)     │ │ • id (PK)   │ │ • id (PK)   │
│ • user_id     │ │ • course_id │ │ • course_id │
│ • course_id   │ │ • title     │ │ • title     │
│ • status      │ │ • questions │ │ • code      │
└───────────────┘ └─────────────┘ └─────────────┘
         │                │              │
         │                │              │
         ▼                ▼              ▼
┌───────────────┐ ┌──────────────┐ ┌──────────────┐
│   Progress    │ │QuizAttempts  │ │LabSessions   │
├───────────────┤ ├──────────────┤ ├──────────────┤
│ • id (PK)     │ │ • id (PK)    │ │ • id (PK)    │
│ • user_id     │ │ • user_id    │ │ • user_id    │
│ • course_id   │ │ • quiz_id    │ │ • exercise_id│
│ • progress %  │ │ • score      │ │ • status     │
└───────────────┘ └──────────────┘ └──────────────┘
```

### Data Models

#### User Entity
```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ORGANIZATION_ADMIN = "organization_admin"
    SITE_ADMIN = "site_admin"

@dataclass
class User:
    id: str
    email: str
    password_hash: str
    full_name: str
    role: UserRole
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": self.is_active
        }
```

#### Course Entity
```python
@dataclass
class Course:
    id: str
    title: str
    description: str
    instructor_id: str
    category: str
    difficulty_level: str
    estimated_duration: int
    status: str  # draft, published, archived
    created_at: datetime
    updated_at: datetime

    # Relationships
    instructor: Optional[User] = None
    enrollments: List['Enrollment'] = field(default_factory=list)
    quizzes: List['Quiz'] = field(default_factory=list)
```

### Caching Strategy

#### Redis Cache Layers

**Layer 1: Session Cache**
```python
# User sessions
KEY: f"session:{session_id}"
TTL: 24 hours
VALUE: {
    "user_id": "...",
    "email": "...",
    "role": "...",
    "expires_at": "..."
}
```

**Layer 2: Query Cache**
```python
# Frequently accessed data
KEY: f"user:profile:{user_id}"
TTL: 1 hour
VALUE: User profile JSON

KEY: f"course:{course_id}"
TTL: 10 minutes
VALUE: Course details JSON
```

**Layer 3: AI Generation Cache**
```python
# Expensive AI operations
KEY: f"ai:syllabus:{hash(prompt)}"
TTL: 24 hours
VALUE: Generated syllabus JSON

KEY: f"ai:quiz:{course_id}:{params_hash}"
TTL: 24 hours
VALUE: Generated quiz JSON
```

**Layer 4: Analytics Cache**
```python
# Real-time aggregations
KEY: f"analytics:engagement:{student_id}:{course_id}"
TTL: 5 minutes
VALUE: Engagement score

KEY: f"analytics:course_stats:{course_id}"
TTL: 1 hour
VALUE: Course-wide statistics
```

---

## Security Architecture

### Authentication Flow

```
┌──────────┐
│  Client  │
└────┬─────┘
     │ 1. POST /auth/login {email, password}
     ▼
┌────────────────────────────────────┐
│   User Management Service          │
│  ┌──────────────────────────────┐  │
│  │ 2. Verify credentials         │  │
│  │    - Check email exists       │  │
│  │    - Verify password hash     │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │ 3. Generate JWT token         │  │
│  │    - Create claims            │  │
│  │    - Sign with secret key     │  │
│  │    - Set expiration           │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │ 4. Store session in Redis     │  │
│  │    - Session ID as key        │  │
│  │    - User data as value       │  │
│  │    - TTL = 24 hours           │  │
│  └──────────────────────────────┘  │
└────────────────┬───────────────────┘
                 │ 5. Return JWT token
                 ▼
            ┌──────────┐
            │  Client  │
            └────┬─────┘
                 │ 6. Store token (localStorage/cookie)
                 │
                 │ 7. Subsequent requests
                 │    Authorization: Bearer <token>
                 ▼
            ┌─────────────────┐
            │  Any Service    │
            │  ┌────────────┐ │
            │  │ Verify JWT │ │
            │  │ - Decode   │ │
            │  │ - Validate │ │
            │  │ - Check    │ │
            │  │   expiry   │ │
            │  └────────────┘ │
            └─────────────────┘
```

### Authorization (RBAC)

```python
class Permission(str, Enum):
    # User permissions
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    UPDATE_USERS = "update_users"
    DELETE_USERS = "delete_users"

    # Course permissions
    VIEW_COURSES = "view_courses"
    CREATE_COURSES = "create_courses"
    UPDATE_COURSES = "update_courses"
    PUBLISH_COURSES = "publish_courses"

    # Lab permissions
    CREATE_LABS = "create_labs"
    VIEW_ALL_LABS = "view_all_labs"
    MANAGE_LABS = "manage_labs"

    # Analytics permissions
    VIEW_ANALYTICS = "view_analytics"
    VIEW_ALL_ANALYTICS = "view_all_analytics"

    # Organization permissions
    MANAGE_ORGANIZATION = "manage_organization"
    VIEW_AUDIT_LOGS = "view_audit_logs"

ROLE_PERMISSIONS = {
    UserRole.STUDENT: {
        Permission.VIEW_COURSES,
        Permission.VIEW_ANALYTICS,
    },
    UserRole.INSTRUCTOR: {
        Permission.VIEW_COURSES,
        Permission.CREATE_COURSES,
        Permission.UPDATE_COURSES,
        Permission.PUBLISH_COURSES,
        Permission.CREATE_LABS,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_ALL_ANALYTICS,
    },
    UserRole.ORGANIZATION_ADMIN: {
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.UPDATE_USERS,
        Permission.MANAGE_ORGANIZATION,
        Permission.VIEW_AUDIT_LOGS,
        # ... all instructor permissions
    },
    UserRole.SITE_ADMIN: {
        # All permissions
    }
}
```

### Security Measures

1. **Data Encryption**
   - At rest: Database encryption (PostgreSQL TDE)
   - In transit: TLS 1.3 for all connections
   - Passwords: bcrypt with salt (cost factor: 12)

2. **Input Validation**
   - Pydantic models for all API inputs
   - SQL injection prevention via parameterized queries
   - XSS prevention via output encoding
   - CSRF tokens for state-changing operations

3. **Rate Limiting**
   ```python
   RATE_LIMITS = {
       "/auth/login": "5/minute",
       "/auth/register": "3/hour",
       "/api/v1/*": "100/minute",
       "/labs/create": "10/hour"
   }
   ```

4. **Audit Logging**
   - All authentication attempts
   - All authorization failures
   - All data modifications
   - All admin actions

---

## Frontend Architecture

### Modular Architecture (v3.1)

```
frontend/
├── html/
│   ├── index.html
│   ├── instructor-dashboard.html
│   ├── student-dashboard.html
│   ├── org-admin-dashboard.html
│   └── site-admin-dashboard.html
├── css/
│   ├── main.css
│   ├── dashboard.css
│   └── lab.css
└── js/
    ├── config.js
    ├── modules/
    │   ├── auth.js                # Authentication module
    │   ├── api.js                 # API client module
    │   ├── org-admin-core.js      # Core org admin functionality
    │   ├── org-admin-api.js       # API integration
    │   ├── org-admin-utils.js     # Utility functions
    │   ├── org-admin-students.js  # Student management
    │   ├── org-admin-instructors.js # Instructor management
    │   ├── org-admin-tracks.js    # Track management
    │   ├── org-admin-projects.js  # Project management
    │   └── org-admin-settings.js  # Settings panel
    ├── org-admin-main.js          # Main entry point
    └── instructor-dashboard.js     # Instructor dashboard
```

### Component Communication

```javascript
// Event-driven architecture
class EventBus {
    constructor() {
        this.events = {};
    }

    on(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
    }

    emit(event, data) {
        if (this.events[event]) {
            this.events[event].forEach(callback => callback(data));
        }
    }
}

// Usage
const bus = new EventBus();

// Student module listens
bus.on('student:created', (student) => {
    StudentsModule.addToList(student);
});

// API module emits
bus.emit('student:created', newStudent);
```

---

## Integration Patterns

### Service Communication

```
Synchronous (REST):
    Service A --HTTP POST--> Service B
    Service A <--Response--- Service B

Asynchronous (Future):
    Service A --Event--> Message Queue --Event--> Service B
                                    |
                                    └--> Service C
```

### Error Handling

```python
# Custom exception hierarchy
class ApplicationError(Exception):
    """Base application exception"""
    def __init__(self, message: str, code: str, status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code

class ValidationError(ApplicationError):
    def __init__(self, message: str, field: str = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422
        )
        self.field = field

class AuthenticationError(ApplicationError):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401
        )

# Global error handler
@app.exception_handler(ApplicationError)
async def handle_application_error(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

---

## Scalability & Performance

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  user-management:
    deploy:
      replicas: 3

  course-generator:
    deploy:
      replicas: 2

  lab-manager:
    deploy:
      replicas: 3
```

### Performance Optimizations

1. **Database Query Optimization**
   - Indexes on frequently queried columns
   - Connection pooling (asyncpg)
   - Query result caching

2. **API Response Optimization**
   - Gzip compression
   - Response pagination
   - Field selection (GraphQL-style)

3. **Caching Strategy**
   - Redis for hot data
   - CDN for static assets
   - Browser caching headers

---

## Design Decisions

### Key Technical Decisions

1. **Why FastAPI?**
   - Modern async/await support
   - Automatic API documentation
   - Type hints and validation
   - High performance (comparable to Node.js/Go)

2. **Why PostgreSQL?**
   - ACID compliance
   - JSON support for flexible data
   - Excellent performance
   - Strong ecosystem

3. **Why Docker?**
   - Consistent environments
   - Easy local development
   - Production parity
   - Resource isolation for labs

4. **Why Microservices?**
   - Independent scaling
   - Technology flexibility
   - Team autonomy
   - Fault isolation

---

**Document Version**: 3.1.0
**Last Updated**: 2025-10-04
**Next Review**: 2025-11-04
