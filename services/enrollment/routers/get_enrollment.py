"""
Get_Enrollment router for enrollment service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.get_enrollment_service import Get_EnrollmentService
from ..dependencies import get_database

router = APIRouter()


