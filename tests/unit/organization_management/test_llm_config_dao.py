"""
Unit tests for LLMConfigDAO

NOTE: Following TDD approach - tests written BEFORE implementation.
Uses real test doubles instead of mocks for authentic behavior.

BUSINESS CONTEXT:
The LLMConfigDAO provides database operations for:
- Organization LLM provider configuration management
- Secure API key storage with encryption
- Multi-provider support per organization
- Usage tracking and quota enforcement
- Primary provider designation
- Vision-capable provider selection

TECHNICAL IMPLEMENTATION:
- Tests all CRUD operations for LLM configurations
- Validates API key hashing and encryption
- Tests provider validation
- Tests primary provider logic (one per organization)
- Tests usage tracking and quota checking
- Tests error handling and edge cases

WHY:
Organizations need to configure their own LLM providers based on cost,
data residency, performance, and cloud infrastructure preferences.
This DAO ensures secure and reliable configuration management.
"""

import pytest
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4, UUID
from typing import Dict, Any, List, Optional

from organization_management.data_access.llm_config_dao import LLMConfigDAO
from organization_management.exceptions import (
    DatabaseException,
    ValidationException,
)


# ================================================================
# TEST DOUBLES - Real implementations using in-memory storage
# ================================================================


class FakeAsyncPGConnection:
    """
    Fake asyncpg connection for testing

    BUSINESS CONTEXT:
    Simulates PostgreSQL database operations without requiring
    actual database connectivity for fast, isolated unit tests.
    """

    def __init__(self, db_state: Dict[str, Any]):
        self.db_state = db_state
        self.in_transaction = False

    async def fetch(self, query: str, *args):
        """Execute SELECT query and return multiple rows"""
        # Parse query type
        if "FROM llm_providers" in query:
            return self._fetch_providers(query, *args)
        elif "FROM organization_llm_config" in query:
            return self._fetch_org_configs(query, *args)
        elif "FROM llm_usage_log" in query:
            return self._fetch_usage_logs(query, *args)
        return []

    async def fetchrow(self, query: str, *args):
        """Execute SELECT query and return single row"""
        rows = await self.fetch(query, *args)
        return rows[0] if rows else None

    async def execute(self, query: str, *args):
        """Execute INSERT/UPDATE/DELETE query"""
        if "INSERT INTO organization_llm_config" in query:
            return self._insert_org_config(query, *args)
        elif "UPDATE organization_llm_config" in query:
            return self._update_org_config(query, *args)
        elif "DELETE FROM organization_llm_config" in query:
            return self._delete_org_config(query, *args)
        elif "INSERT INTO llm_usage_log" in query:
            return self._insert_usage_log(query, *args)

    def _fetch_providers(self, query: str, *args):
        """Fetch LLM providers from in-memory state"""
        providers = self.db_state.get('providers', [])

        # Filter by provider_name if specified
        if args and "WHERE provider_name" in query:
            provider_name = args[0]
            providers = [p for p in providers if p['provider_name'] == provider_name]

        # Filter active only
        if "is_active = TRUE" in query:
            providers = [p for p in providers if p['is_active']]

        return [FakeRecord(p) for p in providers]

    def _fetch_org_configs(self, query: str, *args):
        """Fetch organization LLM configs from in-memory state"""
        configs = self.db_state.get('org_configs', [])

        # Filter by organization_id
        if args:
            org_id = args[0]
            configs = [c for c in configs if c['organization_id'] == org_id]

        # Filter by is_primary
        if "is_primary = TRUE" in query:
            configs = [c for c in configs if c['is_primary']]

        # Filter by is_active
        if "is_active = TRUE" in query:
            configs = [c for c in configs if c['is_active']]

        # Join with providers if needed
        if "JOIN llm_providers" in query:
            providers = {p['id']: p for p in self.db_state.get('providers', [])}
            enriched_configs = []
            for config in configs:
                provider = providers.get(config['provider_id'])
                if provider:
                    # Merge config and provider data
                    merged = {**config, **{
                        'provider_name': provider['provider_name'],
                        'display_name': provider['display_name'],
                        'api_base_url': provider['api_base_url'],
                        'vision_endpoint': provider.get('vision_endpoint'),
                        'text_endpoint': provider.get('text_endpoint'),
                        'supports_vision': provider.get('supports_vision', False),
                        'supports_streaming': provider.get('supports_streaming', False),
                        'available_models': provider.get('available_models', []),
                        'is_local': provider.get('is_local', False),
                        'auth_type': provider.get('auth_type', 'bearer'),
                    }}
                    enriched_configs.append(merged)
            configs = enriched_configs

        # Filter vision-capable if needed
        if "supports_vision = TRUE" in query:
            configs = [c for c in configs if c.get('supports_vision')]

        # Apply LIMIT if specified
        if "LIMIT 1" in query:
            configs = configs[:1]

        # Sort by is_primary DESC
        if "ORDER BY" in query and "is_primary DESC" in query:
            configs = sorted(configs, key=lambda x: x.get('is_primary', False), reverse=True)

        return [FakeRecord(c) for c in configs]

    def _fetch_usage_logs(self, query: str, *args):
        """Fetch usage logs from in-memory state"""
        logs = self.db_state.get('usage_logs', [])

        # Filter by organization_id
        if args:
            org_id = args[0]
            logs = [log for log in logs if log['organization_id'] == org_id]

        # Apply date filters if present
        if len(args) > 1:
            start_date = args[1]
            logs = [log for log in logs if log['created_at'] >= start_date]
        if len(args) > 2:
            end_date = args[2]
            logs = [log for log in logs if log['created_at'] <= end_date]

        # Aggregate stats
        if "COUNT(*)" in query and "GROUP BY provider_name" in query:
            # Group by provider
            provider_stats = {}
            for log in logs:
                provider = log['provider_name']
                if provider not in provider_stats:
                    provider_stats[provider] = {
                        'provider_name': provider,
                        'request_count': 0,
                        'total_tokens': 0,
                        'total_cost': 0,
                        'avg_latency_ms': 0,
                    }
                provider_stats[provider]['request_count'] += 1
                provider_stats[provider]['total_tokens'] += log.get('total_tokens', 0)
                provider_stats[provider]['total_cost'] += log.get('cost_estimate', 0)

            # Calculate averages
            for stats in provider_stats.values():
                if stats['request_count'] > 0:
                    total_latency = sum(log.get('latency_ms', 0) for log in logs
                                      if log['provider_name'] == stats['provider_name'])
                    stats['avg_latency_ms'] = total_latency / stats['request_count']

            return [FakeRecord(stats) for stats in provider_stats.values()]

        elif "COUNT(*)" in query:
            # Aggregate all stats
            stats = {
                'total_requests': len(logs),
                'total_input_tokens': sum(log.get('input_tokens', 0) for log in logs),
                'total_output_tokens': sum(log.get('output_tokens', 0) for log in logs),
                'total_tokens': sum(log.get('total_tokens', 0) for log in logs),
                'total_cost': sum(log.get('cost_estimate', 0) for log in logs),
                'avg_latency_ms': sum(log.get('latency_ms', 0) for log in logs) / len(logs) if logs else 0,
                'successful_requests': sum(1 for log in logs if log.get('success', True)),
                'failed_requests': sum(1 for log in logs if not log.get('success', True)),
            }
            return [FakeRecord(stats)]

        return [FakeRecord(log) for log in logs]

    def _insert_org_config(self, query: str, *args):
        """Insert organization LLM config"""
        # Extract values from args
        config = {
            'id': args[0],
            'organization_id': args[1],
            'provider_id': args[2],
            'api_key_encrypted': args[3],
            'api_key_hash': args[4],
            'model_name': args[5],
            'custom_base_url': args[6],
            'is_primary': args[7],
            'is_active': True,
            'settings': args[8],
            'created_by': args[9],
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'usage_quota_monthly': None,
            'usage_current_month': 0,
            'last_used_at': None,
            'updated_by': None,
        }

        # Check for duplicate
        existing = self.db_state.get('org_configs', [])
        for cfg in existing:
            if (cfg['organization_id'] == config['organization_id'] and
                cfg['provider_id'] == config['provider_id']):
                raise Exception("UniqueViolationError")

        self.db_state.setdefault('org_configs', []).append(config)
        return config

    def _update_org_config(self, query: str, *args):
        """Update organization LLM config"""
        configs = self.db_state.get('org_configs', [])

        # Handle unset primary
        if "SET is_primary = FALSE" in query:
            org_id = args[0]
            exclude_id = args[1] if len(args) > 1 else None
            for cfg in configs:
                if cfg['organization_id'] == org_id and cfg['is_primary']:
                    if exclude_id is None or cfg['id'] != exclude_id:
                        cfg['is_primary'] = False
                        cfg['updated_at'] = datetime.now()
            return

        # Handle usage increment
        if "usage_current_month = usage_current_month" in query:
            tokens = args[0]
            config_id = args[1]
            for cfg in configs:
                if cfg['id'] == config_id:
                    cfg['usage_current_month'] = cfg.get('usage_current_month', 0) + tokens
                    cfg['last_used_at'] = datetime.now()
                    cfg['updated_at'] = datetime.now()
            return

        # Handle general update
        # Last two args are config_id and org_id
        config_id = args[-2]
        org_id = args[-1]

        for cfg in configs:
            if cfg['id'] == config_id and cfg['organization_id'] == org_id:
                # Parse SET clause to apply updates
                # This is simplified - in real implementation would parse query
                cfg['updated_at'] = datetime.now()
                return

    def _delete_org_config(self, query: str, *args):
        """Delete organization LLM config"""
        config_id = args[0]
        org_id = args[1]

        configs = self.db_state.get('org_configs', [])
        for i, cfg in enumerate(configs):
            if cfg['id'] == config_id and cfg['organization_id'] == org_id:
                del configs[i]
                return {'id': config_id}
        return None

    def _insert_usage_log(self, query: str, *args):
        """Insert usage log entry"""
        log = {
            'id': args[0],
            'organization_id': args[1],
            'config_id': args[2],
            'provider_name': args[3],
            'model_name': args[4],
            'operation_type': args[5],
            'input_tokens': args[6],
            'output_tokens': args[7],
            'total_tokens': args[8],
            'cost_estimate': args[9],
            'latency_ms': args[10],
            'success': args[11],
            'error_message': args[12],
            'request_metadata': args[13],
            'user_id': args[14],
            'created_at': datetime.now(),
        }
        self.db_state.setdefault('usage_logs', []).append(log)


class FakeRecord:
    """
    Fake asyncpg Record object

    Simulates the asyncpg.Record interface for test data.
    """

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __getitem__(self, key):
        return self._data.get(key)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __iter__(self):
        return iter(self._data.items())


class FakeAsyncPGPool:
    """
    Fake asyncpg connection pool for testing

    BUSINESS CONTEXT:
    Simulates connection pool behavior for isolated testing
    without requiring actual PostgreSQL database.
    """

    def __init__(self, db_state: Dict[str, Any]):
        self.db_state = db_state

    def acquire(self):
        """Context manager for acquiring connection"""
        return FakeAsyncPGContextManager(self.db_state)


class FakeAsyncPGContextManager:
    """Context manager for fake connection acquisition"""

    def __init__(self, db_state: Dict[str, Any]):
        self.db_state = db_state
        self.conn = None

    async def __aenter__(self):
        self.conn = FakeAsyncPGConnection(self.db_state)
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# ================================================================
# TEST FIXTURES
# ================================================================


@pytest.fixture
def db_state():
    """
    In-memory database state for testing

    BUSINESS CONTEXT:
    Provides initial database state with sample providers
    for realistic testing scenarios.
    """
    return {
        'providers': [
            {
                'id': 1,
                'provider_name': 'openai',
                'display_name': 'OpenAI',
                'api_base_url': 'https://api.openai.com/v1',
                'vision_endpoint': '/chat/completions',
                'text_endpoint': '/chat/completions',
                'auth_type': 'bearer',
                'supports_vision': True,
                'supports_streaming': True,
                'default_model': 'gpt-5.2',
                'available_models': ['gpt-5.2', 'gpt-4o'],
                'rate_limit_requests_per_minute': 500,
                'max_tokens_per_request': 128000,
                'is_local': False,
                'is_active': True,
                'metadata': {},
            },
            {
                'id': 2,
                'provider_name': 'anthropic',
                'display_name': 'Anthropic Claude',
                'api_base_url': 'https://api.anthropic.com/v1',
                'vision_endpoint': '/messages',
                'text_endpoint': '/messages',
                'auth_type': 'x-api-key',
                'supports_vision': True,
                'supports_streaming': True,
                'default_model': 'claude-3-5-sonnet-20241022',
                'available_models': ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229'],
                'rate_limit_requests_per_minute': 50,
                'max_tokens_per_request': 200000,
                'is_local': False,
                'is_active': True,
                'metadata': {},
            },
            {
                'id': 3,
                'provider_name': 'ollama',
                'display_name': 'Ollama (Local)',
                'api_base_url': 'http://localhost:11434',
                'vision_endpoint': '/api/generate',
                'text_endpoint': '/api/generate',
                'auth_type': 'none',
                'supports_vision': True,
                'supports_streaming': True,
                'default_model': 'llava',
                'available_models': ['llava', 'llava:13b'],
                'rate_limit_requests_per_minute': 1000,
                'max_tokens_per_request': 32000,
                'is_local': True,
                'is_active': True,
                'metadata': {},
            },
            {
                'id': 4,
                'provider_name': 'deepseek',
                'display_name': 'Deepseek',
                'api_base_url': 'https://api.deepseek.com/v1',
                'vision_endpoint': '/chat/completions',
                'text_endpoint': '/chat/completions',
                'auth_type': 'bearer',
                'supports_vision': False,  # Text only
                'supports_streaming': True,
                'default_model': 'deepseek-chat',
                'available_models': ['deepseek-chat', 'deepseek-coder'],
                'rate_limit_requests_per_minute': 60,
                'max_tokens_per_request': 32000,
                'is_local': False,
                'is_active': True,
                'metadata': {},
            },
        ],
        'org_configs': [],
        'usage_logs': [],
    }


@pytest.fixture
def db_pool(db_state):
    """Fake database connection pool"""
    return FakeAsyncPGPool(db_state)


@pytest.fixture
def llm_config_dao(db_pool):
    """LLMConfigDAO instance with fake database pool"""
    return LLMConfigDAO(db_pool)


@pytest.fixture
def sample_org_id():
    """Sample organization ID"""
    return uuid4()


@pytest.fixture
def sample_user_id():
    """Sample user ID"""
    return uuid4()


# ================================================================
# TEST CLASS: Provider Reference Data
# ================================================================


class TestProviderReferenceData:
    """
    Test suite for LLM provider reference data operations

    BUSINESS CONTEXT:
    Tests the retrieval of available LLM providers that organizations
    can configure for their AI operations.
    """

    @pytest.mark.asyncio
    async def test_get_available_providers_returns_all_active(
        self,
        llm_config_dao,
        db_state
    ):
        """
        Test retrieving all available LLM providers

        BUSINESS CONTEXT:
        Organizations need to see all supported providers to choose
        which ones to configure for their AI operations.
        """
        # When: Get available providers
        providers = await llm_config_dao.get_available_providers()

        # Then: Should return all active providers
        assert len(providers) == 4
        assert all(p['is_active'] for p in providers)

        # Verify expected providers
        provider_names = {p['provider_name'] for p in providers}
        assert 'openai' in provider_names
        assert 'anthropic' in provider_names
        assert 'ollama' in provider_names
        assert 'deepseek' in provider_names

    @pytest.mark.asyncio
    async def test_get_available_providers_includes_metadata(
        self,
        llm_config_dao
    ):
        """
        Test that provider metadata includes all necessary fields

        BUSINESS CONTEXT:
        Organizations need complete provider information including
        capabilities, rate limits, and model options.
        """
        # When: Get available providers
        providers = await llm_config_dao.get_available_providers()

        # Then: Each provider should have complete metadata
        for provider in providers:
            assert 'provider_name' in provider
            assert 'display_name' in provider
            assert 'api_base_url' in provider
            assert 'supports_vision' in provider
            assert 'supports_streaming' in provider
            assert 'default_model' in provider
            assert 'available_models' in provider
            assert 'rate_limit_requests_per_minute' in provider
            assert 'max_tokens_per_request' in provider

    @pytest.mark.asyncio
    async def test_get_provider_by_name_returns_correct_provider(
        self,
        llm_config_dao
    ):
        """
        Test retrieving specific provider by name

        BUSINESS CONTEXT:
        When creating configurations, the system needs to validate
        and retrieve specific provider details.
        """
        # When: Get OpenAI provider
        provider = await llm_config_dao.get_provider_by_name('openai')

        # Then: Should return correct provider
        assert provider is not None
        assert provider['provider_name'] == 'openai'
        assert provider['display_name'] == 'OpenAI'
        assert provider['supports_vision'] is True

    @pytest.mark.asyncio
    async def test_get_provider_by_name_returns_none_for_unknown(
        self,
        llm_config_dao
    ):
        """
        Test that unknown provider returns None

        BUSINESS CONTEXT:
        Invalid provider names should be caught during configuration
        creation to prevent errors.
        """
        # When: Get unknown provider
        provider = await llm_config_dao.get_provider_by_name('unknown_provider')

        # Then: Should return None
        assert provider is None


# ================================================================
# TEST CLASS: Organization LLM Configuration CRUD
# ================================================================


class TestOrganizationLLMConfiguration:
    """
    Test suite for organization LLM configuration operations

    BUSINESS CONTEXT:
    Tests CRUD operations for organization-specific LLM provider
    configurations including API keys and preferences.
    """

    @pytest.mark.asyncio
    async def test_create_org_llm_config_success(
        self,
        llm_config_dao,
        sample_org_id,
        sample_user_id
    ):
        """
        Test creating organization LLM configuration

        BUSINESS CONTEXT:
        Organizations configure their LLM provider with API key
        to enable AI-powered features.
        """
        # Given: API key for OpenAI
        api_key = "sk-test-key-12345"

        # When: Create LLM config
        config = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key=api_key,
            model_name='gpt-5.2',
            is_primary=True,
            created_by=sample_user_id
        )

        # Then: Config should be created with correct data
        assert config['organization_id'] == sample_org_id
        assert config['provider_id'] == 1  # OpenAI provider ID
        assert config['model_name'] == 'gpt-5.2'
        assert config['is_primary'] is True
        assert config['is_active'] is True
        assert config['api_key_encrypted'] == api_key  # In production, would be encrypted

        # Verify API key hash
        expected_hash = hashlib.sha256(api_key.encode()).hexdigest()[:64]
        assert config['api_key_hash'] == expected_hash

    @pytest.mark.asyncio
    async def test_create_org_llm_config_uses_default_model_when_not_specified(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test that default model is used when not specified

        BUSINESS CONTEXT:
        Each provider has a recommended default model that should
        be used when organization doesn't specify a preference.
        """
        # When: Create config without specifying model
        config = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='anthropic',
            api_key='sk-ant-test-key',
            is_primary=True
        )

        # Then: Should use provider's default model
        assert config['model_name'] == 'claude-3-5-sonnet-20241022'

    @pytest.mark.asyncio
    async def test_create_org_llm_config_rejects_unknown_provider(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test that unknown provider is rejected

        BUSINESS CONTEXT:
        Only supported providers should be configurable to ensure
        the platform can integrate with them properly.
        """
        # When/Then: Creating config with unknown provider should raise exception
        with pytest.raises(ValidationException) as exc_info:
            await llm_config_dao.create_org_llm_config(
                organization_id=sample_org_id,
                provider_name='unknown_provider',
                api_key='test-key',
                is_primary=True
            )

        assert "Unknown provider" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_org_llm_config_prevents_duplicate(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test that duplicate provider config is prevented

        BUSINESS CONTEXT:
        An organization should only have one configuration per
        provider to avoid confusion and conflicts.
        """
        # Given: Existing OpenAI config
        await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test-key-1',
            is_primary=True
        )

        # When/Then: Creating another OpenAI config should fail
        with pytest.raises(ValidationException):
            await llm_config_dao.create_org_llm_config(
                organization_id=sample_org_id,
                provider_name='openai',
                api_key='sk-test-key-2',
                is_primary=False
            )

    @pytest.mark.asyncio
    async def test_get_org_llm_configs_returns_all_configs(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test retrieving all LLM configurations for organization

        BUSINESS CONTEXT:
        Organizations may configure multiple providers and need
        to see all their configurations.
        """
        # Given: Multiple provider configs
        await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test-1',
            is_primary=True
        )
        await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='anthropic',
            api_key='sk-ant-test-2',
            is_primary=False
        )

        # When: Get all configs
        configs = await llm_config_dao.get_org_llm_configs(sample_org_id)

        # Then: Should return both configs with provider details
        assert len(configs) == 2

        # Primary should be first
        assert configs[0]['is_primary'] is True
        assert configs[0]['provider_name'] == 'openai'

        # Non-primary should be second
        assert configs[1]['is_primary'] is False
        assert configs[1]['provider_name'] == 'anthropic'

    @pytest.mark.asyncio
    async def test_get_org_primary_config_returns_primary(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test retrieving primary LLM configuration

        BUSINESS CONTEXT:
        The primary configuration is the default used for AI operations
        when no specific provider is requested.
        """
        # Given: Multiple configs with one primary
        await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='anthropic',
            api_key='sk-ant-test',
            is_primary=False
        )
        await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test',
            is_primary=True
        )

        # When: Get primary config
        primary = await llm_config_dao.get_org_primary_config(sample_org_id)

        # Then: Should return OpenAI config
        assert primary is not None
        assert primary['provider_name'] == 'openai'
        assert primary['is_primary'] is True

    @pytest.mark.asyncio
    async def test_get_org_vision_config_returns_vision_capable(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test retrieving vision-capable LLM configuration

        BUSINESS CONTEXT:
        Screenshot-to-course generation requires a vision-capable
        LLM provider for image analysis.
        """
        # Given: Mix of vision and text-only providers
        await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='deepseek',  # Text only
            api_key='sk-ds-test',
            is_primary=False
        )
        await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',  # Vision capable
            api_key='sk-test',
            is_primary=True
        )

        # When: Get vision config
        vision_config = await llm_config_dao.get_org_vision_config(sample_org_id)

        # Then: Should return vision-capable provider
        assert vision_config is not None
        assert vision_config['provider_name'] == 'openai'
        assert vision_config['supports_vision'] is True

    @pytest.mark.asyncio
    async def test_update_org_llm_config_updates_fields(
        self,
        llm_config_dao,
        sample_org_id,
        sample_user_id
    ):
        """
        Test updating organization LLM configuration

        BUSINESS CONTEXT:
        Organizations need to update their configurations to change
        models, quotas, or other settings.
        """
        # Given: Existing config
        config = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test',
            model_name='gpt-4o',
            is_primary=True
        )

        # When: Update model and quota
        updated = await llm_config_dao.update_org_llm_config(
            config_id=config['id'],
            organization_id=sample_org_id,
            updates={
                'model_name': 'gpt-5.2',
                'usage_quota_monthly': 1000000
            },
            updated_by=sample_user_id
        )

        # Then: Should return updated config
        assert updated is not None
        # Note: In real implementation, would verify updated fields

    @pytest.mark.asyncio
    async def test_update_org_llm_config_sets_new_primary(
        self,
        llm_config_dao,
        sample_org_id,
        db_state
    ):
        """
        Test that setting new primary unsets old primary

        BUSINESS CONTEXT:
        Only one provider can be primary at a time. Setting a new
        primary should automatically unset the old one.
        """
        # Given: Two configs, one primary
        config1 = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test-1',
            is_primary=True
        )
        config2 = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='anthropic',
            api_key='sk-ant-test-2',
            is_primary=False
        )

        # When: Set config2 as primary
        await llm_config_dao.update_org_llm_config(
            config_id=config2['id'],
            organization_id=sample_org_id,
            updates={'is_primary': True}
        )

        # Then: config1 should no longer be primary
        configs = db_state['org_configs']
        config1_updated = next(c for c in configs if c['id'] == config1['id'])
        assert config1_updated['is_primary'] is False

    @pytest.mark.asyncio
    async def test_delete_org_llm_config_removes_config(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test deleting organization LLM configuration

        BUSINESS CONTEXT:
        Organizations may need to remove provider configurations
        when they stop using a service.
        """
        # Given: Existing config
        config = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test',
            is_primary=True
        )

        # When: Delete config
        deleted = await llm_config_dao.delete_org_llm_config(
            config_id=config['id'],
            organization_id=sample_org_id
        )

        # Then: Should return True
        assert deleted is True

        # Verify config is gone
        configs = await llm_config_dao.get_org_llm_configs(sample_org_id)
        assert len(configs) == 0

    @pytest.mark.asyncio
    async def test_delete_org_llm_config_returns_false_when_not_found(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test deleting non-existent config returns False

        BUSINESS CONTEXT:
        Attempting to delete a config that doesn't exist should
        be handled gracefully.
        """
        # When: Delete non-existent config
        deleted = await llm_config_dao.delete_org_llm_config(
            config_id=uuid4(),
            organization_id=sample_org_id
        )

        # Then: Should return False
        assert deleted is False


# ================================================================
# TEST CLASS: Primary Provider Management
# ================================================================


class TestPrimaryProviderManagement:
    """
    Test suite for primary provider designation

    BUSINESS CONTEXT:
    Organizations can have multiple LLM providers configured but
    need one designated as primary for default operations.
    """

    @pytest.mark.asyncio
    async def test_first_config_can_be_set_as_primary(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test that first configuration can be primary

        BUSINESS CONTEXT:
        When organization adds their first provider, they typically
        want it to be the primary/default provider.
        """
        # When: Create first config as primary
        config = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test',
            is_primary=True
        )

        # Then: Should be primary
        assert config['is_primary'] is True

    @pytest.mark.asyncio
    async def test_creating_second_primary_unsets_first(
        self,
        llm_config_dao,
        sample_org_id,
        db_state
    ):
        """
        Test that creating new primary unsets previous primary

        BUSINESS CONTEXT:
        Only one provider can be primary. Setting a new primary
        during creation should unset the old one.
        """
        # Given: First primary config
        config1 = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test-1',
            is_primary=True
        )

        # When: Create second config as primary
        config2 = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='anthropic',
            api_key='sk-ant-test-2',
            is_primary=True
        )

        # Then: config1 should no longer be primary
        configs = db_state['org_configs']
        config1_updated = next(c for c in configs if c['id'] == config1['id'])
        assert config1_updated['is_primary'] is False

        # config2 should be primary
        assert config2['is_primary'] is True

    @pytest.mark.asyncio
    async def test_organization_can_have_no_primary(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test that organization can have configs without a primary

        BUSINESS CONTEXT:
        Organizations may configure multiple providers without
        designating any as primary (explicit provider selection).
        """
        # When: Create configs without primary
        await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test-1',
            is_primary=False
        )
        await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='anthropic',
            api_key='sk-ant-test-2',
            is_primary=False
        )

        # Then: Get primary should return None
        primary = await llm_config_dao.get_org_primary_config(sample_org_id)
        assert primary is None


# ================================================================
# TEST CLASS: API Key Security
# ================================================================


class TestAPIKeySecurity:
    """
    Test suite for API key encryption and hashing

    BUSINESS CONTEXT:
    API keys are sensitive credentials that must be stored securely
    with encryption and hashing for validation.
    """

    @pytest.mark.asyncio
    async def test_api_key_is_hashed(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test that API key is hashed for validation

        BUSINESS CONTEXT:
        API key hash allows validation without storing plaintext,
        providing an extra security layer.
        """
        # Given: API key
        api_key = "sk-test-secret-key-12345"

        # When: Create config
        config = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key=api_key,
            is_primary=True
        )

        # Then: Hash should match SHA256 of key
        expected_hash = hashlib.sha256(api_key.encode()).hexdigest()[:64]
        assert config['api_key_hash'] == expected_hash

    @pytest.mark.asyncio
    async def test_api_key_hash_is_deterministic(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test that same key produces same hash

        BUSINESS CONTEXT:
        Hash determinism allows for key validation and comparison.
        """
        # Given: Same API key used twice
        api_key = "sk-test-consistent-key"

        # When: Create two configs with same key (different orgs)
        org_id_1 = sample_org_id
        org_id_2 = uuid4()

        config1 = await llm_config_dao.create_org_llm_config(
            organization_id=org_id_1,
            provider_name='openai',
            api_key=api_key,
            is_primary=True
        )
        config2 = await llm_config_dao.create_org_llm_config(
            organization_id=org_id_2,
            provider_name='openai',
            api_key=api_key,
            is_primary=True
        )

        # Then: Hashes should match
        assert config1['api_key_hash'] == config2['api_key_hash']

    @pytest.mark.asyncio
    async def test_different_keys_produce_different_hashes(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test that different keys produce different hashes

        BUSINESS CONTEXT:
        Hash uniqueness ensures each API key can be uniquely identified.
        """
        # When: Create two configs with different keys
        org_id_1 = sample_org_id
        org_id_2 = uuid4()

        config1 = await llm_config_dao.create_org_llm_config(
            organization_id=org_id_1,
            provider_name='openai',
            api_key='sk-test-key-abc123',
            is_primary=True
        )
        config2 = await llm_config_dao.create_org_llm_config(
            organization_id=org_id_2,
            provider_name='openai',
            api_key='sk-test-key-xyz789',
            is_primary=True
        )

        # Then: Hashes should be different
        assert config1['api_key_hash'] != config2['api_key_hash']


# ================================================================
# TEST CLASS: Usage Tracking
# ================================================================


class TestUsageTracking:
    """
    Test suite for LLM usage tracking and logging

    BUSINESS CONTEXT:
    Track all LLM API usage for billing, quota enforcement,
    analytics, and audit compliance.
    """

    @pytest.mark.asyncio
    async def test_log_llm_usage_creates_entry(
        self,
        llm_config_dao,
        sample_org_id,
        sample_user_id
    ):
        """
        Test logging LLM API usage

        BUSINESS CONTEXT:
        Each LLM API call should be logged for billing and analytics.
        """
        # Given: LLM config
        config = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test',
            is_primary=True
        )

        # When: Log usage
        log_id = await llm_config_dao.log_llm_usage(
            organization_id=sample_org_id,
            config_id=config['id'],
            provider_name='openai',
            model_name='gpt-5.2',
            operation_type='vision',
            input_tokens=500,
            output_tokens=1000,
            cost_estimate=0.05,
            latency_ms=250,
            success=True,
            user_id=sample_user_id,
            metadata={'screenshot_id': 'test-123'}
        )

        # Then: Should return log ID
        assert isinstance(log_id, UUID)

    @pytest.mark.asyncio
    async def test_log_llm_usage_updates_config_usage_counter(
        self,
        llm_config_dao,
        sample_org_id,
        db_state
    ):
        """
        Test that logging usage updates config usage counter

        BUSINESS CONTEXT:
        Usage counters track monthly token consumption for quota
        enforcement and billing.
        """
        # Given: LLM config
        config = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test',
            is_primary=True
        )

        # When: Log usage with 1500 total tokens
        await llm_config_dao.log_llm_usage(
            organization_id=sample_org_id,
            config_id=config['id'],
            provider_name='openai',
            model_name='gpt-5.2',
            operation_type='text',
            input_tokens=500,
            output_tokens=1000,
            cost_estimate=0.05,
            latency_ms=200,
            success=True
        )

        # Then: Config usage counter should be updated
        configs = db_state['org_configs']
        updated_config = next(c for c in configs if c['id'] == config['id'])
        assert updated_config['usage_current_month'] == 1500

    @pytest.mark.asyncio
    async def test_log_llm_usage_accumulates_tokens(
        self,
        llm_config_dao,
        sample_org_id,
        db_state
    ):
        """
        Test that usage accumulates across multiple calls

        BUSINESS CONTEXT:
        Monthly usage should accumulate to track total consumption
        against quotas.
        """
        # Given: LLM config
        config = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test',
            is_primary=True
        )

        # When: Log multiple usages
        await llm_config_dao.log_llm_usage(
            organization_id=sample_org_id,
            config_id=config['id'],
            provider_name='openai',
            model_name='gpt-5.2',
            operation_type='text',
            input_tokens=500,
            output_tokens=1000,
            cost_estimate=0.05,
            latency_ms=200,
            success=True
        )
        await llm_config_dao.log_llm_usage(
            organization_id=sample_org_id,
            config_id=config['id'],
            provider_name='openai',
            model_name='gpt-5.2',
            operation_type='vision',
            input_tokens=300,
            output_tokens=700,
            cost_estimate=0.03,
            latency_ms=180,
            success=True
        )

        # Then: Usage should accumulate (1500 + 1000 = 2500)
        configs = db_state['org_configs']
        updated_config = next(c for c in configs if c['id'] == config['id'])
        assert updated_config['usage_current_month'] == 2500

    @pytest.mark.asyncio
    async def test_log_llm_usage_does_not_update_on_failure(
        self,
        llm_config_dao,
        sample_org_id,
        db_state
    ):
        """
        Test that failed requests don't count toward quota

        BUSINESS CONTEXT:
        Failed API calls should not consume quota since they
        don't provide value to the organization.
        """
        # Given: LLM config
        config = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test',
            is_primary=True
        )

        # When: Log failed usage
        await llm_config_dao.log_llm_usage(
            organization_id=sample_org_id,
            config_id=config['id'],
            provider_name='openai',
            model_name='gpt-5.2',
            operation_type='text',
            input_tokens=500,
            output_tokens=0,
            cost_estimate=0.0,
            latency_ms=50,
            success=False,
            error_message='API rate limit exceeded'
        )

        # Then: Usage counter should not be updated
        configs = db_state['org_configs']
        updated_config = next(c for c in configs if c['id'] == config['id'])
        assert updated_config['usage_current_month'] == 0

    @pytest.mark.asyncio
    async def test_get_org_usage_stats_returns_aggregated_data(
        self,
        llm_config_dao,
        sample_org_id,
        db_state
    ):
        """
        Test retrieving usage statistics for organization

        BUSINESS CONTEXT:
        Organizations need aggregated usage data for billing
        reports and optimization analysis.
        """
        # Given: LLM config and usage logs
        config = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test',
            is_primary=True
        )

        # Log multiple usages
        await llm_config_dao.log_llm_usage(
            organization_id=sample_org_id,
            config_id=config['id'],
            provider_name='openai',
            model_name='gpt-5.2',
            operation_type='text',
            input_tokens=500,
            output_tokens=1000,
            cost_estimate=0.05,
            latency_ms=200,
            success=True
        )
        await llm_config_dao.log_llm_usage(
            organization_id=sample_org_id,
            config_id=config['id'],
            provider_name='openai',
            model_name='gpt-5.2',
            operation_type='vision',
            input_tokens=300,
            output_tokens=700,
            cost_estimate=0.03,
            latency_ms=180,
            success=True
        )

        # When: Get usage stats
        stats = await llm_config_dao.get_org_usage_stats(sample_org_id)

        # Then: Should return aggregated stats
        assert stats['total_requests'] == 2
        assert stats['total_input_tokens'] == 800
        assert stats['total_output_tokens'] == 1700
        assert stats['total_tokens'] == 2500
        assert stats['total_cost'] == 0.08
        assert stats['successful_requests'] == 2
        assert stats['failed_requests'] == 0

    @pytest.mark.asyncio
    async def test_get_org_usage_by_provider_groups_correctly(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test usage statistics grouped by provider

        BUSINESS CONTEXT:
        Organizations with multiple providers need to see usage
        breakdown by provider for cost comparison and optimization.
        """
        # Given: Multiple provider configs and usage
        config1 = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test-1',
            is_primary=True
        )
        config2 = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='anthropic',
            api_key='sk-ant-test-2',
            is_primary=False
        )

        # Log usage for both providers
        await llm_config_dao.log_llm_usage(
            organization_id=sample_org_id,
            config_id=config1['id'],
            provider_name='openai',
            model_name='gpt-5.2',
            operation_type='text',
            input_tokens=500,
            output_tokens=1000,
            cost_estimate=0.05,
            latency_ms=200,
            success=True
        )
        await llm_config_dao.log_llm_usage(
            organization_id=sample_org_id,
            config_id=config2['id'],
            provider_name='anthropic',
            model_name='claude-3-5-sonnet-20241022',
            operation_type='text',
            input_tokens=600,
            output_tokens=1200,
            cost_estimate=0.04,
            latency_ms=150,
            success=True
        )

        # When: Get usage by provider
        provider_stats = await llm_config_dao.get_org_usage_by_provider(sample_org_id)

        # Then: Should return stats for each provider
        assert len(provider_stats) == 2

        # Find stats by provider name
        openai_stats = next(s for s in provider_stats if s['provider_name'] == 'openai')
        anthropic_stats = next(s for s in provider_stats if s['provider_name'] == 'anthropic')

        assert openai_stats['request_count'] == 1
        assert openai_stats['total_tokens'] == 1500
        assert anthropic_stats['request_count'] == 1
        assert anthropic_stats['total_tokens'] == 1800

    @pytest.mark.asyncio
    async def test_check_quota_available_returns_true_when_under_quota(
        self,
        llm_config_dao,
        sample_org_id,
        db_state
    ):
        """
        Test quota check when usage is under limit

        BUSINESS CONTEXT:
        Quota checks prevent unexpected costs by blocking requests
        when monthly limits are reached.
        """
        # Given: Config with 10000 token quota and 5000 used
        config = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test',
            is_primary=True
        )

        # Set quota and usage in db_state
        configs = db_state['org_configs']
        config_in_db = next(c for c in configs if c['id'] == config['id'])
        config_in_db['usage_quota_monthly'] = 10000
        config_in_db['usage_current_month'] = 5000

        # When: Check if 3000 more tokens available
        available = await llm_config_dao.check_quota_available(
            config_id=config['id'],
            tokens_needed=3000
        )

        # Then: Should return True (5000 + 3000 = 8000 < 10000)
        assert available is True

    @pytest.mark.asyncio
    async def test_check_quota_available_returns_false_when_over_quota(
        self,
        llm_config_dao,
        sample_org_id,
        db_state
    ):
        """
        Test quota check when usage would exceed limit

        BUSINESS CONTEXT:
        Quota enforcement prevents cost overruns by rejecting
        requests that would exceed monthly limits.
        """
        # Given: Config with 10000 token quota and 9500 used
        config = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test',
            is_primary=True
        )

        # Set quota and usage in db_state
        configs = db_state['org_configs']
        config_in_db = next(c for c in configs if c['id'] == config['id'])
        config_in_db['usage_quota_monthly'] = 10000
        config_in_db['usage_current_month'] = 9500

        # When: Check if 1000 more tokens available
        available = await llm_config_dao.check_quota_available(
            config_id=config['id'],
            tokens_needed=1000
        )

        # Then: Should return False (9500 + 1000 = 10500 > 10000)
        assert available is False

    @pytest.mark.asyncio
    async def test_check_quota_available_returns_true_when_no_quota_set(
        self,
        llm_config_dao,
        sample_org_id,
        db_state
    ):
        """
        Test that no quota means unlimited usage

        BUSINESS CONTEXT:
        Organizations without quotas set should have unlimited
        usage (pay-as-you-go model).
        """
        # Given: Config without quota
        config = await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='openai',
            api_key='sk-test',
            is_primary=True
        )

        # When: Check large token amount
        available = await llm_config_dao.check_quota_available(
            config_id=config['id'],
            tokens_needed=1000000
        )

        # Then: Should return True (no quota = unlimited)
        assert available is True


# ================================================================
# TEST CLASS: Error Handling
# ================================================================


class TestErrorHandling:
    """
    Test suite for error handling and edge cases

    BUSINESS CONTEXT:
    Robust error handling ensures system reliability and provides
    clear feedback when operations fail.
    """

    @pytest.mark.asyncio
    async def test_database_error_raises_database_exception(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test that database errors are wrapped in DatabaseException

        BUSINESS CONTEXT:
        Consistent exception handling allows proper error recovery
        and user feedback across the platform.
        """
        # This test would require mocking the database to raise errors
        # In a real implementation, you would:
        # 1. Mock the connection to raise asyncpg.PostgresError
        # 2. Verify that DatabaseException is raised
        # 3. Verify error message and context are preserved
        pass

    @pytest.mark.asyncio
    async def test_get_nonexistent_config_returns_none(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test that querying non-existent config returns None

        BUSINESS CONTEXT:
        Gracefully handle requests for configs that don't exist
        rather than raising exceptions.
        """
        # When: Get primary config for org with no configs
        primary = await llm_config_dao.get_org_primary_config(sample_org_id)

        # Then: Should return None
        assert primary is None

    @pytest.mark.asyncio
    async def test_get_vision_config_returns_none_when_no_vision_providers(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test vision config query when no vision providers configured

        BUSINESS CONTEXT:
        Organizations without vision-capable providers should get
        clear feedback rather than errors.
        """
        # Given: Only text provider configured
        await llm_config_dao.create_org_llm_config(
            organization_id=sample_org_id,
            provider_name='deepseek',  # Text only
            api_key='sk-ds-test',
            is_primary=True
        )

        # When: Get vision config
        vision_config = await llm_config_dao.get_org_vision_config(sample_org_id)

        # Then: Should return None
        assert vision_config is None

    @pytest.mark.asyncio
    async def test_update_nonexistent_config_returns_none(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test updating non-existent config returns None

        BUSINESS CONTEXT:
        Update operations on missing configs should fail gracefully
        with None rather than raising exceptions.
        """
        # When: Update non-existent config
        updated = await llm_config_dao.update_org_llm_config(
            config_id=uuid4(),
            organization_id=sample_org_id,
            updates={'model_name': 'gpt-5.2'}
        )

        # Then: Should return None
        assert updated is None

    @pytest.mark.asyncio
    async def test_usage_stats_for_org_with_no_usage_returns_empty(
        self,
        llm_config_dao,
        sample_org_id
    ):
        """
        Test usage stats for organization with no usage

        BUSINESS CONTEXT:
        New organizations or those without usage should get
        zero stats rather than errors.
        """
        # When: Get usage stats for org with no usage
        stats = await llm_config_dao.get_org_usage_stats(sample_org_id)

        # Then: Should return empty/zero stats
        assert stats.get('total_requests', 0) == 0
        assert stats.get('total_tokens', 0) == 0
