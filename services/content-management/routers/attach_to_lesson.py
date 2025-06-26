"""
Attach_To_Lesson router for content-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.attach_to_lesson_service import Attach_To_LessonService
from ..dependencies import get_database

router = APIRouter()


