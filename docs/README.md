# Course Creator Platform Documentation

## 📚 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [API Reference](#api-reference)
- [Frontend Guide](#frontend-guide)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## 🏗️ Overview

Course Creator is a modern web platform for creating, managing, and delivering online courses. Built with FastAPI (backend) and React (frontend), it provides a scalable foundation for educational content management.

### Key Features

- **Course Management**: Create, edit, and organize courses
- **User Authentication**: Secure user registration and login
- **Real-time Communication**: WebSocket support for live features
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **RESTful API**: Clean, documented API endpoints
- **Type Safety**: Full TypeScript support

### Technology Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (Database ORM)
- Pydantic (Data validation)
- JWT Authentication
- SQLite/PostgreSQL support

**Frontend:**
- React 18 with TypeScript
- Tailwind CSS for styling
- Axios for HTTP requests
- Modern ES6+ features

## 🏛️ Architecture

    course-creator/
    ├── course-creator-backend/     # FastAPI backend
    │   ├── app/
    │   │   ├── main.py            # Application entry point
    │   │   ├── models/            # Database models
    │   │   ├── routes/            # API endpoints
    │   │   └── services/          # Business logic
    │   └── docs/                  # Documentation
    │
    └── course-creator-frontnd/    # React frontend
        ├── src/
        │   ├── components/        # Reusable components
        │   ├── pages/             # Page components
        │   └── services/          # API communication
        └── public/                # Static assets

### Data Flow

1. **User Interaction**: User interacts with React frontend
2. **API Request**: Frontend makes HTTP requests to FastAPI backend
3. **Authentication**: JWT tokens validate user permissions
4. **Data Processing**: Backend processes requests and queries database
5. **Response**: JSON data returned to frontend
6. **UI Update**: React updates interface with new data

## 🚀 Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm package manager

### Backend Setup

    # Navigate to backend directory
    cd course-creator/course-creator-backend

    # Create virtual environment
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # venv\Scripts\activate    # Windows

    # Install dependencies
    pip install fastapi uvicorn python-multipart markdown

    # Start development server
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

### Frontend Setup

    # Navigate to frontend directory
    cd course-creator/course-creator-frontnd

    # Install dependencies (already done)
    npm install

    # Start development server (already running)
    npm start

### Environment Variables

Create `.env` files for configuration:

**Backend (.env):**

    DATABASE_URL=sqlite:///./courses.db
    SECRET_KEY=your-secret-key-here
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    ENVIRONMENT=development

**Frontend (.env):**

    REACT_APP_API_URL=http://localhost:8000
    REACT_APP_ENVIRONMENT=development

## 📡 API Reference

### Base URL

    http://localhost:8000

### Core Endpoints

#### Health Check

    GET /health

**Response:**

    {
      "status": "healthy",
      "message": "Course Creator API is running",
      "timestamp": "2025-06-30T12:00:00Z",
      "version": "1.0.0"
    }

#### Documentation

    GET /docs

Returns this documentation as HTML.

#### Courses

**List Courses**

    GET /api/courses

**Response:**

    {
      "success": true,
      "data": [
        {
          "id": "1",
          "title": "Introduction to Web Development",
          "description": "Learn HTML, CSS, and JavaScript basics",
          "instructor": "John Doe",
          "price": 99.00,
          "difficulty": "beginner"
        }
      ],
      "message": "Courses retrieved successfully"
    }

**Get Course**

    GET /api/courses/{course_id}

**Create Course**

    POST /api/courses
    Content-Type: application/json

    {
      "title": "Course Title",
      "description": "Course Description",
      "price": 99.99,
      "difficulty": "beginner"
    }

**Update Course**

    PUT /api/courses/{course_id}
    Content-Type: application/json

    {
      "title": "Updated Title",
      "description": "Updated Description"
    }

**Delete Course**

    DELETE /api/courses/{course_id}

#### Authentication (Planned)

**Register User**

    POST /auth/register
    Content-Type: application/json

    {
      "email": "user@example.com",
      "password": "securepassword",
      "full_name": "John Doe"
    }

**Login**

    POST /auth/login
    Content-Type: application/x-www-form-urlencoded

    username=user@example.com&password=securepassword

**Get Current User**

    GET /auth/me
    Authorization: Bearer <token>

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
