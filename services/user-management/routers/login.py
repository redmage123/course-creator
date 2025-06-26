"""
Login router for user-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.login_service import LoginService
from ..dependencies import get_database

router = APIRouter()


