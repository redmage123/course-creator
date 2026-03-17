# Course Creator Platform - Architecture Documentation

## System Overview

The Course Creator Platform is built using a modern microservices architecture that provides scalability, maintainability, and flexibility. The system consists of multiple loosely-coupled services that communicate through well-defined APIs.

## High-Level Architecture

The Course Creator Platform uses a microservices architecture with 5 core backend services:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Load Balancer / Nginx                    │
│                         (Port 80/443)                           │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────────────────┐
│                       Frontend Layer                            │
│                        (Port 8080)                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ Instructor  │ │   Student   │ │     Lab     │              │
│  │ Dashboard   │ │ Dashboard   │ │ Environment │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│                                                                │
│  Frontend: HTML5/CSS3/JavaScript ES6 + Bootstrap 5            │
│  Lab: xterm.js + WebSocket for real-time interaction          │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────────────────┐
│                    Backend Services                             │
│                                                                │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│ │    User     │ │   Course    │ │   Content   │ │   Course    ││
│ │ Management  │ │ Generator   │ │  Storage    │ │ Management  ││
│ │  (8000)     │ │   (8001)    │ │   (8003)    │ │   (8004)    ││
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│                                                                │
│              ┌─────────────────────────────────┐              │
│              │      Content Management         │              │
│              │         (8005)                  │              │
│              └─────────────────────────────────┘              │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────────────────┐
│                     Data Layer                                 │
│                                                                │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│ │ PostgreSQL  │ │    Redis    │ │ File Storage│ │ MCP Server  ││
│ │  Database   │ │   Cache     │ │ (Local FS)  │ │(Monitoring) ││
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### Frontend Layer

The frontend is built with modern web technologies and serves on port 8080:

#### 1. Instructor Dashboard (`instructor-dashboard.html`)
- **Purpose**: Course creation and management interface
- **Features**:
  - Tabbed interface for course content management
  - AI-powered syllabus generation
  - Slide generation from course content
  - Exercise and quiz creation
  - File upload with drag-and-drop interface
  - Multi-format content export (PowerPoint, PDF, Excel, SCORM)
  - Interactive lab environment configuration
- **Technology**: HTML5, CSS3, JavaScript ES6 modules, Bootstrap 5
- **Key Files**:
  - `js/main.js` - Main application entry point
  - `js/modules/` - Modular components (auth, navigation, notifications)
  - `js/config.js` - Configuration management

#### 2. Student Dashboard (`student-dashboard.html`)
- **Purpose**: Student learning interface
- **Features**:
  - Course enrollment and access
  - Progress tracking and analytics
  - Quiz taking with immediate feedback
  - Lab environment access
  - Interactive learning materials
- **Technology**: HTML5, CSS3, JavaScript ES6 modules, Bootstrap 5
- **Real-time Features**: WebSocket connections for live updates

#### 3. Lab Environment (`lab.html`)
- **Purpose**: Interactive coding environment with AI assistance
- **Features**:
  - Browser-based terminal (xterm.js)
  - Code editor with syntax highlighting
  - File management system
  - Exercise execution and validation
  - AI-powered code assistance
  - Real-time collaboration features
- **Technology**: 
  - xterm.js for terminal emulation
  - Marked.js for markdown rendering
  - WebSocket for real-time communication
- **Security**: Sandboxed execution environment with resource limits

### Backend Services

The platform uses a microservices architecture with 5 core services that follow SOLID principles and Test-Driven Development (TDD):

#### 1. User Management Service (Port 8000)
**Responsibilities**:
- User authentication and authorization
- JWT token management
- User profile management
- Role-based access control (RBAC)

**Technology Stack**:
- FastAPI framework with asyncio
- asyncpg for PostgreSQL connectivity
- JWT for authentication
- Bcrypt for password hashing
- Repository pattern for data access

**Key Endpoints**:
- `POST /auth/login` - User authentication
- `POST /auth/register` - User registration
- `GET /auth/profile` - Get user profile
- `GET /users` - List users (admin only)

#### 2. Course Generator Service (Port 8001)
**Responsibilities**:
- AI-powered content generation using Anthropic Claude
- Course structure and syllabus creation
- Exercise and quiz generation
- Slide generation from content
- Interactive lab environment setup

**Technology Stack**:
- FastAPI framework with asyncio
- Anthropic Claude API integration
- OpenAI API (fallback)
- Hydra configuration management
- Background task processing

**Key Endpoints**:
- `POST /generate/syllabus` - Generate course syllabus
- `POST /generate/slides` - Generate presentation slides
- `POST /exercises/generate` - Generate interactive exercises
- `POST /quiz/generate-for-course` - Generate quizzes
- `GET /exercises/{course_id}` - Get course exercises
- `GET /quiz/course/{course_id}` - Get course quizzes

**Key Components**:
- `services/quiz_service.py` - Quiz generation and management
- `services/exercise_generation_service.py` - Exercise creation (TDD implementation)
- `ai_integration.py` - AI service integration

#### 3. Content Storage Service (Port 8003)
**Responsibilities**:
- File upload and storage management
- Content versioning
- File metadata management
- Storage optimization

**Technology Stack**:
- FastAPI framework
- Local filesystem storage
- File processing utilities
- Metadata management

**Key Endpoints**:
- `POST /upload` - Upload files
- `GET /download/{file_id}` - Download files
- `DELETE /files/{file_id}` - Delete files

#### 4. Course Management Service (Port 8004)
**Responsibilities**:
- Course CRUD operations
- Course metadata management
- Course publishing workflow
- Enrollment management

**Technology Stack**:
- FastAPI framework
- asyncpg for PostgreSQL
- Repository pattern
- Service layer architecture

**Key Endpoints**:
- `GET /courses` - List courses
- `POST /courses` - Create course
- `GET /courses/{course_id}` - Get course details
- `PUT /courses/{course_id}` - Update course
- `DELETE /courses/{course_id}` - Delete course

#### 5. Content Management Service (Port 8005)
**Responsibilities**:
- File upload/download with AI integration
- Multi-format content export (PowerPoint, PDF, Excel, SCORM, ZIP)
- Content processing and extraction
- File metadata and storage management

**Technology Stack**:
- FastAPI framework
- File processing pipeline
- AI integration for content generation
- Multi-format export capabilities

**Key Endpoints**:
- `POST /upload` - Upload and process content files
- `GET /export/{format}` - Export content in various formats
- `GET /files` - List uploaded files

**Export Formats**:
- PowerPoint (.pptx)
- PDF documents
- Excel spreadsheets
- SCORM packages
- ZIP archives
- JSON data

**Key Components**:
- `file_processors.py` - File processing pipeline
- `ai_integration.py` - AI content generation
- `storage_manager.py` - File storage management

### Data Layer

#### PostgreSQL Database
**Purpose**: Primary data storage for all services
**Configuration**:
- Database: `course_creator`
- Port: 5433 (non-standard to avoid conflicts)
- Connection pooling with asyncpg
- ACID compliance for data integrity
- Automated migrations via `setup-database.py`

**Core Tables**:
- `users` - User accounts with role-based access
- `courses` - Course metadata and content
- `enrollments` - Student-course relationships
- `slides` - Generated slide content
- `lab_sessions` - Interactive lab environment data
- `quizzes` - Quiz data with questions and answers
- `quiz_questions` - Individual quiz questions
- `exercises` - Generated coding exercises

#### Redis Cache
**Purpose**: Session management and caching
**Configuration**:
- Port: 6379
- Session storage for JWT tokens
- API response caching
- Real-time data for lab environments

#### File Storage
**Purpose**: Content and media storage
**Implementation**:
- Local filesystem storage (`services/content-management/storage/`)
- File metadata tracking
- Content versioning
- Multi-format support (PDF, DOCX, PPTX, JSON)

#### MCP Server
**Purpose**: Model Context Protocol integration for monitoring
**Features**:
- Real-time service health monitoring
- Platform overview and statistics
- Log access and analysis
- Content management status

## Communication Patterns

### Service Dependencies
Services must be started in dependency order for proper operation:

1. **User Management** (8000) → Authentication foundation
2. **Course Generator** (8001) → AI-powered content generation
3. **Course Management** (8004) → Course CRUD operations
4. **Content Storage** (8003) → File storage and retrieval
5. **Content Management** (8005) → Advanced content processing

### Synchronous Communication
- **REST APIs**: Primary communication method between frontend and backend
- **HTTP/HTTPS**: Secure communication protocol with JWT authentication
- **JSON**: Data exchange format across all services
- **FastAPI**: All services use FastAPI for consistent API structure

### Service-to-Service Communication
- **Direct HTTP calls**: Services communicate via HTTP APIs
- **Health checks**: Each service exposes `/health` endpoint
- **Configuration**: Hydra configuration management across services
- **Error handling**: Consistent error responses across services

### Frontend-Backend Communication
- **AJAX/Fetch**: Modern JavaScript async requests
- **WebSocket**: Real-time features in lab environment
- **File uploads**: Multipart form data for content uploads
- **Authentication**: JWT tokens in Authorization headers

### Platform Control
- **app-control.sh**: Unified service management script
- **Health monitoring**: Automated health checks and dependency management
- **Service discovery**: Services discover each other through configuration
- **Graceful shutdown**: Proper service lifecycle management

## Security Architecture

### Authentication & Authorization Flow
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│    User     │───▶│   Service   │
│             │    │ Management  │    │             │
│ JWT Token   │    │ Service     │    │ Validates   │
│ in Header   │    │ (8000)      │    │ Token       │
└─────────────┘    └─────────────┘    └─────────────┘
```

### JWT Token Management
- **Authentication**: User Management Service handles login/logout
- **Token Generation**: JWT tokens with expiration
- **Token Validation**: Each service validates tokens independently
- **Role-based Access**: Admin, Instructor, Student roles with different permissions

### Security Layers
1. **Network Security**: HTTPS enforcement, secure headers
2. **Application Security**: JWT tokens, RBAC, input validation
3. **Data Security**: SQL injection prevention, secure database connections
4. **File Security**: File type validation, size limits, content scanning

### Lab Environment Security
- **Sandboxing**: Isolated execution environments for student code
- **Resource Limits**: CPU, memory, and disk quotas per session
- **Network Isolation**: Restricted network access from lab environments
- **File System Security**: Controlled file access and permissions
- **Code Validation**: Input sanitization and code execution limits

## Development Standards

### SOLID Principles
The platform follows SOLID principles for maintainable code:

1. **Single Responsibility Principle (SRP)**: Each service has one reason to change
2. **Open/Closed Principle (OCP)**: Services are open for extension, closed for modification
3. **Liskov Substitution Principle (LSP)**: Interfaces can be substituted without breaking functionality
4. **Interface Segregation Principle (ISP)**: Many client-specific interfaces over general-purpose ones
5. **Dependency Inversion Principle (DIP)**: Services depend on abstractions, not concretions

### Test-Driven Development (TDD)
All new code follows TDD methodology:

1. **Red**: Write failing tests that define desired functionality
2. **Green**: Write minimal code to make tests pass
3. **Refactor**: Clean up code while keeping tests passing

**Test Structure**:
- `tests/unit/` - Component-level tests
- `tests/integration/` - Service interaction tests
- `tests/e2e/` - Full workflow tests using Playwright
- Minimum 80% code coverage requirement

### CI/CD Pipeline
Comprehensive pipeline with multiple stages:

1. **Build** - Install dependencies and build application
2. **Test** - Run unit, integration, and e2e tests
3. **Quality** - Code quality checks (linting, formatting, security)
4. **Deploy** - Deploy to staging environment
5. **Verify** - Run smoke tests and health checks
6. **Promote** - Merge to main and deploy to production

### Code Quality Standards
- **Python**: Black formatting, isort imports, flake8 linting
- **JavaScript**: ESLint, npm test suite
- **Documentation**: Comprehensive API documentation with Swagger/OpenAPI
- **Security**: Automated security scanning and vulnerability checks

## Monitoring and Observability

### Service Health Monitoring
- **Health Endpoints**: Each service exposes `/health` endpoint
- **app-control.sh**: Unified health checking across all services
- **Dependency Management**: Services start in correct order with health validation
- **Service Status**: Real-time service availability monitoring

### MCP Integration
- **Unified MCP Server**: Model Context Protocol for Claude Desktop integration
- **Real-time Monitoring**: Service health, platform statistics, and log analysis
- **mcp-control.sh**: MCP server lifecycle management
- **Platform Overview**: Comprehensive system status and metrics

### Logging
- **Service Logs**: Individual service logs in `services/*/outputs/`
- **Centralized Logs**: Platform-wide log aggregation in `logs/` directory
- **Structured Logging**: Consistent log format across services
- **Log Rotation**: Automated log management and cleanup

### Development Monitoring
- **pytest**: Comprehensive test suite with coverage reporting
- **Code Coverage**: Minimum 80% coverage requirement
- **Test Categorization**: Unit, integration, e2e test markers
- **Continuous Testing**: Automated test execution in CI/CD pipeline

## Deployment Architecture

### Local Development Environment
```
┌─────────────────────────────────────────────────────────────┐
│                    Local Development                        │
│                                                             │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│ │  Frontend   │ │    User     │ │   Course    │ │ Content │ │
│ │   (8080)    │ │ Management  │ │ Generator   │ │ Storage │ │
│ │             │ │   (8000)    │ │   (8001)    │ │ (8003)  │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
│                                                             │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │   Course    │ │   Content   │ │ PostgreSQL  │            │
│ │ Management  │ │ Management  │ │   (5433)    │            │
│ │   (8004)    │ │   (8005)    │ │             │            │
│ └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### Service Management
- **app-control.sh**: Unified service lifecycle management
- **Dependency Order**: Services start in correct order with health checks
- **Process Management**: Background service execution with proper shutdown
- **Development Setup**: Local Python virtual environment with all dependencies

### Deployment Strategy
- **Development**: Local services with `app-control.sh`
- **Frontend**: Static file serving with Python HTTP server or npm
- **Database**: Local PostgreSQL instance with automated migrations
- **Configuration**: Environment-specific configuration with `.cc_env` files

### CI/CD Pipeline
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Source    │───▶│    Build    │───▶│    Test     │───▶│   Deploy    │
│   Control   │    │             │    │             │    │             │
│   (Git)     │    │ Dependencies│    │ Unit Tests  │    │ Service     │
│             │    │ Install     │    │ Integration │    │ Restart     │
│             │    │             │    │ E2E Tests   │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### GitHub Actions Integration
- **CI/CD Pipeline**: `.github/workflows/ci.yml`
- **Automated Testing**: Full test suite execution
- **Code Quality**: Linting, formatting, and security checks
- **Deployment**: Automated deployment to staging/production environments

## Data Flow Patterns

### Course Creation Flow
```
Instructor → Frontend (8080) → Course Management Service (8004) → Database
                    ↓
              Course Generator Service (8001) → Anthropic Claude API
                    ↓
              Content Management Service (8005) → File Storage
```

### AI-Powered Content Generation Flow
```
Instructor Request → Course Generator Service (8001) → Anthropic Claude API
                                                  ↓
                    Syllabus/Slides/Quiz Generation → Database
                                                  ↓
                    Content Storage Service (8003) → File Storage
                                                  ↓
                    Frontend Update → Real-time Display
```

### Student Learning Flow
```
Student → Frontend (8080) → Course Management Service (8004) → Database
              ↓
        Lab Environment → xterm.js → WebSocket → Real-time Updates
              ↓
        Quiz System → Course Generator Service (8001) → Progress Tracking
```

### File Upload and Processing Flow
```
Instructor → Frontend (8080) → Content Management Service (8005)
                                          ↓
                    File Processing Pipeline → AI Content Generation
                                          ↓
                    Multi-format Export → PowerPoint/PDF/Excel/SCORM
                                          ↓
                    File Storage → Local Filesystem
```

## Platform Management

### Service Lifecycle Management
- **app-control.sh**: Unified service control with dependency management
- **Health Monitoring**: Continuous service health verification
- **Graceful Shutdown**: Proper service termination handling
- **Auto-restart**: Failed service recovery mechanisms

### Configuration Management
- **Hydra Configuration**: Centralized configuration management
- **Environment Variables**: `.cc_env` file for sensitive configuration
- **Service Configuration**: Individual service configuration files
- **Database Configuration**: Automated database setup and migrations

### Development Workflow
- **Local Development**: Complete platform runs locally with `app-control.sh`
- **Database Setup**: Automated with `setup-database.py`
- **Frontend Development**: Live reload and development server
- **Testing**: Comprehensive test suite with TDD methodology

## Current Status and Roadmap

### Current Implementation (v1.0.0)
- ✅ Complete microservices architecture
- ✅ AI-powered content generation with Anthropic Claude
- ✅ Interactive lab environments with xterm.js
- ✅ Comprehensive quiz system with TDD implementation
- ✅ Multi-format content export (PowerPoint, PDF, Excel, SCORM)
- ✅ User management with JWT authentication
- ✅ File upload/download with content processing
- ✅ MCP integration for monitoring
- ✅ CI/CD pipeline with GitHub Actions

### Planned Enhancements
- **Real-time Collaboration**: Live coding sessions between students and instructors
- **Advanced Analytics**: Machine learning-powered insights and recommendations
- **Mobile Support**: Responsive design and mobile app development
- **Video Content**: Video processing and streaming capabilities
- **Payment Integration**: Course monetization and payment processing

### Technical Roadmap
- **Service Mesh**: Advanced service communication and observability
- **Container Orchestration**: Kubernetes deployment for production scaling
- **Event Sourcing**: Audit trail and replay capabilities
- **GraphQL**: Flexible API queries and real-time subscriptions
- **Edge Computing**: Content delivery optimization

This architecture provides a comprehensive foundation for the Course Creator Platform, supporting current functionality while maintaining flexibility for future enhancements and scaling requirements.