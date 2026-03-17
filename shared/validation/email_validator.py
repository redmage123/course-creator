"""
Professional Email Validation for Course Creator Platform

BUSINESS REQUIREMENT:
The Course Creator Platform requires professional email addresses for organization 
administrators and instructors to ensure legitimate business use and prevent abuse
from personal email providers.

TECHNICAL IMPLEMENTATION:
This module provides email validation that rejects common personal email providers
(Gmail, Yahoo, Hotmail, etc.) while allowing professional domain emails from
educational institutions, companies, and organizations.

SECURITY CONSIDERATIONS:
- Prevents spam registrations from throwaway email providers
- Ensures organizational accountability through business email addresses
- Maintains whitelist of legitimate educational domains (.edu, .ac.uk, etc.)
- Validates email format and domain authenticity
"""

import re
from typing import Set, List, Optional
from email_validator import validate_email, EmailNotValidError


class ProfessionalEmailValidator:
    """
    Professional Email Validation Service
    
    Validates email addresses to ensure they are from professional domains,
    not personal email providers like Gmail, Yahoo, Hotmail, etc.
    
    This enforces business requirements for organizational accountability
    and prevents misuse through personal email registrations.
    """
    
    # Personal email providers that are NOT allowed for organization registration
    BLOCKED_PERSONAL_DOMAINS: Set[str] = {
        # Google services
        'gmail.com', 'googlemail.com',
        
        # Microsoft services  
        'hotmail.com', 'outlook.com', 'live.com', 'msn.com',
        
        # Yahoo services
        'yahoo.com', 'yahoo.co.uk', 'yahoo.ca', 'yahoo.co.in', 'ymail.com',
        
        # Apple services
        'icloud.com', 'me.com', 'mac.com',
        
        # Other common personal providers
        'aol.com', 'protonmail.com', 'tutanota.com',
        'mail.com', 'gmx.com', 'web.de',
        
        # Temporary/disposable email providers
        '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
        'mailinator.com', 'throwaway.email'
    }
    
    # Educational domains that are explicitly allowed
    ALLOWED_EDUCATIONAL_DOMAINS: Set[str] = {
        '.edu', '.ac.uk', '.ac.in', '.edu.au', '.edu.ca',
        '.university', '.college', '.school'
    }
    
    def __init__(self):
        """Initialize professional email validator with business rules"""
        self._logger = None
        try:
            import logging
            self._logger = logging.getLogger(__name__)
        except ImportError:
            pass
    
    def validate_professional_email(self, email: str) -> dict:
        """
        Validate that an email address is from a professional domain.
        
        Args:
            email (str): Email address to validate
            
        Returns:
            dict: Validation result with is_valid, domain, and reason
            
        Business Rules:
            - Must be valid email format
            - Domain must not be in blocked personal providers list
            - Educational domains (.edu, .ac.uk) are always allowed
            - Corporate domains are allowed by default unless blocked
        """
        result = {
            'is_valid': False,
            'email': email.lower().strip(),
            'domain': None,
            'reason': None,
            'is_educational': False,
            'is_corporate': False
        }
        
        try:
            # Basic email format validation
            validated_email = validate_email(email)
            normalized_email = validated_email.email.lower()
            domain = validated_email.domain.lower()
            
            result['email'] = normalized_email
            result['domain'] = domain
            
            # Check if domain is blocked personal provider
            if domain in self.BLOCKED_PERSONAL_DOMAINS:
                result['reason'] = f"Personal email provider '{domain}' not allowed for organization registration"
                return result
            
            # Check if domain is educational (always allowed)
            if self._is_educational_domain(domain):
                result['is_valid'] = True
                result['is_educational'] = True
                result['reason'] = f"Educational domain '{domain}' accepted"
                return result
            
            # Check if domain appears to be corporate/professional
            if self._is_professional_domain(domain):
                result['is_valid'] = True
                result['is_corporate'] = True
                result['reason'] = f"Professional domain '{domain}' accepted"
                return result
            
            # Domain not recognized as professional
            result['reason'] = f"Domain '{domain}' does not appear to be a professional business domain"
            return result
            
        except EmailNotValidError as e:
            result['reason'] = f"Invalid email format: {str(e)}"
            return result
        except Exception as e:
            result['reason'] = f"Email validation error: {str(e)}"
            return result
    
    def _is_educational_domain(self, domain: str) -> bool:
        """Check if domain is from an educational institution"""
        for edu_suffix in self.ALLOWED_EDUCATIONAL_DOMAINS:
            if domain.endswith(edu_suffix):
                return True
        return False
    
    def _is_professional_domain(self, domain: str) -> bool:
        """
        Check if domain appears to be professional/corporate.
        
        Professional domains typically:
        - Have a proper TLD (.com, .org, .net, .co.uk, etc.)
        - Are not in the blocked personal providers list
        - Contain business-like domain names
        """
        # Valid professional TLDs
        professional_tlds = {
            '.com', '.org', '.net', '.biz', '.info',
            '.co.uk', '.co.in', '.co.au', '.co.ca',
            '.gov', '.mil', '.int'
        }
        
        # Check if domain has professional TLD
        for tld in professional_tlds:
            if domain.endswith(tld):
                return True
        
        # Check for country-specific business domains
        if re.match(r'.*\.(com?|org|net|gov)\.[a-z]{2}$', domain):
            return True
        
        return False
    
    def get_blocked_domains(self) -> List[str]:
        """Get list of blocked personal email domains"""
        return sorted(list(self.BLOCKED_PERSONAL_DOMAINS))
    
    def is_domain_blocked(self, domain: str) -> bool:
        """Check if a specific domain is blocked"""
        return domain.lower() in self.BLOCKED_PERSONAL_DOMAINS
    
    def validate_instructor_email(self, email: str, organization_domain: Optional[str] = None) -> dict:
        """
        Validate instructor email with additional organization context.
        
        Args:
            email (str): Instructor email to validate
            organization_domain (str, optional): Organization's primary domain
            
        Returns:
            dict: Enhanced validation result for instructor registration
        """
        result = self.validate_professional_email(email)
        
        if organization_domain and result['is_valid']:
            # Check if instructor email matches organization domain
            if result['domain'] == organization_domain.lower():
                result['matches_organization'] = True
                result['reason'] += f" and matches organization domain"
            else:
                result['matches_organization'] = False
        
        return result


# Global validator instance for shared use
_email_validator = None

def get_professional_email_validator() -> ProfessionalEmailValidator:
    """Get shared professional email validator instance"""
    global _email_validator
    if _email_validator is None:
        _email_validator = ProfessionalEmailValidator()
    return _email_validator


def validate_professional_email(email: str) -> dict:
    """Convenience function for professional email validation"""
    validator = get_professional_email_validator()
    return validator.validate_professional_email(email)


def is_professional_email(email: str) -> bool:
    """Quick check if email is from professional domain"""
    result = validate_professional_email(email)
    return result['is_valid']