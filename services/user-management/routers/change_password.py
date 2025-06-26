"""
Change_Password router for user-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.change_password_service import Change_PasswordService
from ..dependencies import get_database

router = APIRouter()


