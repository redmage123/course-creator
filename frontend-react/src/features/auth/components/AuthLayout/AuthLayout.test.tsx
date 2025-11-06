/**
 * Authentication Layout Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring AuthLayout provides consistent structure
 * for all authentication pages.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests rendering, props, accessibility, and responsive behavior
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AuthLayout } from './AuthLayout';

describe('AuthLayout Component', () => {
  describe('Rendering', () => {
    it('renders children content', () => {
      render(
        <AuthLayout>
          <div data-testid="test-content">Test Content</div>
        </AuthLayout>
      );

      expect(screen.getByTestId('test-content')).toBeInTheDocument();
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('renders without title and subtitle', () => {
      render(
        <AuthLayout>
          <div>Content</div>
        </AuthLayout>
      );

      expect(screen.queryByRole('heading')).not.toBeInTheDocument();
    });

    it('renders with title only', () => {
      render(
        <AuthLayout title="Sign In">
          <div>Content</div>
        </AuthLayout>
      );

      expect(screen.getByRole('heading', { name: 'Sign In' })).toBeInTheDocument();
    });

    it('renders with subtitle only', () => {
      render(
        <AuthLayout subtitle="Welcome back!">
          <div>Content</div>
        </AuthLayout>
      );

      expect(screen.getByText('Welcome back!')).toBeInTheDocument();
    });

    it('renders with both title and subtitle', () => {
      render(
        <AuthLayout title="Sign In" subtitle="Welcome back to your account">
          <div>Content</div>
        </AuthLayout>
      );

      expect(screen.getByRole('heading', { name: 'Sign In' })).toBeInTheDocument();
      expect(screen.getByText('Welcome back to your account')).toBeInTheDocument();
    });
  });

  describe('Props', () => {
    it('applies custom maxWidth', () => {
      const { container } = render(
        <AuthLayout maxWidth="600px">
          <div>Content</div>
        </AuthLayout>
      );

      const authContainer = container.querySelector('[style*="max-width"]');
      expect(authContainer).toHaveStyle({ maxWidth: '600px' });
    });

    it('uses default maxWidth of 480px', () => {
      const { container } = render(
        <AuthLayout>
          <div>Content</div>
        </AuthLayout>
      );

      const authContainer = container.querySelector('[style*="max-width"]');
      expect(authContainer).toHaveStyle({ maxWidth: '480px' });
    });

    it('applies custom className', () => {
      const { container } = render(
        <AuthLayout className="custom-class">
          <div>Content</div>
        </AuthLayout>
      );

      const authLayout = container.firstChild;
      expect(authLayout).toHaveClass('custom-class');
    });

    it('supports all maxWidth options', () => {
      const widths: Array<'480px' | '520px' | '600px'> = ['480px', '520px', '600px'];

      widths.forEach((width) => {
        const { container } = render(
          <AuthLayout maxWidth={width}>
            <div>Content</div>
          </AuthLayout>
        );

        const authContainer = container.querySelector('[style*="max-width"]');
        expect(authContainer).toHaveStyle({ maxWidth: width });
      });
    });
  });

  describe('Structure', () => {
    it('has correct DOM structure with title', () => {
      const { container } = render(
        <AuthLayout title="Test Title" subtitle="Test Subtitle">
          <div data-testid="content">Content</div>
        </AuthLayout>
      );

      // Check outer layout div exists
      const authLayout = container.querySelector('[class*="auth-layout"]');
      expect(authLayout).toBeInTheDocument();

      // Check container div exists
      const authContainer = container.querySelector('[class*="auth-container"]');
      expect(authContainer).toBeInTheDocument();

      // Check header div exists when title provided
      const authHeader = container.querySelector('[class*="auth-header"]');
      expect(authHeader).toBeInTheDocument();

      // Check content is present
      expect(screen.getByTestId('content')).toBeInTheDocument();
    });

    it('omits header when no title or subtitle', () => {
      const { container } = render(
        <AuthLayout>
          <div>Content</div>
        </AuthLayout>
      );

      const authHeader = container.querySelector('[class*="auth-header"]');
      expect(authHeader).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('uses h1 for title', () => {
      render(
        <AuthLayout title="Sign In">
          <div>Content</div>
        </AuthLayout>
      );

      const heading = screen.getByRole('heading', { name: 'Sign In' });
      expect(heading.tagName).toBe('H1');
    });

    it('subtitle has proper semantic markup', () => {
      render(
        <AuthLayout subtitle="Welcome back">
          <div>Content</div>
        </AuthLayout>
      );

      const subtitle = screen.getByText('Welcome back');
      expect(subtitle.tagName).toBe('P');
    });
  });

  describe('Integration', () => {
    it('renders complex auth form structure', () => {
      render(
        <AuthLayout title="Create Account" subtitle="Join us today">
          <form data-testid="auth-form">
            <input type="email" placeholder="Email" />
            <input type="password" placeholder="Password" />
            <button type="submit">Submit</button>
          </form>
        </AuthLayout>
      );

      expect(screen.getByRole('heading', { name: 'Create Account' })).toBeInTheDocument();
      expect(screen.getByText('Join us today')).toBeInTheDocument();
      expect(screen.getByTestId('auth-form')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument();
    });

    it('renders success state content', () => {
      render(
        <AuthLayout>
          <div data-testid="success-state">
            <h2>Success!</h2>
            <p>Your account has been created.</p>
            <button>Continue</button>
          </div>
        </AuthLayout>
      );

      const successState = screen.getByTestId('success-state');
      expect(successState).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Success!' })).toBeInTheDocument();
      expect(screen.getByText('Your account has been created.')).toBeInTheDocument();
    });
  });
});
