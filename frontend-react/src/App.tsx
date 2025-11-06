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

// Eager-loaded pages (small, needed immediately)
import { Homepage } from './pages/Homepage';
import { NotFoundPage } from './pages/NotFoundPage';
import { ComingSoon } from './pages/ComingSoon';

// Lazy-loaded Auth Pages
const LoginPage = lazy(() => import('./features/auth/Login').then(m => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import('./features/auth/Register').then(m => ({ default: m.RegisterPage })));
const ForgotPasswordPage = lazy(() => import('./features/auth/ForgotPassword').then(m => ({ default: m.ForgotPasswordPage })));
const ResetPasswordPage = lazy(() => import('./features/auth/ResetPassword').then(m => ({ default: m.ResetPasswordPage })));

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

// Protected Route Wrapper (small, needed for routing logic)
import { ProtectedRoute } from './components/routing/ProtectedRoute';

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
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
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

            {/* ============================================================
             * PROTECTED ROUTES - ROLE-BASED DASHBOARDS
             * ============================================================ */}

            {/* Student Dashboard */}
            <Route
              path="/dashboard/student"
              element={
                <ProtectedRoute requiredRoles={['student']}>
                  <StudentDashboard />
                </ProtectedRoute>
              }
            />

            {/* Instructor Dashboard */}
            <Route
              path="/dashboard/instructor"
              element={
                <ProtectedRoute requiredRoles={['instructor']}>
                  <InstructorDashboard />
                </ProtectedRoute>
              }
            />

            {/* Organization Admin Dashboard */}
            <Route
              path="/dashboard/org-admin"
              element={
                <ProtectedRoute requiredRoles={['org_admin']}>
                  <OrgAdminDashboard />
                </ProtectedRoute>
              }
            />

            {/* Site Admin Dashboard */}
            <Route
              path="/dashboard/site-admin"
              element={
                <ProtectedRoute requiredRoles={['site_admin']}>
                  <SiteAdminDashboard />
                </ProtectedRoute>
              }
            />

            {/* Generic /dashboard route - redirects based on role */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <ComingSoon
                    title="Dashboard"
                    description="Please use your role-specific dashboard link to access your personalized dashboard."
                    backLink="/"
                    backLinkText="Back to Homepage"
                  />
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
                <ProtectedRoute requiredRoles={['student']}>
                  <LabEnvironment />
                </ProtectedRoute>
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
                <ProtectedRoute requiredRoles={['instructor']}>
                  <ContentGenerationPage />
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
                <ProtectedRoute requiredRoles={['org_admin']}>
                  <ManageTrainers />
                </ProtectedRoute>
              }
            />

            {/* Bulk Enroll Students */}
            <Route
              path="/organization/students/enroll"
              element={
                <ProtectedRoute requiredRoles={['org_admin']}>
                  <BulkEnrollStudents />
                </ProtectedRoute>
              }
            />

            {/* Organization Training Programs */}
            <Route
              path="/organization/programs"
              element={
                <ProtectedRoute requiredRoles={['org_admin']}>
                  <TrainingProgramListPage context="organization" />
                </ProtectedRoute>
              }
            />

            {/* Training Analytics & Compliance */}
            <Route
              path="/organization/analytics"
              element={
                <ProtectedRoute requiredRoles={['org_admin']}>
                  <AnalyticsDashboard viewType="course" />
                </ProtectedRoute>
              }
            />

            {/* Organization Course Analytics */}
            <Route
              path="/organization/courses/:courseId/analytics"
              element={
                <ProtectedRoute requiredRoles={['org_admin']}>
                  <AnalyticsDashboard viewType="course" />
                </ProtectedRoute>
              }
            />

            {/* Organization Settings */}
            <Route
              path="/organization/settings"
              element={
                <ProtectedRoute requiredRoles={['org_admin']}>
                  <OrganizationSettings />
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
        </BrowserRouter>
      </QueryClientProvider>
    </Provider>
  );
}

export default App;
