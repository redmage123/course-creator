# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Version**: 2.0.0 - Enhanced with Individual Lab Container System  
**Last Updated**: 2025-07-26

## Development Commands

### Platform Management

#### Docker Deployment (recommended for production)
```bash
# Production deployment using Docker Compose
./app-control.sh docker-start     # Start platform using Docker Compose
./app-control.sh docker-stop      # Stop all Docker containers
./app-control.sh docker-restart   # Restart platform using Docker Compose
./app-control.sh docker-status    # Show status of Docker containers
./app-control.sh docker-logs [service] # Show Docker logs for a service
./app-control.sh docker-build     # Build Docker images from scratch
./app-control.sh docker-pull      # Pull latest base Docker images
./app-control.sh docker-clean     # Clean up Docker resources

# Or use Docker Compose directly
docker-compose up -d
docker-compose ps                 # Check all service status
docker-compose logs -f            # Follow all logs
docker-compose down               # Stop all services

# Docker deployment includes:
# - PostgreSQL database (port 5433)
# - Redis cache (port 6379)
# - All microservices (ports 8000-8007)
# - Frontend (port 3000)
# - Lab container manager (port 8006)
```

#### Native Deployment (development)
```bash
# Development with app-control.sh (native Python)
./app-control.sh start
./app-control.sh status           # Check service status
./app-control.sh stop             # Stop all services
./app-control.sh restart          # Restart all services
./app-control.sh logs <service>   # View service logs

# Start individual services (in dependency order)
cd services/user-management && python run.py      # Port 8000
cd services/course-generator && python run.py     # Port 8001  
cd services/course-management && python run.py    # Port 8004
cd services/content-storage && python run.py      # Port 8003
cd services/content-management && python run.py   # Port 8005
cd services/analytics && python main.py           # Port 8007
cd lab-containers && python run.py               # Port 8006 (Lab Manager)

# Or start individual services using app-control.sh
./app-control.sh start user-management
./app-control.sh start course-generator
./app-control.sh start analytics
./app-control.sh start lab-manager
# etc...

# Serve frontend
cd frontend && python -m http.server 8080
# Or: npm start (serves on port 8080)
```

### Testing
```bash
# Comprehensive test runner (recommended)
python tests/run_all_tests.py                    # Run all test suites
python tests/run_all_tests.py --suite unit       # Run only unit tests
python tests/run_all_tests.py --suite frontend   # Run only frontend tests
python tests/run_all_tests.py --suite e2e        # Run only e2e tests
python tests/run_all_tests.py --coverage         # Run with coverage reports
python tests/run_all_tests.py --verbose          # Verbose output

# Specialized test runners
python tests/runners/run_lab_tests.py            # Lab system tests (14/14 frontend, 8/9 e2e)
python tests/runners/run_analytics_tests.py      # Analytics system tests (20/20 unit)

# Direct pytest usage
python -m pytest                                 # Run all tests
python -m pytest tests/unit/                     # Unit tests only
python -m pytest tests/integration/              # Integration tests only
python -m pytest tests/e2e/                      # End-to-end tests only
python -m pytest tests/frontend/                 # Frontend tests only

# Run tests with coverage
python -m pytest --cov=services --cov=lab-containers --cov-report=html

# Run frontend tests
npm test                          # Jest unit tests
npm run test:e2e                 # Playwright E2E tests
npm run test:all                 # All frontend tests

# Docker-based testing (for production validation)
docker-compose -f docker-compose.test.yml up --build
```

### Database Operations
```bash
# Setup database and run migrations
python setup-database.py

# Reset database (caution: destructive)
python setup-database.py --reset

# Create admin user
python create-admin.py
```

### Code Quality
```bash
# Lint JavaScript
npm run lint
npm run lint:fix

# Python formatting (no built-in commands, use standard tools)
black services/
isort services/
flake8 services/
```

## Architecture Overview

### Microservices Structure
The platform uses a microservices architecture with 7 core backend services:

1. **User Management Service** (Port 8000) - Authentication, user profiles, RBAC
2. **Course Generator Service** (Port 8001) - AI-powered content generation using Anthropic/OpenAI
3. **Content Storage Service** (Port 8003) - File storage, content versioning
4. **Course Management Service** (Port 8004) - CRUD operations for courses, enrollment
5. **Content Management Service** (Port 8005) - File upload/download, multi-format export
6. **Lab Container Manager Service** (Port 8006) - Individual student Docker container management
7. **Analytics Service** (Port 8007) - Student analytics, progress tracking, learning insights

### Service Dependencies
Services must be started in dependency order:
- User Management → Course Generator → Course Management → Content Storage → Content Management → Analytics → Lab Container Manager

The `app-control.sh` script and Docker Compose handle this automatically with health checks.

### Frontend Architecture
Static HTML/CSS/JavaScript frontend with multiple dashboards:
- `admin.html` - Admin interface
- `instructor-dashboard.html` - Course creation and management  
- `student-dashboard.html` - Course consumption
- `lab.html` - Interactive coding environment with xterm.js

### Data Layer
- **PostgreSQL** - Primary database for all services
- **Redis** - Session management and caching
- **File Storage** - Local filesystem (services/content-management/storage/)

## Key Configuration

### Service Configuration
Each service uses Hydra configuration with YAML files in `config/`:
- `config/config.yaml` - Main configuration
- `config/services/` - Service-specific configs
- `config/database/postgres.yaml` - Database settings
- `config/ai/claude.yaml` - AI service configuration

### Environment Variables
Services read configuration from:
- Environment variables (prefixed appropriately)
- Local config files in each service directory
- Shared config in `config/` directory

### Frontend Configuration
Frontend services are configured in `frontend/js/config.js`:
```javascript
const CONFIG = {
    BASE_URL: 'http://localhost:8001',
    ENDPOINTS: {
        USER_SERVICE: 'http://localhost:8000',
        COURSE_SERVICE: 'http://localhost:8004',
        CONTENT_SERVICE: 'http://localhost:8003'
    }
};
```

## Content Management System

The platform includes comprehensive content upload/download functionality with pane-based integration:

### Enhanced File Processing Pipeline
1. **Upload** - Drag-and-drop interface supports PDF, DOCX, PPTX, JSON with pane-specific functionality
2. **Processing** - `file_processors.py` extracts text and structure
3. **AI Integration** - `ai_integration.py` generates course content from uploads and templates
4. **Storage** - `storage_manager.py` handles file storage with metadata
5. **Export** - Multi-format export (PowerPoint, JSON, PDF, Excel, ZIP, SCORM)

### Pane-Based Content Management (v2.0)
- **Syllabus Pane** - Upload/download syllabus files with AI processing
- **Slides Pane** - Upload slide templates and individual slides, AI uses templates for generation
- **Labs Pane** - Upload custom lab environments and configurations for AI recognition
- **Quizzes Pane** - Upload custom multiple-choice quizzes with automatic answer key recognition

### Key Files
- `services/content-management/main.py` - FastAPI service with upload/export endpoints
- `services/content-management/models.py` - Pydantic models and validation
- `frontend/instructor-dashboard.html` - Enhanced tabbed interface with pane-based content management
- `frontend/js/instructor-dashboard.js` - File upload/download functionality with lab container integration

## Lab Container Management System (v2.1 - Multi-IDE Edition)

The platform now includes a comprehensive lab container management system with multi-IDE support:

### Individual Student Lab Containers
- **Per-Student Isolation** - Each student gets their own Docker container
- **Multi-IDE Support** - VSCode Server, JupyterLab, IntelliJ IDEA, and Terminal access
- **Dynamic Image Building** - Custom images built on-demand with specific packages and IDE configurations
- **IDE Switching** - Seamless switching between IDEs without losing work
- **Automatic Lifecycle** - Containers auto-start on login, pause on logout, resume on return
- **Persistent Storage** - Student work preserved across sessions and IDE switches with mounted volumes
- **Resource Management** - CPU/memory limits with enhanced resources for multi-IDE support (2GB/150% CPU)

### Multi-IDE Environment Features
- **VSCode Server** - Full web-based VSCode with Python extensions, syntax highlighting, and IntelliSense
- **JupyterLab** - Interactive notebook environment for data science with matplotlib, pandas, numpy
- **IntelliJ IDEA** - Professional IDE via JetBrains Projector (optional, resource-intensive)
- **Terminal** - Traditional xterm.js command-line interface
- **Real-time Status** - Live IDE health monitoring and availability indicators
- **Port Management** - Dynamic port allocation for each IDE service (8080-8083)

### Instructor Lab Management
- **Real-time Monitoring** - View all student lab containers with live status and IDE usage
- **Multi-IDE Analytics** - Track which IDEs students prefer and use most
- **Bulk Operations** - Pause, resume, or stop multiple labs simultaneously
- **Individual Controls** - Manage specific student lab sessions and IDE preferences
- **Instructor Labs** - Personal lab environments for course development with full IDE access
- **Resource Analytics** - Usage metrics, performance monitoring, and IDE utilization stats

### Key Lab Container Files
- `lab-containers/main.py` - FastAPI lab manager service with Docker and multi-IDE integration
- `lab-containers/Dockerfile` - Lab manager container configuration
- `lab-containers/lab-images/multi-ide-base/` - Multi-IDE Docker base images
- `lab-containers/lab-images/python-lab-multi-ide/` - Python lab with multi-IDE support
- `lab-containers/lab-images/multi-ide-base/ide-startup.py` - IDE management service
- `frontend/lab-multi-ide.html` - Multi-IDE lab interface with IDE selection
- `frontend/lab.html` - Legacy lab interface (terminal-only)
- `docker-compose.yml` - Full platform orchestration including lab manager
- `frontend/js/modules/lab-lifecycle.js` - Automatic lab lifecycle management
- `frontend/instructor-dashboard.html` - Lab container management interface

### Lab Container API Endpoints
```http
# Core Lab Management
POST /labs                    # Create new lab container (with multi-IDE support)
POST /labs/student            # Get or create student lab
GET  /labs                    # List all lab containers
GET  /labs/{lab_id}          # Get lab details
POST /labs/{lab_id}/pause    # Pause lab container
POST /labs/{lab_id}/resume   # Resume lab container
DELETE /labs/{lab_id}        # Stop and remove lab
GET  /labs/instructor/{course_id} # Get instructor lab overview
GET  /health                 # Lab service health check

# Multi-IDE Management (v2.1)
GET  /labs/{lab_id}/ides     # Get available IDEs for lab
POST /labs/{lab_id}/ide/switch # Switch preferred IDE
GET  /labs/{lab_id}/ide/status # Get IDE health status
```

## Database Schema

### Core Tables
- `users` - User accounts with role-based access
- `courses` - Course metadata and content
- `enrollments` - Student-course relationships
- `slides` - Generated slide content
- `lab_sessions` - Interactive lab environment data (enhanced with container information)

### Lab Container Data (in-memory)
- `active_labs` - Currently running lab containers with metadata
- `user_labs` - User-to-lab mapping for quick lookup
- Container state persisted in Docker volumes

### Migrations
Database migrations are in `data/migrations/` and run via `setup-database.py`.

## Testing Strategy

### Test Organization
- `tests/unit/` - Component-level tests including lab container unit tests
- `tests/integration/` - Service interaction tests with lab lifecycle integration
- `tests/frontend/` - JavaScript module testing with browser simulation
- `tests/e2e/` - Full workflow tests including complete lab container lifecycles
- `tests/security/` - Authentication and authorization tests
- `tests/performance/` - Load testing

### Lab Container Testing (v2.0)
- **Unit Tests** - `tests/unit/lab_container/test_lab_manager_service.py` - Core lab manager functionality
- **Integration Tests** - `tests/integration/test_lab_lifecycle_integration.py` - Lab lifecycle with auth integration
- **Frontend Tests** - `tests/frontend/test_lab_integration_frontend.py` - JavaScript lab functionality (14 tests passing)
- **E2E Tests** - `tests/e2e/test_lab_system_e2e.py` - Complete user workflows (8/9 tests passing)
- **Comprehensive Test Runner** - `run_lab_tests.py` - Unified test execution with detailed reporting

### Test Configuration
- `pytest.ini` - Python test configuration with coverage requirements (80% minimum)
- `package.json` - JavaScript test configuration with Jest and Playwright
- Tests use markers for categorization (unit, integration, e2e, frontend, security, etc.)
- HTML and JSON test reports generated in `test_reports/` directory

## AI Integration

### Content Generation
The platform integrates with AI services for automated content creation:
- Syllabus analysis and course outline generation
- Slide generation from course content
- Exercise and quiz creation
- Lab environment customization

### AI Service Configuration
- Primary: Anthropic Claude (configured in `config/ai/claude.yaml`)
- Fallback: OpenAI (optional)
- Mock data available for development when AI services unavailable

## Security Considerations

### Authentication Flow
- JWT-based authentication with secure session management
- Role-based access control (Admin, Instructor, Student)
- Secure API endpoints with proper authorization checks

### File Upload Security
- File type validation and size limits
- Content scanning and sanitization
- Secure file storage with access controls

## Development Standards

### SOLID Principles
All new software must follow SOLID principles:

1. **Single Responsibility Principle (SRP)** - Each class should have only one reason to change
2. **Open/Closed Principle (OCP)** - Software entities should be open for extension, but closed for modification
3. **Liskov Substitution Principle (LSP)** - Objects of a superclass should be replaceable with objects of a subclass without breaking the application
4. **Interface Segregation Principle (ISP)** - Many client-specific interfaces are better than one general-purpose interface
5. **Dependency Inversion Principle (DIP)** - Depend on abstractions, not concretions

### Test Driven Development (TDD)
Claude Code must use Test Driven Development when creating new code:

1. **Red** - Write a failing test first that defines the desired functionality
2. **Green** - Write the minimum code necessary to make the test pass
3. **Refactor** - Clean up the code while keeping tests passing

#### TDD Workflow:
```bash
# 1. Write failing test
python -m pytest tests/unit/new_feature_test.py::test_new_functionality -v

# 2. Implement minimal code to pass test
# Edit source code...

# 3. Run test to verify it passes
python -m pytest tests/unit/new_feature_test.py::test_new_functionality -v

# 4. Refactor and ensure all tests still pass
python -m pytest tests/unit/ -v

# 5. Run full test suite
python -m pytest --cov=services --cov-report=html
```

### CI/CD Pipeline

The platform uses a comprehensive Jenkins and SonarQube CI/CD pipeline for automated testing, code quality analysis, and multi-environment deployment.

#### Pipeline Overview
```bash
# Start Jenkins and SonarQube services
./jenkins/jenkins-setup.sh      # Setup Jenkins with plugins and configuration
./sonarqube/setup-sonarqube.sh  # Setup SonarQube with quality profiles and gates

# Pipeline trigger methods
# 1. Automatic: Git push/PR to GitHub triggers webhook
# 2. Manual: Jenkins UI or CLI trigger
# 3. Scheduled: Nightly builds for main branch
```

#### Quality Gates
- **Minimum Coverage**: 75% for new code, 70% overall
- **Security**: Zero vulnerabilities or unreviewed security hotspots  
- **Bugs**: Zero new bugs allowed
- **Code Quality**: Maximum 10 new code smells
- **Technical Debt**: Maximum 16 hours for new code

#### Deployment Environments
- **Development**: `course-creator-dev` namespace, 1 replica per service
- **Staging**: `course-creator-staging` namespace, 2 replicas per service  
- **Production**: `course-creator-prod` namespace, 3+ replicas with autoscaling

#### Pipeline Stages
1. **Code Quality** - Linting, formatting, SonarQube analysis
2. **Testing** - Unit, integration, and E2E tests
3. **Security** - Vulnerability scanning, secret detection
4. **Build** - Docker image building and security scanning
5. **Deploy** - Multi-environment Kubernetes deployment with health checks
6. **Notify** - Slack/email notifications

#### Emergency Procedures
```bash
# Force deployment (use only for critical fixes)
jenkins-cli build course-creator-pipeline -p FORCE_DEPLOY=true -p DEPLOY_ENVIRONMENT=prod

# Rollback deployment
kubectl rollout undo deployment/service-name -n course-creator-prod
```

See `docs/ci-cd-pipeline.md` for comprehensive pipeline documentation.

### Git Integration
All code changes must go through the CI/CD pipeline:

#### Git Workflow:
1. **Feature Branch** - Create feature branch from main
   ```bash
   git checkout -b feature/new-functionality
   ```

2. **Development** - Follow TDD process with frequent commits
   ```bash
   git add .
   git commit -m "feat: add failing test for new functionality"
   git commit -m "feat: implement minimal code to pass test"
   git commit -m "refactor: clean up implementation"
   ```

3. **Pre-commit Validation** - Ensure code quality before push
   ```bash
   # Run tests
   python -m pytest --cov=services --cov-report=html
   
   # Code formatting
   black services/
   isort services/
   flake8 services/
   
   # Frontend tests
   npm test
   npm run lint
   ```

4. **Push and Pull Request** - Push to remote and create PR
   ```bash
   git push origin feature/new-functionality
   # Create PR via GitHub/GitLab interface
   ```

#### CI/CD Pipeline Requirements:
- **Automated Testing** - All tests must pass (unit, integration, e2e)
- **Code Coverage** - Minimum 80% code coverage required
- **Code Quality** - Must pass linting and formatting checks
- **Security Scanning** - Automated security vulnerability checks
- **Service Health** - All services must pass health checks
- **Documentation** - Update relevant documentation and CLAUDE.md

#### Pipeline Stages:
1. **Build** - Install dependencies and build application
2. **Test** - Run unit tests, integration tests, and e2e tests
3. **Quality** - Run code quality checks (linting, formatting, security)
4. **Deploy** - Deploy to staging environment
5. **Verify** - Run smoke tests and health checks
6. **Promote** - Merge to main and deploy to production

## Development Workflow

### Adding New Features (Following TDD and SOLID)
1. **Analysis** - Identify which service(s) need modification following SOLID principles
2. **Test First** - Write failing tests that define the expected behavior
3. **Interface Design** - Design interfaces and abstractions (following DIP)
4. **Implementation** - Implement minimal code to pass tests (following SRP, OCP, LSP, ISP)
5. **Refactor** - Clean up code while maintaining test coverage
6. **Integration** - Add API endpoints and update service integration
7. **Frontend** - Update frontend interface and JavaScript
8. **Documentation** - Update configuration and documentation
9. **CI/CD** - Push through git workflow and CI/CD pipeline

### Service Communication
Services communicate via HTTP APIs. Use the service registry pattern where services discover each other through configuration.

### Content Upload/Export Workflow
For content-related features, the flow is:
1. Frontend uploads via drag-and-drop interface
2. Content Management Service processes and stores files
3. AI Integration Service generates content from uploads
4. Export functionality provides multiple format options
5. All operations tracked with comprehensive metadata

## Monitoring and Logging

### Log Files
Service logs are in `logs/` directory and `services/*/outputs/` for individual services.

### Health Checks
All services expose `/health` endpoints for monitoring. The platform startup script uses these for dependency management.

## Common Development Patterns

### Service Structure
Each service follows a consistent structure:
- `main.py` - FastAPI application with endpoints
- `models/` - Modular Pydantic data models
- `services/` - Modular business logic
- `repositories/` - Data access layer
- `config.py` - Service configuration
- `run.py` - Service startup script

### Frontend Architecture
The frontend uses a **modern ES6 module system** with the following structure:
- `js/main-modular.js` - Main application entry point
- `js/modules/` - Modular components including:
  - `auth.js` - Enhanced authentication with lab lifecycle integration
  - `lab-lifecycle.js` - Automatic lab container lifecycle management
  - `navigation.js` - Site navigation
  - `notifications.js` - User notifications and alerts
- `js/config.js` - Configuration (supports both ES6 modules and legacy)
- Individual page scripts:
  - `instructor-dashboard.js` - Enhanced with lab container management
  - `student-dashboard.js` - Integrated with automatic lab lifecycle
  - Other dashboard scripts
- Multi-IDE Lab Interface:
  - `lab-multi-ide.html` - Comprehensive multi-IDE interface with IDE selection, status monitoring, and panel management
  - `lab.html` - Legacy terminal-only interface (still supported)

**Note**: The legacy `main.js` system has been removed in favor of the modular approach with lab container integration. The new multi-IDE interface provides a modern development environment with multiple IDE options.

### Error Handling
Use FastAPI HTTPException for API errors with appropriate status codes and error messages.

### Async Operations
Services use async/await patterns for I/O operations, especially for AI content generation and file processing.

## MCP Integration

### Unified MCP Server
The platform includes a Model Context Protocol (MCP) server for Claude Desktop integration:

```bash
# MCP server control
./mcp-control.sh {start|stop|status|test|run|logs}

# Direct execution
python mcp_server_unified.py [--daemon|--status|--stop]
```

### MCP Features
- Real-time service health monitoring (including lab container manager)
- Platform overview and statistics with lab container metrics
- Log access and analysis across all services
- Content management status
- Lab container system monitoring and management
- Test execution capabilities including lab container tests

### Configuration
Claude Desktop config: `~/.config/claude-desktop/claude_desktop_config.json`

The MCP server provides comprehensive platform management capabilities directly through Claude Desktop interface, including the new lab container management system.

## Docker Deployment (v2.0)

### Full Containerization
The platform is now fully containerized with Docker Compose:

```bash
# Production deployment
docker-compose up -d

# Development with hot reload
docker-compose -f docker-compose.dev.yml up

# Testing environment
docker-compose -f docker-compose.test.yml up --build

# Scale specific services
docker-compose up -d --scale lab-manager=3
```

### Container Architecture
- **Shared Database** - Single PostgreSQL instance for all services
- **Lab Manager** - Docker-in-Docker (DinD) for student lab containers
- **Persistent Volumes** - Student lab data preserved across restarts
- **Network Isolation** - Secure communication between services
- **Resource Limits** - CPU/memory constraints for student containers

### Key Docker Files
- `docker-compose.yml` - Main production orchestration
- `docker-compose.dev.yml` - Development with hot reload
- `docker-compose.test.yml` - Testing environment
- `lab-containers/Dockerfile` - Lab manager service container
- Individual service Dockerfiles in each service directory

## Lab Container System Architecture Notes (v2.1 - Multi-IDE Edition)

**Key Implementation Details:**
- Lab containers require Docker daemon access (`/var/run/docker.sock` mount)
- Dynamic image building uses temporary directories for Dockerfile generation with multi-IDE support
- Student lab persistence achieved through Docker volume mounts (preserved across IDE switches)
- Enhanced resource limits for multi-IDE support (CPU: 1.5 cores, Memory: 2GB for multi-IDE, 1GB for single IDE)
- Multi-IDE port allocation with dynamic port management (8080-8083 range)
- Network isolation prevents student containers from accessing other services
- Automatic cleanup prevents resource leaks from abandoned containers
- Health checks ensure container and IDE service availability before student access
- IDE service management with real-time status monitoring and switching capabilities

**Testing in Non-Docker Environments:**
- Unit and integration tests use comprehensive mocking for Docker operations
- Frontend tests simulate browser behavior without requiring Docker
- E2E tests use browser simulation with mocked API responses
- Full Docker-based testing requires actual Docker daemon access

**Production Deployment Considerations:**
- Docker-in-Docker requires privileged container or socket mounting
- Persistent storage needs adequate disk space for student work
- Load balancing may require session affinity for lab container access
- Monitoring should include container resource usage and health metrics