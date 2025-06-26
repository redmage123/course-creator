"""
Get_Student_Progress router for enrollment service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.get_student_progress_service import Get_Student_ProgressService
from ..dependencies import get_database

router = APIRouter()


