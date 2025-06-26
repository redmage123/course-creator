"""
Unenroll_Student router for enrollment service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.unenroll_student_service import Unenroll_StudentService
from ..dependencies import get_database

router = APIRouter()


