/**
 * Heading Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring Heading provides semantic and accessible
 * typography hierarchy across the platform.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests semantic HTML, visual variants, and accessibility
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Heading } from './Heading';

describe('Heading Component', () => {
  describe('Semantic Levels', () => {
    it('renders h1 by default when level="h1"', () => {
      const { container } = render(<Heading level="h1">Test Heading</Heading>);
      const heading = container.querySelector('h1');
      expect(heading).toBeInTheDocument();
      expect(heading?.textContent).toBe('Test Heading');
    });

    it('renders h2 by default when no level specified', () => {
      const { container } = render(<Heading>Test Heading</Heading>);
      const heading = container.querySelector('h2');
      expect(heading).toBeInTheDocument();
      expect(heading?.textContent).toBe('Test Heading');
    });

    it('renders h3 when level="h3"', () => {
      const { container } = render(<Heading level="h3">Test Heading</Heading>);
      const heading = container.querySelector('h3');
      expect(heading).toBeInTheDocument();
    });

    it('renders h4 when level="h4"', () => {
      const { container } = render(<Heading level="h4">Test Heading</Heading>);
      const heading = container.querySelector('h4');
      expect(heading).toBeInTheDocument();
    });

    it('renders h5 when level="h5"', () => {
      const { container } = render(<Heading level="h5">Test Heading</Heading>);
      const heading = container.querySelector('h5');
      expect(heading).toBeInTheDocument();
    });

    it('renders h6 when level="h6"', () => {
      const { container } = render(<Heading level="h6">Test Heading</Heading>);
      const heading = container.querySelector('h6');
      expect(heading).toBeInTheDocument();
    });
  });

  describe('Visual Variants', () => {
    it('applies display variant styling', () => {
      const { container } = render(
        <Heading level="h1" variant="display">
          Display Heading
        </Heading>
      );
      const heading = container.querySelector('h1');
      expect(heading?.className).toContain('heading-display');
    });

    it('applies h1 variant styling by default for h1', () => {
      const { container } = render(<Heading level="h1">H1 Heading</Heading>);
      const heading = container.querySelector('h1');
      expect(heading?.className).toContain('heading-h1');
    });

    it('applies h2 variant styling by default for h2', () => {
      const { container } = render(<Heading level="h2">H2 Heading</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-h2');
    });

    it('allows visual variant override (h2 looks like h1)', () => {
      const { container } = render(
        <Heading level="h2" variant="h1">
          Looks like H1
        </Heading>
      );
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-h1');
      expect(heading?.className).not.toContain('heading-h2');
    });

    it('allows visual variant override (h3 looks like display)', () => {
      const { container } = render(
        <Heading level="h3" variant="display">
          Looks like Display
        </Heading>
      );
      const heading = container.querySelector('h3');
      expect(heading?.className).toContain('heading-display');
    });
  });

  describe('Text Alignment', () => {
    it('applies left alignment by default', () => {
      const { container } = render(<Heading>Left Aligned</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-align-left');
    });

    it('applies center alignment', () => {
      const { container } = render(<Heading align="center">Centered</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-align-center');
    });

    it('applies right alignment', () => {
      const { container } = render(<Heading align="right">Right Aligned</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-align-right');
    });
  });

  describe('Color Variants', () => {
    it('applies default color', () => {
      const { container } = render(<Heading color="default">Default</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-color-default');
    });

    it('applies muted color', () => {
      const { container } = render(<Heading color="muted">Muted</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-color-muted');
    });

    it('applies primary color', () => {
      const { container } = render(<Heading color="primary">Primary</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-color-primary');
    });

    it('applies error color', () => {
      const { container } = render(<Heading color="error">Error</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-color-error');
    });

    it('applies success color', () => {
      const { container } = render(<Heading color="success">Success</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-color-success');
    });

    it('applies warning color', () => {
      const { container } = render(<Heading color="warning">Warning</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-color-warning');
    });
  });

  describe('Font Weight', () => {
    it('does not apply weight class when not specified', () => {
      const { container } = render(<Heading>Default Weight</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).not.toContain('heading-weight-');
    });

    it('applies normal weight', () => {
      const { container } = render(<Heading weight="normal">Normal</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-weight-normal');
    });

    it('applies medium weight', () => {
      const { container } = render(<Heading weight="medium">Medium</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-weight-medium');
    });

    it('applies semibold weight', () => {
      const { container } = render(<Heading weight="semibold">Semibold</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-weight-semibold');
    });

    it('applies bold weight', () => {
      const { container } = render(<Heading weight="bold">Bold</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-weight-bold');
    });
  });

  describe('Gutter Bottom', () => {
    it('applies gutter bottom by default', () => {
      const { container } = render(<Heading>With Gutter</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-gutter-bottom');
    });

    it('removes gutter bottom when gutterBottom=false', () => {
      const { container } = render(<Heading gutterBottom={false}>No Gutter</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).not.toContain('heading-gutter-bottom');
    });

    it('applies gutter bottom when gutterBottom=true', () => {
      const { container } = render(<Heading gutterBottom={true}>With Gutter</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('heading-gutter-bottom');
    });
  });

  describe('Custom Props', () => {
    it('accepts custom className', () => {
      const { container } = render(<Heading className="custom-heading">Custom</Heading>);
      const heading = container.querySelector('h2');
      expect(heading?.className).toContain('custom-heading');
    });

    it('passes through additional HTML attributes', () => {
      const { container } = render(
        <Heading id="test-heading" data-testid="heading">
          Test
        </Heading>
      );
      const heading = container.querySelector('h2');
      expect(heading).toHaveAttribute('id', 'test-heading');
      expect(heading).toHaveAttribute('data-testid', 'heading');
    });

    it('supports onClick handler', () => {
      const handleClick = vi.fn();
      render(<Heading onClick={handleClick}>Clickable</Heading>);
      const heading = screen.getByText('Clickable');
      heading.click();
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('supports ARIA attributes', () => {
      const { container } = render(
        <Heading aria-label="Main heading" aria-describedby="description">
          Accessible
        </Heading>
      );
      const heading = container.querySelector('h2');
      expect(heading).toHaveAttribute('aria-label', 'Main heading');
      expect(heading).toHaveAttribute('aria-describedby', 'description');
    });
  });

  describe('Children', () => {
    it('renders text children', () => {
      render(<Heading>Simple Text</Heading>);
      expect(screen.getByText('Simple Text')).toBeInTheDocument();
    });

    it('renders JSX children', () => {
      render(
        <Heading>
          <span>Complex</span> <strong>Children</strong>
        </Heading>
      );
      expect(screen.getByText('Complex')).toBeInTheDocument();
      expect(screen.getByText('Children')).toBeInTheDocument();
    });

    it('renders number children', () => {
      render(<Heading>{42}</Heading>);
      expect(screen.getByText('42')).toBeInTheDocument();
    });
  });

  describe('Display Name', () => {
    it('has Heading as display name', () => {
      expect(Heading.displayName).toBe('Heading');
    });
  });

  describe('Forward Ref', () => {
    it('forwards ref to heading element', () => {
      const ref = vi.fn();
      render(<Heading ref={ref}>Test</Heading>);
      expect(ref).toHaveBeenCalled();
    });

    it('ref can access heading properties', () => {
      const ref = { current: null as HTMLHeadingElement | null };
      render(<Heading level="h3" ref={ref}>Test</Heading>);
      expect(ref.current).toBeInstanceOf(HTMLHeadingElement);
      expect(ref.current?.tagName).toBe('H3');
    });
  });

  describe('Accessibility', () => {
    it('maintains semantic heading hierarchy', () => {
      const { container } = render(
        <>
          <Heading level="h1">Page Title</Heading>
          <Heading level="h2">Section</Heading>
          <Heading level="h3">Subsection</Heading>
        </>
      );

      expect(container.querySelector('h1')).toBeInTheDocument();
      expect(container.querySelector('h2')).toBeInTheDocument();
      expect(container.querySelector('h3')).toBeInTheDocument();
    });

    it('allows visual override without breaking semantics', () => {
      const { container } = render(
        <Heading level="h2" variant="h1">
          Visually H1, Semantically H2
        </Heading>
      );

      // Should be h2 element
      const heading = container.querySelector('h2');
      expect(heading).toBeInTheDocument();

      // But look like h1
      expect(heading?.className).toContain('heading-h1');
    });

    it('is discoverable by accessible name', () => {
      render(<Heading>Accessible Heading</Heading>);
      expect(screen.getByText('Accessible Heading')).toBeInTheDocument();
    });
  });

  describe('Regression Tests', () => {
    it('handles empty children gracefully', () => {
      const { container } = render(<Heading>{''}</Heading>);
      const heading = container.querySelector('h2');
      expect(heading).toBeInTheDocument();
      expect(heading?.textContent).toBe('');
    });

    it('combines multiple styling props correctly', () => {
      const { container } = render(
        <Heading
          level="h3"
          variant="h2"
          align="center"
          color="primary"
          weight="bold"
          gutterBottom={false}
          className="custom"
        >
          Combined
        </Heading>
      );

      const heading = container.querySelector('h3');
      expect(heading?.className).toContain('heading-h2');
      expect(heading?.className).toContain('heading-align-center');
      expect(heading?.className).toContain('heading-color-primary');
      expect(heading?.className).toContain('heading-weight-bold');
      expect(heading?.className).not.toContain('heading-gutter-bottom');
      expect(heading?.className).toContain('custom');
    });

    it('cleans up on unmount', () => {
      const { unmount } = render(<Heading>Test</Heading>);
      unmount();
      expect(true).toBe(true); // Should not throw errors
    });

    it('handles very long text', () => {
      const longText = 'A'.repeat(1000);
      render(<Heading>{longText}</Heading>);
      expect(screen.getByText(longText)).toBeInTheDocument();
    });

    it('handles special characters in text', () => {
      render(<Heading>Special {'<>& Characters'}</Heading>);
      expect(screen.getByText(/Special <>&/)).toBeInTheDocument();
    });
  });
});
