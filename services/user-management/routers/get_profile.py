"""
Get_Profile router for user-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.get_profile_service import Get_ProfileService
from ..dependencies import get_database

router = APIRouter()


