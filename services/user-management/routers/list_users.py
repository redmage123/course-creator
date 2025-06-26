"""
List_Users router for user-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.list_users_service import List_UsersService
from ..dependencies import get_database

router = APIRouter()


