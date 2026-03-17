/**
 * Accessibility Feature Module Exports
 *
 * BUSINESS CONTEXT:
 * Central export point for all accessibility-related components, hooks, and
 * utilities. Provides WCAG 2.1 AA compliant accessibility features including
 * user preferences, keyboard navigation, screen reader support, and color
 * contrast validation.
 *
 * TECHNICAL IMPLEMENTATION:
 * Re-exports all accessibility components, hooks, and context providers for
 * easy consumption throughout the application.
 *
 * USAGE:
 * ```tsx
 * import {
 *   AccessibilityProvider,
 *   useAccessibility,
 *   AccessibilitySettings,
 *   SkipLinks,
 * } from '@features/accessibility';
 * ```
 */

// Main Page
export { default as AccessibilitySettings } from './AccessibilitySettings';

// Context & Provider
export {
  AccessibilityProvider,
  useAccessibilityContext,
} from './context/AccessibilityContext';

// Hooks
export { useAccessibility } from './hooks/useAccessibility';
export {
  useKeyboardNavigation,
  type UseKeyboardNavigationReturn,
  type KeyboardNavigationOptions,
  type KeyboardEventHandler,
} from './hooks/useKeyboardNavigation';

// Components
export { FontSizeSelector } from './components/FontSizeSelector';
export type { FontSizeSelectorProps } from './components/FontSizeSelector';

export { ColorSchemeSelector } from './components/ColorSchemeSelector';
export type { ColorSchemeSelectorProps } from './components/ColorSchemeSelector';

export { MotionPreferences } from './components/MotionPreferences';
export type { MotionPreferencesProps } from './components/MotionPreferences';

export { KeyboardShortcutsPanel } from './components/KeyboardShortcutsPanel';

export { SkipLinks } from './components/SkipLinks';

export { FocusIndicator } from './components/FocusIndicator';
export type { FocusIndicatorProps } from './components/FocusIndicator';

export { ScreenReaderAnnouncer } from './components/ScreenReaderAnnouncer';

// Re-export types from service for convenience
export type {
  AccessibilityPreference,
  KeyboardShortcut,
  ScreenReaderAnnouncement,
  ColorContrastResult,
} from '@services/accessibilityService';

export {
  FontSizePreference,
  ColorSchemePreference,
  MotionPreference,
  FocusIndicatorStyle,
  ColorContrastLevel,
} from '@services/accessibilityService';
