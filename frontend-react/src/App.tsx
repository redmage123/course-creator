/**
 * Main Application Component
 *
 * BUSINESS CONTEXT:
 * Root component for Course Creator Platform React application.
 * Manages routing, authentication, and global providers.
 *
 * TECHNICAL IMPLEMENTATION:
 * Wraps application with Redux Provider, React Query, and React Router.
 * Implements route-based code splitting with React.lazy() for optimal performance.
 *
 * PERFORMANCE OPTIMIZATION:
 * - All routes use lazy loading to reduce initial bundle size
 * - Homepage loads ~150KB instead of 864KB
 * - Each dashboard/feature loads on-demand when accessed
 * - Suspense provides loading states during chunk downloads
 */

import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Provider } from 'react-redux';
import { store } from '@store/index';
import { Spinner } from './components/atoms/Spinner';
import { ErrorBoundary } from './components/common/ErrorBoundary';

// Eager-loaded pages (small, needed immediately)
import { Homepage } from './pages/Homepage';
import { NotFoundPage } from './pages/NotFoundPage';
import { ComingSoon } from './pages/ComingSoon';

// Global AI Assistant Widget
import { GlobalAIAssistant } from './components/organisms/GlobalAIAssistant';

// Lazy-loaded Auth Pages
const LoginPage = lazy(() => import('./features/auth/Login').then(m => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import('./features/auth/Register').then(m => ({ default: m.RegisterPage })));
const ForgotPasswordPage = lazy(() => import('./features/auth/ForgotPassword').then(m => ({ default: m.ForgotPasswordPage })));
const ResetPasswordPage = lazy(() => import('./features/auth/ResetPassword').then(m => ({ default: m.ResetPasswordPage })));

// Lazy-loaded Organization Registration (public self-service)
const OrganizationRegistration = lazy(() => import('./pages/OrganizationRegistration').then(m => ({ default: m.OrganizationRegistration })));

// Lazy-loaded Student Certificates
const StudentCertificates = lazy(() => import('./pages/StudentCertificates').then(m => ({ default: m.StudentCertificates })));

// Lazy-loaded Password Change
const PasswordChange = lazy(() => import('./pages/PasswordChange').then(m => ({ default: m.PasswordChange })));

// Lazy-loaded Dashboard Pages
const StudentDashboard = lazy(() => import('./features/dashboard/pages/StudentDashboard').then(m => ({ default: m.StudentDashboard })));
const InstructorDashboard = lazy(() => import('./features/dashboard/pages/InstructorDashboard').then(m => ({ default: m.InstructorDashboard })));
const OrgAdminDashboard = lazy(() => import('./features/dashboard/pages/OrgAdminDashboard').then(m => ({ default: m.OrgAdminDashboard })));
const SiteAdminDashboard = lazy(() => import('./features/dashboard/pages/SiteAdminDashboard').then(m => ({ default: m.SiteAdminDashboard })));

// Lazy-loaded Training Program Pages
const TrainingProgramListPage = lazy(() => import('./features/courses/pages').then(m => ({ default: m.TrainingProgramListPage })));
const TrainingProgramDetailPage = lazy(() => import('./features/courses/pages').then(m => ({ default: m.TrainingProgramDetailPage })));
const CreateEditTrainingProgramPage = lazy(() => import('./features/courses/pages').then(m => ({ default: m.CreateEditTrainingProgramPage })));
const ContentGenerationPage = lazy(() => import('./features/courses/pages').then(m => ({ default: m.ContentGenerationPage })));

// Lazy-loaded Lab Environment (large - Monaco Editor)
const LabEnvironment = lazy(() => import('./features/labs/LabEnvironment').then(m => ({ default: m.LabEnvironment })));

// Lazy-loaded Quiz
const QuizTaking = lazy(() => import('./features/quizzes/QuizTaking').then(m => ({ default: m.QuizTaking })));

// Lazy-loaded Analytics
const AnalyticsDashboard = lazy(() => import('./features/analytics/AnalyticsDashboard').then(m => ({ default: m.AnalyticsDashboard })));

// Lazy-loaded Placeholder Pages
const ManageStudents = lazy(() => import('./pages/ManageStudents').then(m => ({ default: m.ManageStudents })));
const EnrollStudents = lazy(() => import('./pages/EnrollStudents').then(m => ({ default: m.EnrollStudents })));
const LabEnvironmentsList = lazy(() => import('./pages/LabEnvironmentsList').then(m => ({ default: m.LabEnvironmentsList })));
const ManageTrainers = lazy(() => import('./pages/ManageTrainers').then(m => ({ default: m.ManageTrainers })));
const BulkEnrollStudents = lazy(() => import('./pages/BulkEnrollStudents').then(m => ({ default: m.BulkEnrollStudents })));
const OrganizationSettings = lazy(() => import('./pages/OrganizationSettings').then(m => ({ default: m.OrganizationSettings })));
const ManageOrganizations = lazy(() => import('./pages/ManageOrganizations').then(m => ({ default: m.ManageOrganizations })));
const CreateOrganization = lazy(() => import('./pages/CreateOrganization').then(m => ({ default: m.CreateOrganization })));
const ManageUsers = lazy(() => import('./pages/ManageUsers').then(m => ({ default: m.ManageUsers })));
const SystemSettings = lazy(() => import('./pages/SystemSettings').then(m => ({ default: m.SystemSettings })));

// Lazy-loaded Organization Members and Tracks Pages
const MembersPage = lazy(() => import('./features/members/pages/MembersPage').then(m => ({ default: m.MembersPage })));
const TracksPage = lazy(() => import('./features/tracks/pages/TracksPage').then(m => ({ default: m.TracksPage })));

// Lazy-loaded Course Pages
const CourseCreatePage = lazy(() => import('./features/courses/pages/CourseCreatePage').then(m => ({ default: m.CourseCreatePage })));

// Lazy-loaded Import, Quiz, and Resources Pages
const ImportTemplatePage = lazy(() => import('./pages/ImportTemplatePage').then(m => ({ default: m.ImportTemplatePage })));
const QuizListPage = lazy(() => import('./pages/QuizListPage').then(m => ({ default: m.QuizListPage })));
const ResourcesPage = lazy(() => import('./pages/ResourcesPage').then(m => ({ default: m.ResourcesPage })));

// Lazy-loaded Demo Page
const DemoPage = lazy(() => import('./features/demo/pages/DemoPage').then(m => ({ default: m.DemoPage })));

// ============================================================
// Lazy-loaded Enhancement Features (Enhancements 9-13)
// ============================================================

// Enhancement 9: Learning Analytics Dashboard
const LearningAnalyticsDashboard = lazy(() =>
  import('./features/learning-analytics/LearningAnalyticsDashboard').then(m => ({ default: m.LearningAnalyticsDashboard }))
);

// Enhancement 10: Instructor Insights Dashboard
const InstructorInsightsDashboard = lazy(() =>
  import('./features/instructor-insights/InstructorInsightsDashboard').then(m => ({ default: m.InstructorInsightsDashboard }))
);

// Enhancement 12: Integrations Settings
const IntegrationsSettings = lazy(() =>
  import('./features/integrations/IntegrationsSettings').then(m => ({ default: m.IntegrationsSettings }))
);

// Enhancement 13: Accessibility Settings
const AccessibilitySettings = lazy(() =>
  import('./features/accessibility/AccessibilitySettings').then(m => ({ default: m.AccessibilitySettings }))
);

// Protected Route Wrapper (small, needed for routing logic)
import { ProtectedRoute } from './components/routing/ProtectedRoute';

// Dashboard Redirect (role-based navigation)
import { DashboardRedirect } from './components/routing/DashboardRedirect';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

/**
 * Loading Fallback Component
 * Displayed while lazy-loaded route chunks are downloading
 */
const RouteLoadingFallback = () => (
  <div style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    background: '#f5f5f5'
  }}>
    <Spinner size="large" />
  </div>
);

/**
 * Main App Component
 *
 * WHY THIS APPROACH:
 * - Provider hierarchy ensures all children have access to global state
 * - React Router handles client-side navigation
 * - React Query manages server state caching
 * - Redux manages global app state
 * - Suspense enables lazy loading with fallback UI
 * - Route-based code splitting reduces initial bundle size by ~80%
 */
function App() {
  return (
    <ErrorBoundary>
      <Provider store={store}>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <ErrorBoundary>
              <Suspense fallback={<RouteLoadingFallback />}>
                <Routes>
            {/* ============================================================
             * PUBLIC ROUTES (No Authentication Required)
             * ============================================================ */}
            <Route path="/" element={<Homepage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />

            {/* Organization Registration - Public self-service */}
            <Route path="/organization/register" element={<OrganizationRegistration />} />

            {/* Demo Page - Interactive platform walkthrough */}
            <Route path="/demo" element={<DemoPage />} />

            {/* ============================================================
             * PROTECTED ROUTES - ROLE-BASED DASHBOARDS
             * ============================================================ */}

            {/* Student Dashboard */}
            <Route
              path="/dashboard/student"
              element={
                <ErrorBoundary>
                  <ProtectedRoute requiredRoles={['student']}>
                    <StudentDashboard />
                  </ProtectedRoute>
                </ErrorBoundary>
              }
            />

            {/* Instructor Dashboard */}
            <Route
              path="/dashboard/instructor"
              element={
                <ErrorBoundary>
                  <ProtectedRoute requiredRoles={['instructor']}>
                    <InstructorDashboard />
                  </ProtectedRoute>
                </ErrorBoundary>
              }
            />

            {/* Organization Admin Dashboard */}
            <Route
              path="/dashboard/org-admin"
              element={
                <ErrorBoundary>
                  <ProtectedRoute requiredRoles={['organization_admin']}>
                    <OrgAdminDashboard />
                  </ProtectedRoute>
                </ErrorBoundary>
              }
            />

            {/* Site Admin Dashboard */}
            <Route
              path="/dashboard/site-admin"
              element={
                <ErrorBoundary>
                  <ProtectedRoute requiredRoles={['site_admin']}>
                    <SiteAdminDashboard />
                  </ProtectedRoute>
                </ErrorBoundary>
              }
            />

            {/* Generic /dashboard route - redirects based on role */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardRedirect />
                </ProtectedRoute>
              }
            />

            {/* ============================================================
             * PROTECTED ROUTES - STUDENT FEATURES
             * (Students are ASSIGNED courses by trainers - no browsing/selection)
             * ============================================================ */}

            {/* My Assigned Courses */}
            <Route
              path="/courses/my-courses"
              element={
                <ProtectedRoute requiredRoles={['student']}>
                  <TrainingProgramListPage context="instructor" />
                </ProtectedRoute>
              }
            />

            {/* Course Details (for all roles) */}
            <Route
              path="/courses/:courseId"
              element={
                <ProtectedRoute>
                  <TrainingProgramDetailPage />
                </ProtectedRoute>
              }
            />

            {/* Lab Environment - Individual Lab */}
            <Route
              path="/labs/:labId/course/:courseId"
              element={
                <ErrorBoundary>
                  <ProtectedRoute requiredRoles={['student']}>
                    <LabEnvironment />
                  </ProtectedRoute>
                </ErrorBoundary>
              }
            />

            {/* Lab Environments List */}
            <Route
              path="/labs"
              element={
                <ProtectedRoute requiredRoles={['student']}>
                  <LabEnvironmentsList />
                </ProtectedRoute>
              }
            />

            {/* Quiz Taking */}
            <Route
              path="/quizzes/:quizId/course/:courseId"
              element={
                <ProtectedRoute requiredRoles={['student']}>
                  <QuizTaking />
                </ProtectedRoute>
              }
            />

            {/* Quiz List - All student quizzes */}
            <Route
              path="/quizzes"
              element={
                <ProtectedRoute requiredRoles={['student']}>
                  <QuizListPage />
                </ProtectedRoute>
              }
            />

            {/* Quiz History */}
            <Route
              path="/quizzes/history"
              element={
                <ProtectedRoute requiredRoles={['student']}>
                  <QuizListPage />
                </ProtectedRoute>
              }
            />

            {/* Learning Resources */}
            <Route
              path="/resources"
              element={
                <ProtectedRoute requiredRoles={['student']}>
                  <ResourcesPage />
                </ProtectedRoute>
              }
            />

            {/* Download Materials */}
            <Route
              path="/resources/download"
              element={
                <ProtectedRoute requiredRoles={['student']}>
                  <ResourcesPage />
                </ProtectedRoute>
              }
            />

            {/* Progress Tracking / Analytics */}
            <Route
              path="/progress"
              element={
                <ProtectedRoute requiredRoles={['student']}>
                  <AnalyticsDashboard viewType="student" />
                </ProtectedRoute>
              }
            />

            {/* Student Analytics for specific course */}
            <Route
              path="/courses/:courseId/analytics"
              element={
                <ProtectedRoute requiredRoles={['student']}>
                  <AnalyticsDashboard viewType="student" />
                </ProtectedRoute>
              }
            />

            {/* Student Certificates */}
            <Route
              path="/certificates"
              element={
                <ProtectedRoute requiredRoles={['student']}>
                  <StudentCertificates />
                </ProtectedRoute>
              }
            />

            {/* Enhancement 9: Learning Analytics Dashboard */}
            <Route
              path="/learning-analytics"
              element={
                <ProtectedRoute requiredRoles={['student']}>
                  <LearningAnalyticsDashboard />
                </ProtectedRoute>
              }
            />

            {/* ============================================================
             * PROTECTED ROUTES - INSTRUCTOR (CORPORATE TRAINER) FEATURES
             * ============================================================ */}

            {/* Training Programs List */}
            <Route
              path="/instructor/programs"
              element={
                <ProtectedRoute requiredRoles={['instructor']}>
                  <TrainingProgramListPage context="instructor" />
                </ProtectedRoute>
              }
            />

            {/* Create Training Program */}
            <Route
              path="/instructor/programs/create"
              element={
                <ProtectedRoute requiredRoles={['instructor']}>
                  <CreateEditTrainingProgramPage />
                </ProtectedRoute>
              }
            />

            {/* Edit Training Program */}
            <Route
              path="/instructor/programs/:programId/edit"
              element={
                <ProtectedRoute requiredRoles={['instructor']}>
                  <CreateEditTrainingProgramPage />
                </ProtectedRoute>
              }
            />

            {/* Manage Students */}
            <Route
              path="/instructor/students"
              element={
                <ProtectedRoute requiredRoles={['instructor']}>
                  <ManageStudents />
                </ProtectedRoute>
              }
            />

            {/* Enroll Students */}
            <Route
              path="/instructor/students/enroll"
              element={
                <ProtectedRoute requiredRoles={['instructor']}>
                  <EnrollStudents />
                </ProtectedRoute>
              }
            />

            {/* Training Analytics */}
            <Route
              path="/instructor/analytics"
              element={
                <ProtectedRoute requiredRoles={['instructor']}>
                  <AnalyticsDashboard viewType="instructor" />
                </ProtectedRoute>
              }
            />

            {/* Student Analytics for specific student */}
            <Route
              path="/instructor/students/:studentId/analytics"
              element={
                <ProtectedRoute requiredRoles={['instructor']}>
                  <AnalyticsDashboard viewType="instructor" />
                </ProtectedRoute>
              }
            />

            {/* AI Content Generator */}
            <Route
              path="/instructor/content-generator"
              element={
                <ErrorBoundary>
                  <ProtectedRoute requiredRoles={['instructor']}>
                    <ContentGenerationPage />
                  </ProtectedRoute>
                </ErrorBoundary>
              }
            />

            {/* Instructor Bulk Enrollment */}
            <Route
              path="/instructor/students/bulk-enroll"
              element={
                <ProtectedRoute requiredRoles={['instructor']}>
                  <BulkEnrollStudents />
                </ProtectedRoute>
              }
            />

            {/* Instructor Lab Creation */}
            <Route
              path="/instructor/labs/create"
              element={
                <ProtectedRoute requiredRoles={['instructor']}>
                  <LabEnvironmentsList />
                </ProtectedRoute>
              }
            />

            {/* Enhancement 10: Instructor Insights Dashboard */}
            <Route
              path="/instructor/insights"
              element={
                <ProtectedRoute requiredRoles={['instructor']}>
                  <InstructorInsightsDashboard />
                </ProtectedRoute>
              }
            />

            {/* ============================================================
             * PROTECTED ROUTES - ORGANIZATION ADMIN FEATURES
             * (Corporate training program management)
             * ============================================================ */}

            {/* Manage Corporate Trainers */}
            <Route
              path="/organization/trainers"
              element={
                <ProtectedRoute requiredRoles={['organization_admin']}>
                  <ManageTrainers />
                </ProtectedRoute>
              }
            />

            {/* Bulk Enroll Students */}
            <Route
              path="/organization/students/enroll"
              element={
                <ProtectedRoute requiredRoles={['organization_admin']}>
                  <BulkEnrollStudents />
                </ProtectedRoute>
              }
            />

            {/* Organization Training Programs */}
            <Route
              path="/organization/programs"
              element={
                <ProtectedRoute requiredRoles={['organization_admin']}>
                  <TrainingProgramListPage context="organization" />
                </ProtectedRoute>
              }
            />

            {/* Create Training Program (Organization Admin) */}
            <Route
              path="/organization/programs/create"
              element={
                <ProtectedRoute requiredRoles={['organization_admin']}>
                  <CreateEditTrainingProgramPage />
                </ProtectedRoute>
              }
            />

            {/* Edit Training Program (Organization Admin) */}
            <Route
              path="/organization/programs/:programId/edit"
              element={
                <ProtectedRoute requiredRoles={['organization_admin']}>
                  <CreateEditTrainingProgramPage />
                </ProtectedRoute>
              }
            />

            {/* Organization Members Management */}
            <Route
              path="/organization/members"
              element={
                <ProtectedRoute requiredRoles={['organization_admin']}>
                  <MembersPage />
                </ProtectedRoute>
              }
            />

            {/* Organization Tracks Management */}
            <Route
              path="/organization/tracks"
              element={
                <ProtectedRoute requiredRoles={['organization_admin']}>
                  <TracksPage />
                </ProtectedRoute>
              }
            />

            {/* Course Creation (Organization Admin & Instructor) */}
            <Route
              path="/organization/courses/create"
              element={
                <ProtectedRoute requiredRoles={['organization_admin', 'instructor']}>
                  <CourseCreatePage />
                </ProtectedRoute>
              }
            />

            {/* Training Analytics & Compliance */}
            <Route
              path="/organization/analytics"
              element={
                <ProtectedRoute requiredRoles={['organization_admin']}>
                  <AnalyticsDashboard viewType="course" />
                </ProtectedRoute>
              }
            />

            {/* Organization Course Analytics */}
            <Route
              path="/organization/courses/:courseId/analytics"
              element={
                <ProtectedRoute requiredRoles={['organization_admin']}>
                  <AnalyticsDashboard viewType="course" />
                </ProtectedRoute>
              }
            />

            {/* Organization Settings */}
            <Route
              path="/organization/settings"
              element={
                <ProtectedRoute requiredRoles={['organization_admin']}>
                  <OrganizationSettings />
                </ProtectedRoute>
              }
            />

            {/* Import Organization Template */}
            <Route
              path="/organization/import"
              element={
                <ProtectedRoute requiredRoles={['organization_admin']}>
                  <ImportTemplatePage />
                </ProtectedRoute>
              }
            />

            {/* AI Auto Create Project */}
            <Route
              path="/organization/ai-create"
              element={
                <ProtectedRoute requiredRoles={['organization_admin']}>
                  <ImportTemplatePage />
                </ProtectedRoute>
              }
            />

            {/* Download Organization Template */}
            <Route
              path="/organization/templates/download"
              element={
                <ProtectedRoute requiredRoles={['organization_admin']}>
                  <ImportTemplatePage />
                </ProtectedRoute>
              }
            />

            {/* Enhancement 12: Organization Integrations Settings */}
            <Route
              path="/organization/integrations"
              element={
                <ProtectedRoute requiredRoles={['organization_admin']}>
                  <IntegrationsSettings organizationId="" />
                </ProtectedRoute>
              }
            />

            {/* ============================================================
             * PROTECTED ROUTES - SITE ADMIN FEATURES
             * ============================================================ */}

            {/* Manage Organizations */}
            <Route
              path="/admin/organizations"
              element={
                <ProtectedRoute requiredRoles={['site_admin']}>
                  <ManageOrganizations />
                </ProtectedRoute>
              }
            />

            {/* Create Organization */}
            <Route
              path="/admin/organizations/create"
              element={
                <ProtectedRoute requiredRoles={['site_admin']}>
                  <CreateOrganization />
                </ProtectedRoute>
              }
            />

            {/* Manage Users */}
            <Route
              path="/admin/users"
              element={
                <ProtectedRoute requiredRoles={['site_admin']}>
                  <ManageUsers />
                </ProtectedRoute>
              }
            />

            {/* Platform Analytics */}
            <Route
              path="/admin/analytics"
              element={
                <ProtectedRoute requiredRoles={['site_admin']}>
                  <AnalyticsDashboard viewType="course" />
                </ProtectedRoute>
              }
            />

            {/* System Settings */}
            <Route
              path="/admin/settings"
              element={
                <ProtectedRoute requiredRoles={['site_admin']}>
                  <SystemSettings />
                </ProtectedRoute>
              }
            />

            {/* ============================================================
             * PROTECTED ROUTES - USER SETTINGS (ALL ROLES)
             * ============================================================ */}

            {/* Password Change */}
            <Route
              path="/settings/password"
              element={
                <ProtectedRoute>
                  <PasswordChange />
                </ProtectedRoute>
              }
            />

            {/* Enhancement 13: Accessibility Settings */}
            <Route
              path="/settings/accessibility"
              element={
                <ProtectedRoute>
                  <AccessibilitySettings />
                </ProtectedRoute>
              }
            />

            {/* ============================================================
             * ERROR PAGES
             * ============================================================ */}

            {/* Unauthorized Access */}
            <Route
              path="/unauthorized"
              element={<NotFoundPage />}
            />

            {/* 404 Not Found - Catch-all route */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
              </Suspense>
              {/* Global AI Assistant - Available on all pages */}
              <GlobalAIAssistant />
            </ErrorBoundary>
          </BrowserRouter>
        </QueryClientProvider>
      </Provider>
    </ErrorBoundary>
  );
}

export default App;
