"""
Get_Student_Courses router for enrollment service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.get_student_courses_service import Get_Student_CoursesService
from ..dependencies import get_database

router = APIRouter()


