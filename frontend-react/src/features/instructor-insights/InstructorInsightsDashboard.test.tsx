/**
 * Instructor Insights Dashboard Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the Instructor Insights Dashboard provides accurate
 * and actionable analytics for instructors to improve teaching effectiveness.
 *
 * TEST COVERAGE:
 * - Component rendering with different states
 * - Time range selector functionality
 * - Loading and error states
 * - Summary cards display
 * - Widget rendering
 * - Refresh functionality
 * - Accessibility features
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/utils';
import { InstructorInsightsDashboard } from './InstructorInsightsDashboard';

// Mock the custom hook
vi.mock('./hooks/useInstructorInsights');
import * as useInstructorInsightsModule from './hooks/useInstructorInsights';

// Mock child components
vi.mock('./components/ContentEffectivenessChart', () => ({
  ContentEffectivenessChart: ({ contentEffectiveness, timeRange }: any) => (
    <div data-testid="content-effectiveness-chart">
      Content Effectiveness ({contentEffectiveness?.length || 0} items, {timeRange})
    </div>
  ),
}));

vi.mock('./components/StudentEngagementWidget', () => ({
  StudentEngagementWidget: ({ engagement }: any) => (
    <div data-testid="student-engagement-widget">
      Student Engagement ({engagement ? 'loaded' : 'empty'})
    </div>
  ),
}));

vi.mock('./components/CoursePerformanceWidget', () => ({
  CoursePerformanceWidget: ({ coursePerformances, peerComparisons }: any) => (
    <div data-testid="course-performance-widget">
      Course Performance ({coursePerformances?.length || 0} courses)
    </div>
  ),
}));

vi.mock('./components/TeachingRecommendationsWidget', () => ({
  TeachingRecommendationsWidget: ({ recommendations }: any) => (
    <div data-testid="teaching-recommendations-widget">
      Recommendations ({recommendations?.length || 0} items)
    </div>
  ),
}));

// Mock data
const mockEffectiveness = {
  instructor_id: 'instructor-1',
  overall_rating: 4.5,
  rating_trend: 'improving' as const,
  total_students_taught: 250,
  course_completion_rate: 85.5,
  engagement_score: 78,
  engagement_trend: 'stable' as const,
  average_quiz_score: 82,
  average_lab_completion_rate: 75,
  content_quality_score: 88,
  response_time_hours: 4.2,
  period_start: '2025-11-01',
  period_end: '2025-11-30',
};

const mockCoursePerformances = [
  {
    course_id: 'course-1',
    course_name: 'Introduction to Python',
    enrollment_count: 50,
    completion_rate: 88,
    average_quiz_score: 85,
    student_satisfaction: 4.6,
    engagement_score: 82,
    content_effectiveness_score: 90,
  },
];

const mockEngagement = {
  instructor_id: 'instructor-1',
  total_forum_posts: 45,
  total_responses: 120,
  average_response_time_hours: 3.5,
  office_hours_held: 12,
  office_hours_attended: 8,
  one_on_ones_scheduled: 15,
  announcements_sent: 8,
  resources_shared: 25,
};

const mockRecommendations = [
  {
    id: 'rec-1',
    instructor_id: 'instructor-1',
    recommendation_type: 'engagement' as const,
    title: 'Increase Forum Participation',
    description: 'Consider posting more frequently in course forums',
    priority: 'medium' as const,
    status: 'pending' as const,
    created_at: '2025-11-20T10:00:00Z',
  },
];

const mockPeerComparisons = [
  {
    metric: 'completion_rate',
    instructor_value: 85,
    peer_average: 78,
    peer_median: 80,
    percentile: 75,
  },
];

const mockContentEffectiveness = [
  {
    content_id: 'content-1',
    content_type: 'video' as const,
    content_title: 'Python Basics',
    views: 500,
    completion_rate: 92,
    average_watch_time_minutes: 15,
    engagement_score: 88,
    quiz_performance_impact: 5.2,
    feedback_sentiment: 'positive' as const,
  },
];

describe('InstructorInsightsDashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering - Default State', () => {
    /**
     * Test: Renders dashboard with correct title and subtitle
     * WHY: Ensures instructors see the proper heading
     */
    it('renders dashboard with correct title', () => {
      vi.spyOn(useInstructorInsightsModule, 'useInstructorInsights').mockReturnValue({
        effectiveness: mockEffectiveness,
        coursePerformances: mockCoursePerformances,
        engagement: mockEngagement,
        recommendations: mockRecommendations,
        peerComparisons: mockPeerComparisons,
        contentEffectiveness: mockContentEffectiveness,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        acknowledgeRecommendation: vi.fn(),
        startRecommendation: vi.fn(),
        completeRecommendation: vi.fn(),
        dismissRecommendation: vi.fn(),
      });

      renderWithProviders(<InstructorInsightsDashboard />);

      expect(screen.getByText('Instructor Insights')).toBeInTheDocument();
      expect(
        screen.getByText('Track your teaching effectiveness and receive personalized improvement recommendations')
      ).toBeInTheDocument();
    });

    /**
     * Test: Displays effectiveness summary cards
     * WHY: Verifies key metrics are visible to instructors
     */
    it('displays effectiveness summary cards', () => {
      vi.spyOn(useInstructorInsightsModule, 'useInstructorInsights').mockReturnValue({
        effectiveness: mockEffectiveness,
        coursePerformances: mockCoursePerformances,
        engagement: mockEngagement,
        recommendations: mockRecommendations,
        peerComparisons: mockPeerComparisons,
        contentEffectiveness: mockContentEffectiveness,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        acknowledgeRecommendation: vi.fn(),
        startRecommendation: vi.fn(),
        completeRecommendation: vi.fn(),
        dismissRecommendation: vi.fn(),
      });

      renderWithProviders(<InstructorInsightsDashboard />);

      expect(screen.getByText('Overall Rating')).toBeInTheDocument();
      expect(screen.getByText('4.5')).toBeInTheDocument();
      expect(screen.getByText('Students Taught')).toBeInTheDocument();
      expect(screen.getByText('250')).toBeInTheDocument();
      expect(screen.getByText('Completion Rate')).toBeInTheDocument();
      expect(screen.getByText('85.5')).toBeInTheDocument();
      expect(screen.getByText('Engagement Score')).toBeInTheDocument();
      expect(screen.getByText('78')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    /**
     * Test: Displays loading state while fetching data
     * WHY: Ensures instructors see loading feedback
     */
    it('displays loading state while fetching data', () => {
      vi.spyOn(useInstructorInsightsModule, 'useInstructorInsights').mockReturnValue({
        effectiveness: null,
        coursePerformances: null,
        engagement: null,
        recommendations: null,
        peerComparisons: null,
        contentEffectiveness: null,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
        acknowledgeRecommendation: vi.fn(),
        startRecommendation: vi.fn(),
        completeRecommendation: vi.fn(),
        dismissRecommendation: vi.fn(),
      });

      renderWithProviders(<InstructorInsightsDashboard />);

      expect(screen.getByText('Loading instructor insights...')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    /**
     * Test: Displays error message and retry button on fetch failure
     * WHY: Ensures instructors can recover from errors
     */
    it('displays error message and retry button on fetch failure', async () => {
      const mockRefetch = vi.fn();
      vi.spyOn(useInstructorInsightsModule, 'useInstructorInsights').mockReturnValue({
        effectiveness: null,
        coursePerformances: null,
        engagement: null,
        recommendations: null,
        peerComparisons: null,
        contentEffectiveness: null,
        isLoading: false,
        error: 'Failed to load instructor insights',
        refetch: mockRefetch,
        acknowledgeRecommendation: vi.fn(),
        startRecommendation: vi.fn(),
        completeRecommendation: vi.fn(),
        dismissRecommendation: vi.fn(),
      });

      const user = userEvent.setup();
      renderWithProviders(<InstructorInsightsDashboard />);

      expect(screen.getByText('Error Loading Insights')).toBeInTheDocument();
      expect(screen.getByText('Failed to load instructor insights')).toBeInTheDocument();

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      expect(mockRefetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('Time Range Selector', () => {
    /**
     * Test: Renders time range selector with all options
     * WHY: Ensures instructors can filter by time period
     */
    it('renders time range selector with all options', () => {
      vi.spyOn(useInstructorInsightsModule, 'useInstructorInsights').mockReturnValue({
        effectiveness: mockEffectiveness,
        coursePerformances: mockCoursePerformances,
        engagement: mockEngagement,
        recommendations: mockRecommendations,
        peerComparisons: mockPeerComparisons,
        contentEffectiveness: mockContentEffectiveness,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        acknowledgeRecommendation: vi.fn(),
        startRecommendation: vi.fn(),
        completeRecommendation: vi.fn(),
        dismissRecommendation: vi.fn(),
      });

      renderWithProviders(<InstructorInsightsDashboard />);

      const select = screen.getByLabelText('Time Range:');
      expect(select).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Last 7 Days' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Last 30 Days' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Last 90 Days' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Last Year' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'All Time' })).toBeInTheDocument();
    });

    /**
     * Test: Changes time range when selection changes
     * WHY: Verifies time range updates work correctly
     */
    it('changes time range when selection changes', async () => {
      vi.spyOn(useInstructorInsightsModule, 'useInstructorInsights').mockReturnValue({
        effectiveness: mockEffectiveness,
        coursePerformances: mockCoursePerformances,
        engagement: mockEngagement,
        recommendations: mockRecommendations,
        peerComparisons: mockPeerComparisons,
        contentEffectiveness: mockContentEffectiveness,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        acknowledgeRecommendation: vi.fn(),
        startRecommendation: vi.fn(),
        completeRecommendation: vi.fn(),
        dismissRecommendation: vi.fn(),
      });

      const user = userEvent.setup();
      renderWithProviders(<InstructorInsightsDashboard />);

      const select = screen.getByLabelText('Time Range:');
      await user.selectOptions(select, '7d');

      expect((screen.getByRole('option', { name: 'Last 7 Days' }) as HTMLOptionElement).selected).toBe(true);
    });
  });

  describe('Refresh Functionality', () => {
    /**
     * Test: Refresh button calls refetch function
     * WHY: Ensures instructors can manually refresh data
     */
    it('refresh button calls refetch function', async () => {
      const mockRefetch = vi.fn();
      vi.spyOn(useInstructorInsightsModule, 'useInstructorInsights').mockReturnValue({
        effectiveness: mockEffectiveness,
        coursePerformances: mockCoursePerformances,
        engagement: mockEngagement,
        recommendations: mockRecommendations,
        peerComparisons: mockPeerComparisons,
        contentEffectiveness: mockContentEffectiveness,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
        acknowledgeRecommendation: vi.fn(),
        startRecommendation: vi.fn(),
        completeRecommendation: vi.fn(),
        dismissRecommendation: vi.fn(),
      });

      const user = userEvent.setup();
      renderWithProviders(<InstructorInsightsDashboard />);

      const refreshButton = screen.getByTitle('Refresh data');
      await user.click(refreshButton);

      expect(mockRefetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('Widgets Rendering', () => {
    /**
     * Test: Renders all widgets when data is available
     * WHY: Ensures all analytics widgets are displayed
     */
    it('renders all widgets when data is available', () => {
      vi.spyOn(useInstructorInsightsModule, 'useInstructorInsights').mockReturnValue({
        effectiveness: mockEffectiveness,
        coursePerformances: mockCoursePerformances,
        engagement: mockEngagement,
        recommendations: mockRecommendations,
        peerComparisons: mockPeerComparisons,
        contentEffectiveness: mockContentEffectiveness,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        acknowledgeRecommendation: vi.fn(),
        startRecommendation: vi.fn(),
        completeRecommendation: vi.fn(),
        dismissRecommendation: vi.fn(),
      });

      renderWithProviders(<InstructorInsightsDashboard />);

      expect(screen.getByTestId('content-effectiveness-chart')).toBeInTheDocument();
      expect(screen.getByTestId('student-engagement-widget')).toBeInTheDocument();
      expect(screen.getByTestId('course-performance-widget')).toBeInTheDocument();
      expect(screen.getByTestId('teaching-recommendations-widget')).toBeInTheDocument();
    });
  });

  describe('Trend Indicators', () => {
    /**
     * Test: Displays trend indicators for ratings
     * WHY: Helps instructors understand performance direction
     */
    it('displays improving trend indicator', () => {
      vi.spyOn(useInstructorInsightsModule, 'useInstructorInsights').mockReturnValue({
        effectiveness: mockEffectiveness,
        coursePerformances: mockCoursePerformances,
        engagement: mockEngagement,
        recommendations: mockRecommendations,
        peerComparisons: mockPeerComparisons,
        contentEffectiveness: mockContentEffectiveness,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        acknowledgeRecommendation: vi.fn(),
        startRecommendation: vi.fn(),
        completeRecommendation: vi.fn(),
        dismissRecommendation: vi.fn(),
      });

      renderWithProviders(<InstructorInsightsDashboard />);

      expect(screen.getByText(/improving/i)).toBeInTheDocument();
      expect(screen.getByText(/stable/i)).toBeInTheDocument();
    });
  });

  describe('Props Handling', () => {
    /**
     * Test: Passes instructorId and courseId to hook
     * WHY: Ensures filtering works correctly
     */
    it('passes instructorId and courseId props correctly', () => {
      const hookSpy = vi.spyOn(useInstructorInsightsModule, 'useInstructorInsights').mockReturnValue({
        effectiveness: mockEffectiveness,
        coursePerformances: mockCoursePerformances,
        engagement: mockEngagement,
        recommendations: mockRecommendations,
        peerComparisons: mockPeerComparisons,
        contentEffectiveness: mockContentEffectiveness,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        acknowledgeRecommendation: vi.fn(),
        startRecommendation: vi.fn(),
        completeRecommendation: vi.fn(),
        dismissRecommendation: vi.fn(),
      });

      renderWithProviders(
        <InstructorInsightsDashboard instructorId="instructor-123" courseId="course-456" />
      );

      expect(hookSpy).toHaveBeenCalledWith('instructor-123', 'course-456', '30d');
    });
  });
});
