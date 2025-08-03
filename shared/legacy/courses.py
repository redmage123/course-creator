"""
Courses API endpoints
"""
from fastapi import APIRouter
from typing import List

router = APIRouter()

@router.get("/")
async def get_courses():
    """Get all courses"""
    return {
        "message": "Courses endpoint working",
        "courses": []
    }

@router.get("/{course_id}")
async def get_course(course_id: str):
    """Get specific course"""
    return {
        "message": f"Course {course_id} endpoint working",
        "course_id": course_id
    }

@router.post("/")
async def create_course():
    """Create new course"""
    return {"message": "Create course endpoint working"}
