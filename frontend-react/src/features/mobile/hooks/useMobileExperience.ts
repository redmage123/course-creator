/**
 * Mobile Experience Hook
 *
 * BUSINESS CONTEXT:
 * Provides mobile experience state and methods throughout the application.
 * Centralizes mobile-specific logic for consistent behavior across components.
 *
 * TECHNICAL IMPLEMENTATION:
 * Manages device preferences, capabilities, and mobile-specific settings.
 * Integrates with mobileExperienceService for backend synchronization.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  mobileExperienceService,
  UserDevicePreference,
  DeviceCapabilities,
  DeviceType,
  Theme,
  FontSize,
  NavigationType,
  VideoQuality,
  ImageQuality,
} from '@services/mobileExperienceService';

/**
 * Mobile Experience Hook
 *
 * WHY THIS APPROACH:
 * - Single hook for all mobile experience operations
 * - Automatic state management
 * - Consistent error handling
 * - Device capability detection
 * - Preference persistence
 *
 * @returns Mobile experience state and methods
 */
export const useMobileExperience = () => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [devicePreferences, setDevicePreferences] = useState<UserDevicePreference | null>(null);
  const [deviceCapabilities, setDeviceCapabilities] = useState<DeviceCapabilities | null>(null);
  const [deviceType, setDeviceType] = useState<DeviceType>(DeviceType.DESKTOP);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isMetered, setIsMetered] = useState(false);

  /**
   * Initialize mobile experience
   *
   * BUSINESS LOGIC:
   * Called once on hook mount. Initializes mobile service,
   * detects device capabilities, and loads user preferences.
   */
  const initialize = useCallback(async () => {
    if (isInitialized) return;

    try {
      setIsLoading(true);

      // Initialize mobile service
      await mobileExperienceService.initialize();

      // Detect device capabilities
      const capabilities = mobileExperienceService.detectDeviceCapabilities();
      setDeviceCapabilities(capabilities);

      // Detect device type
      const type = mobileExperienceService.detectDeviceType();
      setDeviceType(type);

      // Check if metered connection
      setIsMetered(mobileExperienceService.isMeteredConnection());

      // Load device preferences
      try {
        const preferences = await mobileExperienceService.getDevicePreferences();
        setDevicePreferences(preferences);
      } catch (error) {
        // Preferences may not exist yet - that's okay
        console.warn('[useMobileExperience] No device preferences found');
      }

      setIsInitialized(true);
    } catch (error) {
      console.error('[useMobileExperience] Initialization failed:', error);
    } finally {
      setIsLoading(false);
    }
  }, [isInitialized]);

  /**
   * Update device preferences
   *
   * BUSINESS LOGIC:
   * Updates device preferences both locally and on backend.
   * Triggers UI updates to reflect new settings.
   *
   * @param preferences - Updated preference values
   */
  const updatePreferences = useCallback(
    async (preferences: Partial<UserDevicePreference>) => {
      try {
        setIsLoading(true);
        const updated = await mobileExperienceService.updateDevicePreferences(preferences);
        setDevicePreferences(updated);
      } catch (error) {
        console.error('[useMobileExperience] Update preferences failed:', error);
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  /**
   * Set theme preference
   *
   * BUSINESS LOGIC:
   * Updates theme preference and applies to DOM.
   *
   * @param theme - Theme value to set
   */
  const setTheme = useCallback(
    async (theme: Theme) => {
      try {
        await updatePreferences({ preferred_theme: theme });

        // Apply theme to document
        const root = document.documentElement;
        if (theme === Theme.SYSTEM) {
          const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
          root.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        } else {
          root.setAttribute('data-theme', theme);
        }
      } catch (error) {
        console.error('[useMobileExperience] Set theme failed:', error);
      }
    },
    [updatePreferences]
  );

  /**
   * Set font size preference
   *
   * BUSINESS LOGIC:
   * Updates font size preference and applies to DOM.
   *
   * @param fontSize - Font size value to set
   */
  const setFontSize = useCallback(
    async (fontSize: FontSize) => {
      try {
        await updatePreferences({ font_size_preference: fontSize });

        // Apply font size to document
        const root = document.documentElement;
        root.setAttribute('data-font-size', fontSize);
      } catch (error) {
        console.error('[useMobileExperience] Set font size failed:', error);
      }
    },
    [updatePreferences]
  );

  /**
   * Toggle data saver mode
   *
   * BUSINESS LOGIC:
   * Enables/disables data saver mode which reduces bandwidth usage.
   *
   * @param enabled - Whether to enable data saver
   */
  const toggleDataSaver = useCallback(
    async (enabled: boolean) => {
      try {
        await updatePreferences({
          data_saver_mode: enabled,
          video_quality_preference: enabled ? VideoQuality.LOW : VideoQuality.AUTO,
          image_quality_preference: enabled ? ImageQuality.LOW : ImageQuality.AUTO,
          auto_play_video: !enabled,
        });
      } catch (error) {
        console.error('[useMobileExperience] Toggle data saver failed:', error);
      }
    },
    [updatePreferences]
  );

  /**
   * Toggle reduced motion
   *
   * BUSINESS LOGIC:
   * Enables/disables animations for accessibility.
   *
   * @param enabled - Whether to reduce motion
   */
  const toggleReducedMotion = useCallback(
    async (enabled: boolean) => {
      try {
        await updatePreferences({ reduced_motion: enabled });

        // Apply to document
        const root = document.documentElement;
        root.setAttribute('data-reduced-motion', enabled.toString());
      } catch (error) {
        console.error('[useMobileExperience] Toggle reduced motion failed:', error);
      }
    },
    [updatePreferences]
  );

  /**
   * Vibrate device
   *
   * BUSINESS LOGIC:
   * Provides haptic feedback if supported and enabled.
   *
   * @param pattern - Vibration pattern in milliseconds
   */
  const vibrate = useCallback(
    (pattern: number | number[]) => {
      if (devicePreferences?.haptic_feedback && deviceCapabilities?.hasVibration) {
        mobileExperienceService.vibrate(pattern);
      }
    },
    [devicePreferences, deviceCapabilities]
  );

  /**
   * Handle online/offline events
   */
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  /**
   * Initialize on mount
   */
  useEffect(() => {
    initialize();
  }, [initialize]);

  /**
   * Apply preferences to DOM on load
   */
  useEffect(() => {
    if (devicePreferences) {
      const root = document.documentElement;

      // Apply theme
      if (devicePreferences.preferred_theme === Theme.SYSTEM) {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        root.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
      } else {
        root.setAttribute('data-theme', devicePreferences.preferred_theme);
      }

      // Apply font size
      root.setAttribute('data-font-size', devicePreferences.font_size_preference);

      // Apply reduced motion
      root.setAttribute('data-reduced-motion', devicePreferences.reduced_motion.toString());

      // Apply high contrast
      root.setAttribute('data-high-contrast', devicePreferences.high_contrast.toString());

      // Apply compact mode
      root.setAttribute('data-compact-mode', devicePreferences.compact_mode.toString());
    }
  }, [devicePreferences]);

  return {
    // State
    isInitialized,
    isLoading,
    devicePreferences,
    deviceCapabilities,
    deviceType,
    isOnline,
    isMetered,

    // Methods
    initialize,
    updatePreferences,
    setTheme,
    setFontSize,
    toggleDataSaver,
    toggleReducedMotion,
    vibrate,

    // Computed
    isMobile: deviceType === DeviceType.MOBILE,
    isTablet: deviceType === DeviceType.TABLET,
    isDesktop: deviceType === DeviceType.DESKTOP,
    hasTouch: deviceCapabilities?.hasTouch || false,
    hasServiceWorker: deviceCapabilities?.hasServiceWorker || false,
    hasPushNotifications: deviceCapabilities?.hasPushNotifications || false,
    hasVibration: deviceCapabilities?.hasVibration || false,
    isDataSaverEnabled: devicePreferences?.data_saver_mode || false,
    isReducedMotion: devicePreferences?.reduced_motion || false,
  };
};
