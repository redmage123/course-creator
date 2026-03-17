/**
 * Device Capabilities Hook
 *
 * BUSINESS CONTEXT:
 * Detects device capabilities and connection status for the Course Creator Platform.
 * Enables progressive enhancement and feature detection for optimal user experience.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses browser APIs to detect hardware features, network status, and performance metrics.
 * Provides real-time updates on connection changes and device orientation.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  mobileExperienceService,
  DeviceCapabilities,
  ConnectionType,
} from '@services/mobileExperienceService';

interface NetworkInformation {
  type?: ConnectionType;
  effectiveType?: string;
  downlink?: number;
  rtt?: number;
  saveData?: boolean;
}

interface BatteryStatus {
  level: number; // 0-1
  charging: boolean;
  chargingTime?: number;
  dischargingTime?: number;
}

interface DeviceOrientation {
  angle: number;
  type: 'portrait-primary' | 'portrait-secondary' | 'landscape-primary' | 'landscape-secondary';
}

/**
 * Device Capabilities Hook
 *
 * WHY THIS APPROACH:
 * - Real-time capability detection
 * - Network status monitoring
 * - Battery status tracking
 * - Orientation change detection
 * - Performance metrics collection
 *
 * @returns Device capabilities state and methods
 */
export const useDeviceCapabilities = () => {
  const [capabilities, setCapabilities] = useState<DeviceCapabilities | null>(null);
  const [networkInfo, setNetworkInfo] = useState<NetworkInformation>({});
  const [batteryStatus, setBatteryStatus] = useState<BatteryStatus | null>(null);
  const [orientation, setOrientation] = useState<DeviceOrientation | null>(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [screenWidth, setScreenWidth] = useState(window.innerWidth);
  const [screenHeight, setScreenHeight] = useState(window.innerHeight);

  /**
   * Detect device capabilities
   *
   * BUSINESS LOGIC:
   * Detects all available browser and device features.
   * Called on mount and when capabilities may have changed.
   */
  const detectCapabilities = useCallback(() => {
    const detected = mobileExperienceService.detectDeviceCapabilities();
    setCapabilities(detected);
  }, []);

  /**
   * Update network information
   *
   * BUSINESS LOGIC:
   * Reads current network status from Network Information API.
   * Updates when connection type or quality changes.
   */
  const updateNetworkInfo = useCallback(() => {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      setNetworkInfo({
        type: connection.type,
        effectiveType: connection.effectiveType,
        downlink: connection.downlink,
        rtt: connection.rtt,
        saveData: connection.saveData,
      });
    }
  }, []);

  /**
   * Update battery status
   *
   * BUSINESS LOGIC:
   * Reads current battery level and charging status.
   * Used to adjust behavior when battery is low.
   */
  const updateBatteryStatus = useCallback(async () => {
    try {
      if ('getBattery' in navigator) {
        const battery = await (navigator as any).getBattery();
        setBatteryStatus({
          level: battery.level,
          charging: battery.charging,
          chargingTime: battery.chargingTime,
          dischargingTime: battery.dischargingTime,
        });

        // Listen for battery changes
        battery.addEventListener('levelchange', () => {
          setBatteryStatus({
            level: battery.level,
            charging: battery.charging,
            chargingTime: battery.chargingTime,
            dischargingTime: battery.dischargingTime,
          });
        });

        battery.addEventListener('chargingchange', () => {
          setBatteryStatus({
            level: battery.level,
            charging: battery.charging,
            chargingTime: battery.chargingTime,
            dischargingTime: battery.dischargingTime,
          });
        });
      }
    } catch (error) {
      console.warn('[useDeviceCapabilities] Battery API not available');
    }
  }, []);

  /**
   * Update device orientation
   *
   * BUSINESS LOGIC:
   * Detects current device orientation.
   * Used for responsive layout decisions.
   */
  const updateOrientation = useCallback(() => {
    if ('screen' in window && 'orientation' in screen) {
      const screenOrientation = screen.orientation;
      setOrientation({
        angle: screenOrientation.angle,
        type: screenOrientation.type,
      });
    }
  }, []);

  /**
   * Request camera permission
   *
   * BUSINESS LOGIC:
   * Requests access to device camera for video recording.
   * Used in lab environments and content creation.
   *
   * @returns MediaStream or null if denied
   */
  const requestCamera = useCallback(async (): Promise<MediaStream | null> => {
    try {
      if (!capabilities?.hasCamera) {
        console.warn('[useDeviceCapabilities] Camera not available');
        return null;
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
      });

      return stream;
    } catch (error) {
      console.error('[useDeviceCapabilities] Camera access denied:', error);
      return null;
    }
  }, [capabilities]);

  /**
   * Request microphone permission
   *
   * BUSINESS LOGIC:
   * Requests access to device microphone for audio recording.
   * Used in lab environments and content creation.
   *
   * @returns MediaStream or null if denied
   */
  const requestMicrophone = useCallback(async (): Promise<MediaStream | null> => {
    try {
      if (!capabilities?.hasMicrophone) {
        console.warn('[useDeviceCapabilities] Microphone not available');
        return null;
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: false,
        audio: true,
      });

      return stream;
    } catch (error) {
      console.error('[useDeviceCapabilities] Microphone access denied:', error);
      return null;
    }
  }, [capabilities]);

  /**
   * Request geolocation permission
   *
   * BUSINESS LOGIC:
   * Requests access to device location.
   * Used for location-based features and analytics.
   *
   * @returns GeolocationPosition or null if denied
   */
  const requestGeolocation = useCallback(async (): Promise<GeolocationPosition | null> => {
    try {
      if (!capabilities?.hasGeolocation) {
        console.warn('[useDeviceCapabilities] Geolocation not available');
        return null;
      }

      return new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
          (position) => resolve(position),
          (error) => reject(error)
        );
      });
    } catch (error) {
      console.error('[useDeviceCapabilities] Geolocation access denied:', error);
      return null;
    }
  }, [capabilities]);

  /**
   * Vibrate device
   *
   * BUSINESS LOGIC:
   * Triggers device vibration for haptic feedback.
   * Used for notifications and UI interactions.
   *
   * @param pattern - Vibration pattern in milliseconds
   */
  const vibrate = useCallback(
    (pattern: number | number[]) => {
      if (capabilities?.hasVibration) {
        mobileExperienceService.vibrate(pattern);
      }
    },
    [capabilities]
  );

  /**
   * Copy to clipboard
   *
   * BUSINESS LOGIC:
   * Copies text to device clipboard.
   * Used for sharing content and code snippets.
   *
   * @param text - Text to copy
   * @returns True if successful, false otherwise
   */
  const copyToClipboard = useCallback(async (text: string): Promise<boolean> => {
    try {
      if ('clipboard' in navigator) {
        await navigator.clipboard.writeText(text);
        return true;
      }

      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      const success = document.execCommand('copy');
      document.body.removeChild(textarea);
      return success;
    } catch (error) {
      console.error('[useDeviceCapabilities] Copy to clipboard failed:', error);
      return false;
    }
  }, []);

  /**
   * Share content
   *
   * BUSINESS LOGIC:
   * Uses Web Share API to share content natively.
   * Fallback to clipboard if not supported.
   *
   * @param data - Share data (title, text, url)
   * @returns True if shared, false otherwise
   */
  const shareContent = useCallback(
    async (data: { title?: string; text?: string; url?: string }): Promise<boolean> => {
      try {
        if ('share' in navigator) {
          await navigator.share(data);
          return true;
        }

        // Fallback to clipboard
        const shareText = `${data.title || ''}\n${data.text || ''}\n${data.url || ''}`.trim();
        return await copyToClipboard(shareText);
      } catch (error) {
        console.error('[useDeviceCapabilities] Share failed:', error);
        return false;
      }
    },
    [copyToClipboard]
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
   * Handle network changes
   */
  useEffect(() => {
    updateNetworkInfo();

    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      connection.addEventListener('change', updateNetworkInfo);

      return () => {
        connection.removeEventListener('change', updateNetworkInfo);
      };
    }
  }, [updateNetworkInfo]);

  /**
   * Handle orientation changes
   */
  useEffect(() => {
    updateOrientation();

    if ('screen' in window && 'orientation' in screen) {
      screen.orientation.addEventListener('change', updateOrientation);

      return () => {
        screen.orientation.removeEventListener('change', updateOrientation);
      };
    }
  }, [updateOrientation]);

  /**
   * Handle window resize
   */
  useEffect(() => {
    const handleResize = () => {
      setScreenWidth(window.innerWidth);
      setScreenHeight(window.innerHeight);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  /**
   * Initialize on mount
   */
  useEffect(() => {
    detectCapabilities();
    updateBatteryStatus();
  }, [detectCapabilities, updateBatteryStatus]);

  /**
   * Get responsive breakpoint
   */
  const getBreakpoint = useCallback((): string => {
    if (screenWidth < 640) return 'xs';
    if (screenWidth < 768) return 'sm';
    if (screenWidth < 1024) return 'md';
    if (screenWidth < 1280) return 'lg';
    if (screenWidth < 1536) return 'xl';
    return '2xl';
  }, [screenWidth]);

  return {
    // State
    capabilities,
    networkInfo,
    batteryStatus,
    orientation,
    isOnline,
    screenWidth,
    screenHeight,

    // Methods
    detectCapabilities,
    requestCamera,
    requestMicrophone,
    requestGeolocation,
    vibrate,
    copyToClipboard,
    shareContent,
    getBreakpoint,

    // Computed
    hasServiceWorker: capabilities?.hasServiceWorker || false,
    hasPushNotifications: capabilities?.hasPushNotifications || false,
    hasGeolocation: capabilities?.hasGeolocation || false,
    hasCamera: capabilities?.hasCamera || false,
    hasMicrophone: capabilities?.hasMicrophone || false,
    hasVibration: capabilities?.hasVibration || false,
    hasTouch: capabilities?.hasTouch || false,
    isMetered: networkInfo.saveData || networkInfo.type === ConnectionType.FOUR_G,
    isSlowConnection:
      networkInfo.effectiveType === 'slow-2g' ||
      networkInfo.effectiveType === '2g' ||
      networkInfo.effectiveType === '3g',
    isLowBattery: batteryStatus ? batteryStatus.level < 0.2 && !batteryStatus.charging : false,
    isPortrait: orientation?.type.includes('portrait') || screenHeight > screenWidth,
    isLandscape: orientation?.type.includes('landscape') || screenWidth > screenHeight,
    breakpoint: getBreakpoint(),
  };
};
