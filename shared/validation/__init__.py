"""
Validation utilities for Course Creator Platform

This module provides validation services for:
- Professional email addresses
- Organization data validation
- User input sanitization
- Business rule enforcement
"""

from .email_validator import (
    ProfessionalEmailValidator,
    get_professional_email_validator,
    validate_professional_email,
    is_professional_email
)

__all__ = [
    'ProfessionalEmailValidator',
    'get_professional_email_validator', 
    'validate_professional_email',
    'is_professional_email'
]