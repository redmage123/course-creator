"""
API routers for user-management service
"""

from .register import router as register_router
from .login import router as login_router
from .refresh_token import router as refresh_token_router
from .logout import router as logout_router
from .get_profile import router as get_profile_router
from .update_profile import router as update_profile_router
from .list_users import router as list_users_router
from .change_password import router as change_password_router
from .verify_email import router as verify_email_router

__all__ = ['register_router', 'login_router', 'refresh_token_router', 'logout_router', 'get_profile_router', 'update_profile_router', 'list_users_router', 'change_password_router', 'verify_email_router']
