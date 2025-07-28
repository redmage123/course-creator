# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Version**: 2.2.0 - Complete Quiz Management System with Course Publishing  
**Last Updated**: 2025-07-28

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
4. **Course Management Service** (Port 8004) - CRUD operations for courses, enrollment, **bi-directional feedback system**
5. **Content Management Service** (Port 8005) - File upload/download, multi-format export
6. **Lab Container Manager Service** (Port 8006) - Individual student Docker container management with multi-IDE support
7. **Analytics Service** (Port 8007) - Student analytics, progress tracking, learning insights, PDF report generation

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

## Comprehensive Quiz Management System (v2.2)

The platform includes a complete quiz management system enabling instructors to publish/unpublish quizzes per course instance with full student access control and analytics integration:

### Instructor Quiz Publication Management
- **Course Instance-Specific Publishing** - Publish/unpublish quizzes for individual course instances with separate control per session
- **Modal-Based Interface** - Professional tabbed interface with instance navigation and real-time status updates
- **Bulk Operations** - Publish or unpublish all quizzes for a course instance with single-click batch operations
- **Individual Quiz Controls** - Granular publish/unpublish controls with configuration options and analytics viewing
- **Real-time Analytics** - Live display of student attempts, average scores, and participation metrics
- **Publication Status Tracking** - Visual indicators showing published status, publication dates, and availability windows

### Student Quiz Access Control
- **Enrollment-Based Access** - Only enrolled students can access quizzes for their specific course instance
- **Publication Visibility** - Students see only published quizzes; unpublished quizzes remain completely hidden
- **Attempt Limitations** - Configurable maximum attempts per quiz with remaining attempt tracking
- **Time Limits** - Optional time restrictions with automatic submission when time expires
- **Progress Tracking** - Student dashboard shows quiz completion status and scores achieved

### Quiz Attempt Storage & Analytics Integration
- **Course Instance Tracking** - All quiz attempts stored with `course_instance_id` for precise analytics segmentation
- **Student Performance Data** - Comprehensive storage of student answers, scores, attempt timing, and completion status
- **Analytics Service Integration** - Quiz data fully integrated with analytics service for instructor reporting and insights
- **Progress Monitoring** - Real-time tracking of student quiz participation and performance trends
- **Attempt History** - Complete audit trail of all quiz attempts with detailed scoring and timing information

### Database Schema & API Architecture
```sql
-- Core quiz management tables
quiz_publications        -- Course instance-specific quiz publication control
quiz_attempts           -- Student quiz attempts with course_instance_id for analytics
student_course_enrollments -- Enrollment-based access control
course_instances        -- Session-specific course management
```

### Quiz Management API Endpoints
```http
# Quiz Publication Management
GET  /course-instances/{instance_id}/quiz-publications  # Get quiz publication status for course instance
POST /quizzes/publish                                   # Publish/unpublish quiz for course instance
PUT  /quiz-publications/{publication_id}               # Update quiz publication settings

# Student Quiz Access
GET  /course-instances/{instance_id}/published-quizzes  # Get student-accessible published quizzes
POST /quiz-attempts                                     # Submit student quiz attempt with analytics data
GET  /quiz-attempts/student/{student_id}               # Get student's quiz attempt history
```

### Frontend Implementation Features
- **Responsive Modal Interface** - Professional tabbed modal with course instance navigation and mobile support
- **Interactive Status Controls** - Real-time publish/unpublish buttons with loading states and confirmation dialogs
- **Analytics Dashboard Integration** - Live display of quiz performance metrics and student participation data
- **Professional Styling** - Comprehensive CSS with animations, hover effects, and consistent design language
- **JavaScript Module Architecture** - Modern ES6 modules with proper error handling and notification systems

### Key Quiz Management Files
- `services/course-management/course_publishing_api.py` - Quiz publication API endpoints with analytics integration
- `services/course-management/email_service.py` - Hydra-configured email service for notifications
- `data/migrations/011_update_quiz_attempts_table.sql` - Database migration adding course_instance_id for analytics
- `frontend/instructor-dashboard.html` - Integrated quiz management UI with modal interface
- `frontend/css/main.css` - Comprehensive CSS styling for quiz management components
- `tests/quiz-management/` - Complete test suite including API, frontend, and integration testing

### Student Quiz Experience Workflow
1. **Access** - Students log in via unique enrollment URLs and see their course dashboard
2. **Quiz Discovery** - Published quizzes appear automatically in student quiz section (refresh required for new publications)
3. **Quiz Taking** - Interactive quiz interface with timer, progress tracking, and question navigation
4. **Results** - Immediate score display with pass/fail status and detailed performance feedback
5. **Attempt Tracking** - Students can view attempt history and remaining attempts available

### Configuration Management (Hydra Integration)
- **Email Configuration** - Quiz notification emails use Hydra configuration management instead of environment variables
- **Service Configuration** - All quiz management services properly integrated with platform configuration hierarchy
- **Environment Support** - Development, staging, and production configuration support with proper defaults

## Comprehensive Feedback System (v2.1)

The platform includes a complete bi-directional feedback system enabling rich communication between students and instructors:

### Bi-Directional Feedback Architecture
- **Course Feedback** - Students provide structured feedback on courses, instructors, content quality, and learning outcomes
- **Student Assessment Feedback** - Instructors provide detailed feedback on individual student progress, performance, and development
- **Real-time Analytics** - Comprehensive feedback analytics with rating aggregation and trend analysis
- **Multi-format Responses** - Support for star ratings, text feedback, categorical assessments, and structured forms

### Student Course Feedback Features
- **Star Rating System** - 1-5 star ratings for overall course, instructor, content quality, and difficulty assessment
- **Structured Categories** - Predefined feedback areas including content relevance, instructor effectiveness, pace, and resources
- **Open-ended Responses** - Free-form text feedback for detailed comments and suggestions
- **Anonymous Options** - Students can choose to provide anonymous feedback to encourage honest responses
- **Real-time Submission** - Instant feedback submission with confirmation and thank-you messages

### Instructor Student Feedback Features
- **Comprehensive Assessment Forms** - Detailed evaluation templates covering academic performance, participation, and soft skills
- **Progress Tracking** - Assessment of student improvement trends with 1-5 scale ratings
- **Personalized Recommendations** - Specific, actionable feedback for student development
- **Achievement Recognition** - Highlighting notable accomplishments and milestones
- **Intervention Alerts** - Structured feedback for students needing additional support
- **Privacy Controls** - Instructors can control whether feedback is shared with students immediately

### Feedback Management Dashboard
- **Instructor Analytics View** - Aggregated feedback statistics, rating trends, and response analysis
- **Student Feedback History** - Complete record of all feedback received with filtering and search capabilities
- **Bulk Operations** - Mass feedback operations for class-wide assessments and notifications
- **Export Capabilities** - PDF and Excel export of feedback data for institutional reporting
- **Response Management** - Tools for instructors to respond to student feedback and concerns

### Database Schema & API Endpoints
```sql
-- Core feedback tables
course_feedback          -- Student ratings and comments on courses
student_feedback         -- Instructor assessments of students  
feedback_responses       -- Responses and follow-up communications
feedback_analytics       -- Aggregated statistics and trend data
```

### Feedback System API Endpoints
```http
# Course Feedback (Student → Course)
POST /feedback/course                    # Submit course feedback
GET  /feedback/course/{course_id}        # Get course feedback summary
GET  /feedback/course/student/{user_id}  # Get student's feedback history

# Student Feedback (Instructor → Student)  
POST /feedback/student                   # Submit student assessment
GET  /feedback/student/{user_id}         # Get student feedback history
PUT  /feedback/student/{feedback_id}     # Update feedback visibility

# Analytics & Management
GET  /feedback/analytics/{course_id}     # Course feedback analytics
GET  /feedback/summary/instructor/{id}   # Instructor feedback dashboard
POST /feedback/bulk                      # Bulk feedback operations
```

### Key Feedback System Files
- `services/course-management/main.py` - Feedback API endpoints with full CRUD operations
- `data/migrations/008_add_feedback_system.sql` - Complete database schema for feedback system
- `frontend/js/modules/feedback-manager.js` - Comprehensive JavaScript feedback management module
- `frontend/css/main.css` - Complete CSS styling for feedback forms and UI components
- `frontend/js/student-dashboard.js` - Student feedback submission integration
- `frontend/js/modules/instructor-dashboard.js` - Instructor feedback management and analytics
- `test_feedback_final.py` - Comprehensive test suite with 100% pass rate

### Frontend Integration Features
- **Dynamic Form Generation** - JavaScript-generated feedback forms with validation and user experience optimization
- **Real-time Star Ratings** - Interactive star rating components with hover effects and animations
- **Modal Overlay System** - Clean, accessible modal dialogs for feedback submission and viewing
- **Responsive Design** - Mobile-friendly feedback interfaces with touch-optimized controls
- **Progress Indicators** - Visual feedback on submission status and form completion
- **Error Handling** - Comprehensive client-side validation with helpful error messages

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
- `tests/unit/` - Component-level tests including lab container and feedback system unit tests
- `tests/integration/` - Service interaction tests with lab lifecycle and feedback integration
- `tests/frontend/` - JavaScript module testing with browser simulation for all components
- `tests/e2e/` - Full workflow tests including complete lab container and feedback system lifecycles
- `tests/security/` - Authentication and authorization tests
- `tests/performance/` - Load testing
- `tests/quiz-management/` - Comprehensive quiz management system testing
- `tests/validation/` - System-wide validation and health checks
- `tests/email-integration/` - Email service and Hydra configuration testing
- `tests/file-operations/` - File management and student file system testing
- `tests/lab-systems/` - Lab container creation and management testing

### Feedback System Testing (v2.1)
- **Comprehensive Test Suite** - `test_feedback_final.py` - Complete feedback system validation (6/6 tests passing at 100%)
- **Component Tests** - Individual testing of feedback manager, CSS styles, dashboard integration
- **Database Schema Tests** - Validation of feedback system database tables and migrations
- **API Endpoint Tests** - Complete testing of all feedback REST API endpoints
- **Frontend Integration Tests** - JavaScript module testing for student and instructor feedback workflows
- **Extended Test Suite** - `test_feedback_system.py` - Detailed component-by-component validation (7/7 tests passing)

### Quiz Management System Testing (v2.2)
- **API Testing** - `tests/quiz-management/test_quiz_api_functionality.py` - Complete API endpoint validation
- **Database Testing** - `tests/quiz-management/test_comprehensive_quiz_management.py` - Full database workflow testing  
- **Frontend Testing** - `tests/quiz-management/test_frontend_quiz_management.py` - JavaScript functionality validation
- **Interactive Testing** - `tests/quiz-management/test_quiz_management_frontend.html` - Browser-based testing interface
- **System Validation** - `tests/validation/final_quiz_management_validation.py` - Comprehensive system validation (12/12 components passing)
- **Integration Coverage** - Database schema, API endpoints, frontend UI, analytics integration, and student access control

### Lab Container Testing (v2.1 - Multi-IDE Edition)
- **Unit Tests** - `tests/unit/lab_container/test_lab_manager_service.py` - Core lab manager functionality with multi-IDE support
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

## Common Issues and Troubleshooting

### Service Startup Issues (Resolved v2.1)
Recent fixes have resolved common startup problems:

#### Pydantic Version Compatibility
- **Issue**: Services failing with `'regex' is removed. use 'pattern' instead` error
- **Resolution**: Updated all Pydantic Field definitions from `regex=` to `pattern=` across all services
- **Affected Services**: Course Management, User Management, Content Storage
- **Status**: ✅ Resolved

#### Docker Health Check Failures
- **Issue**: Frontend service showing as unhealthy despite working correctly
- **Root Cause**: Health check using `localhost` resolving to IPv6 `[::1]` while nginx listening on IPv4
- **Resolution**: Updated health check in docker-compose.yml to use `127.0.0.1:3000/health`
- **Status**: ✅ Resolved

#### Container Rebuild Issues
- **Issue**: Code changes not reflected in running containers
- **Resolution**: Use `docker build --no-cache` and ensure proper container recreation
- **Best Practice**: Always stop and remove containers before recreating with new images

### Current Platform Status (v2.1)
All services verified healthy and operational:
- ✅ Frontend (port 3000) - Nginx with proper health checks
- ✅ User Management (port 8000) - Authentication and RBAC
- ✅ Course Generator (port 8001) - AI content generation
- ✅ Content Storage (port 8003) - File management
- ✅ Course Management (port 8004) - Course CRUD + Feedback System
- ✅ Content Management (port 8005) - Upload/export functionality
- ✅ Lab Manager (port 8006) - Multi-IDE container management
- ✅ Analytics (port 8007) - Analytics + PDF generation
- ✅ PostgreSQL (port 5433) - Database
- ✅ Redis (port 6379) - Caching and sessions

### Diagnostic Commands
```bash
# Check all service health
docker ps --format "table {{.Names}}\t{{.Status}}"

# View service logs
docker logs [service-name] --tail 20

# Test individual service health endpoints
curl -s http://localhost:8000/health  # User Management
curl -s http://localhost:8001/health  # Course Generator
curl -s http://localhost:3000/health  # Frontend
# ... etc for all services

# Run comprehensive tests
python test_feedback_final.py        # Feedback system
python tests/run_all_tests.py        # All test suites
```

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