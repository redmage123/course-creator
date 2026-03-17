/**
 * Integrations Settings Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the Integrations Settings page provides comprehensive
 * integration management for LTI, Calendar, Slack, OAuth, and Webhooks.
 *
 * TEST COVERAGE:
 * - Component rendering with all integration panels
 * - Loading and error states
 * - Integration status display
 * - Panel interactions
 * - Accessibility features
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '../../test/utils';
import { IntegrationsSettings } from './IntegrationsSettings';

// Mock the custom hook
vi.mock('./hooks/useIntegrations');
import * as useIntegrationsModule from './hooks/useIntegrations';

// Mock child components
vi.mock('./components/LTIIntegrationPanel', () => ({
  default: ({ platforms }: any) => (
    <div data-testid="lti-integration-panel">LTI Integration Panel ({platforms?.length || 0} platforms)</div>
  ),
}));

vi.mock('./components/CalendarSyncPanel', () => ({
  default: ({ calendars }: any) => (
    <div data-testid="calendar-sync-panel">Calendar Sync Panel ({calendars?.length || 0} calendars)</div>
  ),
}));

vi.mock('./components/SlackIntegrationPanel', () => ({
  default: ({ workspace }: any) => (
    <div data-testid="slack-integration-panel">Slack Integration Panel ({workspace ? 'connected' : 'disconnected'})</div>
  ),
}));

vi.mock('./components/OAuthConnectionsPanel', () => ({
  default: ({ tokens }: any) => (
    <div data-testid="oauth-connections-panel">OAuth Connections Panel ({tokens?.length || 0} tokens)</div>
  ),
}));

vi.mock('./components/WebhookManager', () => ({
  default: ({ outboundWebhooks, inboundWebhooks }: any) => (
    <div data-testid="webhook-manager">Webhook Manager ({(outboundWebhooks?.length || 0) + (inboundWebhooks?.length || 0)} webhooks)</div>
  ),
}));

// Mock hook return data
const mockHookReturn = {
  ltiPlatforms: [{ id: 'lti-1', name: 'Canvas' }],
  ltiLoading: false,
  ltiError: null,
  calendars: [{ id: 'cal-1', provider: 'google' }],
  calendarsLoading: false,
  calendarsError: null,
  slackWorkspace: { id: 'slack-1', name: 'Test Workspace' },
  slackLoading: false,
  slackError: null,
  outboundWebhooks: [{ id: 'wh-1', url: 'https://example.com' }],
  inboundWebhooks: [{ id: 'wh-2', url: 'https://example.com/in' }],
  webhooksLoading: false,
  webhooksError: null,
  oauthTokens: [{ id: 'oauth-1', provider: 'google' }],
  oauthLoading: false,
  oauthError: null,
  isLoading: false,
  hasError: false,
  refreshAll: vi.fn(),
  refreshLTI: vi.fn(),
  refreshCalendars: vi.fn(),
  refreshSlack: vi.fn(),
  refreshWebhooks: vi.fn(),
  refreshOAuth: vi.fn(),
};

describe('IntegrationsSettings Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering - Default State', () => {
    /**
     * Test: Renders integrations page with correct title
     * WHY: Ensures page header is displayed correctly
     */
    it('renders integrations page with correct title', () => {
      vi.spyOn(useIntegrationsModule, 'useIntegrations').mockReturnValue(mockHookReturn);

      renderWithProviders(<IntegrationsSettings organizationId="org-1" userId="user-1" />);

      expect(screen.getByText('Integrations')).toBeInTheDocument();
    });

    /**
     * Test: Renders LTI panel (default tab)
     * WHY: Ensures default integration type is accessible
     */
    it('renders LTI panel by default', () => {
      vi.spyOn(useIntegrationsModule, 'useIntegrations').mockReturnValue(mockHookReturn);

      renderWithProviders(<IntegrationsSettings organizationId="org-1" userId="user-1" />);

      expect(screen.getByTestId('lti-integration-panel')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    /**
     * Test: Displays refresh button disabled while loading
     * WHY: Ensures users see loading feedback
     */
    it('displays refresh button disabled while loading', () => {
      vi.spyOn(useIntegrationsModule, 'useIntegrations').mockReturnValue({
        ...mockHookReturn,
        isLoading: true,
      });

      renderWithProviders(<IntegrationsSettings organizationId="org-1" />);

      const refreshButton = screen.getByTitle('Refresh all integrations');
      expect(refreshButton).toBeDisabled();
      expect(refreshButton).toHaveTextContent('Refreshing...');
    });
  });

  describe('Error State', () => {
    /**
     * Test: Displays error banner when integrations fail to load
     * WHY: Ensures users are informed of errors
     */
    it('displays error banner when integrations fail to load', () => {
      vi.spyOn(useIntegrationsModule, 'useIntegrations').mockReturnValue({
        ...mockHookReturn,
        hasError: true,
        ltiError: 'Failed to load LTI platforms',
      });

      renderWithProviders(<IntegrationsSettings organizationId="org-1" />);

      expect(screen.getByText(/Some integrations failed to load/i)).toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    /**
     * Test: All tabs are rendered with labels
     * WHY: Ensures all integration types are accessible
     */
    it('renders all integration tabs', () => {
      vi.spyOn(useIntegrationsModule, 'useIntegrations').mockReturnValue(mockHookReturn);

      renderWithProviders(<IntegrationsSettings organizationId="org-1" userId="user-1" />);

      expect(screen.getByText('LTI Platforms')).toBeInTheDocument();
      expect(screen.getByText('Calendar Sync')).toBeInTheDocument();
      expect(screen.getByText('Slack')).toBeInTheDocument();
      expect(screen.getByText('Webhooks')).toBeInTheDocument();
      expect(screen.getByText('OAuth Connections')).toBeInTheDocument();
    });

    /**
     * Test: Tab badges show count
     * WHY: Helps users see integration counts at a glance
     */
    it('shows integration counts in tab badges', () => {
      vi.spyOn(useIntegrationsModule, 'useIntegrations').mockReturnValue(mockHookReturn);

      renderWithProviders(<IntegrationsSettings organizationId="org-1" userId="user-1" />);

      // LTI: 1 platform, Calendar: 1, Slack: 1, Webhooks: 2 (1+1), OAuth: 1
      // Multiple tabs have badge count of 1, so use getAllByText
      const badges = screen.getAllByText('1');
      expect(badges.length).toBeGreaterThanOrEqual(4); // At least 4 badges with count 1
    });
  });

  describe('Refresh Functionality', () => {
    /**
     * Test: Refresh button calls refreshAll
     * WHY: Ensures users can manually refresh data
     */
    it('refresh button calls refreshAll', async () => {
      const mockRefreshAll = vi.fn();
      vi.spyOn(useIntegrationsModule, 'useIntegrations').mockReturnValue({
        ...mockHookReturn,
        refreshAll: mockRefreshAll,
      });

      renderWithProviders(<IntegrationsSettings organizationId="org-1" />);

      const refreshButton = screen.getByTitle('Refresh all integrations');
      refreshButton.click();

      expect(mockRefreshAll).toHaveBeenCalledTimes(1);
    });
  });

  describe('Accessibility', () => {
    /**
     * Test: Page has proper heading structure
     * WHY: Ensures screen readers can navigate sections
     */
    it('has proper heading structure', () => {
      vi.spyOn(useIntegrationsModule, 'useIntegrations').mockReturnValue(mockHookReturn);

      renderWithProviders(<IntegrationsSettings organizationId="org-1" />);

      const h1 = screen.getByRole('heading', { level: 1 });
      expect(h1).toHaveTextContent('Integrations');
    });

    /**
     * Test: Tabs are keyboard accessible
     * WHY: Ensures keyboard navigation works
     */
    it('tabs are keyboard accessible buttons', () => {
      vi.spyOn(useIntegrationsModule, 'useIntegrations').mockReturnValue(mockHookReturn);

      renderWithProviders(<IntegrationsSettings organizationId="org-1" />);

      const tabButtons = screen.getAllByRole('button');
      // Should have tab buttons plus refresh button
      expect(tabButtons.length).toBeGreaterThanOrEqual(5);
    });
  });
});
