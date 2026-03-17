# Key Systems

## Advanced Password Management System (v3.0)

The platform includes comprehensive password management capabilities for secure user account administration and self-service password operations:

### Organization Admin Password Creation
- **Registration-Time Password Setting** - Organization administrators set their own passwords during registration process
- **Real-Time Strength Validation** - Password strength indicators with visual feedback (weak/medium/strong scoring)
- **Security Requirements Enforcement** - Minimum 8 characters with complexity scoring based on character types
- **Password Confirmation Validation** - Real-time matching verification with immediate error feedback
- **Professional Email Integration** - Password creation tied to professional email validation for business accounts

### Self-Service Password Management
- **Dedicated Password Change Interface** - Responsive, accessible interface for all user roles (org admin, site admin, instructor)
- **Current Password Verification** - Security-first approach requiring current password before allowing changes
- **Password Visibility Toggle** - User-friendly show/hide functionality for all password input fields
- **Comprehensive Validation** - New password must differ from current, meet strength requirements, and match confirmation
- **Secure Authentication Flow** - Integration with JWT token system for authenticated password change requests

### Enhanced UI/UX Features
- **Mobile-Responsive Design** - Touch-optimized interface with swipe-friendly interactions
- **Accessibility Support** - ARIA labels, keyboard navigation, screen reader compatibility
- **Real-Time Feedback** - Immediate validation with helpful error messages and improvement suggestions
- **Progress Indicators** - Visual feedback during password strength analysis and form submission
- **Success Handling** - Clear confirmation messages with automatic redirect to appropriate dashboard

### Password Management API Endpoints
```http
# Password Management
POST /auth/password/change    # Change user password (requires authentication)
POST /auth/register          # Create user account with password (enhanced for org admins)

# Organization Admin Creation
POST /organizations          # Create organization with admin user account
POST /organizations/upload   # Create organization with logo and admin account
```

### Technical Integration
- **Service-to-Service Communication** - Organization service creates admin users via HTTP client to user management service
- **Password Security** - Secure handling of user-provided passwords vs auto-generated temporary passwords
- **Configuration Management** - Support for both ES6 modules and script tag loading contexts
- **Error Handling** - Comprehensive error management with specific feedback for different failure scenarios

## Enhanced UI Accessibility Features (v3.0)

### Keyboard Navigation System
- **Country Dropdown Search** - Type-to-search functionality for 195+ countries in phone number fields
- **Real-Time Filtering** - Instant country matching with visual search feedback and match count display
- **Keyboard Controls** - Arrow key navigation, Enter to select, Escape to clear search
- **Search Persistence** - 1-second search timeout with automatic clear for continuous typing experience
- **Accessibility Labels** - Comprehensive ARIA labeling and tooltips for keyboard navigation instructions

### Form Enhancement Features
- **Real-Time Validation** - Immediate field validation with specific, actionable error messages
- **Visual Feedback Systems** - Color-coded validation states with progress bars and strength indicators
- **Responsive Design** - Mobile-first approach with touch-friendly controls and optimized layouts
- **Professional Email Validation** - Business-only email enforcement with clear guidance for acceptable domains
- **Progressive Disclosure** - Smart form organization with contextual help text and inline guidance

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

## Enhanced RBAC System (v2.3)

The platform includes a comprehensive Role-Based Access Control (RBAC) system with multi-tenant organization management:

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

#### Organization Administrator  
- **Organization Management** - Complete control within their organization boundary
- **Member Management** - Add, remove, and manage organization members
- **Track Creation** - Design and manage learning tracks and curricula
- **Meeting Room Management** - Create and configure MS Teams/Zoom meeting rooms

#### Instructor
- **Course Creation** - Create and manage courses within assigned projects
- **Student Management** - Manage students within their courses
- **Content Development** - Access to AI content generation tools
- **Assessment Tools** - Create and grade quizzes, assignments

#### Student
- **Course Access** - Access to enrolled courses and learning materials
- **Assignment Submission** - Submit assignments and take quizzes
- **Lab Environment** - Access to personalized lab containers
- **Progress Tracking** - View personal learning progress and achievements

### Track-Based Learning System
- **Automatic Enrollment** - Students automatically enrolled in relevant tracks
- **Learning Path Optimization** - AI-recommended learning sequences
- **Progress Tracking** - Comprehensive progress monitoring across tracks
- **Prerequisite Management** - Automatic prerequisite validation and enforcement
- **Certification Tracking** - Track completion certificates and achievements

### Meeting Room Integration
#### MS Teams Integration
- **Automatic Room Creation** - Dynamic Teams meeting room generation
- **Organization Rooms** - Persistent meeting spaces for entire organizations
- **Track-Specific Rooms** - Dedicated rooms for learning tracks
- **Instructor Rooms** - Personal meeting spaces for instructors

#### Zoom Integration
- **Meeting Management** - Full Zoom meeting lifecycle management
- **Room Configuration** - Custom settings for different meeting types
- **Participant Controls** - Mute, recording, and screen sharing permissions
- **Security Settings** - Waiting rooms and password protection

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
```

## RAG-Enhanced AI System (v2.4 - Intelligent Learning Integration)

The platform includes a comprehensive Retrieval-Augmented Generation (RAG) system that makes AI progressively smarter through continuous learning:

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

### RAG Service API Endpoints
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

### RAG Learning Mechanisms
- **Quality Scoring** - Automatic assessment of generation quality and learning prioritization
- **User Feedback Integration** - Learning from instructor and student feedback on content effectiveness
- **Pattern Recognition** - Identification of successful educational structures and approaches
- **Domain Specialization** - Building expertise in specific subjects and difficulty levels
- **Continuous Optimization** - Progressive improvement through accumulated experience

## Lab Container Management System (v2.1 - Multi-IDE Edition)

The platform includes a comprehensive lab container management system with multi-IDE support:

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

# Multi-IDE Management
GET  /labs/{lab_id}/ides     # Get available IDEs for lab
POST /labs/{lab_id}/ide/switch # Switch preferred IDE
GET  /labs/{lab_id}/ide/status # Get IDE health status
```

### Lab Container Architecture
- **Docker-in-Docker (DinD)** - Lab containers require Docker daemon access
- **Dynamic Image Building** - Temporary directories for Dockerfile generation with multi-IDE support
- **Network Isolation** - Student containers cannot access other platform services
- **Automatic Cleanup** - Prevents resource leaks from abandoned containers
- **Health Monitoring** - Container and IDE service availability checks before student access

## System Integration

### Cross-System Communication
- **Event-Driven Architecture** - Systems communicate through well-defined APIs
- **Data Consistency** - Shared database ensures data integrity across systems
- **Real-time Updates** - WebSocket and polling mechanisms for live updates
- **Error Handling** - Comprehensive error propagation and recovery mechanisms

### Shared Resources
- **PostgreSQL Database** - Central data store for all systems
- **Redis Cache** - Shared caching layer for performance optimization
- **File Storage** - Centralized file management for content and lab data
- **Authentication** - Unified JWT-based authentication across all systems

### Performance Optimization
- **Caching Strategies** - Redis-based caching for frequently accessed data
- **Database Optimization** - Indexed queries and connection pooling
- **Resource Management** - Dynamic resource allocation based on usage patterns
- **Load Balancing** - Horizontal scaling capabilities for high-demand systems

## Demo Service System (v2.9)

The platform includes a comprehensive demo service that allows potential users to explore the platform functionality without registration:

### Realistic Demo Data Generation
- **Multi-User Role Support** - Separate demo experiences for instructors, students, and administrators
- **Faker Integration** - Realistic course data, student profiles, analytics, and feedback using Python Faker library
- **Dynamic Content** - Fresh demo data generated for each session with realistic relationships and dependencies
- **Context-Aware Data** - Demo content adapts based on user type (instructor sees smaller classes, admin sees platform-wide metrics)

### Session Management
- **Time-Limited Sessions** - 2-hour demo sessions with automatic expiration and cleanup
- **Session Isolation** - Each demo session is completely isolated with independent data
- **Multi-Concurrent Support** - Multiple users can run demo sessions simultaneously without interference
- **Graceful Expiration** - Sessions expire gracefully with user notifications and cleanup

### Demo Features Coverage
- **Course Management** - Create, view, and manage AI-generated courses with realistic content
- **Student Analytics** - View comprehensive student progress, engagement metrics, and performance data
- **Lab Environments** - Explore multi-IDE lab container system with simulated development environments
- **Feedback Systems** - Experience bi-directional feedback with realistic student and instructor interactions
- **RBAC Demonstration** - Multi-tenant organization management with role-based access controls

### API Endpoints
```http
# Demo Session Management
POST /api/v1/demo/start?user_type={instructor|student|admin}  # Start demo session
GET  /api/v1/demo/session/info?session_id={id}               # Get session information
DELETE /api/v1/demo/session?session_id={id}                  # End demo session

# Demo Data Access
GET  /api/v1/demo/courses?session_id={id}                    # Get demo courses
GET  /api/v1/demo/students?session_id={id}                   # Get demo students (instructor/admin only)
GET  /api/v1/demo/analytics?session_id={id}&timeframe={7d|30d|90d|1y}  # Get demo analytics
GET  /api/v1/demo/labs?session_id={id}                       # Get demo lab environments
GET  /api/v1/demo/feedback?session_id={id}                   # Get demo feedback data

# Demo Content Creation
POST /api/v1/demo/course/create?session_id={id}              # Simulate AI course creation
```

### Frontend Integration
- **Try Demo Button** - Prominent demo access from home page with user type selection
- **Demo Mode Indicators** - Clear visual indicators when users are in demo mode
- **Session Timers** - Display remaining demo time with warnings before expiration
- **Seamless Transitions** - Smooth transitions between demo dashboards and real platform registration