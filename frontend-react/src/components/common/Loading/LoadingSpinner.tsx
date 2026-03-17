/**
 * Loading Spinner Component
 *
 * BUSINESS CONTEXT:
 * Provides visual feedback to users during asynchronous operations,
 * improving perceived performance and user experience.
 *
 * TECHNICAL IMPLEMENTATION:
 * Reusable spinner component with multiple size variants.
 * Pure CSS animation for optimal performance.
 *
 * USAGE:
 * - API requests
 * - Page transitions
 * - Data loading states
 * - Form submissions
 */

import styles from './Loading.module.css';

interface LoadingSpinnerProps {
  /** Size of the spinner */
  size?: 'small' | 'medium' | 'large';
  /** Optional text to display below spinner */
  text?: string;
  /** Make spinner fullscreen with overlay */
  fullscreen?: boolean;
  /** Custom className for additional styling */
  className?: string;
}

/**
 * LoadingSpinner Component
 *
 * DESIGN APPROACH:
 * - CSS-only animation (no JavaScript)
 * - Three size variants for different contexts
 * - Optional fullscreen overlay mode
 * - Accessible with aria-labels
 *
 * SIZE VARIANTS:
 * - small: 24px (inline loading, buttons)
 * - medium: 40px (default, cards, sections)
 * - large: 64px (page-level loading)
 *
 * ACCESSIBILITY:
 * - aria-label for screen readers
 * - role="status" for live region
 * - Semantic loading text
 */
export const LoadingSpinner = ({
  size = 'medium',
  text,
  fullscreen = false,
  className = '',
}: LoadingSpinnerProps) => {
  const spinnerContent = (
    <div
      className={`${styles.spinnerContainer} ${styles[size]} ${className}`}
      role="status"
      aria-label={text || 'Loading'}
    >
      <div className={styles.spinner}>
        <div className={styles.spinnerCircle}></div>
      </div>
      {text && <p className={styles.spinnerText}>{text}</p>}
    </div>
  );

  if (fullscreen) {
    return (
      <div className={styles.fullscreenOverlay}>
        {spinnerContent}
      </div>
    );
  }

  return spinnerContent;
};
