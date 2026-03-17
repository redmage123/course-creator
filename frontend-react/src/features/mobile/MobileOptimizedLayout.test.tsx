/**
 * MobileOptimizedLayout Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the MobileOptimizedLayout provides responsive,
 * mobile-first layouts with device-specific optimizations.
 *
 * TEST COVERAGE:
 * - Component rendering with different device types
 * - Safe area insets for notched devices
 * - Offline indicator display
 * - Navigation integration
 * - Responsive layout modes (mobile, tablet, desktop)
 * - Compact mode preferences
 * - Accessibility features
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing.
 * Mocks mobile experience hooks for isolated testing.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MobileOptimizedLayout } from './MobileOptimizedLayout';
import * as useMobileExperienceModule from './hooks/useMobileExperience';
import * as useDeviceCapabilitiesModule from './hooks/useDeviceCapabilities';

// Mock the hooks
vi.mock('./hooks/useMobileExperience');
vi.mock('./hooks/useDeviceCapabilities');
vi.mock('./components/OfflineIndicator', () => ({
  OfflineIndicator: ({ position }: { position: string }) => (
    <div data-testid="offline-indicator" data-position={position}>
      Offline
    </div>
  ),
}));
vi.mock('./components/MobileNavigation', () => ({
  MobileNavigation: ({ items, position }: any) => (
    <nav data-testid="mobile-navigation" data-position={position}>
      {items.map((item: any) => (
        <div key={item.id}>{item.label}</div>
      ))}
    </nav>
  ),
}));

describe('MobileOptimizedLayout Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock implementations
    vi.spyOn(useMobileExperienceModule, 'useMobileExperience').mockReturnValue({
      isMobile: false,
      isTablet: false,
      devicePreferences: null,
      updatePreferences: vi.fn(),
      isLoading: false,
    });

    vi.spyOn(useDeviceCapabilitiesModule, 'useDeviceCapabilities').mockReturnValue({
      isOnline: true,
      isTouchDevice: false,
      hasCamera: false,
      hasGeolocation: false,
      hasNotifications: false,
      screenSize: { width: 1920, height: 1080 },
      devicePixelRatio: 1,
      platform: 'desktop',
    });
  });

  describe('Rendering', () => {
    it('renders children content', () => {
      render(
        <MobileOptimizedLayout>
          <div>Main Content</div>
        </MobileOptimizedLayout>
      );

      expect(screen.getByText('Main Content')).toBeInTheDocument();
    });

    it('renders with header when provided', () => {
      render(
        <MobileOptimizedLayout header={<div>Header Content</div>}>
          <div>Main Content</div>
        </MobileOptimizedLayout>
      );

      expect(screen.getByText('Header Content')).toBeInTheDocument();
    });

    it('renders with footer when provided', () => {
      render(
        <MobileOptimizedLayout footer={<div>Footer Content</div>}>
          <div>Main Content</div>
        </MobileOptimizedLayout>
      );

      expect(screen.getByText('Footer Content')).toBeInTheDocument();
    });

    it('renders mobile navigation when items provided', () => {
      const navItems = [
        { id: '1', label: 'Home', path: '/', icon: '🏠' },
        { id: '2', label: 'Courses', path: '/courses', icon: '📚' },
      ];

      render(
        <MobileOptimizedLayout navigationItems={navItems}>
          <div>Content</div>
        </MobileOptimizedLayout>
      );

      expect(screen.getByTestId('mobile-navigation')).toBeInTheDocument();
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Courses')).toBeInTheDocument();
    });

    it('does not render navigation when no items provided', () => {
      render(
        <MobileOptimizedLayout>
          <div>Content</div>
        </MobileOptimizedLayout>
      );

      expect(screen.queryByTestId('mobile-navigation')).not.toBeInTheDocument();
    });

    it('applies custom className when provided', () => {
      const { container } = render(
        <MobileOptimizedLayout className="custom-layout">
          <div>Content</div>
        </MobileOptimizedLayout>
      );

      const layoutDiv = container.firstChild as HTMLElement;
      expect(layoutDiv.className).toContain('custom-layout');
    });
  });

  describe('Device Type Layouts', () => {
    it('renders desktop layout by default', () => {
      vi.spyOn(useMobileExperienceModule, 'useMobileExperience').mockReturnValue({
        isMobile: false,
        isTablet: false,
        devicePreferences: null,
        updatePreferences: vi.fn(),
        isLoading: false,
      });

      const { container } = render(
        <MobileOptimizedLayout>
          <div>Content</div>
        </MobileOptimizedLayout>
      );

      const layoutDiv = container.firstChild as HTMLElement;
      expect(layoutDiv.className).toContain('desktop');
    });

    it('renders mobile layout when isMobile is true', () => {
      vi.spyOn(useMobileExperienceModule, 'useMobileExperience').mockReturnValue({
        isMobile: true,
        isTablet: false,
        devicePreferences: null,
        updatePreferences: vi.fn(),
        isLoading: false,
      });

      const { container } = render(
        <MobileOptimizedLayout>
          <div>Content</div>
        </MobileOptimizedLayout>
      );

      const layoutDiv = container.firstChild as HTMLElement;
      expect(layoutDiv.className).toContain('mobile');
    });

    it('renders tablet layout when isTablet is true', () => {
      vi.spyOn(useMobileExperienceModule, 'useMobileExperience').mockReturnValue({
        isMobile: false,
        isTablet: true,
        devicePreferences: null,
        updatePreferences: vi.fn(),
        isLoading: false,
      });

      const { container } = render(
        <MobileOptimizedLayout>
          <div>Content</div>
        </MobileOptimizedLayout>
      );

      const layoutDiv = container.firstChild as HTMLElement;
      expect(layoutDiv.className).toContain('tablet');
    });
  });

  describe('Safe Area Support', () => {
    it('applies safe area class by default', () => {
      const { container } = render(
        <MobileOptimizedLayout>
          <div>Content</div>
        </MobileOptimizedLayout>
      );

      const layoutDiv = container.firstChild as HTMLElement;
      expect(layoutDiv.className).toContain('safeArea');
    });

    it('does not apply safe area class when disabled', () => {
      const { container } = render(
        <MobileOptimizedLayout enableSafeArea={false}>
          <div>Content</div>
        </MobileOptimizedLayout>
      );

      const layoutDiv = container.firstChild as HTMLElement;
      expect(layoutDiv.className).not.toContain('safeArea');
    });
  });

  describe('Compact Mode', () => {
    it('applies compact class when compact mode enabled', () => {
      vi.spyOn(useMobileExperienceModule, 'useMobileExperience').mockReturnValue({
        isMobile: true,
        isTablet: false,
        devicePreferences: { compact_mode: true },
        updatePreferences: vi.fn(),
        isLoading: false,
      });

      const { container } = render(
        <MobileOptimizedLayout>
          <div>Content</div>
        </MobileOptimizedLayout>
      );

      const layoutDiv = container.firstChild as HTMLElement;
      expect(layoutDiv.className).toContain('compact');
    });

    it('does not apply compact class when compact mode disabled', () => {
      vi.spyOn(useMobileExperienceModule, 'useMobileExperience').mockReturnValue({
        isMobile: true,
        isTablet: false,
        devicePreferences: { compact_mode: false },
        updatePreferences: vi.fn(),
        isLoading: false,
      });

      const { container } = render(
        <MobileOptimizedLayout>
          <div>Content</div>
        </MobileOptimizedLayout>
      );

      const layoutDiv = container.firstChild as HTMLElement;
      expect(layoutDiv.className).not.toContain('compact');
    });
  });

  describe('Offline Indicator', () => {
    it('shows offline indicator when offline and showOfflineIndicator is true', () => {
      vi.spyOn(useDeviceCapabilitiesModule, 'useDeviceCapabilities').mockReturnValue({
        isOnline: false,
        isTouchDevice: false,
        hasCamera: false,
        hasGeolocation: false,
        hasNotifications: false,
        screenSize: { width: 375, height: 667 },
        devicePixelRatio: 2,
        platform: 'mobile',
      });

      render(
        <MobileOptimizedLayout showOfflineIndicator={true}>
          <div>Content</div>
        </MobileOptimizedLayout>
      );

      expect(screen.getByTestId('offline-indicator')).toBeInTheDocument();
    });

    it('does not show offline indicator when online', () => {
      vi.spyOn(useDeviceCapabilitiesModule, 'useDeviceCapabilities').mockReturnValue({
        isOnline: true,
        isTouchDevice: false,
        hasCamera: false,
        hasGeolocation: false,
        hasNotifications: false,
        screenSize: { width: 375, height: 667 },
        devicePixelRatio: 2,
        platform: 'mobile',
      });

      render(
        <MobileOptimizedLayout showOfflineIndicator={true}>
          <div>Content</div>
        </MobileOptimizedLayout>
      );

      expect(screen.queryByTestId('offline-indicator')).not.toBeInTheDocument();
    });

    it('does not show offline indicator when showOfflineIndicator is false', () => {
      vi.spyOn(useDeviceCapabilitiesModule, 'useDeviceCapabilities').mockReturnValue({
        isOnline: false,
        isTouchDevice: false,
        hasCamera: false,
        hasGeolocation: false,
        hasNotifications: false,
        screenSize: { width: 375, height: 667 },
        devicePixelRatio: 2,
        platform: 'mobile',
      });

      render(
        <MobileOptimizedLayout showOfflineIndicator={false}>
          <div>Content</div>
        </MobileOptimizedLayout>
      );

      expect(screen.queryByTestId('offline-indicator')).not.toBeInTheDocument();
    });

    it('positions offline indicator at top', () => {
      vi.spyOn(useDeviceCapabilitiesModule, 'useDeviceCapabilities').mockReturnValue({
        isOnline: false,
        isTouchDevice: false,
        hasCamera: false,
        hasGeolocation: false,
        hasNotifications: false,
        screenSize: { width: 375, height: 667 },
        devicePixelRatio: 2,
        platform: 'mobile',
      });

      render(
        <MobileOptimizedLayout>
          <div>Content</div>
        </MobileOptimizedLayout>
      );

      const indicator = screen.getByTestId('offline-indicator');
      expect(indicator).toHaveAttribute('data-position', 'top');
    });
  });

  describe('Accessibility', () => {
    it('renders main content in main element', () => {
      render(
        <MobileOptimizedLayout>
          <div>Main Content</div>
        </MobileOptimizedLayout>
      );

      const main = document.querySelector('main');
      expect(main).toBeInTheDocument();
      expect(main).toHaveTextContent('Main Content');
    });

    it('renders header in header element', () => {
      render(
        <MobileOptimizedLayout header={<div>Header</div>}>
          <div>Content</div>
        </MobileOptimizedLayout>
      );

      const header = document.querySelector('header');
      expect(header).toBeInTheDocument();
      expect(header).toHaveTextContent('Header');
    });

    it('renders footer in footer element', () => {
      render(
        <MobileOptimizedLayout footer={<div>Footer</div>}>
          <div>Content</div>
        </MobileOptimizedLayout>
      );

      const footer = document.querySelector('footer');
      expect(footer).toBeInTheDocument();
      expect(footer).toHaveTextContent('Footer');
    });
  });

  describe('Integration', () => {
    it('combines all layout features correctly', () => {
      vi.spyOn(useMobileExperienceModule, 'useMobileExperience').mockReturnValue({
        isMobile: true,
        isTablet: false,
        devicePreferences: { compact_mode: true },
        updatePreferences: vi.fn(),
        isLoading: false,
      });

      vi.spyOn(useDeviceCapabilitiesModule, 'useDeviceCapabilities').mockReturnValue({
        isOnline: false,
        isTouchDevice: true,
        hasCamera: true,
        hasGeolocation: true,
        hasNotifications: true,
        screenSize: { width: 375, height: 667 },
        devicePixelRatio: 2,
        platform: 'mobile',
      });

      const navItems = [
        { id: '1', label: 'Home', path: '/', icon: '🏠' },
      ];

      const { container } = render(
        <MobileOptimizedLayout
          header={<div>Header</div>}
          footer={<div>Footer</div>}
          navigationItems={navItems}
          showOfflineIndicator={true}
          enableSafeArea={true}
          className="custom-class"
        >
          <div>Main Content</div>
        </MobileOptimizedLayout>
      );

      // Verify all features are present
      expect(screen.getByText('Header')).toBeInTheDocument();
      expect(screen.getByText('Main Content')).toBeInTheDocument();
      expect(screen.getByText('Footer')).toBeInTheDocument();
      expect(screen.getByTestId('offline-indicator')).toBeInTheDocument();
      expect(screen.getByTestId('mobile-navigation')).toBeInTheDocument();

      // Verify layout classes
      const layoutDiv = container.firstChild as HTMLElement;
      expect(layoutDiv.className).toContain('mobile');
      expect(layoutDiv.className).toContain('safeArea');
      expect(layoutDiv.className).toContain('compact');
      expect(layoutDiv.className).toContain('custom-class');
    });
  });
});
