/**
 * Skeleton Loader Component
 *
 * BUSINESS CONTEXT:
 * Provides a content placeholder while actual data is loading,
 * improving perceived performance and reducing layout shift.
 *
 * TECHNICAL IMPLEMENTATION:
 * Animated skeleton screens that match the shape of the final content.
 * Uses CSS animations for smooth shimmer effect.
 *
 * DESIGN RATIONALE:
 * Skeleton screens are proven to reduce perceived loading time by 20-30%
 * compared to blank screens or spinners alone. Users perceive the app
 * as faster when they see content-shaped placeholders.
 *
 * USAGE:
 * - List items loading
 * - Card grids loading
 * - Profile data loading
 * - Dashboard widgets loading
 */

import styles from './Loading.module.css';

interface SkeletonLoaderProps {
  /** Type of skeleton to display */
  variant?: 'text' | 'rectangular' | 'circular' | 'card';
  /** Width of the skeleton */
  width?: string | number;
  /** Height of the skeleton */
  height?: string | number;
  /** Number of skeleton items to render (for lists) */
  count?: number;
  /** Custom className for additional styling */
  className?: string;
}

/**
 * SkeletonLoader Component
 *
 * VARIANTS:
 * - text: Single line of text (e.g., headlines, labels)
 * - rectangular: Rectangle shape (e.g., images, videos)
 * - circular: Circle shape (e.g., avatars, icons)
 * - card: Pre-composed card layout (image + text lines)
 *
 * FEATURES:
 * - Shimmer animation effect
 * - Multiple items support (count prop)
 * - Flexible sizing
 * - Composable for custom layouts
 *
 * ACCESSIBILITY:
 * - aria-busy="true" indicates loading state
 * - aria-label describes content being loaded
 */
export const SkeletonLoader = ({
  variant = 'text',
  width,
  height,
  count = 1,
  className = '',
}: SkeletonLoaderProps) => {
  /**
   * Generate inline styles for custom dimensions
   */
  const getStyles = (): React.CSSProperties => {
    const styles: React.CSSProperties = {};

    if (width) {
      styles.width = typeof width === 'number' ? `${width}px` : width;
    }

    if (height) {
      styles.height = typeof height === 'number' ? `${height}px` : height;
    }

    return styles;
  };

  /**
   * Render card variant (composite skeleton)
   */
  if (variant === 'card') {
    return (
      <div className={`${styles.skeletonCard} ${className}`}>
        {Array.from({ length: count }).map((_, index) => (
          <div key={index} className={styles.skeletonCardItem}>
            <div className={`${styles.skeleton} ${styles.skeletonRectangular}`} style={{ height: '200px' }} />
            <div className={styles.skeletonCardContent}>
              <div className={`${styles.skeleton} ${styles.skeletonText}`} style={{ width: '80%', height: '24px' }} />
              <div className={`${styles.skeleton} ${styles.skeletonText}`} style={{ width: '60%', height: '16px', marginTop: '8px' }} />
              <div className={`${styles.skeleton} ${styles.skeletonText}`} style={{ width: '90%', height: '16px', marginTop: '4px' }} />
            </div>
          </div>
        ))}
      </div>
    );
  }

  /**
   * Render simple variants (text, rectangular, circular)
   */
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className={`${styles.skeleton} ${styles[`skeleton${variant.charAt(0).toUpperCase() + variant.slice(1)}`]} ${className}`}
          style={getStyles()}
          aria-busy="true"
          aria-label="Loading content"
        />
      ))}
    </>
  );
};

/**
 * Predefined Skeleton Layouts
 *
 * BUSINESS VALUE:
 * Common patterns for frequently used layouts to reduce development time.
 */

/**
 * Profile Skeleton
 * Used for user profile loading states
 */
export const ProfileSkeleton = () => (
  <div className={styles.profileSkeleton}>
    <div className={`${styles.skeleton} ${styles.skeletonCircular}`} style={{ width: '80px', height: '80px' }} />
    <div className={styles.profileSkeletonContent}>
      <div className={`${styles.skeleton} ${styles.skeletonText}`} style={{ width: '200px', height: '24px' }} />
      <div className={`${styles.skeleton} ${styles.skeletonText}`} style={{ width: '150px', height: '16px', marginTop: '8px' }} />
    </div>
  </div>
);

/**
 * List Item Skeleton
 * Used for list/table row loading states
 */
export const ListItemSkeleton = ({ count = 5 }: { count?: number }) => (
  <div className={styles.listSkeleton}>
    {Array.from({ length: count }).map((_, index) => (
      <div key={index} className={styles.listSkeletonItem}>
        <div className={`${styles.skeleton} ${styles.skeletonCircular}`} style={{ width: '40px', height: '40px' }} />
        <div className={styles.listSkeletonContent}>
          <div className={`${styles.skeleton} ${styles.skeletonText}`} style={{ width: '70%', height: '16px' }} />
          <div className={`${styles.skeleton} ${styles.skeletonText}`} style={{ width: '50%', height: '14px', marginTop: '8px' }} />
        </div>
      </div>
    ))}
  </div>
);

/**
 * Dashboard Widget Skeleton
 * Used for dashboard card/widget loading states
 */
export const DashboardWidgetSkeleton = ({ count = 3 }: { count?: number }) => (
  <div className={styles.dashboardSkeleton}>
    {Array.from({ length: count }).map((_, index) => (
      <div key={index} className={styles.dashboardSkeletonCard}>
        <div className={`${styles.skeleton} ${styles.skeletonText}`} style={{ width: '60%', height: '20px' }} />
        <div className={`${styles.skeleton} ${styles.skeletonRectangular}`} style={{ width: '100%', height: '120px', marginTop: '16px' }} />
        <div className={`${styles.skeleton} ${styles.skeletonText}`} style={{ width: '80%', height: '16px', marginTop: '12px' }} />
      </div>
    ))}
  </div>
);
