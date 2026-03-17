/**
 * Enrollment Page Object Model
 *
 * BUSINESS CONTEXT:
 * Encapsulates course enrollment workflow for students.
 * Provides methods for browsing and enrolling in courses.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Extends BasePage for common functionality
 * - Provides enrollment-specific methods
 * - Handles course search and enrollment actions
 *
 * USAGE:
 * const enrollmentPage = new EnrollmentPage();
 * enrollmentPage.visit();
 * enrollmentPage.searchCourse('Python');
 * enrollmentPage.enrollInCourse('course-123');
 */

import { BasePage } from './BasePage';

export class EnrollmentPage extends BasePage {
  // URL
  private url = '/courses';

  // Selectors
  private selectors = {
    // Search and filters
    searchInput: 'course-search-input',
    searchButton: 'search-button',
    categoryFilter: 'category-filter',
    difficultyFilter: 'difficulty-filter',
    clearFiltersButton: 'clear-filters-button',

    // Course list
    courseList: 'course-list',
    courseCard: 'course-card',
    courseTitle: 'course-title',
    courseDescription: 'course-description',
    enrollButton: 'enroll-button',
    viewDetailsButton: 'view-details-button',

    // Enrollment confirmation
    enrollmentModal: 'enrollment-modal',
    confirmEnrollButton: 'confirm-enrollment-button',
    cancelEnrollButton: 'cancel-enrollment-button',
    successMessage: 'enrollment-success-message',

    // My enrolled courses
    enrolledCoursesTab: 'enrolled-courses-tab',
    availableCoursesTab: 'available-courses-tab',
    myCoursesList: 'my-courses-list',
  };

  /**
   * Visit Enrollment Page
   *
   * NAVIGATES: To courses/enrollment page
   */
  visit(): void {
    super.visit(this.url);
    this.verifyPageLoaded();
  }

  /**
   * Verify Page Loaded
   *
   * VERIFIES: Enrollment page is fully loaded
   */
  verifyPageLoaded(): void {
    this.verifyUrl(this.url);
    this.verifyVisible(this.selectors.courseList);
  }

  /**
   * Search Course
   *
   * SEARCHES: For courses by keyword
   */
  searchCourse(keyword: string): void {
    this.fillInput(this.selectors.searchInput, keyword);
    this.clickButton(this.selectors.searchButton);
    this.waitForLoading();
  }

  /**
   * Filter By Category
   *
   * FILTERS: Courses by category
   */
  filterByCategory(category: string): void {
    this.selectOption(this.selectors.categoryFilter, category);
    this.waitForLoading();
  }

  /**
   * Filter By Difficulty
   *
   * FILTERS: Courses by difficulty level
   */
  filterByDifficulty(difficulty: string): void {
    this.selectOption(this.selectors.difficultyFilter, difficulty);
    this.waitForLoading();
  }

  /**
   * Clear Filters
   *
   * CLEARS: All active filters
   */
  clearFilters(): void {
    this.clickButton(this.selectors.clearFiltersButton);
    this.waitForLoading();
  }

  /**
   * View Course Details
   *
   * VIEWS: Detailed course information
   */
  viewCourseDetails(courseId: string): void {
    cy.get(`[data-testid="course-card-${courseId}"]`)
      .find(`[data-testid="${this.selectors.viewDetailsButton}"]`)
      .click();
    this.verifyUrl(`/courses/${courseId}`);
  }

  /**
   * Enroll In Course
   *
   * ENROLLS: Student in specified course
   */
  enrollInCourse(courseId: string): void {
    // Click enroll button for specific course
    cy.get(`[data-testid="course-card-${courseId}"]`)
      .find(`[data-testid="${this.selectors.enrollButton}"]`)
      .click();

    // Wait for confirmation modal
    this.verifyVisible(this.selectors.enrollmentModal);

    // Confirm enrollment
    this.clickButton(this.selectors.confirmEnrollButton);

    // Wait for success message
    this.verifyVisible(this.selectors.successMessage);
  }

  /**
   * Cancel Enrollment
   *
   * CANCELS: Enrollment process
   */
  cancelEnrollment(): void {
    this.clickButton(this.selectors.cancelEnrollButton);
    this.verifyNotVisible(this.selectors.enrollmentModal);
  }

  /**
   * View My Courses
   *
   * SWITCHES: To enrolled courses view
   */
  viewMyCourses(): void {
    this.clickButton(this.selectors.enrolledCoursesTab);
    this.verifyVisible(this.selectors.myCoursesList);
  }

  /**
   * View Available Courses
   *
   * SWITCHES: To available courses view
   */
  viewAvailableCourses(): void {
    this.clickButton(this.selectors.availableCoursesTab);
    this.verifyVisible(this.selectors.courseList);
  }

  /**
   * Verify Course Exists
   *
   * VERIFIES: Course appears in search results
   */
  verifyCourseExists(courseName: string): void {
    cy.get(`[data-testid="${this.selectors.courseList}"]`)
      .should('contain', courseName);
  }

  /**
   * Verify No Courses Found
   *
   * VERIFIES: No courses match search criteria
   */
  verifyNoCoursesFound(): void {
    cy.get(`[data-testid="${this.selectors.courseList}"]`)
      .should('contain', 'No courses found');
  }

  /**
   * Verify Enrollment Success
   *
   * VERIFIES: Enrollment completed successfully
   */
  verifyEnrollmentSuccess(courseName: string): void {
    this.verifyVisible(this.selectors.successMessage);
    this.verifyText(this.selectors.successMessage, courseName);
  }
}
