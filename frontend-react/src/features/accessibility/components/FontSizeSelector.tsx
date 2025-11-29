/**
 * Font Size Selector Component
 *
 * BUSINESS CONTEXT:
 * Allows users to adjust text size for better readability. Supports users with
 * low vision or reading difficulties. Implements WCAG 2.1.4.4 (Resize text).
 *
 * TECHNICAL IMPLEMENTATION:
 * Radio button group for selecting font size preference. Updates CSS custom
 * properties for immediate visual feedback.
 *
 * WCAG 2.1 AA Compliance:
 * - 1.4.4 Resize text (Level AA)
 * - Keyboard accessible
 * - Clear labels and descriptions
 */

import React from 'react';
import { FontSizePreference } from '@services/accessibilityService';
import styles from './FontSizeSelector.module.css';

/**
 * Font Size Selector Props
 */
export interface FontSizeSelectorProps {
  /** Current font size preference */
  value: FontSizePreference;
  /** Callback when font size changes */
  onChange: (value: FontSizePreference) => void;
  /** Whether control is disabled */
  disabled?: boolean;
}

/**
 * Font Size Selector Component
 *
 * @param value - Current selected font size
 * @param onChange - Change handler
 * @param disabled - Whether control is disabled
 */
export const FontSizeSelector: React.FC<FontSizeSelectorProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  const options = [
    { value: FontSizePreference.DEFAULT, label: 'Default', size: '100%' },
    { value: FontSizePreference.LARGE, label: 'Large', size: '125%' },
    { value: FontSizePreference.EXTRA_LARGE, label: 'Extra Large', size: '150%' },
    { value: FontSizePreference.HUGE, label: 'Huge', size: '200%' },
  ];

  return (
    <div className={styles.container}>
      <fieldset className={styles.fieldset} disabled={disabled}>
        <legend className={styles.legend}>
          Font Size
          <span className={styles.helpText}>
            Adjust text size for better readability
          </span>
        </legend>

        <div className={styles.options} role="radiogroup" aria-label="Font size options">
          {options.map((option) => (
            <label
              key={option.value}
              className={`${styles.option} ${value === option.value ? styles.selected : ''}`}
            >
              <input
                type="radio"
                name="font-size"
                value={option.value}
                checked={value === option.value}
                onChange={() => onChange(option.value)}
                disabled={disabled}
                className={styles.radio}
                aria-describedby={`font-size-${option.value}-desc`}
              />
              <span className={styles.optionLabel}>
                {option.label}
                <span
                  id={`font-size-${option.value}-desc`}
                  className={styles.optionSize}
                >
                  {option.size}
                </span>
              </span>
            </label>
          ))}
        </div>
      </fieldset>
    </div>
  );
};
