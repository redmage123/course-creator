/**
 * Toast Component - Tami Design System
 *
 * BUSINESS CONTEXT:
 * Notification component for user feedback across the platform.
 * Used for success confirmations, error messages, warnings, and info alerts.
 *
 * TECHNICAL IMPLEMENTATION:
 * React Portal-based toast with auto-dismiss, stacking, and animations.
 * Includes accessibility features (ARIA live regions, keyboard dismissal).
 *
 * DESIGN PRINCIPLES:
 * - Color-coded variants (success green, error red, warning orange, info blue)
 * - 8px border radius
 * - Slide-in animation from top-right
 * - Auto-dismiss after 5 seconds (configurable)
 * - WCAG 2.1 AA+ compliant
 */

import React, { useEffect, useState, ReactNode } from 'react';
import { createPortal } from 'react-dom';
import styles from './Toast.module.css';

export type ToastVariant = 'success' | 'error' | 'warning' | 'info';
export type ToastPosition = 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';

export interface ToastProps {
  /**
   * Toast message
   */
  message: string;

  /**
   * Toast variant
   * - success: Green - successful actions
   * - error: Red - errors and failures
   * - warning: Orange - warnings and cautions
   * - info: Blue - informational messages
   */
  variant?: ToastVariant;

  /**
   * Auto-dismiss duration in milliseconds
   * Set to 0 to disable auto-dismiss
   * @default 5000
   */
  duration?: number;

  /**
   * Callback when toast is dismissed
   */
  onDismiss?: () => void;

  /**
   * Show close button
   * @default true
   */
  showCloseButton?: boolean;

  /**
   * Toast position
   * @default "top-right"
   */
  position?: ToastPosition;

  /**
   * Custom icon (overrides default variant icon)
   */
  icon?: ReactNode;

  /**
   * Custom className
   */
  className?: string;
}

/**
 * Toast Component
 *
 * WHY THIS APPROACH:
 * - React Portal renders outside DOM hierarchy (z-index independence)
 * - Auto-dismiss with configurable duration
 * - Accessible with ARIA live regions
 * - Slide-in animation for smooth UX
 * - Color-coded variants for quick recognition
 *
 * @example
 * ```tsx
 * // Success toast
 * <Toast message="Course created successfully!" variant="success" />
 *
 * // Error toast with no auto-dismiss
 * <Toast
 *   message="Failed to save changes"
 *   variant="error"
 *   duration={0}
 * />
 *
 * // Info toast with custom position
 * <Toast
 *   message="New features available"
 *   variant="info"
 *   position="bottom-center"
 * />
 *
 * // Warning toast with callback
 * <Toast
 *   message="Session expiring soon"
 *   variant="warning"
 *   onDismiss={handleDismiss}
 * />
 * ```
 */
export const Toast: React.FC<ToastProps> = ({
  message,
  variant = 'info',
  duration = 5000,
  onDismiss,
  showCloseButton = true,
  position = 'top-right',
  icon,
  className,
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isExiting, setIsExiting] = useState(false);

  // Auto-dismiss timer
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        handleDismiss();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [duration]);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => {
      setIsVisible(false);
      onDismiss?.();
    }, 300); // Match animation duration
  };

  // ESC key handling
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        handleDismiss();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  if (!isVisible) return null;

  const toastClasses = [
    styles.toast,
    styles[`toast-${variant}`],
    styles[`toast-${position}`],
    isExiting && styles['toast-exiting'],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  // Default icons for each variant
  const defaultIcons: Record<ToastVariant, ReactNode> = {
    success: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path
          d="M16.667 5L7.5 14.167L3.333 10"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
    error: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path
          d="M10 6v4m0 4h.01M19 10c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
    ),
    warning: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path
          d="M10 7v4m0 4h.01M8.5 2.5l-7 12.5h14l-7-12.5z"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
    info: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="2" />
        <path
          d="M10 10v4m0-8h.01"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
    ),
  };

  const displayIcon = icon || defaultIcons[variant];

  const toastContent = (
    <div
      className={toastClasses}
      role="alert"
      aria-live={variant === 'error' ? 'assertive' : 'polite'}
      aria-atomic="true"
    >
      {/* Icon */}
      <div className={styles['toast-icon']} aria-hidden="true">
        {displayIcon}
      </div>

      {/* Message */}
      <div className={styles['toast-message']}>{message}</div>

      {/* Close button */}
      {showCloseButton && (
        <button
          className={styles['toast-close']}
          onClick={handleDismiss}
          aria-label="Dismiss notification"
          type="button"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M12 4L4 12M4 4l8 8"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </button>
      )}

      {/* Progress bar for auto-dismiss */}
      {duration > 0 && (
        <div
          className={styles['toast-progress']}
          style={{
            animationDuration: `${duration}ms`,
          }}
        />
      )}
    </div>
  );

  // Render in portal
  return createPortal(toastContent, document.body);
};

Toast.displayName = 'Toast';
