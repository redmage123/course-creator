/**
 * NotificationManager Component
 *
 * BUSINESS CONTEXT:
 * Global notification manager that displays toast notifications from Redux store.
 * Used throughout the platform for user feedback (success, error, warning, info).
 *
 * TECHNICAL IMPLEMENTATION:
 * Subscribes to Redux notifications slice and renders Toast components.
 * Auto-removes notifications after they're dismissed.
 */

import React from 'react';
import { useAppSelector, useAppDispatch } from '../../../hooks/useRedux';
import { removeNotification } from '../../../store/slices/uiSlice';
import { Toast } from '../../atoms/Toast';

/**
 * NotificationManager Component
 *
 * WHY THIS APPROACH:
 * - Centralized notification rendering
 * - Redux integration for global notification state
 * - Stacks multiple notifications
 * - Auto-dismiss with manual dismiss option
 *
 * @example
 * ```tsx
 * // Add to App.tsx
 * <NotificationManager />
 * ```
 */
export const NotificationManager: React.FC = () => {
  const notifications = useAppSelector((state) => state.ui.notifications);
  const dispatch = useAppDispatch();

  const handleDismiss = (id: string) => {
    dispatch(removeNotification(id));
  };

  if (notifications.length === 0) {
    return null;
  }

  return (
    <>
      {notifications.map((notification, index) => (
        <Toast
          key={notification.id}
          message={notification.message}
          variant={notification.type}
          duration={notification.duration || 5000}
          onDismiss={() => handleDismiss(notification.id)}
          position="top-right"
          className={`notification-toast-${index}`}
        />
      ))}
    </>
  );
};

NotificationManager.displayName = 'NotificationManager';
