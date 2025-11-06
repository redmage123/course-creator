/**
 * Input Component - Tami Design System
 *
 * BUSINESS CONTEXT:
 * Primary text input component for form data collection across all user roles.
 * Provides consistent input styling with validation states for better UX.
 *
 * TECHNICAL IMPLEMENTATION:
 * React component implementing Tami input design with full accessibility support.
 * Includes validation states, helper text, labels, and various input types.
 *
 * DESIGN PRINCIPLES:
 * - Uses platform blue (#2563eb) for focus states
 * - 8px border radius (design system standard)
 * - Clear visual feedback for validation states
 * - WCAG 2.1 AA+ compliant
 * - Proper label association for screen readers
 */

import React, { InputHTMLAttributes, ReactNode, forwardRef } from 'react';
import styles from './Input.module.css';

export type InputVariant = 'default' | 'success' | 'error' | 'warning';
export type InputSize = 'small' | 'medium' | 'large';

export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  /**
   * Input validation state
   * - default: Normal state
   * - success: Valid input
   * - error: Invalid input
   * - warning: Warning state
   */
  variant?: InputVariant;

  /**
   * Input size
   * - small: Compact (32px height)
   * - medium: Default (44px height)
   * - large: Emphasized (52px height)
   */
  size?: InputSize;

  /**
   * Label text displayed above input
   */
  label?: string;

  /**
   * Helper text displayed below input
   * Used for instructions or error messages
   */
  helperText?: string;

  /**
   * Error message (convenience prop)
   * Automatically sets variant="error" and helperText={error}
   * If provided, overrides variant and helperText props
   */
  error?: string;

  /**
   * Icon to display before input text
   */
  leftIcon?: ReactNode;

  /**
   * Icon to display after input text
   */
  rightIcon?: ReactNode;

  /**
   * Full width input (100% of container)
   */
  fullWidth?: boolean;

  /**
   * Required field indicator
   */
  required?: boolean;

  /**
   * Custom container className
   */
  containerClassName?: string;
}

/**
 * Input Component
 *
 * WHY THIS APPROACH:
 * - CSS Modules prevent style conflicts
 * - TypeScript ensures type safety
 * - Extends native input props for full HTML support
 * - Forwards ref for form libraries (React Hook Form, Formik)
 * - Accessible by default (ARIA attributes, label association)
 * - Validation states provide clear visual feedback
 *
 * @example
 * ```tsx
 * // Basic input with label
 * <Input label="Email" type="email" placeholder="you@example.com" />
 *
 * // Input with error state
 * <Input
 *   label="Password"
 *   type="password"
 *   variant="error"
 *   helperText="Password must be at least 8 characters"
 * />
 *
 * // Input with icon
 * <Input
 *   label="Search"
 *   leftIcon={<SearchIcon />}
 *   placeholder="Search courses..."
 * />
 *
 * // Required field
 * <Input
 *   label="Username"
 *   required
 *   helperText="Choose a unique username"
 * />
 * ```
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      variant = 'default',
      size = 'medium',
      label,
      helperText,
      error,
      leftIcon,
      rightIcon,
      fullWidth = false,
      required = false,
      disabled,
      className,
      containerClassName,
      id,
      type = 'text',
      'aria-describedby': ariaDescribedBy,
      ...props
    },
    ref
  ) => {
    // If error prop is provided, override variant and helperText
    const effectiveVariant = error ? 'error' : variant;
    const effectiveHelperText = error || helperText;

    // Generate unique IDs for accessibility
    const inputId = id || `input-${React.useId()}`;
    const helperTextId = effectiveHelperText ? `${inputId}-helper` : undefined;
    const describedBy = [ariaDescribedBy, helperTextId].filter(Boolean).join(' ') || undefined;

    // Combine input class names
    const inputClasses = [
      styles.input,
      styles[`input-${effectiveVariant}`],
      styles[`input-${size}`],
      leftIcon && styles['input-with-left-icon'],
      rightIcon && styles['input-with-right-icon'],
      disabled && styles['input-disabled'],
      className,
    ]
      .filter(Boolean)
      .join(' ');

    // Combine container class names
    const containerClasses = [
      styles['input-container'],
      fullWidth && styles['input-full-width'],
      containerClassName,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <div className={containerClasses}>
        {/* Label */}
        {label && (
          <label htmlFor={inputId} className={styles.label}>
            {label}
            {required && <span className={styles.required} aria-label="required">*</span>}
          </label>
        )}

        {/* Input wrapper (for icons) */}
        <div className={styles['input-wrapper']}>
          {/* Left icon */}
          {leftIcon && (
            <span className={styles['input-icon-left']} aria-hidden="true">
              {leftIcon}
            </span>
          )}

          {/* Input element */}
          <input
            ref={ref}
            id={inputId}
            type={type}
            className={inputClasses}
            disabled={disabled}
            required={required}
            aria-invalid={effectiveVariant === 'error'}
            aria-describedby={describedBy}
            {...props}
          />

          {/* Right icon */}
          {rightIcon && (
            <span className={styles['input-icon-right']} aria-hidden="true">
              {rightIcon}
            </span>
          )}
        </div>

        {/* Helper text */}
        {effectiveHelperText && (
          <span
            id={helperTextId}
            className={`${styles['helper-text']} ${styles[`helper-text-${effectiveVariant}`]}`}
            role={effectiveVariant === 'error' ? 'alert' : undefined}
          >
            {effectiveHelperText}
          </span>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
