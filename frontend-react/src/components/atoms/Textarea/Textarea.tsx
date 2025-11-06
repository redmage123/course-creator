/**
 * Textarea Component - Tami Design System
 *
 * BUSINESS CONTEXT:
 * Multi-line text input component for forms across the platform.
 * Used for course descriptions, feedback, comments, and long-form content.
 *
 * TECHNICAL IMPLEMENTATION:
 * Auto-resize textarea with character counting and validation states.
 * Supports controlled/uncontrolled modes with full accessibility.
 *
 * DESIGN PRINCIPLES:
 * - Platform blue (#2563eb) for focus states
 * - 8px border radius
 * - Auto-resize with min/max constraints
 * - Character counter with warning states
 * - WCAG 2.1 AA+ compliant
 */

import React, { forwardRef, useEffect, useRef, useState, ChangeEvent } from 'react';
import styles from './Textarea.module.css';

export type TextareaResize = 'none' | 'vertical' | 'both';

export interface TextareaProps extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, 'size'> {
  /**
   * Label for the textarea
   */
  label?: string;

  /**
   * Helper text below textarea
   */
  helperText?: string;

  /**
   * Error message (shows error state)
   */
  error?: string;

  /**
   * Success message (shows success state)
   */
  success?: string;

  /**
   * Warning message (shows warning state)
   */
  warning?: string;

  /**
   * Required field indicator
   */
  required?: boolean;

  /**
   * Enable auto-resize
   * @default true
   */
  autoResize?: boolean;

  /**
   * Minimum number of rows
   * @default 3
   */
  minRows?: number;

  /**
   * Maximum number of rows
   * @default 10
   */
  maxRows?: number;

  /**
   * Show character counter
   * @default false
   */
  showCharacterCount?: boolean;

  /**
   * Resize behavior
   * @default "vertical"
   */
  resize?: TextareaResize;

  /**
   * Custom className
   */
  className?: string;
}

/**
 * Textarea Component
 *
 * WHY THIS APPROACH:
 * - Auto-resize improves UX by expanding as user types
 * - Character counter helps users stay within limits
 * - Validation states provide immediate feedback
 * - forwardRef enables integration with form libraries
 * - Controlled/uncontrolled modes for flexibility
 *
 * @example
 * ```tsx
 * // Basic textarea
 * <Textarea
 *   label="Description"
 *   placeholder="Enter course description..."
 *   maxLength={500}
 *   showCharacterCount
 * />
 *
 * // Controlled with validation
 * <Textarea
 *   label="Feedback"
 *   value={feedback}
 *   onChange={(e) => setFeedback(e.target.value)}
 *   error={feedbackError}
 *   required
 * />
 *
 * // Auto-resize with constraints
 * <Textarea
 *   label="Comment"
 *   autoResize
 *   minRows={2}
 *   maxRows={8}
 *   placeholder="Add your comment..."
 * />
 * ```
 */
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({
  label,
  helperText,
  error,
  success,
  warning,
  required = false,
  autoResize = true,
  minRows = 3,
  maxRows = 10,
  showCharacterCount = false,
  resize = 'vertical',
  className,
  value,
  defaultValue,
  onChange,
  maxLength,
  id,
  disabled,
  ...rest
}, ref) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [charCount, setCharCount] = useState(0);

  // Handle ref forwarding
  useEffect(() => {
    if (ref && textareaRef.current) {
      if (typeof ref === 'function') {
        ref(textareaRef.current);
      } else {
        ref.current = textareaRef.current;
      }
    }
  }, [ref]);

  // Auto-resize functionality
  const adjustHeight = () => {
    if (!autoResize || !textareaRef.current) return;

    const textarea = textareaRef.current;
    const lineHeight = parseInt(getComputedStyle(textarea).lineHeight) || 24;
    const minHeight = minRows * lineHeight;
    const maxHeight = maxRows * lineHeight;

    // Reset height to auto to get correct scrollHeight
    textarea.style.height = 'auto';

    // Calculate new height
    const newHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight);

    // Set new height
    textarea.style.height = `${newHeight}px`;

    // Add overflow if max height is reached
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden';
  };

  // Adjust height on mount and when value changes
  useEffect(() => {
    adjustHeight();
  }, [value, defaultValue, autoResize, minRows, maxRows]);

  // Handle change with character counting
  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    setCharCount(newValue.length);
    adjustHeight();
    onChange?.(e);
  };

  // Initialize character count
  useEffect(() => {
    const initialValue = (value || defaultValue || '') as string;
    setCharCount(initialValue.length);
  }, []);

  // Determine validation state
  const validationState = error ? 'error' : success ? 'success' : warning ? 'warning' : 'default';

  // Build container classes
  const containerClasses = [
    styles['textarea-container'],
    styles[`textarea-${validationState}`],
    disabled && styles['textarea-disabled'],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  // Build textarea classes
  const textareaClasses = [
    styles.textarea,
    !autoResize && styles[`textarea-resize-${resize}`],
  ]
    .filter(Boolean)
    .join(' ');

  // Generate unique ID if not provided
  const textareaId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`;

  // Calculate character count percentage for warning
  const charPercentage = maxLength ? (charCount / maxLength) * 100 : 0;
  const showCharWarning = maxLength && charPercentage >= 90;

  return (
    <div className={containerClasses}>
      {/* Label */}
      {label && (
        <label htmlFor={textareaId} className={styles['textarea-label']}>
          {label}
          {required && <span className={styles['textarea-required']}>*</span>}
        </label>
      )}

      {/* Textarea */}
      <textarea
        ref={textareaRef}
        id={textareaId}
        className={textareaClasses}
        value={value}
        defaultValue={defaultValue}
        onChange={handleChange}
        maxLength={maxLength}
        disabled={disabled}
        aria-invalid={!!error}
        aria-required={required}
        aria-describedby={
          error || success || warning || helperText
            ? `${textareaId}-message`
            : undefined
        }
        rows={minRows}
        {...rest}
      />

      {/* Character counter and message container */}
      <div className={styles['textarea-footer']}>
        {/* Helper text or validation message */}
        {(helperText || error || success || warning) && (
          <div id={`${textareaId}-message`} className={styles['textarea-message']}>
            {error && <span className={styles['textarea-error-text']}>{error}</span>}
            {!error && success && <span className={styles['textarea-success-text']}>{success}</span>}
            {!error && !success && warning && (
              <span className={styles['textarea-warning-text']}>{warning}</span>
            )}
            {!error && !success && !warning && helperText && (
              <span className={styles['textarea-helper-text']}>{helperText}</span>
            )}
          </div>
        )}

        {/* Character counter */}
        {showCharacterCount && (
          <div
            className={`${styles['textarea-char-count']} ${
              showCharWarning ? styles['textarea-char-count-warning'] : ''
            }`}
          >
            {charCount}
            {maxLength && ` / ${maxLength}`}
          </div>
        )}
      </div>
    </div>
  );
});

Textarea.displayName = 'Textarea';
