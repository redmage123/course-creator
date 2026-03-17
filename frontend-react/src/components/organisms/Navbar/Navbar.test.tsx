/**
 * Navbar Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring Navbar provides consistent navigation experience
 * with proper authentication handling and role-based access.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Mocks useAuth hook for different authentication states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { Navbar } from './Navbar';

// Mock useAuth hook
const mockLogout = vi.fn();
const mockNavigate = vi.fn();

vi.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: mockUser,
    isAuthenticated: mockIsAuthenticated,
    logout: mockLogout,
  }),
}));

let mockPathname = '/';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ pathname: mockPathname }),
  };
});

let mockUser: any = null;
let mockIsAuthenticated = false;

describe('Navbar Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUser = null;
    mockIsAuthenticated = false;
    mockPathname = '/';
  });

  const renderNavbar = (props = {}) => {
    return render(
      <BrowserRouter>
        <Navbar {...props} />
      </BrowserRouter>
    );
  };

  describe('Unauthenticated State', () => {
    it('renders logo', () => {
      renderNavbar();
      expect(screen.getByText('Course Creator')).toBeInTheDocument();
    });

    it('renders login and sign up buttons', () => {
      renderNavbar();
      expect(screen.getByText('Login')).toBeInTheDocument();
      expect(screen.getByText('Sign Up')).toBeInTheDocument();
    });

    it('does not render navigation links', () => {
      renderNavbar();
      expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
    });

    it('does not render user menu', () => {
      renderNavbar();
      expect(screen.queryByLabelText('User menu')).not.toBeInTheDocument();
    });

    it('renders custom logo', () => {
      renderNavbar({ logo: 'My Custom Platform' });
      expect(screen.getByText('My Custom Platform')).toBeInTheDocument();
    });
  });

  describe('Authenticated State - Student', () => {
    beforeEach(() => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '1',
        username: 'student1',
        email: 'student@example.com',
        firstName: 'John',
        lastName: 'Doe',
        role: 'student',
      };
    });

    it('renders user name', () => {
      renderNavbar();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    it('renders student navigation links', () => {
      renderNavbar();
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('My Courses')).toBeInTheDocument();
      expect(screen.getByText('Labs')).toBeInTheDocument();
      expect(screen.getByText('Progress')).toBeInTheDocument();
    });

    it('does not render login/signup buttons', () => {
      renderNavbar();
      expect(screen.queryByText('Login')).not.toBeInTheDocument();
      expect(screen.queryByText('Sign Up')).not.toBeInTheDocument();
    });

    it('renders user initials when no avatar', () => {
      renderNavbar();
      expect(screen.getByText('JD')).toBeInTheDocument();
    });

    it('renders user avatar when provided', () => {
      mockUser.avatar = 'https://example.com/avatar.jpg';
      renderNavbar();
      const avatar = screen.getByAltText('John Doe');
      expect(avatar).toBeInTheDocument();
      expect(avatar).toHaveAttribute('src', 'https://example.com/avatar.jpg');
    });
  });

  describe('Authenticated State - Instructor', () => {
    beforeEach(() => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '2',
        username: 'instructor1',
        email: 'instructor@example.com',
        role: 'instructor',
      };
    });

    it('renders instructor navigation links', () => {
      renderNavbar();
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('My Courses')).toBeInTheDocument();
      expect(screen.getByText('Students')).toBeInTheDocument();
      expect(screen.getByText('Analytics')).toBeInTheDocument();
    });

    it('uses username when no first/last name', () => {
      renderNavbar();
      expect(screen.getByText('instructor1')).toBeInTheDocument();
    });

    it('renders username initial when no full name', () => {
      renderNavbar();
      expect(screen.getByText('I')).toBeInTheDocument();
    });
  });

  describe('Authenticated State - Org Admin', () => {
    beforeEach(() => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '3',
        username: 'orgadmin1',
        email: 'orgadmin@example.com',
        firstName: 'Jane',
        lastName: 'Smith',
        role: 'org_admin',
      };
    });

    it('renders org admin navigation links', () => {
      renderNavbar();
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Members')).toBeInTheDocument();
      expect(screen.getByText('Courses')).toBeInTheDocument();
      expect(screen.getByText('Analytics')).toBeInTheDocument();
    });
  });

  describe('Authenticated State - Site Admin', () => {
    beforeEach(() => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '4',
        username: 'siteadmin',
        email: 'admin@example.com',
        firstName: 'Admin',
        lastName: 'User',
        role: 'site_admin',
      };
    });

    it('renders site admin navigation links', () => {
      renderNavbar();
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Organizations')).toBeInTheDocument();
      expect(screen.getByText('Users')).toBeInTheDocument();
      expect(screen.getByText('Analytics')).toBeInTheDocument();
    });
  });

  describe('User Menu Interactions', () => {
    beforeEach(() => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'student',
      };
    });

    it('opens user menu on click', async () => {
      renderNavbar();

      const menuButton = screen.getByLabelText('User menu');
      await userEvent.click(menuButton);

      expect(screen.getByText('test@example.com')).toBeInTheDocument();
      expect(screen.getByText('STUDENT')).toBeInTheDocument();
    });

    it('shows settings and profile links', async () => {
      renderNavbar();

      const menuButton = screen.getByLabelText('User menu');
      await userEvent.click(menuButton);

      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByText('Profile')).toBeInTheDocument();
    });

    it('shows logout button', async () => {
      renderNavbar();

      const menuButton = screen.getByLabelText('User menu');
      await userEvent.click(menuButton);

      expect(screen.getByText('Logout')).toBeInTheDocument();
    });

    it('calls logout on logout button click', async () => {
      renderNavbar();

      const menuButton = screen.getByLabelText('User menu');
      await userEvent.click(menuButton);

      const logoutButton = screen.getByText('Logout');
      await userEvent.click(logoutButton);

      expect(mockLogout).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });

    it('displays user role in correct format', async () => {
      renderNavbar();

      const menuButton = screen.getByLabelText('User menu');
      await userEvent.click(menuButton);

      // Student role should be displayed as "STUDENT"
      expect(screen.getByText('STUDENT')).toBeInTheDocument();
    });
  });

  describe('Mobile Menu', () => {
    beforeEach(() => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        role: 'student',
      };
    });

    it('renders mobile menu toggle button', () => {
      renderNavbar();
      expect(screen.getByLabelText('Toggle mobile menu')).toBeInTheDocument();
    });

    it('opens mobile menu on toggle click', async () => {
      renderNavbar();

      const toggleButton = screen.getByLabelText('Toggle mobile menu');
      await userEvent.click(toggleButton);

      expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        role: 'student',
      };
    });

    it('user menu has proper ARIA attributes', () => {
      renderNavbar();

      const menuButton = screen.getByLabelText('User menu');
      expect(menuButton).toHaveAttribute('aria-haspopup', 'true');
      expect(menuButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('mobile menu toggle has proper ARIA attributes', () => {
      renderNavbar();

      const toggleButton = screen.getByLabelText('Toggle mobile menu');
      expect(toggleButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('updates aria-expanded when menu is opened', async () => {
      renderNavbar();

      const menuButton = screen.getByLabelText('User menu');
      await userEvent.click(menuButton);

      expect(menuButton).toHaveAttribute('aria-expanded', 'true');
    });
  });

  describe('Custom Props', () => {
    it('applies custom className', () => {
      const { container } = renderNavbar({ className: 'custom-navbar' });
      const navbar = container.firstChild;
      expect(navbar).toHaveClass('custom-navbar');
    });

    it('renders ReactNode logo', () => {
      const logoElement = <div data-testid="custom-logo">Custom Logo</div>;
      renderNavbar({ logo: logoElement });
      expect(screen.getByTestId('custom-logo')).toBeInTheDocument();
    });
  });

  describe('Active Link Indicator', () => {
    beforeEach(() => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '1',
        username: 'student1',
        email: 'student@example.com',
        firstName: 'John',
        lastName: 'Doe',
        role: 'student',
      };
    });

    it('marks Dashboard link as active when on /dashboard', () => {
      mockPathname = '/dashboard';
      renderNavbar();

      const dashboardLink = screen.getByRole('link', { name: 'Dashboard' });
      expect(dashboardLink).toHaveAttribute('aria-current', 'page');
    });

    it('marks Dashboard link as active when on role-specific dashboard', () => {
      mockPathname = '/dashboard/student';
      renderNavbar();

      const dashboardLink = screen.getByRole('link', { name: 'Dashboard' });
      expect(dashboardLink).toHaveAttribute('aria-current', 'page');
    });

    it('marks My Courses link as active when on /courses/my-courses', () => {
      mockPathname = '/courses/my-courses';
      renderNavbar();

      const myCoursesLink = screen.getByRole('link', { name: 'My Courses' });
      expect(myCoursesLink).toHaveAttribute('aria-current', 'page');
    });

    it('marks Labs link as active when on /labs', () => {
      mockPathname = '/labs';
      renderNavbar();

      const labsLink = screen.getByRole('link', { name: 'Labs' });
      expect(labsLink).toHaveAttribute('aria-current', 'page');
    });

    it('marks Labs link as active when on nested lab route', () => {
      mockPathname = '/labs/123/course/456';
      renderNavbar();

      const labsLink = screen.getByRole('link', { name: 'Labs' });
      expect(labsLink).toHaveAttribute('aria-current', 'page');
    });

    it('does not mark non-active links with aria-current', () => {
      mockPathname = '/dashboard';
      renderNavbar();

      const labsLink = screen.getByRole('link', { name: 'Labs' });
      expect(labsLink).not.toHaveAttribute('aria-current');
    });

    it('active link has correct CSS class applied', () => {
      mockPathname = '/dashboard';
      renderNavbar();

      const dashboardLink = screen.getByRole('link', { name: 'Dashboard' });
      expect(dashboardLink.className).toContain('nav-link-active');
    });

    it('non-active link does not have active CSS class', () => {
      mockPathname = '/dashboard';
      renderNavbar();

      const labsLink = screen.getByRole('link', { name: 'Labs' });
      expect(labsLink.className).not.toContain('nav-link-active');
    });

    describe('Site Admin Active Links', () => {
      beforeEach(() => {
        mockUser = {
          id: '4',
          username: 'siteadmin',
          email: 'admin@example.com',
          firstName: 'Admin',
          lastName: 'User',
          role: 'site_admin',
        };
      });

      it('marks Organizations link as active when on /admin/organizations', () => {
        mockPathname = '/admin/organizations';
        renderNavbar();

        const orgLink = screen.getByRole('link', { name: 'Organizations' });
        expect(orgLink).toHaveAttribute('aria-current', 'page');
      });

      it('marks Users link as active when on /admin/users', () => {
        mockPathname = '/admin/users';
        renderNavbar();

        const usersLink = screen.getByRole('link', { name: 'Users' });
        expect(usersLink).toHaveAttribute('aria-current', 'page');
      });
    });

    describe('Org Admin Active Links', () => {
      beforeEach(() => {
        mockUser = {
          id: '3',
          username: 'orgadmin1',
          email: 'orgadmin@example.com',
          firstName: 'Jane',
          lastName: 'Smith',
          role: 'org_admin',
        };
      });

      it('marks Members link as active when on /organization/members', () => {
        mockPathname = '/organization/members';
        renderNavbar();

        const membersLink = screen.getByRole('link', { name: 'Members' });
        expect(membersLink).toHaveAttribute('aria-current', 'page');
      });
    });
  });
});
