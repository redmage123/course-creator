/**
 * Dashboard Layout Component
 *
 * BUSINESS CONTEXT:
 * Shared layout template for all dashboard pages in Course Creator Platform.
 * Provides consistent structure with navigation, content area, and responsive design.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Navbar at top for navigation
 * - Main content area with consistent padding
 * - Optional sidebar for additional navigation
 * - Responsive layout for mobile/desktop
 * - Accessible page structure
 *
 * DESIGN PRINCIPLES:
 * - Clean, spacious layout
 * - Consistent padding and spacing
 * - Responsive design
 * - Accessibility with semantic HTML
 */

import React from 'react';
import { Navbar } from '../../organisms/Navbar';
import styles from './DashboardLayout.module.css';

export interface DashboardLayoutProps {
  /**
   * Page content to render in main area
   */
  children: React.ReactNode;

  /**
   * Optional sidebar content
   */
  sidebar?: React.ReactNode;

  /**
   * Maximum width of content area
   * @default '1440px'
   */
  maxWidth?: string;

  /**
   * Custom navbar logo
   */
  logo?: string | React.ReactNode;

  /**
   * Additional CSS class name
   */
  className?: string;
}

/**
 * Dashboard Layout Component
 *
 * WHY THIS APPROACH:
 * - Centralized layout reduces duplication across dashboard pages
 * - Navbar integration ensures consistent navigation
 * - Flexible sidebar for role-specific navigation
 * - Responsive design works on all screen sizes
 * - Semantic HTML for accessibility
 *
 * @example
 * ```tsx
 * <DashboardLayout>
 *   <h1>My Dashboard</h1>
 *   <p>Dashboard content...</p>
 * </DashboardLayout>
 * ```
 *
 * @example With sidebar
 * ```tsx
 * <DashboardLayout sidebar={<CourseSidebar />}>
 *   <CourseContent />
 * </DashboardLayout>
 * ```
 */
export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  sidebar,
  maxWidth = '1440px',
  logo,
  className,
}) => {
  return (
    <div className={`${styles['dashboard-layout']} ${className || ''}`}>
      {/* Navigation Bar */}
      <Navbar logo={logo} />

      {/* Main Content Area */}
      <div className={styles['dashboard-container']}>
        <main
          className={styles['dashboard-main']}
          style={{ maxWidth }}
        >
          {sidebar ? (
            <div className={styles['dashboard-with-sidebar']}>
              {/* Sidebar */}
              <aside className={styles['dashboard-sidebar']}>
                {sidebar}
              </aside>

              {/* Content */}
              <div className={styles['dashboard-content']}>
                {children}
              </div>
            </div>
          ) : (
            // Content without sidebar
            children
          )}
        </main>
      </div>
    </div>
  );
};
