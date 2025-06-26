"""
Update_Enrollment router for enrollment service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.update_enrollment_service import Update_EnrollmentService
from ..dependencies import get_database

router = APIRouter()


