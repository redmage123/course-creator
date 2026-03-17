"""
API Key authentication middleware.

Reads X-API-Key header, validates it, and attaches org/user context to request.state.
Can be used as a FastAPI dependency alongside or instead of JWT auth.
"""

import logging
from typing import Optional

from fastapi import Header, HTTPException, Request, status

from api_keys.service import validate_api_key

logger = logging.getLogger(__name__)


async def get_api_key_context(
    request: Request,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> Optional[dict]:
    """
    FastAPI dependency — if X-API-Key header is present, validate it and return
    the key context dict (org_id, user_id, scopes).

    Returns None if no key provided (caller can decide whether to allow or reject).
    Raises 403 if key is present but invalid.
    """
    if not x_api_key:
        return None

    record = validate_api_key(x_api_key)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "invalid_api_key", "message": "API key is invalid or expired"},
        )

    return {
        "org_id": record["org_id"],
        "user_id": record["user_id"],
        "scopes": record["scopes"],
        "key_id": record["id"],
    }


async def require_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> dict:
    """
    FastAPI dependency — requires a valid X-API-Key header.
    Raises 401 if missing, 403 if invalid.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "missing_api_key", "message": "X-API-Key header required"},
        )
    ctx = await get_api_key_context(request, x_api_key)
    return ctx
