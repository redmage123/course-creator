"""
Get_Lesson router for course-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.get_lesson_service import Get_LessonService
from ..dependencies import get_database

router = APIRouter()


