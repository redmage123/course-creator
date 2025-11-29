/**
 * Accessibility Service Tests
 *
 * BUSINESS CONTEXT:
 * Comprehensive test suite ensuring accessibility service correctly manages user preferences,
 * validates color contrast, handles keyboard shortcuts, and provides screen reader support
 * in compliance with WCAG 2.1 AA standards.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest for testing with mocked API client
 * Tests all service methods including preferences, contrast validation, shortcuts, and announcements
 *
 * COVERAGE REQUIREMENTS:
 * - Preferences CRUD operations
 * - Color contrast calculations and validation
 * - Keyboard shortcuts management
 * - Screen reader announcements
 * - Client-side preference application
 * - Error handling and fallbacks
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  accessibilityService,
  FontSizePreference,
  ColorSchemePreference,
  MotionPreference,
  FocusIndicatorStyle,
  ColorContrastLevel,
  AccessibilityPreference,
} from './accessibilityService';
import { apiClient } from './apiClient';

// Mock API client
vi.mock('./apiClient', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('AccessibilityService', () => {
  let mockPreferences: AccessibilityPreference;

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    document.documentElement.className = '';
    document.documentElement.removeAttribute('data-color-scheme');

    // Mock preferences
    mockPreferences = {
      id: 'pref-123',
      userId: 'user-123',
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
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
    };
  });

  afterEach(() => {
    // Clean up live region if created
    const liveRegion = document.getElementById('a11y-announcer');
    if (liveRegion) {
      liveRegion.remove();
    }
  });

  describe('Preferences Management', () => {
    describe('getUserPreferences', () => {
      it('retrieves user preferences from backend', async () => {
        vi.mocked(apiClient.get).mockResolvedValue(mockPreferences);

        const result = await accessibilityService.getUserPreferences('user-123');

        expect(apiClient.get).toHaveBeenCalledWith(
          '/organizations/users/user-123/accessibility-preferences'
        );
        expect(result).toEqual(mockPreferences);
      });

      it('returns default preferences when not found (404)', async () => {
        vi.mocked(apiClient.get).mockRejectedValue({
          response: { status: 404 },
        });

        const result = await accessibilityService.getUserPreferences('user-123');

        expect(result.userId).toBe('user-123');
        expect(result.fontSize).toBe(FontSizePreference.DEFAULT);
        expect(result.colorScheme).toBe(ColorSchemePreference.SYSTEM);
      });

      it('throws error for non-404 failures', async () => {
        vi.mocked(apiClient.get).mockRejectedValue(new Error('Network error'));

        await expect(
          accessibilityService.getUserPreferences('user-123')
        ).rejects.toThrow('Network error');
      });
    });

    describe('updateUserPreferences', () => {
      it('updates user preferences via backend', async () => {
        const updates = { fontSize: FontSizePreference.LARGE };
        const updated = { ...mockPreferences, ...updates };
        vi.mocked(apiClient.put).mockResolvedValue(updated);

        const result = await accessibilityService.updateUserPreferences('user-123', updates);

        expect(apiClient.put).toHaveBeenCalledWith(
          '/organizations/users/user-123/accessibility-preferences',
          updates
        );
        expect(result.fontSize).toBe(FontSizePreference.LARGE);
      });

      it('applies preferences to document after update', async () => {
        const updates = { fontSize: FontSizePreference.LARGE };
        const updated = { ...mockPreferences, ...updates };
        vi.mocked(apiClient.put).mockResolvedValue(updated);

        await accessibilityService.updateUserPreferences('user-123', updates);

        expect(document.documentElement.style.getPropertyValue('--a11y-font-size-multiplier')).toBe('1.25');
      });

      it('validates timeout multiplier range', async () => {
        await expect(
          accessibilityService.updateUserPreferences('user-123', { timeoutMultiplier: 0.5 })
        ).rejects.toThrow('Timeout multiplier must be between 1.0 and 5.0');

        await expect(
          accessibilityService.updateUserPreferences('user-123', { timeoutMultiplier: 6.0 })
        ).rejects.toThrow('Timeout multiplier must be between 1.0 and 5.0');
      });

      it('accepts valid timeout multiplier values', async () => {
        const updated = { ...mockPreferences, timeoutMultiplier: 2.5 };
        vi.mocked(apiClient.put).mockResolvedValue(updated);

        const result = await accessibilityService.updateUserPreferences('user-123', {
          timeoutMultiplier: 2.5,
        });

        expect(result.timeoutMultiplier).toBe(2.5);
      });

      it('throws error on update failure', async () => {
        vi.mocked(apiClient.put).mockRejectedValue(new Error('Update failed'));

        await expect(
          accessibilityService.updateUserPreferences('user-123', { fontSize: FontSizePreference.LARGE })
        ).rejects.toThrow('Update failed');
      });
    });

    describe('resetUserPreferences', () => {
      it('resets preferences to defaults via backend', async () => {
        const defaultPrefs = accessibilityService.getDefaultPreferences('user-123');
        vi.mocked(apiClient.post).mockResolvedValue(defaultPrefs);

        const result = await accessibilityService.resetUserPreferences('user-123');

        expect(apiClient.post).toHaveBeenCalledWith(
          '/organizations/users/user-123/accessibility-preferences/reset'
        );
        expect(result.fontSize).toBe(FontSizePreference.DEFAULT);
      });

      it('applies default preferences to document', async () => {
        const defaultPrefs = accessibilityService.getDefaultPreferences('user-123');
        vi.mocked(apiClient.post).mockResolvedValue(defaultPrefs);

        await accessibilityService.resetUserPreferences('user-123');

        expect(document.documentElement.style.getPropertyValue('--a11y-font-size-multiplier')).toBe('1');
      });

      it('throws error on reset failure', async () => {
        vi.mocked(apiClient.post).mockRejectedValue(new Error('Reset failed'));

        await expect(
          accessibilityService.resetUserPreferences('user-123')
        ).rejects.toThrow('Reset failed');
      });
    });

    describe('getDefaultPreferences', () => {
      it('returns default preferences for user', () => {
        const defaults = accessibilityService.getDefaultPreferences('user-123');

        expect(defaults.userId).toBe('user-123');
        expect(defaults.fontSize).toBe(FontSizePreference.DEFAULT);
        expect(defaults.colorScheme).toBe(ColorSchemePreference.SYSTEM);
        expect(defaults.motionPreference).toBe(MotionPreference.NO_PREFERENCE);
        expect(defaults.keyboardShortcutsEnabled).toBe(true);
        expect(defaults.captionsEnabled).toBe(true);
        expect(defaults.autoPlayMedia).toBe(false);
      });

      it('includes timestamps', () => {
        const defaults = accessibilityService.getDefaultPreferences('user-123');

        expect(defaults.createdAt).toBeTruthy();
        expect(defaults.updatedAt).toBeTruthy();
      });
    });

    describe('applyPreferences', () => {
      it('sets font size CSS custom property', () => {
        const prefs = { ...mockPreferences, fontSize: FontSizePreference.HUGE };
        accessibilityService.applyPreferences(prefs);

        expect(document.documentElement.style.getPropertyValue('--a11y-font-size-multiplier')).toBe('2');
      });

      it('sets animation multiplier CSS custom property', () => {
        const prefs = { ...mockPreferences, motionPreference: MotionPreference.REDUCE };
        accessibilityService.applyPreferences(prefs);

        expect(document.documentElement.style.getPropertyValue('--a11y-animation-multiplier')).toBe('0.3');
      });

      it('sets no motion when motionPreference is NO_MOTION', () => {
        const prefs = { ...mockPreferences, motionPreference: MotionPreference.NO_MOTION };
        accessibilityService.applyPreferences(prefs);

        expect(document.documentElement.style.getPropertyValue('--a11y-animation-multiplier')).toBe('0');
      });

      it('sets transparency reduction CSS custom property', () => {
        const prefs = { ...mockPreferences, reduceTransparency: true };
        accessibilityService.applyPreferences(prefs);

        expect(document.documentElement.style.getPropertyValue('--a11y-reduce-transparency')).toBe('0.5');
      });

      it('sets focus ring width CSS custom property', () => {
        const prefs = { ...mockPreferences, focusIndicatorStyle: FocusIndicatorStyle.HIGH_VISIBILITY };
        accessibilityService.applyPreferences(prefs);

        expect(document.documentElement.style.getPropertyValue('--a11y-focus-ring-width')).toBe('4px');
      });

      it('sets color scheme data attribute', () => {
        const prefs = { ...mockPreferences, colorScheme: ColorSchemePreference.DARK };
        accessibilityService.applyPreferences(prefs);

        expect(document.documentElement.getAttribute('data-color-scheme')).toBe('dark');
      });

      it('removes color scheme data attribute when SYSTEM', () => {
        document.documentElement.setAttribute('data-color-scheme', 'dark');
        const prefs = { ...mockPreferences, colorScheme: ColorSchemePreference.SYSTEM };
        accessibilityService.applyPreferences(prefs);

        expect(document.documentElement.hasAttribute('data-color-scheme')).toBe(false);
      });

      it('adds high-contrast class when enabled', () => {
        const prefs = { ...mockPreferences, highContrastMode: true };
        accessibilityService.applyPreferences(prefs);

        expect(document.documentElement.classList.contains('high-contrast')).toBe(true);
      });

      it('adds skip-links-always-visible class when enabled', () => {
        const prefs = { ...mockPreferences, skipLinksAlwaysVisible: true };
        accessibilityService.applyPreferences(prefs);

        expect(document.documentElement.classList.contains('skip-links-always-visible')).toBe(true);
      });

      it('stores preferences in localStorage', () => {
        accessibilityService.applyPreferences(mockPreferences);

        const stored = localStorage.getItem('accessibility-preferences');
        expect(stored).toBeTruthy();
        const parsed = JSON.parse(stored!);
        expect(parsed.userId).toBe('user-123');
      });
    });
  });

  describe('Color Contrast Validation', () => {
    describe('validateColorContrast', () => {
      it('validates color contrast via backend', async () => {
        const mockResult = {
          id: 'validation-123',
          level: ColorContrastLevel.NORMAL_TEXT_AA,
          foregroundColor: '#000000',
          backgroundColor: '#FFFFFF',
          calculatedRatio: 21.0,
          passes: true,
          requiredRatio: 4.5,
        };
        vi.mocked(apiClient.post).mockResolvedValue(mockResult);

        const result = await accessibilityService.validateColorContrast(
          '#000000',
          '#FFFFFF',
          ColorContrastLevel.NORMAL_TEXT_AA,
          'Button'
        );

        expect(apiClient.post).toHaveBeenCalledWith(
          '/organizations/accessibility/validate-contrast',
          {
            foreground: '#000000',
            background: '#FFFFFF',
            level: ColorContrastLevel.NORMAL_TEXT_AA,
            componentName: 'Button',
          }
        );
        expect(result.passes).toBe(true);
        expect(result.calculatedRatio).toBe(21.0);
      });

      it('uses default level when not specified', async () => {
        const mockResult = {
          id: 'validation-123',
          level: ColorContrastLevel.NORMAL_TEXT_AA,
          foregroundColor: '#000000',
          backgroundColor: '#FFFFFF',
          calculatedRatio: 21.0,
          passes: true,
          requiredRatio: 4.5,
        };
        vi.mocked(apiClient.post).mockResolvedValue(mockResult);

        await accessibilityService.validateColorContrast('#000000', '#FFFFFF');

        expect(apiClient.post).toHaveBeenCalledWith(
          '/organizations/accessibility/validate-contrast',
          expect.objectContaining({
            level: ColorContrastLevel.NORMAL_TEXT_AA,
          })
        );
      });

      it('throws error on validation failure', async () => {
        vi.mocked(apiClient.post).mockRejectedValue(new Error('Validation failed'));

        await expect(
          accessibilityService.validateColorContrast('#000000', '#FFFFFF')
        ).rejects.toThrow('Validation failed');
      });
    });

    describe('calculateContrastRatio', () => {
      it('calculates 21:1 ratio for black on white', () => {
        const ratio = accessibilityService.calculateContrastRatio('#000000', '#FFFFFF');
        expect(ratio).toBeCloseTo(21.0, 1);
      });

      it('calculates 21:1 ratio for white on black', () => {
        const ratio = accessibilityService.calculateContrastRatio('#FFFFFF', '#000000');
        expect(ratio).toBeCloseTo(21.0, 1);
      });

      it('calculates 1:1 ratio for identical colors', () => {
        const ratio = accessibilityService.calculateContrastRatio('#888888', '#888888');
        expect(ratio).toBeCloseTo(1.0, 1);
      });

      it('handles hex colors without # prefix', () => {
        const ratio = accessibilityService.calculateContrastRatio('000000', 'FFFFFF');
        expect(ratio).toBeCloseTo(21.0, 1);
      });

      it('calculates ratio for typical UI colors', () => {
        // Blue on white (should pass AA for normal text)
        const ratio = accessibilityService.calculateContrastRatio('#0000FF', '#FFFFFF');
        expect(ratio).toBeGreaterThan(4.5);
      });

      it('returns high ratio for invalid foreground on white (invalid treated as black)', () => {
        // Invalid hex colors return null from hexToRgb, giving luminance 0 (like black)
        // With invalid foreground (L=0) and white background (L=1):
        // ratio = (1 + 0.05) / (0 + 0.05) = 21
        const ratio = accessibilityService.calculateContrastRatio('invalid', '#FFFFFF');
        expect(ratio).toBeCloseTo(21.0, 1);
      });
    });
  });

  describe('Keyboard Shortcuts Management', () => {
    describe('getKeyboardShortcuts', () => {
      it('retrieves keyboard shortcuts from backend', async () => {
        const mockShortcuts = [
          {
            id: 'shortcut-1',
            key: 'KeyS',
            modifiers: ['alt'],
            action: 'skip_to_main',
            description: 'Skip to main content',
            context: 'global',
            enabled: true,
            isCustomizable: true,
          },
        ];
        vi.mocked(apiClient.get).mockResolvedValue(mockShortcuts);

        const result = await accessibilityService.getKeyboardShortcuts('user-123', 'global');

        expect(apiClient.get).toHaveBeenCalledWith(
          '/organizations/accessibility/keyboard-shortcuts?userId=user-123&context=global'
        );
        expect(result).toEqual(mockShortcuts);
      });

      it('uses default context if not specified', async () => {
        vi.mocked(apiClient.get).mockResolvedValue([]);

        await accessibilityService.getKeyboardShortcuts('user-123');

        expect(apiClient.get).toHaveBeenCalledWith(
          expect.stringContaining('context=global')
        );
      });

      it('returns default shortcuts on error', async () => {
        vi.mocked(apiClient.get).mockRejectedValue(new Error('Network error'));

        const result = await accessibilityService.getKeyboardShortcuts('user-123');

        expect(result.length).toBeGreaterThan(0);
        expect(result[0]).toHaveProperty('key');
        expect(result[0]).toHaveProperty('action');
      });
    });

    describe('getDefaultShortcuts', () => {
      it('returns default keyboard shortcuts', () => {
        const shortcuts = accessibilityService.getDefaultShortcuts();

        expect(shortcuts.length).toBeGreaterThan(0);
        expect(shortcuts[0]).toHaveProperty('id');
        expect(shortcuts[0]).toHaveProperty('key');
        expect(shortcuts[0]).toHaveProperty('modifiers');
        expect(shortcuts[0]).toHaveProperty('action');
      });

      it('includes skip to main shortcut', () => {
        const shortcuts = accessibilityService.getDefaultShortcuts();
        const skipToMain = shortcuts.find(s => s.action === 'skip_to_main');

        expect(skipToMain).toBeTruthy();
        expect(skipToMain?.key).toBe('KeyS');
        expect(skipToMain?.modifiers).toContain('alt');
      });

      it('includes modal close shortcut', () => {
        const shortcuts = accessibilityService.getDefaultShortcuts();
        const closeModal = shortcuts.find(s => s.action === 'close_modal');

        expect(closeModal).toBeTruthy();
        expect(closeModal?.key).toBe('Escape');
        expect(closeModal?.modifiers).toEqual([]);
      });

      it('marks escape shortcut as non-customizable', () => {
        const shortcuts = accessibilityService.getDefaultShortcuts();
        const closeModal = shortcuts.find(s => s.action === 'close_modal');

        expect(closeModal?.isCustomizable).toBe(false);
      });
    });

    describe('updateKeyboardShortcut', () => {
      it('updates keyboard shortcut via backend', async () => {
        const mockUpdated = {
          id: 'shortcut-1',
          key: 'KeyM',
          modifiers: ['alt'],
          action: 'skip_to_main',
          description: 'Skip to main content',
          context: 'global',
          enabled: true,
          isCustomizable: true,
        };
        vi.mocked(apiClient.put).mockResolvedValue(mockUpdated);

        const result = await accessibilityService.updateKeyboardShortcut(
          'user-123',
          'skip_to_main',
          'KeyM',
          ['alt']
        );

        expect(apiClient.put).toHaveBeenCalledWith(
          '/organizations/users/user-123/keyboard-shortcuts/skip_to_main',
          { key: 'KeyM', modifiers: ['alt'] }
        );
        expect(result.key).toBe('KeyM');
      });

      it('throws error on update failure', async () => {
        vi.mocked(apiClient.put).mockRejectedValue(new Error('Update failed'));

        await expect(
          accessibilityService.updateKeyboardShortcut('user-123', 'skip_to_main', 'KeyM', ['alt'])
        ).rejects.toThrow('Update failed');
      });
    });
  });

  describe('Screen Reader Support', () => {
    describe('createAnnouncement', () => {
      it('creates announcement with default politeness', () => {
        const announcement = accessibilityService.createAnnouncement('Test message');

        expect(announcement.message).toBe('Test message');
        expect(announcement.politeness).toBe('polite');
        expect(announcement.atomic).toBe(true);
        expect(announcement.delayMs).toBe(0);
      });

      it('creates announcement with assertive politeness', () => {
        const announcement = accessibilityService.createAnnouncement('Error occurred', 'assertive');

        expect(announcement.politeness).toBe('assertive');
      });

      it('creates announcement with delay', () => {
        const announcement = accessibilityService.createAnnouncement('Delayed message', 'polite', 1000);

        expect(announcement.delayMs).toBe(1000);
      });

      it('generates unique ID for each announcement', () => {
        vi.useFakeTimers();

        const ann1 = accessibilityService.createAnnouncement('Message 1');
        // Advance time to ensure Date.now() returns a different value
        vi.advanceTimersByTime(1);
        const ann2 = accessibilityService.createAnnouncement('Message 2');

        expect(ann1.id).not.toBe(ann2.id);

        vi.useRealTimers();
      });
    });

    describe('announce', () => {
      beforeEach(() => {
        vi.useFakeTimers();
      });

      afterEach(() => {
        vi.useRealTimers();
      });

      it('creates ARIA live region if not exists', () => {
        accessibilityService.announce('Test message');

        const liveRegion = document.getElementById('a11y-announcer');
        expect(liveRegion).toBeTruthy();
        expect(liveRegion?.getAttribute('role')).toBe('status');
        expect(liveRegion?.getAttribute('aria-live')).toBe('polite');
        expect(liveRegion?.getAttribute('aria-atomic')).toBe('true');
      });

      it('announces message with polite politeness', () => {
        accessibilityService.announce('Test message', 'polite');

        const liveRegion = document.getElementById('a11y-announcer');
        expect(liveRegion?.textContent).toBe('Test message');
        expect(liveRegion?.getAttribute('aria-live')).toBe('polite');
      });

      it('announces message with assertive politeness', () => {
        accessibilityService.announce('Error message', 'assertive');

        const liveRegion = document.getElementById('a11y-announcer');
        expect(liveRegion?.textContent).toBe('Error message');
        expect(liveRegion?.getAttribute('aria-live')).toBe('assertive');
      });

      it('clears message after 3 seconds', () => {
        accessibilityService.announce('Test message');

        const liveRegion = document.getElementById('a11y-announcer');
        expect(liveRegion?.textContent).toBe('Test message');

        vi.advanceTimersByTime(3000);
        expect(liveRegion?.textContent).toBe('');
      });

      it('delays announcement when delayMs specified', () => {
        accessibilityService.announce('Delayed message', 'polite', 1000);

        // When delayed, the live region may not exist yet OR may be empty
        let liveRegion = document.getElementById('a11y-announcer');
        // Check that the message is not announced yet (either no region or empty)
        expect(liveRegion?.textContent || '').toBe('');

        vi.advanceTimersByTime(1000);
        liveRegion = document.getElementById('a11y-announcer');
        expect(liveRegion?.textContent).toBe('Delayed message');
      });

      it('reuses existing live region', () => {
        accessibilityService.announce('Message 1');
        const liveRegion1 = document.getElementById('a11y-announcer');

        accessibilityService.announce('Message 2');
        const liveRegion2 = document.getElementById('a11y-announcer');

        expect(liveRegion1).toBe(liveRegion2);
      });

      it('applies sr-only styling to live region', () => {
        accessibilityService.announce('Test message');

        const liveRegion = document.getElementById('a11y-announcer');
        expect(liveRegion?.className).toBe('sr-only');
        expect(liveRegion?.style.position).toBe('absolute');
        expect(liveRegion?.style.width).toBe('1px');
        expect(liveRegion?.style.height).toBe('1px');
      });
    });
  });

  describe('Display Name', () => {
    it('has AccessibilityService as constructor name', () => {
      expect(accessibilityService.constructor.name).toBe('AccessibilityService');
    });
  });

  describe('Regression Tests', () => {
    it('handles multiple preference updates in sequence', async () => {
      // Each response should reflect cumulative state
      // First update: fontSize becomes LARGE
      const afterFirstUpdate = { ...mockPreferences, fontSize: FontSizePreference.LARGE };
      // Second update: colorScheme becomes DARK (keeping LARGE font from first update)
      const afterSecondUpdate = { ...afterFirstUpdate, colorScheme: ColorSchemePreference.DARK };

      vi.mocked(apiClient.put)
        .mockResolvedValueOnce(afterFirstUpdate)
        .mockResolvedValueOnce(afterSecondUpdate);

      await accessibilityService.updateUserPreferences('user-123', { fontSize: FontSizePreference.LARGE });
      await accessibilityService.updateUserPreferences('user-123', { colorScheme: ColorSchemePreference.DARK });

      expect(document.documentElement.style.getPropertyValue('--a11y-font-size-multiplier')).toBe('1.25');
      expect(document.documentElement.getAttribute('data-color-scheme')).toBe('dark');
    });

    it('handles concurrent announcements without conflict', () => {
      vi.useFakeTimers();

      accessibilityService.announce('Message 1');
      accessibilityService.announce('Message 2');
      accessibilityService.announce('Message 3');

      const liveRegion = document.getElementById('a11y-announcer');
      expect(liveRegion?.textContent).toBe('Message 3');

      vi.useRealTimers();
    });

    it('preserves preferences in localStorage across sessions', () => {
      accessibilityService.applyPreferences(mockPreferences);

      const stored = localStorage.getItem('accessibility-preferences');
      expect(stored).toBeTruthy();

      localStorage.clear();
      accessibilityService.applyPreferences(mockPreferences);

      const restoredStored = localStorage.getItem('accessibility-preferences');
      expect(restoredStored).toBeTruthy();
    });
  });
});
