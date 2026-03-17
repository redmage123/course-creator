# Architecture Overview

## Microservices Structure
The platform uses a microservices architecture with 8 core backend services:

1. **User Management Service** (Port 8000) - Authentication, user profiles, basic RBAC, **password management system**
2. **Course Generator Service** (Port 8001) - AI-powered content generation using Anthropic/OpenAI
3. **Content Storage Service** (Port 8003) - File storage, content versioning
4. **Course Management Service** (Port 8004) - CRUD operations for courses, enrollment, **bi-directional feedback system**
5. **Content Management Service** (Port 8005) - File upload/download, multi-format export
6. **Lab Container Manager Service** (Port 8006) - Individual student Docker container management with multi-IDE support
7. **Analytics Service** (Port 8007) - Student analytics, progress tracking, learning insights, PDF report generation
8. **Organization Management Service** (Port 8008) - **Enhanced RBAC system with multi-tenant organization management, granular permissions, track-based learning paths, MS Teams/Zoom integration, and automatic admin account creation with password management**

## Service Dependencies
Services must be started in dependency order:
- User Management → Organization Management → Course Generator → Course Management → Content Storage → Content Management → Analytics → Lab Container Manager

The `app-control.sh` script and Docker Compose handle this automatically with health checks.

## Frontend Architecture
Static HTML/CSS/JavaScript frontend with multiple dashboards:
- `admin.html` - Admin interface
- `instructor-dashboard.html` - Course creation and management  
- `student-dashboard.html` - Course consumption
- `lab.html` - Interactive coding environment with xterm.js
- `lab-multi-ide.html` - Multi-IDE lab environment with VSCode, Jupyter, IntelliJ, Terminal
- `org-admin-enhanced.html` - **Enhanced RBAC organization administration dashboard**
- `site-admin-dashboard.html` - **Site administrator dashboard with user management and platform analytics**
- `organization-registration.html` - **Professional organization registration with enhanced UI, password management, and keyboard navigation**
- `password-change.html` - **Self-service password management interface for all user roles**

## Data Layer
- **PostgreSQL** - Primary database for all services
- **Redis** - Session management and caching
- **File Storage** - Local filesystem (services/content-management/storage/)
- **ChromaDB** - Vector database for RAG-enhanced AI system

## Service Configuration

### Hydra Configuration System
Each service uses Hydra configuration with YAML files in `config/`:
- `config/config.yaml` - Main configuration
- `config/services/` - Service-specific configs
- `config/database/postgres.yaml` - Database settings
- `config/ai/claude.yaml` - AI service configuration
- `config/memory/claude_memory.yaml` - Memory system configuration

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
        CONTENT_SERVICE: 'http://localhost:8003',
        LAB_MANAGER: 'http://localhost:8006',
        ANALYTICS: 'http://localhost:8007',
        ORGANIZATION: 'http://localhost:8008'
    }
};
```

## Docker Deployment Architecture

### Full Containerization
The platform is fully containerized with Docker Compose:

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
- **Shared Base Image**: `course-creator-base:latest` eliminating system package duplication
- **Virtual Environment Mounting**: Host `.venv` mounted with `--copies` flag for Python 3.11 compatibility
- **Shared Database** - Single PostgreSQL instance for all services
- **Lab Manager** - Docker-in-Docker (DinD) for student lab containers
- **Persistent Volumes** - Student lab data preserved across restarts
- **Network Isolation** - Secure communication between services
- **Resource Limits** - CPU/memory constraints for student containers

### Key Docker Files
- `docker-compose.yml` - Main production orchestration
- `docker-compose.dev.yml` - Development with hot reload
- `docker-compose.test.yml` - Testing environment
- `services/lab-manager/Dockerfile` - Lab manager service container
- `Dockerfile.base` - Shared base image for all services
- Individual service Dockerfiles in each service directory

## Lab Container System Architecture (v2.1 - Multi-IDE Edition)

### Key Implementation Details
- Lab containers require Docker daemon access (`/var/run/docker.sock` mount)
- Dynamic image building uses temporary directories for Dockerfile generation with multi-IDE support
- Student lab persistence achieved through Docker volume mounts (preserved across IDE switches)
- Enhanced resource limits for multi-IDE support (CPU: 1.5 cores, Memory: 2GB for multi-IDE, 1GB for single IDE)
- Multi-IDE port allocation with dynamic port management (8080-8083 range)
- Network isolation prevents student containers from accessing other services
- Automatic cleanup prevents resource leaks from abandoned containers
- Health checks ensure container and IDE service availability before student access
- IDE service management with real-time status monitoring and switching capabilities

### Supported IDEs
1. **Terminal** (Port 8080) - xterm.js based terminal access
2. **VSCode Server** (Port 8081) - Full web-based Visual Studio Code
3. **JupyterLab** (Port 8082) - Interactive notebook environment
4. **IntelliJ IDEA** (Port 8083) - Professional IDE via JetBrains Projector (optional)

### Testing Architecture
- **Unit and integration tests** use comprehensive mocking for Docker operations
- **Frontend tests** simulate browser behavior without requiring Docker
- **E2E tests** use browser simulation with mocked API responses
- **Full Docker-based testing** requires actual Docker daemon access

### Production Deployment Considerations
- Docker-in-Docker requires privileged container or socket mounting
- Persistent storage needs adequate disk space for student work
- Load balancing may require session affinity for lab container access
- Multi-IDE support requires increased resource allocation

## Security Architecture

### Authentication & Authorization
- **JWT-based authentication** across all services
- **Enhanced RBAC system** with multi-tenant organization management
- **Session management** with Redis-based storage
- **Role-based access control** with granular permissions

### Data Security
- **Organization data isolation** - Complete separation between organizations
- **Encrypted communication** between services
- **Secure file storage** with access controls
- **Audit logging** for administrative actions

### Container Security
- **Network isolation** for student lab containers
- **Resource constraints** to prevent resource exhaustion
- **Sandboxed execution** environment for student code
- **Automatic cleanup** of temporary resources

## Monitoring and Observability

### Health Monitoring
- **Comprehensive health checks** for all services
- **Real-time status monitoring** with app-control.sh
- **Dependency chain visualization** showing service relationships
- **Service URL display** for quick access

### Logging System
- **Centralized logging** with structured format
- **Performance monitoring** with request timing
- **Error aggregation** and analysis
- **Debug capabilities** with detailed log information

### Analytics
- **Student progress tracking** with detailed metrics
- **Usage analytics** for platform optimization
- **Performance metrics** for system monitoring
- **Resource utilization** tracking