/**
 * Learning Analytics Dashboard Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the Learning Analytics Dashboard provides accurate,
 * accessible, and responsive learning progress visualization for students,
 * instructors, and administrators.
 *
 * TEST COVERAGE:
 * - Component rendering with different view types (student, instructor, org_admin)
 * - Time range selector functionality
 * - Loading and error states
 * - Data visualization widgets
 * - Summary statistics cards
 * - Skills needing review section
 * - Recent milestones display
 * - Responsive behavior
 * - Accessibility features
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/utils';
import { LearningAnalyticsDashboard } from './LearningAnalyticsDashboard';
import type { LearningAnalyticsViewType } from './LearningAnalyticsDashboard';

// Mock the custom hook
vi.mock('./hooks/useLearningAnalytics');
import * as useLearningAnalyticsModule from './hooks/useLearningAnalytics';

// Mock child components
vi.mock('./components/LearningProgressChart', () => ({
  LearningProgressChart: ({ data }: any) => (
    <div data-testid="learning-progress-chart">
      Progress Chart ({data?.length || 0} data points)
    </div>
  ),
}));

vi.mock('./components/SkillMasteryWidget', () => ({
  SkillMasteryWidget: ({ skills }: any) => (
    <div data-testid="skill-mastery-widget">
      Skill Mastery ({skills?.length || 0} skills)
    </div>
  ),
}));

vi.mock('./components/LearningPathProgress', () => ({
  LearningPathProgress: ({ paths }: any) => (
    <div data-testid="learning-path-progress">
      Learning Paths ({paths?.length || 0} paths)
    </div>
  ),
}));

vi.mock('./components/SessionActivityWidget', () => ({
  SessionActivityWidget: ({ sessions }: any) => (
    <div data-testid="session-activity-widget">
      Session Activity ({sessions?.length || 0} sessions)
    </div>
  ),
}));

// Mock data
const mockSummary = {
  student_id: 'student-1',
  overall_engagement_score: 85,
  total_learning_time_minutes: 720,
  active_learning_paths: 2,
  completed_learning_paths: 1,
  total_skills_tracked: 15,
  skills_mastered: 8,
  average_mastery_score: 75,
  current_streak_days: 7,
  longest_streak_days: 14,
  sessions_this_week: 5,
  sessions_this_month: 18,
  skills_needing_review: [
    {
      id: 'skill-1',
      student_id: 'student-1',
      skill_topic: 'React Hooks',
      mastery_level: 'intermediate' as const,
      mastery_score: 70,
      current_interval_days: 3,
      assessments_completed: 5,
      assessments_passed: 4,
      total_practice_time_minutes: 120,
      practice_streak_days: 3,
      retention_estimate: 0.75,
      ease_factor: 2.5,
      repetition_count: 3,
      last_quality_rating: 4,
    },
  ],
  recent_milestones: [
    {
      milestone_id: 'milestone-1',
      name: 'Completed React Basics',
      completed_at: '2025-11-28T10:00:00Z',
      score: 92,
    },
  ],
};

const mockProgressData = [
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

const mockSkillMastery = [
  {
    id: 'skill-1',
    student_id: 'student-1',
    skill_topic: 'TypeScript',
    mastery_level: 'proficient' as const,
    mastery_score: 85,
    assessments_completed: 8,
    assessments_passed: 7,
    total_practice_time_minutes: 240,
    practice_streak_days: 5,
    retention_estimate: 0.85,
    ease_factor: 2.8,
    repetition_count: 5,
    current_interval_days: 7,
    last_quality_rating: 5,
  },
];

const mockLearningPaths = [
  {
    id: 'path-1',
    user_id: 'student-1',
    track_id: 'track-1',
    overall_progress: 75,
    milestones_completed: [],
    total_time_spent_minutes: 360,
    status: 'in_progress' as const,
  },
];

const mockSessionActivity = [
  {
    session_id: 'session-1',
    user_id: 'student-1',
    started_at: '2025-11-28T09:00:00Z',
    duration_minutes: 60,
    activities_count: 12,
    engagement_score: 85,
    content_items_viewed: 5,
    quizzes_attempted: 2,
    labs_worked_on: 1,
    pages_visited: ['/course/1', '/quiz/2'],
  },
];

describe('LearningAnalyticsDashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering - Student View', () => {
    /**
     * Test: Renders dashboard with student view type
     * WHY: Ensures correct title and subtitle for students
     */
    it('renders student view with correct title', () => {
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: mockSummary,
        learningPaths: mockLearningPaths,
        skillMastery: mockSkillMastery,
        sessionActivity: mockSessionActivity,
        progressTimeSeries: mockProgressData,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(
        <LearningAnalyticsDashboard viewType="student" />
      );

      expect(screen.getByText('My Learning Analytics')).toBeInTheDocument();
      expect(screen.getByText('Track your learning progress and skill development')).toBeInTheDocument();
    });

    /**
     * Test: Displays summary statistics cards
     * WHY: Verifies key metrics are visible to students
     */
    it('displays summary statistics cards', () => {
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: mockSummary,
        learningPaths: mockLearningPaths,
        skillMastery: mockSkillMastery,
        sessionActivity: mockSessionActivity,
        progressTimeSeries: mockProgressData,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(
        <LearningAnalyticsDashboard viewType="student" />
      );

      expect(screen.getByText('Engagement Score')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.getByText('Skills Mastered')).toBeInTheDocument();
      expect(screen.getByText('8/15')).toBeInTheDocument();
      expect(screen.getByText('Current Streak')).toBeInTheDocument();
      expect(screen.getByText('7 days')).toBeInTheDocument();
      expect(screen.getByText('Learning Time')).toBeInTheDocument();
      expect(screen.getByText('12h')).toBeInTheDocument();
    });
  });

  describe('Rendering - Instructor View', () => {
    /**
     * Test: Renders dashboard with instructor view type
     * WHY: Ensures correct title and subtitle for instructors
     */
    it('renders instructor view with correct title', () => {
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: mockSummary,
        learningPaths: mockLearningPaths,
        skillMastery: mockSkillMastery,
        sessionActivity: mockSessionActivity,
        progressTimeSeries: mockProgressData,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(
        <LearningAnalyticsDashboard viewType="instructor" studentId="student-1" />
      );

      expect(screen.getByText('Student Learning Analytics')).toBeInTheDocument();
      expect(screen.getByText('Monitor student learning outcomes and engagement')).toBeInTheDocument();
    });
  });

  describe('Rendering - Org Admin View', () => {
    /**
     * Test: Renders dashboard with org admin view type
     * WHY: Ensures correct title and subtitle for organization admins
     */
    it('renders org admin view with correct title', () => {
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: mockSummary,
        learningPaths: mockLearningPaths,
        skillMastery: mockSkillMastery,
        sessionActivity: mockSessionActivity,
        progressTimeSeries: mockProgressData,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(
        <LearningAnalyticsDashboard viewType="org_admin" />
      );

      expect(screen.getByText('Organization Learning Analytics')).toBeInTheDocument();
      expect(screen.getByText('Organizational learning insights and trends')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    /**
     * Test: Displays loading spinner while fetching data
     * WHY: Ensures users see loading feedback
     */
    it('displays loading spinner while fetching data', () => {
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: null,
        learningPaths: null,
        skillMastery: null,
        sessionActivity: null,
        progressTimeSeries: null,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(
        <LearningAnalyticsDashboard viewType="student" />
      );

      expect(screen.getByText('Loading learning analytics...')).toBeInTheDocument();
      expect(screen.getByLabelText('Loading analytics')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    /**
     * Test: Displays error message on fetch failure
     * WHY: Ensures users are informed of errors with retry option
     */
    it('displays error message and retry button on fetch failure', async () => {
      const mockRefetch = vi.fn();
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: null,
        learningPaths: null,
        skillMastery: null,
        sessionActivity: null,
        progressTimeSeries: null,
        isLoading: false,
        error: 'Failed to load analytics data',
        refetch: mockRefetch,
      });

      const user = userEvent.setup();
      renderWithProviders(
        <LearningAnalyticsDashboard viewType="student" />
      );

      expect(screen.getByText('Error Loading Learning Analytics')).toBeInTheDocument();
      expect(screen.getByText('Failed to load analytics data')).toBeInTheDocument();

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      expect(mockRefetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('Time Range Selector', () => {
    /**
     * Test: Renders all time range options
     * WHY: Ensures users can select different time periods
     */
    it('renders all time range options', () => {
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: mockSummary,
        learningPaths: mockLearningPaths,
        skillMastery: mockSkillMastery,
        sessionActivity: mockSessionActivity,
        progressTimeSeries: mockProgressData,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(
        <LearningAnalyticsDashboard viewType="student" />
      );

      expect(screen.getByRole('button', { name: 'Week' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Month' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Quarter' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '6 Months' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Year' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'All Time' })).toBeInTheDocument();
    });

    /**
     * Test: Time range button interaction
     * WHY: Verifies users can change time ranges
     */
    it('changes time range when button clicked', async () => {
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: mockSummary,
        learningPaths: mockLearningPaths,
        skillMastery: mockSkillMastery,
        sessionActivity: mockSessionActivity,
        progressTimeSeries: mockProgressData,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      const user = userEvent.setup();
      renderWithProviders(
        <LearningAnalyticsDashboard viewType="student" />
      );

      const weekButton = screen.getByRole('button', { name: 'Week' });
      await user.click(weekButton);

      expect(weekButton).toHaveAttribute('aria-pressed', 'true');
    });
  });

  describe('Analytics Widgets', () => {
    /**
     * Test: Renders all analytics widgets with data
     * WHY: Ensures all visualizations are displayed
     */
    it('renders all analytics widgets when data available', () => {
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: mockSummary,
        learningPaths: mockLearningPaths,
        skillMastery: mockSkillMastery,
        sessionActivity: mockSessionActivity,
        progressTimeSeries: mockProgressData,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(
        <LearningAnalyticsDashboard viewType="student" />
      );

      expect(screen.getByTestId('learning-progress-chart')).toBeInTheDocument();
      expect(screen.getByTestId('skill-mastery-widget')).toBeInTheDocument();
      expect(screen.getByTestId('learning-path-progress')).toBeInTheDocument();
      expect(screen.getByTestId('session-activity-widget')).toBeInTheDocument();
    });

    /**
     * Test: Hides widgets when no data available
     * WHY: Prevents rendering empty widgets
     */
    it('does not render widgets when data is null or empty', () => {
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: mockSummary,
        learningPaths: [],
        skillMastery: [],
        sessionActivity: [],
        progressTimeSeries: [],
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(
        <LearningAnalyticsDashboard viewType="student" />
      );

      expect(screen.queryByTestId('learning-progress-chart')).not.toBeInTheDocument();
      expect(screen.queryByTestId('skill-mastery-widget')).not.toBeInTheDocument();
      expect(screen.queryByTestId('learning-path-progress')).not.toBeInTheDocument();
      expect(screen.queryByTestId('session-activity-widget')).not.toBeInTheDocument();
    });
  });

  describe('Skills Needing Review Section', () => {
    /**
     * Test: Displays skills due for review
     * WHY: Ensures spaced repetition recommendations are visible
     */
    it('displays skills needing review when available', () => {
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: mockSummary,
        learningPaths: mockLearningPaths,
        skillMastery: mockSkillMastery,
        sessionActivity: mockSessionActivity,
        progressTimeSeries: mockProgressData,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(
        <LearningAnalyticsDashboard viewType="student" />
      );

      expect(screen.getByText('Skills Due for Review')).toBeInTheDocument();
      expect(screen.getByText('Based on spaced repetition schedule (SM-2 algorithm)')).toBeInTheDocument();
      expect(screen.getByText('React Hooks')).toBeInTheDocument();
      expect(screen.getByText('Intermediate')).toBeInTheDocument();
      expect(screen.getByText('Next review: 3 days')).toBeInTheDocument();
    });

    /**
     * Test: Hides review section when no skills need review
     * WHY: Prevents rendering empty section
     */
    it('does not display review section when no skills need review', () => {
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: { ...mockSummary, skills_needing_review: [] },
        learningPaths: mockLearningPaths,
        skillMastery: mockSkillMastery,
        sessionActivity: mockSessionActivity,
        progressTimeSeries: mockProgressData,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(
        <LearningAnalyticsDashboard viewType="student" />
      );

      expect(screen.queryByText('Skills Due for Review')).not.toBeInTheDocument();
    });
  });

  describe('Recent Milestones Section', () => {
    /**
     * Test: Displays recent milestones
     * WHY: Ensures achievements are visible to motivate students
     */
    it('displays recent milestones when available', () => {
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: mockSummary,
        learningPaths: mockLearningPaths,
        skillMastery: mockSkillMastery,
        sessionActivity: mockSessionActivity,
        progressTimeSeries: mockProgressData,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(
        <LearningAnalyticsDashboard viewType="student" />
      );

      expect(screen.getByText('Recent Milestones')).toBeInTheDocument();
      expect(screen.getByText('Completed React Basics')).toBeInTheDocument();
      expect(screen.getByText('Score: 92%')).toBeInTheDocument();
    });

    /**
     * Test: Hides milestones section when none available
     * WHY: Prevents rendering empty section
     */
    it('does not display milestones section when none available', () => {
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: { ...mockSummary, recent_milestones: [] },
        learningPaths: mockLearningPaths,
        skillMastery: mockSkillMastery,
        sessionActivity: mockSessionActivity,
        progressTimeSeries: mockProgressData,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(
        <LearningAnalyticsDashboard viewType="student" />
      );

      expect(screen.queryByText('Recent Milestones')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    /**
     * Test: Time range buttons have proper ARIA attributes
     * WHY: Ensures accessibility for screen readers
     */
    it('time range buttons have proper aria-pressed attributes', () => {
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: mockSummary,
        learningPaths: mockLearningPaths,
        skillMastery: mockSkillMastery,
        sessionActivity: mockSessionActivity,
        progressTimeSeries: mockProgressData,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(
        <LearningAnalyticsDashboard viewType="student" />
      );

      const monthButton = screen.getByRole('button', { name: 'Month' });
      expect(monthButton).toHaveAttribute('aria-pressed', 'true');

      const weekButton = screen.getByRole('button', { name: 'Week' });
      expect(weekButton).toHaveAttribute('aria-pressed', 'false');
    });

    /**
     * Test: Loading spinner has aria-label
     * WHY: Ensures screen readers announce loading state
     */
    it('loading spinner has aria-label for screen readers', () => {
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: null,
        learningPaths: null,
        skillMastery: null,
        sessionActivity: null,
        progressTimeSeries: null,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(
        <LearningAnalyticsDashboard viewType="student" />
      );

      const spinner = screen.getByLabelText('Loading analytics');
      expect(spinner).toBeInTheDocument();
    });
  });

  describe('Responsive Behavior', () => {
    /**
     * Test: Dashboard renders with proper grid layout
     * WHY: Ensures responsive design structure is present
     */
    it('renders with grid layout classes', () => {
      vi.spyOn(useLearningAnalyticsModule, 'useLearningAnalytics').mockReturnValue({
        summary: mockSummary,
        learningPaths: mockLearningPaths,
        skillMastery: mockSkillMastery,
        sessionActivity: mockSessionActivity,
        progressTimeSeries: mockProgressData,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      const { container } = renderWithProviders(
        <LearningAnalyticsDashboard viewType="student" />
      );

      const summaryGrid = container.querySelector('[class*="summaryGrid"]');
      const widgetsGrid = container.querySelector('[class*="widgetsGrid"]');

      expect(summaryGrid).toBeInTheDocument();
      expect(widgetsGrid).toBeInTheDocument();
    });
  });
});
