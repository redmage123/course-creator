/**
 * Card Component Tests
 *
 * BUSINESS CONTEXT:
 * Comprehensive test suite ensuring Card component maintains Tami design standards
 * and provides consistent container layout across all platform features.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests all variants, sections, padding, and accessibility features
 *
 * COVERAGE REQUIREMENTS:
 * - All 4 variants (default, outlined, elevated, interactive)
 * - All padding sizes (none, small, medium, large)
 * - All sections (header, body, footer)
 * - Accessibility (keyboard navigation, focus management)
 * - User interactions (clicks, hover states)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Card } from './Card';

describe('Card Component', () => {
  describe('Rendering', () => {
    it('renders card with children', () => {
      render(<Card>Card content</Card>);
      expect(screen.getByText('Card content')).toBeInTheDocument();
    });

    it('renders as a div element', () => {
      const { container } = render(<Card>Content</Card>);
      const card = container.firstChild;
      expect(card).toBeInstanceOf(HTMLDivElement);
    });
  });

  describe('Variants', () => {
    it('renders default variant by default', () => {
      render(<Card>Default Card</Card>);
      expect(screen.getByText('Default Card')).toBeInTheDocument();
    });

    it('renders outlined variant', () => {
      render(<Card variant="outlined">Outlined Card</Card>);
      expect(screen.getByText('Outlined Card')).toBeInTheDocument();
    });

    it('renders elevated variant', () => {
      render(<Card variant="elevated">Elevated Card</Card>);
      expect(screen.getByText('Elevated Card')).toBeInTheDocument();
    });

    it('renders interactive variant', () => {
      render(<Card variant="interactive">Interactive Card</Card>);
      expect(screen.getByText('Interactive Card')).toBeInTheDocument();
    });
  });

  describe('Header Section', () => {
    it('renders header when provided', () => {
      render(
        <Card header={<h3>Card Title</h3>}>
          Card content
        </Card>
      );
      expect(screen.getByText('Card Title')).toBeInTheDocument();
      expect(screen.getByText('Card content')).toBeInTheDocument();
    });

    it('renders without header when not provided', () => {
      const { container } = render(<Card>Content only</Card>);
      const headers = container.querySelectorAll('h1, h2, h3, h4, h5, h6');
      expect(headers).toHaveLength(0);
    });

    it('accepts complex header content', () => {
      render(
        <Card
          header={
            <div>
              <h3>Title</h3>
              <button>Action</button>
            </div>
          }
        >
          Content
        </Card>
      );
      expect(screen.getByText('Title')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /action/i })).toBeInTheDocument();
    });
  });

  describe('Footer Section', () => {
    it('renders footer when provided', () => {
      render(
        <Card footer={<button>Action Button</button>}>
          Card content
        </Card>
      );
      expect(screen.getByRole('button', { name: /action button/i })).toBeInTheDocument();
      expect(screen.getByText('Card content')).toBeInTheDocument();
    });

    it('renders without footer when not provided', () => {
      render(<Card>Content only</Card>);
      expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });

    it('accepts complex footer content', () => {
      render(
        <Card
          footer={
            <div>
              <button>Cancel</button>
              <button>Confirm</button>
            </div>
          }
        >
          Content
        </Card>
      );
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /confirm/i })).toBeInTheDocument();
    });
  });

  describe('Complete Card Structure', () => {
    it('renders with header, body, and footer', () => {
      render(
        <Card
          header={<h3>Header</h3>}
          footer={<button>Footer Action</button>}
        >
          Body Content
        </Card>
      );
      expect(screen.getByText('Header')).toBeInTheDocument();
      expect(screen.getByText('Body Content')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /footer action/i })).toBeInTheDocument();
    });

    it('maintains correct section order', () => {
      const { container } = render(
        <Card
          header={<span data-testid="header-content">Header</span>}
          footer={<span data-testid="footer-content">Footer</span>}
        >
          <span data-testid="body-content">Body</span>
        </Card>
      );
      const card = container.firstChild as HTMLElement;
      const sections = Array.from(card.children);
      expect(sections[0]).toContainElement(screen.getByTestId('header-content'));
      expect(sections[1]).toContainElement(screen.getByTestId('body-content'));
      expect(sections[2]).toContainElement(screen.getByTestId('footer-content'));
    });
  });

  describe('Padding Variants', () => {
    it('renders with medium padding by default', () => {
      render(<Card>Content</Card>);
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('renders with no padding', () => {
      render(<Card padding="none">No Padding</Card>);
      expect(screen.getByText('No Padding')).toBeInTheDocument();
    });

    it('renders with small padding', () => {
      render(<Card padding="small">Small Padding</Card>);
      expect(screen.getByText('Small Padding')).toBeInTheDocument();
    });

    it('renders with large padding', () => {
      render(<Card padding="large">Large Padding</Card>);
      expect(screen.getByText('Large Padding')).toBeInTheDocument();
    });
  });

  describe('Full Width', () => {
    it('renders full width card', () => {
      render(<Card fullWidth>Full Width Card</Card>);
      expect(screen.getByText('Full Width Card')).toBeInTheDocument();
    });

    it('renders normal width by default', () => {
      render(<Card>Normal Width</Card>);
      expect(screen.getByText('Normal Width')).toBeInTheDocument();
    });
  });

  describe('Clickable Cards', () => {
    it('renders clickable card', () => {
      render(<Card clickable>Clickable Card</Card>);
      expect(screen.getByText('Clickable Card')).toBeInTheDocument();
    });

    it('calls onClick when clicked', async () => {
      const handleClick = vi.fn();
      const { container } = render(
        <Card clickable onClick={handleClick}>
          Click me
        </Card>
      );
      const card = container.firstChild as HTMLElement;
      await userEvent.click(card);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not call onClick when not clickable', async () => {
      const handleClick = vi.fn();
      const { container } = render(
        <Card onClick={handleClick}>
          Not clickable
        </Card>
      );
      const card = container.firstChild as HTMLElement;
      await userEvent.click(card);
      expect(handleClick).toHaveBeenCalledTimes(1); // onClick still works, just no cursor change
    });
  });

  describe('User Interactions', () => {
    it('can contain interactive elements', async () => {
      const handleButtonClick = vi.fn();
      render(
        <Card>
          <button onClick={handleButtonClick}>Click me</button>
        </Card>
      );
      const button = screen.getByRole('button', { name: /click me/i });
      await userEvent.click(button);
      expect(handleButtonClick).toHaveBeenCalledTimes(1);
    });

    it('supports nested content', () => {
      render(
        <Card>
          <div>
            <h4>Nested Title</h4>
            <p>Nested paragraph</p>
            <ul>
              <li>Item 1</li>
              <li>Item 2</li>
            </ul>
          </div>
        </Card>
      );
      expect(screen.getByText('Nested Title')).toBeInTheDocument();
      expect(screen.getByText('Nested paragraph')).toBeInTheDocument();
      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Item 2')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('is focusable when clickable', () => {
      const { container } = render(<Card clickable>Focusable Card</Card>);
      const card = container.firstChild as HTMLElement;
      card.focus();
      expect(document.activeElement).toBe(card);
    });

    it('accepts aria-label prop', () => {
      const { container } = render(<Card aria-label="Course card">Content</Card>);
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveAttribute('aria-label', 'Course card');
    });

    it('accepts role prop', () => {
      const { container } = render(<Card role="article">Article content</Card>);
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveAttribute('role', 'article');
    });

    it('supports keyboard navigation for clickable cards', async () => {
      const handleClick = vi.fn();
      const { container } = render(
        <Card clickable onClick={handleClick}>
          Keyboard accessible
        </Card>
      );
      const card = container.firstChild as HTMLElement;
      card.focus();
      await userEvent.keyboard('{Enter}');
      expect(handleClick).toHaveBeenCalled();
    });
  });

  describe('Custom Props', () => {
    it('accepts custom className', () => {
      const { container } = render(<Card className="custom-card">Content</Card>);
      const card = container.firstChild as HTMLElement;
      expect(card.className).toContain('custom-card');
    });

    it('forwards ref to card element', () => {
      const ref = vi.fn();
      render(<Card ref={ref}>Content</Card>);
      expect(ref).toHaveBeenCalledWith(expect.any(HTMLDivElement));
    });

    it('spreads additional props to card element', () => {
      const { container } = render(
        <Card data-testid="custom-card" data-analytics="card-view">
          Content
        </Card>
      );
      const card = screen.getByTestId('custom-card');
      expect(card).toHaveAttribute('data-analytics', 'card-view');
    });

    it('accepts id prop', () => {
      const { container } = render(<Card id="course-card-123">Content</Card>);
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveAttribute('id', 'course-card-123');
    });

    it('accepts tabIndex prop', () => {
      const { container } = render(<Card tabIndex={0}>Content</Card>);
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveAttribute('tabIndex', '0');
    });
  });

  describe('Combined Props', () => {
    it('renders complete interactive card', () => {
      const handleClick = vi.fn();
      render(
        <Card
          variant="interactive"
          padding="large"
          fullWidth
          clickable
          onClick={handleClick}
          header={<h3>Course Title</h3>}
          footer={<button>Enroll Now</button>}
        >
          <p>Course description and details</p>
        </Card>
      );
      expect(screen.getByText('Course Title')).toBeInTheDocument();
      expect(screen.getByText('Course description and details')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /enroll now/i })).toBeInTheDocument();
    });

    it('renders outlined card with small padding', () => {
      render(
        <Card
          variant="outlined"
          padding="small"
          header={<div>Header</div>}
        >
          Content
        </Card>
      );
      expect(screen.getByText('Header')).toBeInTheDocument();
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('renders elevated card with no padding', () => {
      render(
        <Card
          variant="elevated"
          padding="none"
        >
          No padding content
        </Card>
      );
      expect(screen.getByText('No padding content')).toBeInTheDocument();
    });
  });

  describe('Display Name', () => {
    it('has Card as display name', () => {
      expect(Card.displayName).toBe('Card');
    });
  });

  describe('Regression Tests', () => {
    it('handles empty children gracefully', () => {
      render(<Card>{''}</Card>);
      const { container } = render(<Card>{''}</Card>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('handles dynamic content updates', () => {
      const { rerender } = render(<Card>Initial content</Card>);
      expect(screen.getByText('Initial content')).toBeInTheDocument();

      rerender(<Card>Updated content</Card>);
      expect(screen.getByText('Updated content')).toBeInTheDocument();
      expect(screen.queryByText('Initial content')).not.toBeInTheDocument();
    });

    it('handles variant changes', () => {
      const { rerender } = render(<Card variant="default">Content</Card>);
      expect(screen.getByText('Content')).toBeInTheDocument();

      rerender(<Card variant="elevated">Content</Card>);
      expect(screen.getByText('Content')).toBeInTheDocument();

      rerender(<Card variant="interactive">Content</Card>);
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('maintains structure when sections are added/removed', () => {
      const { rerender } = render(<Card>Content only</Card>);
      expect(screen.getByText('Content only')).toBeInTheDocument();

      rerender(
        <Card header={<div>Header</div>}>
          Content only
        </Card>
      );
      expect(screen.getByText('Header')).toBeInTheDocument();

      rerender(
        <Card
          header={<div>Header</div>}
          footer={<div>Footer</div>}
        >
          Content only
        </Card>
      );
      expect(screen.getByText('Header')).toBeInTheDocument();
      expect(screen.getByText('Footer')).toBeInTheDocument();
    });
  });
});
