"""
Hello router for test-service service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from models import *
from services.hello_service import HelloService
from dependencies import get_database

router = APIRouter()


@router.get("/hello")
async def say_hello() -> Dict[str, str]:
    """
    Simple hello endpoint
    """
    # TODO: Implement say_hello
    return {"message": "Not implemented yet"}

