/**
 * Color Scheme Selector Component
 *
 * BUSINESS CONTEXT:
 * Allows users to select color theme (light, dark, high contrast). Supports
 * users with light sensitivity, color vision deficiencies, or low vision.
 * Implements WCAG 2.1.4.3 (Contrast minimum).
 *
 * TECHNICAL IMPLEMENTATION:
 * Radio buttons for color scheme selection, checkbox for high contrast mode.
 * Updates document attribute for immediate theme change.
 *
 * WCAG 2.1 AA Compliance:
 * - 1.4.3 Contrast (Minimum) (Level AA)
 * - 1.4.8 Visual Presentation (Level AAA)
 * - Keyboard accessible
 */

import React from 'react';
import { ColorSchemePreference } from '@services/accessibilityService';
import styles from './ColorSchemeSelector.module.css';

/**
 * Color Scheme Selector Props
 */
export interface ColorSchemeSelectorProps {
  /** Current color scheme */
  value: ColorSchemePreference;
  /** High contrast mode enabled */
  highContrastMode: boolean;
  /** Callback when color scheme changes */
  onColorSchemeChange: (value: ColorSchemePreference) => void;
  /** Callback when high contrast mode changes */
  onHighContrastChange: (enabled: boolean) => void;
  /** Whether control is disabled */
  disabled?: boolean;
}

/**
 * Color Scheme Selector Component
 */
export const ColorSchemeSelector: React.FC<ColorSchemeSelectorProps> = ({
  value,
  highContrastMode,
  onColorSchemeChange,
  onHighContrastChange,
  disabled = false,
}) => {
  const options = [
    { value: ColorSchemePreference.SYSTEM, label: 'System', description: 'Follow system preference' },
    { value: ColorSchemePreference.LIGHT, label: 'Light', description: 'Light background' },
    { value: ColorSchemePreference.DARK, label: 'Dark', description: 'Dark background' },
    { value: ColorSchemePreference.HIGH_CONTRAST, label: 'High Contrast', description: 'Maximum contrast' },
  ];

  return (
    <div className={styles.container}>
      {/* Color Scheme */}
      <fieldset className={styles.fieldset} disabled={disabled}>
        <legend className={styles.legend}>
          Color Scheme
          <span className={styles.helpText}>
            Choose your preferred color theme
          </span>
        </legend>

        <div className={styles.options} role="radiogroup" aria-label="Color scheme options">
          {options.map((option) => (
            <label
              key={option.value}
              className={`${styles.option} ${value === option.value ? styles.selected : ''}`}
            >
              <input
                type="radio"
                name="color-scheme"
                value={option.value}
                checked={value === option.value}
                onChange={() => onColorSchemeChange(option.value)}
                disabled={disabled}
                className={styles.radio}
                aria-describedby={`color-scheme-${option.value}-desc`}
              />
              <span className={styles.optionLabel}>
                {option.label}
                <span
                  id={`color-scheme-${option.value}-desc`}
                  className={styles.optionDescription}
                >
                  {option.description}
                </span>
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      {/* High Contrast Mode */}
      <div className={styles.highContrast}>
        <label htmlFor="high-contrast-mode" className={styles.checkboxLabel}>
          <input
            type="checkbox"
            id="high-contrast-mode"
            checked={highContrastMode}
            onChange={(e) => onHighContrastChange(e.target.checked)}
            disabled={disabled}
            className={styles.checkbox}
          />
          <span className={styles.checkboxText}>
            Enable High Contrast Mode
            <span className={styles.checkboxHelp}>
              Increases contrast beyond standard levels (WCAG AAA)
            </span>
          </span>
        </label>
      </div>
    </div>
  );
};
