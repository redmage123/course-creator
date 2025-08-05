"""
Security Headers Middleware for Course Creator Platform

SECURITY PROTECTION:
Implements essential security headers to protect against common web
vulnerabilities including XSS, clickjacking, MIME sniffing, and more.

HEADERS IMPLEMENTED:
- Content Security Policy (CSP)
- X-Frame-Options (Clickjacking protection)
- X-Content-Type-Options (MIME sniffing protection) 
- X-XSS-Protection (XSS filtering)
- Strict-Transport-Security (HTTPS enforcement)
- Referrer-Policy (Information leakage protection)
- Permissions-Policy (Feature access control)

CONFIGURATION:
Headers are configurable per environment (development, staging, production)
with appropriate policies for each deployment context.
"""

from typing import Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security headers middleware for web application protection
    
    Adds essential security headers to all HTTP responses to protect
    against common web vulnerabilities and attacks.
    """
    
    def __init__(self, app, config: Dict[str, Any]):
        super().__init__(app)
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Determine environment
        self.environment = config.get('environment', 'development')
        self.is_development = self.environment == 'development'
        
        # Security headers configuration
        self.security_headers = self._get_security_headers_config()
    
    def _get_security_headers_config(self) -> Dict[str, str]:
        """Get security headers configuration based on environment"""
        
        # Base security headers for all environments
        headers = {
            # Prevent MIME type sniffing
            'X-Content-Type-Options': 'nosniff',
            
            # Control referrer information
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            
            # Basic XSS protection (legacy, but still useful)
            'X-XSS-Protection': '1; mode=block',
            
            # Feature policy restrictions
            'Permissions-Policy': (
                'camera=(), microphone=(), geolocation=(), '
                'payment=(), usb=(), magnetometer=(), gyroscope=()'
            )
        }
        
        # Environment-specific headers
        if self.is_development:
            # Development - Relaxed policies for debugging
            headers.update({
                'X-Frame-Options': 'SAMEORIGIN',
                'Content-Security-Policy': (
                    "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:; "
                    "connect-src 'self' ws: wss: http: https:; "
                    "img-src 'self' data: blob: https:; "
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "
                    "style-src 'self' 'unsafe-inline' https:; "
                    "font-src 'self' data: https:;"
                )
            })
        else:
            # Production - Strict policies for security
            headers.update({
                # Prevent clickjacking
                'X-Frame-Options': 'DENY',
                
                # Enforce HTTPS (only in production)
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
                
                # Strict Content Security Policy
                'Content-Security-Policy': (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: blob:; "
                    "font-src 'self' data:; "
                    "connect-src 'self'; "
                    "object-src 'none'; "
                    "frame-ancestors 'none'; "
                    "base-uri 'self'; "
                    "form-action 'self';"
                )
            })
        
        return headers
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers to all responses"""
        
        # Process the request
        response = await call_next(request)
        
        # Skip adding headers to WebSocket upgrades
        if response.status_code == 101:
            return response
        
        # Add security headers
        for header_name, header_value in self.security_headers.items():
            # Don't override existing headers
            if header_name not in response.headers:
                response.headers[header_name] = header_value
        
        # Add security-specific headers based on content type
        content_type = response.headers.get('content-type', '')
        
        # For HTML responses, add additional protection
        if 'text/html' in content_type:
            if 'X-Frame-Options' not in response.headers:
                response.headers['X-Frame-Options'] = 'DENY' if not self.is_development else 'SAMEORIGIN'
        
        # For API responses, add API-specific headers
        elif 'application/json' in content_type:
            if 'Cache-Control' not in response.headers:
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            if 'Pragma' not in response.headers:
                response.headers['Pragma'] = 'no-cache'
        
        # For file downloads, add download-specific headers
        elif 'application/octet-stream' in content_type or 'attachment' in response.headers.get('content-disposition', ''):
            if 'X-Content-Type-Options' not in response.headers:
                response.headers['X-Content-Type-Options'] = 'nosniff'
        
        return response


def setup_security_headers(app, config: Dict[str, Any]):
    """Set up security headers middleware"""
    if config.get('security', {}).get('headers', {}).get('enabled', True):
        app.add_middleware(SecurityHeadersMiddleware, config=config)
        logging.getLogger(__name__).info("Security headers middleware enabled")
    else:
        logging.getLogger(__name__).info("Security headers middleware disabled by configuration")