-- Migration: 032_integrations.sql
-- What: Database schema for external integrations (LTI, Calendar, Slack).
-- Where: PostgreSQL database for organization and course management.
-- Why: Enables:
--      1. LTI 1.3 tool integration with external learning platforms
--      2. Calendar synchronization (Google, Outlook, Apple)
--      3. Slack workspace integration for notifications
--      4. Webhook management for external events
--      5. OAuth token management for integrations

-- ============================================================================
-- LTI (LEARNING TOOLS INTEROPERABILITY) TABLES
-- ============================================================================

-- LTI Platform Registration
-- Stores LMS platforms (Canvas, Moodle, etc.) that connect to us as a tool
CREATE TABLE IF NOT EXISTS lti_platform_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Platform identification
    platform_name VARCHAR(255) NOT NULL,
    issuer VARCHAR(500) NOT NULL,  -- LMS issuer URL
    client_id VARCHAR(255) NOT NULL,
    deployment_id VARCHAR(255),

    -- Platform URLs (for tool to platform communication)
    auth_login_url VARCHAR(500) NOT NULL,
    auth_token_url VARCHAR(500) NOT NULL,
    jwks_url VARCHAR(500) NOT NULL,

    -- Our tool configuration
    tool_public_key TEXT,
    tool_private_key TEXT,  -- Encrypted

    -- Platform public keys (for verifying platform messages)
    platform_public_keys JSONB DEFAULT '[]'::jsonb,

    -- Scopes and capabilities
    scopes TEXT[] DEFAULT '{}',
    deep_linking_enabled BOOLEAN DEFAULT true,
    names_role_service_enabled BOOLEAN DEFAULT true,
    assignment_grade_service_enabled BOOLEAN DEFAULT true,

    -- Status
    is_active BOOLEAN DEFAULT true,
    verified_at TIMESTAMP WITH TIME ZONE,
    last_connection_at TIMESTAMP WITH TIME ZONE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),

    UNIQUE(issuer, client_id, deployment_id)
);

-- LTI Context (Course/Resource link)
CREATE TABLE IF NOT EXISTS lti_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform_id UUID NOT NULL REFERENCES lti_platform_registrations(id) ON DELETE CASCADE,

    -- LTI context identification
    lti_context_id VARCHAR(255) NOT NULL,
    lti_context_type VARCHAR(50),  -- CourseTemplate, CourseOffering, etc.
    lti_context_title VARCHAR(500),
    lti_context_label VARCHAR(100),

    -- Link to our course
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    course_instance_id UUID REFERENCES course_instances(id) ON DELETE SET NULL,

    -- Deep linking
    resource_link_id VARCHAR(255),
    resource_link_title VARCHAR(500),

    -- Membership sync
    last_roster_sync TIMESTAMP WITH TIME ZONE,
    auto_roster_sync BOOLEAN DEFAULT false,
    roster_sync_interval_hours INTEGER DEFAULT 24,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(platform_id, lti_context_id)
);

-- LTI User Mapping
CREATE TABLE IF NOT EXISTS lti_user_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform_id UUID NOT NULL REFERENCES lti_platform_registrations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- LTI user identification
    lti_user_id VARCHAR(255) NOT NULL,
    lti_email VARCHAR(255),
    lti_name VARCHAR(500),
    lti_given_name VARCHAR(255),
    lti_family_name VARCHAR(255),
    lti_picture_url VARCHAR(500),

    -- Roles from LTI
    lti_roles TEXT[] DEFAULT '{}',  -- LTI role URIs
    mapped_role_name VARCHAR(50),  -- Our system role

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(platform_id, lti_user_id)
);

-- LTI Grade Passback
CREATE TABLE IF NOT EXISTS lti_grade_sync (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_id UUID NOT NULL REFERENCES lti_contexts(id) ON DELETE CASCADE,
    user_mapping_id UUID NOT NULL REFERENCES lti_user_mappings(id) ON DELETE CASCADE,

    -- Grade details
    lineitem_id VARCHAR(500),  -- AGS lineitem URL
    score DECIMAL(5,2),
    max_score DECIMAL(5,2) DEFAULT 100.00,
    comment TEXT,

    -- Source of grade
    quiz_attempt_id UUID,
    assignment_id UUID,

    -- Sync status
    sync_status VARCHAR(20) DEFAULT 'pending',  -- pending, sent, confirmed, failed
    last_sync_attempt TIMESTAMP WITH TIME ZONE,
    last_sync_success TIMESTAMP WITH TIME ZONE,
    sync_error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CALENDAR INTEGRATION TABLES
-- ============================================================================

-- Calendar Provider Configuration
CREATE TABLE IF NOT EXISTS calendar_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Provider details
    provider_type VARCHAR(50) NOT NULL,  -- google, outlook, apple, caldav
    provider_name VARCHAR(100),

    -- OAuth credentials (encrypted)
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,

    -- Calendar identification
    calendar_id VARCHAR(255),  -- The specific calendar to sync with
    calendar_name VARCHAR(255),
    calendar_timezone VARCHAR(50),

    -- Sync settings
    sync_enabled BOOLEAN DEFAULT true,
    sync_direction VARCHAR(20) DEFAULT 'bidirectional',  -- bidirectional, push_only, pull_only
    sync_deadline_reminders BOOLEAN DEFAULT true,
    sync_class_schedules BOOLEAN DEFAULT true,
    sync_quiz_dates BOOLEAN DEFAULT true,
    reminder_minutes_before INTEGER DEFAULT 30,

    -- Status
    is_connected BOOLEAN DEFAULT false,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    last_sync_error TEXT,
    connection_error_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, provider_type, calendar_id)
);

-- Calendar Events (synced events)
CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES calendar_providers(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- External event reference
    external_event_id VARCHAR(255),
    external_calendar_id VARCHAR(255),

    -- Event details
    title VARCHAR(500) NOT NULL,
    description TEXT,
    location VARCHAR(500),

    -- Timing
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    all_day BOOLEAN DEFAULT false,
    timezone VARCHAR(50),

    -- Recurrence
    is_recurring BOOLEAN DEFAULT false,
    recurrence_rule TEXT,  -- RRULE format
    recurring_event_id UUID,  -- Parent recurring event

    -- Source within our platform
    event_type VARCHAR(50),  -- deadline, class_session, quiz, lab, office_hours
    source_type VARCHAR(50),  -- course, assignment, quiz, course_instance
    source_id UUID,

    -- Sync status
    sync_status VARCHAR(20) DEFAULT 'synced',  -- synced, pending, conflict, error
    local_updated_at TIMESTAMP WITH TIME ZONE,
    remote_updated_at TIMESTAMP WITH TIME ZONE,
    last_sync_at TIMESTAMP WITH TIME ZONE,

    -- Reminders
    reminder_sent BOOLEAN DEFAULT false,
    reminder_sent_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(provider_id, external_event_id)
);

-- ============================================================================
-- SLACK INTEGRATION TABLES
-- ============================================================================

-- Slack Workspace Configuration
CREATE TABLE IF NOT EXISTS slack_workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Slack workspace details
    workspace_id VARCHAR(100) NOT NULL,
    workspace_name VARCHAR(255),
    workspace_domain VARCHAR(100),

    -- OAuth credentials (encrypted)
    bot_token TEXT NOT NULL,
    bot_user_id VARCHAR(50),
    app_id VARCHAR(50),

    -- Permissions and scopes
    scopes TEXT[] DEFAULT '{}',

    -- Default notification channels
    default_announcements_channel VARCHAR(100),
    default_alerts_channel VARCHAR(100),

    -- Features
    enable_notifications BOOLEAN DEFAULT true,
    enable_commands BOOLEAN DEFAULT true,
    enable_ai_assistant BOOLEAN DEFAULT false,

    -- Status
    is_active BOOLEAN DEFAULT true,
    installed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    installed_by UUID REFERENCES users(id),

    UNIQUE(organization_id, workspace_id)
);

-- Slack Channel Mappings
CREATE TABLE IF NOT EXISTS slack_channel_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES slack_workspaces(id) ON DELETE CASCADE,

    -- Slack channel details
    channel_id VARCHAR(100) NOT NULL,
    channel_name VARCHAR(255),
    channel_type VARCHAR(20) DEFAULT 'channel',  -- channel, private, dm

    -- Mapping to our entities
    entity_type VARCHAR(50) NOT NULL,  -- course, course_instance, project, organization
    entity_id UUID NOT NULL,

    -- Notification settings
    notify_announcements BOOLEAN DEFAULT true,
    notify_deadlines BOOLEAN DEFAULT true,
    notify_grades BOOLEAN DEFAULT true,
    notify_new_content BOOLEAN DEFAULT true,
    notify_discussions BOOLEAN DEFAULT true,

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_message_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(workspace_id, channel_id)
);

-- Slack User Mappings
CREATE TABLE IF NOT EXISTS slack_user_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES slack_workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Slack user details
    slack_user_id VARCHAR(50) NOT NULL,
    slack_username VARCHAR(100),
    slack_email VARCHAR(255),
    slack_real_name VARCHAR(255),
    slack_display_name VARCHAR(255),

    -- Notification preferences
    dm_notifications_enabled BOOLEAN DEFAULT true,
    mention_notifications_enabled BOOLEAN DEFAULT true,
    daily_digest_enabled BOOLEAN DEFAULT false,
    digest_time TIME,

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_dm_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(workspace_id, slack_user_id)
);

-- Slack Message History (for analytics and audit)
CREATE TABLE IF NOT EXISTS slack_message_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES slack_workspaces(id) ON DELETE CASCADE,
    channel_mapping_id UUID REFERENCES slack_channel_mappings(id) ON DELETE SET NULL,
    user_mapping_id UUID REFERENCES slack_user_mappings(id) ON DELETE SET NULL,

    -- Message details
    slack_message_ts VARCHAR(50),  -- Slack's message timestamp ID
    message_type VARCHAR(50) NOT NULL,  -- announcement, deadline_reminder, grade_notification, etc.
    message_text TEXT,

    -- Source
    source_type VARCHAR(50),
    source_id UUID,

    -- Delivery status
    delivery_status VARCHAR(20) DEFAULT 'sent',  -- sent, delivered, read, failed
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,

    -- Engagement
    reaction_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- WEBHOOK MANAGEMENT TABLES
-- ============================================================================

-- Outbound Webhooks (we send to external services)
CREATE TABLE IF NOT EXISTS outbound_webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Webhook details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    target_url VARCHAR(500) NOT NULL,

    -- Authentication
    auth_type VARCHAR(20) DEFAULT 'none',  -- none, bearer, basic, hmac
    auth_secret TEXT,  -- Encrypted

    -- Events to trigger
    event_types TEXT[] DEFAULT '{}',  -- course.created, enrollment.completed, etc.

    -- Filtering
    filter_conditions JSONB DEFAULT '{}'::jsonb,

    -- Delivery settings
    retry_count INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 60,
    timeout_seconds INTEGER DEFAULT 30,

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

-- Webhook Delivery Logs
CREATE TABLE IF NOT EXISTS webhook_delivery_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id UUID NOT NULL REFERENCES outbound_webhooks(id) ON DELETE CASCADE,

    -- Event details
    event_type VARCHAR(100) NOT NULL,
    event_id UUID NOT NULL,
    payload JSONB NOT NULL,

    -- Delivery attempt
    attempt_number INTEGER DEFAULT 1,
    request_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    response_timestamp TIMESTAMP WITH TIME ZONE,

    -- Response
    response_status_code INTEGER,
    response_body TEXT,
    response_headers JSONB,

    -- Status
    delivery_status VARCHAR(20) DEFAULT 'pending',  -- pending, success, failed, retry_scheduled
    error_message TEXT,

    next_retry_at TIMESTAMP WITH TIME ZONE
);

-- Inbound Webhooks (external services send to us)
CREATE TABLE IF NOT EXISTS inbound_webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Webhook details
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Endpoint
    webhook_token VARCHAR(100) NOT NULL UNIQUE,  -- Used in URL path

    -- Authentication
    auth_type VARCHAR(20) DEFAULT 'token',  -- token, hmac, none
    auth_secret TEXT,  -- For HMAC verification
    allowed_ips TEXT[],  -- IP whitelist

    -- Processing
    handler_type VARCHAR(50) NOT NULL,  -- github, stripe, zapier, custom
    handler_config JSONB DEFAULT '{}'::jsonb,

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_received_at TIMESTAMP WITH TIME ZONE,
    total_received INTEGER DEFAULT 0,
    total_processed INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

-- Inbound Webhook Logs
CREATE TABLE IF NOT EXISTS inbound_webhook_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id UUID NOT NULL REFERENCES inbound_webhooks(id) ON DELETE CASCADE,

    -- Request details
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_ip VARCHAR(45),
    request_method VARCHAR(10),
    request_headers JSONB,
    request_body JSONB,

    -- Validation
    signature_valid BOOLEAN,
    validation_errors TEXT[],

    -- Processing
    processing_status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, success, failed
    processed_at TIMESTAMP WITH TIME ZONE,
    processing_result JSONB,
    error_message TEXT
);

-- ============================================================================
-- OAUTH TOKENS TABLE (Shared across integrations)
-- ============================================================================

CREATE TABLE IF NOT EXISTS oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    -- Provider details
    provider VARCHAR(50) NOT NULL,  -- google, microsoft, slack, github, etc.
    provider_user_id VARCHAR(255),

    -- Tokens (encrypted)
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',

    -- Expiration
    expires_at TIMESTAMP WITH TIME ZONE,
    refresh_expires_at TIMESTAMP WITH TIME ZONE,

    -- Scopes
    scopes TEXT[] DEFAULT '{}',

    -- Status
    is_valid BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    last_refreshed_at TIMESTAMP WITH TIME ZONE,

    -- Error tracking
    consecutive_failures INTEGER DEFAULT 0,
    last_error TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, provider, provider_user_id)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- LTI indexes
CREATE INDEX IF NOT EXISTS idx_lti_platforms_org ON lti_platform_registrations(organization_id);
CREATE INDEX IF NOT EXISTS idx_lti_platforms_issuer ON lti_platform_registrations(issuer);
CREATE INDEX IF NOT EXISTS idx_lti_contexts_platform ON lti_contexts(platform_id);
CREATE INDEX IF NOT EXISTS idx_lti_contexts_course ON lti_contexts(course_id);
CREATE INDEX IF NOT EXISTS idx_lti_user_mappings_platform ON lti_user_mappings(platform_id);
CREATE INDEX IF NOT EXISTS idx_lti_user_mappings_user ON lti_user_mappings(user_id);
CREATE INDEX IF NOT EXISTS idx_lti_grade_sync_context ON lti_grade_sync(context_id);
CREATE INDEX IF NOT EXISTS idx_lti_grade_sync_status ON lti_grade_sync(sync_status);

-- Calendar indexes
CREATE INDEX IF NOT EXISTS idx_calendar_providers_user ON calendar_providers(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_providers_type ON calendar_providers(provider_type);
CREATE INDEX IF NOT EXISTS idx_calendar_events_provider ON calendar_events(provider_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_user ON calendar_events(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_start ON calendar_events(start_time);
CREATE INDEX IF NOT EXISTS idx_calendar_events_source ON calendar_events(source_type, source_id);

-- Slack indexes
CREATE INDEX IF NOT EXISTS idx_slack_workspaces_org ON slack_workspaces(organization_id);
CREATE INDEX IF NOT EXISTS idx_slack_channel_mappings_workspace ON slack_channel_mappings(workspace_id);
CREATE INDEX IF NOT EXISTS idx_slack_channel_mappings_entity ON slack_channel_mappings(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_slack_user_mappings_workspace ON slack_user_mappings(workspace_id);
CREATE INDEX IF NOT EXISTS idx_slack_user_mappings_user ON slack_user_mappings(user_id);
CREATE INDEX IF NOT EXISTS idx_slack_message_history_workspace ON slack_message_history(workspace_id);
CREATE INDEX IF NOT EXISTS idx_slack_message_history_sent ON slack_message_history(sent_at);

-- Webhook indexes
CREATE INDEX IF NOT EXISTS idx_outbound_webhooks_org ON outbound_webhooks(organization_id);
CREATE INDEX IF NOT EXISTS idx_outbound_webhooks_active ON outbound_webhooks(is_active);
CREATE INDEX IF NOT EXISTS idx_webhook_delivery_logs_webhook ON webhook_delivery_logs(webhook_id);
CREATE INDEX IF NOT EXISTS idx_webhook_delivery_logs_status ON webhook_delivery_logs(delivery_status);
CREATE INDEX IF NOT EXISTS idx_inbound_webhooks_org ON inbound_webhooks(organization_id);
CREATE INDEX IF NOT EXISTS idx_inbound_webhooks_token ON inbound_webhooks(webhook_token);
CREATE INDEX IF NOT EXISTS idx_inbound_webhook_logs_webhook ON inbound_webhook_logs(webhook_id);

-- OAuth indexes
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_user ON oauth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_org ON oauth_tokens(organization_id);
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_provider ON oauth_tokens(provider);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update timestamp triggers
CREATE OR REPLACE FUNCTION update_integration_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    -- LTI triggers
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_lti_platform_timestamp') THEN
        CREATE TRIGGER update_lti_platform_timestamp
            BEFORE UPDATE ON lti_platform_registrations
            FOR EACH ROW EXECUTE FUNCTION update_integration_timestamp();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_lti_context_timestamp') THEN
        CREATE TRIGGER update_lti_context_timestamp
            BEFORE UPDATE ON lti_contexts
            FOR EACH ROW EXECUTE FUNCTION update_integration_timestamp();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_lti_user_mapping_timestamp') THEN
        CREATE TRIGGER update_lti_user_mapping_timestamp
            BEFORE UPDATE ON lti_user_mappings
            FOR EACH ROW EXECUTE FUNCTION update_integration_timestamp();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_lti_grade_sync_timestamp') THEN
        CREATE TRIGGER update_lti_grade_sync_timestamp
            BEFORE UPDATE ON lti_grade_sync
            FOR EACH ROW EXECUTE FUNCTION update_integration_timestamp();
    END IF;

    -- Calendar triggers
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_calendar_provider_timestamp') THEN
        CREATE TRIGGER update_calendar_provider_timestamp
            BEFORE UPDATE ON calendar_providers
            FOR EACH ROW EXECUTE FUNCTION update_integration_timestamp();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_calendar_event_timestamp') THEN
        CREATE TRIGGER update_calendar_event_timestamp
            BEFORE UPDATE ON calendar_events
            FOR EACH ROW EXECUTE FUNCTION update_integration_timestamp();
    END IF;

    -- Slack triggers
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_slack_workspace_timestamp') THEN
        CREATE TRIGGER update_slack_workspace_timestamp
            BEFORE UPDATE ON slack_workspaces
            FOR EACH ROW EXECUTE FUNCTION update_integration_timestamp();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_slack_channel_mapping_timestamp') THEN
        CREATE TRIGGER update_slack_channel_mapping_timestamp
            BEFORE UPDATE ON slack_channel_mappings
            FOR EACH ROW EXECUTE FUNCTION update_integration_timestamp();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_slack_user_mapping_timestamp') THEN
        CREATE TRIGGER update_slack_user_mapping_timestamp
            BEFORE UPDATE ON slack_user_mappings
            FOR EACH ROW EXECUTE FUNCTION update_integration_timestamp();
    END IF;

    -- Webhook triggers
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_outbound_webhook_timestamp') THEN
        CREATE TRIGGER update_outbound_webhook_timestamp
            BEFORE UPDATE ON outbound_webhooks
            FOR EACH ROW EXECUTE FUNCTION update_integration_timestamp();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_inbound_webhook_timestamp') THEN
        CREATE TRIGGER update_inbound_webhook_timestamp
            BEFORE UPDATE ON inbound_webhooks
            FOR EACH ROW EXECUTE FUNCTION update_integration_timestamp();
    END IF;

    -- OAuth trigger
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_oauth_token_timestamp') THEN
        CREATE TRIGGER update_oauth_token_timestamp
            BEFORE UPDATE ON oauth_tokens
            FOR EACH ROW EXECUTE FUNCTION update_integration_timestamp();
    END IF;
END $$;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE lti_platform_registrations IS 'LTI 1.3 platform registrations for connecting external LMS systems';
COMMENT ON TABLE lti_contexts IS 'LTI contexts mapping external courses to internal courses';
COMMENT ON TABLE lti_user_mappings IS 'LTI user mappings between external LMS users and internal users';
COMMENT ON TABLE lti_grade_sync IS 'LTI grade passback records for AGS (Assignment and Grades Service)';

COMMENT ON TABLE calendar_providers IS 'User calendar provider configurations (Google, Outlook, etc.)';
COMMENT ON TABLE calendar_events IS 'Synced calendar events between platform and external calendars';

COMMENT ON TABLE slack_workspaces IS 'Slack workspace integrations for organizations';
COMMENT ON TABLE slack_channel_mappings IS 'Mapping between Slack channels and platform entities';
COMMENT ON TABLE slack_user_mappings IS 'Mapping between Slack users and platform users';
COMMENT ON TABLE slack_message_history IS 'History of Slack messages sent by the platform';

COMMENT ON TABLE outbound_webhooks IS 'Outbound webhook configurations for external service notifications';
COMMENT ON TABLE webhook_delivery_logs IS 'Delivery logs for outbound webhooks';
COMMENT ON TABLE inbound_webhooks IS 'Inbound webhook endpoints for receiving external events';
COMMENT ON TABLE inbound_webhook_logs IS 'Request logs for inbound webhooks';

COMMENT ON TABLE oauth_tokens IS 'OAuth tokens for all external integrations';
