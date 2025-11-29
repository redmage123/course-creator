/**
 * Mobile Experience Module
 *
 * BUSINESS CONTEXT:
 * Provides comprehensive mobile experience features for the Course Creator Platform
 * including offline sync, push notifications, device capability detection,
 * and mobile-optimized UI components.
 *
 * TECHNICAL IMPLEMENTATION:
 * Exports hooks, components, and utilities for building mobile-first
 * responsive experiences with offline support and native-like interactions.
 *
 * FEATURES:
 * - Offline content synchronization
 * - Push notification management
 * - Device capability detection
 * - Touch-friendly UI components
 * - Mobile-optimized layouts
 * - Swipe gestures
 * - Pull-to-refresh
 * - Responsive navigation
 */

// ============================================================================
// HOOKS
// ============================================================================

export { useMobileExperience } from './hooks/useMobileExperience';
export { useOfflineSync } from './hooks/useOfflineSync';
export { useDeviceCapabilities } from './hooks/useDeviceCapabilities';

// ============================================================================
// COMPONENTS
// ============================================================================

export { OfflineIndicator } from './components/OfflineIndicator';
export type { OfflineIndicatorProps } from './components/OfflineIndicator';

export { SyncStatusWidget } from './components/SyncStatusWidget';
export type { SyncStatusWidgetProps } from './components/SyncStatusWidget';

export { MobileNavigation } from './components/MobileNavigation';
export type { MobileNavigationProps, NavigationItem } from './components/MobileNavigation';

export { SwipeableCard } from './components/SwipeableCard';
export type { SwipeableCardProps, SwipeAction } from './components/SwipeableCard';

export { PullToRefresh } from './components/PullToRefresh';
export type { PullToRefreshProps } from './components/PullToRefresh';

// ============================================================================
// LAYOUT
// ============================================================================

export { MobileOptimizedLayout } from './MobileOptimizedLayout';
export type { MobileOptimizedLayoutProps } from './MobileOptimizedLayout';

// ============================================================================
// SERVICES & TYPES
// ============================================================================

export {
  mobileExperienceService,
  DeviceType,
  Theme,
  FontSize,
  NavigationType,
  VideoQuality,
  ImageQuality,
  ConnectionType,
  SyncStatus,
  ContentType,
  NotificationCategory,
} from '@services/mobileExperienceService';

export type {
  UserDevicePreference,
  OfflineContentSync,
  PushNotificationSettings,
  DeviceCapabilities,
  BandwidthUsage,
} from '@services/mobileExperienceService';
