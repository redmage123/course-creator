/**
 * Navbar Component
 *
 * BUSINESS CONTEXT:
 * Main navigation bar for Course Creator Platform. Displayed across all authenticated
 * pages, providing access to key features and user account management.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Sticky navigation with platform branding
 * - Role-based navigation links
 * - User menu dropdown for account actions
 * - Responsive design with mobile menu
 * - Accessible navigation with ARIA attributes
 *
 * DESIGN PRINCIPLES:
 * - Tami design system colors and spacing
 * - Platform blue (#2563eb) for primary elements
 * - White background with subtle shadow
 * - Clean, professional appearance
 */

import React, { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../../hooks/useAuth';
import { Button } from '../../atoms/Button';
import styles from './Navbar.module.css';

export interface NavbarProps {
  /**
   * Application logo URL or text
   * @default 'Course Creator'
   */
  logo?: string | React.ReactNode;

  /**
   * Additional CSS class name
   */
  className?: string;
}

/**
 * Navbar Component
 *
 * WHY THIS APPROACH:
 * - Conditional rendering based on authentication state
 * - Role-based navigation links for different user types
 * - User menu dropdown for account management
 * - Sticky positioning for persistent navigation
 * - Mobile-responsive with hamburger menu
 *
 * @example
 * ```tsx
 * <Navbar logo="Course Creator Platform" />
 * ```
 */
export const Navbar: React.FC<NavbarProps> = ({
  logo = 'Course Creator',
  className,
}) => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const userMenuTriggerRef = useRef<HTMLButtonElement>(null);

  /**
   * Close dropdowns on Escape key
   */
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        if (isUserMenuOpen) {
          setIsUserMenuOpen(false);
          userMenuTriggerRef.current?.focus();
        }
        if (isMenuOpen) {
          setIsMenuOpen(false);
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isUserMenuOpen, isMenuOpen]);

  /**
   * Close user menu when clicking outside
   */
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        userMenuRef.current &&
        !userMenuRef.current.contains(event.target as Node)
      ) {
        setIsUserMenuOpen(false);
      }
    };

    if (isUserMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isUserMenuOpen]);

  /**
   * Check if a navigation link is active
   *
   * WHY THIS APPROACH:
   * - Exact match for home/dashboard routes
   * - Prefix match for nested routes (e.g., /admin/users matches /admin)
   * - Special handling for dashboard redirect
   */
  const isLinkActive = useMemo(() => {
    return (linkPath: string): boolean => {
      const currentPath = location.pathname;

      // Exact match
      if (currentPath === linkPath) return true;

      // For /dashboard, also check role-specific dashboards
      if (linkPath === '/dashboard') {
        return currentPath.startsWith('/dashboard');
      }

      // Prefix match for nested routes (but not root path)
      if (linkPath !== '/' && currentPath.startsWith(linkPath + '/')) {
        return true;
      }

      return false;
    };
  }, [location.pathname]);

  /**
   * Handle logout action
   */
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  /**
   * Get navigation links based on user role
   */
  const getNavLinks = () => {
    if (!isAuthenticated || !user) return [];

    const commonLinks = [
      { to: '/dashboard', label: 'Dashboard' },
    ];

    switch (user.role) {
      case 'site_admin':
        return [
          ...commonLinks,
          { to: '/admin/organizations', label: 'Organizations' },
          { to: '/admin/users', label: 'Users' },
          { to: '/admin/analytics', label: 'Analytics' },
        ];
      case 'organization_admin':
        return [
          ...commonLinks,
          { to: '/organization/members', label: 'Members' },
          { to: '/organization/courses', label: 'Courses' },
          { to: '/organization/analytics', label: 'Analytics' },
        ];
      case 'instructor':
        return [
          ...commonLinks,
          { to: '/courses', label: 'My Courses' },
          { to: '/students', label: 'Students' },
          { to: '/analytics', label: 'Analytics' },
        ];
      case 'student':
        return [
          ...commonLinks,
          { to: '/courses/my-courses', label: 'My Courses' },
          { to: '/labs', label: 'Labs' },
          { to: '/progress', label: 'Progress' },
        ];
      default:
        return commonLinks;
    }
  };

  const navLinks = getNavLinks();

  /**
   * Get user display name
   */
  const getUserDisplayName = () => {
    if (!user) return '';
    if (user.firstName && user.lastName) {
      return `${user.firstName} ${user.lastName}`;
    }
    return user.username;
  };

  /**
   * Get user initials for avatar
   */
  const getUserInitials = () => {
    if (!user) return '?';
    if (user.firstName && user.lastName) {
      return `${user.firstName[0]}${user.lastName[0]}`.toUpperCase();
    }
    return user.username[0].toUpperCase();
  };

  return (
    <nav className={`${styles.navbar} ${className || ''}`}>
      <div className={styles['navbar-container']}>
        {/* Logo */}
        <Link to="/" className={styles['navbar-logo']}>
          {typeof logo === 'string' ? (
            <span className={styles['logo-text']}>{logo}</span>
          ) : (
            logo
          )}
        </Link>

        {/* Navigation Links (Desktop) */}
        {isAuthenticated && navLinks.length > 0 && (
          <div className={styles['navbar-links']}>
            {navLinks.map((link) => {
              const active = isLinkActive(link.to);
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`${styles['nav-link']} ${active ? styles['nav-link-active'] : ''}`}
                  aria-current={active ? 'page' : undefined}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        )}

        {/* Right Section */}
        <div className={styles['navbar-right']}>
          {isAuthenticated && user ? (
            <>
              {/* Bug Report Icon */}
              <Link
                to="/bugs/submit"
                className={styles['icon-button']}
                title="Report a Bug"
                aria-label="Report a bug"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M8 2v4M16 2v4M12 14v4M12 14l-3 3m3-3l3 3M9 10h.01M15 10h.01M3 8h18v13a2 2 0 01-2 2H5a2 2 0 01-2-2V8zM5 8V6a2 2 0 012-2h10a2 2 0 012 2v2"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </Link>

              {/* User Menu */}
              <div ref={userMenuRef} className={styles['user-menu-container']}>
                <button
                  ref={userMenuTriggerRef}
                  className={styles['user-menu-trigger']}
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  aria-label="User menu"
                  aria-expanded={isUserMenuOpen}
                  aria-haspopup="true"
                >
                  {/* User Avatar */}
                  {user.avatar ? (
                    <img
                      src={user.avatar}
                      alt={getUserDisplayName()}
                      className={styles['user-avatar']}
                    />
                  ) : (
                    <div className={styles['user-avatar-placeholder']}>
                      {getUserInitials()}
                    </div>
                  )}
                  <span className={styles['user-name']}>
                    {getUserDisplayName()}
                  </span>
                  <svg
                    className={styles['dropdown-icon']}
                    width="12"
                    height="12"
                    viewBox="0 0 12 12"
                    fill="none"
                  >
                    <path
                      d="M2 4L6 8L10 4"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </button>

                {/* User Dropdown Menu */}
                {isUserMenuOpen && (
                  <div className={styles['user-dropdown']}>
                    <div className={styles['user-info']}>
                      <div className={styles['user-info-name']}>
                        {getUserDisplayName()}
                      </div>
                      <div className={styles['user-info-email']}>
                        {user.email}
                      </div>
                      <div className={styles['user-info-role']}>
                        {user.role.replace('_', ' ').toUpperCase()}
                      </div>
                    </div>
                    <div className={styles['dropdown-divider']} />
                    <Link
                      to="/settings"
                      className={styles['dropdown-item']}
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      Settings
                    </Link>
                    <Link
                      to="/profile"
                      className={styles['dropdown-item']}
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      Profile
                    </Link>
                    <Link
                      to="/bugs/submit"
                      className={styles['dropdown-item']}
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        style={{ marginRight: '8px', verticalAlign: 'middle' }}
                      >
                        <path
                          d="M8 2v4M16 2v4M12 14v4M12 14l-3 3m3-3l3 3M9 10h.01M15 10h.01M3 8h18v13a2 2 0 01-2 2H5a2 2 0 01-2-2V8zM5 8V6a2 2 0 012-2h10a2 2 0 012 2v2"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                      Report Bug
                    </Link>
                    <a
                      href="/docs/USER_GUIDE.pdf"
                      download="Course_Creator_User_Guide.pdf"
                      className={styles['dropdown-item']}
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        style={{ marginRight: '8px', verticalAlign: 'middle' }}
                      >
                        <path
                          d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                        <path
                          d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                      User Guide (PDF)
                    </a>
                    <div className={styles['dropdown-divider']} />
                    <button
                      className={styles['dropdown-item-button']}
                      onClick={handleLogout}
                    >
                      Logout
                    </button>
                  </div>
                )}
              </div>

              {/* Mobile Menu Toggle */}
              <button
                className={styles['mobile-menu-toggle']}
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                aria-label="Toggle mobile menu"
                aria-expanded={isMenuOpen}
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  {isMenuOpen ? (
                    <path
                      d="M6 18L18 6M6 6L18 18"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  ) : (
                    <path
                      d="M4 6H20M4 12H20M4 18H20"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  )}
                </svg>
              </button>
            </>
          ) : (
            <>
              <a
                href="/docs/USER_GUIDE.pdf"
                download="Course_Creator_User_Guide.pdf"
                className={styles['help-link']}
                title="Download User Guide"
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path
                    d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </a>
              <Link to="/login">
                <Button variant="ghost" size="medium">
                  Login
                </Button>
              </Link>
              <Link to="/register">
                <Button variant="primary" size="medium">
                  Sign Up
                </Button>
              </Link>
            </>
          )}
        </div>
      </div>

      {/* Mobile Navigation Menu */}
      {isAuthenticated && isMenuOpen && navLinks.length > 0 && (
        <div className={styles['mobile-menu']}>
          {navLinks.map((link) => {
            const active = isLinkActive(link.to);
            return (
              <Link
                key={link.to}
                to={link.to}
                className={`${styles['mobile-menu-link']} ${active ? styles['mobile-menu-link-active'] : ''}`}
                onClick={() => setIsMenuOpen(false)}
                aria-current={active ? 'page' : undefined}
              >
                {link.label}
              </Link>
            );
          })}
        </div>
      )}
    </nav>
  );
};
