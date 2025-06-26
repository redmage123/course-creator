"""
Issue_Certificate router for enrollment service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.issue_certificate_service import Issue_CertificateService
from ..dependencies import get_database

router = APIRouter()


