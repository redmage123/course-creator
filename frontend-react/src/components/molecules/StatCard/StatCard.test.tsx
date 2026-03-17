/**
 * StatCard Component Tests
 *
 * BUSINESS CONTEXT:
 * Comprehensive test suite ensuring StatCard displays metrics correctly
 * with proper trend indicators and accessibility support.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests rendering, formatting, trends, and accessibility
 *
 * COVERAGE REQUIREMENTS:
 * - Basic rendering with value and label
 * - Different value formats (number, percentage, currency, duration)
 * - Trend indicators (up, down, neutral)
 * - Icon display
 * - Accessibility attributes
 * - Responsive behavior
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatCard } from './StatCard';

describe('StatCard Component', () => {
  describe('Basic Rendering', () => {
    it('renders value and label', () => {
      render(<StatCard value={42} label="Active Courses" />);

      expect(screen.getByText('42')).toBeInTheDocument();
      expect(screen.getByText('Active Courses')).toBeInTheDocument();
    });

    it('renders with test id', () => {
      render(<StatCard value={100} label="Test Stat" />);

      expect(screen.getByTestId('stat-card')).toBeInTheDocument();
    });

    it('renders string values directly', () => {
      render(<StatCard value="N/A" label="Pending Data" />);

      expect(screen.getByText('N/A')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      render(<StatCard value={0} label="Test" className="custom-stat" />);

      const card = screen.getByTestId('stat-card');
      expect(card.className).toContain('custom-stat');
    });
  });

  describe('Value Formatting', () => {
    it('formats number with locale separators', () => {
      render(<StatCard value={1234567} label="Total Users" valueFormat="number" />);

      // Locale formatting adds commas
      expect(screen.getByText('1,234,567')).toBeInTheDocument();
    });

    it('formats percentage values', () => {
      render(<StatCard value={85} label="Completion Rate" valueFormat="percentage" />);

      expect(screen.getByText('85%')).toBeInTheDocument();
    });

    it('formats currency values with default symbol', () => {
      render(<StatCard value={1500} label="Revenue" valueFormat="currency" />);

      expect(screen.getByText('$1,500')).toBeInTheDocument();
    });

    it('formats currency values with custom symbol', () => {
      render(
        <StatCard
          value={2000}
          label="Revenue"
          valueFormat="currency"
          currencySymbol="€"
        />
      );

      expect(screen.getByText('€2,000')).toBeInTheDocument();
    });

    it('formats duration in hours and minutes', () => {
      render(<StatCard value={135} label="Time Spent" valueFormat="duration" />);

      expect(screen.getByText('2h 15m')).toBeInTheDocument();
    });

    it('formats duration with only minutes', () => {
      render(<StatCard value={45} label="Time Spent" valueFormat="duration" />);

      expect(screen.getByText('45m')).toBeInTheDocument();
    });
  });

  describe('Trend Indicators', () => {
    it('shows positive trend indicator', () => {
      render(<StatCard value={50} label="Test" trend={12.5} />);

      expect(screen.getByText('+12.5%')).toBeInTheDocument();
    });

    it('shows negative trend indicator', () => {
      render(<StatCard value={50} label="Test" trend={-8.3} />);

      expect(screen.getByText('-8.3%')).toBeInTheDocument();
    });

    it('shows neutral trend indicator', () => {
      render(<StatCard value={50} label="Test" trend={0} />);

      expect(screen.getByText('0.0%')).toBeInTheDocument();
    });

    it('shows custom trend label', () => {
      render(
        <StatCard
          value={50}
          label="Test"
          trend={5}
          trendLabel="vs last week"
        />
      );

      expect(screen.getByText('vs last week')).toBeInTheDocument();
    });

    it('uses default trend label', () => {
      render(<StatCard value={50} label="Test" trend={5} />);

      expect(screen.getByText('vs last period')).toBeInTheDocument();
    });

    it('does not show trend when not provided', () => {
      render(<StatCard value={50} label="Test" />);

      expect(screen.queryByText('vs last period')).not.toBeInTheDocument();
    });

    it('applies correct CSS class for positive trend', () => {
      const { container } = render(<StatCard value={50} label="Test" trend={10} />);

      const trendElement = container.querySelector('[class*="trend-up"]');
      expect(trendElement).toBeInTheDocument();
    });

    it('applies correct CSS class for negative trend', () => {
      const { container } = render(<StatCard value={50} label="Test" trend={-10} />);

      const trendElement = container.querySelector('[class*="trend-down"]');
      expect(trendElement).toBeInTheDocument();
    });

    it('applies correct CSS class for neutral trend', () => {
      const { container } = render(<StatCard value={50} label="Test" trend={0} />);

      const trendElement = container.querySelector('[class*="trend-neutral"]');
      expect(trendElement).toBeInTheDocument();
    });

    it('allows override of trend direction', () => {
      const { container } = render(
        <StatCard
          value={50}
          label="Test"
          trend={-5}
          trendDirection="up"  // Override: negative value but show as up
        />
      );

      const trendElement = container.querySelector('[class*="trend-up"]');
      expect(trendElement).toBeInTheDocument();
    });
  });

  describe('Icon Display', () => {
    it('renders icon when provided', () => {
      const testIcon = <span data-testid="test-icon">📊</span>;
      render(<StatCard value={42} label="Test" icon={testIcon} />);

      expect(screen.getByTestId('test-icon')).toBeInTheDocument();
    });

    it('does not render icon container when not provided', () => {
      const { container } = render(<StatCard value={42} label="Test" />);

      const iconContainer = container.querySelector('[class*="stat-icon"]');
      expect(iconContainer).not.toBeInTheDocument();
    });
  });

  describe('Card Variants', () => {
    it('uses elevated variant by default', () => {
      render(<StatCard value={42} label="Test" />);

      // Card component handles variant styling
      const card = screen.getByTestId('stat-card');
      expect(card).toBeInTheDocument();
    });

    it('accepts outlined variant', () => {
      render(<StatCard value={42} label="Test" variant="outlined" />);

      const card = screen.getByTestId('stat-card');
      expect(card).toBeInTheDocument();
    });

    it('accepts filled variant', () => {
      render(<StatCard value={42} label="Test" variant="filled" />);

      const card = screen.getByTestId('stat-card');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has accessible group role', () => {
      render(<StatCard value={42} label="Active Courses" />);

      expect(screen.getByRole('group')).toBeInTheDocument();
    });

    it('generates accessible description without trend', () => {
      render(<StatCard value={42} label="Active Courses" />);

      const group = screen.getByRole('group');
      expect(group).toHaveAttribute('aria-label', 'Active Courses: 42');
    });

    it('generates accessible description with positive trend', () => {
      render(
        <StatCard
          value={42}
          label="Active Courses"
          trend={12.5}
          trendLabel="vs last month"
        />
      );

      const group = screen.getByRole('group');
      expect(group).toHaveAttribute(
        'aria-label',
        'Active Courses: 42, up 12.5% vs last month'
      );
    });

    it('generates accessible description with negative trend', () => {
      render(
        <StatCard
          value={42}
          label="Active Courses"
          trend={-5.2}
          trendLabel="vs last week"
        />
      );

      const group = screen.getByRole('group');
      expect(group).toHaveAttribute(
        'aria-label',
        'Active Courses: 42, down 5.2% vs last week'
      );
    });

    it('generates accessible description with neutral trend', () => {
      render(<StatCard value={42} label="Active Courses" trend={0} />);

      const group = screen.getByRole('group');
      expect(group).toHaveAttribute(
        'aria-label',
        'Active Courses: 42, unchanged vs last period'
      );
    });

    it('uses custom aria description when provided', () => {
      render(
        <StatCard
          value={42}
          label="Active Courses"
          ariaDescription="You have 42 courses currently active"
        />
      );

      const group = screen.getByRole('group');
      expect(group).toHaveAttribute(
        'aria-label',
        'You have 42 courses currently active'
      );
    });

    it('trend indicator has aria-label', () => {
      render(<StatCard value={42} label="Test" trend={10} trendLabel="vs last week" />);

      // The trend indicator should have accessible label
      const trendIndicator = screen.getByLabelText(/Trend: 10% up vs last week/i);
      expect(trendIndicator).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles zero value', () => {
      render(<StatCard value={0} label="Empty Stat" />);

      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('handles large numbers', () => {
      render(<StatCard value={9999999} label="Big Number" />);

      expect(screen.getByText('9,999,999')).toBeInTheDocument();
    });

    it('handles very small trend percentages', () => {
      render(<StatCard value={100} label="Test" trend={0.1} />);

      expect(screen.getByText('+0.1%')).toBeInTheDocument();
    });

    it('handles very large trend percentages', () => {
      render(<StatCard value={100} label="Test" trend={500} />);

      expect(screen.getByText('+500.0%')).toBeInTheDocument();
    });

    it('handles negative zero trend', () => {
      render(<StatCard value={100} label="Test" trend={-0} />);

      // -0 should be treated as neutral
      expect(screen.getByText('0.0%')).toBeInTheDocument();
    });
  });

  describe('Display Name', () => {
    it('has StatCard as display name', () => {
      expect(StatCard.displayName).toBe('StatCard');
    });
  });
});
