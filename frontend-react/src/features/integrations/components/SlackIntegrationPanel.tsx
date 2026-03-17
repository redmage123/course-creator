/**
 * SlackIntegrationPanel Component
 *
 * What: Slack workspace integration and channel mapping management
 * Where: Used in IntegrationsSettings for Slack notifications
 * Why: Enables automated notifications to Slack for course updates
 *
 * BUSINESS CONTEXT:
 * Slack integration keeps teams informed with real-time notifications for:
 * - Course announcements
 * - Assignment deadlines
 * - Grade releases
 * - New content availability
 * - Discussion replies
 *
 * @module features/integrations/components/SlackIntegrationPanel
 */

import React, { useState } from 'react';
import { integrationsService } from '../../../services/integrationsService';
import type { SlackWorkspace, UpdateSlackSettingsRequest } from '../../../services/integrationsService';
import IntegrationStatusBadge from './IntegrationStatusBadge';
import styles from './SlackIntegrationPanel.module.css';

export interface SlackIntegrationPanelProps {
  organizationId: string;
  workspace: SlackWorkspace | null;
  onRefresh: () => void;
}

export const SlackIntegrationPanel: React.FC<SlackIntegrationPanelProps> = ({
  organizationId,
  workspace,
  onRefresh,
}) => {
  const [testing, setTesting] = useState(false);

  const handleConnect = () => {
    const redirectUri = `${window.location.origin}/integrations/slack/callback`;
    const scopes = [
      'chat:write',
      'channels:read',
      'groups:read',
      'users:read',
      'incoming-webhook',
    ];

    integrationsService.initiateOAuthFlow('slack', scopes, redirectUri);
  };

  const handleDisconnect = async () => {
    if (!workspace || !window.confirm('Disconnect Slack workspace?')) return;

    try {
      await integrationsService.disconnectSlackWorkspace(workspace.id);
      onRefresh();
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to disconnect Slack');
    }
  };

  const handleTestConnection = async () => {
    if (!workspace) return;

    setTesting(true);
    try {
      const result = await integrationsService.testSlackConnection(workspace.id);
      alert(result.message);
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to test Slack connection');
    } finally {
      setTesting(false);
    }
  };

  const handleUpdateSettings = async (settings: UpdateSlackSettingsRequest) => {
    if (!workspace) return;

    try {
      await integrationsService.updateSlackSettings(workspace.id, settings);
      onRefresh();
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to update settings');
    }
  };

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>💬 Slack Integration</h2>
          <p className={styles.description}>
            Send automated notifications to Slack channels for course updates
          </p>
        </div>
      </div>

      {!workspace ? (
        <div className={styles.connectSection}>
          <button className={styles.connectButton} onClick={handleConnect}>
            <span className={styles.slackIcon}>💬</span>
            Add to Slack
          </button>
          <p className={styles.connectHint}>
            Connect your Slack workspace to receive course notifications
          </p>
        </div>
      ) : (
        <div className={styles.workspaceCard}>
          <div className={styles.workspaceHeader}>
            <div>
              <h3 className={styles.workspaceName}>
                {workspace.workspace_name || 'Slack Workspace'}
              </h3>
              {workspace.workspace_domain && (
                <p className={styles.workspaceDomain}>{workspace.workspace_domain}.slack.com</p>
              )}
            </div>
            <IntegrationStatusBadge
              status={workspace.is_active ? 'connected' : 'disconnected'}
              lastSync={workspace.last_activity_at}
            />
          </div>

          {/* Notification settings */}
          <div className={styles.settings}>
            <h4 className={styles.settingsTitle}>Notification Settings</h4>
            <label className={styles.settingRow}>
              <input
                type="checkbox"
                checked={workspace.enable_notifications}
                onChange={(e) => handleUpdateSettings({ enable_notifications: e.target.checked })}
              />
              <span>Enable notifications</span>
            </label>
            <label className={styles.settingRow}>
              <input
                type="checkbox"
                checked={workspace.enable_commands}
                onChange={(e) => handleUpdateSettings({ enable_commands: e.target.checked })}
              />
              <span>Enable slash commands</span>
            </label>
            <label className={styles.settingRow}>
              <input
                type="checkbox"
                checked={workspace.enable_ai_assistant}
                onChange={(e) => handleUpdateSettings({ enable_ai_assistant: e.target.checked })}
              />
              <span>Enable AI assistant</span>
            </label>
          </div>

          {/* Default channels */}
          <div className={styles.channels}>
            <h4 className={styles.settingsTitle}>Default Channels</h4>
            <div className={styles.channelRow}>
              <label>Announcements Channel:</label>
              <input
                type="text"
                className={styles.channelInput}
                placeholder="#announcements"
                value={workspace.default_announcements_channel || ''}
                onChange={(e) => handleUpdateSettings({ default_announcements_channel: e.target.value })}
              />
            </div>
            <div className={styles.channelRow}>
              <label>Alerts Channel:</label>
              <input
                type="text"
                className={styles.channelInput}
                placeholder="#alerts"
                value={workspace.default_alerts_channel || ''}
                onChange={(e) => handleUpdateSettings({ default_alerts_channel: e.target.value })}
              />
            </div>
          </div>

          {/* Actions */}
          <div className={styles.actions}>
            <button
              className={styles.testButton}
              onClick={handleTestConnection}
              disabled={testing}
            >
              {testing ? 'Testing...' : 'Test Connection'}
            </button>
            <button className={styles.disconnectButton} onClick={handleDisconnect}>
              Disconnect
            </button>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className={styles.instructions}>
        <h4 className={styles.instructionsTitle}>Slack Integration Features</h4>
        <ul>
          <li>📢 Automatic notifications for course announcements</li>
          <li>⏰ Deadline reminders sent to designated channels</li>
          <li>📊 Grade release notifications (optional)</li>
          <li>🆕 New content availability alerts</li>
          <li>💬 Discussion reply notifications</li>
          <li>🤖 AI assistant for course questions (beta)</li>
        </ul>
      </div>
    </div>
  );
};

export default SlackIntegrationPanel;
