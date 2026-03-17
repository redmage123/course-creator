/**
 * Accessibility Settings Page
 *
 * BUSINESS CONTEXT:
 * Comprehensive accessibility settings page where users can customize their
 * accessibility preferences including font size, color scheme, motion, keyboard
 * navigation, and screen reader optimizations. Implements WCAG 2.1 AA guidelines.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses AccessibilityContext for state management. Organizes settings into logical
 * sections with clear labels and descriptions. Provides immediate visual feedback
 * for all changes.
 *
 * WCAG 2.1 AA Compliance:
 * - Keyboard accessible throughout
 * - ARIA labels for all controls
 * - Clear visual feedback
 * - Logical focus order
 * - High contrast support
 */

import React, { useState } from 'react';
import { useAccessibility } from './hooks/useAccessibility';
import { FontSizeSelector } from './components/FontSizeSelector';
import { ColorSchemeSelector } from './components/ColorSchemeSelector';
import { MotionPreferences } from './components/MotionPreferences';
import { KeyboardShortcutsPanel } from './components/KeyboardShortcutsPanel';
import { SkipLinks } from './components/SkipLinks';
import { FocusIndicator } from './components/FocusIndicator';
import { ScreenReaderAnnouncer } from './components/ScreenReaderAnnouncer';
import styles from './AccessibilitySettings.module.css';

/**
 * Accessibility Settings Component
 *
 * BUSINESS LOGIC:
 * Provides comprehensive accessibility customization interface.
 * Organizes settings into logical sections for easy navigation.
 * Saves changes automatically with visual feedback.
 *
 * @returns Accessibility settings page
 */
export const AccessibilitySettings: React.FC = () => {
  const {
    preferences,
    isLoading,
    error,
    updatePreferences,
    resetPreferences,
    announce,
  } = useAccessibility();

  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  /**
   * Handle preference update
   *
   * BUSINESS LOGIC:
   * Updates a single preference with loading and success feedback.
   *
   * @param updates - Preferences to update
   */
  const handleUpdate = async (updates: Partial<typeof preferences>): Promise<void> => {
    if (!preferences) return;

    setIsSaving(true);
    setSaveMessage(null);

    try {
      await updatePreferences(updates);
      setSaveMessage('Settings saved successfully');
      announce('Settings saved successfully');

      // Clear success message after 3 seconds
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (err: any) {
      setSaveMessage(`Error: ${err.message}`);
      announce('Failed to save settings', 'assertive');
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Handle reset to defaults
   *
   * BUSINESS LOGIC:
   * Resets all preferences to platform defaults with confirmation.
   */
  const handleReset = async (): Promise<void> => {
    if (!confirm('Reset all accessibility settings to defaults? This cannot be undone.')) {
      return;
    }

    setIsSaving(true);
    setSaveMessage(null);

    try {
      await resetPreferences();
      setSaveMessage('Settings reset to defaults');
      announce('Settings reset to defaults');

      setTimeout(() => setSaveMessage(null), 3000);
    } catch (err: any) {
      setSaveMessage(`Error: ${err.message}`);
      announce('Failed to reset settings', 'assertive');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className={styles.container} role="main" aria-busy="true">
        <div className={styles.loading}>
          <div className={styles.spinner} aria-label="Loading accessibility settings"></div>
          <p>Loading accessibility settings...</p>
        </div>
      </div>
    );
  }

  if (!preferences) {
    return (
      <div className={styles.container} role="main">
        <div className={styles.error} role="alert">
          <h1>Error Loading Settings</h1>
          <p>{error || 'Failed to load accessibility preferences'}</p>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Skip Links */}
      <SkipLinks />

      {/* Main Content */}
      <div className={styles.container} role="main" id="main-content">
        {/* Page Header */}
        <header className={styles.header}>
          <h1 className={styles.title}>Accessibility Settings</h1>
          <p className={styles.description}>
            Customize your accessibility preferences to personalize your learning experience.
            All changes are saved automatically.
          </p>
        </header>

        {/* Save Status */}
        {saveMessage && (
          <div
            className={`${styles.saveStatus} ${saveMessage.startsWith('Error') ? styles.error : styles.success}`}
            role="status"
            aria-live="polite"
          >
            {saveMessage}
          </div>
        )}

        {/* Settings Sections */}
        <div className={styles.sections}>
          {/* Visual Preferences Section */}
          <section className={styles.section} aria-labelledby="visual-heading">
            <h2 id="visual-heading" className={styles.sectionTitle}>
              Visual Preferences
            </h2>
            <p className={styles.sectionDescription}>
              Customize text size, color scheme, and visual appearance
            </p>

            <div className={styles.controls}>
              {/* Font Size */}
              <FontSizeSelector
                value={preferences.fontSize}
                onChange={(fontSize) => handleUpdate({ fontSize })}
                disabled={isSaving}
              />

              {/* Color Scheme */}
              <ColorSchemeSelector
                value={preferences.colorScheme}
                highContrastMode={preferences.highContrastMode}
                onColorSchemeChange={(colorScheme) => handleUpdate({ colorScheme })}
                onHighContrastChange={(highContrastMode) => handleUpdate({ highContrastMode })}
                disabled={isSaving}
              />

              {/* Focus Indicator */}
              <FocusIndicator
                value={preferences.focusIndicatorStyle}
                onChange={(focusIndicatorStyle) => handleUpdate({ focusIndicatorStyle })}
                disabled={isSaving}
              />

              {/* Transparency */}
              <div className={styles.control}>
                <label htmlFor="reduce-transparency" className={styles.label}>
                  Reduce Transparency
                  <span className={styles.helpText}>
                    Reduces transparency effects for better visibility
                  </span>
                </label>
                <input
                  type="checkbox"
                  id="reduce-transparency"
                  checked={preferences.reduceTransparency}
                  onChange={(e) => handleUpdate({ reduceTransparency: e.target.checked })}
                  disabled={isSaving}
                  className={styles.checkbox}
                />
              </div>
            </div>
          </section>

          {/* Motion Preferences Section */}
          <section className={styles.section} aria-labelledby="motion-heading">
            <h2 id="motion-heading" className={styles.sectionTitle}>
              Motion & Animation
            </h2>
            <p className={styles.sectionDescription}>
              Control animations and motion effects
            </p>

            <div className={styles.controls}>
              <MotionPreferences
                value={preferences.motionPreference}
                onChange={(motionPreference) => handleUpdate({ motionPreference })}
                disabled={isSaving}
              />
            </div>
          </section>

          {/* Keyboard Navigation Section */}
          <section className={styles.section} aria-labelledby="keyboard-heading">
            <h2 id="keyboard-heading" className={styles.sectionTitle}>
              Keyboard Navigation
            </h2>
            <p className={styles.sectionDescription}>
              Configure keyboard shortcuts and navigation
            </p>

            <div className={styles.controls}>
              {/* Keyboard Shortcuts Enabled */}
              <div className={styles.control}>
                <label htmlFor="keyboard-shortcuts" className={styles.label}>
                  Enable Keyboard Shortcuts
                  <span className={styles.helpText}>
                    Enable custom keyboard shortcuts for faster navigation
                  </span>
                </label>
                <input
                  type="checkbox"
                  id="keyboard-shortcuts"
                  checked={preferences.keyboardShortcutsEnabled}
                  onChange={(e) => handleUpdate({ keyboardShortcutsEnabled: e.target.checked })}
                  disabled={isSaving}
                  className={styles.checkbox}
                />
              </div>

              {/* Skip Links Visible */}
              <div className={styles.control}>
                <label htmlFor="skip-links-visible" className={styles.label}>
                  Always Show Skip Links
                  <span className={styles.helpText}>
                    Keep skip navigation links always visible (normally shown on focus)
                  </span>
                </label>
                <input
                  type="checkbox"
                  id="skip-links-visible"
                  checked={preferences.skipLinksAlwaysVisible}
                  onChange={(e) => handleUpdate({ skipLinksAlwaysVisible: e.target.checked })}
                  disabled={isSaving}
                  className={styles.checkbox}
                />
              </div>

              {/* Focus Highlight */}
              <div className={styles.control}>
                <label htmlFor="focus-highlight" className={styles.label}>
                  Enable Focus Highlights
                  <span className={styles.helpText}>
                    Show visual highlight for focused elements
                  </span>
                </label>
                <input
                  type="checkbox"
                  id="focus-highlight"
                  checked={preferences.focusHighlightEnabled}
                  onChange={(e) => handleUpdate({ focusHighlightEnabled: e.target.checked })}
                  disabled={isSaving}
                  className={styles.checkbox}
                />
              </div>

              {/* Keyboard Shortcuts Panel */}
              {preferences.keyboardShortcutsEnabled && (
                <KeyboardShortcutsPanel />
              )}
            </div>
          </section>

          {/* Screen Reader Section */}
          <section className={styles.section} aria-labelledby="screen-reader-heading">
            <h2 id="screen-reader-heading" className={styles.sectionTitle}>
              Screen Reader
            </h2>
            <p className={styles.sectionDescription}>
              Optimize for screen reader users
            </p>

            <div className={styles.controls}>
              {/* Screen Reader Optimizations */}
              <div className={styles.control}>
                <label htmlFor="screen-reader-optimizations" className={styles.label}>
                  Enable Screen Reader Optimizations
                  <span className={styles.helpText}>
                    Optimizes interface for screen reader users
                  </span>
                </label>
                <input
                  type="checkbox"
                  id="screen-reader-optimizations"
                  checked={preferences.screenReaderOptimizations}
                  onChange={(e) => handleUpdate({ screenReaderOptimizations: e.target.checked })}
                  disabled={isSaving}
                  className={styles.checkbox}
                />
              </div>

              {/* Announce Page Changes */}
              <div className={styles.control}>
                <label htmlFor="announce-page-changes" className={styles.label}>
                  Announce Page Changes
                  <span className={styles.helpText}>
                    Announce when navigating to new pages
                  </span>
                </label>
                <input
                  type="checkbox"
                  id="announce-page-changes"
                  checked={preferences.announcePageChanges}
                  onChange={(e) => handleUpdate({ announcePageChanges: e.target.checked })}
                  disabled={isSaving}
                  className={styles.checkbox}
                />
              </div>

              {/* Verbose Announcements */}
              <div className={styles.control}>
                <label htmlFor="verbose-announcements" className={styles.label}>
                  Verbose Announcements
                  <span className={styles.helpText}>
                    Provide more detailed screen reader announcements
                  </span>
                </label>
                <input
                  type="checkbox"
                  id="verbose-announcements"
                  checked={preferences.verboseAnnouncements}
                  onChange={(e) => handleUpdate({ verboseAnnouncements: e.target.checked })}
                  disabled={isSaving}
                  className={styles.checkbox}
                />
              </div>
            </div>
          </section>

          {/* Media Preferences Section */}
          <section className={styles.section} aria-labelledby="media-heading">
            <h2 id="media-heading" className={styles.sectionTitle}>
              Media Preferences
            </h2>
            <p className={styles.sectionDescription}>
              Configure audio and video settings
            </p>

            <div className={styles.controls}>
              {/* Auto-play Media */}
              <div className={styles.control}>
                <label htmlFor="auto-play-media" className={styles.label}>
                  Auto-play Media
                  <span className={styles.helpText}>
                    Automatically play videos and audio when loaded
                  </span>
                </label>
                <input
                  type="checkbox"
                  id="auto-play-media"
                  checked={preferences.autoPlayMedia}
                  onChange={(e) => handleUpdate({ autoPlayMedia: e.target.checked })}
                  disabled={isSaving}
                  className={styles.checkbox}
                />
              </div>

              {/* Captions Enabled */}
              <div className={styles.control}>
                <label htmlFor="captions-enabled" className={styles.label}>
                  Enable Captions
                  <span className={styles.helpText}>
                    Show captions for video content by default
                  </span>
                </label>
                <input
                  type="checkbox"
                  id="captions-enabled"
                  checked={preferences.captionsEnabled}
                  onChange={(e) => handleUpdate({ captionsEnabled: e.target.checked })}
                  disabled={isSaving}
                  className={styles.checkbox}
                />
              </div>

              {/* Audio Descriptions */}
              <div className={styles.control}>
                <label htmlFor="audio-descriptions" className={styles.label}>
                  Enable Audio Descriptions
                  <span className={styles.helpText}>
                    Enable audio descriptions for video content
                  </span>
                </label>
                <input
                  type="checkbox"
                  id="audio-descriptions"
                  checked={preferences.audioDescriptionsEnabled}
                  onChange={(e) => handleUpdate({ audioDescriptionsEnabled: e.target.checked })}
                  disabled={isSaving}
                  className={styles.checkbox}
                />
              </div>
            </div>
          </section>

          {/* Timing Preferences Section */}
          <section className={styles.section} aria-labelledby="timing-heading">
            <h2 id="timing-heading" className={styles.sectionTitle}>
              Timing & Timeouts
            </h2>
            <p className={styles.sectionDescription}>
              Adjust timing and auto-refresh settings
            </p>

            <div className={styles.controls}>
              {/* Extend Timeouts */}
              <div className={styles.control}>
                <label htmlFor="extend-timeouts" className={styles.label}>
                  Extend Session Timeouts
                  <span className={styles.helpText}>
                    Extend session timeout durations
                  </span>
                </label>
                <input
                  type="checkbox"
                  id="extend-timeouts"
                  checked={preferences.extendTimeouts}
                  onChange={(e) => handleUpdate({ extendTimeouts: e.target.checked })}
                  disabled={isSaving}
                  className={styles.checkbox}
                />
              </div>

              {/* Timeout Multiplier */}
              {preferences.extendTimeouts && (
                <div className={styles.control}>
                  <label htmlFor="timeout-multiplier" className={styles.label}>
                    Timeout Extension (1.0x to 5.0x)
                    <span className={styles.helpText}>
                      Current: {preferences.timeoutMultiplier.toFixed(1)}x
                    </span>
                  </label>
                  <input
                    type="range"
                    id="timeout-multiplier"
                    min="1.0"
                    max="5.0"
                    step="0.5"
                    value={preferences.timeoutMultiplier}
                    onChange={(e) => handleUpdate({ timeoutMultiplier: parseFloat(e.target.value) })}
                    disabled={isSaving}
                    className={styles.slider}
                    aria-valuemin={1.0}
                    aria-valuemax={5.0}
                    aria-valuenow={preferences.timeoutMultiplier}
                  />
                </div>
              )}

              {/* Disable Auto-refresh */}
              <div className={styles.control}>
                <label htmlFor="disable-auto-refresh" className={styles.label}>
                  Disable Auto-refresh
                  <span className={styles.helpText}>
                    Prevent automatic page refresh
                  </span>
                </label>
                <input
                  type="checkbox"
                  id="disable-auto-refresh"
                  checked={preferences.disableAutoRefresh}
                  onChange={(e) => handleUpdate({ disableAutoRefresh: e.target.checked })}
                  disabled={isSaving}
                  className={styles.checkbox}
                />
              </div>
            </div>
          </section>
        </div>

        {/* Reset Button */}
        <div className={styles.actions}>
          <button
            type="button"
            onClick={handleReset}
            disabled={isSaving}
            className={styles.resetButton}
            aria-label="Reset all accessibility settings to defaults"
          >
            Reset to Defaults
          </button>
        </div>
      </div>

      {/* Screen Reader Announcer */}
      <ScreenReaderAnnouncer />
    </>
  );
};

export default AccessibilitySettings;
