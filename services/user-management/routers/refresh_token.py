"""
Refresh_Token router for user-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.refresh_token_service import Refresh_TokenService
from ..dependencies import get_database

router = APIRouter()


