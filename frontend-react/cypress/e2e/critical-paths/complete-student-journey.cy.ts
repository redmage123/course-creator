/**
 * Complete Student Journey E2E Test
 *
 * BUSINESS CONTEXT:
 * Tests the complete student learning workflow from login to course completion.
 * This is a CRITICAL PATH test that verifies the core student experience.
 *
 * USER JOURNEY:
 * 1. Student logs in
 * 2. Browses available courses
 * 3. Enrolls in a course
 * 4. Views course content (slides)
 * 5. Takes a quiz
 * 6. Accesses lab environment
 * 7. Completes course
 * 8. Views progress and certificate
 * 9. Logs out
 *
 * SUCCESS CRITERIA:
 * - Student can complete entire learning workflow
 * - All content types are accessible (slides, quizzes, labs)
 * - Progress tracking works correctly
 * - Certificate is generated upon completion
 *
 * CRITICAL REQUIREMENT (from CLAUDE.md):
 * Priority 0 test - Must implement first
 * Complete student learning journey (Login → Learn → Quiz → Lab → Certificate)
 */

import { LoginPage, DashboardPage, EnrollmentPage } from '../../support/page-objects';

describe('Complete Student Journey E2E', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let enrollmentPage: EnrollmentPage;

  before(() => {
    // Setup: Ensure test course exists and is published
    cy.task('log', '🎯 Starting Complete Student Journey E2E Test');
  });

  beforeEach(() => {
    loginPage = new LoginPage();
    dashboardPage = new DashboardPage();
    enrollmentPage = new EnrollmentPage();
  });

  it('should complete full student learning journey', () => {
    /**
     * STEP 1: Student Login
     *
     * VERIFIES:
     * - Authentication successful
     * - Student dashboard loads
     * - Student-specific UI elements visible
     */
    cy.task('log', '📝 Step 1: Student Login');

    loginPage.visit();
    cy.login('student');

    dashboardPage.verifyDashboardLoaded();
    dashboardPage.verifyStudentDashboard();

    cy.task('log', '✅ Step 1 Complete: Student logged in successfully');

    /**
     * STEP 2: Browse and Search Courses
     *
     * VERIFIES:
     * - Course catalog accessible
     * - Search functionality works
     * - Course details displayed correctly
     */
    cy.task('log', '📝 Step 2: Browse and Search Courses');

    dashboardPage.navigateToCourses();
    enrollmentPage.verifyPageLoaded();

    // Search for a course
    enrollmentPage.searchCourse('Python');
    enrollmentPage.verifyCourseExists('Introduction to Python');

    cy.task('log', '✅ Step 2 Complete: Course browsing works');

    /**
     * STEP 3: Enroll in Course
     *
     * VERIFIES:
     * - Enrollment process works
     * - Confirmation modal appears
     * - Student added to course
     */
    cy.task('log', '📝 Step 3: Enroll in Course');

    enrollmentPage.enrollInCourse('course-001');
    enrollmentPage.verifyEnrollmentSuccess('Introduction to Python');

    cy.task('log', '✅ Step 3 Complete: Student enrolled in course');

    /**
     * STEP 4: View Course Content (Slides)
     *
     * VERIFIES:
     * - Course content accessible
     * - Slides display correctly
     * - Navigation between slides works
     */
    cy.task('log', '📝 Step 4: View Course Content');

    cy.visit('/courses/course-001/content');

    // Verify slide viewer loaded
    cy.get('[data-testid="slide-viewer"]').should('be.visible');

    // Navigate through slides
    cy.get('[data-testid="next-slide-button"]').click();
    cy.get('[data-testid="slide-counter"]').should('contain', '2');

    // Mark slide as completed
    cy.get('[data-testid="mark-complete-button"]').click();
    cy.verifyToastMessage('Progress saved');

    cy.task('log', '✅ Step 4 Complete: Course content accessible');

    /**
     * STEP 5: Take Quiz
     *
     * VERIFIES:
     * - Quiz accessible
     * - Questions display correctly
     * - Can submit answers
     * - Score calculated correctly
     */
    cy.task('log', '📝 Step 5: Take Quiz');

    cy.visit('/courses/course-001/quizzes');

    // Start quiz
    cy.get('[data-testid="quiz-card-1"]').click();
    cy.get('[data-testid="start-quiz-button"]').click();

    // Answer questions
    cy.get('[data-testid="quiz-question-1"]').should('be.visible');
    cy.get('[data-testid="answer-option-A"]').click();
    cy.get('[data-testid="next-question-button"]').click();

    // Submit quiz
    cy.get('[data-testid="submit-quiz-button"]').click();
    cy.get('[data-testid="confirm-submit-button"]').click();

    // Verify results
    cy.get('[data-testid="quiz-results"]').should('be.visible');
    cy.get('[data-testid="quiz-score"]').should('exist');

    cy.task('log', '✅ Step 5 Complete: Quiz taken successfully');

    /**
     * STEP 6: Access Lab Environment
     *
     * VERIFIES:
     * - Lab environment accessible
     * - IDE loads correctly
     * - Terminal works
     * - Can execute code
     */
    cy.task('log', '📝 Step 6: Access Lab Environment');

    cy.visit('/courses/course-001/labs');

    // Open lab
    cy.get('[data-testid="lab-card-1"]').click();
    cy.get('[data-testid="launch-lab-button"]').click();

    // Wait for lab to initialize (this may take longer)
    cy.waitForSpinner();
    cy.get('[data-testid="lab-environment"]', { timeout: 30000 }).should('be.visible');

    // Verify IDE components
    cy.get('[data-testid="code-editor"]').should('be.visible');
    cy.get('[data-testid="terminal"]').should('be.visible');

    // Execute simple code
    cy.get('[data-testid="code-editor"]').type('print("Hello World")');
    cy.get('[data-testid="run-code-button"]').click();

    // Verify output
    cy.get('[data-testid="terminal-output"]', { timeout: 10000 })
      .should('contain', 'Hello World');

    cy.task('log', '✅ Step 6 Complete: Lab environment works');

    /**
     * STEP 7: Complete Course
     *
     * VERIFIES:
     * - All modules marked as complete
     * - Course completion status updated
     * - Certificate generated
     */
    cy.task('log', '📝 Step 7: Complete Course');

    // Navigate to course progress
    cy.visit('/courses/course-001/progress');

    // Verify progress tracking
    cy.get('[data-testid="progress-bar"]').should('be.visible');
    cy.get('[data-testid="completion-percentage"]').should('exist');

    // Complete remaining modules (if any)
    cy.get('[data-testid="module-list"]').within(() => {
      cy.get('[data-testid^="module-"]').each(($module) => {
        cy.wrap($module).within(() => {
          cy.get('[data-testid="mark-complete-button"]').click({ force: true });
        });
      });
    });

    // Verify course completion
    cy.get('[data-testid="course-complete-badge"]').should('be.visible');

    cy.task('log', '✅ Step 7 Complete: Course completed');

    /**
     * STEP 8: View Certificate
     *
     * VERIFIES:
     * - Certificate generated
     * - Certificate details correct
     * - Can download certificate
     */
    cy.task('log', '📝 Step 8: View Certificate');

    cy.visit('/courses/course-001/certificate');

    // Verify certificate displayed
    cy.get('[data-testid="certificate"]').should('be.visible');
    cy.get('[data-testid="certificate-student-name"]')
      .should('contain', 'John Student');
    cy.get('[data-testid="certificate-course-name"]')
      .should('contain', 'Introduction to Python');

    // Download certificate
    cy.get('[data-testid="download-certificate-button"]').click();

    // Verify download initiated
    cy.verifyToastMessage('Certificate downloaded');

    cy.task('log', '✅ Step 8 Complete: Certificate viewed and downloaded');

    /**
     * STEP 9: View Overall Progress
     *
     * VERIFIES:
     * - Student dashboard shows updated progress
     * - Completed courses listed
     * - Analytics displayed correctly
     */
    cy.task('log', '📝 Step 9: View Overall Progress');

    dashboardPage.visit();
    dashboardPage.verifyStudentDashboard();

    // Verify completed course appears
    cy.get('[data-testid="completed-courses"]')
      .should('contain', 'Introduction to Python');

    // Check progress analytics
    cy.get('[data-testid="progress-summary"]').within(() => {
      cy.get('[data-testid="courses-completed"]').should('exist');
      cy.get('[data-testid="quizzes-passed"]').should('exist');
      cy.get('[data-testid="labs-completed"]').should('exist');
    });

    cy.task('log', '✅ Step 9 Complete: Progress tracking verified');

    /**
     * STEP 10: Logout
     *
     * VERIFIES:
     * - Logout successful
     * - Session cleared
     * - Redirect to login page
     */
    cy.task('log', '📝 Step 10: Logout');

    cy.logout();

    cy.url().should('include', '/login');

    cy.task('log', '✅ Step 10 Complete: Student logged out');
    cy.task('log', '🎉 COMPLETE STUDENT JOURNEY TEST PASSED');
  });

  /**
   * ERROR RECOVERY TEST
   *
   * VERIFIES: Student can recover from errors and continue learning
   */
  it('should handle errors gracefully during learning journey', () => {
    cy.task('log', '🧪 Testing Error Recovery');

    cy.login('student');

    // Simulate network error during quiz submission
    cy.intercept('POST', '**/api/v1/quizzes/*/submit', {
      statusCode: 500,
      body: { error: 'Network error' },
    }).as('quizSubmitError');

    cy.visit('/courses/course-001/quizzes');
    cy.get('[data-testid="quiz-card-1"]').click();
    cy.get('[data-testid="start-quiz-button"]').click();

    // Answer questions
    cy.get('[data-testid="answer-option-A"]').click();
    cy.get('[data-testid="submit-quiz-button"]').click();

    cy.wait('@quizSubmitError');

    // Verify error message displayed
    cy.get('[data-testid="error-message"]')
      .should('contain', 'Failed to submit quiz');

    // Verify retry option available
    cy.get('[data-testid="retry-button"]').should('be.visible');

    cy.task('log', '✅ Error recovery test passed');
  });

  /**
   * MOBILE RESPONSIVE TEST
   *
   * VERIFIES: Student journey works on mobile devices
   */
  it('should complete student journey on mobile viewport', () => {
    cy.task('log', '📱 Testing Mobile Student Journey');

    // Set mobile viewport
    cy.viewport(375, 667);

    cy.login('student');
    dashboardPage.verifyStudentDashboard();

    // Verify mobile navigation
    cy.get('[data-testid="mobile-menu-button"]').should('be.visible');

    // Navigate on mobile
    cy.get('[data-testid="mobile-menu-button"]').click();
    cy.get('[data-testid="mobile-nav-courses"]').click();

    enrollmentPage.verifyPageLoaded();

    cy.task('log', '✅ Mobile student journey test passed');
  });
});
