"""
Verify_Email router for user-management service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.verify_email_service import Verify_EmailService
from ..dependencies import get_database

router = APIRouter()


