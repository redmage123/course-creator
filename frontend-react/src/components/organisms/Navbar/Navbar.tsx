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

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

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
      case 'org_admin':
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
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={styles['nav-link']}
              >
                {link.label}
              </Link>
            ))}
          </div>
        )}

        {/* Right Section */}
        <div className={styles['navbar-right']}>
          {isAuthenticated && user ? (
            <>
              {/* User Menu */}
              <div className={styles['user-menu-container']}>
                <button
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
          {navLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={styles['mobile-menu-link']}
              onClick={() => setIsMenuOpen(false)}
            >
              {link.label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
};
