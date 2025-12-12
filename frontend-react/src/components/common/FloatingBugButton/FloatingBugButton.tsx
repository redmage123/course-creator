/**
 * Floating Bug Report Button Component
 *
 * BUSINESS CONTEXT:
 * Provides easy access to bug reporting from any page in the application.
 * Floating action button (FAB) positioned in bottom-right corner.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fixed position FAB with bug icon
 * - Only visible to authenticated users
 * - Tooltip on hover for clarity
 * - Accessible with keyboard navigation
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../hooks/useAuth';
import styles from './FloatingBugButton.module.css';

/**
 * Floating Bug Report Button
 *
 * WHY THIS APPROACH:
 * - Always visible for easy access to bug reporting
 * - Non-intrusive position in bottom-right corner
 * - Only shown to authenticated users (they have context to report bugs)
 * - Animated hover state for visual feedback
 */
export const FloatingBugButton: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [showTooltip, setShowTooltip] = useState(false);

  // Only show for authenticated users
  if (!isAuthenticated) {
    return null;
  }

  const handleClick = () => {
    navigate('/bugs/submit');
  };

  return (
    <div className={styles.container}>
      {/* Tooltip */}
      {showTooltip && (
        <div className={styles.tooltip} role="tooltip">
          Report a Bug
        </div>
      )}

      {/* FAB Button */}
      <button
        className={styles.fab}
        onClick={handleClick}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onFocus={() => setShowTooltip(true)}
        onBlur={() => setShowTooltip(false)}
        aria-label="Report a bug"
        title="Report a Bug"
      >
        <i className="fas fa-bug" aria-hidden="true"></i>
      </button>
    </div>
  );
};

export default FloatingBugButton;
