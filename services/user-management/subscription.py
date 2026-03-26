"""
Subscription Tier Management for Course Creator Platform

Defines tier features/limits, resolves tiers from Stripe, and builds
the subscription info payload returned by GET /users/subscription.
"""

import sys
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# ── Tier configuration ────────────────────────────────────────────────────────

TIER_CONFIG: Dict[str, Dict[str, Any]] = {
    "free": {
        "name": "Free",
        "features": {
            "course_creation": True,
            "ai_generation": True,
            "docker_labs": False,
            "analytics": "basic",
        },
        "limits": {
            "courses_max": 3,
            "ai_generation_max": 3,
            "lab_hours_max": 0,
        },
    },
    "pro": {
        "name": "Pro",
        "features": {
            "course_creation": True,
            "ai_generation": True,
            "docker_labs": True,
            "analytics": "full",
        },
        "limits": {
            "courses_max": None,   # unlimited
            "lab_hours_max": None, # unlimited
        },
    },
    "enterprise": {
        "name": "Enterprise",
        "features": {
            "course_creation": True,
            "ai_generation": True,
            "docker_labs": True,
            "analytics": "full+api",
        },
        "limits": {
            "courses_max": None,
            "lab_hours_max": None,
        },
    },
}

UPGRADE_URL = "https://techuni.ai/pricing"

# Product name substrings that map to tiers (case-insensitive match on Stripe product name)
_STRIPE_PRODUCT_TIER_MAP = {
    "enterprise": "enterprise",
    "pro": "pro",
}


def resolve_tier_from_stripe(email: str) -> str:
    """
    Check Stripe for an active subscription and return the matching tier slug.

    Falls back to 'free' on any error so the platform never hard-blocks a user
    due to a Stripe outage.
    """
    try:
        sys.path.insert(0, "/home/aielevate")
        from stripe_payments import check_subscription  # type: ignore
        result = check_subscription(email)

        if result.get("status") != "active":
            return "free"

        # `plan` is a Stripe product ID — look up the product name to map to a tier
        import stripe as stripe_lib
        product_id = result.get("plan", "")
        if not product_id or product_id == "unknown":
            return "free"

        try:
            product = stripe_lib.Product.retrieve(product_id)
            product_name = (product.name or "").lower()
        except Exception:
            # Can't retrieve product — treat as free
            return "free"

        for keyword, tier in _STRIPE_PRODUCT_TIER_MAP.items():
            if keyword in product_name:
                return tier

        return "free"

    except Exception as exc:
        logger.warning("Stripe tier lookup failed for %s: %s", email, exc)
        return "free"


async def get_usage_counts(user_id: str, db_pool) -> Dict[str, int]:
    """
    Return current usage metrics for the user.
    Queries course_creator schema; returns zeros on error.
    """
    counts = {"courses_created": 0, "lab_hours_used": 0}
    try:
        async with db_pool.acquire() as conn:
            # Count courses owned by this user
            course_count = await conn.fetchval(
                """SELECT COUNT(*) FROM course_creator.course_outlines
                   WHERE created_by = $1""",
                user_id
            )
            counts["courses_created"] = int(course_count or 0)

            # Sum lab hours from completed/active lab sessions
            lab_hours = await conn.fetchval(
                """SELECT COALESCE(SUM(
                       EXTRACT(EPOCH FROM (COALESCE(ended_at, NOW()) - started_at)) / 3600
                   ), 0)
                   FROM course_creator.lab_sessions
                   WHERE user_id = $1""",
                user_id
            )
            counts["lab_hours_used"] = round(float(lab_hours or 0), 2)
    except Exception as exc:
        logger.warning("Usage count query failed for user %s: %s", user_id, exc)
    return counts


def build_subscription_response(
    tier: str,
    usage: Dict[str, int],
) -> Dict[str, Any]:
    """Assemble the full subscription info dict."""
    cfg = TIER_CONFIG.get(tier, TIER_CONFIG["free"])
    limits = cfg["limits"]

    return {
        "tier": tier,
        "tier_name": cfg["name"],
        "features": cfg["features"],
        "usage": {
            "courses_created": usage["courses_created"],
            "courses_allowed": limits["courses_max"],
            "lab_hours_used": usage["lab_hours_used"],
            "lab_hours_allowed": limits["lab_hours_max"],
        },
        "upgrade_url": UPGRADE_URL if tier != "enterprise" else None,
    }


def check_feature_allowed(tier: str, feature: str) -> bool:
    """Return True if the given feature is permitted for the tier."""
    cfg = TIER_CONFIG.get(tier, TIER_CONFIG["free"])
    value = cfg["features"].get(feature)
    if isinstance(value, bool):
        return value
    # analytics tiers — any non-False value means some access is available
    return value is not None and value is not False


def build_limit_error(tier: str, limit_type: str, current: int, max_val: Optional[int]) -> Dict[str, Any]:
    """Build the 403 upgrade_required error body."""
    return {
        "error": "upgrade_required",
        "tier": tier,
        "limit": limit_type,
        "current": current,
        "max": max_val,
        "upgrade_url": UPGRADE_URL,
    }
