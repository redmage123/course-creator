/**
 * Dashboard Page Object Model
 *
 * BUSINESS CONTEXT:
 * Encapsulates dashboard page interactions for all user roles.
 * Provides role-specific dashboard verification and navigation.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Extends BasePage for common functionality
 * - Provides dashboard-specific methods
 * - Handles role-based dashboard elements
 *
 * USAGE:
 * const dashboard = new DashboardPage();
 * dashboard.visit();
 * dashboard.verifyStudentDashboard();
 * dashboard.navigateToCourses();
 */

import { BasePage } from './BasePage';

export class DashboardPage extends BasePage {
  // URL
  private url = '/dashboard';

  // Common selectors
  private selectors = {
    welcomeMessage: 'welcome-message',
    userProfile: 'user-profile',
    logoutButton: 'logout-button',
    notificationsBell: 'notifications-bell',

    // Navigation
    dashboardNav: 'dashboard-nav',
    coursesNav: 'courses-nav',
    analyticsNav: 'analytics-nav',
    settingsNav: 'settings-nav',

    // Student dashboard
    enrolledCourses: 'enrolled-courses',
    continueLearningSectiong: 'continue-learning-section',
    progressSummary: 'progress-summary',

    // Instructor dashboard
    myCourses: 'my-courses',
    createCourseButton: 'create-course-button',
    studentStats: 'student-stats',

    // Admin dashboards
    organizationsList: 'organizations-list',
    usersManagement: 'users-management',
    platformStats: 'platform-stats',
  };

  /**
   * Visit Dashboard
   *
   * NAVIGATES: To dashboard page
   */
  visit(): void {
    super.visit(this.url);
  }

  /**
   * Verify Dashboard Loaded
   *
   * VERIFIES: Dashboard is fully loaded
   */
  verifyDashboardLoaded(): void {
    this.verifyUrl(this.url);
    this.verifyVisible(this.selectors.welcomeMessage);
    this.verifyVisible(this.selectors.userProfile);
  }

  /**
   * Verify Student Dashboard
   *
   * VERIFIES: Student-specific dashboard elements visible
   */
  verifyStudentDashboard(): void {
    this.verifyDashboardLoaded();
    this.verifyVisible(this.selectors.enrolledCourses);
    this.verifyVisible(this.selectors.continueLearningSectiong);
    this.verifyVisible(this.selectors.progressSummary);
  }

  /**
   * Verify Instructor Dashboard
   *
   * VERIFIES: Instructor-specific dashboard elements visible
   */
  verifyInstructorDashboard(): void {
    this.verifyDashboardLoaded();
    this.verifyVisible(this.selectors.myCourses);
    this.verifyVisible(this.selectors.createCourseButton);
    this.verifyVisible(this.selectors.studentStats);
  }

  /**
   * Verify Org Admin Dashboard
   *
   * VERIFIES: Organization admin dashboard elements visible
   */
  verifyOrgAdminDashboard(): void {
    this.verifyDashboardLoaded();
    this.verifyVisible(this.selectors.usersManagement);
    this.verifyVisible(this.selectors.organizationsList);
  }

  /**
   * Verify Site Admin Dashboard
   *
   * VERIFIES: Site admin dashboard elements visible
   */
  verifySiteAdminDashboard(): void {
    this.verifyDashboardLoaded();
    this.verifyVisible(this.selectors.platformStats);
    this.verifyVisible(this.selectors.organizationsList);
  }

  /**
   * Navigate To Courses
   *
   * NAVIGATES: To courses page
   */
  navigateToCourses(): void {
    this.clickButton(this.selectors.coursesNav);
    this.verifyUrl('/courses');
  }

  /**
   * Navigate To Analytics
   *
   * NAVIGATES: To analytics page
   */
  navigateToAnalytics(): void {
    this.clickButton(this.selectors.analyticsNav);
    this.verifyUrl('/analytics');
  }

  /**
   * Navigate To Settings
   *
   * NAVIGATES: To settings page
   */
  navigateToSettings(): void {
    this.clickButton(this.selectors.settingsNav);
    this.verifyUrl('/settings');
  }

  /**
   * Logout
   *
   * PERFORMS: Logout action
   */
  logout(): void {
    this.clickButton(this.selectors.logoutButton);
    this.verifyUrl('/login');
  }

  /**
   * Verify Welcome Message
   *
   * VERIFIES: Welcome message contains user name
   */
  verifyWelcomeMessage(userName: string): void {
    this.verifyText(this.selectors.welcomeMessage, userName);
  }

  /**
   * View Notifications
   *
   * OPENS: Notifications panel
   */
  viewNotifications(): void {
    this.clickButton(this.selectors.notificationsBell);
  }
}
