/**
 * Accessibility Context
 *
 * BUSINESS CONTEXT:
 * Provides global accessibility state and preferences throughout the application.
 * Enables real-time accessibility feature updates without page refreshes.
 * Ensures consistent accessibility experience across all components.
 *
 * TECHNICAL IMPLEMENTATION:
 * React Context API for global state management of accessibility preferences.
 * Automatically applies preferences to document on load and update.
 * Persists preferences to localStorage for fast initial load.
 *
 * WCAG 2.1 AA Compliance:
 * - Provides centralized accessibility state management
 * - Ensures preferences are applied consistently
 * - Supports real-time accessibility customization
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import {
  accessibilityService,
  AccessibilityPreference,
  FontSizePreference,
  ColorSchemePreference,
  MotionPreference,
  FocusIndicatorStyle,
} from '@services/accessibilityService';

// =============================================================================
// CONTEXT TYPES
// =============================================================================

/**
 * Accessibility Context State
 *
 * What: Complete accessibility state and actions
 * Where: Available throughout the component tree
 * Why: Enables any component to access and modify accessibility settings
 */
interface AccessibilityContextState {
  // State
  preferences: AccessibilityPreference | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  updatePreferences: (updates: Partial<AccessibilityPreference>) => Promise<void>;
  resetPreferences: () => Promise<void>;
  refreshPreferences: () => Promise<void>;

  // Helpers
  announce: (message: string, politeness?: 'polite' | 'assertive') => void;
  getFontSizeMultiplier: () => number;
  getAnimationMultiplier: () => number;
}

/**
 * Provider Props
 *
 * What: Props for AccessibilityProvider component
 * Where: Root of application tree
 * Why: Configures accessibility system
 */
interface AccessibilityProviderProps {
  children: ReactNode;
  userId?: string; // Optional user ID for authenticated users
}

// =============================================================================
// CONTEXT CREATION
// =============================================================================

const AccessibilityContext = createContext<AccessibilityContextState | undefined>(undefined);

/**
 * Accessibility Provider Component
 *
 * BUSINESS LOGIC:
 * Manages global accessibility state for the entire application.
 * Loads preferences on mount, applies them to document, and provides
 * methods for updating preferences.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Loads preferences from backend or localStorage on mount
 * - Applies preferences to document via CSS custom properties
 * - Provides update methods that persist to backend
 * - Re-applies preferences on update for immediate effect
 *
 * @param children - Child components
 * @param userId - Optional authenticated user ID
 */
export const AccessibilityProvider: React.FC<AccessibilityProviderProps> = ({
  children,
  userId,
}) => {
  const [preferences, setPreferences] = useState<AccessibilityPreference | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Load preferences on mount
   *
   * BUSINESS LOGIC:
   * Attempts to load preferences in this order:
   * 1. From backend if user is authenticated
   * 2. From localStorage if available
   * 3. Falls back to default preferences
   */
  useEffect(() => {
    const loadPreferences = async () => {
      setIsLoading(true);
      setError(null);

      try {
        let prefs: AccessibilityPreference;

        if (userId) {
          // Load from backend for authenticated users
          prefs = await accessibilityService.getUserPreferences(userId);
        } else {
          // Load from localStorage for anonymous users
          const stored = localStorage.getItem('accessibility-preferences');
          if (stored) {
            prefs = JSON.parse(stored);
          } else {
            // Use default preferences
            prefs = accessibilityService.getDefaultPreferences('anonymous');
          }
        }

        setPreferences(prefs);
        accessibilityService.applyPreferences(prefs);
      } catch (err: any) {
        console.error('[AccessibilityContext] Failed to load preferences:', err);
        setError(err.message || 'Failed to load accessibility preferences');

        // Fall back to defaults
        const defaultPrefs = accessibilityService.getDefaultPreferences(userId || 'anonymous');
        setPreferences(defaultPrefs);
        accessibilityService.applyPreferences(defaultPrefs);
      } finally {
        setIsLoading(false);
      }
    };

    loadPreferences();
  }, [userId]);

  /**
   * Update preferences
   *
   * BUSINESS LOGIC:
   * Updates one or more accessibility preferences.
   * Persists to backend for authenticated users, localStorage otherwise.
   * Applies changes immediately to document.
   *
   * @param updates - Partial preferences to update
   */
  const updatePreferences = async (updates: Partial<AccessibilityPreference>): Promise<void> => {
    if (!preferences) return;

    setError(null);

    try {
      let updatedPrefs: AccessibilityPreference;

      if (userId) {
        // Save to backend for authenticated users
        updatedPrefs = await accessibilityService.updateUserPreferences(userId, updates);
      } else {
        // Update locally for anonymous users
        updatedPrefs = { ...preferences, ...updates, updatedAt: new Date().toISOString() };
        localStorage.setItem('accessibility-preferences', JSON.stringify(updatedPrefs));
        accessibilityService.applyPreferences(updatedPrefs);
      }

      setPreferences(updatedPrefs);
    } catch (err: any) {
      console.error('[AccessibilityContext] Failed to update preferences:', err);
      setError(err.message || 'Failed to update accessibility preferences');
      throw err;
    }
  };

  /**
   * Reset preferences to defaults
   *
   * BUSINESS LOGIC:
   * Resets all accessibility preferences to platform defaults.
   * Clears backend storage for authenticated users.
   *
   */
  const resetPreferences = async (): Promise<void> => {
    setError(null);

    try {
      let defaultPrefs: AccessibilityPreference;

      if (userId) {
        // Reset on backend for authenticated users
        defaultPrefs = await accessibilityService.resetUserPreferences(userId);
      } else {
        // Reset locally for anonymous users
        defaultPrefs = accessibilityService.getDefaultPreferences('anonymous');
        localStorage.setItem('accessibility-preferences', JSON.stringify(defaultPrefs));
        accessibilityService.applyPreferences(defaultPrefs);
      }

      setPreferences(defaultPrefs);
    } catch (err: any) {
      console.error('[AccessibilityContext] Failed to reset preferences:', err);
      setError(err.message || 'Failed to reset accessibility preferences');
      throw err;
    }
  };

  /**
   * Refresh preferences from backend
   *
   * BUSINESS LOGIC:
   * Reloads preferences from backend.
   * Useful after external changes or sync issues.
   */
  const refreshPreferences = async (): Promise<void> => {
    if (!userId) return;

    setIsLoading(true);
    setError(null);

    try {
      const prefs = await accessibilityService.getUserPreferences(userId);
      setPreferences(prefs);
      accessibilityService.applyPreferences(prefs);
    } catch (err: any) {
      console.error('[AccessibilityContext] Failed to refresh preferences:', err);
      setError(err.message || 'Failed to refresh accessibility preferences');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Announce message to screen readers
   *
   * TECHNICAL IMPLEMENTATION:
   * Creates ARIA live region announcement for assistive technology.
   *
   * @param message - Message to announce
   * @param politeness - Urgency level
   */
  const announce = (message: string, politeness: 'polite' | 'assertive' = 'polite'): void => {
    if (!preferences?.screenReaderOptimizations && politeness !== 'assertive') {
      // Skip non-critical announcements if screen reader optimizations are off
      return;
    }

    accessibilityService.announce(message, politeness);
  };

  /**
   * Get current font size multiplier
   *
   * BUSINESS LOGIC:
   * Returns current font size scaling factor.
   * Used by components that need to adjust sizes programmatically.
   *
   * @returns Font size multiplier (1.0 to 2.0)
   */
  const getFontSizeMultiplier = (): number => {
    if (!preferences) return 1.0;

    const multipliers: Record<FontSizePreference, number> = {
      [FontSizePreference.DEFAULT]: 1.0,
      [FontSizePreference.LARGE]: 1.25,
      [FontSizePreference.EXTRA_LARGE]: 1.5,
      [FontSizePreference.HUGE]: 2.0,
    };

    return multipliers[preferences.fontSize];
  };

  /**
   * Get current animation duration multiplier
   *
   * BUSINESS LOGIC:
   * Returns current animation speed factor.
   * Used by components with custom animations.
   *
   * @returns Animation multiplier (0 to 1.0)
   */
  const getAnimationMultiplier = (): number => {
    if (!preferences) return 1.0;

    const multipliers: Record<MotionPreference, number> = {
      [MotionPreference.NO_PREFERENCE]: 1.0,
      [MotionPreference.REDUCE]: 0.3,
      [MotionPreference.NO_MOTION]: 0,
    };

    return multipliers[preferences.motionPreference];
  };

  // Context value
  const value: AccessibilityContextState = {
    preferences,
    isLoading,
    error,
    updatePreferences,
    resetPreferences,
    refreshPreferences,
    announce,
    getFontSizeMultiplier,
    getAnimationMultiplier,
  };

  return (
    <AccessibilityContext.Provider value={value}>
      {children}
    </AccessibilityContext.Provider>
  );
};

/**
 * Use Accessibility Hook
 *
 * BUSINESS LOGIC:
 * Provides access to accessibility context in any component.
 * Throws error if used outside AccessibilityProvider.
 *
 * @returns Accessibility context state and actions
 * @throws Error if used outside provider
 */
export const useAccessibilityContext = (): AccessibilityContextState => {
  const context = useContext(AccessibilityContext);

  if (context === undefined) {
    throw new Error('useAccessibilityContext must be used within AccessibilityProvider');
  }

  return context;
};
