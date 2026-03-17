/**
 * Offline Indicator Component
 *
 * BUSINESS CONTEXT:
 * Displays current online/offline status to users.
 * Shows when offline mode is active and provides sync status information.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses useDeviceCapabilities hook to monitor connection status.
 * Shows toast-style notification when connection changes.
 */

import React, { useEffect, useState } from 'react';
import { useDeviceCapabilities } from '../hooks/useDeviceCapabilities';
import styles from './OfflineIndicator.module.css';

export interface OfflineIndicatorProps {
  /**
   * Position of the indicator
   * @default 'top'
   */
  position?: 'top' | 'bottom';

  /**
   * Whether to show indicator when online
   * @default false
   */
  showWhenOnline?: boolean;

  /**
   * Custom message for offline state
   */
  offlineMessage?: string;

  /**
   * Custom message for online state
   */
  onlineMessage?: string;

  /**
   * Auto-hide delay in milliseconds (0 = never hide)
   * @default 3000
   */
  autoHideDelay?: number;
}

/**
 * Offline Indicator Component
 *
 * WHY THIS APPROACH:
 * - Unobtrusive toast-style notification
 * - Auto-dismisses when connection restored
 * - Configurable position and messages
 * - Smooth fade in/out animations
 *
 * @param props - Component props
 */
export const OfflineIndicator: React.FC<OfflineIndicatorProps> = ({
  position = 'top',
  showWhenOnline = false,
  offlineMessage = 'You are offline. Some features may be unavailable.',
  onlineMessage = 'Connection restored',
  autoHideDelay = 3000,
}) => {
  const { isOnline } = useDeviceCapabilities();
  const [isVisible, setIsVisible] = useState(false);
  const [previousOnlineState, setPreviousOnlineState] = useState(isOnline);
  const [justCameOnline, setJustCameOnline] = useState(false);

  /**
   * Handle online/offline state changes
   *
   * BUSINESS LOGIC:
   * Shows indicator when connection status changes.
   * Auto-hides online indicator after delay.
   */
  useEffect(() => {
    if (isOnline !== previousOnlineState) {
      setPreviousOnlineState(isOnline);

      if (!isOnline) {
        // Went offline - show permanently
        setIsVisible(true);
        setJustCameOnline(false);
      } else {
        // Came back online - show temporarily
        setJustCameOnline(true);
        setIsVisible(showWhenOnline);

        if (showWhenOnline && autoHideDelay > 0) {
          const timer = setTimeout(() => {
            setIsVisible(false);
            setJustCameOnline(false);
          }, autoHideDelay);

          return () => clearTimeout(timer);
        }
      }
    }
  }, [isOnline, previousOnlineState, showWhenOnline, autoHideDelay]);

  // Don't render if invisible
  if (!isVisible) {
    return null;
  }

  const indicatorClass = [
    styles.offlineIndicator,
    styles[position],
    isOnline ? styles.online : styles.offline,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={indicatorClass} role="status" aria-live="polite">
      <div className={styles.content}>
        <span className={styles.icon} aria-hidden="true">
          {isOnline ? '✓' : '⚠'}
        </span>
        <span className={styles.message}>
          {isOnline && justCameOnline ? onlineMessage : offlineMessage}
        </span>
      </div>
    </div>
  );
};
