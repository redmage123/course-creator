"""
Process_Video router for content-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.process_video_service import Process_VideoService
from ..dependencies import get_database

router = APIRouter()


