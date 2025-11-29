/**
 * CalendarSyncPanel Component
 *
 * What: Calendar integration management for Google Calendar and Outlook
 * Where: Used in IntegrationsSettings for calendar synchronization
 * Why: Enables automatic sync of deadlines, quizzes, and class schedules
 *
 * BUSINESS CONTEXT:
 * Calendar sync improves student engagement by automatically adding course
 * deadlines to their personal calendars. Supports bidirectional sync,
 * reminder notifications, and multiple calendar providers.
 *
 * @module features/integrations/components/CalendarSyncPanel
 */

import React, { useState } from 'react';
import { integrationsService } from '../../../services/integrationsService';
import type { CalendarProvider, UpdateCalendarSettingsRequest } from '../../../services/integrationsService';
import IntegrationStatusBadge from './IntegrationStatusBadge';
import styles from './CalendarSyncPanel.module.css';

export interface CalendarSyncPanelProps {
  userId: string;
  calendars: CalendarProvider[];
  onRefresh: () => void;
}

export const CalendarSyncPanel: React.FC<CalendarSyncPanelProps> = ({
  userId,
  calendars,
  onRefresh,
}) => {
  const [selectedProvider, setSelectedProvider] = useState<CalendarProvider | null>(null);
  const [syncSettings, setSyncSettings] = useState<UpdateCalendarSettingsRequest>({});
  const [syncing, setSyncing] = useState(false);

  const handleConnect = (providerType: 'google' | 'outlook') => {
    const redirectUri = `${window.location.origin}/integrations/calendar/callback`;
    const scopes = providerType === 'google'
      ? ['https://www.googleapis.com/auth/calendar']
      : ['Calendars.ReadWrite'];

    integrationsService.initiateOAuthFlow(
      providerType === 'google' ? 'google' : 'microsoft',
      scopes,
      redirectUri
    );
  };

  const handleDisconnect = async (providerId: string) => {
    if (!window.confirm('Disconnect this calendar?')) return;

    try {
      await integrationsService.disconnectCalendar(providerId);
      onRefresh();
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to disconnect calendar');
    }
  };

  const handleSyncNow = async (providerId: string) => {
    setSyncing(true);
    try {
      const result = await integrationsService.triggerCalendarSync(providerId);
      alert(`Successfully synced ${result.synced_count} events`);
      onRefresh();
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to sync calendar');
    } finally {
      setSyncing(false);
    }
  };

  const handleUpdateSettings = async (provider: CalendarProvider) => {
    try {
      await integrationsService.updateCalendarSettings(provider.id, syncSettings);
      alert('Settings updated successfully');
      setSelectedProvider(null);
      onRefresh();
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to update settings');
    }
  };

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>Calendar Sync</h2>
          <p className={styles.description}>
            Automatically sync course deadlines and events to your calendar
          </p>
        </div>
      </div>

      {/* Connect buttons */}
      <div className={styles.connectButtons}>
        <button
          className={`${styles.connectButton} ${styles.google}`}
          onClick={() => handleConnect('google')}
          disabled={calendars.some(c => c.provider_type === 'google')}
        >
          <span className={styles.icon}>📅</span>
          {calendars.some(c => c.provider_type === 'google') ? 'Google Connected' : 'Connect Google Calendar'}
        </button>
        <button
          className={`${styles.connectButton} ${styles.outlook}`}
          onClick={() => handleConnect('outlook')}
          disabled={calendars.some(c => c.provider_type === 'outlook')}
        >
          <span className={styles.icon}>📆</span>
          {calendars.some(c => c.provider_type === 'outlook') ? 'Outlook Connected' : 'Connect Outlook Calendar'}
        </button>
      </div>

      {/* Connected calendars list */}
      {calendars.length > 0 && (
        <div className={styles.calendarList}>
          {calendars.map((calendar) => (
            <div key={calendar.id} className={styles.calendarCard}>
              <div className={styles.calendarHeader}>
                <div>
                  <h3 className={styles.calendarName}>
                    {calendar.provider_type === 'google' ? '📅 Google Calendar' : '📆 Outlook Calendar'}
                  </h3>
                  {calendar.calendar_name && (
                    <p className={styles.calendarSubtitle}>{calendar.calendar_name}</p>
                  )}
                </div>
                <IntegrationStatusBadge
                  status={calendar.is_connected ? 'connected' : 'disconnected'}
                  lastSync={calendar.last_sync_at}
                  errorMessage={calendar.last_sync_error || undefined}
                />
              </div>

              {/* Sync settings */}
              <div className={styles.settings}>
                <label className={styles.settingRow}>
                  <input
                    type="checkbox"
                    checked={calendar.sync_enabled}
                    onChange={(e) => {
                      integrationsService.updateCalendarSettings(calendar.id, {
                        sync_enabled: e.target.checked
                      }).then(onRefresh);
                    }}
                  />
                  <span>Enable automatic sync</span>
                </label>
                <label className={styles.settingRow}>
                  <input
                    type="checkbox"
                    checked={calendar.sync_deadline_reminders}
                    disabled={!calendar.sync_enabled}
                    onChange={(e) => {
                      integrationsService.updateCalendarSettings(calendar.id, {
                        sync_deadline_reminders: e.target.checked
                      }).then(onRefresh);
                    }}
                  />
                  <span>Sync assignment deadlines</span>
                </label>
                <label className={styles.settingRow}>
                  <input
                    type="checkbox"
                    checked={calendar.sync_quiz_dates}
                    disabled={!calendar.sync_enabled}
                    onChange={(e) => {
                      integrationsService.updateCalendarSettings(calendar.id, {
                        sync_quiz_dates: e.target.checked
                      }).then(onRefresh);
                    }}
                  />
                  <span>Sync quiz dates</span>
                </label>
                <label className={styles.settingRow}>
                  <input
                    type="checkbox"
                    checked={calendar.sync_class_schedules}
                    disabled={!calendar.sync_enabled}
                    onChange={(e) => {
                      integrationsService.updateCalendarSettings(calendar.id, {
                        sync_class_schedules: e.target.checked
                      }).then(onRefresh);
                    }}
                  />
                  <span>Sync class schedules</span>
                </label>
              </div>

              {/* Actions */}
              <div className={styles.calendarActions}>
                <button
                  className={styles.syncButton}
                  onClick={() => handleSyncNow(calendar.id)}
                  disabled={syncing}
                >
                  {syncing ? 'Syncing...' : 'Sync Now'}
                </button>
                <button
                  className={styles.disconnectButton}
                  onClick={() => handleDisconnect(calendar.id)}
                >
                  Disconnect
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {calendars.length === 0 && (
        <div className={styles.emptyState}>
          <p>No calendars connected</p>
          <p className={styles.emptyStateHint}>
            Connect Google Calendar or Outlook to automatically sync course events
          </p>
        </div>
      )}
    </div>
  );
};

export default CalendarSyncPanel;
