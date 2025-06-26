"""
List_Content router for content-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.list_content_service import List_ContentService
from ..dependencies import get_database

router = APIRouter()


