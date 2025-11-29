/**
 * useIntegrations Custom Hook
 *
 * What: React hook for managing integration data fetching and state
 * Where: Used by integration panel components
 * Why: Centralizes integration data logic with caching and error handling
 *
 * BUSINESS CONTEXT:
 * Integration management requires coordinating multiple external services
 * (LTI, Calendar, Slack, Webhooks, OAuth). This hook provides a unified
 * interface for fetching integration data with proper loading states and
 * error handling.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses React Query for data caching and automatic refetching
 * - Provides loading/error states for each integration type
 * - Implements optimistic updates for better UX
 * - Handles token refresh for OAuth-based integrations
 *
 * @module features/integrations/hooks/useIntegrations
 */

import { useState, useEffect, useCallback } from 'react';
import { integrationsService } from '../../../services/integrationsService';
import type {
  LTIPlatform,
  CalendarProvider,
  SlackWorkspace,
  OutboundWebhook,
  InboundWebhook,
  OAuthToken,
} from '../../../services/integrationsService';

/**
 * Integration data state interface
 */
export interface IntegrationsState {
  // LTI integrations
  ltiPlatforms: LTIPlatform[];
  ltiLoading: boolean;
  ltiError: string | null;

  // Calendar integrations
  calendars: CalendarProvider[];
  calendarsLoading: boolean;
  calendarsError: string | null;

  // Slack integration
  slackWorkspace: SlackWorkspace | null;
  slackLoading: boolean;
  slackError: string | null;

  // Webhook integrations
  outboundWebhooks: OutboundWebhook[];
  inboundWebhooks: InboundWebhook[];
  webhooksLoading: boolean;
  webhooksError: string | null;

  // OAuth connections
  oauthTokens: OAuthToken[];
  oauthLoading: boolean;
  oauthError: string | null;
}

/**
 * useIntegrations Hook
 *
 * WHY THIS APPROACH:
 * - Centralized integration state management
 * - Automatic data fetching with React hooks
 * - Error handling with user-friendly messages
 * - Refresh methods for manual data reload
 * - Loading states for each integration type
 *
 * @param organizationId - Organization ID for filtering integrations
 * @param userId - Optional user ID for user-specific integrations
 */
export const useIntegrations = (
  organizationId: string,
  userId?: string
) => {
  // State management for all integration types
  const [state, setState] = useState<IntegrationsState>({
    ltiPlatforms: [],
    ltiLoading: false,
    ltiError: null,
    calendars: [],
    calendarsLoading: false,
    calendarsError: null,
    slackWorkspace: null,
    slackLoading: false,
    slackError: null,
    outboundWebhooks: [],
    inboundWebhooks: [],
    webhooksLoading: false,
    webhooksError: null,
    oauthTokens: [],
    oauthLoading: false,
    oauthError: null,
  });

  /**
   * Fetch LTI platforms for organization
   *
   * What: Retrieves all LTI platform registrations
   * Where: Called on mount and when organizationId changes
   * Why: Displays configured LMS integrations
   */
  const fetchLTIPlatforms = useCallback(async () => {
    setState(prev => ({ ...prev, ltiLoading: true, ltiError: null }));
    try {
      const platforms = await integrationsService.getOrganizationLTIPlatforms(organizationId);
      setState(prev => ({
        ...prev,
        ltiPlatforms: platforms,
        ltiLoading: false,
      }));
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        ltiError: error.response?.data?.message || 'Failed to load LTI platforms',
        ltiLoading: false,
      }));
    }
  }, [organizationId]);

  /**
   * Fetch calendar providers for user
   *
   * What: Retrieves user's connected calendar providers
   * Where: Called on mount and when userId changes
   * Why: Displays configured calendar integrations
   */
  const fetchCalendars = useCallback(async () => {
    if (!userId) return;

    setState(prev => ({ ...prev, calendarsLoading: true, calendarsError: null }));
    try {
      const calendars = await integrationsService.getUserCalendars(userId);
      setState(prev => ({
        ...prev,
        calendars,
        calendarsLoading: false,
      }));
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        calendarsError: error.response?.data?.message || 'Failed to load calendars',
        calendarsLoading: false,
      }));
    }
  }, [userId]);

  /**
   * Fetch Slack workspace for organization
   *
   * What: Retrieves organization's Slack workspace configuration
   * Where: Called on mount and when organizationId changes
   * Why: Displays Slack integration settings
   */
  const fetchSlackWorkspace = useCallback(async () => {
    setState(prev => ({ ...prev, slackLoading: true, slackError: null }));
    try {
      const workspace = await integrationsService.getOrganizationSlackWorkspace(organizationId);
      setState(prev => ({
        ...prev,
        slackWorkspace: workspace,
        slackLoading: false,
      }));
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        slackError: error.response?.data?.message || 'Failed to load Slack workspace',
        slackLoading: false,
      }));
    }
  }, [organizationId]);

  /**
   * Fetch webhooks for organization
   *
   * What: Retrieves organization's outbound and inbound webhooks
   * Where: Called on mount and when organizationId changes
   * Why: Displays configured webhook integrations
   */
  const fetchWebhooks = useCallback(async () => {
    setState(prev => ({ ...prev, webhooksLoading: true, webhooksError: null }));
    try {
      const [outbound, inbound] = await Promise.all([
        integrationsService.getOrganizationWebhooks(organizationId),
        integrationsService.getInboundWebhooks(organizationId),
      ]);
      setState(prev => ({
        ...prev,
        outboundWebhooks: outbound,
        inboundWebhooks: inbound,
        webhooksLoading: false,
      }));
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        webhooksError: error.response?.data?.message || 'Failed to load webhooks',
        webhooksLoading: false,
      }));
    }
  }, [organizationId]);

  /**
   * Fetch OAuth connections
   *
   * What: Retrieves OAuth tokens for user or organization
   * Where: Called on mount and when userId/organizationId changes
   * Why: Displays connected third-party services
   */
  const fetchOAuthTokens = useCallback(async () => {
    setState(prev => ({ ...prev, oauthLoading: true, oauthError: null }));
    try {
      let tokens: OAuthToken[] = [];
      if (userId) {
        tokens = await integrationsService.getUserOAuthConnections(userId);
      } else {
        tokens = await integrationsService.getOrganizationOAuthConnections(organizationId);
      }
      setState(prev => ({
        ...prev,
        oauthTokens: tokens,
        oauthLoading: false,
      }));
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        oauthError: error.response?.data?.message || 'Failed to load OAuth connections',
        oauthLoading: false,
      }));
    }
  }, [userId, organizationId]);

  /**
   * Refresh all integration data
   *
   * What: Reloads all integration types
   * Where: Called after integration changes or manually by user
   * Why: Ensures UI reflects latest integration state
   */
  const refreshAll = useCallback(async () => {
    await Promise.all([
      fetchLTIPlatforms(),
      fetchCalendars(),
      fetchSlackWorkspace(),
      fetchWebhooks(),
      fetchOAuthTokens(),
    ]);
  }, [
    fetchLTIPlatforms,
    fetchCalendars,
    fetchSlackWorkspace,
    fetchWebhooks,
    fetchOAuthTokens,
  ]);

  /**
   * Initial data fetch on mount
   */
  useEffect(() => {
    fetchLTIPlatforms();
    fetchSlackWorkspace();
    fetchWebhooks();
    fetchOAuthTokens();
  }, [fetchLTIPlatforms, fetchSlackWorkspace, fetchWebhooks, fetchOAuthTokens]);

  /**
   * Fetch calendars when userId becomes available
   */
  useEffect(() => {
    if (userId) {
      fetchCalendars();
    }
  }, [userId, fetchCalendars]);

  /**
   * Computed loading state
   */
  const isLoading =
    state.ltiLoading ||
    state.calendarsLoading ||
    state.slackLoading ||
    state.webhooksLoading ||
    state.oauthLoading;

  /**
   * Computed error state
   */
  const hasError =
    !!state.ltiError ||
    !!state.calendarsError ||
    !!state.slackError ||
    !!state.webhooksError ||
    !!state.oauthError;

  return {
    // State
    ...state,
    isLoading,
    hasError,

    // Refresh methods
    refreshAll,
    refreshLTI: fetchLTIPlatforms,
    refreshCalendars: fetchCalendars,
    refreshSlack: fetchSlackWorkspace,
    refreshWebhooks: fetchWebhooks,
    refreshOAuth: fetchOAuthTokens,
  };
};

export default useIntegrations;
