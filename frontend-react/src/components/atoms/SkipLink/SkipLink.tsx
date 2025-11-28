/**
 * SkipLink Component - Accessibility Feature
 *
 * BUSINESS CONTEXT:
 * Provides keyboard users and screen reader users the ability to bypass
 * repetitive navigation and jump directly to main content. This is a
 * WCAG 2.1 Level A requirement (Success Criterion 2.4.1).
 *
 * TECHNICAL IMPLEMENTATION:
 * - Visually hidden until focused via keyboard
 * - Positioned absolutely at top of page
 * - Jumps to main content landmark on activation
 * - Smooth focus management for seamless navigation
 *
 * DESIGN PRINCIPLES:
 * - Platform blue (#2563eb) for visibility when focused
 * - High contrast for accessibility
 * - Prominent position (top-left) when visible
 * - Smooth transitions for professional appearance
 */

import React, { useCallback } from 'react';
import styles from './SkipLink.module.css';

export interface SkipLinkProps {
  /**
   * Target element ID to skip to (without #)
   * @default 'main-content'
   */
  targetId?: string;

  /**
   * Link text displayed when focused
   * @default 'Skip to main content'
   */
  children?: React.ReactNode;

  /**
   * Additional CSS class name
   */
  className?: string;
}

/**
 * SkipLink Component
 *
 * WHY THIS APPROACH:
 * - Visually hidden but accessible to keyboard/screen reader users
 * - Uses native anchor element for proper semantics
 * - Focus handling ensures smooth navigation
 * - Follows WCAG 2.1 bypass blocks requirement
 *
 * @example
 * ```tsx
 * // In DashboardLayout or App component
 * <SkipLink targetId="main-content" />
 * <Navbar />
 * <main id="main-content" tabIndex={-1}>
 *   {children}
 * </main>
 * ```
 */
export const SkipLink: React.FC<SkipLinkProps> = ({
  targetId = 'main-content',
  children = 'Skip to main content',
  className,
}) => {
  /**
   * Handle click to focus the target element
   *
   * WHY: Some browsers don't focus the target on anchor click,
   * so we manually focus for consistent behavior.
   */
  const handleClick = useCallback((event: React.MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault();
    const target = document.getElementById(targetId);

    if (target) {
      // Set tabindex=-1 if not already focusable
      if (!target.hasAttribute('tabindex')) {
        target.setAttribute('tabindex', '-1');
      }

      // Focus the target element
      target.focus();

      // Scroll into view smoothly (check for browser support)
      if (target.scrollIntoView) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }, [targetId]);

  /**
   * Handle keyboard activation
   */
  const handleKeyDown = useCallback((event: React.KeyboardEvent<HTMLAnchorElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      const target = document.getElementById(targetId);

      if (target) {
        if (!target.hasAttribute('tabindex')) {
          target.setAttribute('tabindex', '-1');
        }
        target.focus();
        if (target.scrollIntoView) {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
    }
  }, [targetId]);

  const classes = [styles['skip-link'], className].filter(Boolean).join(' ');

  return (
    <a
      href={`#${targetId}`}
      className={classes}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      data-testid="skip-link"
    >
      {children}
    </a>
  );
};

SkipLink.displayName = 'SkipLink';
