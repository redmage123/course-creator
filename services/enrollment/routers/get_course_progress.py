"""
Get_Course_Progress router for enrollment service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.get_course_progress_service import Get_Course_ProgressService
from ..dependencies import get_database

router = APIRouter()


