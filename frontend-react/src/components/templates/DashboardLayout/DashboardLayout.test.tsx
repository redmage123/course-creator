/**
 * Dashboard Layout Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring DashboardLayout provides consistent structure
 * and navigation across all dashboard pages.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests layout structure, navbar integration, sidebar, and accessibility
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { DashboardLayout } from './DashboardLayout';

// Mock useAuth hook for Navbar
vi.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: null,
    isAuthenticated: false,
    logout: vi.fn(),
  }),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

describe('DashboardLayout Component', () => {
  const renderDashboardLayout = (props = {}) => {
    return render(
      <BrowserRouter>
        <DashboardLayout {...props}>
          <div data-testid="test-content">Test Content</div>
        </DashboardLayout>
      </BrowserRouter>
    );
  };

  describe('Rendering', () => {
    it('renders children content', () => {
      renderDashboardLayout();
      expect(screen.getByTestId('test-content')).toBeInTheDocument();
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('renders Navbar component', () => {
      renderDashboardLayout();
      // Navbar should render default logo
      expect(screen.getByText('Course Creator')).toBeInTheDocument();
    });

    it('renders content without sidebar by default', () => {
      renderDashboardLayout();
      const content = screen.getByTestId('test-content');
      expect(content).toBeInTheDocument();
    });

    it('renders with sidebar when provided', () => {
      const sidebar = <div data-testid="test-sidebar">Sidebar Content</div>;
      renderDashboardLayout({ sidebar });

      expect(screen.getByTestId('test-sidebar')).toBeInTheDocument();
      expect(screen.getByText('Sidebar Content')).toBeInTheDocument();
    });
  });

  describe('Props', () => {
    it('passes custom logo to Navbar', () => {
      renderDashboardLayout({ logo: 'My Custom App' });
      expect(screen.getByText('My Custom App')).toBeInTheDocument();
    });

    it('applies custom maxWidth', () => {
      const { container } = renderDashboardLayout({ maxWidth: '1200px' });
      const main = container.querySelector('main');
      expect(main).toHaveStyle({ maxWidth: '1200px' });
    });

    it('uses default maxWidth of 1440px', () => {
      const { container } = renderDashboardLayout();
      const main = container.querySelector('main');
      expect(main).toHaveStyle({ maxWidth: '1440px' });
    });

    it('applies custom className', () => {
      const { container } = renderDashboardLayout({ className: 'custom-dashboard' });
      const layout = container.firstChild;
      expect(layout).toHaveClass('custom-dashboard');
    });
  });

  describe('Layout Structure', () => {
    it('has correct DOM structure without sidebar', () => {
      const { container } = renderDashboardLayout();

      // Check for layout wrapper
      const layout = container.querySelector('[class*="dashboard-layout"]');
      expect(layout).toBeInTheDocument();

      // Check for container
      const dashboardContainer = container.querySelector('[class*="dashboard-container"]');
      expect(dashboardContainer).toBeInTheDocument();

      // Check for main element
      const main = container.querySelector('main');
      expect(main).toBeInTheDocument();
    });

    it('has correct DOM structure with sidebar', () => {
      const sidebar = <div>Sidebar</div>;
      const { container } = renderDashboardLayout({ sidebar });

      // Check for sidebar container
      const sidebarElement = container.querySelector('aside');
      expect(sidebarElement).toBeInTheDocument();

      // Check for with-sidebar wrapper
      const withSidebar = container.querySelector('[class*="dashboard-with-sidebar"]');
      expect(withSidebar).toBeInTheDocument();

      // Check for content wrapper
      const content = container.querySelector('[class*="dashboard-content"]');
      expect(content).toBeInTheDocument();
    });
  });

  describe('Sidebar', () => {
    it('renders sidebar content correctly', () => {
      const sidebar = (
        <nav data-testid="sidebar-nav">
          <a href="/link1">Link 1</a>
          <a href="/link2">Link 2</a>
        </nav>
      );

      renderDashboardLayout({ sidebar });

      const sidebarNav = screen.getByTestId('sidebar-nav');
      expect(sidebarNav).toBeInTheDocument();
      expect(screen.getByText('Link 1')).toBeInTheDocument();
      expect(screen.getByText('Link 2')).toBeInTheDocument();
    });

    it('sidebar is within aside element', () => {
      const sidebar = <div data-testid="sidebar-content">Sidebar</div>;
      const { container } = renderDashboardLayout({ sidebar });

      const aside = container.querySelector('aside');
      const sidebarContent = screen.getByTestId('sidebar-content');

      expect(aside).toContainElement(sidebarContent);
    });

    it('does not render aside element without sidebar', () => {
      const { container } = renderDashboardLayout();
      const aside = container.querySelector('aside');
      expect(aside).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('uses semantic HTML elements', () => {
      const { container } = renderDashboardLayout();

      expect(container.querySelector('nav')).toBeInTheDocument(); // Navbar
      expect(container.querySelector('main')).toBeInTheDocument();
    });

    it('uses aside for sidebar', () => {
      const sidebar = <div>Sidebar</div>;
      const { container } = renderDashboardLayout({ sidebar });

      const aside = container.querySelector('aside');
      expect(aside).toBeInTheDocument();
      expect(aside?.tagName).toBe('ASIDE');
    });

    it('main element contains content', () => {
      renderDashboardLayout();

      const main = screen.getByRole('main');
      const content = screen.getByTestId('test-content');

      expect(main).toContainElement(content);
    });
  });

  describe('Integration', () => {
    it('renders complex dashboard content', () => {
      const sidebar = (
        <nav>
          <ul>
            <li><a href="/courses">Courses</a></li>
            <li><a href="/students">Students</a></li>
          </ul>
        </nav>
      );

      const content = (
        <div data-testid="dashboard-content">
          <h1>Dashboard</h1>
          <div className="cards">
            <div className="card">Card 1</div>
            <div className="card">Card 2</div>
          </div>
        </div>
      );

      render(
        <BrowserRouter>
          <DashboardLayout sidebar={sidebar}>
            {content}
          </DashboardLayout>
        </BrowserRouter>
      );

      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Courses')).toBeInTheDocument();
      expect(screen.getByText('Students')).toBeInTheDocument();
      expect(screen.getByText('Card 1')).toBeInTheDocument();
      expect(screen.getByText('Card 2')).toBeInTheDocument();
    });

    it('renders ReactNode logo in navbar', () => {
      const logoElement = (
        <div data-testid="custom-logo">
          <img src="/logo.png" alt="Logo" />
          <span>Platform</span>
        </div>
      );

      renderDashboardLayout({ logo: logoElement });

      expect(screen.getByTestId('custom-logo')).toBeInTheDocument();
      expect(screen.getByAltText('Logo')).toBeInTheDocument();
      expect(screen.getByText('Platform')).toBeInTheDocument();
    });
  });

  describe('Multiple Children', () => {
    it('renders multiple child elements', () => {
      render(
        <BrowserRouter>
          <DashboardLayout>
            <h1>Title</h1>
            <p>Paragraph</p>
            <button>Button</button>
          </DashboardLayout>
        </BrowserRouter>
      );

      expect(screen.getByText('Title')).toBeInTheDocument();
      expect(screen.getByText('Paragraph')).toBeInTheDocument();
      expect(screen.getByText('Button')).toBeInTheDocument();
    });
  });
});
