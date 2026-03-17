/**
 * Integrations Service
 *
 * BUSINESS CONTEXT:
 * Manages external integrations for the course-creator platform including:
 * - LTI 1.3 platform connections for LMS integration
 * - Calendar synchronization (Google Calendar, Outlook)
 * - Slack workspace integration for notifications
 * - Outbound/inbound webhooks for external service communication
 * - OAuth token management for third-party service access
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses centralized apiClient with authentication
 * - Handles CRUD operations for all integration types
 * - Manages OAuth flows and token refresh
 * - Integrates with organization-management service (port 8005)
 *
 * WHY THIS APPROACH:
 * - Centralized integration management reduces code duplication
 * - Type-safe interfaces ensure data consistency
 * - Supports multi-tenant B2B architecture with organization-level isolation
 * - Provides comprehensive error handling for external service failures
 */

import { apiClient } from './apiClient';

// ============================================================================
// LTI INTERFACES
// ============================================================================

/**
 * LTI Platform Registration
 *
 * What: LTI 1.3 platform configuration for external LMS integration
 * Where: Used when connecting Canvas, Moodle, Blackboard, etc.
 * Why: Enables LTI tool launches and grade passback to external LMS
 */
export interface LTIPlatform {
  id: string;
  organization_id: string;
  platform_name: string;
  issuer: string;
  client_id: string;
  auth_login_url: string;
  auth_token_url: string;
  jwks_url: string;
  deployment_id?: string;
  scopes: string[];
  deep_linking_enabled: boolean;
  names_role_service_enabled: boolean;
  assignment_grade_service_enabled: boolean;
  is_active: boolean;
  verified_at?: string;
  last_connection_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateLTIPlatformRequest {
  platform_name: string;
  issuer: string;
  client_id: string;
  auth_login_url: string;
  auth_token_url: string;
  jwks_url: string;
  deployment_id?: string;
  scopes?: string[];
}

/**
 * LTI Context Mapping
 *
 * What: Maps external LMS course to platform course
 * Where: Created during LTI launch with context claim
 * Why: Enables course linking and roster synchronization
 */
export interface LTIContext {
  id: string;
  platform_id: string;
  lti_context_id: string;
  lti_context_type?: string;
  lti_context_title?: string;
  course_id?: string;
  auto_roster_sync: boolean;
  last_roster_sync?: string;
  created_at: string;
  updated_at: string;
}

/**
 * LTI Grade Sync Record
 *
 * What: Tracks grade passback to external LMS
 * Where: Created when student receives grade
 * Why: Enables asynchronous grade delivery via LTI AGS
 */
export interface LTIGradeSync {
  id: string;
  context_id: string;
  user_mapping_id: string;
  score: number;
  max_score: number;
  sync_status: 'pending' | 'sent' | 'confirmed' | 'failed' | 'retry_scheduled';
  last_sync_attempt?: string;
  last_sync_success?: string;
  sync_error_message?: string;
  retry_count: number;
  created_at: string;
}

// ============================================================================
// CALENDAR INTERFACES
// ============================================================================

/**
 * Calendar Provider Configuration
 *
 * What: User calendar integration settings
 * Where: Created when user authorizes calendar access
 * Why: Enables bidirectional calendar sync for deadlines and events
 */
export interface CalendarProvider {
  id: string;
  user_id: string;
  provider_type: 'google' | 'outlook' | 'apple' | 'caldav';
  provider_name?: string;
  calendar_id?: string;
  calendar_name?: string;
  calendar_timezone?: string;
  sync_enabled: boolean;
  sync_direction: 'bidirectional' | 'push_only' | 'pull_only';
  sync_deadline_reminders: boolean;
  sync_class_schedules: boolean;
  sync_quiz_dates: boolean;
  reminder_minutes_before: number;
  is_connected: boolean;
  last_sync_at?: string;
  last_sync_error?: string;
  created_at: string;
  updated_at: string;
}

export interface ConnectCalendarRequest {
  provider_type: 'google' | 'outlook' | 'apple' | 'caldav';
  access_token: string;
  refresh_token?: string;
  token_expires_at?: string;
  calendar_id?: string;
  calendar_name?: string;
  calendar_timezone?: string;
}

export interface UpdateCalendarSettingsRequest {
  sync_enabled?: boolean;
  sync_direction?: 'bidirectional' | 'push_only' | 'pull_only';
  sync_deadline_reminders?: boolean;
  sync_class_schedules?: boolean;
  sync_quiz_dates?: boolean;
  reminder_minutes_before?: number;
}

/**
 * Calendar Event
 *
 * What: Synced calendar event record
 * Where: Created during calendar synchronization
 * Why: Tracks events between platform and external calendar
 */
export interface CalendarEvent {
  id: string;
  provider_id: string;
  user_id: string;
  title: string;
  start_time: string;
  end_time: string;
  external_event_id?: string;
  description?: string;
  location?: string;
  event_type?: string;
  source_type?: string;
  source_id?: string;
  sync_status: 'synced' | 'pending' | 'conflict' | 'error';
  created_at: string;
  updated_at: string;
}

// ============================================================================
// SLACK INTERFACES
// ============================================================================

/**
 * Slack Workspace Configuration
 *
 * What: Organization Slack workspace connection
 * Where: Created after Slack OAuth flow completes
 * Why: Enables Slack notifications, commands, and AI assistant
 */
export interface SlackWorkspace {
  id: string;
  organization_id: string;
  workspace_id: string;
  workspace_name?: string;
  workspace_domain?: string;
  bot_user_id?: string;
  scopes: string[];
  default_announcements_channel?: string;
  default_alerts_channel?: string;
  enable_notifications: boolean;
  enable_commands: boolean;
  enable_ai_assistant: boolean;
  is_active: boolean;
  installed_at?: string;
  last_activity_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ConnectSlackRequest {
  workspace_id: string;
  bot_token: string;
  workspace_name?: string;
  workspace_domain?: string;
  scopes?: string[];
}

export interface UpdateSlackSettingsRequest {
  enable_notifications?: boolean;
  enable_commands?: boolean;
  enable_ai_assistant?: boolean;
  default_announcements_channel?: string;
  default_alerts_channel?: string;
}

/**
 * Slack Channel Mapping
 *
 * What: Maps Slack channel to course/project entity
 * Where: Created when linking channel to entity
 * Why: Enables targeted notifications to specific channels
 */
export interface SlackChannelMapping {
  id: string;
  workspace_id: string;
  channel_id: string;
  channel_name?: string;
  channel_type: 'channel' | 'private' | 'dm';
  entity_type: string;
  entity_id: string;
  notify_announcements: boolean;
  notify_deadlines: boolean;
  notify_grades: boolean;
  notify_new_content: boolean;
  notify_discussions: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// WEBHOOK INTERFACES
// ============================================================================

/**
 * Outbound Webhook Configuration
 *
 * What: Webhook endpoint for sending events to external services
 * Where: Created when setting up webhook integration
 * Why: Enables event notifications to external systems (Zapier, custom apps)
 */
export interface OutboundWebhook {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  target_url: string;
  auth_type: 'none' | 'bearer' | 'basic' | 'hmac' | 'api_key';
  event_types: string[];
  retry_count: number;
  retry_delay_seconds: number;
  timeout_seconds: number;
  is_active: boolean;
  last_triggered_at?: string;
  success_count: number;
  failure_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateOutboundWebhookRequest {
  name: string;
  description?: string;
  target_url: string;
  auth_type: 'none' | 'bearer' | 'basic' | 'hmac' | 'api_key';
  auth_secret?: string;
  event_types?: string[];
  retry_count?: number;
  retry_delay_seconds?: number;
  timeout_seconds?: number;
}

/**
 * Webhook Delivery Log
 *
 * What: Records webhook delivery attempts
 * Where: Created for each webhook delivery
 * Why: Enables debugging and monitoring webhook reliability
 */
export interface WebhookDeliveryLog {
  id: string;
  webhook_id: string;
  event_type: string;
  event_id: string;
  attempt_number: number;
  request_timestamp: string;
  response_timestamp?: string;
  response_status_code?: number;
  delivery_status: 'pending' | 'success' | 'failed' | 'retry_scheduled';
  error_message?: string;
}

/**
 * Inbound Webhook Configuration
 *
 * What: Webhook endpoint for receiving events from external services
 * Where: Created when setting up webhook receiver
 * Why: Enables integration with GitHub, Stripe, Zapier, etc.
 */
export interface InboundWebhook {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  webhook_token: string;
  handler_type: 'github' | 'stripe' | 'zapier' | 'custom' | 'lms_webhook';
  auth_type: 'none' | 'bearer' | 'basic' | 'hmac' | 'api_key';
  allowed_ips: string[];
  is_active: boolean;
  last_received_at?: string;
  total_received: number;
  total_processed: number;
  total_failed: number;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// OAUTH INTERFACES
// ============================================================================

/**
 * OAuth Token
 *
 * What: OAuth token storage for external service access
 * Where: Created after OAuth authorization flow
 * Why: Manages tokens for Google, Microsoft, Slack, GitHub, Zoom APIs
 */
export interface OAuthToken {
  id: string;
  provider: 'google' | 'microsoft' | 'slack' | 'github' | 'zoom';
  user_id?: string;
  organization_id?: string;
  provider_user_id?: string;
  token_type: string;
  expires_at?: string;
  refresh_expires_at?: string;
  scopes: string[];
  is_valid: boolean;
  last_used_at?: string;
  last_refreshed_at?: string;
  consecutive_failures: number;
  last_error?: string;
  created_at: string;
  updated_at: string;
}

export interface StoreOAuthTokenRequest {
  provider: 'google' | 'microsoft' | 'slack' | 'github' | 'zoom';
  access_token: string;
  user_id?: string;
  organization_id?: string;
  refresh_token?: string;
  expires_at?: string;
  scopes?: string[];
}

// ============================================================================
// SERVICE CLASS
// ============================================================================

/**
 * Integrations Service Class
 *
 * WHY THIS APPROACH:
 * - Centralized integration API logic for all external services
 * - Type-safe interfaces for compile-time validation
 * - Comprehensive error handling for external service failures
 * - Supports OAuth flows and token refresh
 * - Multi-tenant architecture with organization-level isolation
 */
class IntegrationsService {
  private baseUrl = '/integrations';

  // ========================================================================
  // LTI PLATFORM METHODS
  // ========================================================================

  /**
   * Register new LTI 1.3 platform
   *
   * What: Creates LTI platform registration for external LMS
   * Where: Called when organization admin sets up LTI integration
   * Why: Enables external LMS to launch into platform as LTI tool
   */
  async registerLTIPlatform(
    organizationId: string,
    data: CreateLTIPlatformRequest
  ): Promise<LTIPlatform> {
    return await apiClient.post<LTIPlatform>(
      `${this.baseUrl}/lti/platforms`,
      { ...data, organization_id: organizationId }
    );
  }

  /**
   * Get all LTI platforms for organization
   */
  async getOrganizationLTIPlatforms(organizationId: string): Promise<LTIPlatform[]> {
    return await apiClient.get<LTIPlatform[]>(
      `${this.baseUrl}/lti/platforms`,
      { params: { organization_id: organizationId } }
    );
  }

  /**
   * Get LTI platform by ID
   */
  async getLTIPlatformById(platformId: string): Promise<LTIPlatform> {
    return await apiClient.get<LTIPlatform>(
      `${this.baseUrl}/lti/platforms/${platformId}`
    );
  }

  /**
   * Verify LTI platform after successful handshake
   */
  async verifyLTIPlatform(platformId: string): Promise<LTIPlatform> {
    return await apiClient.post<LTIPlatform>(
      `${this.baseUrl}/lti/platforms/${platformId}/verify`
    );
  }

  /**
   * Deactivate LTI platform
   */
  async deactivateLTIPlatform(platformId: string): Promise<LTIPlatform> {
    return await apiClient.post<LTIPlatform>(
      `${this.baseUrl}/lti/platforms/${platformId}/deactivate`
    );
  }

  /**
   * Get LTI contexts for platform
   */
  async getLTIContexts(platformId: string): Promise<LTIContext[]> {
    return await apiClient.get<LTIContext[]>(
      `${this.baseUrl}/lti/platforms/${platformId}/contexts`
    );
  }

  /**
   * Link LTI context to course
   */
  async linkLTIContextToCourse(
    contextId: string,
    courseId: string
  ): Promise<LTIContext> {
    return await apiClient.post<LTIContext>(
      `${this.baseUrl}/lti/contexts/${contextId}/link`,
      { course_id: courseId }
    );
  }

  /**
   * Get pending grade syncs for monitoring
   */
  async getPendingGradeSyncs(limit: number = 100): Promise<LTIGradeSync[]> {
    return await apiClient.get<LTIGradeSync[]>(
      `${this.baseUrl}/lti/grade-syncs/pending`,
      { params: { limit } }
    );
  }

  // ========================================================================
  // CALENDAR METHODS
  // ========================================================================

  /**
   * Connect calendar provider
   *
   * What: Connects user calendar for synchronization
   * Where: Called after OAuth authorization completes
   * Why: Enables automatic calendar sync for deadlines and events
   */
  async connectCalendar(data: ConnectCalendarRequest): Promise<CalendarProvider> {
    return await apiClient.post<CalendarProvider>(
      `${this.baseUrl}/calendars/connect`,
      data
    );
  }

  /**
   * Get user's connected calendars
   */
  async getUserCalendars(userId: string): Promise<CalendarProvider[]> {
    return await apiClient.get<CalendarProvider[]>(
      `${this.baseUrl}/calendars`,
      { params: { user_id: userId } }
    );
  }

  /**
   * Update calendar settings
   */
  async updateCalendarSettings(
    providerId: string,
    data: UpdateCalendarSettingsRequest
  ): Promise<CalendarProvider> {
    return await apiClient.put<CalendarProvider>(
      `${this.baseUrl}/calendars/${providerId}`,
      data
    );
  }

  /**
   * Disconnect calendar
   */
  async disconnectCalendar(providerId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/calendars/${providerId}`);
  }

  /**
   * Get calendar events for user
   */
  async getCalendarEvents(
    userId: string,
    startDate?: string,
    endDate?: string
  ): Promise<CalendarEvent[]> {
    return await apiClient.get<CalendarEvent[]>(
      `${this.baseUrl}/calendars/events`,
      { params: { user_id: userId, start_date: startDate, end_date: endDate } }
    );
  }

  /**
   * Trigger manual calendar sync
   */
  async triggerCalendarSync(providerId: string): Promise<{ synced_count: number }> {
    return await apiClient.post<{ synced_count: number }>(
      `${this.baseUrl}/calendars/${providerId}/sync`
    );
  }

  // ========================================================================
  // SLACK METHODS
  // ========================================================================

  /**
   * Connect Slack workspace
   *
   * What: Connects organization Slack workspace
   * Where: Called after Slack OAuth flow completes
   * Why: Enables Slack notifications, commands, and AI assistant
   */
  async connectSlackWorkspace(
    organizationId: string,
    data: ConnectSlackRequest
  ): Promise<SlackWorkspace> {
    return await apiClient.post<SlackWorkspace>(
      `${this.baseUrl}/slack/workspaces`,
      { ...data, organization_id: organizationId }
    );
  }

  /**
   * Get organization Slack workspace
   */
  async getOrganizationSlackWorkspace(
    organizationId: string
  ): Promise<SlackWorkspace | null> {
    return await apiClient.get<SlackWorkspace | null>(
      `${this.baseUrl}/slack/workspaces`,
      { params: { organization_id: organizationId } }
    );
  }

  /**
   * Update Slack workspace settings
   */
  async updateSlackSettings(
    workspaceId: string,
    data: UpdateSlackSettingsRequest
  ): Promise<SlackWorkspace> {
    return await apiClient.put<SlackWorkspace>(
      `${this.baseUrl}/slack/workspaces/${workspaceId}`,
      data
    );
  }

  /**
   * Disconnect Slack workspace
   */
  async disconnectSlackWorkspace(workspaceId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/slack/workspaces/${workspaceId}`);
  }

  /**
   * Get Slack channel mappings for entity
   */
  async getEntitySlackChannels(
    entityType: string,
    entityId: string
  ): Promise<SlackChannelMapping[]> {
    return await apiClient.get<SlackChannelMapping[]>(
      `${this.baseUrl}/slack/channels`,
      { params: { entity_type: entityType, entity_id: entityId } }
    );
  }

  /**
   * Map Slack channel to entity
   */
  async mapSlackChannel(
    workspaceId: string,
    channelId: string,
    entityType: string,
    entityId: string,
    channelName?: string
  ): Promise<SlackChannelMapping> {
    return await apiClient.post<SlackChannelMapping>(
      `${this.baseUrl}/slack/channels`,
      {
        workspace_id: workspaceId,
        channel_id: channelId,
        channel_name: channelName,
        entity_type: entityType,
        entity_id: entityId,
      }
    );
  }

  /**
   * Test Slack connection
   */
  async testSlackConnection(workspaceId: string): Promise<{ success: boolean; message: string }> {
    return await apiClient.post<{ success: boolean; message: string }>(
      `${this.baseUrl}/slack/workspaces/${workspaceId}/test`
    );
  }

  // ========================================================================
  // WEBHOOK METHODS
  // ========================================================================

  /**
   * Create outbound webhook
   *
   * What: Creates webhook for sending events to external services
   * Where: Called when setting up webhook integration
   * Why: Enables event notifications to Zapier, custom apps, etc.
   */
  async createOutboundWebhook(
    organizationId: string,
    data: CreateOutboundWebhookRequest
  ): Promise<OutboundWebhook> {
    return await apiClient.post<OutboundWebhook>(
      `${this.baseUrl}/webhooks/outbound`,
      { ...data, organization_id: organizationId }
    );
  }

  /**
   * Get organization outbound webhooks
   */
  async getOrganizationWebhooks(organizationId: string): Promise<OutboundWebhook[]> {
    return await apiClient.get<OutboundWebhook[]>(
      `${this.baseUrl}/webhooks/outbound`,
      { params: { organization_id: organizationId } }
    );
  }

  /**
   * Update outbound webhook
   */
  async updateOutboundWebhook(
    webhookId: string,
    data: Partial<CreateOutboundWebhookRequest>
  ): Promise<OutboundWebhook> {
    return await apiClient.put<OutboundWebhook>(
      `${this.baseUrl}/webhooks/outbound/${webhookId}`,
      data
    );
  }

  /**
   * Delete outbound webhook
   */
  async deleteOutboundWebhook(webhookId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/webhooks/outbound/${webhookId}`);
  }

  /**
   * Test outbound webhook
   */
  async testOutboundWebhook(
    webhookId: string
  ): Promise<{ success: boolean; status_code?: number; message: string }> {
    return await apiClient.post<{ success: boolean; status_code?: number; message: string }>(
      `${this.baseUrl}/webhooks/outbound/${webhookId}/test`
    );
  }

  /**
   * Get webhook delivery logs
   */
  async getWebhookDeliveryLogs(
    webhookId: string,
    limit: number = 50
  ): Promise<WebhookDeliveryLog[]> {
    return await apiClient.get<WebhookDeliveryLog[]>(
      `${this.baseUrl}/webhooks/outbound/${webhookId}/logs`,
      { params: { limit } }
    );
  }

  /**
   * Get inbound webhooks for organization
   */
  async getInboundWebhooks(organizationId: string): Promise<InboundWebhook[]> {
    return await apiClient.get<InboundWebhook[]>(
      `${this.baseUrl}/webhooks/inbound`,
      { params: { organization_id: organizationId } }
    );
  }

  /**
   * Create inbound webhook
   */
  async createInboundWebhook(
    organizationId: string,
    name: string,
    handlerType: 'github' | 'stripe' | 'zapier' | 'custom' | 'lms_webhook',
    description?: string
  ): Promise<InboundWebhook> {
    return await apiClient.post<InboundWebhook>(
      `${this.baseUrl}/webhooks/inbound`,
      {
        organization_id: organizationId,
        name,
        handler_type: handlerType,
        description,
      }
    );
  }

  /**
   * Delete inbound webhook
   */
  async deleteInboundWebhook(webhookId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/webhooks/inbound/${webhookId}`);
  }

  // ========================================================================
  // OAUTH TOKEN METHODS
  // ========================================================================

  /**
   * Store OAuth token
   *
   * What: Stores OAuth token for external service access
   * Where: Called after OAuth authorization
   * Why: Enables API access to Google, Microsoft, Slack, GitHub, Zoom
   */
  async storeOAuthToken(data: StoreOAuthTokenRequest): Promise<OAuthToken> {
    return await apiClient.post<OAuthToken>(
      `${this.baseUrl}/oauth/tokens`,
      data
    );
  }

  /**
   * Get OAuth token for provider
   */
  async getOAuthToken(
    provider: 'google' | 'microsoft' | 'slack' | 'github' | 'zoom',
    userId?: string,
    organizationId?: string
  ): Promise<OAuthToken | null> {
    return await apiClient.get<OAuthToken | null>(
      `${this.baseUrl}/oauth/tokens/${provider}`,
      { params: { user_id: userId, organization_id: organizationId } }
    );
  }

  /**
   * Refresh OAuth token
   */
  async refreshOAuthToken(tokenId: string): Promise<OAuthToken> {
    return await apiClient.post<OAuthToken>(
      `${this.baseUrl}/oauth/tokens/${tokenId}/refresh`
    );
  }

  /**
   * Revoke OAuth token
   */
  async revokeOAuthToken(tokenId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/oauth/tokens/${tokenId}`);
  }

  /**
   * Get user's OAuth connections
   */
  async getUserOAuthConnections(userId: string): Promise<OAuthToken[]> {
    return await apiClient.get<OAuthToken[]>(
      `${this.baseUrl}/oauth/tokens`,
      { params: { user_id: userId } }
    );
  }

  /**
   * Get organization's OAuth connections
   */
  async getOrganizationOAuthConnections(organizationId: string): Promise<OAuthToken[]> {
    return await apiClient.get<OAuthToken[]>(
      `${this.baseUrl}/oauth/tokens`,
      { params: { organization_id: organizationId } }
    );
  }

  // ========================================================================
  // OAUTH FLOW HELPERS
  // ========================================================================

  /**
   * Initiate OAuth flow
   *
   * What: Redirects to OAuth provider authorization page
   * Where: Called when user clicks "Connect" button
   * Why: Starts OAuth authorization flow for external service
   */
  initiateOAuthFlow(
    provider: 'google' | 'microsoft' | 'slack' | 'github' | 'zoom',
    scopes: string[],
    redirectUri: string
  ): void {
    const params = new URLSearchParams({
      provider,
      scopes: scopes.join(','),
      redirect_uri: redirectUri,
    });
    window.location.href = `${this.baseUrl}/oauth/authorize?${params.toString()}`;
  }

  /**
   * Handle OAuth callback
   *
   * What: Processes OAuth callback with authorization code
   * Where: Called on OAuth redirect URL
   * Why: Exchanges authorization code for access token
   */
  async handleOAuthCallback(
    provider: string,
    code: string,
    state: string
  ): Promise<{ success: boolean; token?: OAuthToken; error?: string }> {
    return await apiClient.post<{ success: boolean; token?: OAuthToken; error?: string }>(
      `${this.baseUrl}/oauth/callback`,
      { provider, code, state }
    );
  }
}

// Export singleton instance
export const integrationsService = new IntegrationsService();
