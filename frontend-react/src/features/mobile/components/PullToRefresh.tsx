/**
 * Pull to Refresh Component
 *
 * BUSINESS CONTEXT:
 * Provides pull-to-refresh functionality for mobile content views.
 * Common pattern in mobile apps for refreshing data.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses touch events and scroll position to detect pull gesture.
 * Shows loading indicator and triggers refresh callback.
 */

import React, { useRef, useState, useCallback, TouchEvent } from 'react';
import { useMobileExperience } from '../hooks/useMobileExperience';
import styles from './PullToRefresh.module.css';

export interface PullToRefreshProps {
  children: React.ReactNode;
  onRefresh: () => Promise<void>;
  disabled?: boolean;
  pullThreshold?: number; // pixels
}

/**
 * Pull to Refresh Component
 *
 * WHY THIS APPROACH:
 * - Native mobile app behavior
 * - Visual feedback during pull
 * - Smooth animations
 * - Haptic feedback on refresh
 */
export const PullToRefresh: React.FC<PullToRefreshProps> = ({
  children,
  onRefresh,
  disabled = false,
  pullThreshold = 80,
}) => {
  const { vibrate, isMobile } = useMobileExperience();
  const [isPulling, setIsPulling] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const startY = useRef(0);
  const containerRef = useRef<HTMLDivElement>(null);

  /**
   * Handle touch start
   */
  const handleTouchStart = useCallback(
    (e: TouchEvent) => {
      if (disabled || isRefreshing || !isMobile) return;

      // Only start pull if at top of scroll
      if (containerRef.current && containerRef.current.scrollTop === 0) {
        startY.current = e.touches[0].clientY;
        setIsPulling(true);
      }
    },
    [disabled, isRefreshing, isMobile]
  );

  /**
   * Handle touch move
   */
  const handleTouchMove = useCallback(
    (e: TouchEvent) => {
      if (!isPulling || disabled || isRefreshing) return;

      const currentY = e.touches[0].clientY;
      const diff = currentY - startY.current;

      // Only allow pulling down
      if (diff > 0) {
        // Apply resistance to pull
        const resistance = 0.5;
        const limitedDiff = Math.min(diff * resistance, pullThreshold * 1.5);
        setPullDistance(limitedDiff);

        // Haptic feedback when threshold reached
        if (limitedDiff >= pullThreshold && pullDistance < pullThreshold) {
          vibrate(20);
        }
      }
    },
    [isPulling, disabled, isRefreshing, pullThreshold, pullDistance, vibrate]
  );

  /**
   * Handle touch end
   */
  const handleTouchEnd = useCallback(async () => {
    if (!isPulling || disabled) return;

    setIsPulling(false);

    // Trigger refresh if threshold met
    if (pullDistance >= pullThreshold && !isRefreshing) {
      setIsRefreshing(true);
      vibrate(30);

      try {
        await onRefresh();
      } catch (error) {
        console.error('[PullToRefresh] Refresh failed:', error);
      } finally {
        setIsRefreshing(false);
        setPullDistance(0);
      }
    } else {
      setPullDistance(0);
    }
  }, [isPulling, disabled, pullDistance, pullThreshold, isRefreshing, onRefresh, vibrate]);

  const progress = Math.min(pullDistance / pullThreshold, 1);
  const rotation = progress * 360;

  const pullIndicatorStyle = {
    transform: `translateY(${Math.min(pullDistance, pullThreshold)}px)`,
    opacity: isPulling || isRefreshing ? 1 : 0,
  };

  const spinnerStyle = {
    transform: `rotate(${isRefreshing ? 0 : rotation}deg)`,
    animation: isRefreshing ? `${styles.spin} 1s linear infinite` : 'none',
  };

  if (!isMobile) {
    return <>{children}</>;
  }

  return (
    <div
      ref={containerRef}
      className={styles.pullToRefresh}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Pull indicator */}
      <div className={styles.pullIndicator} style={pullIndicatorStyle}>
        <div className={styles.spinner} style={spinnerStyle}>
          ↻
        </div>
        <div className={styles.pullText}>
          {isRefreshing ? 'Refreshing...' : progress >= 1 ? 'Release to refresh' : 'Pull to refresh'}
        </div>
      </div>

      {/* Content */}
      <div className={styles.content}>{children}</div>
    </div>
  );
};
