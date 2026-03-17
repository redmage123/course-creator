/**
 * Focus Indicator Component
 *
 * BUSINESS CONTEXT:
 * Allows users to customize keyboard focus indicator visibility and style.
 * Essential for keyboard navigation. Implements WCAG 2.4.7 (Focus Visible).
 *
 * TECHNICAL IMPLEMENTATION:
 * Radio button group for focus indicator style. Updates CSS custom properties
 * for immediate visual feedback.
 *
 * WCAG 2.1 AA Compliance:
 * - 2.4.7 Focus Visible (Level AA)
 * - Clear focus indicators
 * - Keyboard accessible
 */

import React from 'react';
import { FocusIndicatorStyle } from '@services/accessibilityService';
import styles from './FocusIndicator.module.css';

/**
 * Focus Indicator Props
 */
export interface FocusIndicatorProps {
  /** Current focus indicator style */
  value: FocusIndicatorStyle;
  /** Callback when focus indicator style changes */
  onChange: (value: FocusIndicatorStyle) => void;
  /** Whether control is disabled */
  disabled?: boolean;
}

/**
 * Focus Indicator Component
 */
export const FocusIndicator: React.FC<FocusIndicatorProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  const options = [
    {
      value: FocusIndicatorStyle.DEFAULT,
      label: 'Default',
      description: '2px outline',
    },
    {
      value: FocusIndicatorStyle.ENHANCED,
      label: 'Enhanced',
      description: '3px outline with offset',
    },
    {
      value: FocusIndicatorStyle.HIGH_VISIBILITY,
      label: 'High Visibility',
      description: '4px outline with glow',
    },
  ];

  return (
    <div className={styles.container}>
      <fieldset className={styles.fieldset} disabled={disabled}>
        <legend className={styles.legend}>
          Focus Indicator Style
          <span className={styles.helpText}>
            Customize keyboard focus visibility
          </span>
        </legend>

        <div className={styles.options} role="radiogroup" aria-label="Focus indicator style options">
          {options.map((option) => (
            <label
              key={option.value}
              className={`${styles.option} ${value === option.value ? styles.selected : ''}`}
            >
              <input
                type="radio"
                name="focus-indicator"
                value={option.value}
                checked={value === option.value}
                onChange={() => onChange(option.value)}
                disabled={disabled}
                className={styles.radio}
                aria-describedby={`focus-indicator-${option.value}-desc`}
              />
              <span className={styles.optionLabel}>
                {option.label}
                <span
                  id={`focus-indicator-${option.value}-desc`}
                  className={styles.optionDescription}
                >
                  {option.description}
                </span>
              </span>
            </label>
          ))}
        </div>
      </fieldset>
    </div>
  );
};
