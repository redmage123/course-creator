/**
 * Modal Component - Tami Design System
 *
 * BUSINESS CONTEXT:
 * Dialog component for confirmations, forms, and important messages across the platform.
 * Used for course creation, user registration, settings, and critical user actions.
 *
 * TECHNICAL IMPLEMENTATION:
 * React Portal-based modal with focus trap, keyboard navigation, and backdrop.
 * Includes accessibility features (ARIA, focus management, ESC key handling).
 *
 * DESIGN PRINCIPLES:
 * - Uses platform blue (#2563eb) for primary actions
 * - 12px border radius for modal container
 * - Smooth fade-in/fade-out animations
 * - Focus trap keeps keyboard navigation within modal
 * - WCAG 2.1 AA+ compliant
 */

import React, { useEffect, useRef, ReactNode } from 'react';
import { createPortal } from 'react-dom';
import styles from './Modal.module.css';

export type ModalSize = 'small' | 'medium' | 'large' | 'fullscreen';

export interface ModalProps {
  /**
   * Whether modal is open
   */
  isOpen: boolean;

  /**
   * Callback when modal should close
   */
  onClose: () => void;

  /**
   * Modal title
   */
  title?: string;

  /**
   * Modal content
   */
  children: ReactNode;

  /**
   * Modal footer (typically action buttons)
   */
  footer?: ReactNode;

  /**
   * Modal size
   * - small: 400px max width
   * - medium: 600px max width (default)
   * - large: 800px max width
   * - fullscreen: 90% viewport
   */
  size?: ModalSize;

  /**
   * Close modal when clicking backdrop
   * @default true
   */
  closeOnBackdropClick?: boolean;

  /**
   * Close modal when pressing ESC key
   * @default true
   */
  closeOnEscape?: boolean;

  /**
   * Prevent closing modal (for critical actions)
   * @default false
   */
  preventClose?: boolean;

  /**
   * Custom className for modal container
   */
  className?: string;

  /**
   * ARIA label for accessibility
   */
  ariaLabel?: string;
}

/**
 * Modal Component
 *
 * WHY THIS APPROACH:
 * - React Portal renders outside DOM hierarchy (prevents z-index issues)
 * - Focus trap keeps keyboard navigation accessible
 * - ESC key handling follows standard UX patterns
 * - Body scroll lock prevents background scrolling
 * - CSS Modules prevent style conflicts
 *
 * @example
 * ```tsx
 * // Simple confirmation modal
 * <Modal isOpen={isOpen} onClose={handleClose} title="Confirm Action">
 *   <p>Are you sure you want to proceed?</p>
 * </Modal>
 *
 * // Modal with footer actions
 * <Modal
 *   isOpen={isOpen}
 *   onClose={handleClose}
 *   title="Create Course"
 *   footer={
 *     <>
 *       <Button variant="ghost" onClick={handleClose}>Cancel</Button>
 *       <Button variant="primary" onClick={handleSubmit}>Create</Button>
 *     </>
 *   }
 * >
 *   <form>...</form>
 * </Modal>
 *
 * // Large modal that cannot be closed
 * <Modal
 *   isOpen={isOpen}
 *   onClose={handleClose}
 *   size="large"
 *   preventClose
 *   title="Important Information"
 * >
 *   <p>Critical content that user must read</p>
 * </Modal>
 * ```
 */
export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'medium',
  closeOnBackdropClick = true,
  closeOnEscape = true,
  preventClose = false,
  className,
  ariaLabel,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  // Lock body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement as HTMLElement;
      document.body.style.overflow = 'hidden';

      // Focus modal container
      setTimeout(() => {
        modalRef.current?.focus();
      }, 100);

      return () => {
        document.body.style.overflow = '';
        // Restore focus to previous element
        previousActiveElement.current?.focus();
      };
    }
  }, [isOpen]);

  // Handle ESC key
  useEffect(() => {
    if (!isOpen || preventClose || !closeOnEscape) return;

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose, preventClose, closeOnEscape]);

  // Handle backdrop click
  const handleBackdropClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (
      closeOnBackdropClick &&
      !preventClose &&
      event.target === event.currentTarget
    ) {
      onClose();
    }
  };

  // Trap focus within modal
  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'Tab') return;

    const focusableElements = modalRef.current?.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    if (!focusableElements || focusableElements.length === 0) return;

    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    if (event.shiftKey && document.activeElement === firstElement) {
      event.preventDefault();
      lastElement.focus();
    } else if (!event.shiftKey && document.activeElement === lastElement) {
      event.preventDefault();
      firstElement.focus();
    }
  };

  if (!isOpen) return null;

  const modalClasses = [
    styles.modal,
    styles[`modal-${size}`],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  const modalContent = (
    <div className={styles.backdrop} onClick={handleBackdropClick}>
      <div
        ref={modalRef}
        className={modalClasses}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
        aria-label={ariaLabel || title}
        tabIndex={-1}
        onKeyDown={handleKeyDown}
      >
        {/* Header */}
        {title && (
          <div className={styles['modal-header']}>
            <h2 id="modal-title" className={styles['modal-title']}>
              {title}
            </h2>
            {!preventClose && (
              <button
                className={styles['modal-close']}
                onClick={onClose}
                aria-label="Close modal"
                type="button"
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 20 20"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M15 5L5 15M5 5L15 15"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
            )}
          </div>
        )}

        {/* Body */}
        <div className={styles['modal-body']}>{children}</div>

        {/* Footer */}
        {footer && <div className={styles['modal-footer']}>{footer}</div>}
      </div>
    </div>
  );

  // Render in portal
  return createPortal(modalContent, document.body);
};

Modal.displayName = 'Modal';
