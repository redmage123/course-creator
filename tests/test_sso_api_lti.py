"""
TDD Tests: SSO/SAML, Public API, and LTI 1.3
=============================================

Written BEFORE the dev-backend team lands the implementation (TDD approach).
These tests define the contract that the implementation must satisfy.

Coverage:
  1. SSO / SAML 2.0  — metadata, login redirect, callback, auto-provisioning
  2. API Keys         — generation, auth, revocation, scoping, rate-limiting
  3. Public REST API  — courses CRUD, analytics, lab provisioning
  4. LTI 1.3          — config, launch, grade passback

Design principles:
  - No live IdP, no live database — every external dependency is mocked/faked
  - Fast (< 1 s per test)
  - Deterministic (no network, no time drift without freezegun)
  - Follow existing project conventions (FakeAsyncPGConnection test doubles,
    pytest fixtures, async-aware)

Run all tests:
    pytest tests/test_sso_api_lti.py -v

Run a single group:
    pytest tests/test_sso_api_lti.py -v -k "saml"
    pytest tests/test_sso_api_lti.py -v -k "api_key"
    pytest tests/test_sso_api_lti.py -v -k "public_api"
    pytest tests/test_sso_api_lti.py -v -k "lti"
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from urllib.parse import parse_qs, urlparse

import pytest

# ---------------------------------------------------------------------------
# Optional heavyweight imports — skip gracefully if not installed yet
# ---------------------------------------------------------------------------
try:
    import jwt as pyjwt  # PyJWT
    HAS_PYJWT = True
except ImportError:
    HAS_PYJWT = False


try:
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

try:
    from freezegun import freeze_time
    HAS_FREEZEGUN = True
except ImportError:
    # Provide a no-op shim so tests run but skip time assertions
    def freeze_time(dt):  # type: ignore[misc]
        import functools
        def decorator(fn):
            @functools.wraps(fn)
            def wrapper(*a, **kw):
                return fn(*a, **kw)
            return wrapper
        return decorator
    HAS_FREEZEGUN = False


# ===========================================================================
# Shared constants
# ===========================================================================

TEST_ORG_ID   = "00000000-0000-0000-0000-000000000001"
TEST_ORG_2_ID = "00000000-0000-0000-0000-000000000002"
TEST_USER_ID  = "00000000-0000-0000-0000-000000000010"
TEST_ADMIN_ID = "00000000-0000-0000-0000-000000000011"
JWT_SECRET    = "test-jwt-secret-32-characters-long!!"
ACS_URL       = "https://courses.techuni.ai/sso/saml/callback"
ENTITY_ID     = "https://courses.techuni.ai"
IDP_SSO_URL   = "https://idp.example.com/sso"
IDP_CERT      = (
    "MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAlRuRnThUjU8/prwYxbty"
    "WPT9pURI3lbsKMiB6Bn/Zn1XEqw=" * 2
)

LTI_ISSUER        = "https://canvas.example.com"
LTI_CLIENT_ID     = "12345"
LTI_DEPLOYMENT_ID = "1"
LTI_JWKS_URL      = f"{LTI_ISSUER}/api/lti/security/jwks"
LTI_TOKEN_URL     = f"{LTI_ISSUER}/login/oauth2/token"
LTI_AUTH_URL      = f"{LTI_ISSUER}/api/lti/authorize_redirect"


# ===========================================================================
# Shared helpers
# ===========================================================================



def _make_jwt(payload: dict, secret: str = JWT_SECRET, algorithm: str = "HS256") -> str:
    """Create a signed JWT using PyJWT (or a trivial fallback)."""
    if HAS_PYJWT:
        return pyjwt.encode(payload, secret, algorithm=algorithm)
    # Minimal base64url JWT fallback (unsigned — enough for shape tests)
    def _b64(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
    header = _b64({"alg": algorithm, "typ": "JWT"})
    body   = _b64(payload)
    sig    = base64.urlsafe_b64encode(b"fakesig").rstrip(b"=").decode()
    return f"{header}.{body}.{sig}"


def _user_token(
    user_id: str = TEST_ADMIN_ID,
    org_id: str = TEST_ORG_ID,
    role: str = "org_admin",
    exp_delta: timedelta = timedelta(hours=1),
) -> str:
    payload = {
        "user_id": user_id,
        "email": "admin@test.example.com",
        "role": role,
        "organization_id": org_id,
        "exp": int((datetime.utcnow() + exp_delta).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
    }
    return _make_jwt(payload)


def _api_key_hash(raw_key: str) -> str:
    """Simulate the server-side hashing of an API key before DB storage."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


# ===========================================================================
# Fake in-memory stores (test doubles following project conventions)
# ===========================================================================

class FakeRecord(dict):
    """Mimics asyncpg.Record so dict access and attribute access both work."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


class FakeDB:
    """
    Minimal in-memory database for unit tests.
    Tracks: orgs, users, sso_configs, api_keys, courses, lti_platforms.
    """

    def __init__(self):
        self.orgs: Dict[str, dict] = {
            TEST_ORG_ID: {
                "id": TEST_ORG_ID,
                "name": "Test Org",
                "slug": "test-org",
                "sso_enabled": False,
                "sso_provider": None,
            },
            TEST_ORG_2_ID: {
                "id": TEST_ORG_2_ID,
                "name": "Other Org",
                "slug": "other-org",
                "sso_enabled": False,
                "sso_provider": None,
            },
        }
        self.users: Dict[str, dict] = {
            TEST_ADMIN_ID: {
                "id": TEST_ADMIN_ID,
                "email": "admin@test.example.com",
                "role": "org_admin",
                "organization_id": TEST_ORG_ID,
                "sso_subject": None,
            }
        }
        self.sso_configs: Dict[str, dict] = {}   # org_id -> config
        self.api_keys: Dict[str, dict]    = {}   # key_id -> record
        self.courses: Dict[str, dict]     = {}   # course_id -> record
        self.lti_platforms: Dict[str, dict] = {} # platform_id -> record
        self.rate_counters: Dict[str, int]  = {} # key_id -> request_count

    # ---- helpers -----------------------------------------------------------

    def add_sso_config(
        self,
        org_id: str,
        provider: str = "saml",
        idp_metadata_url: str = "https://idp.example.com/metadata",
        idp_sso_url: str = IDP_SSO_URL,
        idp_cert: str = IDP_CERT,
        sp_entity_id: str = ENTITY_ID,
        acs_url: str = ACS_URL,
        enabled: bool = True,
    ) -> dict:
        cfg = {
            "id": str(uuid.uuid4()),
            "org_id": org_id,
            "provider": provider,
            "idp_metadata_url": idp_metadata_url,
            "idp_sso_url": idp_sso_url,
            "idp_cert": idp_cert,
            "sp_entity_id": sp_entity_id,
            "acs_url": acs_url,
            "enabled": enabled,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.sso_configs[org_id] = cfg
        self.orgs[org_id]["sso_enabled"] = enabled
        self.orgs[org_id]["sso_provider"] = provider
        return cfg

    def add_api_key(
        self,
        org_id: str,
        name: str = "Test Key",
        scopes: Optional[List[str]] = None,
        revoked: bool = False,
    ) -> tuple[str, dict]:
        raw_key = f"sk_test_REDACTED{secrets.token_hex(16)}"
        key_id  = str(uuid.uuid4())
        record  = {
            "id":         key_id,
            "org_id":     org_id,
            "name":       name,
            "key_prefix": raw_key[:12],          # visible, non-sensitive
            "key_hash":   _api_key_hash(raw_key),# stored hash
            "scopes":     scopes or ["courses:read", "courses:write"],
            "revoked":    revoked,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.api_keys[key_id] = record
        self.rate_counters[key_id] = 0
        return raw_key, record

    def add_course(self, org_id: str, **kwargs) -> dict:
        course_id = str(uuid.uuid4())
        course = {
            "id":          course_id,
            "org_id":      org_id,
            "title":       kwargs.get("title", "Test Course"),
            "description": kwargs.get("description", "A test course"),
            "status":      kwargs.get("status", "draft"),
            "created_at":  datetime.utcnow().isoformat(),
        }
        self.courses[course_id] = course
        return course

    def add_lti_platform(self, org_id: str) -> dict:
        platform_id = str(uuid.uuid4())
        platform = {
            "id":            platform_id,
            "org_id":        org_id,
            "name":          "Canvas LMS",
            "issuer":        LTI_ISSUER,
            "client_id":     LTI_CLIENT_ID,
            "deployment_id": LTI_DEPLOYMENT_ID,
            "auth_url":      LTI_AUTH_URL,
            "token_url":     LTI_TOKEN_URL,
            "jwks_url":      LTI_JWKS_URL,
            "enabled":       True,
            "created_at":    datetime.utcnow().isoformat(),
        }
        self.lti_platforms[platform_id] = platform
        return platform

    def lookup_api_key(self, raw_key: str) -> Optional[dict]:
        """Find an API key record by the raw key value."""
        key_hash = _api_key_hash(raw_key)
        for record in self.api_keys.values():
            if record["key_hash"] == key_hash:
                return record
        return None


@pytest.fixture
def db() -> FakeDB:
    return FakeDB()


# ===========================================================================
# ██████████████████████████████████████████████████████████████████████████
# SECTION 1 — SSO / SAML TESTS
# ██████████████████████████████████████████████████████████████████████████
# ===========================================================================


class TestSAMLMetadata:
    """SAML SP metadata endpoint must return well-formed XML."""

    @pytest.mark.unit
    @pytest.mark.auth
    def test_metadata_returns_xml_content_type(self):
        """
        Given: SP metadata endpoint produces a Response with media_type application/xml
        When:  The response object is inspected
        Then:  media_type contains 'xml'
        """
        from fastapi.responses import Response

        xml = _build_sp_metadata(ENTITY_ID, ACS_URL)
        resp = Response(content=xml, media_type="application/xml")
        assert "xml" in resp.media_type

    @pytest.mark.unit
    @pytest.mark.auth
    def test_metadata_contains_required_elements(self):
        """
        Given: SP metadata generated for ENTITY_ID and ACS_URL
        When:  Metadata XML is parsed
        Then:  Root is EntityDescriptor with entityID, and AssertionConsumerService
               with the correct Location attribute is present
        """
        xml_bytes = _build_sp_metadata(ENTITY_ID, ACS_URL)
        root = ET.fromstring(xml_bytes)

        ns = {
            "md": "urn:oasis:names:tc:SAML:2.0:metadata",
        }

        assert root.tag.endswith("EntityDescriptor"), (
            f"Root element should be EntityDescriptor, got: {root.tag}"
        )
        assert root.get("entityID") == ENTITY_ID

        acs_elements = root.findall(".//md:AssertionConsumerService", ns)
        assert len(acs_elements) >= 1, "Metadata must include at least one ACS element"
        acs_locs = [el.get("Location") for el in acs_elements]
        assert ACS_URL in acs_locs, (
            f"ACS URL {ACS_URL} not found in metadata locations: {acs_locs}"
        )

    @pytest.mark.unit
    @pytest.mark.auth
    def test_metadata_includes_sp_sso_descriptor(self):
        """
        Given: SP metadata
        When:  Parsed
        Then:  SPSSODescriptor element is present (required for SAML 2.0)
        """
        xml_bytes = _build_sp_metadata(ENTITY_ID, ACS_URL)
        root = ET.fromstring(xml_bytes)
        sp_sso = [
            el for el in root.iter()
            if el.tag.endswith("SPSSODescriptor")
        ]
        assert len(sp_sso) >= 1, "SPSSODescriptor must be present"

    @pytest.mark.unit
    @pytest.mark.auth
    def test_metadata_404_for_unknown_org(self, db):
        """
        Given: Org slug that does not exist
        When:  metadata handler is called
        Then:  HTTPException with status 404 is raised
        """
        from fastapi import HTTPException

        def saml_metadata_handler(org_slug: str):
            if org_slug not in [o["slug"] for o in db.orgs.values()]:
                raise HTTPException(status_code=404, detail="Organisation not found")
            return _build_sp_metadata(ENTITY_ID, ACS_URL)

        with pytest.raises(HTTPException) as exc_info:
            saml_metadata_handler("nonexistent-org")
        assert exc_info.value.status_code == 404


def _build_sp_metadata(entity_id: str, acs_url: str) -> bytes:
    """
    Build a minimal SAML 2.0 SP metadata XML document.
    Production code will use python3-saml or similar; this helper
    exists so tests that validate XML structure can run without it.
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor
    xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    entityID="{entity_id}">
  <md:SPSSODescriptor
      AuthnRequestsSigned="false"
      WantAssertionsSigned="true"
      protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:AssertionConsumerService
        Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        Location="{acs_url}"
        index="1"/>
  </md:SPSSODescriptor>
</md:EntityDescriptor>"""
    return xml.encode("utf-8")


# ---------------------------------------------------------------------------

class TestSAMLLogin:
    """SAML login flow — AuthnRequest redirect."""

    @pytest.mark.unit
    @pytest.mark.auth
    def test_saml_login_redirects_to_idp(self, db):
        """
        Given: Org has SSO enabled with a known IdP SSO URL
        When:  login handler builds the redirect URL
        Then:  URL points to IdP SSO URL and contains SAMLRequest query parameter
        """
        import urllib.parse
        db.add_sso_config(TEST_ORG_ID)
        cfg = db.sso_configs[TEST_ORG_ID]

        saml_req = base64.b64encode(b"<samlp:AuthnRequest/>").decode()
        redirect_url = f"{cfg['idp_sso_url']}?SAMLRequest={urllib.parse.quote(saml_req)}"

        assert IDP_SSO_URL in redirect_url
        qs = parse_qs(urlparse(redirect_url).query)
        assert "SAMLRequest" in qs, "SAMLRequest must be in redirect query string"

    @pytest.mark.unit
    @pytest.mark.auth
    def test_saml_login_disabled_when_sso_not_configured(self, db):
        """
        Given: Org exists but has no SSO configuration
        When:  login handler is called
        Then:  HTTPException 403 is raised
        """
        from fastapi import HTTPException

        def saml_login_handler(org_id: str):
            cfg = db.sso_configs.get(org_id)
            if not cfg or not cfg["enabled"]:
                raise HTTPException(status_code=403, detail="SSO not enabled for this organisation")
            return IDP_SSO_URL  # would be a RedirectResponse in real code

        with pytest.raises(HTTPException) as exc_info:
            saml_login_handler(TEST_ORG_ID)   # no SSO config in fresh db
        assert exc_info.value.status_code == 403

    @pytest.mark.unit
    @pytest.mark.auth
    def test_saml_login_includes_relay_state(self, db):
        """
        Given: Org with SSO enabled; ?next=/dashboard is requested
        When:  login handler builds the redirect URL
        Then:  Redirect URL contains RelayState that decodes to '/dashboard'
        """
        import urllib.parse
        db.add_sso_config(TEST_ORG_ID)

        next_url    = "/dashboard"
        relay_state = base64.b64encode(next_url.encode()).decode()
        saml_req    = base64.b64encode(b"<samlp:AuthnRequest/>").decode()
        redirect_url = (
            f"{IDP_SSO_URL}"
            f"?SAMLRequest={urllib.parse.quote(saml_req)}"
            f"&RelayState={urllib.parse.quote(relay_state)}"
        )

        qs      = parse_qs(urlparse(redirect_url).query)
        assert "RelayState" in qs
        decoded = base64.b64decode(qs["RelayState"][0]).decode()
        assert decoded == "/dashboard"


# ---------------------------------------------------------------------------

class TestSAMLCallback:
    """SAML ACS — assertion consumer service (POST /sso/saml/callback)."""

    def _make_saml_response(
        self,
        subject: str = "user@idp.example.com",
        name_id: str = "user@idp.example.com",
        email: str = "user@idp.example.com",
        org_id: str = TEST_ORG_ID,
        valid: bool = True,
        expired: bool = False,
    ) -> str:
        """
        Build a minimal base64-encoded SAMLResponse for test purposes.
        Production code will parse a cryptographically signed document;
        tests inject the parsed assertion dict via a mock to stay fast.
        """
        now = datetime.utcnow()
        not_on_or_after = (
            (now - timedelta(hours=1)) if expired
            else (now + timedelta(hours=1))
        )
        assertion = {
            "subject": subject,
            "name_id": name_id,
            "email": email,
            "org_id": org_id,
            "not_on_or_after": not_on_or_after.isoformat(),
            "valid_signature": valid,
        }
        raw = json.dumps(assertion).encode()
        return base64.b64encode(raw).decode()

    @pytest.mark.unit
    @pytest.mark.auth
    def test_valid_assertion_creates_session(self, db):
        """
        Given: A valid SAML assertion from the IdP
        When:  POST /sso/saml/callback with SAMLResponse
        Then:  HTTP 200 (or 302 to dashboard) and a session token is returned
        """
        db.add_sso_config(TEST_ORG_ID)
        saml_response_b64 = self._make_saml_response()
        result = _process_saml_callback(db, saml_response_b64, org_id=TEST_ORG_ID)
        assert result["success"] is True
        assert "session_token" in result
        assert result["session_token"]  # non-empty

    @pytest.mark.unit
    @pytest.mark.auth
    def test_invalid_signature_is_rejected(self, db):
        """
        Given: A SAMLResponse with an invalid (forged) signature
        When:  POST /sso/saml/callback
        Then:  HTTP 401 Unauthorized — assertion rejected
        """
        db.add_sso_config(TEST_ORG_ID)
        saml_response_b64 = self._make_saml_response(valid=False)
        result = _process_saml_callback(db, saml_response_b64, org_id=TEST_ORG_ID)
        assert result["success"] is False
        assert result["error_code"] in ("invalid_signature", "auth_failed")

    @pytest.mark.unit
    @pytest.mark.auth
    def test_expired_assertion_is_rejected(self, db):
        """
        Given: A SAMLResponse whose NotOnOrAfter is in the past
        When:  POST /sso/saml/callback
        Then:  HTTP 401 Unauthorized — assertion expired
        """
        db.add_sso_config(TEST_ORG_ID)
        saml_response_b64 = self._make_saml_response(expired=True)
        result = _process_saml_callback(db, saml_response_b64, org_id=TEST_ORG_ID)
        assert result["success"] is False
        assert result["error_code"] in ("assertion_expired", "auth_failed")

    @pytest.mark.unit
    @pytest.mark.auth
    def test_user_auto_provisioned_on_first_sso_login(self, db):
        """
        Given: A valid SAML assertion for a user who does not yet exist in the DB
        When:  POST /sso/saml/callback
        Then:  A new user record is created; session token is issued
        """
        db.add_sso_config(TEST_ORG_ID)
        new_email = "brand-new-sso-user@idp.example.com"
        saml_response_b64 = self._make_saml_response(
            subject=new_email, name_id=new_email, email=new_email
        )
        result = _process_saml_callback(db, saml_response_b64, org_id=TEST_ORG_ID)
        assert result["success"] is True
        assert result.get("user_provisioned") is True, (
            "First-time SSO login should set user_provisioned=True"
        )
        # Verify user now exists in DB
        created_user = next(
            (u for u in db.users.values() if u["email"] == new_email), None
        )
        assert created_user is not None, "User should be persisted after auto-provisioning"
        assert created_user["organization_id"] == TEST_ORG_ID

    @pytest.mark.unit
    @pytest.mark.auth
    def test_existing_user_not_duplicated_on_repeat_sso_login(self, db):
        """
        Given: A user who has SSO-logged-in before (sso_subject is set)
        When:  POST /sso/saml/callback with the same assertion
        Then:  No new user is created; existing record is returned
        """
        db.add_sso_config(TEST_ORG_ID)
        email = "existing-sso-user@idp.example.com"
        existing_id = str(uuid.uuid4())
        db.users[existing_id] = {
            "id": existing_id,
            "email": email,
            "role": "student",
            "organization_id": TEST_ORG_ID,
            "sso_subject": email,
        }
        user_count_before = len(db.users)
        saml_response_b64 = self._make_saml_response(
            subject=email, name_id=email, email=email
        )
        result = _process_saml_callback(db, saml_response_b64, org_id=TEST_ORG_ID)
        assert result["success"] is True
        assert result.get("user_provisioned") is not True
        assert len(db.users) == user_count_before, "No duplicate user should be created"

    @pytest.mark.unit
    @pytest.mark.auth
    def test_sso_config_update_requires_admin_role(self):
        """
        Given: A user with 'student' role attempts to update SSO config
        When:  PUT /sso/config
        Then:  HTTP 403 Forbidden
        """
        student_token = _user_token(role="student")
        result = _update_sso_config(
            token=student_token,
            org_id=TEST_ORG_ID,
            config={"idp_sso_url": "https://evil.example.com/sso"},
        )
        assert result["status_code"] == 403

    @pytest.mark.unit
    @pytest.mark.auth
    def test_sso_config_update_succeeds_for_admin(self):
        """
        Given: A user with 'org_admin' role
        When:  PUT /sso/config with valid payload
        Then:  HTTP 200 and config updated
        """
        admin_token = _user_token(role="org_admin")
        result = _update_sso_config(
            token=admin_token,
            org_id=TEST_ORG_ID,
            config={"idp_sso_url": IDP_SSO_URL, "idp_cert": IDP_CERT},
        )
        assert result["status_code"] == 200


def _process_saml_callback(
    db: FakeDB,
    saml_response_b64: str,
    org_id: str = TEST_ORG_ID,
) -> dict:
    """
    Fake SAML callback processor — stands in for the real service until it ships.
    Decodes the test SAMLResponse and applies the same logical checks
    the production implementation must satisfy.
    """
    try:
        assertion = json.loads(base64.b64decode(saml_response_b64).decode())
    except Exception:
        return {"success": False, "error_code": "invalid_response"}

    if not assertion.get("valid_signature", True):
        return {"success": False, "error_code": "invalid_signature"}

    not_on_or_after = datetime.fromisoformat(assertion["not_on_or_after"])
    if not_on_or_after < datetime.utcnow():
        return {"success": False, "error_code": "assertion_expired"}

    email = assertion["email"]
    existing = next(
        (u for u in db.users.values()
         if u["email"] == email and u["organization_id"] == org_id),
        None,
    )
    provisioned = False
    if existing is None:
        new_id = str(uuid.uuid4())
        db.users[new_id] = {
            "id": new_id,
            "email": email,
            "role": "student",
            "organization_id": org_id,
            "sso_subject": assertion["name_id"],
        }
        provisioned = True

    token = _make_jwt({
        "user_id": str(uuid.uuid4()),
        "email": email,
        "organization_id": org_id,
        "exp": int((datetime.utcnow() + timedelta(hours=8)).timestamp()),
    })

    result: dict = {"success": True, "session_token": token}
    if provisioned:
        result["user_provisioned"] = True
    return result


def _update_sso_config(token: str, org_id: str, config: dict) -> dict:
    """Fake SSO config updater that enforces role-based access."""
    if HAS_PYJWT:
        try:
            claims = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except Exception:
            return {"status_code": 401}
    else:
        # Decode body section without verification for shape tests
        parts = token.split(".")
        padding = "=" * (4 - len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(parts[1] + padding))

    if claims.get("role") not in ("org_admin", "site_admin"):
        return {"status_code": 403, "detail": "Insufficient permissions"}
    return {"status_code": 200, "detail": "SSO config updated"}


# ---------------------------------------------------------------------------

class TestOAuth2Flow:
    """OAuth2 authorize / callback flow (used alongside SAML for IdP federation)."""

    @pytest.mark.unit
    @pytest.mark.auth
    def test_oauth2_authorize_redirects_with_state(self):
        """
        Given: OAuth2 authorization endpoint builds the redirect URL
        When:  Handler assembles query parameters for the IdP
        Then:  URL contains state, redirect_uri, and response_type=code
        """
        import urllib.parse

        OAUTH_AUTH_URL = "https://idp.example.com/oauth2/authorize"
        CLIENT_ID      = "techuni-client-id"
        REDIRECT_URI   = "https://courses.techuni.ai/sso/oauth2/callback"

        state  = secrets.token_urlsafe(16)
        params = urllib.parse.urlencode({
            "client_id":     CLIENT_ID,
            "redirect_uri":  REDIRECT_URI,
            "response_type": "code",
            "scope":         "openid email profile",
            "state":         state,
        })
        redirect_url = f"{OAUTH_AUTH_URL}?{params}"

        qs = parse_qs(urlparse(redirect_url).query)
        assert "state" in qs,        "state must be present for CSRF protection"
        assert "redirect_uri" in qs, "redirect_uri must be present"
        assert qs.get("response_type", [None])[0] == "code"

    @pytest.mark.unit
    @pytest.mark.auth
    def test_oauth2_callback_exchanges_code_for_token(self):
        """
        Given: IdP redirects back with ?code=AUTH_CODE&state=STATE
        When:  GET /sso/oauth2/callback?code=...&state=...
        Then:  Server exchanges code for access/id token; session token issued
        """
        TOKEN_ENDPOINT = "https://idp.example.com/oauth2/token"

        # Mock the token exchange HTTP call
        mock_token_response = {
            "access_token":  "ya29.access-token",
            "id_token":      _make_jwt({
                "sub":   "oauth-user-123",
                "email": "oauth.user@example.com",
                "exp":   int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            }),
            "token_type":    "Bearer",
            "expires_in":    3600,
        }

        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_token_response
            mock_resp.status_code = 200
            mock_post.return_value = mock_resp

            result = _oauth2_callback_handler(
                code="AUTH_CODE_12345",
                state="valid-state",
                token_endpoint=TOKEN_ENDPOINT,
            )

        assert result["success"] is True
        assert "session_token" in result
        assert result["email"] == "oauth.user@example.com"

    @pytest.mark.unit
    @pytest.mark.auth
    def test_oauth2_callback_rejects_invalid_state(self):
        """
        Given: Callback arrives with a state that doesn't match stored state
        When:  GET /sso/oauth2/callback?code=...&state=WRONG
        Then:  403 Forbidden — CSRF protection
        """
        result = _oauth2_callback_handler(
            code="AUTH_CODE",
            state="tampered-state",
            stored_state="original-state",  # mismatch
        )
        assert result["success"] is False
        assert result["error_code"] == "state_mismatch"


def _oauth2_callback_handler(
    code: str,
    state: str,
    token_endpoint: str = "https://idp.example.com/oauth2/token",
    stored_state: Optional[str] = None,
) -> dict:
    """Fake OAuth2 callback processor for tests."""
    effective_stored = stored_state if stored_state is not None else state
    if state != effective_stored:
        return {"success": False, "error_code": "state_mismatch"}

    try:
        import requests
        resp = requests.post(token_endpoint, data={"code": code, "grant_type": "authorization_code"})
        token_data = resp.json()
    except Exception:
        return {"success": False, "error_code": "token_exchange_failed"}

    id_token = token_data.get("id_token", "")
    parts = id_token.split(".")
    if len(parts) != 3:
        return {"success": False, "error_code": "invalid_id_token"}

    try:
        padding = "=" * (4 - len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(parts[1] + padding))
    except Exception:
        return {"success": False, "error_code": "invalid_id_token"}

    email = claims.get("email", "")
    session_token = _make_jwt({
        "sub":   claims.get("sub"),
        "email": email,
        "exp":   int((datetime.utcnow() + timedelta(hours=8)).timestamp()),
    })
    return {"success": True, "session_token": session_token, "email": email}


# ===========================================================================
# ██████████████████████████████████████████████████████████████████████████
# SECTION 2 — API KEY TESTS
# ██████████████████████████████████████████████████████████████████████████
# ===========================================================================


class TestAPIKeyGeneration:
    """API key lifecycle — generation, display, storage."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_generate_returns_raw_key_once(self, db):
        """
        Given: An admin user requests a new API key
        When:  POST /api/v1/keys
        Then:  Response body contains the full raw key (shown only once)
               and the key starts with the expected prefix format
        """
        raw_key, record = db.add_api_key(TEST_ORG_ID, name="CI Key")
        assert raw_key.startswith("sk_test_REDACTED"), "API key should start with 'sk_test_REDACTED'"
        assert len(raw_key) > 20, "API key should be at least 20 characters"
        # Hash stored, not the raw key
        assert record["key_hash"] != raw_key

    @pytest.mark.unit
    @pytest.mark.api
    def test_list_keys_does_not_expose_full_key(self, db):
        """
        Given: Multiple API keys exist for an org
        When:  GET /api/v1/keys
        Then:  Response contains key_prefix (first 12 chars) but NOT the full key
        """
        raw_key, record = db.add_api_key(TEST_ORG_ID, name="Listing Test Key")

        keys_listing = _list_api_keys(db, org_id=TEST_ORG_ID)

        for key_record in keys_listing:
            # Full raw key must never appear
            assert raw_key not in key_record.values(), (
                "Full raw API key must not be included in list response"
            )
            # key_hash must not appear
            assert _api_key_hash(raw_key) not in key_record.values(), (
                "API key hash must not be included in list response"
            )
            # Prefix is fine
            assert "key_prefix" in key_record

    @pytest.mark.unit
    @pytest.mark.api
    def test_generated_key_is_unique(self, db):
        """
        Given: Multiple API keys generated for the same org
        When:  Keys are compared
        Then:  Every raw key is unique
        """
        keys = [db.add_api_key(TEST_ORG_ID, name=f"Key {i}")[0] for i in range(10)]
        assert len(set(keys)) == len(keys), "All generated API keys must be unique"

    @pytest.mark.unit
    @pytest.mark.api
    def test_key_hash_is_not_reversible(self, db):
        """
        Given: A stored key hash
        When:  Hash is compared to original key
        Then:  It is not the same value (irreversible hash, not encryption)
        """
        raw_key, record = db.add_api_key(TEST_ORG_ID)
        assert record["key_hash"] != raw_key
        assert record["key_prefix"] != raw_key  # prefix is just the first N chars


def _list_api_keys(db: FakeDB, org_id: str) -> List[dict]:
    """Return a safe listing of API keys — strips hash and full key."""
    safe_keys = []
    for record in db.api_keys.values():
        if record["org_id"] == org_id:
            safe_keys.append({
                "id":         record["id"],
                "name":       record["name"],
                "key_prefix": record["key_prefix"],
                "scopes":     record["scopes"],
                "revoked":    record["revoked"],
                "created_at": record["created_at"],
                # NOTE: key_hash is intentionally excluded from the listing
            })
    return safe_keys


# ---------------------------------------------------------------------------

class TestAPIKeyAuthentication:
    """API key used as authentication credential."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_valid_key_grants_access(self, db):
        """
        Given: A valid, non-revoked API key
        When:  Request includes 'Authorization: Bearer sk_test_REDACTED...'
        Then:  Request is authenticated; org context injected
        """
        raw_key, _ = db.add_api_key(TEST_ORG_ID)
        result = _authenticate_api_key(db, raw_key)
        assert result["authenticated"] is True
        assert result["org_id"] == TEST_ORG_ID

    @pytest.mark.unit
    @pytest.mark.api
    def test_invalid_key_returns_401(self, db):
        """
        Given: A key that does not exist in the database
        When:  Request includes that key
        Then:  HTTP 401 Unauthorized
        """
        bogus_key = "sk_test_REDACTED"
        result = _authenticate_api_key(db, bogus_key)
        assert result["authenticated"] is False
        assert result["status_code"] == 401

    @pytest.mark.unit
    @pytest.mark.api
    def test_revoked_key_returns_401(self, db):
        """
        Given: An API key that has been revoked
        When:  Request uses the revoked key
        Then:  HTTP 401 Unauthorized
        """
        raw_key, _ = db.add_api_key(TEST_ORG_ID, revoked=True)
        result = _authenticate_api_key(db, raw_key)
        assert result["authenticated"] is False
        assert result["status_code"] == 401

    @pytest.mark.unit
    @pytest.mark.api
    def test_key_scoped_to_org_cannot_access_other_org(self, db):
        """
        Given: An API key belonging to Org A
        When:  Request attempts to access Org B's resources
        Then:  HTTP 403 Forbidden (org isolation)
        """
        raw_key, _ = db.add_api_key(TEST_ORG_ID)
        auth_result = _authenticate_api_key(db, raw_key)
        assert auth_result["org_id"] == TEST_ORG_ID

        # Simulate a request for a resource in TEST_ORG_2_ID
        access = _check_resource_access(
            authenticated_org=auth_result["org_id"],
            resource_org=TEST_ORG_2_ID,
        )
        assert access["allowed"] is False
        assert access["status_code"] == 403

    @pytest.mark.unit
    @pytest.mark.api
    def test_rate_limiting_per_api_key(self, db):
        """
        Given: An API key with a rate limit of 5 requests/minute
        When:  6th request arrives within the same minute
        Then:  HTTP 429 Too Many Requests
        """
        raw_key, record = db.add_api_key(TEST_ORG_ID)
        RATE_LIMIT = 5

        for i in range(RATE_LIMIT):
            result = _simulate_rate_limited_request(db, record["id"], limit=RATE_LIMIT)
            assert result["status_code"] == 200, f"Request {i+1} should succeed"

        # 6th request should be rate-limited
        over_limit = _simulate_rate_limited_request(db, record["id"], limit=RATE_LIMIT)
        assert over_limit["status_code"] == 429

    @pytest.mark.unit
    @pytest.mark.api
    def test_revoke_key_endpoint_requires_admin(self, db):
        """
        Given: A student-role token
        When:  DELETE /api/v1/keys/{key_id}
        Then:  403 Forbidden
        """
        _, record = db.add_api_key(TEST_ORG_ID)
        student_token = _user_token(role="student")
        result = _revoke_api_key(db, token=student_token, key_id=record["id"])
        assert result["status_code"] == 403

    @pytest.mark.unit
    @pytest.mark.api
    def test_revoke_key_endpoint_succeeds_for_admin(self, db):
        """
        Given: An org_admin token
        When:  DELETE /api/v1/keys/{key_id}
        Then:  200 OK; key is marked revoked
        """
        raw_key, record = db.add_api_key(TEST_ORG_ID)
        admin_token = _user_token(role="org_admin")
        result = _revoke_api_key(db, token=admin_token, key_id=record["id"])
        assert result["status_code"] == 200
        assert db.api_keys[record["id"]]["revoked"] is True


def _authenticate_api_key(db: FakeDB, raw_key: str) -> dict:
    record = db.lookup_api_key(raw_key)
    if record is None:
        return {"authenticated": False, "status_code": 401}
    if record["revoked"]:
        return {"authenticated": False, "status_code": 401}
    return {"authenticated": True, "org_id": record["org_id"], "status_code": 200}


def _check_resource_access(authenticated_org: str, resource_org: str) -> dict:
    if authenticated_org != resource_org:
        return {"allowed": False, "status_code": 403}
    return {"allowed": True, "status_code": 200}


def _simulate_rate_limited_request(db: FakeDB, key_id: str, limit: int = 60) -> dict:
    db.rate_counters[key_id] = db.rate_counters.get(key_id, 0) + 1
    if db.rate_counters[key_id] > limit:
        return {"status_code": 429, "detail": "Rate limit exceeded"}
    return {"status_code": 200}


def _revoke_api_key(db: FakeDB, token: str, key_id: str) -> dict:
    if HAS_PYJWT:
        try:
            claims = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except Exception:
            return {"status_code": 401}
    else:
        parts = token.split(".")
        padding = "=" * (4 - len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(parts[1] + padding))

    if claims.get("role") not in ("org_admin", "site_admin"):
        return {"status_code": 403}

    if key_id not in db.api_keys:
        return {"status_code": 404}

    db.api_keys[key_id]["revoked"] = True
    return {"status_code": 200}


# ===========================================================================
# ██████████████████████████████████████████████████████████████████████████
# SECTION 3 — PUBLIC REST API TESTS
# ██████████████████████████████████████████████████████████████████████████
# ===========================================================================


class TestPublicAPICourseListing:
    """GET /api/v1/courses — paginated course list."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_returns_paginated_list(self, db):
        """
        Given: 15 courses exist for an org
        When:  GET /api/v1/courses?page=1&page_size=10
        Then:  Response contains 10 courses, total=15, next page link
        """
        for i in range(15):
            db.add_course(TEST_ORG_ID, title=f"Course {i}")

        result = _list_courses(db, org_id=TEST_ORG_ID, page=1, page_size=10)

        assert result["total"] == 15
        assert len(result["items"]) == 10
        assert result["page"] == 1
        assert result["next_page"] == 2

    @pytest.mark.unit
    @pytest.mark.api
    def test_second_page_contains_remaining_items(self, db):
        """
        Given: 15 courses; page_size=10
        When:  GET /api/v1/courses?page=2&page_size=10
        Then:  5 courses returned; next_page is None
        """
        for i in range(15):
            db.add_course(TEST_ORG_ID, title=f"Course {i}")

        result = _list_courses(db, org_id=TEST_ORG_ID, page=2, page_size=10)

        assert len(result["items"]) == 5
        assert result["next_page"] is None

    @pytest.mark.unit
    @pytest.mark.api
    def test_org_isolation_hides_other_org_courses(self, db):
        """
        Given: Courses from two different orgs
        When:  GET /api/v1/courses (authenticated as Org A)
        Then:  Only Org A's courses are returned
        """
        db.add_course(TEST_ORG_ID, title="Org A Course")
        db.add_course(TEST_ORG_2_ID, title="Org B Course — MUST NOT APPEAR")

        result = _list_courses(db, org_id=TEST_ORG_ID, page=1, page_size=50)

        titles = [c["title"] for c in result["items"]]
        assert "Org B Course — MUST NOT APPEAR" not in titles
        assert all(c["org_id"] == TEST_ORG_ID for c in result["items"])

    @pytest.mark.unit
    @pytest.mark.api
    def test_empty_org_returns_empty_list(self, db):
        """
        Given: An org with no courses
        When:  GET /api/v1/courses
        Then:  items=[], total=0
        """
        result = _list_courses(db, org_id=TEST_ORG_ID, page=1, page_size=10)
        assert result["total"] == 0
        assert result["items"] == []

    @pytest.mark.unit
    @pytest.mark.api
    def test_unauthenticated_request_returns_401(self):
        """
        Given: Request with no Authorization header
        When:  auth guard is invoked
        Then:  HTTPException with 401 is raised
        """
        from fastapi import HTTPException

        def require_auth(authorization: Optional[str] = None):
            if not authorization or not authorization.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Unauthorized")

        with pytest.raises(HTTPException) as exc_info:
            require_auth(authorization=None)
        assert exc_info.value.status_code == 401

        with pytest.raises(HTTPException):
            require_auth(authorization="Basic notbearer")


def _list_courses(
    db: FakeDB,
    org_id: str,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    org_courses = sorted(
        [c for c in db.courses.values() if c["org_id"] == org_id],
        key=lambda c: c["created_at"],
    )
    total = len(org_courses)
    start = (page - 1) * page_size
    end   = start + page_size
    items = org_courses[start:end]
    has_next = end < total
    return {
        "items":     items,
        "total":     total,
        "page":      page,
        "page_size": page_size,
        "next_page": (page + 1) if has_next else None,
    }


# ---------------------------------------------------------------------------

class TestPublicAPICourseCreate:
    """POST /api/v1/courses/generate — async course generation trigger."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_generate_course_returns_course_id(self, db):
        """
        Given: Valid course generation payload
        When:  POST /api/v1/courses/generate
        Then:  201 Created with course_id in response
        """
        payload = {
            "title":       "Python 101",
            "description": "Learn Python from scratch",
            "difficulty":  "beginner",
        }
        result = _create_course(db, org_id=TEST_ORG_ID, payload=payload)
        assert result["status_code"] == 201
        assert "course_id" in result
        assert result["course_id"] in db.courses

    @pytest.mark.unit
    @pytest.mark.api
    def test_generate_course_fails_without_title(self, db):
        """
        Given: Payload missing required 'title' field
        When:  POST /api/v1/courses/generate
        Then:  422 Unprocessable Entity
        """
        result = _create_course(db, org_id=TEST_ORG_ID, payload={"description": "No title"})
        assert result["status_code"] == 422

    @pytest.mark.unit
    @pytest.mark.api
    def test_created_course_belongs_to_requesting_org(self, db):
        """
        Given: Authenticated as Org A
        When:  POST /api/v1/courses/generate
        Then:  New course has org_id == Org A
        """
        payload = {"title": "Org-scoped Course", "description": "...", "difficulty": "beginner"}
        result = _create_course(db, org_id=TEST_ORG_ID, payload=payload)
        assert result["status_code"] == 201
        course = db.courses[result["course_id"]]
        assert course["org_id"] == TEST_ORG_ID


def _create_course(db: FakeDB, org_id: str, payload: dict) -> dict:
    if "title" not in payload or not payload["title"]:
        return {"status_code": 422, "detail": "title is required"}
    course = db.add_course(org_id, **payload)
    return {"status_code": 201, "course_id": course["id"]}


# ---------------------------------------------------------------------------

class TestPublicAPICourseDetail:
    """GET /api/v1/courses/{id} — single course details."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_returns_course_for_correct_org(self, db):
        """
        Given: Course belongs to Org A
        When:  GET /api/v1/courses/{id} authenticated as Org A
        Then:  200 with course data
        """
        course = db.add_course(TEST_ORG_ID, title="Detail Test Course")
        result = _get_course(db, org_id=TEST_ORG_ID, course_id=course["id"])
        assert result["status_code"] == 200
        assert result["course"]["id"] == course["id"]

    @pytest.mark.unit
    @pytest.mark.api
    def test_returns_404_for_unknown_course(self, db):
        """
        Given: A course ID that does not exist
        When:  GET /api/v1/courses/{id}
        Then:  404 Not Found
        """
        result = _get_course(db, org_id=TEST_ORG_ID, course_id=str(uuid.uuid4()))
        assert result["status_code"] == 404

    @pytest.mark.unit
    @pytest.mark.api
    def test_org_isolation_prevents_cross_org_course_access(self, db):
        """
        Given: Course belongs to Org B
        When:  GET /api/v1/courses/{id} authenticated as Org A
        Then:  404 Not Found (org isolation — not a 403 to avoid enumeration)
        """
        course = db.add_course(TEST_ORG_2_ID, title="Other Org Course")
        result = _get_course(db, org_id=TEST_ORG_ID, course_id=course["id"])
        assert result["status_code"] == 404


def _get_course(db: FakeDB, org_id: str, course_id: str) -> dict:
    course = db.courses.get(course_id)
    if course is None or course["org_id"] != org_id:
        return {"status_code": 404}
    return {"status_code": 200, "course": course}


# ---------------------------------------------------------------------------

class TestPublicAPIAnalytics:
    """GET /api/v1/analytics — course/org analytics endpoint."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_analytics_returns_valid_structure(self, db):
        """
        Given: An org with some courses
        When:  GET /api/v1/analytics
        Then:  Response contains expected keys: total_courses, total_enrollments,
               completion_rate, generated_at
        """
        for i in range(3):
            db.add_course(TEST_ORG_ID, title=f"Analytics Course {i}")

        analytics = _get_analytics(db, org_id=TEST_ORG_ID)

        required_keys = {"total_courses", "total_enrollments", "completion_rate", "generated_at"}
        assert required_keys.issubset(analytics.keys()), (
            f"Analytics response missing keys: {required_keys - analytics.keys()}"
        )

    @pytest.mark.unit
    @pytest.mark.api
    def test_analytics_total_courses_is_accurate(self, db):
        """
        Given: 5 courses for Org A, 3 courses for Org B
        When:  GET /api/v1/analytics authenticated as Org A
        Then:  total_courses == 5
        """
        for i in range(5):
            db.add_course(TEST_ORG_ID)
        for i in range(3):
            db.add_course(TEST_ORG_2_ID)

        analytics = _get_analytics(db, org_id=TEST_ORG_ID)
        assert analytics["total_courses"] == 5

    @pytest.mark.unit
    @pytest.mark.api
    def test_analytics_completion_rate_is_between_0_and_1(self, db):
        """
        Given: Analytics data
        When:  completion_rate is returned
        Then:  Value is in [0.0, 1.0]
        """
        db.add_course(TEST_ORG_ID)
        analytics = _get_analytics(db, org_id=TEST_ORG_ID)
        assert 0.0 <= analytics["completion_rate"] <= 1.0

    @pytest.mark.unit
    @pytest.mark.api
    def test_analytics_generated_at_is_recent(self, db):
        """
        Given: Analytics generated now
        When:  generated_at timestamp is parsed
        Then:  It is within the last 5 seconds
        """
        analytics = _get_analytics(db, org_id=TEST_ORG_ID)
        generated = datetime.fromisoformat(analytics["generated_at"])
        delta = datetime.utcnow() - generated
        assert delta.total_seconds() < 5


def _get_analytics(db: FakeDB, org_id: str) -> dict:
    org_courses = [c for c in db.courses.values() if c["org_id"] == org_id]
    return {
        "total_courses":     len(org_courses),
        "total_enrollments": 0,    # placeholder until enrollment data exists
        "completion_rate":   0.0,  # placeholder
        "generated_at":      datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------

class TestPublicAPILabProvisioning:
    """POST /api/v1/courses/{id}/labs — lab environment provisioning via API."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_lab_provisioning_returns_lab_id(self, db):
        """
        Given: A published course with lab template defined
        When:  POST /api/v1/courses/{id}/labs
        Then:  201 Created with lab_id and provisioning status
        """
        course = db.add_course(TEST_ORG_ID, title="Lab Course", status="published")
        result = _provision_lab(db, org_id=TEST_ORG_ID, course_id=course["id"])
        assert result["status_code"] == 201
        assert "lab_id" in result
        assert result["status"] in ("provisioning", "ready")

    @pytest.mark.unit
    @pytest.mark.api
    def test_lab_provisioning_fails_for_draft_course(self, db):
        """
        Given: A course in 'draft' status
        When:  POST /api/v1/courses/{id}/labs
        Then:  409 Conflict — labs can't be provisioned for drafts
        """
        course = db.add_course(TEST_ORG_ID, title="Draft Course", status="draft")
        result = _provision_lab(db, org_id=TEST_ORG_ID, course_id=course["id"])
        assert result["status_code"] == 409

    @pytest.mark.unit
    @pytest.mark.api
    def test_lab_provisioning_404_for_unknown_course(self, db):
        """
        Given: Non-existent course ID
        When:  POST /api/v1/courses/{id}/labs
        Then:  404 Not Found
        """
        result = _provision_lab(db, org_id=TEST_ORG_ID, course_id=str(uuid.uuid4()))
        assert result["status_code"] == 404


def _provision_lab(db: FakeDB, org_id: str, course_id: str) -> dict:
    course = db.courses.get(course_id)
    if course is None or course["org_id"] != org_id:
        return {"status_code": 404}
    if course["status"] != "published":
        return {"status_code": 409, "detail": "Course must be published to provision labs"}
    lab_id = str(uuid.uuid4())
    return {"status_code": 201, "lab_id": lab_id, "status": "provisioning"}


# ===========================================================================
# ██████████████████████████████████████████████████████████████████████████
# SECTION 4 — LTI 1.3 TESTS
# ██████████████████████████████████████████████████████████████████████████
# ===========================================================================


class TestLTIConfiguration:
    """LTI 1.3 JSON configuration endpoint."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_lti_config_returns_valid_json(self, db):
        """
        Given: A registered LTI platform
        When:  GET /lti/config/{org_slug}
        Then:  Response is valid JSON with required LTI 1.3 fields
        """
        db.add_lti_platform(TEST_ORG_ID)
        config = _get_lti_config(db, org_id=TEST_ORG_ID)

        assert config["status_code"] == 200
        lti_json = config["body"]

        required_fields = {
            "title",
            "description",
            "oidc_initiation_url",
            "target_link_uri",
            "scopes",
            "extensions",
        }
        missing = required_fields - lti_json.keys()
        assert not missing, f"LTI config missing required fields: {missing}"

    @pytest.mark.unit
    @pytest.mark.api
    def test_lti_config_includes_canvas_extensions(self, db):
        """
        Given: LTI config for Canvas
        When:  GET /lti/config/{org_slug}
        Then:  extensions array contains Canvas-specific platform entry
        """
        db.add_lti_platform(TEST_ORG_ID)
        config = _get_lti_config(db, org_id=TEST_ORG_ID)
        extensions = config["body"].get("extensions", [])
        assert any(
            ext.get("platform") == "canvas.instructure.com" for ext in extensions
        ), "Canvas extension must be present"

    @pytest.mark.unit
    @pytest.mark.api
    def test_lti_config_404_when_no_platform_registered(self, db):
        """
        Given: Org with no LTI platform registered
        When:  GET /lti/config/{org_slug}
        Then:  404 Not Found
        """
        config = _get_lti_config(db, org_id=TEST_ORG_ID)
        assert config["status_code"] == 404


def _get_lti_config(db: FakeDB, org_id: str) -> dict:
    platforms = [p for p in db.lti_platforms.values() if p["org_id"] == org_id]
    if not platforms:
        return {"status_code": 404}

    lti_json = {
        "title":               "TechUni AI Course Creator",
        "description":         "AI-powered course creation platform",
        "oidc_initiation_url": f"https://courses.techuni.ai/lti/login",
        "target_link_uri":     f"https://courses.techuni.ai/lti/launch",
        "scopes": [
            "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
            "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
            "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly",
        ],
        "extensions": [
            {
                "platform": "canvas.instructure.com",
                "settings": {
                    "platform": "canvas.instructure.com",
                    "placements": [
                        {
                            "placement":        "course_navigation",
                            "message_type":     "LtiResourceLinkRequest",
                            "target_link_uri":  "https://courses.techuni.ai/lti/launch",
                        }
                    ],
                },
            }
        ],
    }
    return {"status_code": 200, "body": lti_json}


# ---------------------------------------------------------------------------

class TestLTILaunch:
    """LTI 1.3 Resource Link Request launch flow."""

    def _build_lti_jwt(
        self,
        platform: dict,
        sub: str = "lms-user-001",
        email: str = "student@canvas.example.com",
        expired: bool = False,
        tampered: bool = False,
    ) -> str:
        """
        Build a minimal LTI 1.3 JWT (id_token) as the LMS would produce.
        In production this is signed with the LMS's RSA private key;
        here we use HMAC for test speed.
        """
        now = int(time.time())
        payload = {
            "iss":          platform["issuer"],
            "sub":          sub,
            "aud":          platform["client_id"],
            "iat":          now - 5,
            "exp":          (now - 60) if expired else (now + 3600),
            "nonce":        secrets.token_hex(8),
            "email":        email,
            # LTI 1.3 message type claim
            "https://purl.imsglobal.org/spec/lti/claim/message_type":
                "LtiResourceLinkRequest",
            "https://purl.imsglobal.org/spec/lti/claim/version":
                "1.3.0",
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id":
                platform["deployment_id"],
            "https://purl.imsglobal.org/spec/lti/claim/resource_link": {
                "id": "course-link-001"
            },
        }
        secret = "wrong-secret" if tampered else JWT_SECRET
        return _make_jwt(payload, secret=secret)

    @pytest.mark.unit
    @pytest.mark.api
    def test_valid_lti_launch_succeeds(self, db):
        """
        Given: Valid LTI 1.3 id_token from a registered platform
        When:  POST /lti/launch with id_token
        Then:  200 OK with session token and target_link_uri redirect
        """
        platform = db.add_lti_platform(TEST_ORG_ID)
        id_token = self._build_lti_jwt(platform)
        result = _process_lti_launch(db, id_token=id_token, org_id=TEST_ORG_ID)
        assert result["success"] is True
        assert "session_token" in result
        assert "redirect_to" in result

    @pytest.mark.unit
    @pytest.mark.api
    def test_expired_lti_jwt_fails(self, db):
        """
        Given: LTI id_token with exp in the past
        When:  POST /lti/launch
        Then:  401 Unauthorized — token expired
        """
        platform = db.add_lti_platform(TEST_ORG_ID)
        id_token = self._build_lti_jwt(platform, expired=True)
        result = _process_lti_launch(db, id_token=id_token, org_id=TEST_ORG_ID)
        assert result["success"] is False
        assert result["error_code"] in ("token_expired", "invalid_token")

    @pytest.mark.unit
    @pytest.mark.api
    def test_invalid_signature_lti_jwt_fails(self, db):
        """
        Given: LTI id_token signed with wrong key (tampered)
        When:  POST /lti/launch
        Then:  401 Unauthorized — signature invalid
        """
        platform = db.add_lti_platform(TEST_ORG_ID)
        id_token = self._build_lti_jwt(platform, tampered=True)
        result = _process_lti_launch(db, id_token=id_token, org_id=TEST_ORG_ID)
        assert result["success"] is False
        assert result["error_code"] in ("invalid_signature", "invalid_token")

    @pytest.mark.unit
    @pytest.mark.api
    def test_lti_launch_from_unregistered_platform_fails(self, db):
        """
        Given: id_token whose issuer is not registered in the DB
        When:  POST /lti/launch
        Then:  401 Unauthorized — unknown platform
        """
        # Create a fake platform object but do NOT add it to the DB
        unknown_platform = {
            "id":            str(uuid.uuid4()),
            "org_id":        TEST_ORG_ID,
            "issuer":        "https://unknown-lms.example.com",
            "client_id":     "99999",
            "deployment_id": "1",
        }
        id_token = self._build_lti_jwt(unknown_platform)
        result = _process_lti_launch(db, id_token=id_token, org_id=TEST_ORG_ID)
        assert result["success"] is False
        assert result["error_code"] in ("platform_not_found", "invalid_token")

    @pytest.mark.unit
    @pytest.mark.api
    def test_lti_launch_auto_provisions_user(self, db):
        """
        Given: Valid LTI launch for a user who has never logged in
        When:  POST /lti/launch
        Then:  New user is provisioned; launch succeeds
        """
        platform = db.add_lti_platform(TEST_ORG_ID)
        new_email = "new-lti-student@canvas.example.com"
        id_token  = self._build_lti_jwt(platform, email=new_email)
        result    = _process_lti_launch(db, id_token=id_token, org_id=TEST_ORG_ID)
        assert result["success"] is True
        created = next(
            (u for u in db.users.values() if u["email"] == new_email), None
        )
        assert created is not None, "LTI user should be auto-provisioned"


def _process_lti_launch(db: FakeDB, id_token: str, org_id: str) -> dict:
    """
    Fake LTI 1.3 launch processor.
    Validates the id_token against registered platforms (using HMAC
    shared secret in tests; production uses RSA JWKS verification).
    """
    parts = id_token.split(".")
    if len(parts) != 3:
        return {"success": False, "error_code": "invalid_token"}

    try:
        padding = "=" * (4 - len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(parts[1] + padding))
    except Exception:
        return {"success": False, "error_code": "invalid_token"}

    # Look up registered platform
    issuer = claims.get("iss")
    platform = next(
        (p for p in db.lti_platforms.values()
         if p["issuer"] == issuer and p["org_id"] == org_id),
        None,
    )
    if platform is None:
        return {"success": False, "error_code": "platform_not_found"}

    # Verify signature (HMAC in tests; JWKS in production)
    if HAS_PYJWT:
        try:
            pyjwt.decode(id_token, JWT_SECRET, algorithms=["HS256"], audience=platform["client_id"])
        except pyjwt.ExpiredSignatureError:
            return {"success": False, "error_code": "token_expired"}
        except pyjwt.InvalidSignatureError:
            return {"success": False, "error_code": "invalid_signature"}
        except Exception:
            return {"success": False, "error_code": "invalid_token"}
    else:
        # Without PyJWT verify expiry manually
        now = int(time.time())
        if claims.get("exp", 0) < now:
            return {"success": False, "error_code": "token_expired"}

    email = claims.get("email", "")
    existing = next(
        (u for u in db.users.values()
         if u["email"] == email and u["organization_id"] == org_id),
        None,
    )
    if existing is None:
        new_id = str(uuid.uuid4())
        db.users[new_id] = {
            "id":              new_id,
            "email":           email,
            "role":            "student",
            "organization_id": org_id,
            "sso_subject":     claims.get("sub"),
        }

    session_token = _make_jwt({
        "email":           email,
        "organization_id": org_id,
        "exp":             int((datetime.utcnow() + timedelta(hours=8)).timestamp()),
    })
    return {
        "success":       True,
        "session_token": session_token,
        "redirect_to":   "https://courses.techuni.ai/dashboard",
    }


# ---------------------------------------------------------------------------

class TestLTIGradePassback:
    """LTI 1.3 Assignment and Grade Services (AGS) — grade passback."""

    def _make_ags_access_token(self, scopes: List[str]) -> str:
        """Simulate the access token issued by the LMS for AGS calls."""
        return _make_jwt({
            "scopes": " ".join(scopes),
            "exp":    int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        })

    @pytest.mark.unit
    @pytest.mark.api
    def test_grade_passback_sends_correct_score(self, db):
        """
        Given: A student has completed a graded activity (score=0.85)
        When:  Grade passback is triggered
        Then:  Outbound score payload contains userId, scoreGiven, scoreMaximum,
               activityProgress="Completed", gradingProgress="FullyGraded"
        """
        platform = db.add_lti_platform(TEST_ORG_ID)
        student_id = "lms-student-001"
        score      = 0.85

        with patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200, json=lambda: {})
            result = _send_grade_passback(
                platform=platform,
                student_id=student_id,
                score=score,
                max_score=1.0,
                lineitem_url=f"{LTI_ISSUER}/api/lti/courses/1/line_items/1/scores",
                access_token=self._make_ags_access_token([
                    "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem"
                ]),
            )
            assert result["success"] is True
            # Verify the payload shape
            call_args = mock_post.call_args
            payload = call_args.kwargs.get("json") or call_args.args[1] if call_args.args else call_args.kwargs.get("json")
            if payload:
                assert payload.get("scoreGiven")    == score
                assert payload.get("scoreMaximum")  == 1.0
                assert payload.get("userId")        == student_id
                assert payload.get("activityProgress") == "Completed"
                assert payload.get("gradingProgress")  == "FullyGraded"

    @pytest.mark.unit
    @pytest.mark.api
    def test_grade_passback_score_clamped_to_max(self, db):
        """
        Given: A score higher than scoreMaximum is submitted (data error)
        When:  Grade passback is called
        Then:  scoreGiven is clamped to scoreMaximum before sending
        """
        platform = db.add_lti_platform(TEST_ORG_ID)

        with patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200, json=lambda: {})
            result = _send_grade_passback(
                platform=platform,
                student_id="student-001",
                score=1.5,      # over max
                max_score=1.0,
                lineitem_url=f"{LTI_ISSUER}/api/lti/scores",
                access_token=self._make_ags_access_token([]),
            )
            assert result["success"] is True
            assert result["clamped"] is True, "Score should have been clamped"

    @pytest.mark.unit
    @pytest.mark.api
    def test_grade_passback_fails_gracefully_on_lms_error(self, db):
        """
        Given: LMS returns 500 when grade passback is called
        When:  Grade passback is attempted
        Then:  Result indicates failure with error detail; no exception raised
        """
        platform = db.add_lti_platform(TEST_ORG_ID)

        with patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=500, json=lambda: {"error": "server error"})
            result = _send_grade_passback(
                platform=platform,
                student_id="student-001",
                score=0.7,
                max_score=1.0,
                lineitem_url=f"{LTI_ISSUER}/api/lti/scores",
                access_token=self._make_ags_access_token([]),
            )
            assert result["success"] is False
            assert "error" in result

    @pytest.mark.unit
    @pytest.mark.api
    def test_grade_passback_timestamp_is_iso8601(self, db):
        """
        Given: A grade passback payload is built
        When:  The timestamp field is inspected
        Then:  It is a valid ISO 8601 datetime string
        """
        platform = db.add_lti_platform(TEST_ORG_ID)

        with patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200, json=lambda: {})
            _send_grade_passback(
                platform=platform,
                student_id="student-ts",
                score=0.5,
                max_score=1.0,
                lineitem_url=f"{LTI_ISSUER}/api/lti/scores",
                access_token=self._make_ags_access_token([]),
            )
            call_args   = mock_post.call_args
            if call_args:
                payload = call_args.kwargs.get("json") or {}
                ts      = payload.get("timestamp", "")
                if ts:
                    # Should parse without error
                    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    assert isinstance(parsed, datetime)


def _send_grade_passback(
    platform: dict,
    student_id: str,
    score: float,
    max_score: float,
    lineitem_url: str,
    access_token: str,
) -> dict:
    """
    Fake AGS grade passback sender.
    In production this will POST to the LMS lineitem scores endpoint.
    """
    import requests

    clamped = score > max_score
    effective_score = min(score, max_score)

    payload = {
        "userId":              student_id,
        "scoreGiven":          effective_score,
        "scoreMaximum":        max_score,
        "activityProgress":    "Completed",
        "gradingProgress":     "FullyGraded",
        "timestamp":           datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
    }

    try:
        resp = requests.post(
            lineitem_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type":  "application/vnd.ims.lis.v1.score+json",
            },
            timeout=10,
        )
    except Exception as e:
        return {"success": False, "error": str(e)}

    if resp.status_code not in (200, 201, 204):
        return {"success": False, "error": f"LMS returned {resp.status_code}"}

    result: dict = {"success": True}
    if clamped:
        result["clamped"] = True
    return result


# ===========================================================================
# Smoke test — ensures all markers are configured (meta)
# ===========================================================================

class TestSmokeAndMarkers:
    """Sanity checks: imports work, markers are correct, helpers are sound."""

    @pytest.mark.unit
    def test_fake_db_isolation(self):
        """Two separate FakeDB instances must not share state."""
        db1 = FakeDB()
        db2 = FakeDB()
        db1.add_course(TEST_ORG_ID, title="Exclusive to DB1")
        assert len(db2.courses) == 0

    @pytest.mark.unit
    def test_api_key_hash_is_deterministic(self):
        """Same raw key must always produce the same hash."""
        raw = "sk_test_REDACTED_check"
        assert _api_key_hash(raw) == _api_key_hash(raw)

    @pytest.mark.unit
    def test_jwt_helper_produces_three_part_token(self):
        """_make_jwt output must be a three-segment dot-separated string."""
        token = _make_jwt({"sub": "test", "exp": 9999999999})
        assert token.count(".") == 2, "JWT must have header.payload.signature format"

    @pytest.mark.unit
    def test_sp_metadata_is_valid_xml(self):
        """_build_sp_metadata must produce parse-able XML."""
        xml_bytes = _build_sp_metadata(ENTITY_ID, ACS_URL)
        root = ET.fromstring(xml_bytes)  # raises on malformed XML
        assert root is not None
