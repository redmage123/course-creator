"""
Update_Profile router for user-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.update_profile_service import Update_ProfileService
from ..dependencies import get_database

router = APIRouter()


