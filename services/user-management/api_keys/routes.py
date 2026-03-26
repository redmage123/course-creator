"""
API Key management endpoints.

POST   /api/v1/keys            — generate a new API key
GET    /api/v1/keys            — list org API keys
DELETE /api/v1/keys/{key_id}   — revoke a key
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from api_keys.service import create_api_key, list_api_keys, revoke_api_key

logger = logging.getLogger(__name__)

router = APIRouter(tags=["api-keys"])


# ── Request/Response models ───────────────────────────────────────────────────

class CreateKeyRequest(BaseModel):
    name: str
    scopes: List[str] = ["read", "write"]
    expires_at: Optional[datetime] = None


class KeyResponse(BaseModel):
    id: str
    org_id: str
    name: str
    scopes: List[str]
    created_at: str
    last_used_at: Optional[str] = None
    expires_at: Optional[str] = None
    is_active: bool = True


class CreateKeyResponse(KeyResponse):
    key: str  # plaintext — shown ONCE


# ── Endpoints ─────────────────────────────────────────────────────────────────

def _get_current_user_from_request(request: Request) -> dict:
    """Extract user context from JWT (already validated by auth middleware)."""
    import sys
    if '/app/shared' not in sys.path:
        sys.path.append('/app/shared')
    try:
        import jwt
        from fastapi.security.utils import get_authorization_scheme_param
        auth = request.headers.get("Authorization", "")
        scheme, token = get_authorization_scheme_param(auth)
        if scheme.lower() != "bearer" or not token:
            raise ValueError("No bearer token")
        payload = jwt.decode(token, options={"verify_signature": False})
        return {
            "user_id": payload.get("user_id") or payload.get("sub"),
            "org_id": payload.get("org_id") or "default",
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication required")


@router.post("/keys", response_model=CreateKeyResponse, status_code=201)
async def generate_key(body: CreateKeyRequest, request: Request):
    """Generate a new API key for the authenticated user's org."""
    ctx = _get_current_user_from_request(request)
    result = create_api_key(
        org_id=ctx["org_id"],
        user_id=ctx["user_id"],
        name=body.name,
        scopes=body.scopes,
        expires_at=body.expires_at,
    )
    return result


@router.get("/keys", response_model=List[KeyResponse])
async def list_keys(request: Request):
    """List all API keys for the authenticated user's org."""
    ctx = _get_current_user_from_request(request)
    return list_api_keys(ctx["org_id"])


@router.delete("/keys/{key_id}", status_code=204)
async def revoke_key(key_id: str, request: Request):
    """Revoke (deactivate) an API key."""
    ctx = _get_current_user_from_request(request)
    ok = revoke_api_key(key_id, ctx["org_id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found")
