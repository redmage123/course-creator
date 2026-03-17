/**
 * Accessibility Service
 *
 * BUSINESS CONTEXT:
 * Manages user accessibility preferences, color contrast validation, keyboard shortcuts,
 * and screen reader support for WCAG 2.1 AA compliance. Enables personalized accessibility
 * features for users with disabilities including visual impairments, motor disabilities,
 * cognitive disabilities, and hearing impairments.
 *
 * TECHNICAL IMPLEMENTATION:
 * Communicates with organization-management service (port 8001) for accessibility
 * preferences and audit management. Implements client-side accessibility helpers
 * for immediate user experience enhancements.
 *
 * WCAG 2.1 AA Compliance:
 * - Font size adjustments (1.4.4 Resize text)
 * - Color contrast validation (1.4.3 Contrast minimum)
 * - Motion reduction (2.3.3 Animation from Interactions)
 * - Keyboard navigation (2.1.1 Keyboard)
 * - Screen reader support (4.1.3 Status Messages)
 * - Focus indicators (2.4.7 Focus Visible)
 */

import { apiClient } from './apiClient';

// =============================================================================
// TYPES - Accessibility Preferences
// =============================================================================

/**
 * Font Size Preference Options
 *
 * What: User-selectable font size settings
 * Where: Applied globally to all text content
 * Why: Supports users with low vision or reading difficulties
 */
export enum FontSizePreference {
  DEFAULT = 'default',     // Browser default (100%)
  LARGE = 'large',         // 125% scaling
  EXTRA_LARGE = 'xlarge',  // 150% scaling
  HUGE = 'huge',           // 200% scaling
}

/**
 * Color Scheme Preference Options
 *
 * What: User-selectable color theme settings
 * Where: Applied globally via CSS custom properties
 * Why: Supports users with light sensitivity or color vision deficiencies
 */
export enum ColorSchemePreference {
  SYSTEM = 'system',           // Follow OS preference
  LIGHT = 'light',             // Light background, dark text
  DARK = 'dark',               // Dark background, light text
  HIGH_CONTRAST = 'high_contrast', // Maximum contrast mode
}

/**
 * Motion Preference Options
 *
 * What: Animation and motion control settings
 * Where: Applied to CSS transitions and animations
 * Why: Supports users with vestibular disorders or motion sensitivity
 */
export enum MotionPreference {
  NO_PREFERENCE = 'no_preference',  // Use animations normally
  REDUCE = 'reduce',                 // Minimize non-essential motion
  NO_MOTION = 'no_motion',           // Disable all animations
}

/**
 * Focus Indicator Style Options
 *
 * What: Keyboard focus indicator visual styles
 * Where: Applied to all interactive elements
 * Why: Ensures keyboard users can see their current focus position
 */
export enum FocusIndicatorStyle {
  DEFAULT = 'default',               // Standard 2px outline
  ENHANCED = 'enhanced',             // 3px outline with offset
  HIGH_VISIBILITY = 'high_visibility', // 4px solid with glow effect
}

/**
 * User Accessibility Preferences Interface
 *
 * What: Complete set of user accessibility customization options
 * Where: Stored in database and session storage
 * Why: Enables personalized accessibility experience for all users
 */
export interface AccessibilityPreference {
  id: string;
  userId: string;

  // Visual Preferences
  fontSize: FontSizePreference;
  colorScheme: ColorSchemePreference;
  focusIndicatorStyle: FocusIndicatorStyle;
  highContrastMode: boolean;

  // Motion Preferences
  motionPreference: MotionPreference;
  reduceTransparency: boolean;

  // Screen Reader Optimizations
  screenReaderOptimizations: boolean;
  announcePageChanges: boolean;
  verboseAnnouncements: boolean;

  // Keyboard Navigation
  keyboardShortcutsEnabled: boolean;
  skipLinksAlwaysVisible: boolean;
  focusHighlightEnabled: boolean;

  // Audio/Visual Preferences
  autoPlayMedia: boolean;
  captionsEnabled: boolean;
  audioDescriptionsEnabled: boolean;

  // Timing Preferences
  extendTimeouts: boolean;
  timeoutMultiplier: number; // 1.0 to 5.0
  disableAutoRefresh: boolean;

  // Metadata
  createdAt: string;
  updatedAt: string;
}

/**
 * Color Contrast Level Requirements
 *
 * What: WCAG 2.1 contrast ratio requirements
 * Where: Design system validation
 * Why: Ensures text readability for users with low vision
 */
export enum ColorContrastLevel {
  NORMAL_TEXT_AA = 'normal_text_aa',       // 4.5:1
  LARGE_TEXT_AA = 'large_text_aa',         // 3:1
  NORMAL_TEXT_AAA = 'normal_text_aaa',     // 7:1
  LARGE_TEXT_AAA = 'large_text_aaa',       // 4.5:1
  UI_COMPONENT = 'ui_component',           // 3:1
}

/**
 * Color Contrast Validation Result
 *
 * What: Result of WCAG color contrast validation
 * Where: Design system and component validation
 * Why: Verifies color combinations meet accessibility standards
 */
export interface ColorContrastResult {
  id: string;
  level: ColorContrastLevel;
  foregroundColor: string; // Hex color code
  backgroundColor: string; // Hex color code
  calculatedRatio: number;
  passes: boolean;
  componentName?: string;
  requiredRatio: number;
}

/**
 * Keyboard Shortcut Configuration
 *
 * What: Platform-wide keyboard navigation shortcuts
 * Where: Global keyboard event handlers
 * Why: Enables efficient keyboard-only navigation
 */
export interface KeyboardShortcut {
  id: string;
  key: string;                // Key code (e.g., "KeyS", "Enter")
  modifiers: string[];        // ["ctrl", "alt", "shift", "meta"]
  action: string;             // Action identifier
  description: string;        // Human-readable description
  context: string;            // Where shortcut is active
  enabled: boolean;
  isCustomizable: boolean;
}

/**
 * Screen Reader Announcement
 *
 * What: Announcement for assistive technology
 * Where: Dynamic content updates and user actions
 * Why: Ensures screen reader users are informed of changes
 */
export interface ScreenReaderAnnouncement {
  id: string;
  message: string;
  politeness: 'polite' | 'assertive' | 'off';
  atomic: boolean;
  relevant: string;
  delayMs: number;
  clearAfterMs?: number;
}

// =============================================================================
// SERVICE CLASS
// =============================================================================

/**
 * Accessibility Service Class
 *
 * WHY THIS APPROACH:
 * - Centralized accessibility feature management
 * - Type-safe API calls with comprehensive error handling
 * - Client-side helpers for immediate UX improvements
 * - WCAG 2.1 AA compliance validation
 */
class AccessibilityService {
  private baseURL = '/organizations'; // organization-management service

  // =========================================================================
  // PREFERENCES MANAGEMENT
  // =========================================================================

  /**
   * Get user accessibility preferences
   *
   * BUSINESS LOGIC:
   * Retrieves user's saved accessibility settings from the backend.
   * If no preferences exist, returns default settings.
   *
   * @param userId - UUID of the user
   * @returns User's accessibility preferences
   */
  async getUserPreferences(userId: string): Promise<AccessibilityPreference> {
    try {
      const response = await apiClient.get<AccessibilityPreference>(
        `${this.baseURL}/users/${userId}/accessibility-preferences`
      );
      return response;
    } catch (error: any) {
      console.error('[AccessibilityService] Failed to get preferences:', error);

      // Return default preferences if not found
      if (error.response?.status === 404) {
        return this.getDefaultPreferences(userId);
      }

      throw error;
    }
  }

  /**
   * Update user accessibility preferences
   *
   * BUSINESS LOGIC:
   * Updates one or more accessibility settings for the user.
   * Validates settings before saving to ensure WCAG compliance.
   *
   * @param userId - UUID of the user
   * @param preferences - Partial preferences to update
   * @returns Updated preferences
   */
  async updateUserPreferences(
    userId: string,
    preferences: Partial<Omit<AccessibilityPreference, 'id' | 'userId' | 'createdAt' | 'updatedAt'>>
  ): Promise<AccessibilityPreference> {
    try {
      // Validate timeout multiplier
      if (preferences.timeoutMultiplier !== undefined) {
        if (preferences.timeoutMultiplier < 1.0 || preferences.timeoutMultiplier > 5.0) {
          throw new Error('Timeout multiplier must be between 1.0 and 5.0');
        }
      }

      const response = await apiClient.put<AccessibilityPreference>(
        `${this.baseURL}/users/${userId}/accessibility-preferences`,
        preferences
      );

      // Apply preferences immediately to document
      this.applyPreferences(response);

      return response;
    } catch (error: any) {
      console.error('[AccessibilityService] Failed to update preferences:', error);
      throw error;
    }
  }

  /**
   * Reset user preferences to defaults
   *
   * BUSINESS LOGIC:
   * Resets all accessibility settings to platform defaults.
   * Useful when user wants to start fresh.
   *
   * @param userId - UUID of the user
   * @returns Default preferences
   */
  async resetUserPreferences(userId: string): Promise<AccessibilityPreference> {
    try {
      const response = await apiClient.post<AccessibilityPreference>(
        `${this.baseURL}/users/${userId}/accessibility-preferences/reset`
      );

      // Apply default preferences to document
      this.applyPreferences(response);

      return response;
    } catch (error: any) {
      console.error('[AccessibilityService] Failed to reset preferences:', error);
      throw error;
    }
  }

  /**
   * Get default accessibility preferences
   *
   * BUSINESS LOGIC:
   * Returns platform default accessibility settings.
   * Used for new users or as fallback.
   *
   * @param userId - UUID of the user
   * @returns Default preferences
   */
  getDefaultPreferences(userId: string): AccessibilityPreference {
    return {
      id: 'default',
      userId,
      fontSize: FontSizePreference.DEFAULT,
      colorScheme: ColorSchemePreference.SYSTEM,
      focusIndicatorStyle: FocusIndicatorStyle.DEFAULT,
      highContrastMode: false,
      motionPreference: MotionPreference.NO_PREFERENCE,
      reduceTransparency: false,
      screenReaderOptimizations: false,
      announcePageChanges: true,
      verboseAnnouncements: false,
      keyboardShortcutsEnabled: true,
      skipLinksAlwaysVisible: false,
      focusHighlightEnabled: true,
      autoPlayMedia: false,
      captionsEnabled: true,
      audioDescriptionsEnabled: false,
      extendTimeouts: false,
      timeoutMultiplier: 1.0,
      disableAutoRefresh: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  }

  /**
   * Apply preferences to document
   *
   * TECHNICAL IMPLEMENTATION:
   * Sets CSS custom properties on document root for immediate effect.
   * Updates ARIA attributes and accessibility settings.
   *
   * @param preferences - Preferences to apply
   */
  applyPreferences(preferences: AccessibilityPreference): void {
    const root = document.documentElement;

    // Font size multiplier
    const fontSizeMultipliers: Record<FontSizePreference, number> = {
      [FontSizePreference.DEFAULT]: 1.0,
      [FontSizePreference.LARGE]: 1.25,
      [FontSizePreference.EXTRA_LARGE]: 1.5,
      [FontSizePreference.HUGE]: 2.0,
    };
    root.style.setProperty('--a11y-font-size-multiplier', fontSizeMultipliers[preferences.fontSize].toString());

    // Animation duration multiplier
    const animationMultipliers: Record<MotionPreference, number> = {
      [MotionPreference.NO_PREFERENCE]: 1.0,
      [MotionPreference.REDUCE]: 0.3,
      [MotionPreference.NO_MOTION]: 0,
    };
    root.style.setProperty('--a11y-animation-multiplier', animationMultipliers[preferences.motionPreference].toString());

    // Transparency reduction
    root.style.setProperty('--a11y-reduce-transparency', preferences.reduceTransparency ? '0.5' : '0');

    // Focus ring width
    const focusWidths: Record<FocusIndicatorStyle, string> = {
      [FocusIndicatorStyle.DEFAULT]: '2px',
      [FocusIndicatorStyle.ENHANCED]: '3px',
      [FocusIndicatorStyle.HIGH_VISIBILITY]: '4px',
    };
    root.style.setProperty('--a11y-focus-ring-width', focusWidths[preferences.focusIndicatorStyle]);

    // Color scheme
    if (preferences.colorScheme !== ColorSchemePreference.SYSTEM) {
      root.setAttribute('data-color-scheme', preferences.colorScheme);
    } else {
      root.removeAttribute('data-color-scheme');
    }

    // High contrast mode
    root.classList.toggle('high-contrast', preferences.highContrastMode);

    // Skip links visibility
    root.classList.toggle('skip-links-always-visible', preferences.skipLinksAlwaysVisible);

    // Store in localStorage for persistence
    localStorage.setItem('accessibility-preferences', JSON.stringify(preferences));
  }

  // =========================================================================
  // COLOR CONTRAST VALIDATION
  // =========================================================================

  /**
   * Validate color contrast ratio
   *
   * BUSINESS LOGIC:
   * Validates that two colors meet WCAG 2.1 contrast requirements.
   * Used in design system and component validation.
   *
   * @param foreground - Foreground hex color (e.g., "#000000")
   * @param background - Background hex color (e.g., "#FFFFFF")
   * @param level - WCAG contrast level requirement
   * @param componentName - Optional component identifier
   * @returns Validation result with pass/fail status
   */
  async validateColorContrast(
    foreground: string,
    background: string,
    level: ColorContrastLevel = ColorContrastLevel.NORMAL_TEXT_AA,
    componentName?: string
  ): Promise<ColorContrastResult> {
    try {
      const response = await apiClient.post<ColorContrastResult>(
        `${this.baseURL}/accessibility/validate-contrast`,
        { foreground, background, level, componentName }
      );
      return response;
    } catch (error: any) {
      console.error('[AccessibilityService] Failed to validate contrast:', error);
      throw error;
    }
  }

  /**
   * Calculate contrast ratio between two colors
   *
   * TECHNICAL IMPLEMENTATION:
   * Client-side calculation of WCAG contrast ratio.
   * Formula: (L1 + 0.05) / (L2 + 0.05) where L is relative luminance.
   *
   * @param foreground - Foreground hex color
   * @param background - Background hex color
   * @returns Contrast ratio (1:1 to 21:1)
   */
  calculateContrastRatio(foreground: string, background: string): number {
    const getLuminance = (hex: string): number => {
      const rgb = this.hexToRgb(hex);
      if (!rgb) return 0;

      const [r, g, b] = rgb.map((val) => {
        const v = val / 255;
        return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
      });

      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };

    const lum1 = getLuminance(foreground);
    const lum2 = getLuminance(background);
    const lighter = Math.max(lum1, lum2);
    const darker = Math.min(lum1, lum2);

    return (lighter + 0.05) / (darker + 0.05);
  }

  /**
   * Convert hex color to RGB
   *
   * @param hex - Hex color code
   * @returns RGB array or null if invalid
   */
  private hexToRgb(hex: string): [number, number, number] | null {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [
      parseInt(result[1], 16),
      parseInt(result[2], 16),
      parseInt(result[3], 16),
    ] : null;
  }

  // =========================================================================
  // KEYBOARD SHORTCUTS MANAGEMENT
  // =========================================================================

  /**
   * Get keyboard shortcuts
   *
   * BUSINESS LOGIC:
   * Retrieves available keyboard shortcuts for the platform.
   * Includes both default and user-customized shortcuts.
   *
   * @param userId - Optional user ID for customized shortcuts
   * @param context - Shortcut context filter (global, modal, form, etc.)
   * @returns List of keyboard shortcuts
   */
  async getKeyboardShortcuts(
    userId?: string,
    context: string = 'global'
  ): Promise<KeyboardShortcut[]> {
    try {
      const params = new URLSearchParams();
      if (userId) params.append('userId', userId);
      if (context) params.append('context', context);

      const response = await apiClient.get<KeyboardShortcut[]>(
        `${this.baseURL}/accessibility/keyboard-shortcuts?${params.toString()}`
      );
      return response;
    } catch (error: any) {
      console.error('[AccessibilityService] Failed to get shortcuts:', error);
      return this.getDefaultShortcuts();
    }
  }

  /**
   * Get default keyboard shortcuts
   *
   * BUSINESS LOGIC:
   * Returns platform default keyboard shortcuts.
   * Follows WCAG 2.1.1 (Keyboard) and 2.1.4 (Character Key Shortcuts).
   *
   * @returns Default keyboard shortcuts
   */
  getDefaultShortcuts(): KeyboardShortcut[] {
    return [
      {
        id: 'skip-to-main',
        key: 'KeyS',
        modifiers: ['alt'],
        action: 'skip_to_main',
        description: 'Skip to main content',
        context: 'global',
        enabled: true,
        isCustomizable: true,
      },
      {
        id: 'skip-to-nav',
        key: 'KeyN',
        modifiers: ['alt'],
        action: 'skip_to_nav',
        description: 'Skip to navigation',
        context: 'global',
        enabled: true,
        isCustomizable: true,
      },
      {
        id: 'open-help',
        key: 'KeyH',
        modifiers: ['alt'],
        action: 'open_help',
        description: 'Open keyboard shortcuts help',
        context: 'global',
        enabled: true,
        isCustomizable: true,
      },
      {
        id: 'go-dashboard',
        key: 'KeyD',
        modifiers: ['alt'],
        action: 'go_to_dashboard',
        description: 'Go to dashboard',
        context: 'global',
        enabled: true,
        isCustomizable: true,
      },
      {
        id: 'go-courses',
        key: 'KeyC',
        modifiers: ['alt'],
        action: 'go_to_courses',
        description: 'Go to courses',
        context: 'global',
        enabled: true,
        isCustomizable: true,
      },
      {
        id: 'close-modal',
        key: 'Escape',
        modifiers: [],
        action: 'close_modal',
        description: 'Close current modal or dialog',
        context: 'modal',
        enabled: true,
        isCustomizable: false,
      },
    ];
  }

  /**
   * Update keyboard shortcut
   *
   * BUSINESS LOGIC:
   * Customizes a keyboard shortcut for the user.
   * Validates for conflicts with existing shortcuts.
   *
   * @param userId - UUID of the user
   * @param action - Action to customize
   * @param key - New key code
   * @param modifiers - New modifier keys
   * @returns Updated shortcut
   */
  async updateKeyboardShortcut(
    userId: string,
    action: string,
    key: string,
    modifiers: string[]
  ): Promise<KeyboardShortcut> {
    try {
      const response = await apiClient.put<KeyboardShortcut>(
        `${this.baseURL}/users/${userId}/keyboard-shortcuts/${action}`,
        { key, modifiers }
      );
      return response;
    } catch (error: any) {
      console.error('[AccessibilityService] Failed to update shortcut:', error);
      throw error;
    }
  }

  // =========================================================================
  // SCREEN READER SUPPORT
  // =========================================================================

  /**
   * Create screen reader announcement
   *
   * BUSINESS LOGIC:
   * Creates an announcement for assistive technology users.
   * Uses ARIA live regions to announce dynamic content changes.
   *
   * @param message - Message to announce
   * @param politeness - Urgency level ("polite" or "assertive")
   * @param delayMs - Delay before announcement
   * @returns Announcement configuration
   */
  createAnnouncement(
    message: string,
    politeness: 'polite' | 'assertive' = 'polite',
    delayMs: number = 0
  ): ScreenReaderAnnouncement {
    return {
      id: `announcement-${Date.now()}`,
      message,
      politeness,
      atomic: true,
      relevant: 'additions text',
      delayMs,
    };
  }

  /**
   * Announce to screen reader
   *
   * TECHNICAL IMPLEMENTATION:
   * Dynamically creates ARIA live region and announces message.
   * Automatically cleans up after announcement.
   *
   * @param message - Message to announce
   * @param politeness - Urgency level
   * @param delayMs - Delay before announcement
   */
  announce(
    message: string,
    politeness: 'polite' | 'assertive' = 'polite',
    delayMs: number = 0
  ): void {
    const announce = () => {
      const liveRegion = document.getElementById('a11y-announcer') ||
        this.createLiveRegion();

      liveRegion.setAttribute('aria-live', politeness);
      liveRegion.textContent = message;

      // Clear after 3 seconds
      setTimeout(() => {
        liveRegion.textContent = '';
      }, 3000);
    };

    if (delayMs > 0) {
      setTimeout(announce, delayMs);
    } else {
      announce();
    }
  }

  /**
   * Create ARIA live region
   *
   * TECHNICAL IMPLEMENTATION:
   * Creates a visually hidden live region for screen reader announcements.
   *
   * @returns Live region element
   */
  private createLiveRegion(): HTMLElement {
    const existing = document.getElementById('a11y-announcer');
    if (existing) return existing;

    const liveRegion = document.createElement('div');
    liveRegion.id = 'a11y-announcer';
    liveRegion.setAttribute('role', 'status');
    liveRegion.setAttribute('aria-live', 'polite');
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'sr-only';
    liveRegion.style.cssText = `
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border-width: 0;
    `;

    document.body.appendChild(liveRegion);
    return liveRegion;
  }
}

// Export singleton instance
export const accessibilityService = new AccessibilityService();
