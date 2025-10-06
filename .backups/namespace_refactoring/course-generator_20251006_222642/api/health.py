"""
Health API Routes

Simple health check and system status endpoints.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime
import logging

from app.dependencies import get_container

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def root() -> Dict[str, Any]:
    """
    Root endpoint providing basic API information.
    
    Returns:
        Basic API information and status
    """
    return {
        "message": "Course Generator API",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Basic health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "course-generator",
        "version": "2.0.0"
    }


@router.get("/templates")
async def get_templates() -> Dict[str, Any]:
    """
    Get available course templates for content generation.
    
    Business Context:
    Course templates provide predefined structures and formats for AI-powered
    content generation, ensuring consistency and quality across generated
    educational materials while reducing generation time and improving outcomes.
    
    Returns:
        Available course templates with metadata and configuration options
    """
    # Standard course templates for AI content generation
    templates = [
        {
            "id": "programming-fundamentals",
            "name": "Programming Fundamentals",
            "description": "Comprehensive programming course template with hands-on labs",
            "difficulty": "beginner",
            "modules": 12,
            "estimated_hours": 40,
            "includes": ["syllabus", "quizzes", "slides", "exercises", "labs"]
        },
        {
            "id": "data-science-intro",
            "name": "Introduction to Data Science",
            "description": "Data science course with Python and analytics focus",
            "difficulty": "intermediate",
            "modules": 10,
            "estimated_hours": 35,
            "includes": ["syllabus", "quizzes", "slides", "exercises", "jupyter_labs"]
        },
        {
            "id": "web-development",
            "name": "Modern Web Development",
            "description": "Full-stack web development with modern frameworks",
            "difficulty": "intermediate",
            "modules": 15,
            "estimated_hours": 50,
            "includes": ["syllabus", "quizzes", "slides", "projects", "labs"]
        },
        {
            "id": "cybersecurity-basics",
            "name": "Cybersecurity Fundamentals",
            "description": "Essential cybersecurity concepts and practices",
            "difficulty": "beginner",
            "modules": 8,
            "estimated_hours": 30,
            "includes": ["syllabus", "quizzes", "slides", "scenarios", "labs"]
        }
    ]
    
    return {
        "templates": templates,
        "total_count": len(templates),
        "categories": list(set(t["difficulty"] for t in templates)),
        "message": "Course templates available for AI content generation"
    }