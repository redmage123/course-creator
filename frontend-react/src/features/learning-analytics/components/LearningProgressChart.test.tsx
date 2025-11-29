/**
 * Learning Progress Chart Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the Learning Progress Chart provides accurate
 * time-series visualization of learning progress, engagement, and time spent.
 *
 * TEST COVERAGE:
 * - Component rendering with data
 * - Empty state handling
 * - Data transformation for chart
 * - Summary statistics calculations
 * - Chart configuration
 * - Accessibility features
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '../../../test/utils';
import { LearningProgressChart } from './LearningProgressChart';
import type { LearningProgressDataPoint } from '../../../services/learningAnalyticsService';

// Mock Chart.js components
vi.mock('react-chartjs-2', () => ({
  Line: ({ data, options }: any) => (
    <div data-testid="line-chart">
      <div data-testid="chart-labels">{JSON.stringify(data.labels)}</div>
      <div data-testid="chart-datasets">{data.datasets.length} datasets</div>
    </div>
  ),
}));

describe('LearningProgressChart Component', () => {
  const mockData: LearningProgressDataPoint[] = [
    {
      date: '2025-11-21',
      progress_percentage: 60,
      items_completed: 10,
      time_spent_minutes: 120,
      engagement_score: 75,
    },
    {
      date: '2025-11-28',
      progress_percentage: 85,
      items_completed: 15,
      time_spent_minutes: 180,
      engagement_score: 85,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering with Data', () => {
    /**
     * Test: Renders chart when data provided
     * WHY: Ensures chart displays with valid data
     */
    it('renders chart when data is provided', () => {
      renderWithProviders(<LearningProgressChart data={mockData} />);
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });

    /**
     * Test: Displays summary statistics
     * WHY: Ensures calculated metrics are visible
     */
    it('displays summary statistics below chart', () => {
      renderWithProviders(<LearningProgressChart data={mockData} />);

      expect(screen.getByText('Total Items')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument(); // Last item count

      expect(screen.getByText('Total Time')).toBeInTheDocument();
      expect(screen.getByText('5h')).toBeInTheDocument(); // (120 + 180) / 60

      expect(screen.getByText('Avg Engagement')).toBeInTheDocument();
      expect(screen.getByText('80%')).toBeInTheDocument(); // (75 + 85) / 2
    });

    /**
     * Test: Formats chart labels correctly
     * WHY: Ensures date labels are human-readable
     */
    it('formats dates correctly for chart labels', () => {
      renderWithProviders(<LearningProgressChart data={mockData} />);

      const labelsElement = screen.getByTestId('chart-labels');
      const labels = JSON.parse(labelsElement.textContent || '[]');

      expect(labels).toEqual(['11/21', '11/28']);
    });

    /**
     * Test: Creates multiple datasets
     * WHY: Ensures progress and engagement are both plotted
     */
    it('creates datasets for progress and engagement', () => {
      renderWithProviders(<LearningProgressChart data={mockData} />);

      expect(screen.getByText('2 datasets')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    /**
     * Test: Shows empty state when no data
     * WHY: Prevents rendering errors with empty data
     */
    it('displays empty state when data array is empty', () => {
      renderWithProviders(<LearningProgressChart data={[]} />);

      expect(screen.getByText('No progress data available')).toBeInTheDocument();
      expect(screen.queryByTestId('line-chart')).not.toBeInTheDocument();
    });

    /**
     * Test: Shows empty state when data is null
     * WHY: Handles null data gracefully
     */
    it('displays empty state when data is null', () => {
      renderWithProviders(<LearningProgressChart data={null as any} />);

      expect(screen.getByText('No progress data available')).toBeInTheDocument();
    });
  });

  describe('Data Calculations', () => {
    /**
     * Test: Calculates total time correctly
     * WHY: Ensures accurate time aggregation
     */
    it('calculates total time spent correctly', () => {
      const data: LearningProgressDataPoint[] = [
        { date: '2025-11-21', progress_percentage: 50, items_completed: 5, time_spent_minutes: 90, engagement_score: 70 },
        { date: '2025-11-28', progress_percentage: 75, items_completed: 10, time_spent_minutes: 150, engagement_score: 80 },
      ];

      renderWithProviders(<LearningProgressChart data={data} />);

      // (90 + 150) / 60 = 4 hours
      expect(screen.getByText('4h')).toBeInTheDocument();
    });

    /**
     * Test: Calculates average engagement correctly
     * WHY: Ensures accurate engagement metric
     */
    it('calculates average engagement score correctly', () => {
      const data: LearningProgressDataPoint[] = [
        { date: '2025-11-21', progress_percentage: 50, items_completed: 5, time_spent_minutes: 90, engagement_score: 60 },
        { date: '2025-11-28', progress_percentage: 75, items_completed: 10, time_spent_minutes: 150, engagement_score: 80 },
      ];

      renderWithProviders(<LearningProgressChart data={data} />);

      // (60 + 80) / 2 = 70
      expect(screen.getByText('70%')).toBeInTheDocument();
    });

    /**
     * Test: Shows last item count as total
     * WHY: Ensures cumulative count is displayed
     */
    it('displays last items_completed as total', () => {
      renderWithProviders(<LearningProgressChart data={mockData} />);

      // Last value is 15
      expect(screen.getByText('15')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    /**
     * Test: Handles single data point
     * WHY: Ensures chart works with minimal data
     */
    it('renders with single data point', () => {
      const singlePoint: LearningProgressDataPoint[] = [
        { date: '2025-11-28', progress_percentage: 50, items_completed: 5, time_spent_minutes: 60, engagement_score: 75 },
      ];

      renderWithProviders(<LearningProgressChart data={singlePoint} />);

      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument(); // Total items
      expect(screen.getByText('1h')).toBeInTheDocument(); // Total time
      expect(screen.getByText('75%')).toBeInTheDocument(); // Avg engagement
    });

    /**
     * Test: Handles zero values
     * WHY: Ensures graceful handling of edge cases
     */
    it('handles zero values correctly', () => {
      const zeroData: LearningProgressDataPoint[] = [
        { date: '2025-11-28', progress_percentage: 0, items_completed: 0, time_spent_minutes: 0, engagement_score: 0 },
      ];

      renderWithProviders(<LearningProgressChart data={zeroData} />);

      expect(screen.getByText('0')).toBeInTheDocument();
      expect(screen.getByText('0h')).toBeInTheDocument();
      expect(screen.getByText('0%')).toBeInTheDocument();
    });
  });
});
