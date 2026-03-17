/**
 * Skip Links Component
 *
 * BUSINESS CONTEXT:
 * Provides skip navigation links for keyboard users to bypass repetitive content.
 * Critical for screen reader and keyboard-only users. Implements WCAG 2.4.1
 * (Bypass Blocks).
 *
 * TECHNICAL IMPLEMENTATION:
 * Renders visually hidden links that become visible on focus. Links jump to
 * main content areas. Always first in tab order.
 *
 * WCAG 2.1 AA Compliance:
 * - 2.4.1 Bypass Blocks (Level A)
 * - Visible on keyboard focus
 * - Logical tab order
 */

import React from 'react';
import styles from './SkipLinks.module.css';

/**
 * Skip Links Component
 */
export const SkipLinks: React.FC = () => {
  const skipLinks = [
    { href: '#main-content', label: 'Skip to main content' },
    { href: '#navigation', label: 'Skip to navigation' },
    { href: '#footer', label: 'Skip to footer' },
  ];

  return (
    <nav className={styles.skipLinks} aria-label="Skip navigation">
      {skipLinks.map((link) => (
        <a
          key={link.href}
          href={link.href}
          className={styles.skipLink}
        >
          {link.label}
        </a>
      ))}
    </nav>
  );
};
