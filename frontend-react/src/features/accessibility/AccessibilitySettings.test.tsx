/**
 * Accessibility Settings Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the Accessibility Settings page provides comprehensive
 * customization options and follows WCAG 2.1 AA guidelines.
 *
 * TEST COVERAGE:
 * - Component rendering with all sections
 * - Loading and error states
 * - Preference updates and saving
 * - Reset to defaults functionality
 * - ARIA attributes and accessibility
 * - Keyboard navigation
 * - Screen reader announcements
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/utils';
import { AccessibilitySettings } from './AccessibilitySettings';

// Mock the custom hook
vi.mock('./hooks/useAccessibility');
import * as useAccessibilityModule from './hooks/useAccessibility';

// Mock child components
vi.mock('./components/FontSizeSelector', () => ({
  FontSizeSelector: ({ value, onChange, disabled }: any) => (
    <div data-testid="font-size-selector">
      <button onClick={() => onChange('large')} disabled={disabled}>
        Change Font Size (current: {value})
      </button>
    </div>
  ),
}));

vi.mock('./components/ColorSchemeSelector', () => ({
  ColorSchemeSelector: ({ value, highContrastMode, onColorSchemeChange, disabled }: any) => (
    <div data-testid="color-scheme-selector">
      <button onClick={() => onColorSchemeChange('dark')} disabled={disabled}>
        Change Color Scheme (current: {value}, contrast: {highContrastMode ? 'high' : 'normal'})
      </button>
    </div>
  ),
}));

vi.mock('./components/MotionPreferences', () => ({
  MotionPreferences: ({ value, onChange, disabled }: any) => (
    <div data-testid="motion-preferences">
      <button onClick={() => onChange('reduce')} disabled={disabled}>
        Motion Preference (current: {value})
      </button>
    </div>
  ),
}));

vi.mock('./components/KeyboardShortcutsPanel', () => ({
  KeyboardShortcutsPanel: () => (
    <div data-testid="keyboard-shortcuts-panel">Keyboard Shortcuts Panel</div>
  ),
}));

vi.mock('./components/SkipLinks', () => ({
  SkipLinks: () => <div data-testid="skip-links">Skip Links</div>,
}));

vi.mock('./components/FocusIndicator', () => ({
  FocusIndicator: ({ value, onChange, disabled }: any) => (
    <div data-testid="focus-indicator">
      <button onClick={() => onChange('outline')} disabled={disabled}>
        Focus Indicator (current: {value})
      </button>
    </div>
  ),
}));

vi.mock('./components/ScreenReaderAnnouncer', () => ({
  ScreenReaderAnnouncer: () => <div data-testid="screen-reader-announcer">Screen Reader Announcer</div>,
}));

// Mock preferences data
const mockPreferences = {
  userId: 'user-1',
  fontSize: 'medium' as const,
  colorScheme: 'light' as const,
  highContrastMode: false,
  reduceTransparency: false,
  motionPreference: 'no-preference' as const,
  keyboardShortcutsEnabled: true,
  skipLinksAlwaysVisible: false,
  focusHighlightEnabled: true,
  focusIndicatorStyle: 'default' as const,
  screenReaderOptimizations: false,
  announcePageChanges: true,
  verboseAnnouncements: false,
  autoPlayMedia: true,
  captionsEnabled: false,
  audioDescriptionsEnabled: false,
  extendTimeouts: false,
  timeoutMultiplier: 1.0,
  disableAutoRefresh: false,
};

describe('AccessibilitySettings Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering - Default State', () => {
    /**
     * Test: Renders settings page with correct title
     * WHY: Ensures page header is displayed correctly
     */
    it('renders settings page with correct title', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.getByText('Accessibility Settings')).toBeInTheDocument();
      // Component includes "All changes are saved automatically." in the description
      expect(
        screen.getByText(/Customize your accessibility preferences to personalize your learning experience/i)
      ).toBeInTheDocument();
    });

    /**
     * Test: Renders all setting sections
     * WHY: Ensures comprehensive settings coverage
     */
    it('renders all setting sections', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.getByText('Visual Preferences')).toBeInTheDocument();
      expect(screen.getByText('Motion & Animation')).toBeInTheDocument();
      expect(screen.getByText('Keyboard Navigation')).toBeInTheDocument();
      expect(screen.getByText('Screen Reader')).toBeInTheDocument();
      expect(screen.getByText('Media Preferences')).toBeInTheDocument();
      expect(screen.getByText('Timing & Timeouts')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    /**
     * Test: Displays loading state while fetching preferences
     * WHY: Ensures users see loading feedback
     */
    it('displays loading state', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: null,
        isLoading: true,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.getByText('Loading accessibility settings...')).toBeInTheDocument();
      expect(screen.getByLabelText('Loading accessibility settings')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    /**
     * Test: Displays error message when preferences fail to load
     * WHY: Ensures users are informed of errors
     */
    it('displays error message on load failure', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: null,
        isLoading: false,
        error: 'Failed to load preferences',
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.getByText('Error Loading Settings')).toBeInTheDocument();
      expect(screen.getByText('Failed to load preferences')).toBeInTheDocument();
    });
  });

  describe('Visual Preferences Section', () => {
    /**
     * Test: Renders font size selector
     * WHY: Ensures font size customization is available
     */
    it('renders font size selector', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.getByTestId('font-size-selector')).toBeInTheDocument();
    });

    /**
     * Test: Renders color scheme selector
     * WHY: Ensures color scheme customization is available
     */
    it('renders color scheme selector', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.getByTestId('color-scheme-selector')).toBeInTheDocument();
    });

    /**
     * Test: Renders reduce transparency checkbox
     * WHY: Ensures transparency control is available
     */
    it('renders reduce transparency checkbox', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.getByLabelText(/Reduce Transparency/i)).toBeInTheDocument();
    });
  });

  describe('Motion Preferences Section', () => {
    /**
     * Test: Renders motion preferences control
     * WHY: Ensures motion control is available for vestibular disorders
     */
    it('renders motion preferences control', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.getByTestId('motion-preferences')).toBeInTheDocument();
    });
  });

  describe('Keyboard Navigation Section', () => {
    /**
     * Test: Renders keyboard shortcuts toggle
     * WHY: Ensures keyboard navigation can be enabled/disabled
     */
    it('renders keyboard shortcuts toggle', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.getByLabelText(/Enable Keyboard Shortcuts/i)).toBeInTheDocument();
    });

    /**
     * Test: Shows keyboard shortcuts panel when enabled
     * WHY: Ensures shortcuts are visible when feature is enabled
     */
    it('shows keyboard shortcuts panel when enabled', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: { ...mockPreferences, keyboardShortcutsEnabled: true },
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.getByTestId('keyboard-shortcuts-panel')).toBeInTheDocument();
    });

    /**
     * Test: Hides keyboard shortcuts panel when disabled
     * WHY: Ensures shortcuts are hidden when feature is disabled
     */
    it('hides keyboard shortcuts panel when disabled', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: { ...mockPreferences, keyboardShortcutsEnabled: false },
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.queryByTestId('keyboard-shortcuts-panel')).not.toBeInTheDocument();
    });
  });

  describe('Screen Reader Section', () => {
    /**
     * Test: Renders screen reader optimization controls
     * WHY: Ensures screen reader users can optimize their experience
     */
    it('renders screen reader optimization controls', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.getByLabelText(/Enable Screen Reader Optimizations/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Announce Page Changes/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Verbose Announcements/i)).toBeInTheDocument();
    });
  });

  describe('Media Preferences Section', () => {
    /**
     * Test: Renders media preference controls
     * WHY: Ensures users can control media playback
     */
    it('renders media preference controls', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.getByLabelText(/Auto-play Media/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Enable Captions/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Enable Audio Descriptions/i)).toBeInTheDocument();
    });
  });

  describe('Timing Section', () => {
    /**
     * Test: Renders timing controls
     * WHY: Ensures users can extend timeouts
     */
    it('renders timing controls', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.getByLabelText(/Extend Session Timeouts/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Disable Auto-refresh/i)).toBeInTheDocument();
    });

    /**
     * Test: Shows timeout multiplier slider when extend timeouts is enabled
     * WHY: Ensures users can configure timeout duration
     */
    it('shows timeout multiplier slider when extend timeouts is enabled', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: { ...mockPreferences, extendTimeouts: true, timeoutMultiplier: 2.0 },
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.getByLabelText(/Timeout Extension/i)).toBeInTheDocument();
    });
  });

  describe('Preference Updates', () => {
    /**
     * Test: Updates preferences when checkbox is toggled
     * WHY: Ensures settings changes are saved
     */
    it('updates preferences when checkbox is toggled', async () => {
      const mockUpdatePreferences = vi.fn().mockResolvedValue(undefined);
      const mockAnnounce = vi.fn();

      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: mockUpdatePreferences,
        resetPreferences: vi.fn(),
        announce: mockAnnounce,
      });

      const user = userEvent.setup();
      renderWithProviders(<AccessibilitySettings />);

      const captionsCheckbox = screen.getByLabelText(/Enable Captions/i);
      await user.click(captionsCheckbox);

      expect(mockUpdatePreferences).toHaveBeenCalledWith({ captionsEnabled: true });
    });

    /**
     * Test: Shows success message after saving
     * WHY: Provides feedback that settings were saved
     */
    it('shows success message after saving', async () => {
      const mockUpdatePreferences = vi.fn().mockResolvedValue(undefined);

      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: mockUpdatePreferences,
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      const user = userEvent.setup();
      renderWithProviders(<AccessibilitySettings />);

      const captionsCheckbox = screen.getByLabelText(/Enable Captions/i);
      await user.click(captionsCheckbox);

      await waitFor(() => {
        expect(screen.getByText('Settings saved successfully')).toBeInTheDocument();
      });
    });
  });

  describe('Reset Functionality', () => {
    /**
     * Test: Reset button is rendered
     * WHY: Ensures users can reset to defaults
     */
    it('renders reset button', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      // Button has aria-label="Reset all accessibility settings to defaults"
      expect(screen.getByRole('button', { name: /Reset.*accessibility.*defaults/i })).toBeInTheDocument();
    });
  });

  describe('Accessibility Features', () => {
    /**
     * Test: Skip links are rendered
     * WHY: Ensures keyboard users can skip navigation
     */
    it('renders skip links', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.getByTestId('skip-links')).toBeInTheDocument();
    });

    /**
     * Test: Screen reader announcer is rendered
     * WHY: Ensures screen readers receive announcements
     */
    it('renders screen reader announcer', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      expect(screen.getByTestId('screen-reader-announcer')).toBeInTheDocument();
    });

    /**
     * Test: Main content has proper role and ID
     * WHY: Ensures skip links can target main content
     */
    it('main content has proper role and ID', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      renderWithProviders(<AccessibilitySettings />);

      const mainContent = screen.getByRole('main');
      expect(mainContent).toHaveAttribute('id', 'main-content');
    });

    /**
     * Test: Section headings have proper ARIA labelledby
     * WHY: Ensures screen readers announce section context
     */
    it('section headings use aria-labelledby', () => {
      vi.spyOn(useAccessibilityModule, 'useAccessibility').mockReturnValue({
        preferences: mockPreferences,
        isLoading: false,
        error: null,
        updatePreferences: vi.fn(),
        resetPreferences: vi.fn(),
        announce: vi.fn(),
      });

      const { container } = renderWithProviders(<AccessibilitySettings />);

      const sections = container.querySelectorAll('section[aria-labelledby]');
      expect(sections.length).toBeGreaterThan(0);
    });
  });
});
