/**
 * Screen Reader Announcer Component
 *
 * BUSINESS CONTEXT:
 * Provides ARIA live region for screen reader announcements. Ensures screen
 * reader users are informed of dynamic content changes. Implements WCAG 4.1.3
 * (Status Messages).
 *
 * TECHNICAL IMPLEMENTATION:
 * Creates hidden live region element. Listens for custom announcement events
 * and announces messages with appropriate politeness level.
 *
 * WCAG 2.1 AA Compliance:
 * - 4.1.3 Status Messages (Level AA)
 * - ARIA live regions
 * - Polite vs assertive announcements
 */

import React, { useEffect, useRef } from 'react';
import styles from './ScreenReaderAnnouncer.module.css';

/**
 * Screen Reader Announcer Component
 */
export const ScreenReaderAnnouncer: React.FC = () => {
  const politeRef = useRef<HTMLDivElement>(null);
  const assertiveRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    /**
     * Handle announcement request
     *
     * TECHNICAL IMPLEMENTATION:
     * Listens for custom 'announce' events and displays message in
     * appropriate ARIA live region.
     */
    const handleAnnounce = (event: CustomEvent) => {
      const { message, politeness = 'polite' } = event.detail;

      const target = politeness === 'assertive' ? assertiveRef.current : politeRef.current;
      if (target) {
        target.textContent = message;

        // Clear after 3 seconds
        setTimeout(() => {
          target.textContent = '';
        }, 3000);
      }
    };

    // Listen for custom announce events
    window.addEventListener('announce' as any, handleAnnounce);

    return () => {
      window.removeEventListener('announce' as any, handleAnnounce);
    };
  }, []);

  return (
    <>
      {/* Polite announcements */}
      <div
        ref={politeRef}
        className={styles.announcer}
        role="status"
        aria-live="polite"
        aria-atomic="true"
      />

      {/* Assertive announcements */}
      <div
        ref={assertiveRef}
        className={styles.announcer}
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
      />
    </>
  );
};
