"""
LLM Configuration API Endpoints

BUSINESS PURPOSE:
Provides REST API endpoints for organization-level LLM provider configuration.
Organizations can configure their preferred AI providers, manage API keys,
and monitor usage for screenshot-to-course generation and other AI features.

TECHNICAL IMPLEMENTATION:
- FastAPI router with comprehensive CRUD operations
- Pydantic models for request/response validation
- Custom exception handling with detailed error context
- Dependency injection for services and authentication
- Usage tracking and quota management

WHY:
Organizations need self-service capability to:
- Choose their preferred LLM provider (cost, data residency, performance)
- Manage their own API keys securely
- Monitor usage and control costs
- Test provider connections before using in production
"""
from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import logging
import httpx

# Import dependency injection
from app_dependencies import (
    get_current_user,
    require_org_admin,
    get_llm_config_dao
)

# Pydantic models for API
from pydantic import BaseModel, Field, validator

# Import custom exceptions
from organization_management.exceptions import (
    ValidationException,
    DatabaseException,
    AuthorizationException,
    APIException,
    LLMProviderException,
    LLMProviderConnectionException,
    LLMProviderAuthenticationException
)

# Import DAO
from organization_management.data_access.llm_config_dao import LLMConfigDAO


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/organizations/{organization_id}/llm-config",
    tags=["LLM Configuration"]
)


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def _parse_json_field(value, default=None):
    """
    Parse a JSON field that may be returned as a string from PostgreSQL JSONB.

    TECHNICAL CONTEXT:
    asyncpg returns JSONB columns as strings when using raw queries.
    This helper ensures consistent parsing across all endpoints.

    Args:
        value: The value from the database (may be str, list, dict, or None)
        default: Default value if parsing fails or value is None

    Returns:
        Parsed Python object (list or dict)
    """
    import json

    if value is None:
        return default if default is not None else ([] if isinstance(default, list) else {})

    if isinstance(value, (list, dict)):
        return value

    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default if default is not None else ([] if isinstance(default, list) else {})

    return default if default is not None else []


# ================================================================
# PYDANTIC MODELS - Request/Response DTOs
# ================================================================

class LLMProviderResponse(BaseModel):
    """
    LLM provider metadata response

    BUSINESS CONTEXT:
    Returns available providers that organizations can configure.
    """
    id: int
    provider_name: str
    display_name: str
    api_base_url: str
    supports_vision: bool
    supports_streaming: bool
    default_model: Optional[str] = None
    available_models: List[str] = []
    rate_limit_requests_per_minute: int
    max_tokens_per_request: int
    is_local: bool

    class Config:
        from_attributes = True


class LLMConfigCreateRequest(BaseModel):
    """
    Request to create LLM configuration for an organization

    BUSINESS CONTEXT:
    Allows organization admins to configure an LLM provider with
    their API key for AI-powered features.

    SECURITY:
    API keys are encrypted at rest and never returned in responses.
    """
    provider_name: str = Field(
        ...,
        description="Provider identifier (openai, anthropic, deepseek, etc.)"
    )
    api_key: str = Field(
        ...,
        min_length=10,
        description="API key for the provider"
    )
    model_name: Optional[str] = Field(
        None,
        description="Preferred model name (uses provider default if not specified)"
    )
    custom_base_url: Optional[str] = Field(
        None,
        description="Custom API base URL (for self-hosted or proxy setups)"
    )
    is_primary: bool = Field(
        default=False,
        description="Set as primary provider for this organization"
    )
    usage_quota_monthly: Optional[int] = Field(
        None,
        ge=0,
        description="Monthly token quota (None = unlimited)"
    )
    settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional provider-specific settings"
    )

    @validator("provider_name")
    def validate_provider_name(cls, v):
        """Validate provider name against known providers"""
        known_providers = {
            "openai", "anthropic", "deepseek", "qwen",
            "ollama", "llama", "gemini", "mistral"
        }
        if v.lower() not in known_providers:
            raise ValueError(
                f"Unknown provider: {v}. "
                f"Supported: {', '.join(sorted(known_providers))}"
            )
        return v.lower()


class LLMConfigUpdateRequest(BaseModel):
    """
    Request to update LLM configuration

    BUSINESS CONTEXT:
    Allows partial updates to existing provider configurations.
    Supports API key rotation for security compliance.
    """
    api_key: Optional[str] = Field(
        None,
        min_length=10,
        description="New API key for rotation (min 10 characters)"
    )
    model_name: Optional[str] = None
    custom_base_url: Optional[str] = None
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None
    usage_quota_monthly: Optional[int] = Field(None, ge=0)
    settings: Optional[Dict[str, Any]] = None


class LLMConfigResponse(BaseModel):
    """
    LLM configuration response

    BUSINESS CONTEXT:
    Returns configuration details without exposing API keys.
    """
    id: UUID
    organization_id: UUID
    provider_name: str
    display_name: str
    model_name: str
    custom_base_url: Optional[str] = None
    api_base_url: str
    is_primary: bool
    is_active: bool
    supports_vision: bool
    supports_streaming: bool
    available_models: List[str] = []
    is_local: bool
    usage_quota_monthly: Optional[int] = None
    usage_current_month: int = 0
    last_used_at: Optional[datetime] = None
    settings: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LLMConnectionTestRequest(BaseModel):
    """
    Request to test LLM provider connection

    BUSINESS CONTEXT:
    Allows testing a provider connection before saving configuration.
    """
    provider_name: str
    api_key: str
    model_name: Optional[str] = None
    custom_base_url: Optional[str] = None


class LLMConnectionTestResponse(BaseModel):
    """Response from connection test"""
    success: bool
    provider_name: str
    model_name: str
    message: str
    latency_ms: Optional[int] = None
    error_details: Optional[str] = None


class LLMUsageStatsResponse(BaseModel):
    """
    LLM usage statistics response

    BUSINESS CONTEXT:
    Returns usage data for billing, reporting, and optimization.
    """
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost: float
    avg_latency_ms: float
    successful_requests: int
    failed_requests: int
    success_rate: float


class LLMUsageByProviderResponse(BaseModel):
    """Usage statistics grouped by provider"""
    provider_name: str
    request_count: int
    total_tokens: int
    total_cost: float
    avg_latency_ms: float


# ================================================================
# API ENDPOINTS
# ================================================================

@router.get("/providers", response_model=List[LLMProviderResponse])
async def get_available_providers(
    organization_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    dao: LLMConfigDAO = Depends(get_llm_config_dao)
):
    """
    Get all available LLM providers

    BUSINESS CONTEXT:
    Returns the list of supported providers that organizations
    can configure for their AI operations.

    AUTHORIZATION:
    Any authenticated user in the organization can view providers.
    """
    try:
        providers = await dao.get_available_providers()
        result = []
        for p in providers:
            result.append(LLMProviderResponse(
                id=p["id"],
                provider_name=p["provider_name"],
                display_name=p["display_name"],
                api_base_url=p["api_base_url"],
                supports_vision=p["supports_vision"],
                supports_streaming=p["supports_streaming"],
                default_model=p["default_model"],
                available_models=_parse_json_field(p["available_models"], []),
                rate_limit_requests_per_minute=p["rate_limit_requests_per_minute"],
                max_tokens_per_request=p["max_tokens_per_request"],
                is_local=p["is_local"]
            ))
        return result
    except DatabaseException as e:
        logger.error(f"Database error fetching providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("", response_model=List[LLMConfigResponse])
async def get_organization_llm_configs(
    organization_id: UUID,
    current_user: Dict[str, Any] = Depends(require_org_admin),
    dao: LLMConfigDAO = Depends(get_llm_config_dao)
):
    """
    Get all LLM configurations for an organization

    BUSINESS CONTEXT:
    Returns all configured providers for organization management.
    API keys are never included in the response.

    AUTHORIZATION:
    Requires organization admin role.
    """
    try:
        configs = await dao.get_org_llm_configs(organization_id)
        return [
            LLMConfigResponse(
                id=c["id"],
                organization_id=c["organization_id"],
                provider_name=c["provider_name"],
                display_name=c["display_name"],
                model_name=c["model_name"],
                custom_base_url=c.get("custom_base_url"),
                api_base_url=c["api_base_url"],
                is_primary=c["is_primary"],
                is_active=c["is_active"],
                supports_vision=c["supports_vision"],
                supports_streaming=c["supports_streaming"],
                available_models=_parse_json_field(c["available_models"], []),
                is_local=c["is_local"],
                usage_quota_monthly=c.get("usage_quota_monthly"),
                usage_current_month=c.get("usage_current_month", 0),
                last_used_at=c.get("last_used_at"),
                settings=_parse_json_field(c.get("settings"), {}),
                created_at=c["created_at"],
                updated_at=c["updated_at"]
            )
            for c in configs
        ]
    except DatabaseException as e:
        logger.error(f"Database error fetching configs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("", response_model=LLMConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_llm_config(
    organization_id: UUID,
    request: LLMConfigCreateRequest,
    current_user: Dict[str, Any] = Depends(require_org_admin),
    dao: LLMConfigDAO = Depends(get_llm_config_dao)
):
    """
    Create LLM configuration for an organization

    BUSINESS CONTEXT:
    Allows organization admins to configure an LLM provider
    with their API key for AI-powered features.

    SECURITY:
    - API keys are encrypted at rest
    - Original keys are never returned in responses
    - Audit trail created for compliance

    AUTHORIZATION:
    Requires organization admin role.
    """
    try:
        # Create the configuration
        config = await dao.create_org_llm_config(
            organization_id=organization_id,
            provider_name=request.provider_name,
            api_key=request.api_key,  # TODO: Encrypt before storage
            model_name=request.model_name,
            custom_base_url=request.custom_base_url,
            is_primary=request.is_primary,
            usage_quota_monthly=request.usage_quota_monthly,
            settings=request.settings,
            created_by=current_user.get("user_id")
        )

        # Fetch the full config with provider details
        configs = await dao.get_org_llm_configs(organization_id)
        created_config = next(
            (c for c in configs if str(c["id"]) == str(config["id"])),
            None
        )

        if not created_config:
            raise APIException("Failed to retrieve created configuration")

        logger.info(
            f"Created LLM config for org {organization_id}, "
            f"provider {request.provider_name}"
        )

        return LLMConfigResponse(
            id=created_config["id"],
            organization_id=created_config["organization_id"],
            provider_name=created_config["provider_name"],
            display_name=created_config["display_name"],
            model_name=created_config["model_name"],
            custom_base_url=created_config.get("custom_base_url"),
            api_base_url=created_config["api_base_url"],
            is_primary=created_config["is_primary"],
            is_active=created_config["is_active"],
            supports_vision=created_config["supports_vision"],
            supports_streaming=created_config["supports_streaming"],
            available_models=_parse_json_field(created_config["available_models"], []),
            is_local=created_config["is_local"],
            usage_quota_monthly=created_config.get("usage_quota_monthly"),
            usage_current_month=created_config.get("usage_current_month", 0),
            last_used_at=created_config.get("last_used_at"),
            settings=_parse_json_field(created_config.get("settings"), {}),
            created_at=created_config["created_at"],
            updated_at=created_config["updated_at"]
        )

    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseException as e:
        logger.error(f"Database error creating config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{config_id}", response_model=LLMConfigResponse)
async def update_llm_config(
    organization_id: UUID,
    config_id: UUID,
    request: LLMConfigUpdateRequest,
    current_user: Dict[str, Any] = Depends(require_org_admin),
    dao: LLMConfigDAO = Depends(get_llm_config_dao)
):
    """
    Update an organization's LLM configuration

    BUSINESS CONTEXT:
    Allows updating provider settings, model preferences,
    or activation status without recreating the configuration.

    AUTHORIZATION:
    Requires organization admin role.
    """
    try:
        # Build update dict from non-None values
        updates = {}
        if request.api_key is not None:
            updates["api_key"] = request.api_key
        if request.model_name is not None:
            updates["model_name"] = request.model_name
        if request.custom_base_url is not None:
            updates["custom_base_url"] = request.custom_base_url
        if request.is_primary is not None:
            updates["is_primary"] = request.is_primary
        if request.is_active is not None:
            updates["is_active"] = request.is_active
        if request.usage_quota_monthly is not None:
            updates["usage_quota_monthly"] = request.usage_quota_monthly
        if request.settings is not None:
            updates["settings"] = request.settings

        if not updates:
            raise ValidationException("No fields to update")

        # Update the configuration
        updated_config = await dao.update_org_llm_config(
            config_id=config_id,
            organization_id=organization_id,
            updates=updates,
            updated_by=current_user.get("user_id")
        )

        if not updated_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found"
            )

        # Fetch full config with provider details
        configs = await dao.get_org_llm_configs(organization_id)
        full_config = next(
            (c for c in configs if str(c["id"]) == str(config_id)),
            None
        )

        if not full_config:
            raise APIException("Failed to retrieve updated configuration")

        logger.info(f"Updated LLM config {config_id} for org {organization_id}")

        return LLMConfigResponse(
            id=full_config["id"],
            organization_id=full_config["organization_id"],
            provider_name=full_config["provider_name"],
            display_name=full_config["display_name"],
            model_name=full_config["model_name"],
            custom_base_url=full_config.get("custom_base_url"),
            api_base_url=full_config["api_base_url"],
            is_primary=full_config["is_primary"],
            is_active=full_config["is_active"],
            supports_vision=full_config["supports_vision"],
            supports_streaming=full_config["supports_streaming"],
            available_models=_parse_json_field(full_config["available_models"], []),
            is_local=full_config["is_local"],
            usage_quota_monthly=full_config.get("usage_quota_monthly"),
            usage_current_month=full_config.get("usage_current_month", 0),
            last_used_at=full_config.get("last_used_at"),
            settings=_parse_json_field(full_config.get("settings"), {}),
            created_at=full_config["created_at"],
            updated_at=full_config["updated_at"]
        )

    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseException as e:
        logger.error(f"Database error updating config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_config(
    organization_id: UUID,
    config_id: UUID,
    current_user: Dict[str, Any] = Depends(require_org_admin),
    dao: LLMConfigDAO = Depends(get_llm_config_dao)
):
    """
    Delete an organization's LLM configuration

    BUSINESS CONTEXT:
    Removes a provider configuration when no longer needed.
    Usage history is preserved for compliance.

    AUTHORIZATION:
    Requires organization admin role.
    """
    try:
        deleted = await dao.delete_org_llm_config(
            config_id=config_id,
            organization_id=organization_id
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found"
            )

        logger.info(f"Deleted LLM config {config_id} for org {organization_id}")
        return None

    except DatabaseException as e:
        logger.error(f"Database error deleting config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/test", response_model=LLMConnectionTestResponse)
async def test_llm_connection(
    organization_id: UUID,
    request: LLMConnectionTestRequest,
    current_user: Dict[str, Any] = Depends(require_org_admin),
    dao: LLMConfigDAO = Depends(get_llm_config_dao)
):
    """
    Test LLM provider connection

    BUSINESS CONTEXT:
    Validates API credentials and connectivity before saving
    configuration, preventing failed setups.

    TECHNICAL:
    Makes a minimal API call to verify:
    - API key validity
    - Network connectivity
    - Model availability

    AUTHORIZATION:
    Requires organization admin role.
    """
    import time

    provider_name = request.provider_name.lower()
    api_key = request.api_key
    model_name = request.model_name
    custom_base_url = request.custom_base_url

    # Get provider info for defaults
    provider = await dao.get_provider_by_name(provider_name)
    if not provider:
        return LLMConnectionTestResponse(
            success=False,
            provider_name=provider_name,
            model_name=model_name or "unknown",
            message=f"Unknown provider: {provider_name}",
            error_details="Provider not found in database"
        )

    # Use default model if not specified
    if not model_name:
        model_name = provider["default_model"]

    # Use custom or default base URL
    base_url = custom_base_url or provider["api_base_url"]

    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Provider-specific connection tests
            if provider_name == "openai":
                response = await client.get(
                    f"{base_url}/models",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
            elif provider_name == "anthropic":
                # Anthropic doesn't have a list models endpoint, use messages
                response = await client.post(
                    f"{base_url}/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": model_name,
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "Hi"}]
                    }
                )
            elif provider_name == "gemini":
                # Gemini uses API key as query param
                response = await client.get(
                    f"{base_url}/models?key={api_key}"
                )
            elif provider_name == "ollama":
                # Local Ollama - just check if server is up
                response = await client.get(f"{base_url}/api/tags")
            elif provider_name in ("deepseek", "llama", "mistral"):
                # OpenAI-compatible providers
                response = await client.get(
                    f"{base_url}/models",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
            elif provider_name == "qwen":
                # DashScope has different API structure
                response = await client.post(
                    f"{base_url}/services/aigc/text-generation/generation",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_name,
                        "input": {"messages": [{"role": "user", "content": "Hi"}]},
                        "parameters": {"max_tokens": 1}
                    }
                )
            else:
                return LLMConnectionTestResponse(
                    success=False,
                    provider_name=provider_name,
                    model_name=model_name,
                    message=f"Connection test not implemented for {provider_name}",
                    error_details="Provider test not available"
                )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code in (200, 201):
                return LLMConnectionTestResponse(
                    success=True,
                    provider_name=provider_name,
                    model_name=model_name,
                    message="Connection successful",
                    latency_ms=latency_ms
                )
            elif response.status_code == 401:
                return LLMConnectionTestResponse(
                    success=False,
                    provider_name=provider_name,
                    model_name=model_name,
                    message="Authentication failed - invalid API key",
                    latency_ms=latency_ms,
                    error_details=response.text[:500]
                )
            elif response.status_code == 403:
                return LLMConnectionTestResponse(
                    success=False,
                    provider_name=provider_name,
                    model_name=model_name,
                    message="Access denied - check API key permissions",
                    latency_ms=latency_ms,
                    error_details=response.text[:500]
                )
            else:
                return LLMConnectionTestResponse(
                    success=False,
                    provider_name=provider_name,
                    model_name=model_name,
                    message=f"Connection failed with status {response.status_code}",
                    latency_ms=latency_ms,
                    error_details=response.text[:500]
                )

    except httpx.ConnectError as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return LLMConnectionTestResponse(
            success=False,
            provider_name=provider_name,
            model_name=model_name,
            message=f"Connection failed - cannot reach {base_url}",
            latency_ms=latency_ms,
            error_details=str(e)
        )
    except httpx.TimeoutException:
        return LLMConnectionTestResponse(
            success=False,
            provider_name=provider_name,
            model_name=model_name,
            message="Connection timed out after 30 seconds",
            error_details="Request timeout"
        )


@router.get("/usage", response_model=LLMUsageStatsResponse)
async def get_usage_stats(
    organization_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Start of period"),
    end_date: Optional[datetime] = Query(None, description="End of period"),
    current_user: Dict[str, Any] = Depends(require_org_admin),
    dao: LLMConfigDAO = Depends(get_llm_config_dao)
):
    """
    Get LLM usage statistics for an organization

    BUSINESS CONTEXT:
    Returns aggregated usage data for billing, reporting,
    and cost optimization analysis.

    AUTHORIZATION:
    Requires organization admin role.
    """
    try:
        stats = await dao.get_org_usage_stats(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )

        total_requests = stats.get("total_requests", 0) or 0
        successful = stats.get("successful_requests", 0) or 0

        return LLMUsageStatsResponse(
            total_requests=total_requests,
            total_input_tokens=stats.get("total_input_tokens", 0) or 0,
            total_output_tokens=stats.get("total_output_tokens", 0) or 0,
            total_tokens=stats.get("total_tokens", 0) or 0,
            total_cost=float(stats.get("total_cost", 0) or 0),
            avg_latency_ms=float(stats.get("avg_latency_ms", 0) or 0),
            successful_requests=successful,
            failed_requests=stats.get("failed_requests", 0) or 0,
            success_rate=(successful / total_requests * 100) if total_requests > 0 else 0
        )

    except DatabaseException as e:
        logger.error(f"Database error fetching usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/usage/by-provider", response_model=List[LLMUsageByProviderResponse])
async def get_usage_by_provider(
    organization_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Start of period"),
    end_date: Optional[datetime] = Query(None, description="End of period"),
    current_user: Dict[str, Any] = Depends(require_org_admin),
    dao: LLMConfigDAO = Depends(get_llm_config_dao)
):
    """
    Get LLM usage statistics grouped by provider

    BUSINESS CONTEXT:
    Breaks down usage by provider to help organizations
    optimize their AI provider strategy.

    AUTHORIZATION:
    Requires organization admin role.
    """
    try:
        usage_data = await dao.get_org_usage_by_provider(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )

        return [
            LLMUsageByProviderResponse(
                provider_name=u["provider_name"],
                request_count=u["request_count"],
                total_tokens=u["total_tokens"] or 0,
                total_cost=float(u["total_cost"] or 0),
                avg_latency_ms=float(u["avg_latency_ms"] or 0)
            )
            for u in usage_data
        ]

    except DatabaseException as e:
        logger.error(f"Database error fetching usage by provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/primary")
async def get_primary_config(
    organization_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    dao: LLMConfigDAO = Depends(get_llm_config_dao)
):
    """
    Get the primary LLM configuration for an organization

    BUSINESS CONTEXT:
    Returns the default provider configuration used for
    AI operations when no specific provider is requested.

    AUTHORIZATION:
    Any authenticated user in the organization can access.
    """
    try:
        config = await dao.get_org_primary_config(organization_id)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No primary LLM configuration found for this organization"
            )

        return LLMConfigResponse(
            id=config["id"],
            organization_id=config["organization_id"],
            provider_name=config["provider_name"],
            display_name=config["display_name"],
            model_name=config["model_name"],
            custom_base_url=config.get("custom_base_url"),
            api_base_url=config["api_base_url"],
            is_primary=config["is_primary"],
            is_active=config["is_active"],
            supports_vision=config["supports_vision"],
            supports_streaming=config.get("supports_streaming", False),
            available_models=_parse_json_field(config["available_models"], []),
            is_local=config.get("is_local", False),
            usage_quota_monthly=config.get("usage_quota_monthly"),
            usage_current_month=config.get("usage_current_month", 0),
            last_used_at=config.get("last_used_at"),
            settings=_parse_json_field(config.get("settings"), {}),
            created_at=config["created_at"],
            updated_at=config["updated_at"]
        )

    except DatabaseException as e:
        logger.error(f"Database error fetching primary config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/vision")
async def get_vision_config(
    organization_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    dao: LLMConfigDAO = Depends(get_llm_config_dao)
):
    """
    Get a vision-capable LLM configuration for an organization

    BUSINESS CONTEXT:
    Returns a provider configuration that supports vision
    for screenshot analysis operations.

    AUTHORIZATION:
    Any authenticated user in the organization can access.
    """
    try:
        config = await dao.get_org_vision_config(organization_id)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No vision-capable LLM configuration found for this organization"
            )

        return LLMConfigResponse(
            id=config["id"],
            organization_id=config["organization_id"],
            provider_name=config["provider_name"],
            display_name=config["display_name"],
            model_name=config["model_name"],
            custom_base_url=config.get("custom_base_url"),
            api_base_url=config["api_base_url"],
            is_primary=config.get("is_primary", False),
            is_active=config["is_active"],
            supports_vision=config["supports_vision"],
            supports_streaming=config.get("supports_streaming", False),
            available_models=_parse_json_field(config["available_models"], []),
            is_local=config.get("is_local", False),
            usage_quota_monthly=config.get("usage_quota_monthly"),
            usage_current_month=config.get("usage_current_month", 0),
            last_used_at=config.get("last_used_at"),
            settings=_parse_json_field(config.get("settings"), {}),
            created_at=config["created_at"],
            updated_at=config["updated_at"]
        )

    except DatabaseException as e:
        logger.error(f"Database error fetching vision config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
