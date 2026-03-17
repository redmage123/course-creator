/**
 * IntegrationsSettings Page
 *
 * What: Main integrations management page with tabbed interface
 * Where: Accessible from organization/user settings
 * Why: Central hub for managing all external integrations
 *
 * BUSINESS CONTEXT:
 * Integration management is critical for platform value delivery.
 * This page provides a unified interface for:
 * - LTI 1.3 platform connections (LMS integration)
 * - Calendar synchronization (Google, Outlook)
 * - Slack workspace integration
 * - Webhook management (inbound/outbound)
 * - OAuth token management
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses useIntegrations hook for data fetching
 * - Tabbed interface for organized integration management
 * - Real-time status indicators for all integrations
 * - Comprehensive error handling and user feedback
 *
 * @module features/integrations/IntegrationsSettings
 */

import React, { useState } from 'react';
import { useIntegrations } from './hooks/useIntegrations';
import LTIIntegrationPanel from './components/LTIIntegrationPanel';
import CalendarSyncPanel from './components/CalendarSyncPanel';
import SlackIntegrationPanel from './components/SlackIntegrationPanel';
import WebhookManager from './components/WebhookManager';
import OAuthConnectionsPanel from './components/OAuthConnectionsPanel';
import styles from './IntegrationsSettings.module.css';

export interface IntegrationsSettingsProps {
  /** Organization ID for organization-level integrations */
  organizationId: string;
  /** Optional user ID for user-level integrations (calendar, OAuth) */
  userId?: string;
}

/**
 * Integration tab types
 */
type IntegrationTab = 'lti' | 'calendar' | 'slack' | 'webhooks' | 'oauth';

/**
 * IntegrationsSettings Component
 *
 * WHY THIS APPROACH:
 * - Tabbed interface reduces cognitive load
 * - Each integration type has dedicated panel
 * - Unified data fetching via custom hook
 * - Loading states prevent stale data display
 * - Error boundaries for robust error handling
 */
export const IntegrationsSettings: React.FC<IntegrationsSettingsProps> = ({
  organizationId,
  userId,
}) => {
  const [activeTab, setActiveTab] = useState<IntegrationTab>('lti');

  // Fetch all integration data
  const {
    ltiPlatforms,
    ltiLoading,
    ltiError,
    calendars,
    calendarsLoading,
    calendarsError,
    slackWorkspace,
    slackLoading,
    slackError,
    outboundWebhooks,
    inboundWebhooks,
    webhooksLoading,
    webhooksError,
    oauthTokens,
    oauthLoading,
    oauthError,
    isLoading,
    hasError,
    refreshAll,
    refreshLTI,
    refreshCalendars,
    refreshSlack,
    refreshWebhooks,
    refreshOAuth,
  } = useIntegrations(organizationId, userId);

  /**
   * Tab configuration with metadata
   */
  const tabs: Array<{
    id: IntegrationTab;
    label: string;
    icon: string;
    count?: number;
    error?: string | null;
  }> = [
    {
      id: 'lti',
      label: 'LTI Platforms',
      icon: '🔗',
      count: ltiPlatforms.length,
      error: ltiError,
    },
    {
      id: 'calendar',
      label: 'Calendar Sync',
      icon: '📅',
      count: calendars.length,
      error: calendarsError,
    },
    {
      id: 'slack',
      label: 'Slack',
      icon: '💬',
      count: slackWorkspace ? 1 : 0,
      error: slackError,
    },
    {
      id: 'webhooks',
      label: 'Webhooks',
      icon: '🔗',
      count: outboundWebhooks.length + inboundWebhooks.length,
      error: webhooksError,
    },
    {
      id: 'oauth',
      label: 'OAuth Connections',
      icon: '🔐',
      count: oauthTokens.length,
      error: oauthError,
    },
  ];

  /**
   * Render active tab content
   */
  const renderTabContent = () => {
    switch (activeTab) {
      case 'lti':
        return (
          <LTIIntegrationPanel
            organizationId={organizationId}
            platforms={ltiPlatforms}
            onRefresh={refreshLTI}
          />
        );

      case 'calendar':
        if (!userId) {
          return (
            <div className={styles.errorState}>
              <p>Calendar sync requires user authentication</p>
            </div>
          );
        }
        return (
          <CalendarSyncPanel
            userId={userId}
            calendars={calendars}
            onRefresh={refreshCalendars}
          />
        );

      case 'slack':
        return (
          <SlackIntegrationPanel
            organizationId={organizationId}
            workspace={slackWorkspace}
            onRefresh={refreshSlack}
          />
        );

      case 'webhooks':
        return (
          <WebhookManager
            organizationId={organizationId}
            outboundWebhooks={outboundWebhooks}
            inboundWebhooks={inboundWebhooks}
            onRefresh={refreshWebhooks}
          />
        );

      case 'oauth':
        return (
          <OAuthConnectionsPanel
            userId={userId}
            organizationId={organizationId}
            tokens={oauthTokens}
            onRefresh={refreshOAuth}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className={styles.container}>
      {/* Page header */}
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Integrations</h1>
          <p className={styles.pageDescription}>
            Connect external services and manage integration settings
          </p>
        </div>
        <button
          className={styles.refreshButton}
          onClick={refreshAll}
          disabled={isLoading}
          title="Refresh all integrations"
        >
          {isLoading ? '⟳ Refreshing...' : '⟳ Refresh'}
        </button>
      </div>

      {/* Global error message */}
      {hasError && (
        <div className={styles.errorBanner}>
          <strong>⚠️ Some integrations failed to load.</strong>
          <span>Check individual tabs for details.</span>
        </div>
      )}

      {/* Tabs navigation */}
      <div className={styles.tabs}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`${styles.tab} ${activeTab === tab.id ? styles.activeTab : ''} ${
              tab.error ? styles.errorTab : ''
            }`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className={styles.tabIcon}>{tab.icon}</span>
            <span className={styles.tabLabel}>{tab.label}</span>
            {tab.count !== undefined && tab.count > 0 && (
              <span className={styles.tabBadge}>{tab.count}</span>
            )}
            {tab.error && (
              <span className={styles.tabErrorIndicator} title={tab.error}>
                !
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className={styles.tabContent}>
        {renderTabContent()}
      </div>
    </div>
  );
};

export default IntegrationsSettings;
