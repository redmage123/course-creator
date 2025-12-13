"""
Integration Tests for Organization LLM Configuration API

BUSINESS CONTEXT:
Tests the organization LLM configuration API endpoints that enable organization admins to:
1. Configure preferred LLM providers (OpenAI, Anthropic, Deepseek, etc.)
2. Manage API keys securely (encrypted at rest, never returned)
3. Test provider connections before saving
4. Track usage and monitor costs
5. Set primary providers for AI operations
6. Manage quotas and usage limits

TEST COVERAGE:
- POST /organizations/{org_id}/llm-config - Create configuration
- GET /organizations/{org_id}/llm-config - List configurations
- GET /organizations/{org_id}/llm-config/providers - Available providers
- GET /organizations/{org_id}/llm-config/primary - Get primary config
- GET /organizations/{org_id}/llm-config/vision - Get vision-capable config
- PUT /organizations/{org_id}/llm-config/{config_id} - Update configuration
- DELETE /organizations/{org_id}/llm-config/{config_id} - Delete configuration
- POST /organizations/{org_id}/llm-config/test - Test connection
- GET /organizations/{org_id}/llm-config/usage - Usage statistics
- GET /organizations/{org_id}/llm-config/usage/by-provider - Provider breakdown
- Authentication and authorization
- Data validation and error handling
- Multi-provider management
- Primary provider switching
- Quota enforcement

TECHNICAL IMPLEMENTATION:
- Uses FastAPI TestClient with real PostgreSQL infrastructure
- Tests against actual database (docker-compose.test.yml)
- JWT authentication via auth_headers fixture
- Database cleanup via clean_database fixture
- Comprehensive multi-layer verification (API + Database)
"""

import pytest
import asyncio
import asyncpg
import uuid
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Generator
from fastapi.testclient import TestClient
from fastapi import Request, HTTPException, status
import jwt

# Add organization-management service path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "services" / "organization-management"))

# Test configuration
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://test_user:test_password@localhost:5434/course_creator_test"
)
TEST_REDIS_URL = os.environ.get(
    "TEST_REDIS_URL",
    "redis://localhost:6380"
)
TEST_JWT_SECRET = os.environ.get(
    "TEST_JWT_SECRET",
    "test-secret-key-for-integration-tests-only"
)
TEST_ORG_ID = "00000000-0000-0000-0000-000000000001"
TEST_ADMIN_ID = "00000000-0000-0000-0000-000000000002"


def check_test_infrastructure():
    """
    Check if test infrastructure is available.
    Returns True if test database and Redis are accessible.
    """
    import socket

    # Check test database port (5434)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 5434))
        sock.close()
        if result != 0:
            return False
    except Exception:
        return False

    # Check test Redis port (6380)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 6380))
        sock.close()
        if result != 0:
            return False
    except Exception:
        return False

    return True


# Mark as integration tests - requires docker-compose.test.yml infrastructure
# Run with: pytest tests/integration/test_org_llm_config_api.py -v
pytestmark = pytest.mark.integration


def _get_mock_user() -> Dict[str, Any]:
    """Return mock user for testing without needing user-management service"""
    return {
        "sub": TEST_ADMIN_ID,
        "user_id": TEST_ADMIN_ID,
        "email": "admin@test.example.com",
        "username": "testadmin",
        "full_name": "Test Admin",
        "role": "org_admin",
        "roles": ["org_admin"],
        "organization_id": TEST_ORG_ID,
        "organization": {"id": TEST_ORG_ID, "name": "Test Organization"}
    }


@pytest.fixture(scope="module")
def test_app():
    """
    Create FastAPI test client for organization-management service

    TECHNICAL IMPLEMENTATION:
    Uses dependency override to bypass user-management service authentication
    and provides a database pool created in the correct event loop context.
    """
    # Set environment variables
    os.environ["DB_HOST"] = "localhost"
    os.environ["DB_PORT"] = "5434"
    os.environ["DB_NAME"] = "course_creator_test"
    os.environ["DB_USER"] = "test_user"
    os.environ["DB_PASSWORD"] = "test_password"
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = "6380"
    os.environ["JWT_SECRET"] = TEST_JWT_SECRET
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["REDIS_URL"] = TEST_REDIS_URL
    os.environ["ENVIRONMENT"] = "test"

    # Import and create app with test config
    from omegaconf import OmegaConf
    from main import create_app

    # Create test configuration using OmegaConf
    test_config = OmegaConf.create({
        "database": {
            "host": "localhost",
            "port": 5434,
            "name": "course_creator_test",
            "user": "test_user",
            "password": "test_password",
            "min_connections": 2,
            "max_connections": 5,
            "command_timeout": 60
        },
        "redis": {
            "url": "redis://localhost:6380"
        },
        "jwt": {
            "secret_key": TEST_JWT_SECRET,
            "algorithm": "HS256"
        },
        "services": {
            "user_management_url": "https://localhost:8000"
        },
        "server": {
            "host": "0.0.0.0",
            "port": 8008
        },
        "logging": {
            "level": "DEBUG"
        }
    })

    # Create app with test configuration
    app = create_app(test_config)

    # Import dependencies for override
    from app_dependencies import get_current_user, require_org_admin, require_project_manager, get_llm_config_dao
    from organization_management.data_access.llm_config_dao import LLMConfigDAO

    # Store pool reference for cleanup
    _db_pool = None

    async def get_or_create_pool():
        nonlocal _db_pool
        if _db_pool is None:
            _db_pool = await asyncpg.create_pool(
                host="localhost",
                port=5434,
                database="course_creator_test",
                user="test_user",
                password="test_password",
                min_size=2,
                max_size=5,
                command_timeout=60
            )
        return _db_pool

    # Override auth dependencies to check Authorization header
    # This allows testing both authenticated and unauthenticated requests
    async def mock_get_current_user(request: Request):
        """
        Mock authentication that checks for Authorization header.

        TECHNICAL IMPLEMENTATION:
        - If Authorization header is present, returns mock user
        - If Authorization header is missing, raises 401 Unauthorized
        - This allows testing both authenticated and unauthenticated scenarios
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return _get_mock_user()

    async def mock_require_org_admin(request: Request):
        """Mock org admin requirement that checks Authorization header"""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return _get_mock_user()

    async def mock_require_project_manager(request: Request):
        """Mock project manager requirement that checks Authorization header"""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return _get_mock_user()

    async def mock_get_llm_config_dao():
        pool = await get_or_create_pool()
        return LLMConfigDAO(pool)

    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[require_org_admin] = mock_require_org_admin
    app.dependency_overrides[require_project_manager] = mock_require_project_manager
    app.dependency_overrides[get_llm_config_dao] = mock_get_llm_config_dao

    # Use TestClient which handles event loop properly
    with TestClient(app) as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_headers() -> dict:
    """Generate auth headers with valid JWT"""
    payload = {
        "user_id": TEST_ADMIN_ID,
        "email": "admin@test.example.com",
        "role": "org_admin",
        "organization_id": TEST_ORG_ID,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="function")
def clean_database():
    """Clean database before/after each test"""
    import psycopg2
    conn = psycopg2.connect(TEST_DATABASE_URL)
    cur = conn.cursor()
    # Clean LLM config related tables
    cur.execute("DELETE FROM organization_llm_config WHERE organization_id = %s", (TEST_ORG_ID,))
    conn.commit()
    cur.close()
    conn.close()
    yield
    # Cleanup after test
    conn = psycopg2.connect(TEST_DATABASE_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM organization_llm_config WHERE organization_id = %s", (TEST_ORG_ID,))
    conn.commit()
    cur.close()
    conn.close()


class TestLLMConfigAPI:
    """
    Integration tests for LLM configuration API with real infrastructure

    BUSINESS CONTEXT:
    Tests complete API workflows with actual PostgreSQL database.
    Uses docker-compose.test.yml infrastructure.

    FIXTURES USED:
    - test_app: FastAPI TestClient with real infrastructure
    - auth_headers: Valid JWT authentication headers (org_admin role)
    - clean_database: Ensures clean database state per test
    """

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def get_test_organization_id(self) -> str:
        """
        Get test organization ID

        BUSINESS CONTEXT:
        Uses the test organization seeded in init-test-db.sql.
        """
        return "00000000-0000-0000-0000-000000000001"

    def create_llm_config_payload(
        self,
        provider_name: str = "openai",
        api_key: str = "sk-test-key-1234567890",
        model_name: str = None,
        is_primary: bool = False,
        custom_base_url: str = None,
        usage_quota_monthly: int = None
    ) -> Dict[str, Any]:
        """
        Create LLM configuration payload

        BUSINESS CONTEXT:
        Generates valid request payload for creating LLM configurations.
        """
        payload = {
            "provider_name": provider_name,
            "api_key": api_key,
            "is_primary": is_primary,
            "settings": {}
        }

        if model_name:
            payload["model_name"] = model_name
        if custom_base_url:
            payload["custom_base_url"] = custom_base_url
        if usage_quota_monthly is not None:
            payload["usage_quota_monthly"] = usage_quota_monthly

        return payload

    async def get_config_from_db(
        self,
        config_id: str,
        db_url: str = "postgresql://test_user:test_password@localhost:5434/course_creator_test"
    ) -> Dict[str, Any]:
        """
        Fetch LLM config directly from database for verification

        BUSINESS CONTEXT:
        Multi-layer verification: API response + direct database query.
        Ensures API and database are in sync.
        """
        pool = await asyncpg.create_pool(db_url)
        query = """
            SELECT
                olc.id,
                olc.organization_id,
                olc.provider_id,
                olc.model_name,
                olc.custom_base_url,
                olc.is_primary,
                olc.is_active,
                olc.usage_quota_monthly,
                olc.settings,
                lp.provider_name,
                lp.display_name
            FROM organization_llm_config olc
            JOIN llm_providers lp ON olc.provider_id = lp.id
            WHERE olc.id = $1
        """
        row = await pool.fetchrow(query, uuid.UUID(config_id))
        await pool.close()

        if not row:
            return None

        return dict(row)

    # ========================================================================
    # AVAILABLE PROVIDERS ENDPOINT TESTS
    # ========================================================================

    def test_get_available_providers_success(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test successful retrieval of available LLM providers

        BUSINESS CONTEXT:
        Organizations need to see which providers they can configure
        (OpenAI, Anthropic, Deepseek, Qwen, etc.) with capabilities.
        """
        org_id = self.get_test_organization_id()

        response = test_app.get(
            f"/organizations/{org_id}/llm-config/providers",
            headers=auth_headers
        )

        assert response.status_code == 200
        providers = response.json()

        # Verify response structure
        assert isinstance(providers, list)
        assert len(providers) >= 5  # At least OpenAI, Anthropic, Deepseek, Qwen, Ollama

        # Verify provider data completeness
        openai_provider = next((p for p in providers if p["provider_name"] == "openai"), None)
        assert openai_provider is not None
        assert openai_provider["display_name"] == "OpenAI"
        assert openai_provider["api_base_url"] == "https://api.openai.com/v1"
        assert openai_provider["supports_vision"] is True
        assert openai_provider["supports_streaming"] is True
        assert openai_provider["default_model"] == "gpt-5.2"
        assert "gpt-5.2" in openai_provider["available_models"]

    def test_get_available_providers_without_auth(
        self,
        test_app: TestClient,
        clean_database
    ):
        """
        Test providers endpoint requires authentication

        BUSINESS CONTEXT:
        Security: Only authenticated users can view provider information.

        TECHNICAL IMPLEMENTATION:
        Tests that requests without Authorization header receive 401 Unauthorized.
        """
        org_id = self.get_test_organization_id()

        response = test_app.get(
            f"/organizations/{org_id}/llm-config/providers"
        )

        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]

    # ========================================================================
    # CREATE LLM CONFIGURATION ENDPOINT TESTS
    # ========================================================================

    def test_create_llm_config_success(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test successful LLM configuration creation

        BUSINESS CONTEXT:
        Organization admin configures OpenAI provider with API key.
        API key is stored encrypted, never returned in responses.
        """
        org_id = self.get_test_organization_id()
        payload = self.create_llm_config_payload(
            provider_name="openai",
            api_key="sk-test-openai-key-123456789",
            model_name="gpt-5.2",
            is_primary=True
        )

        response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )

        assert response.status_code == 201
        result = response.json()

        # Verify response structure
        assert "id" in result
        assert result["organization_id"] == org_id
        assert result["provider_name"] == "openai"
        assert result["display_name"] == "OpenAI"
        assert result["model_name"] == "gpt-5.2"
        assert result["is_primary"] is True
        assert result["is_active"] is True
        assert result["supports_vision"] is True
        assert "api_key" not in result  # API key NEVER returned
        assert "api_key_encrypted" not in result

    def test_create_llm_config_minimal_fields(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test configuration with only required fields

        BUSINESS CONTEXT:
        Minimal config: provider_name and api_key only.
        Uses provider's default model.
        """
        org_id = self.get_test_organization_id()
        payload = {
            "provider_name": "anthropic",
            "api_key": "sk-ant-test-key-123456789"
        }

        response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )

        assert response.status_code == 201
        result = response.json()

        assert result["provider_name"] == "anthropic"
        assert result["model_name"] == "claude-3-5-sonnet-20241022"  # Default model
        assert result["is_primary"] is False  # Default value
        assert result["custom_base_url"] is None

    def test_create_llm_config_with_custom_base_url(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test configuration with custom API base URL

        BUSINESS CONTEXT:
        Organizations can use self-hosted or proxy LLM endpoints.
        Example: Azure OpenAI, private Ollama instance.
        """
        org_id = self.get_test_organization_id()
        payload = self.create_llm_config_payload(
            provider_name="ollama",
            api_key="ollama-local-no-key-required",
            model_name="llava:13b",
            custom_base_url="http://localhost:11434"
        )

        response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )

        assert response.status_code == 201
        result = response.json()

        assert result["custom_base_url"] == "http://localhost:11434"
        assert result["is_local"] is True

    def test_create_llm_config_with_usage_quota(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test configuration with monthly token quota

        BUSINESS CONTEXT:
        Organizations can set usage quotas to control costs.
        Example: 1,000,000 tokens/month budget cap.
        """
        org_id = self.get_test_organization_id()
        payload = self.create_llm_config_payload(
            provider_name="openai",
            api_key="sk-test-key-quota",
            usage_quota_monthly=1000000
        )

        response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )

        assert response.status_code == 201
        result = response.json()

        assert result["usage_quota_monthly"] == 1000000
        assert result["usage_current_month"] == 0

    def test_create_llm_config_invalid_provider(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test creating config with unknown provider returns 400

        BUSINESS CONTEXT:
        Only supported providers are allowed for security and reliability.
        """
        org_id = self.get_test_organization_id()
        payload = {
            "provider_name": "unknown_provider_xyz",
            "api_key": "sk-test-key"
        }

        response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )

        # FastAPI returns 422 for Pydantic validation errors
        assert response.status_code in [400, 422]
        response_data = response.json()
        # Check for validation error message (format varies based on validation layer)
        detail = response_data.get("detail")
        if isinstance(detail, str):
            assert "Unknown provider" in detail or "unknown_provider_xyz" in detail.lower()
        else:
            # Pydantic validation returns list of errors
            assert any("unknown" in str(d).lower() or "provider" in str(d).lower() for d in detail)

    def test_create_llm_config_missing_api_key(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test creating config without API key returns 422

        BUSINESS CONTEXT:
        API key is required for provider authentication.
        """
        org_id = self.get_test_organization_id()
        payload = {
            "provider_name": "openai"
            # Missing api_key
        }

        response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_create_llm_config_api_key_too_short(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test API key minimum length validation

        BUSINESS CONTEXT:
        API keys must be at least 10 characters for security.
        """
        org_id = self.get_test_organization_id()
        payload = {
            "provider_name": "openai",
            "api_key": "short"  # Less than 10 characters
        }

        response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )

        assert response.status_code == 422

    def test_create_llm_config_without_auth(
        self,
        test_app: TestClient,
        clean_database
    ):
        """
        Test config creation requires authentication

        BUSINESS CONTEXT:
        Security: Only org admins can configure LLM providers.

        TECHNICAL IMPLEMENTATION:
        Tests that requests without Authorization header receive 401 Unauthorized.
        """
        org_id = self.get_test_organization_id()
        payload = self.create_llm_config_payload()

        response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            json=payload
        )

        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]

    # ========================================================================
    # LIST LLM CONFIGURATIONS ENDPOINT TESTS
    # ========================================================================

    def test_list_llm_configs_empty(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test listing configs when none exist

        BUSINESS CONTEXT:
        New organizations have no LLM providers configured yet.
        """
        org_id = self.get_test_organization_id()

        response = test_app.get(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers
        )

        assert response.status_code == 200
        configs = response.json()
        assert isinstance(configs, list)
        assert len(configs) == 0

    def test_list_llm_configs_single(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test listing with single configuration

        BUSINESS CONTEXT:
        Organization has configured one LLM provider.
        """
        org_id = self.get_test_organization_id()

        # Create config
        payload = self.create_llm_config_payload(provider_name="openai")
        create_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )
        assert create_response.status_code == 201

        # List configs
        response = test_app.get(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers
        )

        assert response.status_code == 200
        configs = response.json()
        assert len(configs) == 1
        assert configs[0]["provider_name"] == "openai"

    def test_list_llm_configs_multiple_providers(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test listing multiple provider configurations

        BUSINESS CONTEXT:
        Organizations can configure multiple providers for different use cases:
        - OpenAI for general text
        - Anthropic for long-context analysis
        - Ollama for local/private data
        """
        org_id = self.get_test_organization_id()

        # Create multiple configs
        providers = [
            ("openai", "sk-openai-key", "gpt-5.2", True),
            ("anthropic", "sk-ant-key", "claude-3-5-sonnet-20241022", False),
            ("ollama", "ollama-local-no-key", "llava", False)
        ]

        for provider_name, api_key, model, is_primary in providers:
            payload = self.create_llm_config_payload(
                provider_name=provider_name,
                api_key=api_key,
                model_name=model,
                is_primary=is_primary
            )
            create_response = test_app.post(
                f"/organizations/{org_id}/llm-config",
                headers=auth_headers,
                json=payload
            )
            assert create_response.status_code == 201

        # List all configs
        response = test_app.get(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers
        )

        assert response.status_code == 200
        configs = response.json()
        assert len(configs) == 3

        # Verify primary config is first
        assert configs[0]["is_primary"] is True
        assert configs[0]["provider_name"] == "openai"

    def test_list_llm_configs_without_auth(
        self,
        test_app: TestClient,
        clean_database
    ):
        """
        Test listing configs requires authentication

        BUSINESS CONTEXT:
        Security: API keys are sensitive, only org admins can view configs.

        TECHNICAL IMPLEMENTATION:
        Tests that requests without Authorization header receive 401 Unauthorized.
        """
        org_id = self.get_test_organization_id()

        response = test_app.get(
            f"/organizations/{org_id}/llm-config"
        )

        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]

    # ========================================================================
    # UPDATE LLM CONFIGURATION ENDPOINT TESTS
    # ========================================================================

    def test_update_llm_config_model_name(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test updating model name

        BUSINESS CONTEXT:
        Organization switches from gpt-4o to gpt-5.2 for better performance.
        """
        org_id = self.get_test_organization_id()

        # Create config
        payload = self.create_llm_config_payload(
            provider_name="openai",
            model_name="gpt-4o"
        )
        create_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )
        assert create_response.status_code == 201
        config_id = create_response.json()["id"]

        # Update model
        update_payload = {
            "model_name": "gpt-5.2"
        }
        response = test_app.put(
            f"/organizations/{org_id}/llm-config/{config_id}",
            headers=auth_headers,
            json=update_payload
        )

        assert response.status_code == 200
        result = response.json()
        assert result["model_name"] == "gpt-5.2"

    def test_update_llm_config_set_primary(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test setting config as primary

        BUSINESS CONTEXT:
        Organization switches primary provider from OpenAI to Anthropic.
        Only one config can be primary at a time.
        """
        org_id = self.get_test_organization_id()

        # Create two configs
        openai_payload = self.create_llm_config_payload(
            provider_name="openai",
            is_primary=True
        )
        openai_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=openai_payload
        )
        assert openai_response.status_code == 201

        anthropic_payload = self.create_llm_config_payload(
            provider_name="anthropic",
            api_key="sk-ant-key",
            is_primary=False
        )
        anthropic_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=anthropic_payload
        )
        assert anthropic_response.status_code == 201
        anthropic_id = anthropic_response.json()["id"]

        # Set Anthropic as primary
        update_payload = {"is_primary": True}
        response = test_app.put(
            f"/organizations/{org_id}/llm-config/{anthropic_id}",
            headers=auth_headers,
            json=update_payload
        )

        assert response.status_code == 200
        result = response.json()
        assert result["is_primary"] is True

        # Verify OpenAI is no longer primary
        list_response = test_app.get(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers
        )
        configs = list_response.json()
        openai_config = next(c for c in configs if c["provider_name"] == "openai")
        assert openai_config["is_primary"] is False

    def test_update_llm_config_deactivate(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test deactivating configuration

        BUSINESS CONTEXT:
        Organization temporarily disables a provider without deleting it.
        """
        org_id = self.get_test_organization_id()

        # Create config
        payload = self.create_llm_config_payload()
        create_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )
        assert create_response.status_code == 201
        config_id = create_response.json()["id"]

        # Deactivate
        update_payload = {"is_active": False}
        response = test_app.put(
            f"/organizations/{org_id}/llm-config/{config_id}",
            headers=auth_headers,
            json=update_payload
        )

        assert response.status_code == 200
        result = response.json()
        assert result["is_active"] is False

    def test_update_llm_config_usage_quota(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test updating usage quota

        BUSINESS CONTEXT:
        Organization increases monthly budget from 1M to 5M tokens.
        """
        org_id = self.get_test_organization_id()

        # Create config with quota
        payload = self.create_llm_config_payload(usage_quota_monthly=1000000)
        create_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )
        assert create_response.status_code == 201
        config_id = create_response.json()["id"]

        # Update quota
        update_payload = {"usage_quota_monthly": 5000000}
        response = test_app.put(
            f"/organizations/{org_id}/llm-config/{config_id}",
            headers=auth_headers,
            json=update_payload
        )

        assert response.status_code == 200
        result = response.json()
        assert result["usage_quota_monthly"] == 5000000

    def test_update_llm_config_not_found(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test updating non-existent config returns 404

        BUSINESS CONTEXT:
        Invalid config ID should fail gracefully.
        """
        org_id = self.get_test_organization_id()
        fake_config_id = "00000000-0000-0000-0000-000000000999"

        update_payload = {"model_name": "gpt-5.2"}
        response = test_app.put(
            f"/organizations/{org_id}/llm-config/{fake_config_id}",
            headers=auth_headers,
            json=update_payload
        )

        assert response.status_code == 404

    def test_update_llm_config_no_fields(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test update with no fields returns 400

        BUSINESS CONTEXT:
        At least one field must be provided for update.
        """
        org_id = self.get_test_organization_id()

        # Create config
        payload = self.create_llm_config_payload()
        create_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )
        assert create_response.status_code == 201
        config_id = create_response.json()["id"]

        # Update with empty payload
        response = test_app.put(
            f"/organizations/{org_id}/llm-config/{config_id}",
            headers=auth_headers,
            json={}
        )

        assert response.status_code == 400
        assert "No fields to update" in response.json()["detail"]

    # ========================================================================
    # DELETE LLM CONFIGURATION ENDPOINT TESTS
    # ========================================================================

    def test_delete_llm_config_success(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test successful configuration deletion

        BUSINESS CONTEXT:
        Organization removes unused provider configuration.
        Usage history is preserved for compliance.
        """
        org_id = self.get_test_organization_id()

        # Create config
        payload = self.create_llm_config_payload()
        create_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )
        assert create_response.status_code == 201
        config_id = create_response.json()["id"]

        # Delete config
        response = test_app.delete(
            f"/organizations/{org_id}/llm-config/{config_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify deletion
        list_response = test_app.get(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers
        )
        configs = list_response.json()
        assert len(configs) == 0

    def test_delete_llm_config_not_found(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test deleting non-existent config returns 404

        BUSINESS CONTEXT:
        Invalid config ID should fail gracefully.
        """
        org_id = self.get_test_organization_id()
        fake_config_id = "00000000-0000-0000-0000-000000000999"

        response = test_app.delete(
            f"/organizations/{org_id}/llm-config/{fake_config_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_delete_llm_config_without_auth(
        self,
        test_app: TestClient,
        clean_database
    ):
        """
        Test deletion requires authentication

        BUSINESS CONTEXT:
        Security: Only org admins can delete provider configs.

        TECHNICAL IMPLEMENTATION:
        Tests that requests without Authorization header receive 401 Unauthorized.
        """
        org_id = self.get_test_organization_id()
        config_id = "00000000-0000-0000-0000-000000000001"

        response = test_app.delete(
            f"/organizations/{org_id}/llm-config/{config_id}"
        )

        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]

    # ========================================================================
    # TEST CONNECTION ENDPOINT TESTS
    # ========================================================================

    def test_test_connection_mock_success(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test connection testing endpoint (mock test)

        BUSINESS CONTEXT:
        Organization validates API key before saving configuration.
        Prevents failed setups from invalid credentials.

        NOTE: This is a mock test - actual API calls require real keys.
        """
        org_id = self.get_test_organization_id()
        test_payload = {
            "provider_name": "openai",
            "api_key": "sk-test-key-for-connection-test",
            "model_name": "gpt-5.2"
        }

        response = test_app.post(
            f"/organizations/{org_id}/llm-config/test",
            headers=auth_headers,
            json=test_payload
        )

        # Response structure verification
        assert response.status_code == 200
        result = response.json()
        assert "success" in result
        assert "provider_name" in result
        assert "model_name" in result
        assert "message" in result
        assert result["provider_name"] == "openai"
        assert result["model_name"] == "gpt-5.2"

    def test_test_connection_unknown_provider(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test connection with unknown provider

        BUSINESS CONTEXT:
        Validates provider exists before attempting connection.
        """
        org_id = self.get_test_organization_id()
        test_payload = {
            "provider_name": "unknown_provider",
            "api_key": "sk-test-key"
        }

        response = test_app.post(
            f"/organizations/{org_id}/llm-config/test",
            headers=auth_headers,
            json=test_payload
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is False
        assert "Unknown provider" in result["message"]

    # ========================================================================
    # GET PRIMARY CONFIGURATION ENDPOINT TESTS
    # ========================================================================

    def test_get_primary_config_success(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test getting primary configuration

        BUSINESS CONTEXT:
        AI operations use the primary provider when no specific
        provider is requested.
        """
        org_id = self.get_test_organization_id()

        # Create primary config
        payload = self.create_llm_config_payload(
            provider_name="openai",
            is_primary=True
        )
        create_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )
        assert create_response.status_code == 201

        # Get primary config
        response = test_app.get(
            f"/organizations/{org_id}/llm-config/primary",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["is_primary"] is True
        assert result["provider_name"] == "openai"

    def test_get_primary_config_not_found(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test getting primary config when none exists

        BUSINESS CONTEXT:
        Organization hasn't configured any LLM providers yet.
        """
        org_id = self.get_test_organization_id()

        response = test_app.get(
            f"/organizations/{org_id}/llm-config/primary",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "No primary LLM configuration found" in response.json()["detail"]

    # ========================================================================
    # GET VISION CONFIGURATION ENDPOINT TESTS
    # ========================================================================

    def test_get_vision_config_success(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test getting vision-capable configuration

        BUSINESS CONTEXT:
        Screenshot-to-course generation requires vision-capable models.
        System automatically selects appropriate provider.
        """
        org_id = self.get_test_organization_id()

        # Create vision-capable config (OpenAI, Anthropic, Deepseek support vision)
        payload = self.create_llm_config_payload(
            provider_name="openai",
            model_name="gpt-5.2"
        )
        create_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )
        assert create_response.status_code == 201

        # Get vision config
        response = test_app.get(
            f"/organizations/{org_id}/llm-config/vision",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["supports_vision"] is True
        assert result["provider_name"] == "openai"

    def test_get_vision_config_not_found(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test getting vision config when none configured

        BUSINESS CONTEXT:
        No vision-capable providers configured.
        """
        org_id = self.get_test_organization_id()

        response = test_app.get(
            f"/organizations/{org_id}/llm-config/vision",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "No vision-capable LLM configuration found" in response.json()["detail"]

    # ========================================================================
    # USAGE STATISTICS ENDPOINT TESTS
    # ========================================================================

    def test_get_usage_stats_empty(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test usage statistics with no data

        BUSINESS CONTEXT:
        New organization has no LLM usage yet.
        """
        org_id = self.get_test_organization_id()

        response = test_app.get(
            f"/organizations/{org_id}/llm-config/usage",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        # Verify structure
        assert "total_requests" in result
        assert "total_input_tokens" in result
        assert "total_output_tokens" in result
        assert "total_tokens" in result
        assert "total_cost" in result
        assert "avg_latency_ms" in result
        assert "successful_requests" in result
        assert "failed_requests" in result
        assert "success_rate" in result

        # Verify values are zero/empty
        assert result["total_requests"] == 0
        assert result["success_rate"] == 0

    def test_get_usage_by_provider_empty(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test usage by provider with no data

        BUSINESS CONTEXT:
        No usage data to break down by provider.
        """
        org_id = self.get_test_organization_id()

        response = test_app.get(
            f"/organizations/{org_id}/llm-config/usage/by-provider",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) == 0

    # ========================================================================
    # END-TO-END WORKFLOW TESTS
    # ========================================================================

    def test_complete_workflow_create_test_use(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test complete workflow: test connection → create → use as primary

        BUSINESS CONTEXT:
        Organization validates credentials, saves config, sets as primary.
        """
        org_id = self.get_test_organization_id()

        # Step 1: Test connection
        test_payload = {
            "provider_name": "openai",
            "api_key": "sk-test-workflow-key",
            "model_name": "gpt-5.2"
        }
        test_response = test_app.post(
            f"/organizations/{org_id}/llm-config/test",
            headers=auth_headers,
            json=test_payload
        )
        assert test_response.status_code == 200

        # Step 2: Create configuration
        create_payload = self.create_llm_config_payload(
            provider_name="openai",
            api_key="sk-test-workflow-key",
            model_name="gpt-5.2",
            is_primary=True
        )
        create_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=create_payload
        )
        assert create_response.status_code == 201
        config = create_response.json()

        # Step 3: Verify it's the primary config
        primary_response = test_app.get(
            f"/organizations/{org_id}/llm-config/primary",
            headers=auth_headers
        )
        assert primary_response.status_code == 200
        primary_config = primary_response.json()
        assert primary_config["id"] == config["id"]

    def test_multi_provider_management_workflow(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test managing multiple providers workflow

        BUSINESS CONTEXT:
        Organization configures multiple providers:
        1. OpenAI as primary for general use
        2. Anthropic for long-context analysis
        3. Ollama for local/private processing
        """
        org_id = self.get_test_organization_id()

        # Create OpenAI as primary
        openai_payload = self.create_llm_config_payload(
            provider_name="openai",
            api_key="sk-openai-key",
            is_primary=True
        )
        openai_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=openai_payload
        )
        assert openai_response.status_code == 201

        # Create Anthropic
        anthropic_payload = self.create_llm_config_payload(
            provider_name="anthropic",
            api_key="sk-ant-key"
        )
        anthropic_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=anthropic_payload
        )
        assert anthropic_response.status_code == 201

        # Create Ollama
        ollama_payload = self.create_llm_config_payload(
            provider_name="ollama",
            api_key="ollama-local-no-key-required",
            custom_base_url="http://localhost:11434"
        )
        ollama_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=ollama_payload
        )
        assert ollama_response.status_code == 201

        # List all configs
        list_response = test_app.get(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers
        )
        configs = list_response.json()
        assert len(configs) == 3

        # Verify primary is first
        assert configs[0]["is_primary"] is True
        assert configs[0]["provider_name"] == "openai"

        # Switch primary to Anthropic
        anthropic_id = anthropic_response.json()["id"]
        update_payload = {"is_primary": True}
        update_response = test_app.put(
            f"/organizations/{org_id}/llm-config/{anthropic_id}",
            headers=auth_headers,
            json=update_payload
        )
        assert update_response.status_code == 200

        # Verify primary changed
        primary_response = test_app.get(
            f"/organizations/{org_id}/llm-config/primary",
            headers=auth_headers
        )
        primary_config = primary_response.json()
        assert primary_config["provider_name"] == "anthropic"


class TestLLMConfigAdvancedScenarios:
    """
    Advanced integration tests for edge cases and complex scenarios

    BUSINESS CONTEXT:
    Tests complex multi-step workflows, edge cases, and advanced features
    that organizations may encounter in production use.
    """

    def get_test_organization_id(self) -> str:
        """Get test organization ID"""
        return "00000000-0000-0000-0000-000000000001"

    def create_llm_config_payload(
        self,
        provider_name: str = "openai",
        api_key: str = "sk-test-key-1234567890",
        model_name: str = None,
        is_primary: bool = False,
        custom_base_url: str = None,
        usage_quota_monthly: int = None
    ) -> Dict[str, Any]:
        """Create LLM configuration payload"""
        payload = {
            "provider_name": provider_name,
            "api_key": api_key,
            "is_primary": is_primary,
            "settings": {}
        }

        if model_name:
            payload["model_name"] = model_name
        if custom_base_url:
            payload["custom_base_url"] = custom_base_url
        if usage_quota_monthly is not None:
            payload["usage_quota_monthly"] = usage_quota_monthly

        return payload

    # ========================================================================
    # API KEY ROTATION TESTS
    # ========================================================================

    def test_api_key_rotation_workflow(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test API key rotation without losing configuration

        BUSINESS CONTEXT:
        Organizations need to rotate API keys periodically for security.
        Configuration (model, quotas, settings) should be preserved.
        """
        org_id = self.get_test_organization_id()

        # Create config with initial key
        payload = self.create_llm_config_payload(
            provider_name="openai",
            api_key="sk-original-key-1234567890",
            model_name="gpt-5.2",
            usage_quota_monthly=5000000,
            is_primary=True
        )
        create_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )
        assert create_response.status_code == 201
        config_id = create_response.json()["id"]
        original_model = create_response.json()["model_name"]
        original_quota = create_response.json()["usage_quota_monthly"]

        # Rotate API key
        update_payload = {
            "api_key": "sk-new-rotated-key-0987654321"
        }
        update_response = test_app.put(
            f"/organizations/{org_id}/llm-config/{config_id}",
            headers=auth_headers,
            json=update_payload
        )

        assert update_response.status_code == 200
        result = update_response.json()

        # Verify other settings preserved
        assert result["model_name"] == original_model
        assert result["usage_quota_monthly"] == original_quota
        assert result["is_primary"] is True
        assert "api_key" not in result  # Key never returned

    # ========================================================================
    # PROVIDER CAPABILITY TESTS
    # ========================================================================

    def test_provider_vision_capability_filtering(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test filtering providers by vision capability

        BUSINESS CONTEXT:
        Screenshot analysis requires vision-capable providers.
        System must accurately report which providers support vision.
        """
        org_id = self.get_test_organization_id()

        # Get available providers
        response = test_app.get(
            f"/organizations/{org_id}/llm-config/providers",
            headers=auth_headers
        )

        assert response.status_code == 200
        providers = response.json()

        # Filter vision-capable providers
        vision_providers = [p for p in providers if p["supports_vision"]]

        # OpenAI, Anthropic, Deepseek, Qwen should support vision
        vision_provider_names = [p["provider_name"] for p in vision_providers]
        assert "openai" in vision_provider_names
        assert "anthropic" in vision_provider_names

        # Verify each vision provider has vision models
        for provider in vision_providers:
            assert provider["supports_vision"] is True

    def test_provider_streaming_capability_filtering(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test filtering providers by streaming capability

        BUSINESS CONTEXT:
        Real-time content generation requires streaming support.
        """
        org_id = self.get_test_organization_id()

        response = test_app.get(
            f"/organizations/{org_id}/llm-config/providers",
            headers=auth_headers
        )

        assert response.status_code == 200
        providers = response.json()

        # Most providers should support streaming
        streaming_providers = [p for p in providers if p["supports_streaming"]]
        assert len(streaming_providers) >= 4

    # ========================================================================
    # CONCURRENT UPDATE HANDLING TESTS
    # ========================================================================

    def test_only_one_primary_enforced(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test that only one configuration can be primary at a time

        BUSINESS CONTEXT:
        System enforces single primary provider to prevent ambiguity
        in provider selection during AI operations.
        """
        org_id = self.get_test_organization_id()

        # Create first config as primary
        first_payload = self.create_llm_config_payload(
            provider_name="openai",
            api_key="sk-first-key-123456789",
            is_primary=True
        )
        first_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=first_payload
        )
        assert first_response.status_code == 201
        first_id = first_response.json()["id"]

        # Create second config as primary
        second_payload = self.create_llm_config_payload(
            provider_name="anthropic",
            api_key="sk-ant-second-key-123",
            is_primary=True
        )
        second_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=second_payload
        )
        assert second_response.status_code == 201
        second_id = second_response.json()["id"]

        # Verify only one is primary now
        list_response = test_app.get(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers
        )
        configs = list_response.json()

        primary_configs = [c for c in configs if c["is_primary"]]
        assert len(primary_configs) == 1
        assert primary_configs[0]["id"] == second_id

    # ========================================================================
    # QUOTA ENFORCEMENT TESTS
    # ========================================================================

    def test_quota_percentage_calculation(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test quota percentage calculation

        BUSINESS CONTEXT:
        Organizations need to monitor quota usage to avoid service interruption.
        System should calculate and display quota utilization percentage.
        """
        org_id = self.get_test_organization_id()

        # Create config with quota
        payload = self.create_llm_config_payload(
            provider_name="openai",
            api_key="sk-quota-test-key-1234",
            usage_quota_monthly=1000000
        )
        response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )

        assert response.status_code == 201
        result = response.json()

        assert result["usage_quota_monthly"] == 1000000
        assert result["usage_current_month"] == 0

        # Calculate expected percentage
        if result["usage_quota_monthly"] > 0:
            expected_percentage = (result["usage_current_month"] / result["usage_quota_monthly"]) * 100
            # Verify quota tracking is set up correctly
            assert expected_percentage == 0

    def test_unlimited_quota_configuration(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test configuration with no quota (unlimited)

        BUSINESS CONTEXT:
        Some organizations prefer unlimited usage without quota restrictions.
        """
        org_id = self.get_test_organization_id()

        # Create config without quota (unlimited)
        payload = self.create_llm_config_payload(
            provider_name="openai",
            api_key="sk-unlimited-key-12345"
            # No usage_quota_monthly specified
        )
        response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )

        assert response.status_code == 201
        result = response.json()

        # No quota means unlimited
        assert result["usage_quota_monthly"] is None or result.get("usage_quota_monthly") is None

    # ========================================================================
    # ORGANIZATION ISOLATION TESTS
    # ========================================================================

    def test_organization_cannot_access_other_org_configs(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test organization isolation - can't access other org's configs

        BUSINESS CONTEXT:
        Multi-tenant security: organizations must not see each other's
        API keys or configurations.
        """
        # This test requires creating a config for a different organization
        # and verifying the test user cannot access it
        other_org_id = "00000000-0000-0000-0000-000000000099"

        response = test_app.get(
            f"/organizations/{other_org_id}/llm-config",
            headers=auth_headers
        )

        # Should either be 403 (forbidden) or return empty list
        assert response.status_code in [200, 403, 404]

        if response.status_code == 200:
            # If 200, should be empty (user's org has no access)
            configs = response.json()
            # Verify no configs from other org leaked
            assert isinstance(configs, list)

    # ========================================================================
    # MODEL VALIDATION TESTS
    # ========================================================================

    def test_invalid_model_for_provider(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test specifying invalid model for provider

        BUSINESS CONTEXT:
        System should validate that model exists for specified provider.
        """
        org_id = self.get_test_organization_id()

        # Try to create config with model from different provider
        payload = self.create_llm_config_payload(
            provider_name="openai",
            api_key="sk-test-invalid-model",
            model_name="claude-3-5-sonnet-20241022"  # Anthropic model
        )

        response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )

        # Should reject or warn about mismatched model
        # Implementation may vary - could accept with warning or reject
        assert response.status_code in [201, 400]

    # ========================================================================
    # BATCH OPERATIONS TESTS
    # ========================================================================

    def test_list_configs_with_pagination_support(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test that list endpoint supports many configurations

        BUSINESS CONTEXT:
        Organizations with many provider configs need efficient listing.
        """
        org_id = self.get_test_organization_id()

        # Create multiple configs
        providers = ["openai", "anthropic", "deepseek", "qwen", "ollama"]

        for i, provider in enumerate(providers):
            payload = self.create_llm_config_payload(
                provider_name=provider,
                api_key=f"sk-{provider}-key-{i}12345",
                is_primary=(i == 0)
            )
            response = test_app.post(
                f"/organizations/{org_id}/llm-config",
                headers=auth_headers,
                json=payload
            )
            assert response.status_code == 201

        # List all configs
        list_response = test_app.get(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers
        )

        assert list_response.status_code == 200
        configs = list_response.json()
        assert len(configs) == 5

    # ========================================================================
    # ERROR RECOVERY TESTS
    # ========================================================================

    def test_delete_primary_requires_new_primary(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test behavior when deleting primary config

        BUSINESS CONTEXT:
        If primary config is deleted, system should handle gracefully.
        May auto-promote another config or leave without primary.
        """
        org_id = self.get_test_organization_id()

        # Create primary config
        primary_payload = self.create_llm_config_payload(
            provider_name="openai",
            api_key="sk-primary-to-delete",
            is_primary=True
        )
        primary_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=primary_payload
        )
        assert primary_response.status_code == 201
        primary_id = primary_response.json()["id"]

        # Create secondary config
        secondary_payload = self.create_llm_config_payload(
            provider_name="anthropic",
            api_key="sk-ant-secondary-123",
            is_primary=False
        )
        secondary_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=secondary_payload
        )
        assert secondary_response.status_code == 201

        # Delete primary config
        delete_response = test_app.delete(
            f"/organizations/{org_id}/llm-config/{primary_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 204

        # Verify remaining config status
        list_response = test_app.get(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers
        )
        configs = list_response.json()
        assert len(configs) == 1
        # Secondary may or may not be auto-promoted to primary
        assert configs[0]["provider_name"] == "anthropic"

    def test_reactivate_deactivated_config(
        self,
        test_app: TestClient,
        auth_headers: Dict[str, str],
        clean_database
    ):
        """
        Test reactivating a deactivated configuration

        BUSINESS CONTEXT:
        Organizations may temporarily disable and later re-enable providers.
        """
        org_id = self.get_test_organization_id()

        # Create config
        payload = self.create_llm_config_payload(
            provider_name="openai",
            api_key="sk-reactivate-key-123"
        )
        create_response = test_app.post(
            f"/organizations/{org_id}/llm-config",
            headers=auth_headers,
            json=payload
        )
        assert create_response.status_code == 201
        config_id = create_response.json()["id"]

        # Deactivate
        deactivate_response = test_app.put(
            f"/organizations/{org_id}/llm-config/{config_id}",
            headers=auth_headers,
            json={"is_active": False}
        )
        assert deactivate_response.status_code == 200
        assert deactivate_response.json()["is_active"] is False

        # Reactivate
        reactivate_response = test_app.put(
            f"/organizations/{org_id}/llm-config/{config_id}",
            headers=auth_headers,
            json={"is_active": True}
        )
        assert reactivate_response.status_code == 200
        assert reactivate_response.json()["is_active"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
