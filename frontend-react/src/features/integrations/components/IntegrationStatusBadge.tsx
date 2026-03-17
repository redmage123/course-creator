/**
 * IntegrationStatusBadge Component
 *
 * What: Displays integration connection status with color-coded visual indicator
 * Where: Used in all integration panels to show real-time connection health
 * Why: Provides at-a-glance status visualization for integration monitoring
 *
 * BUSINESS CONTEXT:
 * Integration health is critical for business operations - disconnected integrations
 * mean missed notifications, failed grade passbacks, and broken workflows.
 * This component provides immediate visual feedback for troubleshooting.
 *
 * @module features/integrations/components/IntegrationStatusBadge
 */

import React from 'react';
import styles from './IntegrationStatusBadge.module.css';

export interface IntegrationStatusBadgeProps {
  /** Connection status */
  status: 'connected' | 'disconnected' | 'error' | 'pending' | 'syncing';
  /** Optional last sync/connection timestamp */
  lastSync?: string;
  /** Optional error message */
  errorMessage?: string;
  /** Badge size variant */
  size?: 'small' | 'medium' | 'large';
}

/**
 * IntegrationStatusBadge Component
 *
 * WHY THIS APPROACH:
 * - Color-coded status (green=connected, red=error, yellow=pending, blue=syncing)
 * - Animated pulse effect for active syncing state
 * - Tooltip with last sync time and error details
 * - Multiple size variants for different UI contexts
 * - Accessible with aria-label for screen readers
 */
export const IntegrationStatusBadge: React.FC<IntegrationStatusBadgeProps> = ({
  status,
  lastSync,
  errorMessage,
  size = 'medium'
}) => {
  /**
   * Get status display text
   */
  const getStatusText = (): string => {
    switch (status) {
      case 'connected':
        return 'Connected';
      case 'disconnected':
        return 'Disconnected';
      case 'error':
        return 'Error';
      case 'pending':
        return 'Pending';
      case 'syncing':
        return 'Syncing...';
      default:
        return 'Unknown';
    }
  };

  /**
   * Get status color class
   */
  const getStatusClass = (): string => {
    switch (status) {
      case 'connected':
        return styles.statusConnected;
      case 'disconnected':
        return styles.statusDisconnected;
      case 'error':
        return styles.statusError;
      case 'pending':
        return styles.statusPending;
      case 'syncing':
        return styles.statusSyncing;
      default:
        return styles.statusDisconnected;
    }
  };

  /**
   * Format last sync timestamp
   */
  const formatLastSync = (): string | null => {
    if (!lastSync) return null;

    try {
      const date = new Date(lastSync);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
      if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
      if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

      return date.toLocaleDateString();
    } catch (error) {
      return null;
    }
  };

  const statusText = getStatusText();
  const statusClass = getStatusClass();
  const lastSyncText = formatLastSync();

  return (
    <div
      className={`${styles.badge} ${statusClass} ${styles[`size-${size}`]}`}
      role="status"
      aria-label={`Integration status: ${statusText}${errorMessage ? ` - ${errorMessage}` : ''}`}
    >
      {/* Status indicator dot */}
      <span
        className={`${styles.indicator} ${status === 'syncing' ? styles.pulse : ''}`}
        aria-hidden="true"
      />

      {/* Status text */}
      <span className={styles.text}>{statusText}</span>

      {/* Last sync info (medium/large sizes only) */}
      {size !== 'small' && lastSyncText && (
        <span className={styles.lastSync} title={`Last synced: ${lastSync}`}>
          {lastSyncText}
        </span>
      )}

      {/* Error message tooltip */}
      {errorMessage && (
        <span className={styles.errorTooltip} title={errorMessage}>
          ⓘ
        </span>
      )}
    </div>
  );
};

export default IntegrationStatusBadge;
