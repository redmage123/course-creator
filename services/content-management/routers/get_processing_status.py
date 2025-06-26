"""
Get_Processing_Status router for content-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.get_processing_status_service import Get_Processing_StatusService
from ..dependencies import get_database

router = APIRouter()


