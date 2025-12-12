/**
 * Welcome Popup Manager Component
 *
 * BUSINESS CONTEXT:
 * Manages the display of the AI Assistant welcome popup.
 * Shows the popup when a user logs in for the first time.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Listens to Redux auth state for isFirstLogin flag
 * - Renders WelcomePopup when appropriate
 * - Clears the flag after popup is closed
 */

import React from 'react';
import { useAuth } from '../../../../hooks/useAuth';
import { WelcomePopup } from '../WelcomePopup';

/**
 * WelcomePopupManager Component
 *
 * WHY THIS APPROACH:
 * - Separates popup display logic from the App component
 * - Uses Redux state to determine when to show popup
 * - Clean integration with authentication flow
 */
export const WelcomePopupManager: React.FC = () => {
  const { isAuthenticated, isFirstLogin, clearFirstLogin } = useAuth();

  // Only show popup if user is authenticated and it's their first login
  if (!isAuthenticated || !isFirstLogin) {
    return null;
  }

  return (
    <WelcomePopup
      isFirstLogin={isFirstLogin}
      onClose={clearFirstLogin}
      onStartTour={clearFirstLogin}
    />
  );
};

export default WelcomePopupManager;
