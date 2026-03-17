"""
Users API endpoints
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_users():
    """Get all users"""
    return {
        "message": "Users endpoint working",
        "users": []
    }

@router.get("/{user_id}")
async def get_user(user_id: str):
    """Get specific user"""
    return {
        "message": f"User {user_id} endpoint working",
        "user_id": user_id
    }
