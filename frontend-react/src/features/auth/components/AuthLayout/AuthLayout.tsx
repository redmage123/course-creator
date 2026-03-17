/**
 * Authentication Layout Component
 *
 * BUSINESS CONTEXT:
 * Shared layout wrapper for all authentication pages (Login, Registration, Password Reset).
 * Provides consistent branding, layout, and responsive behavior across auth flows.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Gradient background with centered card layout
 * - Responsive design (mobile/desktop)
 * - Optional header with title/subtitle
 * - Customizable container width
 * - Accessible structure with semantic HTML
 *
 * DESIGN PRINCIPLES:
 * - Tami design system colors and spacing
 * - Platform blue (#2563eb) for accents
 * - 8px border radius standard
 * - Smooth transitions and animations
 */

import React from 'react';
import { Heading } from '../../../../components/atoms/Heading';
import styles from './AuthLayout.module.css';

export interface AuthLayoutProps {
  /**
   * Page content (form, success state, etc.)
   */
  children: React.ReactNode;

  /**
   * Optional page title
   */
  title?: string;

  /**
   * Optional page subtitle/description
   */
  subtitle?: string;

  /**
   * Maximum width of content container
   * @default '480px'
   */
  maxWidth?: '480px' | '520px' | '600px';

  /**
   * Additional CSS class name
   */
  className?: string;
}

/**
 * Authentication Layout Component
 *
 * WHY THIS APPROACH:
 * - Extracts common auth page structure for DRY principle
 * - Provides consistent UX across all auth flows
 * - Responsive by default with mobile-first approach
 * - Flexible enough to support different auth page needs
 *
 * @example
 * ```tsx
 * <AuthLayout title="Sign In" subtitle="Welcome back!">
 *   <LoginForm />
 * </AuthLayout>
 * ```
 */
export const AuthLayout: React.FC<AuthLayoutProps> = ({
  children,
  title,
  subtitle,
  maxWidth = '480px',
  className,
}) => {
  return (
    <div className={`${styles['auth-layout']} ${className || ''}`}>
      <div
        className={styles['auth-container']}
        style={{ maxWidth }}
      >
        {/* Optional Header */}
        {(title || subtitle) && (
          <div className={styles['auth-header']}>
            {title && (
              <Heading level="h1" align="center" gutterBottom={false}>
                {title}
              </Heading>
            )}
            {subtitle && (
              <p className={styles['auth-subtitle']}>
                {subtitle}
              </p>
            )}
          </div>
        )}

        {/* Page Content */}
        {children}
      </div>
    </div>
  );
};
