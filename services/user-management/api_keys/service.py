"""
API Key service — generation, validation, revocation.

Keys are generated as secrets.token_urlsafe(32) (URL-safe random string).
Only the bcrypt hash is stored; the plaintext is returned once on creation.
"""

import secrets
import logging
from datetime import datetime, timezone
from typing import Optional

import bcrypt

logger = logging.getLogger(__name__)

# In-memory store (replace with DB in production)
# Format: {key_hash: {"id": str, "org_id": str, "user_id": str, "name": str,
#                      "scopes": list, "is_active": bool, "created_at": datetime,
#                      "last_used_at": datetime|None, "expires_at": datetime|None}}
_keys: dict = {}
_keys_by_id: dict = {}  # id → key_hash (for lookup by ID)


def _generate_id() -> str:
    return secrets.token_hex(8)


def create_api_key(
    org_id: str,
    user_id: str,
    name: str,
    scopes: list = None,
    expires_at: Optional[datetime] = None,
) -> dict:
    """
    Generate a new API key.
    Returns a dict with 'key' (plaintext, shown ONCE) and metadata.
    """
    plaintext = secrets.token_urlsafe(32)
    key_hash = bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()
    key_id = _generate_id()

    record = {
        "id": key_id,
        "org_id": org_id,
        "user_id": user_id,
        "name": name,
        "scopes": scopes or ["read", "write"],
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used_at": None,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "key_hash": key_hash,
    }
    _keys[key_hash] = record
    _keys_by_id[key_id] = key_hash

    return {
        "id": key_id,
        "key": plaintext,  # only time plaintext is returned
        "org_id": org_id,
        "name": name,
        "scopes": record["scopes"],
        "created_at": record["created_at"],
        "expires_at": record["expires_at"],
    }


def list_api_keys(org_id: str) -> list:
    """Return all active API keys for an org (no plaintext)."""
    return [
        {k: v for k, v in rec.items() if k != "key_hash"}
        for rec in _keys.values()
        if rec["org_id"] == org_id
    ]


def revoke_api_key(key_id: str, org_id: str) -> bool:
    """Mark a key as inactive. Returns False if not found."""
    key_hash = _keys_by_id.get(key_id)
    if not key_hash:
        return False
    rec = _keys.get(key_hash)
    if not rec or rec["org_id"] != org_id:
        return False
    rec["is_active"] = False
    return True


def validate_api_key(plaintext: str) -> Optional[dict]:
    """
    Validate an API key from X-API-Key header.
    Returns the key record on success, None on failure.
    """
    for key_hash, rec in _keys.items():
        if not rec["is_active"]:
            continue
        try:
            if bcrypt.checkpw(plaintext.encode(), key_hash.encode()):
                # Update last_used_at
                rec["last_used_at"] = datetime.now(timezone.utc).isoformat()
                # Check expiry
                if rec["expires_at"]:
                    exp = datetime.fromisoformat(rec["expires_at"])
                    if datetime.now(timezone.utc) > exp:
                        rec["is_active"] = False
                        return None
                return rec
        except Exception:
            continue
    return None
