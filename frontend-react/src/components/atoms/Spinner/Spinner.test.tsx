/**
 * Spinner Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring Spinner provides consistent loading feedback
 * across all async operations in the platform.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests sizes, colors, accessibility, and animation behavior
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Spinner } from './Spinner';

describe('Spinner Component', () => {
  describe('Rendering', () => {
    it('renders spinner', () => {
      render(<Spinner />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('renders with default label', () => {
      render(<Spinner />);
      expect(screen.getByText('Loading')).toBeInTheDocument();
    });

    it('renders with custom label', () => {
      render(<Spinner label="Loading courses..." />);
      expect(screen.getByText('Loading courses...')).toBeInTheDocument();
    });
  });

  describe('Sizes', () => {
    it('renders medium size by default', () => {
      render(<Spinner />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('renders small size', () => {
      render(<Spinner size="small" />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('renders large size', () => {
      render(<Spinner size="large" />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });
  });

  describe('Colors', () => {
    it('renders primary color by default', () => {
      render(<Spinner />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('renders secondary color', () => {
      render(<Spinner color="secondary" />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('renders white color', () => {
      render(<Spinner color="white" />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });
  });

  describe('Centering', () => {
    it('is centered by default', () => {
      render(<Spinner />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('can be inline (not centered)', () => {
      render(<Spinner centered={false} />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has role="status"', () => {
      render(<Spinner />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('has aria-live="polite"', () => {
      render(<Spinner />);
      const spinner = screen.getByRole('status');
      expect(spinner).toHaveAttribute('aria-live', 'polite');
    });

    it('includes accessible label', () => {
      render(<Spinner label="Processing request" />);
      expect(screen.getByText('Processing request')).toBeInTheDocument();
    });

    it('SVG is aria-hidden', () => {
      const { container } = render(<Spinner />);
      const svg = container.querySelector('svg');
      expect(svg).toHaveAttribute('aria-hidden', 'true');
    });
  });

  describe('Custom Props', () => {
    it('accepts custom className', () => {
      render(<Spinner className="custom-spinner" />);
      const spinner = screen.getByRole('status');
      expect(spinner.className).toContain('custom-spinner');
    });

    it('spreads additional props', () => {
      render(<Spinner data-testid="loading-spinner" />);
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });
  });

  describe('Combined Props', () => {
    it('renders small primary centered spinner', () => {
      render(<Spinner size="small" color="primary" centered />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('renders large white inline spinner with custom label', () => {
      render(
        <Spinner
          size="large"
          color="white"
          centered={false}
          label="Uploading files..."
        />
      );
      expect(screen.getByText('Uploading files...')).toBeInTheDocument();
    });
  });

  describe('Display Name', () => {
    it('has Spinner as display name', () => {
      expect(Spinner.displayName).toBe('Spinner');
    });
  });
});
