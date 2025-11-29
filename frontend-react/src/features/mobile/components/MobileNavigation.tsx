/**
 * Mobile Navigation Component
 *
 * BUSINESS CONTEXT:
 * Provides touch-friendly bottom navigation for mobile devices.
 * Displays primary navigation items with icons and labels.
 *
 * TECHNICAL IMPLEMENTATION:
 * Responsive navigation that switches between bottom tabs (mobile)
 * and sidebar (desktop) based on screen size.
 */

import React from 'react';
import { NavLink } from 'react-router-dom';
import { useDeviceCapabilities } from '../hooks/useDeviceCapabilities';
import styles from './MobileNavigation.module.css';

export interface NavigationItem {
  label: string;
  icon: string;
  path: string;
  badge?: number;
}

export interface MobileNavigationProps {
  items: NavigationItem[];
  position?: 'bottom' | 'top';
}

/**
 * Mobile Navigation Component
 *
 * WHY THIS APPROACH:
 * - Touch-friendly bottom tabs for mobile
 * - Clear visual hierarchy
 * - Badge support for notifications
 * - Smooth transitions
 */
export const MobileNavigation: React.FC<MobileNavigationProps> = ({
  items,
  position = 'bottom',
}) => {
  const { isMobile, vibrate } = useDeviceCapabilities();

  const handleClick = () => {
    vibrate(10); // Haptic feedback on navigation
  };

  if (!isMobile) {
    return null; // Only show on mobile
  }

  return (
    <nav className={`${styles.mobileNavigation} ${styles[position]}`} role="navigation">
      <ul className={styles.navList}>
        {items.map((item) => (
          <li key={item.path} className={styles.navItem}>
            <NavLink
              to={item.path}
              className={({ isActive }) =>
                `${styles.navLink} ${isActive ? styles.active : ''}`
              }
              onClick={handleClick}
            >
              <span className={styles.icon} aria-hidden="true">
                {item.icon}
              </span>
              <span className={styles.label}>{item.label}</span>
              {item.badge && item.badge > 0 && (
                <span className={styles.badge} aria-label={`${item.badge} notifications`}>
                  {item.badge > 99 ? '99+' : item.badge}
                </span>
              )}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
};
