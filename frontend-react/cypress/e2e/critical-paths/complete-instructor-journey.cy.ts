/**
 * Complete Instructor Journey E2E Test
 *
 * BUSINESS CONTEXT:
 * Tests the complete instructor workflow from login to course publishing.
 * This is a CRITICAL PATH test that verifies the core instructor experience.
 *
 * USER JOURNEY:
 * 1. Instructor logs in
 * 2. Creates a new course
 * 3. Generates course content (slides, quizzes, labs)
 * 4. Reviews and edits content
 * 5. Publishes course
 * 6. Manages student enrollments
 * 7. Views analytics and student progress
 * 8. Responds to student questions
 * 9. Logs out
 *
 * SUCCESS CRITERIA:
 * - Instructor can create and publish courses
 * - AI content generation works
 * - Student management features accessible
 * - Analytics and reporting functional
 *
 * CRITICAL REQUIREMENT (from CLAUDE.md):
 * Priority 0 test - Must implement first
 * Complete instructor workflow (Create Course → Generate Content → Manage Students → Analytics)
 */

import { LoginPage, DashboardPage, CourseCreationPage } from '../../support/page-objects';

describe('Complete Instructor Journey E2E', () => {
  let courseId: string;

  before(() => {
    cy.task('log', '🎯 Starting Complete Instructor Journey E2E Test');
  });

  it('should complete full instructor workflow', () => {
    /**
     * STEP 1: Instructor Login
     */
    cy.task('log', '📝 Step 1: Instructor Login');

    cy.login('instructor');

    const dashboardPage = new DashboardPage();
    dashboardPage.verifyDashboardLoaded();
    dashboardPage.verifyInstructorDashboard();

    cy.task('log', '✅ Step 1 Complete: Instructor logged in');

    /**
     * STEP 2: Create New Course
     */
    cy.task('log', '📝 Step 2: Create New Course');

    const coursePage = new CourseCreationPage();
    coursePage.visit();

    coursePage.createCompleteCourse({
      name: 'E2E Test Course',
      description: 'Course created during E2E testing',
      category: 'Programming',
      difficulty: 'Beginner',
      estimatedHours: 20,
    });

    coursePage.verifySuccess();

    // Extract course ID from URL
    cy.url().then((url) => {
      courseId = url.split('/').pop() || '';
      cy.wrap(courseId).as('courseId');
    });

    cy.task('log', '✅ Step 2 Complete: Course created');

    /**
     * STEP 3: Generate Course Content with AI
     */
    cy.task('log', '📝 Step 3: Generate Course Content');

    // Generate slides
    cy.get('@courseId').then((id) => {
      cy.generateSlides(id as string, {
        topic: 'Introduction to Programming',
        slideCount: 10,
      });
    });

    cy.verifyToastMessage('Slides generated successfully');

    // Generate quiz
    cy.get('@courseId').then((id) => {
      cy.generateQuiz(id as string, {
        topic: 'Programming Basics',
        questionCount: 5,
        difficulty: 'easy',
      });
    });

    cy.verifyToastMessage('Quiz generated successfully');

    // Generate lab
    cy.get('@courseId').then((id) => {
      cy.generateLab(id as string, {
        name: 'First Programming Lab',
        description: 'Write your first program',
        environment: 'python',
      });
    });

    cy.verifyToastMessage('Lab created successfully');

    cy.task('log', '✅ Step 3 Complete: Content generated');

    /**
     * STEP 4: Review and Edit Content
     */
    cy.task('log', '📝 Step 4: Review and Edit Content');

    cy.get('@courseId').then((id) => {
      cy.visit(`/courses/${id}/content`);
    });

    // Review slides
    cy.get('[data-testid="slide-list"]').should('be.visible');
    cy.get('[data-testid="slide-card"]').should('have.length.greaterThan', 0);

    // Edit a slide
    cy.get('[data-testid="slide-card"]').first().click();
    cy.get('[data-testid="edit-slide-button"]').click();
    cy.get('[data-testid="slide-content-editor"]').type(' - Updated');
    cy.get('[data-testid="save-slide-button"]').click();

    cy.verifyToastMessage('Slide updated');

    cy.task('log', '✅ Step 4 Complete: Content reviewed and edited');

    /**
     * STEP 5: Publish Course
     */
    cy.task('log', '📝 Step 5: Publish Course');

    cy.get('@courseId').then((id) => {
      cy.publishCourse(id as string);
    });

    cy.verifyToastMessage('Course published successfully');

    cy.task('log', '✅ Step 5 Complete: Course published');

    /**
     * STEP 6: Manage Student Enrollments
     */
    cy.task('log', '📝 Step 6: Manage Student Enrollments');

    cy.get('@courseId').then((id) => {
      cy.visit(`/courses/${id}/students`);
    });

    // View enrolled students
    cy.get('[data-testid="student-list"]').should('be.visible');

    // Manually enroll a student
    cy.get('[data-testid="enroll-student-button"]').click();
    cy.get('[data-testid="student-search-input"]').type('student@test.com');
    cy.get('[data-testid="student-option-student@test.com"]').click();
    cy.get('[data-testid="confirm-enroll-button"]').click();

    cy.verifyToastMessage('Student enrolled successfully');

    cy.task('log', '✅ Step 6 Complete: Students managed');

    /**
     * STEP 7: View Analytics and Student Progress
     */
    cy.task('log', '📝 Step 7: View Analytics');

    cy.get('@courseId').then((id) => {
      cy.visit(`/courses/${id}/analytics`);
    });

    // Verify analytics dashboard
    cy.get('[data-testid="analytics-dashboard"]').should('be.visible');
    cy.get('[data-testid="enrollment-stats"]').should('be.visible');
    cy.get('[data-testid="completion-rate"]').should('be.visible');
    cy.get('[data-testid="quiz-performance"]').should('be.visible');

    // View individual student progress
    cy.get('[data-testid="student-progress-link"]').first().click();
    cy.get('[data-testid="student-detail-view"]').should('be.visible');

    cy.task('log', '✅ Step 7 Complete: Analytics reviewed');

    /**
     * STEP 8: Respond to Student Questions
     */
    cy.task('log', '📝 Step 8: Respond to Student Questions');

    cy.get('@courseId').then((id) => {
      cy.visit(`/courses/${id}/discussions`);
    });

    // View discussion board
    cy.get('[data-testid="discussion-board"]').should('be.visible');

    // Respond to a question
    cy.get('[data-testid="discussion-thread"]').first().click();
    cy.get('[data-testid="reply-input"]').type('Great question! Here is the answer...');
    cy.get('[data-testid="post-reply-button"]').click();

    cy.verifyToastMessage('Reply posted');

    cy.task('log', '✅ Step 8 Complete: Student questions answered');

    /**
     * STEP 9: Logout
     */
    cy.task('log', '📝 Step 9: Logout');

    cy.logout();

    cy.task('log', '🎉 COMPLETE INSTRUCTOR JOURNEY TEST PASSED');
  });
});
