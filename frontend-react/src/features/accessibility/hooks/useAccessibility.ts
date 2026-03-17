/**
 * useAccessibility Hook
 *
 * BUSINESS CONTEXT:
 * Provides convenient access to accessibility features and preferences.
 * Simplifies component integration with accessibility system.
 *
 * TECHNICAL IMPLEMENTATION:
 * Re-exports context hook with additional helper methods.
 * Provides typed access to accessibility state and actions.
 *
 * WCAG 2.1 AA Compliance:
 * - Enables components to respect user accessibility preferences
 * - Provides helpers for creating accessible experiences
 */

import { useAccessibilityContext } from '../context/AccessibilityContext';

export { useAccessibilityContext as useAccessibility };
