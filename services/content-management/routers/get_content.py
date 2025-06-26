"""
Get_Content router for content-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.get_content_service import Get_ContentService
from ..dependencies import get_database

router = APIRouter()


