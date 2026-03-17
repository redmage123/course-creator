/**
 * Checkbox Component - Tami Design System
 *
 * BUSINESS CONTEXT:
 * Checkbox input component for forms and selections across the platform.
 * Used for terms acceptance, feature toggles, multi-select lists, etc.
 *
 * TECHNICAL IMPLEMENTATION:
 * Custom checkbox with indeterminate state and group support.
 * Supports controlled/uncontrolled modes with full accessibility.
 *
 * DESIGN PRINCIPLES:
 * - Platform blue (#2563eb) for checked states
 * - Indeterminate state for partial selections
 * - 4px border radius for checkbox shape
 * - WCAG 2.1 AA+ compliant
 */

import React, { forwardRef, useEffect, useRef } from 'react';
import styles from './Checkbox.module.css';

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size' | 'type'> {
  /**
   * Label for the checkbox (can be string or React element for links)
   */
  label?: React.ReactNode;

  /**
   * Helper text below checkbox
   */
  helperText?: string;

  /**
   * Error message (shows error state)
   */
  error?: string;

  /**
   * Indeterminate state (for "select all" functionality)
   * @default false
   */
  indeterminate?: boolean;

  /**
   * Size variant
   * @default "medium"
   */
  size?: 'small' | 'medium' | 'large';

  /**
   * Custom className
   */
  className?: string;
}

/**
 * Checkbox Component
 *
 * WHY THIS APPROACH:
 * - Custom styling for consistent design across browsers
 * - Indeterminate state for partial selections in groups
 * - forwardRef enables integration with form libraries
 * - Controlled/uncontrolled modes for flexibility
 * - Full keyboard navigation and accessibility
 *
 * @example
 * ```tsx
 * // Basic checkbox
 * <Checkbox
 *   label="I accept the terms and conditions"
 *   required
 * />
 *
 * // Controlled with validation
 * <Checkbox
 *   label="Enable notifications"
 *   checked={notificationsEnabled}
 *   onChange={(e) => setNotificationsEnabled(e.target.checked)}
 *   error={validationError}
 * />
 *
 * // Indeterminate state (for "select all")
 * <Checkbox
 *   label="Select all"
 *   checked={allSelected}
 *   indeterminate={someSelected}
 *   onChange={handleSelectAll}
 * />
 * ```
 */
export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(({
  label,
  helperText,
  error,
  indeterminate = false,
  size = 'medium',
  className,
  disabled,
  id,
  ...rest
}, ref) => {
  const inputRef = useRef<HTMLInputElement>(null);

  // Handle ref forwarding
  useEffect(() => {
    if (ref && inputRef.current) {
      if (typeof ref === 'function') {
        ref(inputRef.current);
      } else {
        ref.current = inputRef.current;
      }
    }
  }, [ref]);

  // Set indeterminate property (not controllable via HTML attribute)
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.indeterminate = indeterminate;
    }
  }, [indeterminate]);

  // Generate unique ID if not provided
  const checkboxId = id || `checkbox-${Math.random().toString(36).substr(2, 9)}`;

  // Build container classes
  const containerClasses = [
    styles['checkbox-container'],
    styles[`checkbox-${size}`],
    error && styles['checkbox-error'],
    disabled && styles['checkbox-disabled'],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={containerClasses}>
      <div className={styles['checkbox-wrapper']}>
        {/* Hidden native checkbox */}
        <input
          ref={inputRef}
          type="checkbox"
          id={checkboxId}
          className={styles['checkbox-input']}
          disabled={disabled}
          aria-invalid={!!error}
          aria-describedby={error || helperText ? `${checkboxId}-message` : undefined}
          {...rest}
        />

        {/* Custom checkbox visual */}
        <label htmlFor={checkboxId} className={styles['checkbox-label-wrapper']}>
          <span className={styles['checkbox-custom']}>
            {/* Checkmark icon */}
            <svg
              className={styles['checkbox-icon']}
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M13.333 4L6 11.333L2.667 8"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>

            {/* Indeterminate dash icon */}
            <svg
              className={styles['checkbox-indeterminate-icon']}
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M3 8H13"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </span>

          {/* Label text */}
          {label && <span className={styles['checkbox-label']}>{label}</span>}
        </label>
      </div>

      {/* Helper text or error message */}
      {(helperText || error) && (
        <div id={`${checkboxId}-message`} className={styles['checkbox-message']}>
          {error ? (
            <span className={styles['checkbox-error-text']} role="alert">{error}</span>
          ) : (
            <span className={styles['checkbox-helper-text']}>{helperText}</span>
          )}
        </div>
      )}
    </div>
  );
});

Checkbox.displayName = 'Checkbox';
