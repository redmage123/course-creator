/**
 * Learning Analytics Feature Module Exports
 *
 * WHAT: Centralized exports for learning analytics feature
 * WHERE: Main entry point for learning analytics module
 * WHY: Provides clean import interface for consuming components
 *
 * @module features/learning-analytics
 */

// Main dashboard component
export { LearningAnalyticsDashboard } from './LearningAnalyticsDashboard';
export type { LearningAnalyticsDashboardProps, LearningAnalyticsViewType } from './LearningAnalyticsDashboard';

// Chart and widget components
export { LearningProgressChart } from './components/LearningProgressChart';
export type { LearningProgressChartProps } from './components/LearningProgressChart';

export { SkillMasteryWidget } from './components/SkillMasteryWidget';
export type { SkillMasteryWidgetProps } from './components/SkillMasteryWidget';

export { LearningPathProgress } from './components/LearningPathProgress';
export type { LearningPathProgressProps } from './components/LearningPathProgress';

export { SessionActivityWidget } from './components/SessionActivityWidget';
export type { SessionActivityWidgetProps } from './components/SessionActivityWidget';

// Custom hooks
export { useLearningAnalytics } from './hooks/useLearningAnalytics';
export type { UseLearningAnalyticsResult } from './hooks/useLearningAnalytics';

// Re-export service types for convenience
export type {
  LearningPathProgress as LearningPathData,
  LearningPathStatus,
  SkillMastery,
  MasteryLevel,
  SessionActivity,
  LearningProgressDataPoint,
  LearningAnalyticsSummary,
  MilestoneData,
  TimeRange,
} from '../../services/learningAnalyticsService';
