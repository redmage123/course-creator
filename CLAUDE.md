# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Platform Management
```bash
# Start entire platform with dependency management
./app-control.sh start

# Other useful app-control.sh commands:
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

# Or start individual services using app-control.sh
./app-control.sh start user-management
./app-control.sh start course-generator
# etc...

# Serve frontend
cd frontend && python -m http.server 8080
# Or: npm start (serves on port 8080)
```

### Testing
```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest -m unit          # Unit tests only
python -m pytest -m integration   # Integration tests only
python -m pytest -m e2e          # End-to-end tests only

# Run tests with coverage
python -m pytest --cov=services --cov-report=html

# Run frontend tests
npm test                          # Jest unit tests
npm run test:e2e                 # Playwright E2E tests
npm run test:all                 # All frontend tests
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
The platform uses a microservices architecture with 5 core backend services:

1. **User Management Service** (Port 8000) - Authentication, user profiles, RBAC
2. **Course Generator Service** (Port 8001) - AI-powered content generation using Anthropic/OpenAI
3. **Course Management Service** (Port 8004) - CRUD operations for courses, enrollment
4. **Content Storage Service** (Port 8003) - File storage, content versioning
5. **Content Management Service** (Port 8005) - File upload/download, multi-format export

### Service Dependencies
Services must be started in dependency order:
- User Management → Course Generator → Course Management → Content Storage → Content Management

The `app-control.sh` script handles this automatically with health checks.

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

The platform recently added comprehensive content upload/download functionality:

### File Processing Pipeline
1. **Upload** - Drag-and-drop interface supports PDF, DOCX, PPTX, JSON
2. **Processing** - `file_processors.py` extracts text and structure
3. **AI Integration** - `ai_integration.py` generates course content from uploads
4. **Storage** - `storage_manager.py` handles file storage with metadata
5. **Export** - Multi-format export (PowerPoint, JSON, PDF, Excel, ZIP, SCORM)

### Key Files
- `services/content-management/main.py` - FastAPI service with upload/export endpoints
- `services/content-management/models.py` - Pydantic models and validation
- `frontend/instructor-dashboard.html` - Tabbed content management interface
- `frontend/js/instructor-dashboard.js` - File upload/download functionality

## Database Schema

### Core Tables
- `users` - User accounts with role-based access
- `courses` - Course metadata and content
- `enrollments` - Student-course relationships
- `slides` - Generated slide content
- `lab_sessions` - Interactive lab environment data

### Migrations
Database migrations are in `data/migrations/` and run via `setup-database.py`.

## Testing Strategy

### Test Organization
- `tests/unit/` - Component-level tests
- `tests/integration/` - Service interaction tests  
- `tests/e2e/` - Full workflow tests using Playwright
- `tests/security/` - Authentication and authorization tests
- `tests/performance/` - Load testing

### Test Configuration
- `pytest.ini` - Python test configuration with coverage requirements (80% minimum)
- `package.json` - JavaScript test configuration with Jest and Playwright
- Tests use markers for categorization (unit, integration, e2e, security, etc.)

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

### CI/CD Pipeline with Git Integration
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
- `js/modules/` - Modular components (auth, navigation, notifications, etc.)
- `js/config.js` - Configuration (supports both ES6 modules and legacy)
- Individual page scripts (instructor-dashboard.js, student-dashboard.js, etc.)

**Note**: The legacy `main.js` system has been removed in favor of the modular approach.

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
- Real-time service health monitoring
- Platform overview and statistics
- Log access and analysis
- Content management status
- Test execution capabilities

### Configuration
Claude Desktop config: `~/.config/claude-desktop/claude_desktop_config.json`

The MCP server provides comprehensive platform management capabilities directly through Claude Desktop interface.