/**
 * Heading Component - Tami Design System
 *
 * BUSINESS CONTEXT:
 * Typography component for semantic headings (h1-h6) across the platform.
 * Used for page titles, section headers, card titles, and content hierarchy.
 *
 * TECHNICAL IMPLEMENTATION:
 * Polymorphic component that renders semantic HTML headings with
 * consistent Tami design system typography and spacing.
 *
 * DESIGN PRINCIPLES:
 * - Semantic HTML for accessibility (h1-h6)
 * - Consistent typography scale
 * - Optional visual styling decoupled from semantic level
 * - WCAG 2.1 AA+ compliant contrast ratios
 */

import React, { forwardRef } from 'react';
import styles from './Heading.module.css';

export type HeadingLevel = 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
export type HeadingVariant = 'display' | 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';

export interface HeadingProps extends React.HTMLAttributes<HTMLHeadingElement> {
  /**
   * Semantic heading level (determines HTML element)
   * @default "h2"
   */
  level?: HeadingLevel;

  /**
   * Visual styling variant (decoupled from semantic level)
   * Allows h2 to look like h1, etc.
   * @default matches level
   */
  variant?: HeadingVariant;

  /**
   * Text alignment
   * @default "left"
   */
  align?: 'left' | 'center' | 'right';

  /**
   * Text color
   * @default "default"
   */
  color?: 'default' | 'muted' | 'primary' | 'error' | 'success' | 'warning';

  /**
   * Font weight
   * @default matches variant default
   */
  weight?: 'normal' | 'medium' | 'semibold' | 'bold';

  /**
   * Bottom margin
   * @default true
   */
  gutterBottom?: boolean;

  /**
   * Custom className
   */
  className?: string;

  /**
   * Heading text content
   */
  children: React.ReactNode;
}

/**
 * Heading Component
 *
 * WHY THIS APPROACH:
 * - Polymorphic rendering allows semantic HTML while controlling visual style
 * - Decoupled semantic level from visual variant for flexibility
 * - forwardRef enables ref access to heading elements
 * - Consistent typography scale from Tami design system
 * - Accessible heading hierarchy for screen readers
 *
 * @example
 * ```tsx
 * // Semantic h1 with h1 styling (default)
 * <Heading level="h1">
 *   Course Creator Platform
 * </Heading>
 *
 * // Semantic h2 that looks like h1 (visual override)
 * <Heading level="h2" variant="h1">
 *   Dashboard Overview
 * </Heading>
 *
 * // With custom styling
 * <Heading
 *   level="h3"
 *   color="primary"
 *   align="center"
 *   weight="bold"
 * >
 *   Welcome Back
 * </Heading>
 *
 * // Without bottom margin
 * <Heading level="h4" gutterBottom={false}>
 *   Card Title
 * </Heading>
 * ```
 */
export const Heading = forwardRef<HTMLHeadingElement, HeadingProps>(({
  level = 'h2',
  variant,
  align = 'left',
  color = 'default',
  weight,
  gutterBottom = true,
  className,
  children,
  ...rest
}, ref) => {
  // Use level as variant if variant not specified
  const finalVariant = variant || level;

  // Build className string
  const headingClasses = [
    styles['heading'],
    styles[`heading-${finalVariant}`],
    styles[`heading-align-${align}`],
    styles[`heading-color-${color}`],
    weight && styles[`heading-weight-${weight}`],
    gutterBottom && styles['heading-gutter-bottom'],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  // Render the appropriate semantic HTML element
  const HeadingTag = level as React.ElementType;

  return (
    <HeadingTag ref={ref} className={headingClasses} {...rest}>
      {children}
    </HeadingTag>
  );
});

Heading.displayName = 'Heading';
