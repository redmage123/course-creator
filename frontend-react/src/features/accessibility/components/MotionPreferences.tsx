/**
 * Motion Preferences Component
 *
 * BUSINESS CONTEXT:
 * Allows users to control animation and motion effects. Supports users with
 * vestibular disorders or motion sensitivity. Implements WCAG 2.3.3
 * (Animation from Interactions).
 *
 * TECHNICAL IMPLEMENTATION:
 * Radio button group for motion preference selection. Updates CSS custom
 * properties to control animation durations.
 *
 * WCAG 2.1 AA Compliance:
 * - 2.3.3 Animation from Interactions (Level AAA)
 * - Respects prefers-reduced-motion
 * - Keyboard accessible
 */

import React from 'react';
import { MotionPreference } from '@services/accessibilityService';
import styles from './MotionPreferences.module.css';

/**
 * Motion Preferences Props
 */
export interface MotionPreferencesProps {
  /** Current motion preference */
  value: MotionPreference;
  /** Callback when motion preference changes */
  onChange: (value: MotionPreference) => void;
  /** Whether control is disabled */
  disabled?: boolean;
}

/**
 * Motion Preferences Component
 */
export const MotionPreferences: React.FC<MotionPreferencesProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  const options = [
    {
      value: MotionPreference.NO_PREFERENCE,
      label: 'Full Motion',
      description: 'Use all animations and transitions',
    },
    {
      value: MotionPreference.REDUCE,
      label: 'Reduced Motion',
      description: 'Minimize non-essential motion effects',
    },
    {
      value: MotionPreference.NO_MOTION,
      label: 'No Motion',
      description: 'Disable all animations and transitions',
    },
  ];

  return (
    <div className={styles.container}>
      <fieldset className={styles.fieldset} disabled={disabled}>
        <legend className={styles.legend}>
          Motion & Animation
          <span className={styles.helpText}>
            Control motion effects for comfort and accessibility
          </span>
        </legend>

        <div className={styles.options} role="radiogroup" aria-label="Motion preference options">
          {options.map((option) => (
            <label
              key={option.value}
              className={`${styles.option} ${value === option.value ? styles.selected : ''}`}
            >
              <input
                type="radio"
                name="motion-preference"
                value={option.value}
                checked={value === option.value}
                onChange={() => onChange(option.value)}
                disabled={disabled}
                className={styles.radio}
                aria-describedby={`motion-${option.value}-desc`}
              />
              <span className={styles.optionLabel}>
                {option.label}
                <span
                  id={`motion-${option.value}-desc`}
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
