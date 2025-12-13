-- Organization LLM Provider Configuration Migration
-- Created: 2025-12-13
-- Purpose: Enable organizations to configure their preferred LLM providers and API keys
-- for screenshot-to-course generation and other AI features

-- ========================================
-- LLM PROVIDERS REFERENCE TABLE
-- ========================================
-- Stores metadata about supported LLM providers including API endpoints and capabilities

CREATE TABLE IF NOT EXISTS llm_providers (
    id SERIAL PRIMARY KEY,
    provider_name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    api_base_url VARCHAR(500) NOT NULL,
    vision_endpoint VARCHAR(200),
    text_endpoint VARCHAR(200),
    auth_type VARCHAR(50) NOT NULL DEFAULT 'bearer',
    supports_vision BOOLEAN DEFAULT FALSE,
    supports_streaming BOOLEAN DEFAULT FALSE,
    default_model VARCHAR(100),
    available_models JSONB DEFAULT '[]',
    rate_limit_requests_per_minute INTEGER DEFAULT 60,
    max_tokens_per_request INTEGER DEFAULT 4096,
    is_local BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert supported providers
INSERT INTO llm_providers (
    provider_name, display_name, api_base_url, vision_endpoint, text_endpoint,
    auth_type, supports_vision, supports_streaming, default_model, available_models,
    rate_limit_requests_per_minute, max_tokens_per_request, is_local
) VALUES
    -- OpenAI GPT-5.2
    (
        'openai', 'OpenAI', 'https://api.openai.com/v1',
        '/chat/completions', '/chat/completions',
        'bearer', TRUE, TRUE, 'gpt-5.2',
        '["gpt-5.2", "gpt-5.2-vision", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]',
        500, 128000, FALSE
    ),
    -- Anthropic Claude
    (
        'anthropic', 'Anthropic Claude', 'https://api.anthropic.com/v1',
        '/messages', '/messages',
        'x-api-key', TRUE, TRUE, 'claude-3-5-sonnet-20241022',
        '["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"]',
        50, 200000, FALSE
    ),
    -- Deepseek
    (
        'deepseek', 'Deepseek', 'https://api.deepseek.com/v1',
        '/chat/completions', '/chat/completions',
        'bearer', TRUE, TRUE, 'deepseek-vl',
        '["deepseek-vl", "deepseek-chat", "deepseek-coder"]',
        60, 32000, FALSE
    ),
    -- Qwen (Alibaba)
    (
        'qwen', 'Qwen (Alibaba)', 'https://dashscope.aliyuncs.com/api/v1',
        '/services/aigc/multimodal-generation/generation', '/services/aigc/text-generation/generation',
        'bearer', TRUE, TRUE, 'qwen-vl-max',
        '["qwen-vl-max", "qwen-vl-plus", "qwen-max", "qwen-plus", "qwen-turbo"]',
        100, 128000, FALSE
    ),
    -- Ollama (Local)
    (
        'ollama', 'Ollama (Local)', 'http://localhost:11434',
        '/api/generate', '/api/generate',
        'none', TRUE, TRUE, 'llava',
        '["llava", "llava:13b", "bakllava", "llama3.2-vision", "moondream"]',
        1000, 32000, TRUE
    ),
    -- Meta Llama (via Together AI)
    (
        'llama', 'Meta Llama', 'https://api.together.xyz/v1',
        '/chat/completions', '/chat/completions',
        'bearer', TRUE, TRUE, 'meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo',
        '["meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo", "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo", "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo"]',
        60, 131072, FALSE
    ),
    -- Google Gemini
    (
        'gemini', 'Google Gemini', 'https://generativelanguage.googleapis.com/v1beta',
        '/models/{model}:generateContent', '/models/{model}:generateContent',
        'api_key_param', TRUE, TRUE, 'gemini-2.0-flash-exp',
        '["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-pro-vision"]',
        60, 2000000, FALSE
    ),
    -- Mistral AI
    (
        'mistral', 'Mistral AI', 'https://api.mistral.ai/v1',
        '/chat/completions', '/chat/completions',
        'bearer', TRUE, TRUE, 'pixtral-large-latest',
        '["pixtral-large-latest", "pixtral-12b-2409", "mistral-large-latest", "mistral-medium-latest", "mistral-small-latest", "codestral-latest"]',
        100, 128000, FALSE
    )
ON CONFLICT (provider_name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    api_base_url = EXCLUDED.api_base_url,
    vision_endpoint = EXCLUDED.vision_endpoint,
    text_endpoint = EXCLUDED.text_endpoint,
    supports_vision = EXCLUDED.supports_vision,
    available_models = EXCLUDED.available_models,
    updated_at = NOW();

-- Indexes for llm_providers
CREATE INDEX IF NOT EXISTS idx_llm_providers_active ON llm_providers(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_llm_providers_vision ON llm_providers(supports_vision) WHERE supports_vision = TRUE;

-- ========================================
-- ORGANIZATION LLM CONFIGURATION TABLE
-- ========================================
-- Stores organization-specific LLM provider settings and encrypted API keys

CREATE TABLE IF NOT EXISTS organization_llm_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    provider_id INTEGER NOT NULL REFERENCES llm_providers(id),
    api_key_encrypted TEXT,
    api_key_hash VARCHAR(64),
    model_name VARCHAR(100),
    custom_base_url VARCHAR(500),
    max_tokens_override INTEGER,
    temperature DECIMAL(3,2) DEFAULT 0.7 CHECK (temperature >= 0 AND temperature <= 2),
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    usage_quota_monthly INTEGER,
    usage_current_month INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

-- Partial unique index for primary provider (only when is_primary = true)
CREATE UNIQUE INDEX IF NOT EXISTS idx_org_llm_primary
    ON organization_llm_config(organization_id)
    WHERE is_primary = TRUE;

-- Indexes for organization_llm_config
CREATE INDEX IF NOT EXISTS idx_org_llm_config_org ON organization_llm_config(organization_id);
CREATE INDEX IF NOT EXISTS idx_org_llm_config_provider ON organization_llm_config(provider_id);
CREATE INDEX IF NOT EXISTS idx_org_llm_config_active ON organization_llm_config(is_active) WHERE is_active = TRUE;

-- ========================================
-- LLM USAGE TRACKING TABLE
-- ========================================
-- Tracks API usage for billing, quotas, and analytics

CREATE TABLE IF NOT EXISTS llm_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    config_id UUID REFERENCES organization_llm_config(id) ON DELETE SET NULL,
    provider_name VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cost_estimate DECIMAL(10,6),
    latency_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    request_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id UUID
);

-- Indexes for usage tracking
CREATE INDEX IF NOT EXISTS idx_llm_usage_org ON llm_usage_log(organization_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_created ON llm_usage_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_usage_provider ON llm_usage_log(provider_name);
CREATE INDEX IF NOT EXISTS idx_llm_usage_operation ON llm_usage_log(operation_type);

-- Partition hint for future partitioning by month
COMMENT ON TABLE llm_usage_log IS 'LLM API usage tracking - consider partitioning by created_at for high volume';

-- ========================================
-- HELPER FUNCTIONS
-- ========================================

-- Function to get active LLM config for an organization
CREATE OR REPLACE FUNCTION get_org_llm_config(p_organization_id UUID)
RETURNS TABLE (
    config_id UUID,
    provider_name VARCHAR,
    display_name VARCHAR,
    model_name VARCHAR,
    api_base_url VARCHAR,
    vision_endpoint VARCHAR,
    supports_vision BOOLEAN,
    is_primary BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        olc.id AS config_id,
        lp.provider_name,
        lp.display_name,
        COALESCE(olc.model_name, lp.default_model) AS model_name,
        COALESCE(olc.custom_base_url, lp.api_base_url) AS api_base_url,
        lp.vision_endpoint,
        lp.supports_vision,
        olc.is_primary
    FROM organization_llm_config olc
    JOIN llm_providers lp ON olc.provider_id = lp.id
    WHERE olc.organization_id = p_organization_id
      AND olc.is_active = TRUE
      AND lp.is_active = TRUE
    ORDER BY olc.is_primary DESC, olc.created_at;
END;
$$;

-- Function to get primary vision-capable provider for an organization
CREATE OR REPLACE FUNCTION get_org_vision_provider(p_organization_id UUID)
RETURNS TABLE (
    config_id UUID,
    provider_name VARCHAR,
    model_name VARCHAR,
    api_base_url VARCHAR,
    vision_endpoint VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        olc.id AS config_id,
        lp.provider_name,
        COALESCE(olc.model_name, lp.default_model) AS model_name,
        COALESCE(olc.custom_base_url, lp.api_base_url) AS api_base_url,
        lp.vision_endpoint
    FROM organization_llm_config olc
    JOIN llm_providers lp ON olc.provider_id = lp.id
    WHERE olc.organization_id = p_organization_id
      AND olc.is_active = TRUE
      AND lp.is_active = TRUE
      AND lp.supports_vision = TRUE
    ORDER BY olc.is_primary DESC, olc.created_at
    LIMIT 1;
END;
$$;

-- Function to increment monthly usage
CREATE OR REPLACE FUNCTION increment_llm_usage(
    p_config_id UUID,
    p_tokens INTEGER
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE organization_llm_config
    SET
        usage_current_month = usage_current_month + p_tokens,
        last_used_at = NOW(),
        updated_at = NOW()
    WHERE id = p_config_id;
END;
$$;

-- Function to reset monthly usage (run via cron on 1st of each month)
CREATE OR REPLACE FUNCTION reset_monthly_llm_usage()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE organization_llm_config
    SET
        usage_current_month = 0,
        updated_at = NOW();
END;
$$;

-- ========================================
-- COMMENTS
-- ========================================

COMMENT ON TABLE llm_providers IS 'Reference table of supported LLM providers with their API configurations';
COMMENT ON TABLE organization_llm_config IS 'Organization-specific LLM provider configurations with encrypted API keys';
COMMENT ON TABLE llm_usage_log IS 'Detailed log of all LLM API calls for billing and analytics';
COMMENT ON FUNCTION get_org_llm_config IS 'Get all active LLM configurations for an organization';
COMMENT ON FUNCTION get_org_vision_provider IS 'Get the primary vision-capable LLM provider for an organization';
COMMENT ON FUNCTION increment_llm_usage IS 'Increment token usage counter for a configuration';
COMMENT ON FUNCTION reset_monthly_llm_usage IS 'Reset monthly usage counters (run on 1st of month)';
