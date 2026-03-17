/**
 * Mobile Optimized Layout Component
 *
 * BUSINESS CONTEXT:
 * Provides responsive, mobile-first layout for the Course Creator Platform.
 * Adapts UI based on device type, screen size, and user preferences.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses CSS Grid and Flexbox for responsive layouts.
 * Integrates with mobile experience hooks for device-specific optimizations.
 */

import React from 'react';
import { useMobileExperience } from './hooks/useMobileExperience';
import { useDeviceCapabilities } from './hooks/useDeviceCapabilities';
import { OfflineIndicator } from './components/OfflineIndicator';
import { NavigationItem, MobileNavigation } from './components/MobileNavigation';
import styles from './MobileOptimizedLayout.module.css';

export interface MobileOptimizedLayoutProps {
  /**
   * Page content
   */
  children: React.ReactNode;

  /**
   * Navigation items for mobile bottom nav
   */
  navigationItems?: NavigationItem[];

  /**
   * Header content
   */
  header?: React.ReactNode;

  /**
   * Footer content
   */
  footer?: React.ReactNode;

  /**
   * Whether to show offline indicator
   * @default true
   */
  showOfflineIndicator?: boolean;

  /**
   * Whether to enable safe area insets (notch/home indicator)
   * @default true
   */
  enableSafeArea?: boolean;

  /**
   * Custom class name
   */
  className?: string;
}

/**
 * Mobile Optimized Layout Component
 *
 * WHY THIS APPROACH:
 * - Mobile-first responsive design
 * - Automatic device-specific optimizations
 * - Safe area support for notched devices
 * - Flexible content areas
 * - Optional bottom navigation
 *
 * @param props - Component props
 */
export const MobileOptimizedLayout: React.FC<MobileOptimizedLayoutProps> = ({
  children,
  navigationItems,
  header,
  footer,
  showOfflineIndicator = true,
  enableSafeArea = true,
  className = '',
}) => {
  const {
    isMobile,
    isTablet,
    devicePreferences,
  } = useMobileExperience();

  const { isOnline } = useDeviceCapabilities();

  // Determine layout mode
  const layoutMode = isMobile ? 'mobile' : isTablet ? 'tablet' : 'desktop';

  // Apply safe area class
  const safeAreaClass = enableSafeArea ? styles.safeArea : '';

  // Apply compact mode if enabled
  const compactClass = devicePreferences?.compact_mode ? styles.compact : '';

  // Combined class names
  const layoutClass = [
    styles.mobileOptimizedLayout,
    styles[layoutMode],
    safeAreaClass,
    compactClass,
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={layoutClass}>
      {/* Offline indicator */}
      {showOfflineIndicator && !isOnline && (
        <OfflineIndicator position="top" />
      )}

      {/* Header */}
      {header && (
        <header className={styles.header}>
          {header}
        </header>
      )}

      {/* Main content */}
      <main className={styles.main}>
        {children}
      </main>

      {/* Footer */}
      {footer && (
        <footer className={styles.footer}>
          {footer}
        </footer>
      )}

      {/* Mobile navigation */}
      {navigationItems && navigationItems.length > 0 && (
        <MobileNavigation items={navigationItems} position="bottom" />
      )}
    </div>
  );
};
