/**
 * Services Index
 *
 * BUSINESS CONTEXT:
 * Central export point for all API services used by the React frontend.
 * Provides clean imports for components and hooks.
 *
 * USAGE:
 * ```typescript
 * import { trainingProgramService, enrollmentService } from '@/services';
 * ```
 */

// Core services
export { apiClient } from './apiClient';
export { authService } from './authService';

// Domain services
export { trainingProgramService } from './trainingProgramService';
export { enrollmentService } from './enrollmentService';
export { analyticsService } from './analyticsService';
export { organizationService } from './organizationService';

// Type exports for convenience
export type {
  TrainingProgram,
  TrainingProgramListResponse,
  CreateTrainingProgramRequest,
  UpdateTrainingProgramRequest,
  TrainingProgramFilters,
} from './trainingProgramService';

export type {
  Enrollment,
  EnrollmentStatus,
  EnrollStudentRequest,
  BulkEnrollStudentsRequest,
  BulkEnrollStudentsInTrackRequest,
  BulkEnrollmentResponse,
  StudentEnrollmentSummary,
} from './enrollmentService';

export type {
  StudentAnalytics,
  TrainingProgramAnalytics,
  InstructorAnalytics,
  OrganizationAnalytics,
  DashboardStats,
  TimeSeriesDataPoint,
  TimeRange,
} from './analyticsService';

export type {
  Organization,
  OrganizationMember,
  CreateOrganizationRequest,
  UpdateOrganizationRequest,
  AddMemberRequest,
  BulkAddMembersRequest,
  OrganizationListResponse,
} from './organizationService';
