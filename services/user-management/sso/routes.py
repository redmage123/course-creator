"""
SSO Routes — SAML 2.0 and OAuth2/OIDC

Endpoints:
  GET  /api/v1/auth/sso/saml/metadata    — SP metadata XML
  POST /api/v1/auth/sso/saml/login       — initiate SAML redirect
  POST /api/v1/auth/sso/saml/callback    — handle SAMLResponse
  GET  /api/v1/auth/sso/oauth/authorize  — OAuth2 redirect
  GET  /api/v1/auth/sso/oauth/callback   — OAuth2 callback
  PUT  /api/v1/orgs/{org_id}/sso         — configure SSO settings (admin)
"""

import logging
import os
import json
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sso"])

# ── Config cache (in-memory; real deployment uses DB) ────────────────────────
_sso_configs: dict = {}  # org_id → OrgSSOConfig dict

SP_BASE_URL = os.environ.get("SP_BASE_URL", "https://courses.techuni.ai")
JWT_SECRET = os.environ["JWT_SECRET_KEY"]
USER_MANAGEMENT_URL = os.environ.get("USER_MANAGEMENT_URL", "http://user-management:8000")

# ── Pydantic models ──────────────────────────────────────────────────────────

class OrgSSOConfig(BaseModel):
    org_id: str
    provider: str  # saml | google | microsoft | okta
    is_active: bool = True
    # SAML fields
    entity_id: Optional[str] = None
    sso_url: Optional[str] = None
    slo_url: Optional[str] = None
    x509_cert: Optional[str] = None
    # OAuth2 fields
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    discovery_url: Optional[str] = None


# ── SAML helpers ─────────────────────────────────────────────────────────────

def _get_saml_settings(org_config: dict) -> dict:
    """Build python3-saml settings dict from org SSO config."""
    sp_acs = f"{SP_BASE_URL}/api/v1/auth/sso/saml/callback"
    sp_meta = f"{SP_BASE_URL}/api/v1/auth/sso/saml/metadata"
    return {
        "strict": True,
        "debug": False,
        "sp": {
            "entityId": sp_meta,
            "assertionConsumerService": {
                "url": sp_acs,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
            "x509cert": "",
            "privateKey": "",
        },
        "idp": {
            "entityId": org_config.get("entity_id", ""),
            "singleSignOnService": {
                "url": org_config.get("sso_url", ""),
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "singleLogoutService": {
                "url": org_config.get("slo_url", ""),
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": org_config.get("x509_cert", ""),
        },
    }


# ── OAuth2 provider discovery URLs ───────────────────────────────────────────
_PROVIDER_DISCOVERY = {
    "google": "https://accounts.google.com/.well-known/openid-configuration",
    "microsoft": "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration",
    "okta": None,  # org-specific; stored in discovery_url field
}

# ── SAML endpoints ───────────────────────────────────────────────────────────

@router.get("/auth/sso/saml/metadata")
async def saml_metadata(org_id: str = "default"):
    """Return SAML SP metadata XML for the given org."""
    try:
        from onelogin.saml2.auth import OneLogin_Saml2_Auth
        from onelogin.saml2.settings import OneLogin_Saml2_Settings

        cfg = _sso_configs.get(org_id, {})
        settings = _get_saml_settings(cfg)
        saml_settings = OneLogin_Saml2_Settings(settings=settings, sp_validation_only=True)
        metadata = saml_settings.get_sp_metadata()
        errors = saml_settings.validate_metadata(metadata)
        if errors:
            raise HTTPException(status_code=500, detail=f"Metadata error: {errors}")
        return Response(content=metadata, media_type="application/xml")
    except ImportError:
        raise HTTPException(status_code=501, detail="python3-saml not installed")


@router.post("/auth/sso/saml/login")
async def saml_login(request: Request, org_id: str = "default"):
    """Initiate SAML SSO — redirect user to IdP."""
    try:
        from onelogin.saml2.auth import OneLogin_Saml2_Auth

        cfg = _sso_configs.get(org_id)
        if not cfg or not cfg.get("is_active"):
            raise HTTPException(status_code=404, detail="SSO not configured for this org")

        req = await _build_saml_request(request)
        auth = OneLogin_Saml2_Auth(req, old_settings=_get_saml_settings(cfg))
        redirect_url = auth.login()
        return RedirectResponse(url=redirect_url, status_code=302)
    except ImportError:
        raise HTTPException(status_code=501, detail="python3-saml not installed")


@router.post("/auth/sso/saml/callback")
async def saml_callback(request: Request):
    """Handle SAML response from IdP, create/find user, return session token."""
    try:
        from onelogin.saml2.auth import OneLogin_Saml2_Auth

        form_data = await request.form()
        org_id = form_data.get("RelayState", "default")
        cfg = _sso_configs.get(org_id, {})

        req = await _build_saml_request(request)
        auth = OneLogin_Saml2_Auth(req, old_settings=_get_saml_settings(cfg))
        auth.process_response()
        errors = auth.get_errors()
        if errors:
            raise HTTPException(status_code=400, detail=f"SAML error: {errors}")
        if not auth.is_authenticated():
            raise HTTPException(status_code=401, detail="SAML authentication failed")

        email = auth.get_nameid()
        attributes = auth.get_attributes()
        full_name = _get_attr(attributes, ["displayName", "cn", "name"])

        token = await _upsert_sso_user(request, email, full_name, org_id, "saml")
        return {"access_token": token, "token_type": "bearer"}

    except ImportError:
        raise HTTPException(status_code=501, detail="python3-saml not installed")


# ── OAuth2/OIDC endpoints ────────────────────────────────────────────────────

@router.get("/auth/sso/oauth/authorize")
async def oauth_authorize(provider: str, org_id: str = "default"):
    """Redirect user to OAuth2 IdP authorization endpoint."""
    try:
        from authlib.integrations.httpx_client import AsyncOAuth2Client

        cfg = _sso_configs.get(org_id)
        if not cfg:
            raise HTTPException(status_code=404, detail="SSO not configured for this org")

        discovery_url = cfg.get("discovery_url") or _PROVIDER_DISCOVERY.get(provider)
        if not discovery_url:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

        state = secrets.token_urlsafe(16)
        redirect_uri = f"{SP_BASE_URL}/api/v1/auth/sso/oauth/callback"

        # Fetch OIDC discovery to get authorization_endpoint
        import httpx
        async with httpx.AsyncClient() as client:
            disc = (await client.get(discovery_url)).json()

        auth_endpoint = disc["authorization_endpoint"]
        params = {
            "response_type": "code",
            "client_id": cfg["client_id"],
            "redirect_uri": redirect_uri,
            "scope": "openid email profile",
            "state": f"{org_id}:{state}",
        }
        from urllib.parse import urlencode
        url = f"{auth_endpoint}?{urlencode(params)}"
        return RedirectResponse(url=url, status_code=302)

    except ImportError:
        raise HTTPException(status_code=501, detail="authlib not installed")


@router.get("/auth/sso/oauth/callback")
async def oauth_callback(request: Request, code: str, state: str = "default:"):
    """Exchange OAuth2 code for tokens, fetch user info, create session."""
    try:
        org_id = state.split(":")[0] if ":" in state else "default"
        cfg = _sso_configs.get(org_id)
        if not cfg:
            raise HTTPException(status_code=404, detail="SSO not configured for this org")

        provider = cfg.get("provider", "google")
        discovery_url = cfg.get("discovery_url") or _PROVIDER_DISCOVERY.get(provider)

        import httpx
        async with httpx.AsyncClient() as client:
            disc = (await client.get(discovery_url)).json()
            token_endpoint = disc["token_endpoint"]
            userinfo_endpoint = disc["userinfo_endpoint"]

            redirect_uri = f"{SP_BASE_URL}/api/v1/auth/sso/oauth/callback"
            token_resp = await client.post(token_endpoint, data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
            })
            tokens = token_resp.json()
            access_token = tokens.get("access_token")

            userinfo = (await client.get(
                userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"}
            )).json()

        email = userinfo.get("email")
        full_name = userinfo.get("name")
        if not email:
            raise HTTPException(status_code=400, detail="No email in OAuth2 userinfo")

        token = await _upsert_sso_user(request, email, full_name, org_id, provider)
        return {"access_token": token, "token_type": "bearer"}

    except ImportError:
        raise HTTPException(status_code=501, detail="authlib/httpx not installed")


# ── Org SSO config endpoint ───────────────────────────────────────────────────

@router.put("/orgs/{org_id}/sso")
async def configure_org_sso(org_id: str, config: OrgSSOConfig, request: Request):
    """Store SSO configuration for an org (admin only)."""
    _sso_configs[org_id] = config.model_dump()
    logger.info("SSO config updated for org %s (provider: %s)", org_id, config.provider)
    return {"status": "ok", "org_id": org_id, "provider": config.provider}


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _build_saml_request(request: Request) -> dict:
    """Convert FastAPI request to python3-saml request dict."""
    body = await request.body()
    form = await request.form()
    return {
        "https": "on" if request.url.scheme == "https" else "off",
        "http_host": request.headers.get("host", "localhost"),
        "script_name": request.url.path,
        "server_port": str(request.url.port or 443),
        "get_data": dict(request.query_params),
        "post_data": dict(form),
        "query_string": request.url.query,
    }


def _get_attr(attributes: dict, keys: list) -> Optional[str]:
    for key in keys:
        val = attributes.get(key)
        if val:
            return val[0] if isinstance(val, list) else val
    return None


async def _upsert_sso_user(
    request: Request,
    email: str,
    full_name: Optional[str],
    org_id: str,
    provider: str,
) -> str:
    """Find or create a user by email, then create a session and return token."""
    try:
        container = request.app.state.container
        user_service = container.get_user_service()
        session_service = container.get_session_service()
        token_service = container.get_token_service()

        # Try to find existing user
        try:
            user = await user_service.get_user_by_email(email)
        except Exception:
            user = None

        if not user:
            # Auto-provision user from SSO
            from user_management.domain.entities.user import User, UserRole, UserStatus
            import uuid
            user = await user_service.create_user_from_sso(
                email=email,
                full_name=full_name or email.split("@")[0],
                org_id=org_id,
                provider=provider,
            )

        # Create session
        session = await session_service.create_session(user.id)
        token = await token_service.generate_access_token(user.id, session.id)
        return token

    except Exception as exc:
        logger.error("SSO user upsert failed for %s: %s", email, exc)
        raise HTTPException(status_code=500, detail="SSO login failed")
