/**
 * Swipeable Card Component
 *
 * BUSINESS CONTEXT:
 * Provides swipe gestures for card-based content interactions.
 * Supports swipe-to-delete, swipe-to-archive, and custom swipe actions.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses touch events and CSS transforms for smooth swipe animations.
 * Configurable swipe thresholds and action callbacks.
 */

import React, { useRef, useState, useCallback, TouchEvent } from 'react';
import { useMobileExperience } from '../hooks/useMobileExperience';
import styles from './SwipeableCard.module.css';

export interface SwipeAction {
  label: string;
  icon: string;
  color: string;
  onAction: () => void | Promise<void>;
}

export interface SwipeableCardProps {
  children: React.ReactNode;
  leftAction?: SwipeAction;
  rightAction?: SwipeAction;
  swipeThreshold?: number; // pixels
  disabled?: boolean;
}

/**
 * Swipeable Card Component
 *
 * WHY THIS APPROACH:
 * - Native-feeling swipe gestures
 * - Visual feedback during swipe
 * - Configurable actions for left/right swipe
 * - Haptic feedback on action trigger
 */
export const SwipeableCard: React.FC<SwipeableCardProps> = ({
  children,
  leftAction,
  rightAction,
  swipeThreshold = 80,
  disabled = false,
}) => {
  const { vibrate } = useMobileExperience();
  const [translateX, setTranslateX] = useState(0);
  const [isSwiping, setIsSwiping] = useState(false);
  const [actionTriggered, setActionTriggered] = useState(false);
  const startX = useRef(0);
  const currentX = useRef(0);

  /**
   * Handle touch start
   */
  const handleTouchStart = useCallback(
    (e: TouchEvent) => {
      if (disabled) return;

      startX.current = e.touches[0].clientX;
      setIsSwiping(true);
      setActionTriggered(false);
    },
    [disabled]
  );

  /**
   * Handle touch move
   */
  const handleTouchMove = useCallback(
    (e: TouchEvent) => {
      if (disabled || !isSwiping) return;

      currentX.current = e.touches[0].clientX;
      const diff = currentX.current - startX.current;

      // Limit swipe distance
      const maxSwipe = 150;
      const limitedDiff = Math.max(-maxSwipe, Math.min(maxSwipe, diff));

      setTranslateX(limitedDiff);

      // Trigger haptic feedback when threshold reached
      if (!actionTriggered) {
        if (Math.abs(limitedDiff) >= swipeThreshold) {
          vibrate(20);
          setActionTriggered(true);
        }
      }
    },
    [disabled, isSwiping, swipeThreshold, vibrate, actionTriggered]
  );

  /**
   * Handle touch end
   */
  const handleTouchEnd = useCallback(async () => {
    if (disabled || !isSwiping) return;

    setIsSwiping(false);

    // Check if action threshold was met
    if (Math.abs(translateX) >= swipeThreshold) {
      // Execute action
      if (translateX > 0 && leftAction) {
        vibrate(30);
        await leftAction.onAction();
      } else if (translateX < 0 && rightAction) {
        vibrate(30);
        await rightAction.onAction();
      }
    }

    // Reset position
    setTranslateX(0);
    setActionTriggered(false);
  }, [disabled, isSwiping, translateX, swipeThreshold, leftAction, rightAction, vibrate]);

  const cardStyle = {
    transform: `translateX(${translateX}px)`,
    transition: isSwiping ? 'none' : 'transform 0.3s ease-out',
  };

  const showLeftAction = leftAction && translateX > 0;
  const showRightAction = rightAction && translateX < 0;
  const leftActionActive = translateX >= swipeThreshold;
  const rightActionActive = Math.abs(translateX) >= swipeThreshold;

  return (
    <div className={styles.swipeableCard}>
      {/* Left action background */}
      {showLeftAction && (
        <div
          className={`${styles.actionBackground} ${styles.leftAction} ${leftActionActive ? styles.active : ''}`}
          style={{ backgroundColor: leftAction.color }}
        >
          <span className={styles.actionIcon}>{leftAction.icon}</span>
          <span className={styles.actionLabel}>{leftAction.label}</span>
        </div>
      )}

      {/* Right action background */}
      {showRightAction && (
        <div
          className={`${styles.actionBackground} ${styles.rightAction} ${rightActionActive ? styles.active : ''}`}
          style={{ backgroundColor: rightAction.color }}
        >
          <span className={styles.actionIcon}>{rightAction.icon}</span>
          <span className={styles.actionLabel}>{rightAction.label}</span>
        </div>
      )}

      {/* Card content */}
      <div
        className={styles.cardContent}
        style={cardStyle}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {children}
      </div>
    </div>
  );
};
