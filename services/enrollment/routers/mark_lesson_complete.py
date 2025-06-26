"""
Mark_Lesson_Complete router for enrollment service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.mark_lesson_complete_service import Mark_Lesson_CompleteService
from ..dependencies import get_database

router = APIRouter()


