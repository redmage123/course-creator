# Course Creator Platform Documentation

Welcome to the comprehensive documentation for the Course Creator Platform - a modern, microservices-based educational platform with multi-IDE lab environments.

## 📚 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Multi-IDE Lab System](#multi-ide-lab-system)
- [Installation](#installation)
- [API Reference](#api-reference)
- [Frontend Guide](#frontend-guide)
- [Development](#development)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## 🏗️ Overview

Course Creator is a comprehensive web platform for creating, managing, and delivering interactive programming courses with hands-on lab environments. Built with a microservices architecture using FastAPI (backend) and modern HTML/CSS/JavaScript (frontend), it provides a scalable foundation for educational content management with AI-powered content generation and individual student lab containers.

### Key Features

- **AI-Powered Content Generation**: Generate complete courses with syllabus, slides, exercises, and quizzes
- **Multi-IDE Lab Environments**: VSCode Server, JupyterLab, IntelliJ IDEA, and Terminal support
- **Individual Student Lab Containers**: Per-student isolated Docker environments with persistent storage
- **Seamless IDE Switching**: Change development environments without losing work
- **Real-time Lab Monitoring**: Instructor controls for managing student lab sessions
- **Interactive Quiz System**: Automated quiz generation with immediate feedback
- **Comprehensive Analytics**: Student progress tracking and usage metrics
- **Multi-Format Export**: Export content to PowerPoint, PDF, Excel, SCORM, ZIP formats
- **Secure Authentication**: JWT-based authentication with role-based access control

### Technology Stack

**Backend (Microservices):**
- FastAPI (Python web framework)
- PostgreSQL (Primary database)
- Redis (Session management and caching)
- Docker & Docker Compose (Containerization)
- JWT Authentication with RBAC
- Hydra (Configuration management)
- Pydantic (Data validation)

**Frontend:**
- Modern HTML5/CSS3/JavaScript (ES6 modules)
- Bootstrap 5 (UI framework)
- xterm.js (Terminal emulation)
- Multi-IDE web interfaces (VSCode Server, JupyterLab)

**AI Integration:**
- Anthropic Claude (Primary)
- OpenAI (Fallback)
- Content generation and analysis

**Infrastructure:**
- Docker-in-Docker for student lab containers
- Nginx (Reverse proxy)
- Individual container orchestration
- Persistent storage management

## 🏛️ Architecture

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
    └── api/                   # API documentation including multi-IDE endpoints
```

### Service Dependencies
Services start in dependency order with health checks:
User Management → Course Generator → Course Management → Content Storage → Content Management → Lab Container Manager → Analytics Service

### Data Flow

1. **User Interaction**: User interacts with modern HTML/CSS/JavaScript frontend
2. **API Request**: Frontend makes HTTP requests to FastAPI microservices
3. **Authentication**: JWT tokens validate user permissions
4. **Lab Container Management**: Lab manager creates/manages Docker containers
5. **IDE Selection**: Users can switch between VSCode, Jupyter, IntelliJ, Terminal
6. **Data Processing**: Backend processes requests and queries database
7. **Response**: JSON data returned to frontend
8. **UI Update**: Frontend updates interface with new data and lab status

## 🔬 Multi-IDE Lab System

The Course Creator platform features a comprehensive multi-IDE lab environment that provides students and instructors with flexible development options.

### Supported IDEs

#### 1. Terminal (xterm.js)
- **Port**: 8080 (main port)
- **Description**: Traditional command-line interface
- **Features**: Full terminal access, file system navigation, command execution
- **Always Available**: Yes
- **Best For**: System administration, command-line tools, shell scripting

#### 2. VSCode Server
- **Port**: 8081
- **Description**: Full web-based Visual Studio Code
- **Features**: 
  - Syntax highlighting and IntelliSense
  - Integrated terminal and debugging
  - File explorer and Git integration
  - Extension support
- **Pre-installed Extensions**: Python, Black Formatter, Pylint, Jupyter
- **Best For**: General programming, web development, code editing

#### 3. JupyterLab
- **Port**: 8082
- **Description**: Interactive notebook environment for data science
- **Features**:
  - Notebook interface with code and markdown cells
  - Rich output display (plots, tables, images)
  - File browser and terminal access
  - Built-in Python kernel
- **Pre-installed Packages**: NumPy, Pandas, Matplotlib, Seaborn, Requests
- **Best For**: Data science, research, exploratory programming, documentation

#### 4. IntelliJ IDEA (Optional)
- **Port**: 8083
- **Description**: Professional IDE via JetBrains Projector
- **Features**:
  - Advanced code intelligence and refactoring
  - Integrated version control and database tools
  - Comprehensive debugging capabilities
- **Availability**: Resource-intensive, may not always be enabled
- **Best For**: Professional Java/Python development, complex projects

### Key Features

#### Seamless IDE Switching
- Change development environments without losing work
- Persistent file system across all IDEs
- Session state maintained during switches
- Real-time status indicators

#### Resource Management
- **Multi-IDE Mode**: 2GB memory, 150% CPU allocation
- **Single IDE Mode**: 1GB memory, 100% CPU allocation
- Dynamic port allocation (8080-8083 range)
- Automatic resource scaling based on usage

#### Health Monitoring
- Real-time IDE service health checks
- Automatic recovery from service failures
- Performance monitoring and analytics
- Usage tracking for optimization

### Student Experience

1. **Lab Initialization**: Automatic setup on login with preferred IDE
2. **IDE Selection**: Click tabs to switch between development environments
3. **Persistent Storage**: Work automatically saved across sessions and IDE switches
4. **Status Indicators**: Real-time feedback on IDE availability and health
5. **Seamless Workflow**: Continue work in any IDE without data loss

### Instructor Controls

1. **Real-time Monitoring**: View all student lab containers with IDE usage
2. **Resource Analytics**: Track which IDEs students prefer and use most
3. **Performance Metrics**: Monitor resource usage and optimize allocation
4. **Bulk Operations**: Manage multiple lab sessions simultaneously
5. **Custom Environments**: Create specialized lab images with specific IDE configurations

## 🚀 Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Redis 6+
- Docker 20.10+ and Docker Compose V2
- Node.js 16+ (for frontend testing)
- Docker daemon running (for lab container functionality)

### Quick Start (Docker Compose - Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd course-creator
   ```

2. **Configure environment variables**
   ```bash
   # Copy and edit environment configuration
   cp .cc_env.example .cc_env
   # Edit .cc_env with your database credentials and API keys
   ```

3. **Start the entire platform**
   ```bash
   # Production deployment using Docker Compose
   docker-compose up -d
   
   # Check service status
   docker-compose ps
   
   # View logs
   docker-compose logs -f
   ```

4. **Access the application**
   - Frontend: http://localhost:8080
   - Multi-IDE Lab Environment: http://localhost:8080/lab-multi-ide.html
   - Instructor Dashboard: http://localhost:8080/instructor-dashboard.html
   - API Documentation: http://localhost:8001/docs

### Development Setup (Native)

1. **Set up environment**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Set up the database**
   ```bash
   # Setup database and run migrations
   python setup-database.py
   
   # Create admin user
   python create-admin.py
   ```

3. **Start all services**
   ```bash
   # Using app-control.sh for development
   ./app-control.sh start
   
   # Check service status
   ./app-control.sh status
   ```

4. **Serve frontend**
   ```bash
   # Using Python's built-in server
   cd frontend && python -m http.server 8080
   ```

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

# Lab Container Configuration
MAX_CONCURRENT_LABS=50
LAB_SESSION_TIMEOUT=3600
LAB_STORAGE_PATH=/app/lab-storage
```

## 📡 API Reference

### Microservices Overview

The platform consists of 7 core backend services, each with its own API:

- **User Management** (Port 8000): Authentication & user profiles
- **Course Generator** (Port 8001): AI content generation
- **Content Storage** (Port 8003): File storage & versioning
- **Course Management** (Port 8004): Course CRUD operations
- **Content Management** (Port 8005): Upload/download & export
- **Lab Container Manager** (Port 8006): Multi-IDE lab environments
- **Analytics** (Port 8007): Student analytics & progress tracking

### Authentication

All endpoints require JWT authentication:
```
Authorization: Bearer <your-jwt-token>
```

### Core API Endpoints

#### User Management Service (Port 8000)
```http
POST /auth/login              # User login
GET /auth/profile            # Get user profile
GET /users                   # List users (admin)
POST /users                  # Create user
```

#### Course Generator Service (Port 8001)
```http
POST /generate/syllabus      # Generate course syllabus
POST /generate/slides        # Generate course slides
POST /exercises/generate     # Generate exercises
POST /quiz/generate-for-course # Generate quizzes
GET /exercises/{course_id}   # Get course exercises
GET /quiz/course/{course_id} # Get course quizzes
```

#### Course Management Service (Port 8004)
```http
GET /courses                 # List all courses
POST /courses                # Create new course
GET /courses/{course_id}     # Get course details
PUT /courses/{course_id}     # Update course
DELETE /courses/{course_id}  # Delete course
```

#### Lab Container Manager (Port 8006) - Multi-IDE Support
```http
# Core Lab Management
POST /labs                   # Create new lab container (with multi-IDE support)
POST /labs/student           # Get or create student lab
GET  /labs                   # List all lab containers
GET  /labs/{lab_id}         # Get lab details
POST /labs/{lab_id}/pause   # Pause lab container
POST /labs/{lab_id}/resume  # Resume lab container
DELETE /labs/{lab_id}       # Stop and remove lab
GET  /labs/instructor/{course_id} # Get instructor lab overview

# Multi-IDE Management
GET  /labs/{lab_id}/ides    # Get available IDEs for lab
POST /labs/{lab_id}/ide/switch # Switch preferred IDE
GET  /labs/{lab_id}/ide/status # Get IDE health status
```

#### Analytics Service (Port 8007)
```http
POST /activities/track       # Track student activities
POST /lab-usage/track       # Track lab usage metrics
POST /quiz-performance/track # Track quiz performance
POST /progress/update       # Update student progress
GET  /analytics/student/{id} # Get student analytics
GET  /analytics/course/{id}  # Get course analytics
```

### Multi-IDE Lab API

For detailed multi-IDE API documentation, see [Multi-IDE Endpoints Documentation](api/multi-ide-endpoints.md).

#### Key Multi-IDE Endpoints

**Create Multi-IDE Lab:**
```http
POST /labs
{
  "user_id": "student123",
  "course_id": "python101",
  "lab_type": "python",
  "preferred_ide": "vscode",
  "enable_multi_ide": true
}
```

**Switch IDE:**
```http
POST /labs/{lab_id}/ide/switch?ide_type=jupyter
```

**Get IDE Status:**
```http
GET /labs/{lab_id}/ide/status
```

Response includes health status for all IDEs:
```json
{
  "status": "running",
  "ides": {
    "terminal": {"healthy": true, "port": 8080},
    "vscode": {"healthy": true, "port": 8081},
    "jupyter": {"healthy": true, "port": 8082},
    "intellij": {"healthy": false, "port": 8083}
  }
}
```

### Response Formats

**Success Response:**

    {
      "success": true,
      "data": {},
      "message": "Operation successful"
    }

**Error Response:**

    {
      "success": false,
      "error": "Error message",
      "details": {}
    }

### Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## 🎨 Frontend Guide

### Current Structure

The frontend is built with React and includes:

- **Home Page**: Landing page with course overview
- **Courses Page**: Browse available courses
- **Teaching Page**: Information for instructors
- **Navigation**: Seamless page transitions

### Key Components

**App.tsx**: Main application component with routing

    const [currentPage, setCurrentPage] = useState<string>('home');

    const navigateTo = (page: string) => {
      console.log('Navigating to:', page);
      setCurrentPage(page);
    };

**Component Structure:**

    import React, { useState, useEffect } from 'react';

    const CourseList = () => {
      const [courses, setCourses] = useState([]);
      const [loading, setLoading] = useState(true);

      useEffect(() => {
        fetchCourses();
      }, []);

      const fetchCourses = async () => {
        try {
          const response = await fetch('/api/courses');
          const data = await response.json();
          setCourses(data.data);
        } catch (error) {
          console.error('Error fetching courses:', error);
        } finally {
          setLoading(false);
        }
      };

      if (loading) return <div>Loading...</div>;

      return (
        <div className="grid gap-4">
          {courses.map(course => (
            <div key={course.id} className="bg-white p-6 rounded-lg">
              <h3>{course.title}</h3>
              <p>{course.description}</p>
            </div>
          ))}
        </div>
      );
    };

### Styling Guidelines

**Tailwind CSS Classes:**

    // Layout
    <div className="container mx-auto px-4 py-8">

    // Buttons
    <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">

    // Cards
    <div className="bg-white rounded-xl shadow-lg p-6">

    // Forms
    <input className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">

### State Management

**Local State (useState):**

    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

**Effect Hooks (useEffect):**

    useEffect(() => {
      // Component mount logic
      fetchData();
      
      return () => {
        // Cleanup logic
      };
    }, [dependency]);

## 🛠️ Development

### Adding New Features

**1. Backend Endpoint:**

    # app/main.py
    @app.post("/api/courses")
    async def create_course(course_data: dict):
        # Implementation
        return {"message": "Course created", "success": True}

**2. Frontend Component:**

    // src/components/NewFeature.tsx
    import React from 'react';

    const NewFeature = () => {
      return (
        <div className="new-feature">
          {/* Component implementation */}
        </div>
      );
    };

    export default NewFeature;

### Code Style

**Python (PEP 8):**

    # Use descriptive variable names
    course_title = "Introduction to Python"
    
    # Use type hints
    def create_course(title: str, price: float) -> dict:
        return {"title": title, "price": price}

**TypeScript/React:**

    // Use proper typing
    interface Course {
      id: string;
      title: string;
      price: number;
    }
    
    const CourseCard: React.FC<{course: Course}> = ({ course }) => {
      return <div>{course.title}</div>;
    };

### Current Development Status

✅ **Completed:**
- React frontend with navigation
- FastAPI backend with documentation endpoint
- Health check endpoint
- Responsive design with Tailwind CSS
- TypeScript support
- CORS configuration

🔄 **In Progress:**
- Course management API endpoints
- Database integration
- User authentication system

📋 **Planned:**
- User registration/login
- Course creation interface
- Payment integration
- Video upload support
- Real-time features with WebSockets

## 🐛 Troubleshooting

### Common Issues

**Frontend Not Loading:**

    # Check if React is running
    npm start

    # Clear cache
    npm start -- --reset-cache

    # Check for port conflicts
    lsof -i :3000

**Backend Connection Issues:**

    # Check if FastAPI is running
    uvicorn app.main:app --reload --port 8000

    # Test health endpoint
    curl http://localhost:8000/health

    # Check for port conflicts
    lsof -i :8000

**CORS Issues:**

The backend is configured to allow requests from `localhost:3000`. If you're running on different ports, update the CORS settings in `app/main.py`:

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

**TypeScript Errors:**

Ensure proper typing:

    // Good
    const navigateTo = (page: string) => { ... }

    // Bad
    const navigateTo = (page) => { ... }

**Module Not Found Errors:**

    # Frontend dependencies
    cd course-creator-frontnd
    npm install

    # Backend dependencies
    cd course-creator-backend
    pip install -r requirements.txt

### Performance Issues

**Frontend Bundle Size:**

    # Analyze bundle
    npm run build
    npx serve -s build

**Backend Response Time:**

    # Add logging
    import time
    
    @app.middleware("http")
    async def add_process_time_header(request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

### Debugging Tips

**Frontend Console Logs:**

Open browser DevTools (F12) and check:
- Console tab for JavaScript errors
- Network tab for API call failures
- Application tab for localStorage data

**Backend Logs:**

FastAPI automatically logs requests when running with `--reload` flag:

    uvicorn app.main:app --reload --log-level debug

**API Testing:**

Use curl to test endpoints directly:

    # Test health endpoint
    curl http://localhost:8000/health

    # Test courses endpoint
    curl http://localhost:8000/api/courses

## 📞 Support

### System Requirements

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

### Quick Start Checklist

1. ✅ Backend running on port 8000
2. ✅ Frontend running on port 3000
3. ✅ Both services can communicate
4. ✅ Documentation accessible
5. ✅ No console errors

### For Issues or Questions:

1. Check this documentation first
2. Review console logs for errors
3. Verify both services are running
4. Test API endpoints directly
5. Check network connectivity

### Useful Commands

    # Stop all node processes
    pkill -f node

    # Stop all Python processes
    pkill -f python

    # Restart everything
    cd course-creator-backend && uvicorn app.main:app --reload &
    cd course-creator-frontnd && npm start

---

**Documentation Version**: 1.0.0  
**Last Updated**: 2025-06-30  
**Generated**: Course Creator Platform
