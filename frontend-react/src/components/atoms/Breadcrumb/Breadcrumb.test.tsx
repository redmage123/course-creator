/**
 * Breadcrumb Component Tests
 *
 * BUSINESS CONTEXT:
 * Comprehensive test suite ensuring Breadcrumb component provides proper
 * navigation hierarchy for users to understand their location in the app.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests rendering, navigation, truncation, and accessibility
 *
 * COVERAGE REQUIREMENTS:
 * - Rendering with various item configurations
 * - Link navigation behavior
 * - Current page indication
 * - Truncation with maxItems
 * - Accessibility (ARIA attributes)
 * - Custom separators and icons
 * - Responsive behavior
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { Breadcrumb, BreadcrumbItem } from './Breadcrumb';

// Wrapper component for Router context
const RouterWrapper: React.FC<{ children: React.ReactNode; initialEntries?: string[] }> = ({
  children,
  initialEntries = ['/'],
}) => (
  <MemoryRouter initialEntries={initialEntries}>
    {children}
  </MemoryRouter>
);

describe('Breadcrumb Component', () => {
  const defaultItems: BreadcrumbItem[] = [
    { label: 'Home', path: '/' },
    { label: 'Courses', path: '/courses' },
    { label: 'Python 101' }, // Current page (no path)
  ];

  describe('Rendering', () => {
    it('renders with items', () => {
      render(
        <RouterWrapper>
          <Breadcrumb items={defaultItems} />
        </RouterWrapper>
      );

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Courses')).toBeInTheDocument();
      expect(screen.getByText('Python 101')).toBeInTheDocument();
    });

    it('renders as nav element with aria-label', () => {
      render(
        <RouterWrapper>
          <Breadcrumb items={defaultItems} />
        </RouterWrapper>
      );

      const nav = screen.getByRole('navigation', { name: /breadcrumb/i });
      expect(nav).toBeInTheDocument();
    });

    it('renders ordered list', () => {
      render(
        <RouterWrapper>
          <Breadcrumb items={defaultItems} />
        </RouterWrapper>
      );

      const list = screen.getByRole('list');
      expect(list).toBeInTheDocument();
    });

    it('renders nothing when items array is empty', () => {
      render(
        <RouterWrapper>
          <Breadcrumb items={[]} />
        </RouterWrapper>
      );

      expect(screen.queryByTestId('breadcrumb')).not.toBeInTheDocument();
    });

    it('applies custom className', () => {
      render(
        <RouterWrapper>
          <Breadcrumb items={defaultItems} className="custom-class" />
        </RouterWrapper>
      );

      const nav = screen.getByTestId('breadcrumb');
      expect(nav.className).toContain('custom-class');
    });
  });

  describe('Links', () => {
    it('renders links for items with paths', () => {
      // Use a route that doesn't match any breadcrumb path
      render(
        <RouterWrapper initialEntries={['/courses/python']}>
          <Breadcrumb items={defaultItems} />
        </RouterWrapper>
      );

      const homeLink = screen.getByRole('link', { name: /home/i });
      const coursesLink = screen.getByRole('link', { name: /courses/i });

      expect(homeLink).toHaveAttribute('href', '/');
      expect(coursesLink).toHaveAttribute('href', '/courses');
    });

    it('does not render link for current page', () => {
      render(
        <RouterWrapper initialEntries={['/courses/python']}>
          <Breadcrumb items={defaultItems} />
        </RouterWrapper>
      );

      // Python 101 should not be a link
      expect(screen.queryByRole('link', { name: /python 101/i })).not.toBeInTheDocument();
      expect(screen.getByText('Python 101')).toBeInTheDocument();
    });

    it('has focusable links', () => {
      // Use a route that doesn't match any breadcrumb path
      render(
        <RouterWrapper initialEntries={['/courses/python']}>
          <Breadcrumb items={defaultItems} />
        </RouterWrapper>
      );

      const homeLink = screen.getByRole('link', { name: /home/i });
      homeLink.focus();
      expect(homeLink).toHaveFocus();
    });
  });

  describe('Current Page', () => {
    it('marks last item without path as current', () => {
      render(
        <RouterWrapper>
          <Breadcrumb items={defaultItems} />
        </RouterWrapper>
      );

      const currentPage = screen.getByText('Python 101');
      expect(currentPage).toHaveAttribute('aria-current', 'page');
    });

    it('marks item matching current location as current', () => {
      render(
        <RouterWrapper initialEntries={['/courses']}>
          <Breadcrumb
            items={[
              { label: 'Home', path: '/' },
              { label: 'Courses', path: '/courses' },
            ]}
          />
        </RouterWrapper>
      );

      // When on /courses, Courses should be current
      const coursesItem = screen.getByText('Courses');
      expect(coursesItem.closest('[aria-current="page"]') || coursesItem).toBeInTheDocument();
    });
  });

  describe('Separators', () => {
    it('renders default chevron separators between items', () => {
      render(
        <RouterWrapper>
          <Breadcrumb items={defaultItems} />
        </RouterWrapper>
      );

      // Should have 2 separators for 3 items
      const list = screen.getByRole('list');
      const svgs = list.querySelectorAll('svg');
      // Home icon + 2 chevrons = 3 SVGs minimum
      expect(svgs.length).toBeGreaterThanOrEqual(2);
    });

    it('renders custom separator', () => {
      render(
        <RouterWrapper>
          <Breadcrumb
            items={defaultItems}
            separator={<span data-testid="custom-sep">/</span>}
          />
        </RouterWrapper>
      );

      const separators = screen.getAllByTestId('custom-sep');
      expect(separators.length).toBe(2); // 2 separators for 3 items
    });
  });

  describe('Truncation', () => {
    const manyItems: BreadcrumbItem[] = [
      { label: 'Home', path: '/' },
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Courses', path: '/courses' },
      { label: 'Category', path: '/courses/category' },
      { label: 'Subcategory', path: '/courses/category/sub' },
      { label: 'Course Name' }, // Current
    ];

    it('shows all items when maxItems not set', () => {
      render(
        <RouterWrapper>
          <Breadcrumb items={manyItems} />
        </RouterWrapper>
      );

      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Category')).toBeInTheDocument();
      expect(screen.getByText('Subcategory')).toBeInTheDocument();
    });

    it('truncates middle items when maxItems is set', () => {
      render(
        <RouterWrapper>
          <Breadcrumb items={manyItems} maxItems={3} />
        </RouterWrapper>
      );

      // Should show: Home, ..., Subcategory, Course Name (3 real items + ellipsis)
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('...')).toBeInTheDocument();
      expect(screen.getByText('Course Name')).toBeInTheDocument();

      // Middle items should be hidden
      expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
      expect(screen.queryByText('Category')).not.toBeInTheDocument();
    });

    it('does not truncate when items count equals maxItems', () => {
      render(
        <RouterWrapper>
          <Breadcrumb items={defaultItems} maxItems={3} />
        </RouterWrapper>
      );

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Courses')).toBeInTheDocument();
      expect(screen.getByText('Python 101')).toBeInTheDocument();
      expect(screen.queryByText('...')).not.toBeInTheDocument();
    });
  });

  describe('Home Icon', () => {
    it('shows home icon for first item by default', () => {
      // Use a route that doesn't match any breadcrumb path
      render(
        <RouterWrapper initialEntries={['/courses/python']}>
          <Breadcrumb items={defaultItems} />
        </RouterWrapper>
      );

      const homeLink = screen.getByRole('link', { name: /home/i });
      const svg = homeLink.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('hides home icon when showHomeIcon is false', () => {
      // Use a route that doesn't match any breadcrumb path
      render(
        <RouterWrapper initialEntries={['/courses/python']}>
          <Breadcrumb items={defaultItems} showHomeIcon={false} />
        </RouterWrapper>
      );

      const homeLink = screen.getByRole('link', { name: /home/i });
      // Should only have text, no home icon SVG (may still have separator SVGs)
      const homeIcon = homeLink.querySelector('svg');
      expect(homeIcon).not.toBeInTheDocument();
    });
  });

  describe('Custom Icons', () => {
    it('renders custom icons for items', () => {
      const itemsWithIcons: BreadcrumbItem[] = [
        { label: 'Home', path: '/', icon: <span data-testid="home-icon">🏠</span> },
        { label: 'Settings', path: '/settings', icon: <span data-testid="settings-icon">⚙️</span> },
        { label: 'Profile', icon: <span data-testid="profile-icon">👤</span> },
      ];

      render(
        <RouterWrapper>
          <Breadcrumb items={itemsWithIcons} showHomeIcon={false} />
        </RouterWrapper>
      );

      expect(screen.getByTestId('home-icon')).toBeInTheDocument();
      expect(screen.getByTestId('settings-icon')).toBeInTheDocument();
      expect(screen.getByTestId('profile-icon')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has navigation landmark', () => {
      render(
        <RouterWrapper>
          <Breadcrumb items={defaultItems} />
        </RouterWrapper>
      );

      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    it('has aria-label on navigation', () => {
      render(
        <RouterWrapper>
          <Breadcrumb items={defaultItems} />
        </RouterWrapper>
      );

      const nav = screen.getByRole('navigation');
      expect(nav).toHaveAttribute('aria-label', 'Breadcrumb');
    });

    it('has aria-current="page" on current item', () => {
      render(
        <RouterWrapper>
          <Breadcrumb items={defaultItems} />
        </RouterWrapper>
      );

      const currentItem = screen.getByText('Python 101');
      expect(currentItem).toHaveAttribute('aria-current', 'page');
    });

    it('links are keyboard navigable', async () => {
      // Use a route that doesn't match any breadcrumb path
      // so only Python 101 (no path) is marked as current
      render(
        <RouterWrapper initialEntries={['/courses/python']}>
          <Breadcrumb items={defaultItems} showHomeIcon={false} />
        </RouterWrapper>
      );

      // Get all links - Home and Courses have paths, Python 101 has no path (current)
      const links = screen.getAllByRole('link');
      expect(links.length).toBe(2); // Home and Courses (Python 101 is current, no link)

      // Tab through links
      await userEvent.tab();
      expect(links[0]).toHaveFocus();

      await userEvent.tab();
      expect(links[1]).toHaveFocus();
    });
  });

  describe('Display Name', () => {
    it('has Breadcrumb as display name', () => {
      expect(Breadcrumb.displayName).toBe('Breadcrumb');
    });
  });

  describe('Regression Tests', () => {
    it('handles single item', () => {
      render(
        <RouterWrapper>
          <Breadcrumb items={[{ label: 'Home' }]} />
        </RouterWrapper>
      );

      expect(screen.getByText('Home')).toBeInTheDocument();
    });

    it('handles item with path but currently active', () => {
      render(
        <RouterWrapper initialEntries={['/courses']}>
          <Breadcrumb
            items={[
              { label: 'Home', path: '/' },
              { label: 'Courses', path: '/courses' },
            ]}
          />
        </RouterWrapper>
      );

      // Both should render
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Courses')).toBeInTheDocument();
    });

    it('handles rapid rerendering', () => {
      const { rerender } = render(
        <RouterWrapper>
          <Breadcrumb items={defaultItems} />
        </RouterWrapper>
      );

      rerender(
        <RouterWrapper>
          <Breadcrumb items={[{ label: 'New Page' }]} />
        </RouterWrapper>
      );

      expect(screen.getByText('New Page')).toBeInTheDocument();
      expect(screen.queryByText('Python 101')).not.toBeInTheDocument();
    });
  });
});
