"""
Simple FastAPI test
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI application
app = FastAPI(
    title="Course Creator Platform",
    description="A comprehensive platform for creating and managing online courses",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "message": "Course Creator Platform is running",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Course Creator Platform API",
        "docs": "/docs",
        "health": "/health"
    }

# Simple test endpoints
@app.get("/auth/test")
async def auth_test():
    return {"message": "Auth endpoint working"}

@app.get("/api/courses")
async def courses_test():
    return {"message": "Courses endpoint working", "courses": []}

@app.get("/api/users")
async def users_test():
    return {"message": "Users endpoint working", "users": []}

@app.get("/api/enrollments")
async def enrollments_test():
    return {"message": "Enrollments endpoint working", "enrollments": []}
