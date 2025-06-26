"""
Update_Lesson_Progress router for enrollment service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.update_lesson_progress_service import Update_Lesson_ProgressService
from ..dependencies import get_database

router = APIRouter()


