/**
 * Card Component - Tami Design System
 *
 * BUSINESS CONTEXT:
 * Flexible container component for displaying organized content across all platform features.
 * Used for course cards, dashboard widgets, profile sections, and content grouping.
 *
 * TECHNICAL IMPLEMENTATION:
 * React component implementing Tami card design with header, body, and footer sections.
 * Includes variants for different visual treatments and interactive states.
 *
 * DESIGN PRINCIPLES:
 * - Uses platform blue (#2563eb) for interactive states
 * - 8px border radius (design system standard)
 * - Consistent shadow elevations
 * - Flexible content sections (header, body, footer)
 * - WCAG 2.1 AA+ compliant
 */

import React, { HTMLAttributes, ReactNode } from 'react';
import styles from './Card.module.css';

export type CardVariant = 'default' | 'outlined' | 'elevated' | 'interactive';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /**
   * Card visual variant
   * - default: Subtle border with white background
   * - outlined: Emphasized border without shadow
   * - elevated: Shadow with no border
   * - interactive: Hover effects for clickable cards
   */
  variant?: CardVariant;

  /**
   * Card header content (title, actions)
   */
  header?: ReactNode;

  /**
   * Card footer content (actions, metadata)
   */
  footer?: ReactNode;

  /**
   * Card body content
   */
  children: ReactNode;

  /**
   * Card padding size
   * - none: No padding
   * - small: 12px
   * - medium: 16px (default)
   * - large: 24px
   */
  padding?: 'none' | 'small' | 'medium' | 'large';

  /**
   * Full width card (100% of container)
   */
  fullWidth?: boolean;

  /**
   * Clickable card (adds cursor pointer)
   */
  clickable?: boolean;
}

/**
 * Card Component
 *
 * WHY THIS APPROACH:
 * - CSS Modules prevent style conflicts
 * - TypeScript ensures type safety
 * - Extends native div props for full HTML support
 * - Flexible sections (header, body, footer) for different layouts
 * - Interactive variant for clickable cards
 *
 * @example
 * ```tsx
 * // Simple card with title and content
 * <Card header={<h3>Course Title</h3>}>
 *   <p>Course description goes here</p>
 * </Card>
 *
 * // Elevated card with footer
 * <Card
 *   variant="elevated"
 *   header={<h3>Dashboard Widget</h3>}
 *   footer={<Button>View Details</Button>}
 * >
 *   <p>Widget content</p>
 * </Card>
 *
 * // Interactive clickable card
 * <Card
 *   variant="interactive"
 *   clickable
 *   onClick={() => navigate('/course/123')}
 * >
 *   <h4>Click to view course</h4>
 *   <p>Course description</p>
 * </Card>
 *
 * // Card with custom padding
 * <Card padding="large">
 *   <Content />
 * </Card>
 * ```
 */
export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = 'default',
      header,
      footer,
      children,
      padding = 'medium',
      fullWidth = false,
      clickable = false,
      className,
      onClick,
      onKeyDown,
      tabIndex,
      ...props
    },
    ref
  ) => {
    // Combine class names
    const classes = [
      styles.card,
      styles[`card-${variant}`],
      styles[`card-padding-${padding}`],
      fullWidth && styles['card-full-width'],
      clickable && styles['card-clickable'],
      className,
    ]
      .filter(Boolean)
      .join(' ');

    // Handle keyboard events for clickable cards
    const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
      if (clickable && onClick && (event.key === 'Enter' || event.key === ' ')) {
        event.preventDefault();
        onClick(event as unknown as React.MouseEvent<HTMLDivElement>);
      }
      onKeyDown?.(event);
    };

    // Make clickable cards focusable
    const effectiveTabIndex = clickable ? (tabIndex ?? 0) : tabIndex;

    return (
      <div
        ref={ref}
        className={classes}
        onClick={onClick}
        onKeyDown={handleKeyDown}
        tabIndex={effectiveTabIndex}
        {...props}
      >
        {/* Header section */}
        {header && <div className={styles['card-header']}>{header}</div>}

        {/* Body section */}
        <div className={styles['card-body']}>{children}</div>

        {/* Footer section */}
        {footer && <div className={styles['card-footer']}>{footer}</div>}
      </div>
    );
  }
);

Card.displayName = 'Card';
