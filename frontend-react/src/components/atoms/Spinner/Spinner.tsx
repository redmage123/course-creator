/**
 * Spinner Component - Tami Design System
 *
 * BUSINESS CONTEXT:
 * Loading indicator for async operations across the platform.
 * Used during API calls, page loads, and content generation.
 *
 * TECHNICAL IMPLEMENTATION:
 * Animated SVG spinner with multiple sizes and color variants.
 * Includes accessibility features (ARIA labels, reduced motion support).
 *
 * DESIGN PRINCIPLES:
 * - Uses platform blue (#2563eb) by default
 * - Smooth 0.8s rotation animation
 * - Three sizes (small, medium, large)
 * - Centered by default with optional inline placement
 * - WCAG 2.1 AA+ compliant
 */

import React, { HTMLAttributes } from 'react';
import styles from './Spinner.module.css';

export type SpinnerSize = 'small' | 'medium' | 'large';
export type SpinnerColor = 'primary' | 'secondary' | 'white';

export interface SpinnerProps extends Omit<HTMLAttributes<HTMLDivElement>, 'color'> {
  /**
   * Spinner size
   * - small: 20px (inline usage)
   * - medium: 40px (default)
   * - large: 60px (full-page loading)
   */
  size?: SpinnerSize;

  /**
   * Spinner color variant
   * - primary: Platform blue (#2563eb)
   * - secondary: Gray (#64748b)
   * - white: White (#ffffff) for dark backgrounds
   */
  color?: SpinnerColor;

  /**
   * Center spinner in container
   * @default true
   */
  centered?: boolean;

  /**
   * Accessible label for screen readers
   * @default "Loading"
   */
  label?: string;
}

/**
 * Spinner Component
 *
 * WHY THIS APPROACH:
 * - SVG ensures crisp rendering at all sizes
 * - CSS animations provide smooth, performant rotation
 * - Accessible by default with ARIA live region
 * - Respects prefers-reduced-motion for accessibility
 *
 * @example
 * ```tsx
 * // Default spinner
 * <Spinner />
 *
 * // Small inline spinner
 * <Spinner size="small" centered={false} />
 *
 * // Large full-page spinner
 * <Spinner size="large" label="Loading courses..." />
 *
 * // White spinner on dark background
 * <Spinner color="white" />
 * ```
 */
export const Spinner: React.FC<SpinnerProps> = ({
  size = 'medium',
  color = 'primary',
  centered = true,
  label = 'Loading',
  className,
  ...props
}) => {
  const containerClasses = [
    styles['spinner-container'],
    centered && styles['spinner-centered'],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  const spinnerClasses = [
    styles.spinner,
    styles[`spinner-${size}`],
    styles[`spinner-${color}`],
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={containerClasses} role="status" aria-live="polite" {...props}>
      <svg
        className={spinnerClasses}
        viewBox="0 0 50 50"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <circle
          className={styles['spinner-circle']}
          cx="25"
          cy="25"
          r="20"
          fill="none"
          strokeWidth="4"
        />
      </svg>
      <span className={styles['spinner-label']}>{label}</span>
    </div>
  );
};

Spinner.displayName = 'Spinner';
