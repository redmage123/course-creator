"""
LTI 1.3 Tool Provider endpoints.

GET  /api/v1/lti/config     — LTI 1.3 tool configuration JSON
POST /api/v1/lti/launch     — LTI launch handler (id_token validation)
POST /api/v1/lti/grades     — Grade passback (AGS 2.0)
"""

import logging
import os
import json
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["lti"])

SP_BASE_URL = os.environ.get("SP_BASE_URL", "https://courses.techuni.ai")
LTI_CLIENT_ID = os.environ.get("LTI_CLIENT_ID", "course-creator-lti")

# In-memory registration store: platform_id → registration config
_lti_registrations: dict = {}


# ── LTI Tool Config ───────────────────────────────────────────────────────────

@router.get("/lti/config")
async def lti_config():
    """
    Return LTI 1.3 tool configuration JSON.
    Used by LMS platforms (Moodle, Canvas, Blackboard) to configure this tool.
    """
    return {
        "title": "Course Creator",
        "description": "AI-powered course creation and delivery platform",
        "oidc_initiation_url": f"{SP_BASE_URL}/api/v1/lti/launch",
        "target_link_uri": f"{SP_BASE_URL}/api/v1/lti/launch",
        "scopes": [
            "openid",
            "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
            "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
            "https://purl.imsglobal.org/spec/lti-ags/scope/score",
        ],
        "extensions": [
            {
                "platform": "canvas.instructure.com",
                "settings": {
                    "platform": "canvas.instructure.com",
                    "placements": [
                        {
                            "placement": "course_navigation",
                            "message_type": "LtiResourceLinkRequest",
                            "target_link_uri": f"{SP_BASE_URL}/api/v1/lti/launch",
                        }
                    ],
                },
            }
        ],
        "public_jwk_url": f"{SP_BASE_URL}/api/v1/lti/jwks",
        "custom_fields": {},
        "redirect_uris": [f"{SP_BASE_URL}/api/v1/lti/launch"],
    }


# ── LTI Launch ────────────────────────────────────────────────────────────────

@router.post("/lti/launch")
async def lti_launch(
    request: Request,
    id_token: Optional[str] = Form(default=None),
    state: Optional[str] = Form(default=None),
):
    """
    Handle LTI 1.3 Resource Link Request launch.

    The platform sends an id_token (JWT) signed with its private key.
    We validate it and provision/find the user, then redirect to the course.
    """
    if not id_token:
        raise HTTPException(status_code=400, detail="Missing id_token in LTI launch")

    try:
        from pylti1p3.contrib.fastapi import FastAPIMessageLaunch, FastAPIRequest
        from pylti1p3.tool_config import ToolConfDict
        from pylti1p3.exception import LtiException
    except ImportError:
        # Fallback: decode JWT without verification for dev/demo
        return await _lti_launch_fallback(request, id_token)

    try:
        tool_conf = _build_tool_conf()
        fastapi_request = FastAPIRequest(request, {"id_token": id_token, "state": state or ""})
        message_launch = FastAPIMessageLaunch(fastapi_request, tool_conf)
        launch_data = message_launch.get_launch_data()

        email = launch_data.get("email") or launch_data.get(
            "https://purl.imsglobal.org/spec/lti/claim/ext", {}
        ).get("user_username", "")
        name = launch_data.get("name", "")
        platform_id = launch_data.get("iss", "unknown")
        course_id = launch_data.get(
            "https://purl.imsglobal.org/spec/lti/claim/resource_link", {}
        ).get("id", "")

        if not email:
            raise HTTPException(status_code=400, detail="No email in LTI launch data")

        token = await _provision_lti_user(request, email, name, platform_id)
        redirect_url = f"{SP_BASE_URL}/courses/{course_id}?token={token}"
        return RedirectResponse(url=redirect_url, status_code=302)

    except Exception as exc:
        logger.error("LTI launch failed: %s", exc)
        raise HTTPException(status_code=400, detail=f"LTI launch error: {exc}")


async def _lti_launch_fallback(request: Request, id_token: str):
    """Dev fallback: decode id_token JWT without signature verification."""
    import jwt as pyjwt
    try:
        payload = pyjwt.decode(id_token, options={"verify_signature": False})
        email = payload.get("email", "lti_user@unknown.edu")
        name = payload.get("name", "LTI User")
        platform_id = payload.get("iss", "lms")
        token = await _provision_lti_user(request, email, name, platform_id)
        course_id = payload.get("https://purl.imsglobal.org/spec/lti/claim/resource_link", {}).get("id", "")
        return RedirectResponse(url=f"{SP_BASE_URL}/courses/{course_id}?token={token}", status_code=302)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"LTI fallback error: {exc}")


# ── Grade Passback ────────────────────────────────────────────────────────────

class GradePassback(BaseModel):
    launch_id: str
    user_id: str
    score: float  # 0.0 – 1.0
    activity_progress: str = "Completed"
    grading_progress: str = "FullyGraded"


@router.post("/lti/grades")
async def lti_grades(body: GradePassback, request: Request):
    """
    Accept grade passback from the platform (AGS 2.0).
    Stores the grade and optionally forwards it to the LMS lineitem.
    """
    logger.info(
        "LTI grade passback: user=%s score=%.2f launch=%s",
        body.user_id, body.score, body.launch_id,
    )
    # TODO: persist grade and call AGS lineitem score endpoint
    return {
        "status": "accepted",
        "user_id": body.user_id,
        "score": body.score,
    }


# ── JWKS endpoint (for platform JWT verification) ─────────────────────────────

@router.get("/lti/jwks")
async def lti_jwks():
    """Return public JWKS for platforms to verify our JWTs."""
    return {"keys": []}  # TODO: return actual public key when signing is configured


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_tool_conf():
    """Build PyLTI1p3 ToolConfDict from registered platforms."""
    from pylti1p3.tool_config import ToolConfDict
    registrations = {}
    for platform_id, reg in _lti_registrations.items():
        registrations[platform_id] = {
            reg["client_id"]: {
                "default": True,
                "client_id": reg["client_id"],
                "auth_login_url": reg["auth_login_url"],
                "auth_token_url": reg["auth_token_url"],
                "key_set_url": reg["key_set_url"],
                "key_set": None,
                "private_key_file": reg.get("private_key_file", ""),
                "public_key_file": reg.get("public_key_file", ""),
                "deployment_ids": reg.get("deployment_ids", ["1"]),
            }
        }
    return ToolConfDict(registrations)


async def _provision_lti_user(
    request: Request,
    email: str,
    name: str,
    platform_id: str,
) -> str:
    """Find or create a user from LTI launch data, return session token."""
    try:
        container = request.app.state.container
        user_service = container.get_user_service()
        session_service = container.get_session_service()
        token_service = container.get_token_service()

        try:
            user = await user_service.get_user_by_email(email)
        except Exception:
            user = None

        if not user:
            user = await user_service.create_user_from_sso(
                email=email,
                full_name=name or email.split("@")[0],
                org_id="lti",
                provider=f"lti:{platform_id}",
            )

        session = await session_service.create_session(user.id)
        token = await token_service.generate_access_token(user.id, session.id)
        return token

    except Exception as exc:
        logger.error("LTI user provision failed for %s: %s", email, exc)
        raise HTTPException(status_code=500, detail="LTI user provisioning failed")
