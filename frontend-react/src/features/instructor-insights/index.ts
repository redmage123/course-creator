/**
 * Instructor Insights Module Exports
 *
 * WHAT: Central export point for instructor insights feature
 * WHERE: Frontend React features directory
 * WHY: Provides clean imports for other modules
 *
 * @module features/instructor-insights
 */

// Main dashboard
export { InstructorInsightsDashboard } from './InstructorInsightsDashboard';
export type { InstructorInsightsDashboardProps } from './InstructorInsightsDashboard';

// Components
export { ContentEffectivenessChart } from './components/ContentEffectivenessChart';
export type { ContentEffectivenessChartProps } from './components/ContentEffectivenessChart';

export { StudentEngagementWidget } from './components/StudentEngagementWidget';
export type { StudentEngagementWidgetProps } from './components/StudentEngagementWidget';

export { CoursePerformanceWidget } from './components/CoursePerformanceWidget';
export type { CoursePerformanceWidgetProps } from './components/CoursePerformanceWidget';

export { TeachingRecommendationsWidget } from './components/TeachingRecommendationsWidget';
export type { TeachingRecommendationsWidgetProps } from './components/TeachingRecommendationsWidget';

// Hooks
export { useInstructorInsights } from './hooks/useInstructorInsights';
export type { UseInstructorInsightsResult } from './hooks/useInstructorInsights';

// Default export (main dashboard)
export { InstructorInsightsDashboard as default } from './InstructorInsightsDashboard';
