# Course Creator Platform

A comprehensive web-based platform for creating, managing, and delivering interactive programming courses with hands-on lab environments and AI-powered content generation.

## 🚀 Features

### For Instructors
- **AI-Powered Course Generation**: Generate complete courses with syllabus, slides, exercises, and quizzes
- **Interactive Lab Environments**: Create browser-based coding environments with xterm.js
- **Comprehensive Quiz System**: Generate and manage quizzes with automatic grading
- **Content Management**: Upload and manage course materials (PDF, DOCX, PPTX, JSON)
- **Student Progress Tracking**: Monitor student performance and engagement
- **Multi-Format Export**: Export content to PowerPoint, PDF, Excel, SCORM formats

### For Students
- **Interactive Learning**: Access courses with integrated coding environments
- **Real-time Lab Sessions**: Code directly in browser terminals with AI assistance
- **Quiz System**: Take quizzes with immediate feedback and explanations
- **Progress Tracking**: Monitor learning progress and achievements
- **Secure Environment**: Sandboxed lab environments for safe experimentation

### For Administrators
- **User Management**: Manage instructor and student accounts with RBAC
- **Platform Analytics**: System-wide usage and performance metrics
- **MCP Integration**: Model Context Protocol server for enhanced AI interactions

## 🏗️ Architecture

The platform follows a microservices architecture with 5 core backend services:

```
course-creator/
├── frontend/                    # Static HTML/CSS/JavaScript frontend
│   ├── instructor-dashboard.html # Main instructor interface
│   ├── student-dashboard.html   # Student learning interface
│   ├── lab.html                 # Interactive coding environment
│   └── js/modules/             # Modular ES6 components
├── services/                   # Backend microservices
│   ├── user-management/        # Authentication & user profiles (Port 8000)
│   ├── course-generator/       # AI content generation (Port 8001)
│   ├── content-storage/        # File storage & versioning (Port 8003)
│   ├── course-management/      # Course CRUD operations (Port 8004)
│   └── content-management/     # Upload/download & export (Port 8005)
├── config/                     # Hydra configuration files
├── data/migrations/           # Database migrations
├── tests/                     # Comprehensive test suite
└── docs/                      # Documentation
```

### Service Dependencies
Services start in dependency order with health checks:
User Management → Course Generator → Course Management → Content Storage → Content Management

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
- **Docker** - Containerization
- **Nginx** - Reverse proxy
- **Prometheus/Grafana** - Monitoring
- **GitHub Actions** - CI/CD with comprehensive pipeline

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Redis 6+
- Node.js 16+ (for frontend testing)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd course-creator
   ```

2. **Set up environment**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   # Copy and edit environment configuration
   cp .cc_env.example .cc_env
   # Edit .cc_env with your database credentials and API keys
   ```

4. **Set up the database**
   ```bash
   # Setup database and run migrations
   python setup-database.py
   
   # Create admin user
   python create-admin.py
   ```

5. **Start all services**
   ```bash
   # Start entire platform with dependency management
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
   - Instructor Dashboard: http://localhost:8080/instructor-dashboard.html
   - Student Dashboard: http://localhost:8080/student-dashboard.html
   - API Documentation: http://localhost:8001/docs

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

### Managing Lab Environments

1. **Create Interactive Labs**
   - Generate exercises from course content
   - Configure terminal environments
   - Set up AI assistance for students

2. **Monitor Student Progress**
   - Track lab session activity
   - View student code and progress
   - Provide real-time assistance

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

# Run tests with coverage (80% minimum required)
python -m pytest --cov=services --cov-report=html

# Frontend tests
npm test                          # Jest unit tests
npm run test:e2e                 # Playwright E2E tests
npm run test:all                 # All frontend tests
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
# Using app-control.sh
./app-control.sh start

# Check all services are healthy
./app-control.sh status

# Monitor logs
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
- HTTPS enforcement
- Security headers
- Input validation and sanitization
- SQL injection prevention

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
- Core microservices architecture
- AI-powered content generation
- Interactive lab environments
- Comprehensive quiz system
- File upload/download with multi-format export
- User management with RBAC
- Database persistence with PostgreSQL
- Comprehensive test suite with TDD
- CI/CD pipeline with GitHub Actions
- MCP integration for Claude Desktop

**🔄 In Progress:**
- Enhanced analytics dashboard
- Mobile responsiveness improvements
- Advanced AI features

**📋 Planned:**
- Real-time collaboration features
- Video content support
- Payment integration
- Mobile application

---

**Project Status**: Active Development  
**Version**: 1.0.0  
**Last Updated**: 2025-07-16

For detailed development information, see [CLAUDE.md](CLAUDE.md) for comprehensive setup and development instructions.