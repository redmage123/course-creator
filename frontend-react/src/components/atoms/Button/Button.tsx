/**
 * Button Component - Tami Design System
 *
 * BUSINESS CONTEXT:
 * Primary interaction point for user actions throughout the educational platform.
 * Provides consistent, accessible button styling for students, instructors, and admins.
 *
 * TECHNICAL IMPLEMENTATION:
 * React component implementing Tami button design with full accessibility support.
 * Includes variants, sizes, loading states, and keyboard navigation.
 *
 * DESIGN PRINCIPLES:
 * - Uses platform blue (#2563eb), not Tami purple/orange
 * - 8px border radius (design system standard)
 * - 2px hover lift for tactile feedback
 * - 200ms transitions for responsiveness
 * - WCAG 2.1 AA+ compliant
 */

import React, { ButtonHTMLAttributes, ReactNode } from 'react';
import styles from './Button.module.css';

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'success' | 'ghost' | 'text';
export type ButtonSize = 'small' | 'medium' | 'large';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * Button visual variant
   * - primary: Main actions (blue background)
   * - secondary: Less prominent actions (white background, blue border)
   * - danger: Destructive actions (red background)
   * - success: Positive actions (green background)
   * - ghost: Low priority (transparent background)
   */
  variant?: ButtonVariant;

  /**
   * Button size
   * - small: Compact (8px/16px padding)
   * - medium: Default (12px/24px padding)
   * - large: Emphasized (16px/32px padding)
   */
  size?: ButtonSize;

  /**
   * Loading state - shows spinner and disables interaction
   */
  loading?: boolean;

  /**
   * Full width button (100% of container)
   */
  fullWidth?: boolean;

  /**
   * Icon to display before text
   */
  leftIcon?: ReactNode;

  /**
   * Icon to display after text
   */
  rightIcon?: ReactNode;

  /**
   * Button content
   */
  children: ReactNode;
}

/**
 * Button Component
 *
 * WHY THIS APPROACH:
 * - CSS Modules prevent style conflicts
 * - TypeScript ensures type safety
 * - Extends native button props for full HTML support
 * - Forwards ref for advanced use cases
 * - Accessible by default (ARIA attributes, keyboard support)
 *
 * @example
 * ```tsx
 * // Primary button
 * <Button variant="primary">Create Course</Button>
 *
 * // With loading state
 * <Button variant="primary" loading>Saving...</Button>
 *
 * // With icon
 * <Button variant="secondary" leftIcon={<PlusIcon />}>Add Item</Button>
 *
 * // Danger action
 * <Button variant="danger" size="small">Delete</Button>
 * ```
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'medium',
      loading = false,
      fullWidth = false,
      leftIcon,
      rightIcon,
      disabled,
      className,
      children,
      type = 'button',
      ...props
    },
    ref
  ) => {
    // Combine class names
    const classes = [
      styles.btn,
      styles[`btn-${variant}`],
      styles[`btn-${size}`],
      loading && styles['btn-loading'],
      fullWidth && styles['btn-full-width'],
      className,
    ]
      .filter(Boolean)
      .join(' ');

    // Button is disabled when loading or explicitly disabled
    const isDisabled = loading || disabled;

    return (
      <button
        ref={ref}
        type={type}
        className={classes}
        disabled={isDisabled}
        aria-busy={loading}
        {...props}
      >
        {/* Loading spinner */}
        {loading && (
          <span className={styles['btn-spinner']} aria-hidden="true">
            <span className={styles['spinner-circle']} />
          </span>
        )}

        {/* Left icon */}
        {leftIcon && !loading && (
          <span className={styles['btn-icon-left']} aria-hidden="true">
            {leftIcon}
          </span>
        )}

        {/* Button text - keep visible for accessibility even when loading */}
        <span>
          {children}
        </span>

        {/* Right icon */}
        {rightIcon && !loading && (
          <span className={styles['btn-icon-right']} aria-hidden="true">
            {rightIcon}
          </span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
