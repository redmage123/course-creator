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
export { tokenManager } from './tokenManager';

// Domain services
export { trainingProgramService } from './trainingProgramService';
export { enrollmentService } from './enrollmentService';
export { analyticsService } from './analyticsService';
export { organizationService } from './organizationService';
export { memberService } from './memberService';
export { trackService } from './trackService';
export { courseService } from './courseService';
export { syllabusService } from './syllabusService';
export { bugService } from './bugService';

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

export type {
  Member,
  MemberRole,
  CreateMemberRequest,
  UpdateMemberRequest,
  MemberListResponse,
} from './memberService';

export type {
  Track,
  CreateTrackRequest,
  UpdateTrackRequest,
  TrackListResponse,
  TrackEnrollmentRequest,
  TrackEnrollmentResponse,
  TrackAnalytics,
} from './trackService';

export type {
  Course,
  DifficultyLevel,
  DurationUnit,
  CreateCourseRequest,
  UpdateCourseRequest,
  CourseListResponse,
  CourseFilters,
} from './courseService';

export type {
  CourseLevel,
  ContentSourceType,
  ExternalSourceConfig,
  SyllabusModule,
  ModuleTopic,
  SyllabusData,
  GenerateSyllabusRequest,
  GenerateSyllabusResponse,
  GenerationProgress,
  GetProgressResponse,
  SourceSummary,
} from './syllabusService';

export type {
  BugSeverity,
  BugStatus,
  ComplexityEstimate,
  BugSubmissionRequest,
  BugReport,
  BugAnalysis,
  BugFix,
  BugDetail,
  BugListResponse,
  BugFilters,
} from './bugService';
