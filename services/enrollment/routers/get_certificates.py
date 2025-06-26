"""
Get_Certificates router for enrollment service
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..models import *
from ..services.get_certificates_service import Get_CertificatesService
from ..dependencies import get_database

router = APIRouter()


