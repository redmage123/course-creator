/**
 * Mobile Experience Service
 *
 * BUSINESS CONTEXT:
 * Handles mobile-specific functionality including offline synchronization,
 * push notifications, device capability detection, and bandwidth optimization
 * for the Course Creator Platform mobile experience.
 *
 * TECHNICAL IMPLEMENTATION:
 * Communicates with user-management service for mobile preferences and settings.
 * Integrates with Service Worker API for offline functionality and Push API
 * for notifications. Manages device detection and responsive behavior.
 */

import { apiClient } from './apiClient';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

export enum DeviceType {
  MOBILE = 'mobile',
  TABLET = 'tablet',
  DESKTOP = 'desktop',
  WATCH = 'watch',
  TV = 'tv',
}

export enum Theme {
  LIGHT = 'light',
  DARK = 'dark',
  SYSTEM = 'system',
  HIGH_CONTRAST = 'high_contrast',
}

export enum FontSize {
  SMALL = 'small',
  MEDIUM = 'medium',
  LARGE = 'large',
  EXTRA_LARGE = 'extra_large',
}

export enum NavigationType {
  BOTTOM_TABS = 'bottom_tabs',
  SIDEBAR = 'sidebar',
  HAMBURGER = 'hamburger',
  AUTO = 'auto',
}

export enum VideoQuality {
  AUTO = 'auto',
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  FOUR_K = '4k',
}

export enum ImageQuality {
  AUTO = 'auto',
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
}

export enum ConnectionType {
  WIFI = 'wifi',
  FIVE_G = '5g',
  FOUR_G = '4g',
  THREE_G = '3g',
  TWO_G = '2g',
  OFFLINE = 'offline',
  UNKNOWN = 'unknown',
}

export enum SyncStatus {
  PENDING = 'pending',
  DOWNLOADING = 'downloading',
  DOWNLOADED = 'downloaded',
  SYNCING = 'syncing',
  SYNCED = 'synced',
  ERROR = 'error',
  EXPIRED = 'expired',
  DELETED = 'deleted',
}

export enum ContentType {
  COURSE = 'course',
  MODULE = 'module',
  LESSON = 'lesson',
  QUIZ = 'quiz',
  LAB = 'lab',
  VIDEO = 'video',
  DOCUMENT = 'document',
  SLIDE = 'slide',
}

export enum NotificationCategory {
  COURSE_UPDATES = 'course_updates',
  QUIZ_REMINDERS = 'quiz_reminders',
  ASSIGNMENT_DEADLINES = 'assignment_deadlines',
  DISCUSSION_REPLIES = 'discussion_replies',
  INSTRUCTOR_MESSAGES = 'instructor_messages',
  CERTIFICATE_EARNED = 'certificate_earned',
  NEW_CONTENT = 'new_content_available',
  PROMOTIONS = 'promotion_offers',
  SYSTEM = 'system_announcements',
}

export interface UserDevicePreference {
  id: string;
  user_id: string;
  device_id: string;
  device_type: DeviceType;
  device_name?: string;
  os_name?: string;
  os_version?: string;
  browser_name?: string;
  browser_version?: string;
  screen_width?: number;
  screen_height?: number;
  pixel_ratio?: number;
  preferred_theme: Theme;
  font_size_preference: FontSize;
  reduced_motion: boolean;
  high_contrast: boolean;
  compact_mode: boolean;
  sidebar_collapsed: boolean;
  preferred_navigation: NavigationType;
  gesture_navigation: boolean;
  haptic_feedback: boolean;
  data_saver_mode: boolean;
  auto_play_video: boolean;
  video_quality_preference: VideoQuality;
  image_quality_preference: ImageQuality;
  offline_enabled: boolean;
  max_offline_storage_mb: number;
  auto_download_wifi_only: boolean;
  is_primary_device: boolean;
  last_active_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface OfflineContentSync {
  id: string;
  user_id: string;
  device_id: string;
  content_type: ContentType;
  content_id: string;
  content_version?: string;
  sync_status: SyncStatus;
  sync_priority: number;
  storage_size_bytes?: number;
  compressed_size_bytes?: number;
  storage_path?: string;
  checksum?: string;
  queued_at: string;
  download_started_at?: string;
  download_completed_at?: string;
  last_synced_at?: string;
  expires_at?: string;
  retry_count: number;
  max_retries: number;
  last_error?: string;
  has_offline_progress: boolean;
  offline_progress_data?: Record<string, any>;
  progress_synced_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface PushNotificationSettings {
  id: string;
  user_id: string;
  device_preference_id?: string;
  fcm_token?: string;
  apns_token?: string;
  web_push_endpoint?: string;
  web_push_p256dh?: string;
  web_push_auth?: string;
  notifications_enabled: boolean;
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  quiet_hours_timezone?: string;
  course_updates: boolean;
  quiz_reminders: boolean;
  assignment_deadlines: boolean;
  discussion_replies: boolean;
  instructor_messages: boolean;
  certificate_earned: boolean;
  new_content_available: boolean;
  promotion_offers: boolean;
  system_announcements: boolean;
  group_notifications: boolean;
  show_preview: boolean;
  sound_enabled: boolean;
  vibration_enabled: boolean;
  badge_count_enabled: boolean;
  max_notifications_per_hour: number;
  digest_mode: boolean;
  digest_time?: string;
  token_updated_at?: string;
  last_notification_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface DeviceCapabilities {
  hasServiceWorker: boolean;
  hasPushNotifications: boolean;
  hasGeolocation: boolean;
  hasCamera: boolean;
  hasMicrophone: boolean;
  hasVibration: boolean;
  hasOrientation: boolean;
  hasTouch: boolean;
  hasNetworkInfo: boolean;
  hasBatteryStatus: boolean;
  maxTouchPoints: number;
  deviceMemory?: number;
  hardwareConcurrency?: number;
  connectionType?: ConnectionType;
  effectiveType?: string;
  downlink?: number;
  rtt?: number;
  saveData?: boolean;
}

export interface BandwidthUsage {
  id: string;
  user_id: string;
  usage_date: string;
  device_preference_id?: string;
  session_id?: string;
  usage_hour?: number;
  video_bytes_downloaded: number;
  image_bytes_downloaded: number;
  document_bytes_downloaded: number;
  api_bytes_downloaded: number;
  other_bytes_downloaded: number;
  total_bytes_downloaded: number;
  bytes_uploaded: number;
  connection_type?: ConnectionType;
  is_metered?: boolean;
  bytes_saved_compression: number;
  bytes_saved_caching: number;
  bytes_saved_data_saver: number;
  created_at?: string;
}

// ============================================================================
// SERVICE CLASS
// ============================================================================

/**
 * Mobile Experience Service Class
 *
 * WHY THIS APPROACH:
 * - Centralized mobile functionality management
 * - Type-safe API calls for mobile features
 * - Consistent error handling across mobile operations
 * - Easy to mock for testing
 * - Supports offline-first architecture
 */
class MobileExperienceService {
  private deviceId: string | null = null;

  /**
   * Initialize mobile experience service
   *
   * BUSINESS LOGIC:
   * Generates or retrieves device ID and detects device capabilities.
   * Called once on app initialization.
   */
  async initialize(): Promise<void> {
    try {
      this.deviceId = this.getOrCreateDeviceId();

      // Register service worker if supported
      if ('serviceWorker' in navigator) {
        await this.registerServiceWorker();
      }
    } catch (error) {
      console.error('[MobileExperienceService] Initialization failed:', error);
    }
  }

  /**
   * Get or create device ID
   *
   * WHY THIS APPROACH:
   * Uses localStorage to persist device ID across sessions.
   * Generates UUID v4 if no ID exists.
   *
   * @returns Device ID string
   */
  private getOrCreateDeviceId(): string {
    const DEVICE_ID_KEY = 'course-creator-device-id';
    let deviceId = localStorage.getItem(DEVICE_ID_KEY);

    if (!deviceId) {
      deviceId = this.generateUUID();
      localStorage.setItem(DEVICE_ID_KEY, deviceId);
    }

    return deviceId;
  }

  /**
   * Generate UUID v4
   *
   * TECHNICAL IMPLEMENTATION:
   * Uses crypto.randomUUID if available, falls back to Math.random.
   */
  private generateUUID(): string {
    if (crypto.randomUUID) {
      return crypto.randomUUID();
    }

    // Fallback for older browsers
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  // ============================================================================
  // DEVICE PREFERENCES
  // ============================================================================

  /**
   * Get current device preferences
   *
   * BUSINESS LOGIC:
   * Retrieves user's device-specific preferences from backend.
   * Used to personalize UI and behavior for current device.
   *
   * @returns Device preferences
   */
  async getDevicePreferences(): Promise<UserDevicePreference> {
    try {
      const response = await apiClient.get(`/mobile/device-preferences/${this.deviceId}`);
      return response.data;
    } catch (error) {
      console.error('[MobileExperienceService] Get device preferences failed:', error);
      throw error;
    }
  }

  /**
   * Update device preferences
   *
   * BUSINESS LOGIC:
   * Updates user's device-specific preferences on backend.
   * Triggers UI updates to reflect new preferences.
   *
   * @param preferences - Updated preference values
   * @returns Updated device preferences
   */
  async updateDevicePreferences(
    preferences: Partial<UserDevicePreference>
  ): Promise<UserDevicePreference> {
    try {
      const response = await apiClient.put(
        `/mobile/device-preferences/${this.deviceId}`,
        preferences
      );
      return response.data;
    } catch (error) {
      console.error('[MobileExperienceService] Update device preferences failed:', error);
      throw error;
    }
  }

  /**
   * Detect device capabilities
   *
   * BUSINESS LOGIC:
   * Detects browser and device capabilities for feature detection.
   * Used to enable/disable features based on device support.
   *
   * @returns Device capabilities object
   */
  detectDeviceCapabilities(): DeviceCapabilities {
    const capabilities: DeviceCapabilities = {
      hasServiceWorker: 'serviceWorker' in navigator,
      hasPushNotifications: 'PushManager' in window,
      hasGeolocation: 'geolocation' in navigator,
      hasCamera: 'mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices,
      hasMicrophone: 'mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices,
      hasVibration: 'vibrate' in navigator,
      hasOrientation: 'DeviceOrientationEvent' in window,
      hasTouch: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
      hasNetworkInfo: 'connection' in navigator,
      hasBatteryStatus: 'getBattery' in navigator,
      maxTouchPoints: navigator.maxTouchPoints || 0,
    };

    // Device memory (Chrome only)
    if ('deviceMemory' in navigator) {
      capabilities.deviceMemory = (navigator as any).deviceMemory;
    }

    // Hardware concurrency
    if ('hardwareConcurrency' in navigator) {
      capabilities.hardwareConcurrency = navigator.hardwareConcurrency;
    }

    // Network information
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      capabilities.effectiveType = connection.effectiveType;
      capabilities.downlink = connection.downlink;
      capabilities.rtt = connection.rtt;
      capabilities.saveData = connection.saveData;

      // Map to ConnectionType enum
      const typeMap: Record<string, ConnectionType> = {
        'slow-2g': ConnectionType.TWO_G,
        '2g': ConnectionType.TWO_G,
        '3g': ConnectionType.THREE_G,
        '4g': ConnectionType.FOUR_G,
        '5g': ConnectionType.FIVE_G,
      };
      capabilities.connectionType = typeMap[connection.effectiveType] || ConnectionType.UNKNOWN;
    }

    return capabilities;
  }

  /**
   * Detect device type
   *
   * BUSINESS LOGIC:
   * Determines device type from user agent and screen size.
   * Used for responsive layout decisions.
   *
   * @returns Device type enum value
   */
  detectDeviceType(): DeviceType {
    const userAgent = navigator.userAgent.toLowerCase();
    const width = window.innerWidth;

    // TV detection
    if (userAgent.includes('tv') || userAgent.includes('smarttv')) {
      return DeviceType.TV;
    }

    // Watch detection
    if (userAgent.includes('watch')) {
      return DeviceType.WATCH;
    }

    // Tablet detection
    if (userAgent.includes('tablet') || userAgent.includes('ipad')) {
      return DeviceType.TABLET;
    }

    // Mobile detection (including large phones)
    if (
      userAgent.includes('mobile') ||
      userAgent.includes('android') ||
      userAgent.includes('iphone') ||
      width < 768
    ) {
      return DeviceType.MOBILE;
    }

    return DeviceType.DESKTOP;
  }

  // ============================================================================
  // OFFLINE SYNC
  // ============================================================================

  /**
   * Get offline sync items
   *
   * BUSINESS LOGIC:
   * Retrieves list of content items queued for offline sync.
   * Used to display sync status to user.
   *
   * @returns List of offline sync items
   */
  async getOfflineSyncItems(): Promise<OfflineContentSync[]> {
    try {
      const response = await apiClient.get(`/mobile/offline-sync/${this.deviceId}`);
      return response.data;
    } catch (error) {
      console.error('[MobileExperienceService] Get offline sync items failed:', error);
      throw error;
    }
  }

  /**
   * Queue content for offline sync
   *
   * BUSINESS LOGIC:
   * Adds content item to offline download queue.
   * Respects data saver and WiFi-only settings.
   *
   * @param contentType - Type of content (course, module, lesson, etc.)
   * @param contentId - ID of content to sync
   * @param priority - Sync priority (1-10)
   * @returns Created sync item
   */
  async queueOfflineSync(
    contentType: ContentType,
    contentId: string,
    priority: number = 5
  ): Promise<OfflineContentSync> {
    try {
      const response = await apiClient.post('/mobile/offline-sync', {
        device_id: this.deviceId,
        content_type: contentType,
        content_id: contentId,
        sync_priority: priority,
      });
      return response.data;
    } catch (error) {
      console.error('[MobileExperienceService] Queue offline sync failed:', error);
      throw error;
    }
  }

  /**
   * Cancel offline sync
   *
   * BUSINESS LOGIC:
   * Removes content from offline download queue or deletes downloaded content.
   * Frees up storage space.
   *
   * @param syncId - ID of sync item to cancel
   */
  async cancelOfflineSync(syncId: string): Promise<void> {
    try {
      await apiClient.delete(`/mobile/offline-sync/${syncId}`);
    } catch (error) {
      console.error('[MobileExperienceService] Cancel offline sync failed:', error);
      throw error;
    }
  }

  /**
   * Sync offline progress
   *
   * BUSINESS LOGIC:
   * Uploads progress made while offline to backend.
   * Called when internet connection is restored.
   *
   * @param syncId - ID of sync item
   * @param progressData - Progress data to sync
   */
  async syncOfflineProgress(syncId: string, progressData: Record<string, any>): Promise<void> {
    try {
      await apiClient.put(`/mobile/offline-sync/${syncId}/progress`, {
        offline_progress_data: progressData,
      });
    } catch (error) {
      console.error('[MobileExperienceService] Sync offline progress failed:', error);
      throw error;
    }
  }

  // ============================================================================
  // PUSH NOTIFICATIONS
  // ============================================================================

  /**
   * Get push notification settings
   *
   * BUSINESS LOGIC:
   * Retrieves user's push notification preferences.
   * Used to configure notification UI.
   *
   * @returns Notification settings
   */
  async getNotificationSettings(): Promise<PushNotificationSettings> {
    try {
      const response = await apiClient.get('/mobile/notification-settings');
      return response.data;
    } catch (error) {
      console.error('[MobileExperienceService] Get notification settings failed:', error);
      throw error;
    }
  }

  /**
   * Update push notification settings
   *
   * BUSINESS LOGIC:
   * Updates user's push notification preferences.
   * Affects which notifications user receives.
   *
   * @param settings - Updated notification settings
   * @returns Updated settings
   */
  async updateNotificationSettings(
    settings: Partial<PushNotificationSettings>
  ): Promise<PushNotificationSettings> {
    try {
      const response = await apiClient.put('/mobile/notification-settings', settings);
      return response.data;
    } catch (error) {
      console.error('[MobileExperienceService] Update notification settings failed:', error);
      throw error;
    }
  }

  /**
   * Request push notification permission
   *
   * BUSINESS LOGIC:
   * Requests browser permission for push notifications.
   * Registers service worker and creates push subscription.
   *
   * @returns Push subscription or null if denied
   */
  async requestPushPermission(): Promise<PushSubscription | null> {
    try {
      // Check if notifications are supported
      if (!('Notification' in window)) {
        console.warn('[MobileExperienceService] Notifications not supported');
        return null;
      }

      // Request permission
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        console.warn('[MobileExperienceService] Notification permission denied');
        return null;
      }

      // Get service worker registration
      const registration = await navigator.serviceWorker.ready;

      // Subscribe to push notifications
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(
          import.meta.env.VITE_VAPID_PUBLIC_KEY || ''
        ),
      });

      // Send subscription to backend
      await this.savePushSubscription(subscription);

      return subscription;
    } catch (error) {
      console.error('[MobileExperienceService] Request push permission failed:', error);
      throw error;
    }
  }

  /**
   * Save push subscription to backend
   *
   * BUSINESS LOGIC:
   * Stores push subscription details in backend for sending notifications.
   *
   * @param subscription - Push subscription object
   */
  private async savePushSubscription(subscription: PushSubscription): Promise<void> {
    try {
      const subscriptionJson = subscription.toJSON();
      await apiClient.post('/mobile/push-subscription', {
        endpoint: subscriptionJson.endpoint,
        keys: subscriptionJson.keys,
        device_id: this.deviceId,
      });
    } catch (error) {
      console.error('[MobileExperienceService] Save push subscription failed:', error);
      throw error;
    }
  }

  /**
   * Convert VAPID key to Uint8Array
   *
   * TECHNICAL IMPLEMENTATION:
   * Converts base64 VAPID public key to Uint8Array format required by Push API.
   */
  private urlBase64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  // ============================================================================
  // SERVICE WORKER
  // ============================================================================

  /**
   * Register service worker
   *
   * BUSINESS LOGIC:
   * Registers service worker for offline functionality and push notifications.
   * Called during app initialization.
   */
  private async registerServiceWorker(): Promise<void> {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js');
      console.log('[MobileExperienceService] Service worker registered:', registration);

      // Listen for service worker updates
      registration.addEventListener('updatefound', () => {
        console.log('[MobileExperienceService] Service worker update found');
      });
    } catch (error) {
      console.error('[MobileExperienceService] Service worker registration failed:', error);
    }
  }

  /**
   * Unregister service worker
   *
   * BUSINESS LOGIC:
   * Removes service worker registration.
   * Used when user disables offline mode.
   */
  async unregisterServiceWorker(): Promise<void> {
    try {
      const registrations = await navigator.serviceWorker.getRegistrations();
      for (const registration of registrations) {
        await registration.unregister();
      }
      console.log('[MobileExperienceService] Service worker unregistered');
    } catch (error) {
      console.error('[MobileExperienceService] Service worker unregister failed:', error);
    }
  }

  // ============================================================================
  // BANDWIDTH TRACKING
  // ============================================================================

  /**
   * Get bandwidth usage
   *
   * BUSINESS LOGIC:
   * Retrieves user's bandwidth usage for current month.
   * Used to display data usage statistics.
   *
   * @param startDate - Start date for usage query
   * @param endDate - End date for usage query
   * @returns List of bandwidth usage records
   */
  async getBandwidthUsage(startDate: string, endDate: string): Promise<BandwidthUsage[]> {
    try {
      const response = await apiClient.get('/mobile/bandwidth-usage', {
        params: { start_date: startDate, end_date: endDate },
      });
      return response.data;
    } catch (error) {
      console.error('[MobileExperienceService] Get bandwidth usage failed:', error);
      throw error;
    }
  }

  /**
   * Track bandwidth usage
   *
   * BUSINESS LOGIC:
   * Records bandwidth usage for analytics.
   * Called after content downloads or API calls.
   *
   * @param usageData - Bandwidth usage data
   */
  async trackBandwidthUsage(
    usageData: Partial<BandwidthUsage>
  ): Promise<void> {
    try {
      await apiClient.post('/mobile/bandwidth-usage', {
        device_id: this.deviceId,
        ...usageData,
      });
    } catch (error) {
      console.error('[MobileExperienceService] Track bandwidth usage failed:', error);
      // Don't throw - bandwidth tracking is non-critical
    }
  }

  // ============================================================================
  // UTILITY METHODS
  // ============================================================================

  /**
   * Check if device is online
   *
   * WHY THIS APPROACH:
   * Uses navigator.onLine with event listeners for real-time status.
   *
   * @returns True if online, false if offline
   */
  isOnline(): boolean {
    return navigator.onLine;
  }

  /**
   * Get current device ID
   *
   * @returns Device ID string or null if not initialized
   */
  getDeviceId(): string | null {
    return this.deviceId;
  }

  /**
   * Check if on metered connection
   *
   * BUSINESS LOGIC:
   * Detects if user is on cellular/metered connection.
   * Used to adjust content quality and disable auto-downloads.
   *
   * @returns True if metered, false otherwise
   */
  isMeteredConnection(): boolean {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      return connection.saveData || connection.type === 'cellular';
    }
    return false;
  }

  /**
   * Vibrate device
   *
   * BUSINESS LOGIC:
   * Provides haptic feedback for user interactions.
   * Used for touch feedback and notifications.
   *
   * @param pattern - Vibration pattern in milliseconds
   */
  vibrate(pattern: number | number[]): void {
    if ('vibrate' in navigator) {
      navigator.vibrate(pattern);
    }
  }
}

// Export singleton instance
export const mobileExperienceService = new MobileExperienceService();
