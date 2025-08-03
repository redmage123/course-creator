# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Version**: 2.6.0 - Docker Optimization, Virtual Environment Fix, and Service Architecture Consolidation  
**Last Updated**: 2025-08-03

## Version 2.6.0 - Major Docker and Architecture Improvements

### Docker Container Optimization
- **Shared Base Image**: Created `course-creator-base:latest` eliminating system package duplication across all services
- **Virtual Environment Mounting**: Fixed container startup by mounting host `.venv` with `--copies` flag for Python 3.11 compatibility
- **Zero Pip Downloads**: Services now start instantly without downloading packages during container initialization
- **Requirements Consolidation**: Created `requirements-base.txt` with common dependencies, eliminated 90% duplication

### Service Architecture Consolidation  
- **Lab Manager Relocation**: Moved `lab-containers/` to `services/lab-manager/` for architectural consistency
- **Unified Service Structure**: All services now follow identical patterns (main.py, run.py, Dockerfile, requirements.txt)
- **Configuration Standardization**: Updated mypy.ini, CLAUDE.md, and all references to use consistent service paths
- **Docker Compose Updates**: Updated build contexts and volume mounts for new service locations

### Virtual Environment Compatibility Fix
- **Python 3.11 Alignment**: Recreated virtual environment using system Python 3.11 to match Docker containers
- **Copy-based Installation**: Used `python3.11 -m venv .venv --copies` to avoid symlink issues in containers
- **Dependency Resolution**: Installed all service-specific requirements (chromadb, sentence-transformers, etc.)
- **Container Testing**: Verified imports work correctly within mounted virtual environment

### Health Monitoring Enhancements
- **Comprehensive Status Display**: Enhanced app-control.sh status to show all 13 configured services
- **Real-time Health Checks**: Added wait_for_service_health() function with 5-minute timeout and progress indicators
- **Dependency Chain Visualization**: Status shows which services are waiting for dependencies vs. actually failing
- **Service URL Display**: Provides quick access links once all services are healthy

## CRITICAL: Python Import Requirements

**ABSOLUTE IMPORTS ONLY**: Claude Code must NEVER write relative import statements in this application. All Python imports must be absolute imports only.

**FORBIDDEN**:
```python
from ..module import something          # NEVER
from .module import something           # NEVER
from ...parent.module import something  # NEVER
```

**REQUIRED**:
```python
from module import something            # ALWAYS
from package.module import something    # ALWAYS
from services.package.module import something  # ALWAYS
```

This directive overrides all other coding conventions and must be followed without exception to prevent Docker container import failures.

## File Editing Efficiency

**CRITICAL**: When making multiple related edits to files, batch them up and complete them all at once instead of asking permission for each individual edit. This improves efficiency and reduces interruptions during systematic updates like:
- Adding logging configuration to multiple services
- Updating environment variables across services  
- Adding volume mounts to Docker Compose services
- Applying consistent changes across multiple files

Use MultiEdit or multiple single Edit calls in one response to complete all related changes efficiently.

## Claude Code Memory System (v2.5 - MANDATORY USAGE)

**CRITICAL**: Claude Code now has access to a comprehensive persistent memory system that MUST be used to maintain context, store important information, and provide continuity across conversations.

### Memory System Overview

The memory system provides Claude Code with:
- **Persistent storage** of facts, entities, and relationships across sessions
- **Context continuity** - remember previous conversations and decisions
- **Knowledge accumulation** - build understanding of the codebase over time
- **Entity tracking** - maintain information about users, systems, files, and concepts
- **Relationship mapping** - understand connections between different components
- **Search capabilities** - quickly recall relevant information from past interactions

### Mandatory Memory Usage Requirements

**WHEN TO USE MEMORY (Required)**:

1. **Every significant interaction** - Store key facts from each conversation
2. **User preferences** - Remember user choices, preferences, and requirements
3. **System discoveries** - Store information learned about the codebase
4. **Problem solutions** - Remember fixes, workarounds, and troubleshooting steps
5. **Entity relationships** - Track connections between users, systems, files, projects
6. **Context preservation** - Maintain conversation context across sessions

### Memory System Location and Files

**Configuration**: `config/memory/claude_memory.yaml` - Hydra-based configuration with environment-aware settings  
**Manager Class**: `claude_memory_manager.py` - Core memory management with Hydra integration  
**Helper Functions**: `claude_memory_helpers.py` - Simplified interface for Claude Code  
**Schema**: `claude_memory_schema.sql` - SQLite database schema  
**Tests**: `memory_tests/test_memory_system.py` - Comprehensive test suite  
**Database Location**: Configurable via Hydra (default: `./claude_memory.db`)

### Memory System Usage Patterns

#### Simple Memory Operations (Use These Frequently)

```python
# Import helper functions (Hydra configuration automatic)
import claude_memory_helpers as memory

# Remember key information
memory.remember("User prefers dark mode interface", category="user_preferences", importance="medium")
memory.remember("Docker containers use ports 8000-8008", category="infrastructure", importance="high")

# Recall information
results = memory.recall("docker ports")
print(results)

# Remember user-specific information
memory.remember_user_preference("ui_theme", "dark")
memory.remember_system_info("Course Creator Platform", "Uses microservices architecture with 8 services")

# Remember troubleshooting solutions
memory.remember_error_solution("Container startup failure", "Remove old containers and rebuild with --no-cache")
```

#### Hydra-Based Memory Initialization (For Services)

```python
# Explicit Hydra initialization for services that need configuration control
import claude_memory_helpers as memory

# Initialize with specific Hydra configuration
memory_manager = memory.init_memory_with_hydra(config_path="config", config_name="config")

# Use memory with custom configuration
memory.remember("Service-specific information", category="service_config", importance="high")

# Access configuration details
config = memory_manager.config
db_path = config.memory.database.db_path
performance_settings = config.memory.performance
```

#### Entity and Relationship Management

```python
# Track entities (people, systems, concepts, files)
memory.note_entity("Course Creator Platform", "system", "Educational platform with microservices")
memory.note_entity("PostgreSQL Database", "system", "Primary database for all services")
memory.note_entity("User", "person", "Platform user working on course creation")

# Create relationships
memory.connect_entities("Course Creator Platform", "PostgreSQL Database", "uses", "Platform stores data in PostgreSQL")
memory.connect_entities("User", "Course Creator Platform", "uses", "User develops and maintains the platform")
```

#### Context and Conversation Management

```python
# Start memory context for significant work sessions
memory.start_memory_context("Database Migration Project", "Migrating database schema for v2.5")

# Get current context
context_info = memory.get_memory_context()
print(context_info)

# View memory statistics
summary = memory.memory_summary()
print(summary)
```

### Integration with Claude Code Workflows

#### Before Starting Work
**ALWAYS** check memory for relevant context:
```python
# Check for related information
results = memory.recall("database migration")
user_prefs = memory.get_user_preferences()
system_info = memory.get_system_info()
```

#### During Work
**CONTINUOUSLY** store important findings:
```python
# Store discoveries
memory.remember("Migration script requires manual intervention for user table", 
                category="database", importance="critical")

# Track file relationships
memory.remember_file_info("/path/to/migration.sql", "Contains user table schema updates")
```

#### After Completing Tasks
**ALWAYS** summarize and store results:
```python
# Store solutions and outcomes
memory.remember("Database migration completed successfully using manual intervention", 
                category="project_completion", importance="high")

# Update entity information
memory.note_entity("Database Schema", "concept", "Updated to v2.5 with enhanced user management")
```

### Memory System Help and Discovery

```python
# Get help on available functions
help_info = memory.memory_help()
print(help_info)

# View recent activity
recent = memory.recent_activity(days=7)
print(recent)

# Search by categories
db_facts = memory.search_facts_by_category("database")
system_entities = memory.search_by_type("system")
```

### Performance and Maintenance

The memory system is optimized for Claude Code usage:
- **Fast retrieval** - Indexed SQLite database with sub-second queries
- **Automatic cleanup** - Old data automatically archived
- **Backup support** - Regular backups ensure data preservation
- **Scalable design** - Handles thousands of facts and entities efficiently

### Memory System Benefits for Development

1. **Continuity** - Remember context across sessions and conversations
2. **Learning** - Build accumulated knowledge about the codebase
3. **Efficiency** - Avoid re-discovering the same information repeatedly
4. **Relationship Awareness** - Understand connections between system components
5. **Problem Prevention** - Remember past issues and their solutions
6. **User Personalization** - Adapt to user preferences and working patterns

### Memory Usage Examples in Development Context

#### Example 1: Remembering User Preferences
```python
# During initial interaction
memory.remember_user_preference("testing_framework", "pytest")
memory.remember_user_preference("code_style", "black_formatting")

# Later in same or different session
user_prefs = memory.get_user_preferences()
# Use stored preferences to adapt behavior
```

#### Example 2: System Architecture Knowledge
```python
# Store architecture information
memory.note_entity("User Management Service", "system", "Handles authentication on port 8000")
memory.note_entity("Course Generator Service", "system", "AI content generation on port 8001")
memory.connect_entities("User Management Service", "Course Generator Service", "authenticates_for", 
                       "User service provides auth for course generation")

# Later recall architecture
architecture_info = memory.search_by_type("system")
```

#### Example 3: Troubleshooting Knowledge Base
```python
# Store troubleshooting solutions
memory.remember_error_solution("ModuleNotFoundError in Docker", 
                               "Use absolute imports instead of relative imports")
memory.remember_error_solution("Service startup timeout", 
                               "Check health endpoints and dependency order")

# Recall when similar issues arise
troubleshooting = memory.get_troubleshooting_info()
```

### Memory System Configuration (Hydra-Based)

The memory system now uses Hydra configuration for flexible, environment-aware setup:

#### Configuration File Structure
```yaml
# config/memory/claude_memory.yaml
memory:
  database:
    db_path: ${oc.env:CLAUDE_MEMORY_DB_PATH,./claude_memory.db}
    schema_path: ${oc.env:CLAUDE_MEMORY_SCHEMA_PATH,./claude_memory_schema.sql}
    connection_params:
      journal_mode: "WAL"
      cache_size: 2000
      foreign_keys: true
  
  session:
    cleanup_after_hours: 24
    max_sessions: 100
    track_context: true
  
  performance:
    enable_caching: true
    cache_timeout_minutes: 30
    auto_optimize_days: 7
```

#### Environment Variable Overrides
```bash
# Override database location
export CLAUDE_MEMORY_DB_PATH="/custom/path/memory.db"
export CLAUDE_MEMORY_SCHEMA_PATH="/custom/path/schema.sql"

# Performance tuning
export MEMORY_CACHE_TIMEOUT=60
export MEMORY_MAX_SEARCH_RESULTS=100
```

#### Configuration Benefits
- **Environment-Aware**: Different settings for development, staging, production
- **No Hardcoded Paths**: All paths configurable via environment variables
- **Performance Tuning**: Adjustable caching, optimization, and resource limits
- **Security Options**: Encryption, audit logging, access controls
- **Development Features**: Test mode, debug logging, sample data population

**COMPLIANCE REQUIREMENT**: Claude Code must demonstrate usage of the memory system in every significant interaction. This is not optional - it's a core requirement for effective assistance.

## Comprehensive Code Documentation Standards (v2.4)

**CRITICAL**: All code in this repository must be extensively documented with multiline strings and comprehensive comments explaining both what the code does and why it does it. This documentation standard has been implemented across multiple services and must be maintained for all future development.

### Documentation Requirements

#### Multiline String Documentation
**PREFERRED**: Use multiline strings (triple quotes) for comprehensive explanations rather than # comments wherever appropriate:

**CRITICAL RESTRICTION**: Python multiline string syntax (`"""` or `'''`) must ONLY be used in Python files. Never use Python multiline syntax in non-Python files such as:
- YAML files (use `#` comments)
- JSON files (comments not supported)
- SQL files (use `--` or `/* */` comments)
- JavaScript files (use `//` or `/* */` comments)
- CSS files (use `/* */` comments)
- HTML files (use `<!-- -->` comments)
- Bash scripts (use `#` comments)
- Docker files (use `#` comments)

```python
"""
COMPREHENSIVE SESSION VALIDATION ON PAGE LOAD

BUSINESS REQUIREMENT:
When a user refreshes the dashboard page after session expiry,
they should be redirected to the home page, not stay on the dashboard
with default username display.

TECHNICAL IMPLEMENTATION:
1. Check if user data exists in localStorage
2. Validate session timestamps against timeout thresholds  
3. Check if authentication token is present and valid
4. Verify user has correct role for dashboard access
5. Redirect to home page if any validation fails
6. Prevent dashboard initialization for expired sessions

WHY THIS PREVENTS THE BUG:
- Previous code only checked if currentUser existed, not if session was valid
- Expired sessions could still have currentUser data in localStorage
- This led to dashboard loading with fallback usernames
- Now we validate the complete session state before allowing access
"""
```

#### JavaScript Documentation Standards
```javascript
"""
Session Management Configuration and Business Requirements

SECURITY TIMEOUT CONFIGURATION:
- SESSION_TIMEOUT: 8 hours (28,800,000 ms) - Maximum session duration
- INACTIVITY_TIMEOUT: 2 hours (7,200,000 ms) - Inactivity threshold
- AUTO_LOGOUT_WARNING: 5 minutes (300,000 ms) - Warning before expiry

WHY THESE SPECIFIC TIMEOUTS:

8-Hour Absolute Session Timeout:
- Aligns with standard work day expectations
- Balances security with user convenience
- Prevents indefinite session persistence
- Meets educational platform security requirements
- Reduces risk of session hijacking over time
"""
this.SESSION_TIMEOUT = 8 * 60 * 60 * 1000;
```

#### CSS Documentation Standards
```css
"""
SIDEBAR SCROLLBAR AND LAYOUT FIX

PROBLEMS ADDRESSED:
1. Missing scrollbar when content exceeds viewport height
2. Sidebar overlapping header when zoomed in
3. Inconsistent z-index causing layout conflicts

SOLUTION:
- Force scrollbar visibility with scrollbar-gutter: stable
- Ensure proper z-index hierarchy (sidebar below header)
- Add webkit scrollbar styling for better UX
- Prevent sidebar from covering top navigation at high zoom levels
"""

.dashboard-sidebar {
    scrollbar-gutter: stable;
    /* Additional CSS properties... */
}
```

### Services with Comprehensive Documentation Implemented

#### ✅ Frontend Components (Fully Documented)
- **`frontend/js/modules/auth.js`** - Complete session management system with business rationale
- **`frontend/js/modules/app.js`** - Application initialization and error handling
- **`frontend/js/student-dashboard.js`** - Student dashboard session validation
- **`frontend/js/admin.js`** - Admin dashboard authentication
- **`frontend/js/org-admin-enhanced.js`** - Organization admin session management
- **`frontend/js/site-admin-dashboard.js`** - Site admin session validation
- **`frontend/css/layout/dashboard.css`** - Dashboard layout fixes with technical explanations
- **`frontend/html/instructor-dashboard.html`** - Instructor dashboard session validation

#### ✅ Infrastructure Components (Fully Documented)
- **`app-control.sh`** - Docker container name resolution fixes with comprehensive problem analysis

### Documentation Content Requirements

Each documented code section must include:

1. **Business Context** - Why this code exists and what business problem it solves
2. **Technical Implementation** - How the code works and its approach
3. **Problem Analysis** - What specific issues the code addresses
4. **Solution Rationale** - Why this particular solution was chosen
5. **Edge Cases** - Special conditions and how they're handled
6. **Security Considerations** - Any security implications or protections
7. **Performance Impact** - How the code affects system performance
8. **Maintenance Notes** - Important information for future developers

### Example Documentation Structure

```python
"""
[COMPONENT NAME] - [Brief Description]

BUSINESS REQUIREMENT:
[Detailed explanation of the business need this code fulfills]

TECHNICAL IMPLEMENTATION:
[Step-by-step breakdown of the technical approach]
1. [First major step]
2. [Second major step]
3. [Third major step]

PROBLEM ANALYSIS:
[Detailed analysis of what problems existed before this implementation]
- [Specific problem 1]
- [Specific problem 2]
- [Root cause analysis]

SOLUTION RATIONALE:
[Explanation of why this specific approach was chosen]
- [Advantage 1]
- [Advantage 2]
- [Trade-offs considered]

SECURITY CONSIDERATIONS:
[Any security implications, protections, or vulnerabilities addressed]

PERFORMANCE IMPACT:
[How this code affects system performance, scalability, or resource usage]

MAINTENANCE NOTES:
[Important information for future developers]
"""
```

### Services Requiring Documentation Implementation

The following services still need comprehensive multiline documentation applied:

- **`services/analytics/`** - Analytics service Python files
- **`services/organization-management/`** - RBAC system Python files  
- **`services/lab-manager/`** - Lab management Python files
- **Remaining frontend JavaScript files** - Additional JS modules
- **Remaining CSS files** - Component and layout stylesheets
- **HTML templates** - Frontend dashboard and component templates
- **Utility and configuration files** - Setup scripts and configuration modules

### Documentation Maintenance

- **All new code** must follow these documentation standards
- **Existing code modifications** must include updated documentation
- **Code reviews** must verify documentation completeness and quality
- **Documentation consistency** must be maintained across similar components

This documentation standard ensures that all developers can understand not just what the code does, but why it was implemented in a specific way, what problems it solves, and how to maintain it effectively.

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
# - Centralized syslog format logging to /var/log/course-creator/
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
cd services/lab-manager && python run.py        # Port 8006 (Lab Manager)

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
python tests/runners/run_rbac_tests.py           # Enhanced RBAC system tests (102/102 tests - 100% success rate)

# Direct pytest usage
python -m pytest                                 # Run all tests
python -m pytest tests/unit/                     # Unit tests only
python -m pytest tests/integration/              # Integration tests only
python -m pytest tests/e2e/                      # End-to-end tests only
python -m pytest tests/frontend/                 # Frontend tests only

# Run tests with coverage
python -m pytest --cov=services --cov-report=html

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
The platform uses a microservices architecture with 8 core backend services:

1. **User Management Service** (Port 8000) - Authentication, user profiles, basic RBAC
2. **Course Generator Service** (Port 8001) - AI-powered content generation using Anthropic/OpenAI
3. **Content Storage Service** (Port 8003) - File storage, content versioning
4. **Course Management Service** (Port 8004) - CRUD operations for courses, enrollment, **bi-directional feedback system**
5. **Content Management Service** (Port 8005) - File upload/download, multi-format export
6. **Lab Container Manager Service** (Port 8006) - Individual student Docker container management with multi-IDE support
7. **Analytics Service** (Port 8007) - Student analytics, progress tracking, learning insights, PDF report generation
8. **Organization Management Service** (Port 8008) - **Enhanced RBAC system with multi-tenant organization management, granular permissions, track-based learning paths, and MS Teams/Zoom integration**

### Service Dependencies
Services must be started in dependency order:
- User Management → Organization Management → Course Generator → Course Management → Content Storage → Content Management → Analytics → Lab Container Manager

The `app-control.sh` script and Docker Compose handle this automatically with health checks.

### Frontend Architecture
Static HTML/CSS/JavaScript frontend with multiple dashboards:
- `admin.html` - Admin interface
- `instructor-dashboard.html` - Course creation and management  
- `student-dashboard.html` - Course consumption
- `lab.html` - Interactive coding environment with xterm.js
- `org-admin-enhanced.html` - **Enhanced RBAC organization administration dashboard**
- `site-admin-dashboard.html` - **Site administrator dashboard with user management and platform analytics**

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

## RAG-Enhanced AI System (v2.4 - Intelligent Learning Integration)

The platform now includes a comprehensive Retrieval-Augmented Generation (RAG) system that makes AI progressively smarter through continuous learning and knowledge accumulation:

### RAG Intelligence Architecture
- **ChromaDB Vector Database** - High-performance vector storage with 4 specialized collections
- **Multi-Domain Knowledge** - Separate knowledge bases for content generation, lab assistance, user interactions, and course knowledge
- **Progressive Learning** - AI gets smarter with each interaction through accumulated experience
- **Context-Aware Generation** - Enhanced AI prompts with relevant historical knowledge and successful patterns
- **Quality-Based Learning** - Prioritizes learning from high-quality interactions and user feedback

### RAG-Enhanced Content Generation
- **Intelligent Syllabus Generation** - Learns from successful syllabi to improve future generations
- **Context Retrieval** - Queries knowledge base for relevant educational patterns and best practices
- **Domain Expertise** - Subject-specific knowledge accumulation for different academic disciplines
- **Continuous Improvement** - Quality scores and user feedback drive learning and optimization
- **Enhanced Prompts** - AI prompts enriched with accumulated educational wisdom and successful patterns

### RAG-Enhanced Lab Assistant
- **Programming Intelligence** - Context-aware coding help that learns from successful debugging solutions
- **Multi-Language Support** - Comprehensive assistance across Python, JavaScript, and other programming languages
- **Personalized Learning** - Adapts to student skill levels and learning preferences over time
- **Error Pattern Recognition** - Learns effective debugging strategies and solution patterns
- **Code Analysis** - Intelligent code review with suggestions based on accumulated programming knowledge

### RAG Service Architecture
```http
# Core RAG Operations
GET  /api/v1/rag/health              # Service health and ChromaDB connectivity
GET  /api/v1/rag/collections         # List available knowledge collections
POST /api/v1/rag/add-document        # Add document to knowledge base
POST /api/v1/rag/query              # Query knowledge base for relevant context
POST /api/v1/rag/learn              # Learn from user interactions and feedback
GET  /api/v1/rag/stats              # Performance metrics and usage statistics

# Lab Assistant Integration
POST /assistant/help                 # RAG-enhanced programming assistance
GET  /assistant/stats               # Lab assistant performance metrics
```

### RAG Integration Points
- **Course Generator Service** - Enhanced content generation with accumulated educational knowledge
- **Lab Container Manager** - Intelligent programming assistance with learning capabilities
- **Analytics Service** - RAG-enhanced insights and recommendations
- **All AI Services** - Systematic integration with RAG context enhancement

### RAG Docker Configuration
```yaml
rag-service:
  image: course-creator-rag-service:latest
  ports: ["8009:8009"]
  volumes: 
    - rag_chromadb_data:/app/chromadb_data
  environment:
    - CHROMADB_PATH=/app/chromadb_data
    - OPENAI_API_KEY=${OPENAI_API_KEY:-}
    - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
```

### RAG Learning Mechanisms
- **Quality Scoring** - Automatic assessment of generation quality and learning prioritization
- **User Feedback Integration** - Learning from instructor and student feedback on content effectiveness
- **Pattern Recognition** - Identification of successful educational structures and approaches
- **Domain Specialization** - Building expertise in specific subjects and difficulty levels
- **Continuous Optimization** - Progressive improvement through accumulated experience

### RAG Performance Features
- **Circuit Breaker Pattern** - Reliable operation with graceful degradation when RAG unavailable
- **Local Embeddings** - SentenceTransformers for fast local vector generation with OpenAI fallback
- **Performance Monitoring** - Comprehensive metrics and logging for optimization
- **Scalable Architecture** - Optimized for high-volume educational content generation
- **Persistent Storage** - ChromaDB data preservation across container restarts

### RAG Testing Framework
- **Integration Tests** - Comprehensive validation of RAG system integration (`test_rag_system_integration.py`)
- **Learning Validation** - Tests for knowledge accumulation and retrieval effectiveness
- **Performance Testing** - Load testing and reliability validation under various conditions
- **Cross-Service Testing** - Validation of RAG integration across all platform services

### Key RAG System Files
- `services/rag-service/main.py` - Complete RAG service with ChromaDB integration
- `services/rag-service/logging_setup.py` - Comprehensive RAG-specific logging
- `services/course-generator/rag_integration.py` - Content generation RAG enhancement
- `services/lab-manager/rag_lab_assistant.py` - Intelligent programming assistance
- `services/course-generator/ai/generators/syllabus_generator.py` - RAG-enhanced syllabus generation
- `tests/integration/test_rag_system_integration.py` - Comprehensive RAG validation tests

## Enhanced RBAC System (v2.3)

The platform now includes a comprehensive Role-Based Access Control (RBAC) system with multi-tenant organization management, providing enterprise-grade security and granular permission control:

### Multi-Tenant Organization Architecture
- **Organization Isolation** - Complete data and resource isolation between organizations
- **Hierarchical Role Management** - Site Admin → Organization Admin → Instructor → Student hierarchy
- **Granular Permissions** - Fine-grained permission system with over 50 distinct permissions
- **Dynamic Role Assignment** - Real-time role changes with immediate permission updates
- **Cross-Organization Security** - Strict boundaries preventing unauthorized cross-tenant access

### Enhanced Role System
#### Site Administrator
- **Platform Management** - Complete control over all organizations and users
- **System Configuration** - Platform-wide settings, integrations, and feature toggles
- **Analytics & Reporting** - Global platform analytics and usage metrics
- **Organization Oversight** - Create, modify, and delete organizations
- **User Management** - Manage users across all organizations

#### Organization Administrator  
- **Organization Management** - Complete control within their organization boundary
- **Member Management** - Add, remove, and manage organization members
- **Track Creation** - Design and manage learning tracks and curricula
- **Meeting Room Management** - Create and configure MS Teams/Zoom meeting rooms
- **Analytics Access** - Organization-specific analytics and reporting
- **Project Assignment** - Assign instructors to projects and manage access

#### Instructor
- **Course Creation** - Create and manage courses within assigned projects
- **Student Management** - Manage students within their courses
- **Content Development** - Access to AI content generation tools
- **Assessment Tools** - Create and grade quizzes, assignments
- **Meeting Room Access** - Create instructor-specific meeting rooms
- **Analytics Viewing** - Access to student performance analytics

#### Student
- **Course Access** - Access to enrolled courses and learning materials
- **Assignment Submission** - Submit assignments and take quizzes
- **Lab Environment** - Access to personalized lab containers
- **Progress Tracking** - View personal learning progress and achievements
- **Meeting Participation** - Join organization and track meeting rooms

### Track-Based Learning System
- **Automatic Enrollment** - Students automatically enrolled in relevant tracks
- **Learning Path Optimization** - AI-recommended learning sequences
- **Progress Tracking** - Comprehensive progress monitoring across tracks
- **Prerequisite Management** - Automatic prerequisite validation and enforcement
- **Certification Tracking** - Track completion certificates and achievements
- **Adaptive Difficulty** - Dynamic difficulty adjustment based on performance

### Meeting Room Integration
#### MS Teams Integration
- **Automatic Room Creation** - Dynamic Teams meeting room generation
- **Organization Rooms** - Persistent meeting spaces for entire organizations
- **Track-Specific Rooms** - Dedicated rooms for learning tracks
- **Instructor Rooms** - Personal meeting spaces for instructors
- **Settings Management** - Recording, waiting room, and participation controls

#### Zoom Integration
- **Meeting Management** - Full Zoom meeting lifecycle management
- **Room Configuration** - Custom settings for different meeting types
- **Participant Controls** - Mute, recording, and screen sharing permissions
- **Security Settings** - Waiting rooms and password protection
- **Integration Analytics** - Meeting usage and participation tracking

### Database Schema & API Architecture
```sql
-- Core RBAC tables
organizations           -- Multi-tenant organization management
organization_memberships -- User-organization relationships with roles
tracks                  -- Learning track definitions and management
track_enrollments       -- Student track enrollment and progress
meeting_rooms          -- MS Teams/Zoom meeting room integration
permissions            -- Granular permission definitions
role_permissions       -- Role-to-permission mappings
user_permissions       -- Direct user permission assignments
```

### Enhanced RBAC API Endpoints
```http
# Organization Management
GET    /api/v1/rbac/organizations                    # List organizations
POST   /api/v1/rbac/organizations                    # Create organization
GET    /api/v1/rbac/organizations/{org_id}          # Get organization details
PUT    /api/v1/rbac/organizations/{org_id}          # Update organization
DELETE /api/v1/rbac/organizations/{org_id}          # Delete organization

# Member Management
GET    /api/v1/rbac/organizations/{org_id}/members   # List organization members
POST   /api/v1/rbac/organizations/{org_id}/members   # Add member to organization
PUT    /api/v1/rbac/organizations/{org_id}/members/{member_id} # Update member role
DELETE /api/v1/rbac/organizations/{org_id}/members/{member_id} # Remove member

# Track Management
GET    /api/v1/rbac/organizations/{org_id}/tracks    # List organization tracks
POST   /api/v1/rbac/organizations/{org_id}/tracks    # Create learning track
PUT    /api/v1/rbac/tracks/{track_id}               # Update track
DELETE /api/v1/rbac/tracks/{track_id}               # Delete track
POST   /api/v1/rbac/tracks/{track_id}/enroll        # Enroll student in track

# Meeting Room Management
GET    /api/v1/rbac/organizations/{org_id}/meeting-rooms # List meeting rooms
POST   /api/v1/rbac/organizations/{org_id}/meeting-rooms # Create meeting room
PUT    /api/v1/rbac/meeting-rooms/{room_id}             # Update meeting room
DELETE /api/v1/rbac/meeting-rooms/{room_id}             # Delete meeting room

# Site Administration
GET    /api/v1/site-admin/organizations              # Site admin organization overview
DELETE /api/v1/site-admin/organizations/{org_id}     # Site admin organization deletion
GET    /api/v1/site-admin/users                     # Platform-wide user management
GET    /api/v1/site-admin/analytics                 # Global platform analytics
```

### Frontend RBAC Implementation
- **Role-Based UI** - Dynamic interface adaptation based on user permissions
- **Organization Selector** - Multi-organization users can switch contexts
- **Permission Guards** - Client-side permission checking for UI elements
- **Real-time Updates** - Live permission updates without page refresh
- **Responsive Design** - Mobile-optimized RBAC interfaces
- **Dashboard Customization** - Role-specific dashboard layouts and content

### Security & Compliance Features
- **JWT Integration** - Secure token-based authentication with role claims
- **Permission Caching** - Optimized permission checking with Redis caching
- **Audit Logging** - Comprehensive audit trail for all RBAC operations
- **Data Encryption** - Encrypted sensitive data storage and transmission
- **Session Management** - Secure session handling with automatic expiration
- **Rate Limiting** - API rate limiting based on user roles and permissions

### Key RBAC System Files
- `services/organization-management/` - Complete RBAC service implementation
- `services/organization-management/api/` - FastAPI RBAC API endpoints
- `services/organization-management/application/services/` - Core business logic services
- `services/organization-management/domain/` - Domain models and interfaces
- `services/organization-management/infrastructure/` - Repository implementations
- `frontend/js/org-admin-enhanced.js` - Organization admin dashboard
- `frontend/js/site-admin-dashboard.js` - Site admin interface with user management
- `data/migrations/014_create_rbac_system.sql` - Complete RBAC database schema
- `tests/unit/rbac/` - Comprehensive unit test suite (59 tests)
- `tests/integration/test_rbac_api_integration.py` - API integration tests (11 tests)
- `tests/frontend/test_rbac_dashboard_frontend.py` - Frontend component tests (9 tests)
- `tests/e2e/test_rbac_complete_workflows.py` - End-to-end workflow tests (6 tests)
- `tests/security/test_rbac_security.py` - Security and authorization tests (17 tests)

### RBAC Testing Framework (100% Success Rate)
The Enhanced RBAC system includes comprehensive testing with **102 total tests** achieving **100% success rate**:

#### Unit Tests (59 tests)
- **Organization Service** - 14 tests covering CRUD operations, validation, statistics
- **Membership Service** - 16 tests covering member management, permissions, invitations
- **Track Service** - 14 tests covering learning track creation, enrollment, progress tracking
- **Meeting Room Service** - 15 tests covering Teams/Zoom integration, room management

#### Integration Tests (11 tests)  
- **API Integration** - Complete API endpoint testing with authentication and authorization
- **Service Communication** - Cross-service integration testing
- **Database Operations** - Data persistence and retrieval validation

#### Frontend Tests (9 tests)
- **Dashboard Components** - UI component testing with browser simulation
- **User Interactions** - Form validation, modal management, responsive design
- **Permission-Based UI** - Role-based interface adaptation testing

#### End-to-End Tests (6 tests)
- **Complete Workflows** - Full user journey testing from login to task completion
- **Cross-Browser Compatibility** - Multi-browser testing for RBAC interfaces
- **Network Failure Recovery** - Resilience testing for network interruptions

#### Security Tests (17 tests)
- **Authentication & Authorization** - JWT validation, role verification, privilege escalation prevention
- **Data Security** - Input validation, SQL injection prevention, XSS protection
- **Session Management** - Secure session handling and timeout validation

### RBAC Code Quality & Standards
- **ESLint Compliance** - JavaScript code quality validation
- **Flake8 Compliance** - Python code quality and PEP8 adherence  
- **StyleLint Compliance** - CSS code quality and consistency
- **100% Test Coverage** - Comprehensive test coverage across all RBAC components
- **SOLID Principles** - Clean architecture following SOLID design principles
- **TDD Implementation** - Test-driven development throughout RBAC system

### RBAC Performance & Scalability
- **Optimized Queries** - Database query optimization for large organizations
- **Caching Strategy** - Redis-based permission and role caching
- **Lazy Loading** - On-demand data loading for improved performance
- **Pagination Support** - Efficient pagination for large datasets
- **Background Processing** - Asynchronous processing for bulk operations

### Integration with Existing Systems
- **User Management Service** - Seamless integration with existing authentication
- **Course Management** - RBAC permissions applied to all course operations
- **Lab Containers** - Role-based access control for lab environments
- **Analytics Service** - Permission-based analytics data access
- **Content Management** - Secure content access based on organization membership

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
- `services/lab-manager/main.py` - FastAPI lab manager service with Docker and multi-IDE integration
- `services/lab-manager/Dockerfile` - Lab manager container configuration
- `services/lab-manager/lab-images/multi-ide-base/` - Multi-IDE Docker base images
- `services/lab-manager/lab-images/python-lab-multi-ide/` - Python lab with multi-IDE support
- `services/lab-manager/lab-images/multi-ide-base/ide-startup.py` - IDE management service
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
- `tests/unit/` - Component-level tests including lab container, feedback system, and RBAC unit tests
- `tests/integration/` - Service interaction tests with lab lifecycle, feedback integration, and RBAC API testing
- `tests/frontend/` - JavaScript module testing with browser simulation for all components including RBAC dashboards
- `tests/e2e/` - Full workflow tests including complete lab container, feedback system, and RBAC workflow lifecycles
- `tests/security/` - Authentication, authorization, and comprehensive RBAC security tests
- `tests/performance/` - Load testing
- `tests/quiz-management/` - Comprehensive quiz management system testing
- `tests/validation/` - System-wide validation and health checks
- `tests/email-integration/` - Email service and Hydra configuration testing
- `tests/file-operations/` - File management and student file system testing
- `tests/lab-systems/` - Lab container creation and management testing
- `tests/unit/rbac/` - **Enhanced RBAC system unit tests (59 tests covering all RBAC services)**
- `tests/fixtures/rbac_fixtures.py` - **Comprehensive RBAC test fixtures and utilities**

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

### Enhanced RBAC System Testing (v2.3 - 100% Success Rate)
The Enhanced RBAC system includes the most comprehensive test suite in the platform with **102 total tests** achieving **100% success rate**:

#### RBAC Unit Tests (59 tests - 100% pass rate)
- **Organization Service Tests** - `tests/unit/rbac/test_organization_service.py` (14 tests)
  - Organization CRUD operations, validation, duplicate handling
  - Organization statistics, membership counts, settings validation
  - Slug generation, data validation, filtering capabilities
- **Membership Service Tests** - `tests/unit/rbac/test_membership_service.py` (16 tests)
  - Member addition, removal, role updates, permission management
  - Bulk operations, invitation workflows, status management
  - Email validation, role validation, duplicate prevention
- **Track Service Tests** - `tests/unit/rbac/test_track_service.py` (14 tests)
  - Track creation, enrollment, progress tracking, completion certification
  - Auto-enrollment, prerequisite management, difficulty filtering
  - Learning path optimization, analytics integration
- **Meeting Room Service Tests** - `tests/unit/rbac/test_meeting_room_service.py` (15 tests)
  - Teams/Zoom integration, room creation, participant management
  - Platform switching, settings validation, invitation management
  - Analytics tracking, error handling, security validation

#### RBAC Integration Tests (11 tests - 100% pass rate)
- **API Integration Tests** - `tests/integration/test_rbac_api_integration.py`
  - Complete API endpoint testing with authentication and authorization
  - Organization creation flow, member management flow, meeting room management
  - Site admin capabilities, permission-based access control
  - Cross-service integration, audit logging, email notifications
  - Authentication requirements, data validation, error handling

#### RBAC Frontend Tests (9 tests - 100% pass rate)
- **Dashboard Frontend Tests** - `tests/frontend/test_rbac_dashboard_frontend.py`
  - Organization admin dashboard initialization and functionality
  - Member management UI operations, meeting room management UI
  - Modal management, form validation and submission
  - Site admin dashboard functionality, notification system
  - Tab navigation, responsive design behavior

#### RBAC End-to-End Tests (6 tests - 100% pass rate)
- **Complete Workflow Tests** - `tests/e2e/test_rbac_complete_workflows.py`
  - Complete organization admin workflow (login to task completion)
  - Complete site admin workflow with platform management
  - Instructor-student interaction workflow across organizations
  - Permission boundary testing and privilege escalation prevention
  - Cross-browser compatibility testing, network failure recovery

#### RBAC Security Tests (17 tests - 100% pass rate)
- **Security & Authorization Tests** - `tests/security/test_rbac_security.py`
  - JWT token validation (valid, invalid, expired, tampered tokens)
  - Role-based access control for all user types (site admin, org admin, instructor, student)
  - Organization boundary enforcement, privilege escalation prevention
  - Session management security, input validation, XSS/SQL injection prevention
  - Rate limiting protection, audit logging security, password requirements
  - Secure API communication, data encryption validation

#### RBAC Code Quality Tests (100% pass rate)
- **ESLint JavaScript Tests** - Frontend code quality validation
- **Flake8 Python Tests** - Backend code quality and PEP8 compliance
- **StyleLint CSS Tests** - Stylesheet quality and consistency
- **Comprehensive Coverage** - 100% test coverage across all RBAC components

#### RBAC Test Fixtures & Utilities
- **Comprehensive Fixtures** - `tests/fixtures/rbac_fixtures.py`
  - Mock organization, user, role, permission, and membership data
  - FastAPI test client with complete RBAC endpoint mocking
  - Test utilities for JWT token creation, authentication, response validation
  - Repository mocks for all RBAC services with realistic behavior
  - Integration service mocks for Teams/Zoom, audit logging, email services

#### RBAC Test Runner & Reporting
- **Specialized Test Runner** - `tests/runners/run_rbac_tests.py`
  - Comprehensive test execution with detailed reporting
  - Code quality validation integration
  - Performance metrics and execution time tracking
  - Component health validation and operational status
  - HTML and JSON test report generation

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

### Docker Service Startup Troubleshooting Guide

#### Common Root Causes and Systematic Solutions

**CRITICAL**: Follow Chain of Thoughts methodology for service startup issues. Do not apply incremental fixes.

##### 1. Python Import Resolution Issues

**Root Cause**: Relative imports fail in Docker containers due to module path resolution.

**Symptoms**:
- `ImportError: attempted relative import beyond top-level package`
- Services continuously restarting with import errors

**Systematic Solution**:
```bash
# 1. Identify all relative imports
grep -r "from \.\.\." services/[service-name]/

# 2. Convert ALL relative imports to absolute imports
# FROM: from ...domain.interfaces.user_repository import IUserRepository
# TO:   from domain.interfaces.user_repository import IUserRepository

# 3. Affected files typically include:
# - application/services/*.py
# - infrastructure/repositories/*.py
# - Any file using ../../.. import patterns
```

**Files Requiring Import Fixes**:
- `services/user-management/application/services/user_service.py`
- `services/user-management/application/services/authentication_service.py`
- `services/user-management/application/services/session_service.py`
- `services/user-management/infrastructure/repositories/postgresql_user_repository.py`
- `services/user-management/infrastructure/repositories/postgresql_session_repository.py`

##### 2. FastAPI Dependency Injection Issues

**Root Cause**: Missing dependency injection functions for FastAPI endpoints.

**Symptoms**:
- `NameError: name 'get_syllabus_service' is not defined`
- Import errors on service startup

**Systematic Solution**:
```python
# Add missing dependency functions to app/dependencies.py:
def get_syllabus_service() -> SyllabusService:
    """Get syllabus service for FastAPI dependency injection."""
    return get_container().get_syllabus_service()

def get_exercise_service() -> ExerciseGenerationService:
    """Get exercise service for FastAPI dependency injection."""
    return get_container().get_exercise_service()
```

**Required Imports in API Files**:
```python
from app.dependencies import get_container, get_syllabus_service
```

##### 3. Hydra Configuration Structure Issues

**Root Cause**: Configuration access patterns don't match actual Hydra config structure.

**Symptoms**:
- `ConfigAttributeError: Key 'app' is not in struct`
- `Missing key service`

**Systematic Solution**:
```python
# Use defensive configuration access:
docs_url="/docs" if getattr(config, 'service', {}).get('debug', False) else None

# Instead of direct access:
docs_url="/docs" if config.app.debug else None  # WRONG
```

##### 4. Docker Container Code Caching

**Root Cause**: Docker containers use cached code that doesn't reflect file system changes due to aggressive build caching.

**Why Docker Caching Fails**:
- Build context caching uses file checksums but sometimes misses changes
- Image removal doesn't always clear associated build cache layers  
- Docker Compose may reference old cached layers even after image removal
- Container recreation vs rebuild - restart uses existing images

**Systematic Solution** (in order of increasing thoroughness):

```bash
# Level 1: Standard rebuild (often insufficient)
docker compose stop [service-name]
docker image rm -f course-creator-[service-name]:latest
docker compose up -d [service-name]

# Level 2: Force complete cache clearing (recommended)
docker compose stop [service-name]
docker image rm -f course-creator-[service-name]:latest
docker builder prune -f
docker compose build --no-cache [service-name]
docker compose up -d [service-name]

# Level 3: Nuclear option (for persistent cache issues)
docker compose down [service-name]
docker image rm -f course-creator-[service-name]:latest
docker builder prune -af
docker system prune -f
docker compose build --no-cache [service-name]
docker compose up -d [service-name]

# Verification Steps:
docker logs course-creator-[service-name]-1 --tail 10
docker inspect course-creator-[service-name]:latest | grep Created
```

**Prevention Best Practices**:
- Always use `--no-cache` flag when debugging code changes
- Use `docker builder prune -f` between rebuilds
- Verify image creation timestamp matches your rebuild time
- Check container logs immediately after rebuild to confirm changes took effect

#### Verification Steps

After applying fixes, verify systematically:

1. **Import Resolution**: Check for import errors in logs
2. **Service Health**: Use `docker compose ps` to verify status
3. **Endpoint Access**: Test health endpoints once running
4. **Dependency Loading**: Verify dependency injection works

#### Missing Dependencies vs Import Issues

**Import Issues** (structural problems):
- `ImportError: attempted relative import beyond top-level package`
- `NameError: name 'get_syllabus_service' is not defined`

**Dependency Issues** (installation problems):
- `ModuleNotFoundError: No module named 'jwt'`
- `ModuleNotFoundError: No module named 'passlib'`

Import issues require systematic code fixes. Dependency issues require `requirements.txt` updates.

## Centralized Logging System (v2.2 - Syslog Format)

The platform implements centralized logging with syslog format across all services:

### Syslog Format Implementation
All logs now follow RFC 3164 syslog format:
```
Jul 31 08:46:30 hostname service[pid]: LEVEL - filename:line - message
```

Example log entries:
```
Jul 31 08:46:30 20b86b2e3329 course-generator[1]: INFO - /app/main.py:71 - Starting Course Generator Service
Jul 31 08:46:29 6dd7386d44f5 user-management[1]: INFO - /app/main.py:497 - Starting User Management Service on port 8000
```

### Log File Locations
- **Docker Environment**: `/var/log/course-creator/<service>.log` (mounted volume)
- **Development Environment**: `./logs/course-creator/<service>.log`
- **Console Output**: All services also output to stdout with syslog format

### Log File Management
- **Rotation**: 50MB max file size, 10 backup files
- **Levels**: DEBUG (file only), INFO+ (console and file)
- **Services Logged**: All microservices, uvicorn, FastAPI
- **Format**: Includes hostname, PID, service name, log level, file location, and message

### Logging Configuration Files
- `config/logging/syslog.yaml` - Centralized syslog configuration template
- `services/*/logging_setup.py` - Service-specific logging implementation
- Docker Compose includes volume mounts and environment variables for centralized logging

### Monitoring Log Files
```bash
# View all service logs in syslog format
docker compose logs -f

# View specific service logs
docker compose logs -f user-management

# Monitor log files directly
tail -f ./logs/course-creator/*.log

# Check log file sizes and rotation
ls -lh ./logs/course-creator/
```

### Current Platform Status (v2.4 - Enhanced Session Management and Dashboard Layout Fixes)
All services verified healthy and operational with syslog format logging, comprehensive RBAC system, and enhanced session management:
- ✅ Frontend (port 3000) - Nginx with proper health checks and RBAC dashboards
- ✅ User Management (port 8000) - Authentication and basic RBAC with syslog logging
- ✅ Course Generator (port 8001) - AI content generation with syslog logging
- ✅ Content Storage (port 8003) - File management
- ✅ Course Management (port 8004) - Course CRUD + Feedback System
- ✅ Content Management (port 8005) - Upload/export functionality
- ✅ Lab Manager (port 8006) - Multi-IDE container management
- ✅ Analytics (port 8007) - Analytics + PDF generation
- ✅ **Organization Management (port 8008) - Enhanced RBAC system with multi-tenant organization management, granular permissions, track-based learning, and Teams/Zoom integration**
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
curl -s http://localhost:8003/health  # Content Storage
curl -s http://localhost:8004/health  # Course Management
curl -s http://localhost:8005/health  # Content Management
curl -s http://localhost:8006/health  # Lab Manager
curl -s http://localhost:8007/health  # Analytics
curl -s http://localhost:8008/health  # Organization Management (RBAC)
curl -s http://localhost:3000/health  # Frontend

# Run comprehensive tests
python test_feedback_final.py        # Feedback system
python tests/runners/run_rbac_tests.py # Enhanced RBAC system (102 tests - 100% success rate)
python tests/run_all_tests.py        # All test suites
```

## Enhanced Session Management System (v2.4)

The platform now implements comprehensive session management with automatic timeout and security features across all dashboards:

### Session Security Configuration
```javascript
// Session timeout constants applied platform-wide
SESSION_TIMEOUT = 8 * 60 * 60 * 1000;     // 8 hours absolute maximum
INACTIVITY_TIMEOUT = 2 * 60 * 60 * 1000;  // 2 hours of inactivity
AUTO_LOGOUT_WARNING = 5 * 60 * 1000;      // 5 minutes warning period
```

### Session Management Features
- **Absolute Session Timeout** - Maximum 8-hour session duration from login
- **Inactivity Timeout** - 2-hour automatic logout for inactive users
- **Warning System** - 5-minute advance warning before session expiry
- **Cross-tab Synchronization** - Session state synchronized across browser tabs
- **Activity Tracking** - User interactions extend session automatically
- **Secure Cleanup** - Complete localStorage cleanup on logout/expiry
- **Smart Redirects** - Context-aware home page redirects after expiry

### Dashboard Session Validation
All dashboards now implement comprehensive session validation on page load:

#### Session Validation Checks
1. **User Data Validation** - Verify currentUser exists in localStorage
2. **Token Validation** - Confirm authToken is present and valid
3. **Timestamp Validation** - Check sessionStart and lastActivity timestamps
4. **Timeout Enforcement** - Validate against absolute and inactivity timeouts
5. **Role Verification** - Ensure user has appropriate role for dashboard
6. **Automatic Cleanup** - Clear expired session data before redirect

#### Dashboards with Enhanced Session Management
- ✅ **Instructor Dashboard** (`instructor-dashboard.html`) - Comprehensive session validation with role verification
- ✅ **Student Dashboard** (`student-dashboard.js`) - Session timeout and role-based access control
- ✅ **Admin Dashboard** (`admin.js`) - Enhanced session validation with admin role verification
- ✅ **Organization Admin Dashboard** (`org-admin-enhanced.js`) - Class-based session management with API integration
- ✅ **Site Admin Dashboard** (`site-admin-dashboard.js`) - Complete session lifecycle management

### Session Management Implementation Patterns

#### Pattern 1: Inline Session Validation (Student/Instructor Dashboards)
```javascript
// Validate complete session state
if (!currentUser || !authToken || !sessionStart || !lastActivity) {
    console.log('Session invalid: Missing session data');
    window.location.href = '../index.html';
    return;
}

// Check session timeouts
const now = Date.now();
const sessionAge = now - parseInt(sessionStart);
const timeSinceActivity = now - parseInt(lastActivity);

if (sessionAge > SESSION_TIMEOUT || timeSinceActivity > INACTIVITY_TIMEOUT) {
    // Clear expired session and redirect
    clearExpiredSessionData();
    window.location.href = '../index.html';
    return;
}
```

#### Pattern 2: Class-based Session Management (RBAC Dashboards)
```javascript
validateSession() {
    // Complete session validation with role checking
    // Automatic cleanup and smart redirect handling
    // Integration with API authentication flows
}

clearExpiredSession() {
    // Comprehensive localStorage cleanup
    // User-friendly redirect to home page
}
```

## Enhanced Dashboard Layout System (v2.4)

The platform now includes comprehensive dashboard layout fixes addressing scrollbar visibility and z-index hierarchy issues:

### Sidebar Layout Improvements

#### Scrollbar Enhancements
- **Forced Scrollbar Visibility** - `scrollbar-gutter: stable` ensures scrollbar space is always reserved
- **Custom Webkit Styling** - Professional scrollbar appearance with hover effects
- **Cross-browser Support** - Works on Firefox (`scrollbar-width: thin`) and Webkit browsers
- **High DPI Support** - Responsive scrollbar sizing for high-resolution displays
- **Mobile Compatibility** - Maintains scrollbar functionality on touch devices

#### Z-index Hierarchy Fixes
- **Sidebar Z-index** - `var(--z-fixed)` (1000) - Base sidebar layer
- **Header Z-index** - `calc(var(--z-fixed) + 10)` (1010) - Always above sidebar
- **Mobile Overlay** - `calc(var(--z-fixed) + 1)` - Proper touch interaction
- **Mobile Sidebar** - `calc(var(--z-fixed) + 5)` - Above overlay when shown

### Layout CSS Implementation
```css
/* Enhanced sidebar with scrollbar and z-index fixes */
.dashboard-sidebar {
    scrollbar-gutter: stable;           /* Reserve scrollbar space */
    scrollbar-width: thin;              /* Firefox scrollbar styling */
    z-index: var(--z-fixed);          /* Proper layering */
    max-height: 100vh;                 /* Prevent header overlap */
}

/* Custom webkit scrollbar styling */
.dashboard-sidebar::-webkit-scrollbar {
    width: 8px;
}

.dashboard-sidebar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.3);
    border-radius: 4px;
    transition: background 0.2s ease;
}

/* Header z-index fix for zoom level compatibility */
.dashboard-header {
    z-index: calc(var(--z-fixed) + 10);  /* Above sidebar */
}
```

### Zoom Level Compatibility
- **High Zoom Support** - Layout remains functional at 300%+ zoom levels
- **Scrollbar Scaling** - Responsive scrollbar sizing at high magnifications  
- **Header Protection** - Prevents sidebar from overlapping header at any zoom level
- **Content Accessibility** - Maintains readability and navigation at all zoom levels

### Responsive Design Enhancements
- **Mobile Sidebar Behavior** - Proper overlay and z-index management on mobile
- **Touch Interaction** - Correct layering for mobile sidebar controls
- **Grid Responsiveness** - Adaptive layouts for different screen sizes
- **Cross-device Compatibility** - Consistent experience across desktop, tablet, mobile

### Dashboard Types Supported
1. **Sidebar Dashboards** (Student, Instructor) - Full sidebar layout with scrollbar and z-index fixes
2. **Tab-based Dashboards** (Site Admin, Org Admin) - Header z-index improvements for proper layering
3. **Hybrid Layouts** - Support for complex dashboard configurations

### Bug Fixes Implemented
- ✅ **Fixed**: Missing scrollbar when sidebar content exceeds viewport height
- ✅ **Fixed**: Sidebar overlapping header at high zoom levels (200%+)
- ✅ **Fixed**: Inconsistent z-index causing layout conflicts
- ✅ **Fixed**: Touch interaction issues on mobile sidebar overlays
- ✅ **Fixed**: Session expiry showing default usernames instead of redirecting

## Problem-Solving Methodology

### Root Cause Analysis Requirement
**CRITICAL**: When encountering technical issues, Claude Code must use systematic root cause analysis instead of applying incremental fixes. Follow these methodologies:

#### Chain of Thoughts (CoT) Analysis
1. **Problem Identification** - Clearly define the exact problem and its symptoms
2. **Hypothesis Formation** - Generate multiple potential root causes
3. **Evidence Gathering** - Systematically collect data to support or refute each hypothesis
4. **Logical Reasoning** - Apply step-by-step logical analysis to identify the fundamental cause
5. **Solution Design** - Create comprehensive solutions that address the root cause, not just symptoms

#### Tree of Thoughts (ToT) Analysis
1. **Problem Decomposition** - Break complex problems into a tree of sub-problems
2. **Branch Exploration** - Systematically explore each branch of potential causes
3. **Path Evaluation** - Assess the likelihood and impact of each potential cause path
4. **Convergence Analysis** - Identify where multiple paths converge to find common root causes
5. **Holistic Solution** - Design solutions that address multiple branches where appropriate

#### Implementation Requirements
- **NO Band-Aid Fixes** - Avoid quick fixes that only address symptoms
- **Systematic Approach** - Document the analysis process and reasoning
- **Comprehensive Testing** - Verify that solutions address the fundamental issue
- **Documentation** - Record the root cause analysis for future reference

This methodology applies to all technical problem-solving including import issues, service startup failures, dependency conflicts, and architectural problems.

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

## Code Quality and Syntax Validation Requirements (v2.4)

**CRITICAL**: All code generated by Claude Code must pass comprehensive syntax checks and adhere to all directives specified in this CLAUDE.md file. This is a mandatory requirement that cannot be bypassed.

### Mandatory Syntax and Quality Checks

#### Pre-Deployment Validation Checklist
Before any code is considered complete, it MUST pass all of the following validation steps:

**✅ Python Code Validation:**
```bash
# 1. Syntax validation
python -m py_compile filename.py

# 2. Import validation (critical for Docker containers)
python -c "import filename; print('Import successful')"

# 3. Code quality checks
flake8 filename.py                    # PEP8 compliance
black --check filename.py             # Formatting validation
isort --check-only filename.py        # Import order validation

# 4. Security scanning
bandit -r filename.py                 # Security vulnerability detection

# 5. Type checking (if type hints used)
mypy filename.py                      # Static type checking
```

**✅ JavaScript Code Validation:**
```bash
# 1. Syntax validation
node -c filename.js                   # Node.js syntax check

# 2. Code quality checks
eslint filename.js                    # ESLint validation
jshint filename.js                    # Alternative syntax checking

# 3. Module import validation
# Verify ES6 imports work correctly in browser environment

# 4. Browser compatibility validation
# Test in Chrome, Firefox, Safari, Edge
```

**✅ CSS Code Validation:**
```bash
# 1. Syntax validation
csslint filename.css                  # CSS syntax validation

# 2. Code quality checks
stylelint filename.css                # Modern CSS linting

# 3. Browser compatibility
# Verify CSS works across target browsers

# 4. Performance validation
# Check for unused CSS and optimization opportunities
```

**✅ HTML Code Validation:**
```bash
# 1. HTML5 validation
html5validator filename.html          # W3C HTML5 validation

# 2. Accessibility validation
axe-core filename.html               # Accessibility compliance

# 3. Cross-browser testing
# Manual verification in target browsers
```

### CLAUDE.md Directive Compliance Verification

Every piece of generated code MUST comply with ALL directives in this CLAUDE.md file:

#### ✅ Critical Directive Compliance Checklist:

**1. Python Import Requirements (CRITICAL)**
- [ ] **VERIFIED**: All Python imports use absolute imports only
- [ ] **VERIFIED**: No relative imports (../, ./) present anywhere
- [ ] **VERIFIED**: Import statements follow required patterns
- [ ] **VERIFIED**: All imports work in Docker container environment

**2. Comprehensive Documentation Standards**
- [ ] **VERIFIED**: All new code includes multiline string documentation
- [ ] **VERIFIED**: Documentation explains both "what" and "why"
- [ ] **VERIFIED**: Business context included in documentation
- [ ] **VERIFIED**: Technical implementation details provided
- [ ] **VERIFIED**: Problem analysis and solution rationale documented

**3. File Editing Efficiency**
- [ ] **VERIFIED**: Multiple related edits batched together
- [ ] **VERIFIED**: MultiEdit used for systematic updates
- [ ] **VERIFIED**: No unnecessary permission requests for related changes

**3a. File Type-Specific Comment Syntax**
- [ ] **VERIFIED**: Python multiline strings (`"""`) only used in .py files
- [ ] **VERIFIED**: YAML files use `#` comments only
- [ ] **VERIFIED**: JSON files have no comments (not supported)
- [ ] **VERIFIED**: SQL files use `--` or `/* */` comments
- [ ] **VERIFIED**: JavaScript files use `//` or `/* */` comments
- [ ] **VERIFIED**: CSS files use `/* */` comments
- [ ] **VERIFIED**: HTML files use `<!-- -->` comments
- [ ] **VERIFIED**: Bash/shell scripts use `#` comments

**4. Session Management Requirements**
- [ ] **VERIFIED**: All dashboard code includes proper session validation
- [ ] **VERIFIED**: Session timeouts properly configured (8hr/2hr/5min)
- [ ] **VERIFIED**: Role-based access control implemented
- [ ] **VERIFIED**: Proper session cleanup on expiry

**5. Dashboard Layout Standards**
- [ ] **VERIFIED**: Sidebar scrollbar visibility implemented
- [ ] **VERIFIED**: Z-index hierarchy properly configured
- [ ] **VERIFIED**: High zoom level compatibility ensured
- [ ] **VERIFIED**: Mobile responsiveness maintained

**6. SOLID Principles Adherence**
- [ ] **VERIFIED**: Single Responsibility Principle followed
- [ ] **VERIFIED**: Open/Closed Principle implemented
- [ ] **VERIFIED**: Interface segregation applied
- [ ] **VERIFIED**: Dependency inversion respected

**7. Test Driven Development**
- [ ] **VERIFIED**: Tests written before implementation
- [ ] **VERIFIED**: Red-Green-Refactor cycle followed
- [ ] **VERIFIED**: Comprehensive test coverage achieved

### Automated Validation Pipeline

#### Pre-Commit Validation Script
```bash
#!/bin/bash
# validate-code.sh - Comprehensive code validation pipeline

echo "🔍 Starting comprehensive code validation..."

# Python validation
echo "🐍 Validating Python code..."
find . -name "*.py" -exec python -m py_compile {} \; || exit 1
find . -name "*.py" -exec flake8 {} \; || exit 1
find . -name "*.py" -exec black --check {} \; || exit 1

# JavaScript validation  
echo "🌐 Validating JavaScript code..."
find . -name "*.js" -exec node -c {} \; || exit 1
find . -name "*.js" -exec eslint {} \; || exit 1

# CSS validation
echo "🎨 Validating CSS code..."
find . -name "*.css" -exec stylelint {} \; || exit 1

# Import validation (critical for Docker)
echo "📦 Validating Python imports..."
python -c "
import sys
import os
sys.path.append('.')
# Test critical imports
try:
    import services.analytics.main
    import services.user_management.main  
    print('✅ Critical imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

# CLAUDE.md directive compliance
echo "📋 Verifying CLAUDE.md directive compliance..."
# Check for relative imports (forbidden)
if grep -r "from \.\." services/ frontend/; then
    echo "❌ ERROR: Relative imports found (violates CLAUDE.md directive)"
    exit 1
fi

# Check for proper documentation
echo "📝 Validating documentation standards..."
# Verify multiline strings exist in new Python files
python -c "
import ast
import os
import sys

def check_documentation(filepath):
    with open(filepath, 'r') as f:
        try:
            tree = ast.parse(f.read())
            # Check for docstrings and multiline strings
            has_multiline_docs = False
            for node in ast.walk(tree):
                if isinstance(node, ast.Str) and '\\n' in node.s and len(node.s) > 100:
                    has_multiline_docs = True
                    break
            return has_multiline_docs
        except:
            return False

documented_files = 0
total_files = 0

for root, dirs, files in os.walk('services/'):
    for file in files:
        if file.endswith('.py') and '__pycache__' not in root:
            filepath = os.path.join(root, file)
            total_files += 1
            if check_documentation(filepath):
                documented_files += 1

if total_files > 0:
    doc_percentage = (documented_files / total_files) * 100
    print(f'📊 Documentation coverage: {doc_percentage:.1f}% ({documented_files}/{total_files})')
    if doc_percentage < 80:
        print('⚠️  WARNING: Documentation coverage below 80%')
"

echo "✅ All validation checks passed!"
echo "🚀 Code is ready for deployment"
```

### Quality Gate Requirements

Code CANNOT be deployed unless it passes ALL of these gates:

1. **Syntax Validation Gate** - 100% syntax error-free
2. **Import Validation Gate** - All imports work in target environment
3. **CLAUDE.md Compliance Gate** - Full adherence to all directives
4. **Documentation Gate** - Comprehensive multiline documentation present
5. **Security Gate** - No security vulnerabilities detected
6. **Performance Gate** - No critical performance issues identified
7. **Test Coverage Gate** - Minimum 80% test coverage achieved
8. **Browser Compatibility Gate** - Works in all target browsers

### Failure Response Protocol

If ANY validation check fails:

1. **STOP IMMEDIATELY** - Do not proceed with deployment
2. **IDENTIFY ROOT CAUSE** - Use systematic analysis to understand the failure
3. **FIX COMPREHENSIVELY** - Address the underlying issue, not just symptoms
4. **RE-VALIDATE COMPLETELY** - Run all validation checks again
5. **DOCUMENT THE FIX** - Update relevant documentation and CLAUDE.md if needed

### Continuous Compliance Monitoring

- **Daily Validation** - Automated validation runs on all changed files
- **Pre-commit Hooks** - Validation integrated into git workflow
- **CI/CD Integration** - Validation gates in deployment pipeline
- **Code Review Requirements** - Manual verification of CLAUDE.md compliance
- **Documentation Audits** - Regular reviews of documentation completeness

**This validation system ensures that all code maintains the high quality standards established in this repository and prevents regressions in critical areas like session management, documentation quality, and architectural compliance.**

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
- `js/main.js` - Main application entry point
- `js/modules/` - Modular components including:
  - `auth.js` - Enhanced authentication with lab lifecycle integration
  - `lab-lifecycle.js` - Automatic lab container lifecycle management
  - `navigation.js` - Site navigation
  - `notifications.js` - User notifications and alerts
- `js/config.js` - Configuration (supports both ES6 modules and legacy)
- Individual page scripts:
  - `instructor-dashboard.js` - Enhanced with lab container management
  - `student-dashboard.js` - Integrated with automatic lab lifecycle
  - `org-admin-enhanced.js` - **Enhanced RBAC organization administration dashboard with member management, track creation, and meeting room integration**
  - `site-admin-dashboard.js` - **Site administrator interface with comprehensive user management, platform analytics, and audit logging**
  - Other dashboard scripts
- Multi-IDE Lab Interface:
  - `lab-multi-ide.html` - Comprehensive multi-IDE interface with IDE selection, status monitoring, and panel management
  - `lab.html` - Legacy terminal-only interface (still supported)
- **Enhanced RBAC Dashboards:**
  - `org-admin-enhanced.html` - Organization administrator dashboard with comprehensive member, track, and meeting room management
  - `site-admin-dashboard.html` - Site administrator interface with platform-wide user management and analytics

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
- `services/lab-manager/Dockerfile` - Lab manager service container
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