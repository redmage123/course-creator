# Development Commands

## Platform Management

### Docker Deployment (Recommended for Production)
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
# - All microservices (ports 8000-8010)
# - Demo service (port 8010)
# - Frontend (port 3000)
# - Lab container manager (port 8006)
# - Centralized syslog format logging to /var/log/course-creator/

# App Control Script Path Fix (v2.9)
# The app-control.sh script now correctly looks for docker-compose.yml
# in the project root directory (/home/bbrelin/course-creator/)
# instead of the parent directory (/home/bbrelin/)
```

### Native Deployment (Development)
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
cd services/lab-manager && python run.py          # Port 8006
cd services/organization-management && python main.py # Port 8008
cd services/demo-service && python main.py           # Port 8010

# Or start individual services using app-control.sh
./app-control.sh start user-management
./app-control.sh start course-generator
./app-control.sh start course-management
./app-control.sh start content-storage
./app-control.sh start content-management
./app-control.sh start analytics
./app-control.sh start lab-manager
./app-control.sh start organization-management

# Serve frontend
cd frontend && python -m http.server 8080
# Or: npm start (serves on port 8080)
```

## Testing

### Comprehensive Test Runners
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
python tests/runners/run_rbac_tests.py           # Enhanced RBAC system tests (102/102 tests - 100% success rate)
python tests/runners/run_enhanced_content_tests.py # Content management tests
python tests/runners/run_track_tests.py          # Learning track system tests
```

### Direct Testing Commands
```bash
# Direct pytest usage
python -m pytest                                 # Run all tests
python -m pytest tests/unit/                     # Unit tests only
python -m pytest tests/integration/              # Integration tests only
python -m pytest tests/e2e/                      # End-to-end tests only
python -m pytest tests/frontend/                 # Frontend tests only

# Run tests with coverage
python -m pytest --cov=services --cov-report=html

# Run specific test files
python -m pytest tests/integration/test_feedback_final.py    # Feedback system tests
python -m pytest tests/integration/test_rbac_api_integration.py # RBAC API tests
python -m pytest tests/e2e/test_track_system_e2e.py         # Track system E2E tests
```

### Frontend Testing
```bash
# Frontend tests
npm test                          # Jest unit tests
npm run test:e2e                 # Playwright E2E tests
npm run test:all                 # All frontend tests

# Browser-based testing
python -m pytest tests/frontend/test_quiz_functionality_selenium.py # Selenium tests
python -m pytest tests/frontend/test_lab_integration_frontend.py    # Lab integration tests
```

### Docker-Based Testing
```bash
# Docker-based testing (for production validation)
docker-compose -f docker-compose.test.yml up --build

# Testing with specific configurations
python tests/setup_test_environment.py           # Setup test environment
python tests/setup_test_environment.py --cleanup # Cleanup after testing
```

## Database Operations

### Database Setup and Migrations
```bash
# Setup database and run migrations
python deploy/setup-database.py

# Reset database (caution: destructive)  
python deploy/setup-database.py --reset

# Run specific migrations
python deploy/setup-database.py --migrate-only

# Check database status
python deploy/setup-database.py --status
```

### User Management
```bash
# Create admin user
python create-admin.py

# Create test users
python scripts/create-test-users.py

# Setup development data
python scripts/setup-dev-data.py
```

### Database Maintenance
```bash
# Database backup
docker exec course-creator-postgres pg_dump -U course_creator course_creator > backup.sql

# Database restore
docker exec -i course-creator-postgres psql -U course_creator course_creator < backup.sql

# Database cleanup and optimization
python scripts/database-maintenance.py
```

## Code Quality and Validation

### JavaScript Code Quality
```bash
# Lint JavaScript
npm run lint
npm run lint:fix

# JavaScript testing
npm run test:unit
npm run test:integration
```

### Python Code Quality
```bash
# Python formatting and linting (use standard tools)
black services/                  # Code formatting
isort services/                  # Import sorting
flake8 services/                 # Linting
mypy services/                   # Type checking

# Python testing with quality checks
python -m pytest --flake8 --mypy
```

### CSS and HTML Validation
```bash
# CSS validation
npm run stylelint

# HTML validation (if configured)
npm run html-validate
```

## Service Management

### Individual Service Operations
```bash
# Service health checks
curl http://localhost:8000/health  # User Management
curl http://localhost:8001/health  # Course Generator
curl http://localhost:8003/health  # Content Storage
curl http://localhost:8004/health  # Course Management
curl http://localhost:8005/health  # Content Management
curl http://localhost:8006/health  # Lab Manager
curl http://localhost:8007/health  # Analytics
curl http://localhost:8008/health  # Organization Management

# Service-specific commands
./app-control.sh restart user-management
./app-control.sh logs course-generator
./app-control.sh status analytics
```

### Health Monitoring
```bash
# Comprehensive health check
./app-control.sh health-check

# Service dependency validation
./app-control.sh validate-dependencies

# Performance monitoring
./app-control.sh monitor
```

## Development Environment

### Environment Setup
```bash
# Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Frontend dependencies
npm install
```

### Configuration Management
```bash
# Copy environment configuration
cp .env.example .env

# Edit configuration
nano .env  # or your preferred editor

# Validate configuration
./app-control.sh config-check
```

### Log Management
```bash
# View application logs
./app-control.sh logs [service_name]

# View all logs
./app-control.sh logs

# Real-time log monitoring
./app-control.sh logs --follow

# Log analysis
./app-control.sh analyze-logs
```

## Performance and Monitoring

### Performance Testing
```bash
# Load testing
python tests/performance/load_test.py

# Memory profiling
python tests/performance/memory_profile.py

# API performance testing
python tests/performance/api_benchmark.py
```

### System Monitoring
```bash
# Resource monitoring
./app-control.sh monitor-resources

# Database performance
./app-control.sh monitor-db

# Service performance metrics
./app-control.sh metrics
```

## Deployment Commands

### Production Deployment
```bash
# Production deployment
./deploy-ubuntu.sh

# Production health check
./app-control.sh production-health-check

# Production monitoring
./app-control.sh production-monitor
```

### CI/CD Integration
```bash
# Jenkins pipeline trigger
./scripts/trigger-jenkins-build.sh

# SonarQube analysis
./scripts/run-sonarqube-analysis.sh

# Automated testing pipeline
./scripts/run-ci-tests.sh
```