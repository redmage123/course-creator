"""
Get_Course_Students router for enrollment service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.get_course_students_service import Get_Course_StudentsService
from ..dependencies import get_database

router = APIRouter()


