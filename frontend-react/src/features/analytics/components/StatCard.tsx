/**
 * StatCard Component
 *
 * Displays a single metric card with title, value, icon, and optional trend/subtitle.
 * Used in the analytics dashboard to show key performance indicators.
 *
 * @module features/analytics/components/StatCard
 */

import React from 'react';
import styles from './StatCard.module.css';

export interface StatCardProps {
  /** Card title */
  title: string;
  /** Main metric value to display */
  value: string | number;
  /** Optional subtitle with additional context */
  subtitle?: string;
  /** Optional trend indicator (positive/negative change) */
  trend?: {
    value: number;
    direction: 'up' | 'down';
  };
  /** Icon/emoji to display */
  icon?: string;
  /** Card accent color */
  color?: string;
}

/**
 * StatCard Component
 *
 * WHY THIS APPROACH:
 * - Reusable metric display component for dashboard consistency
 * - Visual hierarchy: Icon → Title → Value → Subtitle → Trend
 * - Color coding for quick visual identification
 * - Trend indicators show change over time (useful for engagement tracking)
 */
export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  icon,
  color = '#4caf50'
}) => {
  return (
    <div className={styles.statCard} style={{ borderLeftColor: color }}>
      {/* Icon */}
      {icon && (
        <div className={styles.iconContainer} style={{ color }}>
          <span className={styles.icon}>{icon}</span>
        </div>
      )}

      {/* Content */}
      <div className={styles.content}>
        <h3 className={styles.title}>{title}</h3>
        <div className={styles.value}>{value}</div>

        {subtitle && (
          <p className={styles.subtitle}>{subtitle}</p>
        )}

        {trend && (
          <div className={`${styles.trend} ${styles[trend.direction]}`}>
            <span className={styles.trendIcon}>
              {trend.direction === 'up' ? '↑' : '↓'}
            </span>
            <span className={styles.trendValue}>
              {Math.abs(trend.value)}%
            </span>
            <span className={styles.trendLabel}>vs last period</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default StatCard;
