# Course Creator Platform

A comprehensive web-based platform for creating, managing, and delivering interactive programming courses with hands-on lab environments and AI-powered content generation.

## 🚀 Features

### For Instructors
- **AI-Powered Course Generation**: Generate complete courses with syllabus, slides, exercises, and quizzes
- **Individual Lab Container Management**: Create and manage isolated Docker containers for each student
- **Dynamic Image Building**: Build custom lab environments on-demand with specific packages and configurations
- **Real-time Lab Monitoring**: Monitor all student lab sessions with pause/resume/stop controls
- **Template-Based Content Generation**: Upload custom templates for AI to generate structured content
- **Comprehensive Quiz System**: Generate and manage quizzes with automatic grading and analytics
- **Enhanced Content Management**: Drag-and-drop interface for uploading course materials (PDF, DOCX, PPTX, JSON)
- **Comprehensive Student Analytics**: Real-time tracking of student progress, lab usage, quiz performance, and engagement metrics with interactive dashboards
- **Multi-Format Export**: Export content to PowerPoint, PDF, Excel, SCORM, ZIP formats
- **Instructor Lab Environment**: Create personal lab environments for course development and testing

### For Students
- **Multi-IDE Lab Environment**: Choose from VSCode Server, JupyterLab, IntelliJ IDEA, or Terminal
- **Seamless IDE Switching**: Switch between development environments without losing work
- **Persistent Lab Containers**: Individual Docker containers that maintain state across sessions and IDE switches
- **Automatic Lab Lifecycle**: Labs auto-start on login, pause on logout, resume on return
- **Real-time Coding Environment**: Full-featured development environments with syntax highlighting, IntelliSense, and debugging
- **AI-Powered Assistance**: Get help and explanations while working in lab environments
- **Interactive Quiz System**: Take quizzes with immediate feedback, explanations, and progress tracking
- **Seamless Authentication**: Integrated login/logout with automatic lab session management
- **Secure Isolation**: Each student gets their own completely isolated environment

### For Administrators
- **User Management**: Manage instructor and student accounts with RBAC
- **Platform Analytics**: System-wide usage and performance metrics
- **MCP Integration**: Model Context Protocol server for enhanced AI interactions

## 🏗️ Architecture

The platform follows a microservices architecture with 7 core backend services:

```
course-creator/
├── frontend/                    # Static HTML/CSS/JavaScript frontend
│   ├── instructor-dashboard.html # Enhanced instructor interface with lab management
│   ├── student-dashboard.html   # Student learning interface with lab integration
│   ├── lab-multi-ide.html       # Multi-IDE lab environment with VSCode, Jupyter, IntelliJ
│   ├── lab.html                 # Legacy terminal-only lab environment
│   └── js/modules/             # Modular ES6 components (auth, lab-lifecycle, etc.)
├── services/                   # Backend microservices
│   ├── user-management/        # Authentication & user profiles (Port 8000)
│   ├── course-generator/       # AI content generation (Port 8001)
│   ├── content-storage/        # File storage & versioning (Port 8003)
│   ├── course-management/      # Course CRUD operations (Port 8004)
│   ├── content-management/     # Upload/download & export (Port 8005)
│   └── analytics/              # Student analytics & progress tracking (Port 8007)
├── lab-containers/             # Individual student lab container service (Port 8006)
│   ├── main.py                 # FastAPI lab manager with Docker and multi-IDE integration
│   ├── Dockerfile              # Lab manager container
│   ├── lab-images/             # Multi-IDE Docker images
│   │   ├── multi-ide-base/     # Base multi-IDE image with VSCode, Jupyter, IntelliJ
│   │   └── python-lab-multi-ide/ # Python-specific multi-IDE environment
│   └── templates/              # Lab environment templates
├── config/                     # Hydra configuration files
├── data/migrations/           # Database migrations
├── tests/                     # Comprehensive test suite (unit, integration, e2e, frontend)
├── docker-compose.yml         # Full platform orchestration
└── docs/                      # Documentation
```

### Service Dependencies
Services start in dependency order with health checks:
User Management → Course Generator → Course Management → Content Storage → Content Management → Lab Container Manager → Analytics Service

## 🛠️ Technology Stack

### Frontend
- **HTML5/CSS3/JavaScript (ES6 modules)** - Modern web technologies
- **Bootstrap 5** - UI framework
- **xterm.js** - Terminal emulation for lab environments
- **Marked.js** - Markdown rendering

### Backend
- **Python 3.10+** - Core language
- **FastAPI** - Web framework with asyncio
- **PostgreSQL** - Primary database with asyncpg
- **Redis** - Session management and caching
- **Hydra** - Configuration management
- **JWT** - Authentication tokens

### AI Integration
- **Primary**: Anthropic Claude (configured in config/ai/claude.yaml)
- **Fallback**: OpenAI (optional)
- **Mock data**: Available for development when AI services unavailable

### Infrastructure
- **Docker & Docker Compose** - Full containerization with per-student lab containers
- **Docker-in-Docker (DinD)** - Dynamic container creation for student labs
- **Persistent Storage** - Student work preserved across sessions
- **Nginx** - Reverse proxy and load balancing
- **Prometheus/Grafana** - Monitoring and observability
- **GitHub Actions** - CI/CD with comprehensive pipeline including security scanning

## 🚀 Quick Start

**Get running in under 10 minutes!**

### Prerequisites
- Docker & Docker Compose
- Git
- [Anthropic Claude API Key](https://console.anthropic.com/)

### Installation
```bash
# 1. Clone and configure
git clone https://github.com/your-org/course-creator.git
cd course-creator
cp .env.example .env

# 2. Add your API key to .env file
# ANTHROPIC_API_KEY=your_key_here

# 3. Deploy everything with Docker
./app-control.sh docker-start

# 4. Create admin user
python create-admin.py
```

### Access Your Platform
- **🏠 Platform Home**: http://localhost:3000
- **👨‍🏫 Instructor Dashboard**: http://localhost:3000/instructor-dashboard.html
- **👨‍🎓 Student Dashboard**: http://localhost:3000/student-dashboard.html
- **🔧 Admin Panel**: http://localhost:3000/admin.html
- **💻 Interactive Labs**: http://localhost:3000/lab.html

## 📚 Documentation

- **⚡ Quick Start**: [`QUICKSTART.md`](QUICKSTART.md) - Get running in 10 minutes
- **📖 Complete Runbook**: [`docs/RUNBOOK.md`](docs/RUNBOOK.md) - Detailed installation & deployment
- **👥 User Guide**: [`docs/USER-GUIDE.md`](docs/USER-GUIDE.md) - How to use the platform
- **🔧 CI/CD Pipeline**: [`docs/ci-cd-pipeline.md`](docs/ci-cd-pipeline.md) - Jenkins & SonarQube setup
- **⚙️ Technical Details**: [`CLAUDE.md`](CLAUDE.md) - Developer guidance

## 🛠️ Advanced Installation

### Development Setup (Native Python)
```bash
# Clone and setup virtual environment
git clone https://github.com/your-org/course-creator.git
cd course-creator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Setup database and create admin
python setup-database.py
python create-admin.py

# Start services natively
./app-control.sh start
   
   # Or using app-control.sh for development
   ./app-control.sh start
   
   # Check service status
   ./app-control.sh status
   
   # View logs
   ./app-control.sh logs <service>
   ```

6. **Serve frontend**
   ```bash
   # Using Python's built-in server
   cd frontend && python -m http.server 8080
   
   # Or using npm
   npm start
   ```

7. **Access the application**
   - Frontend: http://localhost:8080
   - Instructor Dashboard: http://localhost:8080/instructor-dashboard.html (with lab container management)
   - Student Dashboard: http://localhost:8080/student-dashboard.html (with automatic lab lifecycle)
   - Multi-IDE Lab Environment: http://localhost:8080/lab-multi-ide.html (VSCode, Jupyter, IntelliJ)
   - Legacy Lab Environment: http://localhost:8080/lab.html (terminal-only)
   - API Documentation: http://localhost:8001/docs
   - Lab Manager API: http://localhost:8006/docs

### Using app-control.sh

The platform includes a comprehensive control script:

```bash
# Start all services
./app-control.sh start

# Start specific service
./app-control.sh start user-management

# Stop all services
./app-control.sh stop

# Restart services
./app-control.sh restart

# Check status
./app-control.sh status

# View logs
./app-control.sh logs course-generator
```

## 📖 Usage Guide

### Creating Your First Course

1. **Access Instructor Dashboard**
   - Navigate to `/instructor-dashboard.html`
   - Log in with instructor credentials

2. **Generate Course Content**
   - Use the tabbed interface to:
     - Generate syllabus from course description
     - Create slides from syllabus content
     - Generate exercises and quizzes
     - Set up lab environments

3. **Upload Content**
   - Use drag-and-drop interface for PDF, DOCX, PPTX, JSON files
   - AI will process and generate course content from uploads

4. **Export Content**
   - Export to multiple formats: PowerPoint, PDF, Excel, SCORM, ZIP

### Managing Multi-IDE Lab Container Environments

1. **Create Multi-IDE Student Labs**
   - Each student gets their own isolated Docker container with multiple IDE options
   - Dynamic image building with VSCode Server, JupyterLab, IntelliJ IDEA, and Terminal
   - Template-based lab creation for consistent multi-IDE environments
   - Instructor can create personal lab environments with full IDE access for testing

2. **Multi-IDE Environment Features**
   - **VSCode Server**: Full web-based development environment with extensions, IntelliSense, and debugging
   - **JupyterLab**: Interactive notebook environment for data science with matplotlib, pandas, numpy
   - **IntelliJ IDEA**: Professional IDE via JetBrains Projector (optional, resource-intensive)
   - **Terminal**: Traditional command-line interface with xterm.js
   - **Real-time IDE Status**: Live health monitoring and availability indicators
   - **Seamless Switching**: Change IDEs without losing work or session state

3. **Comprehensive Lab Management**
   - Real-time monitoring of all student lab containers with IDE usage tracking
   - View which IDEs students are using and performance metrics
   - Pause, resume, and stop individual or bulk lab sessions
   - View detailed lab status, resource usage, and IDE health logs
   - Enhanced resource allocation for multi-IDE support (2GB memory, 150% CPU)
   - Automatic cleanup of expired lab sessions

4. **Student Lab Experience**
   - Automatic lab initialization on login with preferred IDE selection
   - Persistent storage - work saved across sessions and IDE switches
   - IDE selection interface with real-time status indicators
   - Seamless pause/resume on browser tab changes
   - Automatic cleanup on logout with work preservation

5. **Advanced Multi-IDE Features**
   - Dynamic port allocation for each IDE service (8080-8083)
   - Resource limits and concurrent lab management with multi-IDE scaling
   - Health monitoring and automatic recovery for each IDE service
   - Performance analytics and IDE usage tracking
   - Custom Dockerfile support for specialized multi-IDE environments
   - IDE-specific configuration and extension management

### Quiz System

1. **Generate Quizzes**
   - Auto-generate from course content
   - Multiple question types supported
   - Automatic grading with explanations

2. **Student Experience**
   - Take quizzes with immediate feedback
   - View explanations for incorrect answers
   - Track progress and scores

## 🔧 Configuration

### Environment Variables (.cc_env)

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5433
DB_NAME=course_creator
DB_USER=course_user
DB_PASSWORD=your_password

# API Keys
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Service Configuration

Each service uses Hydra configuration:
- `config/config.yaml` - Main configuration
- `config/services/` - Service-specific configs
- `config/ai/claude.yaml` - AI service configuration

### Frontend Configuration

Update `frontend/js/config.js`:

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

## 🧪 Testing

### Development Standards

The platform follows **SOLID principles** and **Test Driven Development (TDD)**:

1. **Single Responsibility Principle** - Each class has one reason to change
2. **Open/Closed Principle** - Open for extension, closed for modification
3. **Liskov Substitution Principle** - Subtypes must be substitutable
4. **Interface Segregation Principle** - Many client-specific interfaces
5. **Dependency Inversion Principle** - Depend on abstractions

### TDD Workflow

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

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest -m unit          # Unit tests only
python -m pytest -m integration   # Integration tests only
python -m pytest -m e2e          # End-to-end tests only

# Lab container system tests (comprehensive)
python run_lab_tests.py          # All lab container tests with reports
python run_lab_tests.py --suite frontend  # Frontend lab integration tests
python run_lab_tests.py --suite e2e       # E2E lab system tests

# Run tests with coverage (80% minimum required)
python -m pytest --cov=services --cov-report=html

# Frontend tests
npm test                          # Jest unit tests
npm run test:e2e                 # Playwright E2E tests
npm run test:all                 # All frontend tests

# Docker-based testing (requires Docker)
docker-compose -f docker-compose.test.yml up --build
```

### Code Quality

```bash
# Lint JavaScript
npm run lint
npm run lint:fix

# Python formatting
black services/
isort services/
flake8 services/
```

## 📚 API Documentation

### Core Endpoints

**User Management (Port 8000)**
```http
POST /auth/login
GET /auth/profile
GET /users
POST /users
```

**Course Generator (Port 8001)**
```http
POST /generate/syllabus
POST /generate/slides
POST /exercises/generate
POST /quiz/generate-for-course
GET /exercises/{course_id}
GET /quiz/course/{course_id}
```

**Course Management (Port 8004)**
```http
GET /courses
POST /courses
GET /courses/{course_id}
PUT /courses/{course_id}
DELETE /courses/{course_id}
```

**Content Storage (Port 8003)**
```http
POST /upload
GET /download/{file_id}
DELETE /files/{file_id}
```

**Content Management (Port 8005)**
```http
POST /upload
GET /export/{format}
GET /files
```

**Lab Container Manager (Port 8006)**
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

# Multi-IDE Management
GET  /labs/{lab_id}/ides     # Get available IDEs for lab
POST /labs/{lab_id}/ide/switch # Switch preferred IDE
GET  /labs/{lab_id}/ide/status # Get IDE health status
```

**Analytics Service (Port 8007)**
```http
POST /activities/track       # Track student activities
POST /lab-usage/track       # Track lab usage metrics
POST /quiz-performance/track # Track quiz performance
POST /progress/update       # Update student progress
GET  /analytics/student/{id} # Get student analytics
GET  /analytics/course/{id}  # Get course analytics
GET  /health                # Analytics service health check
```

For complete API documentation, visit the `/docs` endpoint on each service.

## 🚀 Deployment

### Git Workflow with CI/CD

The platform uses a comprehensive CI/CD pipeline:

```bash
# 1. Feature Branch
git checkout -b feature/new-functionality

# 2. Development with TDD
git commit -m "feat: add failing test for new functionality"
git commit -m "feat: implement minimal code to pass test"
git commit -m "refactor: clean up implementation"

# 3. Pre-commit Validation
python -m pytest --cov=services --cov-report=html
black services/
isort services/
flake8 services/
npm test
npm run lint

# 4. Push and Pull Request
git push origin feature/new-functionality
```

### CI/CD Pipeline Stages

1. **Build** - Install dependencies and build application
2. **Test** - Run unit, integration, and e2e tests
3. **Quality** - Code quality checks (linting, formatting, security)
4. **Deploy** - Deploy to staging environment
5. **Verify** - Run smoke tests and health checks
6. **Promote** - Merge to main and deploy to production

### Production Deployment

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Check all services are healthy
docker-compose ps

# Monitor logs
docker-compose logs -f

# Scale lab manager service if needed
docker-compose up -d --scale lab-manager=3

# Alternative: Using app-control.sh
./app-control.sh start
./app-control.sh status
./app-control.sh logs
```

## 🔒 Security

### Authentication & Authorization
- JWT-based authentication with secure session management
- Role-based access control (Admin, Instructor, Student)
- Secure API endpoints with proper authorization checks

### File Upload Security
- File type validation and size limits
- Content scanning and sanitization
- Secure file storage with access controls

### Infrastructure Security
- HTTPS enforcement with SSL/TLS termination
- Security headers and CORS configuration
- Input validation and sanitization
- SQL injection prevention with parameterized queries
- Container isolation with Docker security best practices
- Resource limits and sandboxing for student lab containers
- Secure file upload with type validation and scanning

## 📊 Monitoring

### MCP Integration

The platform includes a unified MCP server for Claude Desktop integration:

```bash
# MCP server control
./mcp-control.sh {start|stop|status|test|run|logs}

# Direct execution
python mcp_server_unified.py [--daemon|--status|--stop]
```

### Observability

- **Service Health**: Real-time health monitoring
- **Platform Statistics**: Usage and performance metrics
- **Log Analysis**: Centralized log access and analysis
- **Content Management**: Status and metrics

## 🤝 Contributing

### Development Standards

Before contributing, ensure:
- [ ] All tests pass (80% coverage minimum)
- [ ] Code follows SOLID principles
- [ ] TDD workflow followed
- [ ] Documentation updated
- [ ] CI/CD pipeline passes

### Code Review Process

1. **Feature Development** - Follow TDD workflow
2. **Pull Request** - Comprehensive description and tests
3. **Code Review** - Peer review for quality and security
4. **CI/CD Pipeline** - All stages must pass
5. **Merge** - Squash and merge to main

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Troubleshooting

**Common Issues:**

1. **Services won't start**
   ```bash
   # Check service status
   ./app-control.sh status
   
   # Check logs
   ./app-control.sh logs <service>
   
   # Restart services
   ./app-control.sh restart
   ```

2. **Database connection errors**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Reset database
   python setup-database.py --reset
   
   # Verify environment variables
   source .cc_env && echo $DB_PASSWORD
   ```

3. **AI services not working**
   ```bash
   # Check API keys in .cc_env
   grep ANTHROPIC_API_KEY .cc_env
   
   # Test AI service
   curl -X POST http://localhost:8001/test-ai
   ```

### Health Checks

All services expose `/health` endpoints:

```bash
# Check all services
for port in 8000 8001 8003 8004 8005; do
  curl -s http://localhost:$port/health | head -c 50
  echo " - Port $port"
done
```

## 🎯 Current Status

**✅ Completed Features:**
- Core microservices architecture with 7 services
- AI-powered content generation with template support
- **Multi-IDE Lab Containers** - VSCode Server, JupyterLab, IntelliJ IDEA, and Terminal support
- **Individual Docker Lab Containers** - Per-student isolated environments with multi-IDE capabilities
- **Seamless IDE Switching** - Change development environments without losing work
- **Dynamic Image Building** - Custom lab environments with multi-IDE support built on-demand
- **Automatic Lab Lifecycle Management** - Login/logout integration with persistence across IDE switches
- **Comprehensive Instructor Lab Controls** - Real-time monitoring, management, and IDE usage analytics
- **Enhanced Resource Management** - Dynamic allocation for multi-IDE environments (2GB/150% CPU)
- Interactive quiz system with analytics
- Enhanced content management with drag-and-drop upload
- Multi-format export (PowerPoint, PDF, Excel, SCORM, ZIP)
- User management with RBAC and secure authentication
- Database persistence with PostgreSQL (single shared database)
- Full Docker Compose orchestration
- Comprehensive test suite (Unit, Integration, E2E, Frontend) with 22+ passing tests
- CI/CD pipeline with security scanning and automated deployment
- MCP integration for Claude Desktop

**🔄 In Progress:**
- Mobile responsiveness improvements
- Advanced AI features and prompt engineering
- Performance optimization for high-concurrency lab usage

**📋 Planned:**
- Real-time collaboration within lab containers
- Video content support and screen sharing
- Advanced analytics dashboard with detailed lab usage and IDE preferences metrics
- Kubernetes deployment for enterprise scaling
- Payment integration for course marketplace
- Additional IDE integrations (Eclipse, Vim/Neovim, Emacs)

---

**Project Status**: Production Ready with Multi-IDE Lab Container System  
**Version**: 2.1.0  
**Last Updated**: 2025-07-26  
**New in v2.1**: Multi-IDE support (VSCode, Jupyter, IntelliJ), seamless IDE switching, enhanced resource management  
**Previous v2.0**: Individual Docker lab containers, automatic lifecycle management, instructor controls, comprehensive testing

For detailed development information, see [CLAUDE.md](CLAUDE.md) for comprehensive setup and development instructions.