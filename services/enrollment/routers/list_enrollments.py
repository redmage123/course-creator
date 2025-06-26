"""
List_Enrollments router for enrollment service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.list_enrollments_service import List_EnrollmentsService
from ..dependencies import get_database

router = APIRouter()


