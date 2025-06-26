"""
Add_Lesson router for course-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.add_lesson_service import Add_LessonService
from ..dependencies import get_database

router = APIRouter()


