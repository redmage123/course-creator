"""
Enrollments API endpoints
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_enrollments():
    """Get all enrollments"""
    return {
        "message": "Enrollments endpoint working",
        "enrollments": []
    }

@router.post("/")
async def create_enrollment():
    """Create new enrollment"""
    return {"message": "Create enrollment endpoint working"}
