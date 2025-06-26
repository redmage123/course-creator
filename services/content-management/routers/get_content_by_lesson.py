"""
Get_Content_By_Lesson router for content-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.get_content_by_lesson_service import Get_Content_By_LessonService
from ..dependencies import get_database

router = APIRouter()


