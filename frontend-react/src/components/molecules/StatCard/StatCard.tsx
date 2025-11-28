/**
 * StatCard Component - Dashboard Statistics with Trend Indicators
 *
 * BUSINESS CONTEXT:
 * Displays key metrics on dashboards with visual trend indicators showing
 * change from previous period. Helps users quickly understand if metrics
 * are improving or declining.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses Card component as base
 * - Trend indicator with up/down arrows and percentage
 * - Accessible color-coded trends (green=up, red=down)
 * - Supports different value formats (number, percentage, currency)
 *
 * DESIGN PRINCIPLES:
 * - Platform blue for primary values
 * - Green (#16a34a) for positive trends
 * - Red (#dc2626) for negative trends
 * - Gray (#64748b) for neutral/labels
 */

import React from 'react';
import { Card } from '../../atoms/Card';
import styles from './StatCard.module.css';

export type TrendDirection = 'up' | 'down' | 'neutral';
export type ValueFormat = 'number' | 'percentage' | 'currency' | 'duration';

export interface StatCardProps {
  /**
   * Main statistic value to display
   */
  value: number | string;

  /**
   * Label describing the statistic
   */
  label: string;

  /**
   * Trend change percentage (e.g., 12.5 for +12.5%)
   * Positive values show green/up, negative show red/down
   */
  trend?: number;

  /**
   * Override automatic trend direction detection
   * @default calculated from trend value
   */
  trendDirection?: TrendDirection;

  /**
   * Label for the trend period (e.g., "vs last week")
   * @default "vs last period"
   */
  trendLabel?: string;

  /**
   * Format for the main value
   * @default 'number'
   */
  valueFormat?: ValueFormat;

  /**
   * Currency symbol for currency format
   * @default '$'
   */
  currencySymbol?: string;

  /**
   * Optional icon to display
   */
  icon?: React.ReactNode;

  /**
   * Card variant
   * @default 'elevated'
   */
  variant?: 'elevated' | 'outlined' | 'filled';

  /**
   * Additional CSS class name
   */
  className?: string;

  /**
   * Accessible description for screen readers
   */
  ariaDescription?: string;
}

/**
 * Format value based on specified format type
 */
const formatValue = (
  value: number | string,
  format: ValueFormat,
  currencySymbol: string
): string => {
  if (typeof value === 'string') return value;

  switch (format) {
    case 'percentage':
      return `${value}%`;
    case 'currency':
      return `${currencySymbol}${value.toLocaleString()}`;
    case 'duration':
      // Format as hours and minutes
      const hours = Math.floor(value / 60);
      const minutes = value % 60;
      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      }
      return `${minutes}m`;
    case 'number':
    default:
      return value.toLocaleString();
  }
};

/**
 * Determine trend direction from value
 */
const getTrendDirection = (trend: number): TrendDirection => {
  if (trend > 0) return 'up';
  if (trend < 0) return 'down';
  return 'neutral';
};

/**
 * Up Arrow Icon
 */
const TrendUpIcon: React.FC = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 16 16"
    fill="none"
    aria-hidden="true"
    className={styles['trend-icon']}
  >
    <path
      d="M8 4L12 8L10.6 9.4L9 7.8V12H7V7.8L5.4 9.4L4 8L8 4Z"
      fill="currentColor"
    />
  </svg>
);

/**
 * Down Arrow Icon
 */
const TrendDownIcon: React.FC = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 16 16"
    fill="none"
    aria-hidden="true"
    className={styles['trend-icon']}
  >
    <path
      d="M8 12L4 8L5.4 6.6L7 8.2V4H9V8.2L10.6 6.6L12 8L8 12Z"
      fill="currentColor"
    />
  </svg>
);

/**
 * StatCard Component
 *
 * WHY THIS APPROACH:
 * - Combines Card with stat display for consistent styling
 * - Trend indicator provides at-a-glance performance info
 * - Color coding follows UX conventions (green=good, red=bad)
 * - Flexible formatting supports various metric types
 * - Screen reader support for accessibility
 *
 * @example Basic usage
 * ```tsx
 * <StatCard
 *   value={42}
 *   label="Active Courses"
 *   trend={12.5}
 *   trendLabel="vs last month"
 * />
 * ```
 *
 * @example With percentage format
 * ```tsx
 * <StatCard
 *   value={85}
 *   label="Completion Rate"
 *   valueFormat="percentage"
 *   trend={-3.2}
 * />
 * ```
 */
export const StatCard: React.FC<StatCardProps> = ({
  value,
  label,
  trend,
  trendDirection,
  trendLabel = 'vs last period',
  valueFormat = 'number',
  currencySymbol = '$',
  icon,
  variant = 'elevated',
  className,
  ariaDescription,
}) => {
  const formattedValue = formatValue(value, valueFormat, currencySymbol);
  const direction = trendDirection ?? (trend !== undefined ? getTrendDirection(trend) : 'neutral');
  const hasTrend = trend !== undefined;

  // Generate accessible description
  const accessibleDescription = ariaDescription ?? (() => {
    let desc = `${label}: ${formattedValue}`;
    if (hasTrend) {
      const trendText = trend > 0 ? `up ${Math.abs(trend)}%` : trend < 0 ? `down ${Math.abs(trend)}%` : 'unchanged';
      desc += `, ${trendText} ${trendLabel}`;
    }
    return desc;
  })();

  const classes = [styles['stat-card'], className].filter(Boolean).join(' ');

  return (
    <Card
      variant={variant}
      padding="medium"
      className={classes}
      data-testid="stat-card"
    >
      <div
        className={styles['stat-content']}
        role="group"
        aria-label={accessibleDescription}
      >
        {/* Icon (optional) */}
        {icon && (
          <div className={styles['stat-icon']} aria-hidden="true">
            {icon}
          </div>
        )}

        {/* Main Value */}
        <div className={styles['stat-value']}>
          {formattedValue}
        </div>

        {/* Label */}
        <div className={styles['stat-label']}>
          {label}
        </div>

        {/* Trend Indicator */}
        {hasTrend && (
          <div
            className={`${styles['trend-indicator']} ${styles[`trend-${direction}`]}`}
            aria-label={`Trend: ${Math.abs(trend)}% ${direction} ${trendLabel}`}
          >
            {direction === 'up' && <TrendUpIcon />}
            {direction === 'down' && <TrendDownIcon />}
            <span className={styles['trend-value']}>
              {direction !== 'neutral' && (direction === 'up' ? '+' : '')}
              {trend.toFixed(1)}%
            </span>
            <span className={styles['trend-label']}>
              {trendLabel}
            </span>
          </div>
        )}
      </div>
    </Card>
  );
};

StatCard.displayName = 'StatCard';
