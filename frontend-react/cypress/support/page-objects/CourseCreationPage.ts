/**
 * Course Creation Page Object Model
 *
 * BUSINESS CONTEXT:
 * Encapsulates course creation workflow for instructors.
 * Provides methods for creating and configuring courses.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Extends BasePage for common functionality
 * - Provides course creation wizard methods
 * - Handles multi-step course creation process
 *
 * USAGE:
 * const coursePage = new CourseCreationPage();
 * coursePage.visit();
 * coursePage.fillBasicInfo('Course Name', 'Description');
 * coursePage.selectCategory('Programming');
 * coursePage.submitCourse();
 */

import { BasePage } from './BasePage';

export class CourseCreationPage extends BasePage {
  // URL
  private url = '/courses/create';

  // Selectors
  private selectors = {
    // Basic info
    courseNameInput: 'course-name-input',
    courseDescriptionInput: 'course-description-input',
    courseCategorySelect: 'course-category-select',
    courseDifficultySelect: 'course-difficulty-select',
    estimatedHoursInput: 'estimated-hours-input',

    // Advanced settings
    maxEnrollmentsInput: 'max-enrollments-input',
    startDateInput: 'start-date-input',
    endDateInput: 'end-date-input',
    enableLabsCheckbox: 'enable-labs-checkbox',
    enableQuizzesCheckbox: 'enable-quizzes-checkbox',

    // Buttons
    nextButton: 'next-button',
    previousButton: 'previous-button',
    submitButton: 'create-course-submit',
    cancelButton: 'cancel-button',

    // Validation
    errorMessage: 'error-message',
    successMessage: 'success-message',
  };

  /**
   * Visit Course Creation Page
   *
   * NAVIGATES: To course creation page
   */
  visit(): void {
    super.visit(this.url);
    this.verifyPageLoaded();
  }

  /**
   * Verify Page Loaded
   *
   * VERIFIES: Course creation page is fully loaded
   */
  verifyPageLoaded(): void {
    this.verifyUrl(this.url);
    this.verifyVisible(this.selectors.courseNameInput);
  }

  /**
   * Fill Basic Info
   *
   * FILLS: Basic course information
   */
  fillBasicInfo(name: string, description: string): void {
    this.fillInput(this.selectors.courseNameInput, name);
    this.fillInput(this.selectors.courseDescriptionInput, description);
  }

  /**
   * Select Category
   *
   * SELECTS: Course category
   */
  selectCategory(category: string): void {
    this.selectOption(this.selectors.courseCategorySelect, category);
  }

  /**
   * Select Difficulty
   *
   * SELECTS: Course difficulty level
   */
  selectDifficulty(difficulty: string): void {
    this.selectOption(this.selectors.courseDifficultySelect, difficulty);
  }

  /**
   * Set Estimated Hours
   *
   * FILLS: Estimated completion hours
   */
  setEstimatedHours(hours: number): void {
    this.fillInput(this.selectors.estimatedHoursInput, hours.toString());
  }

  /**
   * Enable Labs
   *
   * ENABLES: Lab environments for course
   */
  enableLabs(): void {
    this.clickButton(this.selectors.enableLabsCheckbox);
  }

  /**
   * Enable Quizzes
   *
   * ENABLES: Quizzes for course
   */
  enableQuizzes(): void {
    this.clickButton(this.selectors.enableQuizzesCheckbox);
  }

  /**
   * Set Course Dates
   *
   * SETS: Course start and end dates
   */
  setCourseDates(startDate: string, endDate: string): void {
    this.fillInput(this.selectors.startDateInput, startDate);
    this.fillInput(this.selectors.endDateInput, endDate);
  }

  /**
   * Click Next
   *
   * ADVANCES: To next step in wizard
   */
  clickNext(): void {
    this.clickButton(this.selectors.nextButton);
  }

  /**
   * Click Previous
   *
   * RETURNS: To previous step in wizard
   */
  clickPrevious(): void {
    this.clickButton(this.selectors.previousButton);
  }

  /**
   * Submit Course
   *
   * SUBMITS: Course creation form
   */
  submitCourse(): void {
    this.clickButton(this.selectors.submitButton);
    this.waitForLoading();
  }

  /**
   * Cancel Creation
   *
   * CANCELS: Course creation
   */
  cancelCreation(): void {
    this.clickButton(this.selectors.cancelButton);
  }

  /**
   * Verify Success
   *
   * VERIFIES: Course created successfully
   */
  verifySuccess(): void {
    this.verifyVisible(this.selectors.successMessage);
    cy.url().should('not.include', this.url);
  }

  /**
   * Verify Error
   *
   * VERIFIES: Error message displayed
   */
  verifyError(errorText: string): void {
    this.verifyVisible(this.selectors.errorMessage);
    this.verifyText(this.selectors.errorMessage, errorText);
  }

  /**
   * Create Complete Course
   *
   * PERFORMS: Complete course creation workflow
   */
  createCompleteCourse(courseData: {
    name: string;
    description: string;
    category: string;
    difficulty: string;
    estimatedHours: number;
  }): void {
    this.fillBasicInfo(courseData.name, courseData.description);
    this.selectCategory(courseData.category);
    this.selectDifficulty(courseData.difficulty);
    this.setEstimatedHours(courseData.estimatedHours);
    this.enableLabs();
    this.enableQuizzes();
    this.submitCourse();
  }
}
