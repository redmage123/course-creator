"""
Update_Course router for course-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.update_course_service import Update_CourseService
from ..dependencies import get_database

router = APIRouter()


