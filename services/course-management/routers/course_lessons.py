"""
Course_Lessons router for course-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.course_lessons_service import Course_LessonsService
from ..dependencies import get_database

router = APIRouter()


