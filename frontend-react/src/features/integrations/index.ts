/**
 * Integrations Module Exports
 *
 * What: Central export file for integrations feature module
 * Where: Used to import integrations components and hooks throughout the app
 * Why: Provides clean API for integrations feature consumption
 *
 * @module features/integrations
 */

// Main page component
export { default as IntegrationsSettings } from './IntegrationsSettings';
export type { IntegrationsSettingsProps } from './IntegrationsSettings';

// Panel components
export { default as LTIIntegrationPanel } from './components/LTIIntegrationPanel';
export type { LTIIntegrationPanelProps } from './components/LTIIntegrationPanel';

export { default as CalendarSyncPanel } from './components/CalendarSyncPanel';
export type { CalendarSyncPanelProps } from './components/CalendarSyncPanel';

export { default as SlackIntegrationPanel } from './components/SlackIntegrationPanel';
export type { SlackIntegrationPanelProps } from './components/SlackIntegrationPanel';

export { default as WebhookManager } from './components/WebhookManager';
export type { WebhookManagerProps } from './components/WebhookManager';

export { default as OAuthConnectionsPanel } from './components/OAuthConnectionsPanel';
export type { OAuthConnectionsPanelProps } from './components/OAuthConnectionsPanel';

// Utility components
export { default as IntegrationStatusBadge } from './components/IntegrationStatusBadge';
export type { IntegrationStatusBadgeProps } from './components/IntegrationStatusBadge';

// Custom hooks
export { useIntegrations } from './hooks/useIntegrations';
export type { IntegrationsState } from './hooks/useIntegrations';
