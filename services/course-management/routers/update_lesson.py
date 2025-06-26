"""
Update_Lesson router for course-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.update_lesson_service import Update_LessonService
from ..dependencies import get_database

router = APIRouter()


