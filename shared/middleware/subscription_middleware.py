"""
Subscription Tier Middleware for Course Creator Platform

Provides FastAPI dependencies that other services (course-management,
ai-course-generator, lab-environment, analytics) can import to gate
feature access by subscription tier.

Usage in any FastAPI service:
    from shared.middleware.subscription_middleware import require_feature

    @app.post("/courses")
    async def create_course(
        _: None = Depends(require_feature("course_creation")),
        ...
    ):
        ...

The middleware calls the user-management service's /users/subscription
endpoint so tier logic stays in one place.
"""

import logging
import os
from typing import Optional

import httpx
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

logger = logging.getLogger(__name__)

USER_MANAGEMENT_URL = os.environ.get(
    "USER_MANAGEMENT_URL", "http://user-management:8000"
)
JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
UPGRADE_URL = "https://techuni.ai/pricing"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

# ── Tier / feature config (mirrors subscription.py — kept in sync) ────────────

_TIER_CONFIG = {
    "free": {
        "course_creation": True,
        "ai_generation": False,
        "docker_labs": False,
        "analytics": "basic",
        "courses_max": 1,
    },
    "pro": {
        "course_creation": True,
        "ai_generation": True,
        "docker_labs": True,
        "analytics": "full",
        "courses_max": None,
    },
    "enterprise": {
        "course_creation": True,
        "ai_generation": True,
        "docker_labs": True,
        "analytics": "full+api",
        "courses_max": None,
    },
}


def _decode_user_id(token: str) -> Optional[str]:
    """Decode JWT and return user_id (sub claim), or None on failure."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub") or payload.get("user_id")
    except Exception:
        return None


async def _fetch_subscription(token: str) -> dict:
    """
    Call user-management /users/subscription and return the response dict.
    Returns a 'free' fallback on network/auth error so other services
    remain available even if user-management is temporarily down.
    """
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                f"{USER_MANAGEMENT_URL}/users/subscription",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as exc:
        logger.warning("Could not reach user-management for tier check: %s", exc)
    return {"tier": "free", "usage": {"courses_created": 0, "courses_allowed": 1}}


def require_feature(feature: str):
    """
    Return a FastAPI dependency that blocks the request with 403 if the
    user's tier does not include `feature`.

    Supported feature strings:
        course_creation  — create new courses
        ai_generation    — AI-powered course generation
        docker_labs      — Docker lab environments
        analytics        — analytics access (any level)
    """
    async def _check(token: str = Depends(oauth2_scheme)):
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        sub_info = await _fetch_subscription(token)
        tier = sub_info.get("tier", "free")
        cfg = _TIER_CONFIG.get(tier, _TIER_CONFIG["free"])
        feature_value = cfg.get(feature)

        # For analytics, any non-False value means some access
        allowed = bool(feature_value) if not isinstance(feature_value, str) else True

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "upgrade_required",
                    "tier": tier,
                    "limit": feature,
                    "current": None,
                    "max": None,
                    "upgrade_url": UPGRADE_URL,
                },
            )

        # For course_creation, also enforce the count limit
        if feature == "course_creation":
            max_courses = cfg.get("courses_max")
            if max_courses is not None:
                usage = sub_info.get("usage", {})
                current = usage.get("courses_created", 0)
                if current >= max_courses:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={
                            "error": "upgrade_required",
                            "tier": tier,
                            "limit": "courses",
                            "current": current,
                            "max": max_courses,
                            "upgrade_url": UPGRADE_URL,
                        },
                    )

    return Depends(_check)


def require_analytics_api():
    """
    Dependency that allows analytics API access only for 'enterprise' tier.
    """
    async def _check(token: str = Depends(oauth2_scheme)):
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        sub_info = await _fetch_subscription(token)
        tier = sub_info.get("tier", "free")
        if tier != "enterprise":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "upgrade_required",
                    "tier": tier,
                    "limit": "analytics_api",
                    "current": None,
                    "max": None,
                    "upgrade_url": UPGRADE_URL,
                },
            )

    return Depends(_check)
