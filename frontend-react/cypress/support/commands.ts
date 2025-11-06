/**
 * Custom Cypress Commands
 *
 * BUSINESS CONTEXT:
 * Reusable authentication, navigation, and interaction commands
 * for testing the Course Creator Platform across all user roles.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Authentication commands: login, logout, register
 * - Navigation commands: navigateTo, goToPage
 * - Course commands: createCourse, enrollStudent, publishCourse
 * - Content commands: generateContent, createQuiz, createLab
 * - Admin commands: createOrganization, manageUsers, configureTracks
 * - Assertion commands: verifyAuthenticated, verifyRole
 *
 * USAGE:
 * cy.login('instructor')
 * cy.createCourse({ name: 'Test Course', description: 'Test' })
 * cy.enrollStudent('course-123', 'student-456')
 */

/// <reference types="cypress" />

/**
 * Type Definitions for Custom Commands
 *
 * EXTENDS: Cypress.Chainable interface with custom commands
 */
declare global {
  namespace Cypress {
    interface Chainable {
      // Authentication commands
      login(role: 'student' | 'instructor' | 'org_admin' | 'site_admin'): Chainable<void>;
      logout(): Chainable<void>;
      register(userData: UserRegistrationData): Chainable<void>;
      verifyAuthenticated(): Chainable<void>;
      verifyRole(role: string): Chainable<void>;

      // Navigation commands
      navigateTo(page: string): Chainable<void>;
      goToDashboard(): Chainable<void>;

      // Course commands
      createCourse(courseData: CourseData): Chainable<string>;
      enrollStudent(courseId: string, studentId?: string): Chainable<void>;
      publishCourse(courseId: string): Chainable<void>;

      // Content generation commands
      generateSlides(courseId: string, topicData: any): Chainable<void>;
      generateQuiz(courseId: string, quizData: any): Chainable<void>;
      generateLab(courseId: string, labData: any): Chainable<void>;

      // Admin commands
      createOrganization(orgData: OrganizationData): Chainable<string>;
      manageUsers(orgId: string, action: string, userData: any): Chainable<void>;
      createTrack(trackData: TrackData): Chainable<string>;

      // Utility commands
      waitForSpinner(): Chainable<void>;
      fillForm(formData: Record<string, string>): Chainable<void>;
      verifyToastMessage(message: string): Chainable<void>;
    }
  }
}

/**
 * Type Definitions for Command Parameters
 */
interface UserRegistrationData {
  username: string;
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  organizationName?: string;
}

interface CourseData {
  name: string;
  description: string;
  category?: string;
  difficulty?: string;
  estimatedHours?: number;
}

interface OrganizationData {
  name: string;
  description?: string;
  domain?: string;
}

interface TrackData {
  name: string;
  description: string;
  organizationId: string;
}

/**
 * ============================================================================
 * AUTHENTICATION COMMANDS
 * ============================================================================
 */

/**
 * Login Command
 *
 * AUTHENTICATES: User with specified role
 *
 * PARAMETERS:
 * @param role - User role (student, instructor, org_admin, site_admin)
 *
 * WORKFLOW:
 * 1. Visit login page
 * 2. Enter credentials
 * 3. Submit form
 * 4. Verify redirect to dashboard
 * 5. Store auth token in localStorage
 */
Cypress.Commands.add('login', (role: 'student' | 'instructor' | 'org_admin' | 'site_admin') => {
  // Test credentials for each role
  const credentials = {
    student: {
      username: 'student@test.com',
      password: 'test123',
      expectedRole: 'student',
    },
    instructor: {
      username: 'instructor@test.com',
      password: 'test123',
      expectedRole: 'instructor',
    },
    org_admin: {
      username: 'orgadmin@test.com',
      password: 'test123',
      expectedRole: 'organization_admin',
    },
    site_admin: {
      username: 'admin@test.com',
      password: 'test123',
      expectedRole: 'site_admin',
    },
  };

  const creds = credentials[role];

  // Visit login page
  cy.visit('/login');

  // Wait for login form to be visible
  cy.get('[data-testid="login-form"]', { timeout: 10000 }).should('be.visible');

  // Fill in credentials
  cy.get('[data-testid="username-input"]').clear().type(creds.username);
  cy.get('[data-testid="password-input"]').clear().type(creds.password);

  // Submit form
  cy.get('[data-testid="login-button"]').click();

  // Wait for navigation away from login page
  cy.url({ timeout: 10000 }).should('not.include', '/login');

  // Verify authentication token exists
  cy.window().then((win) => {
    const authToken = win.localStorage.getItem('authToken');
    expect(authToken).to.exist;
  });

  // Verify user role
  cy.verifyRole(creds.expectedRole);
});

/**
 * Logout Command
 *
 * LOGS OUT: Current authenticated user
 *
 * WORKFLOW:
 * 1. Click logout button
 * 2. Verify redirect to login page
 * 3. Verify auth token removed
 */
Cypress.Commands.add('logout', () => {
  // Click logout button (adjust selector based on your UI)
  cy.get('[data-testid="logout-button"]', { timeout: 5000 }).click();

  // Verify redirect to login page
  cy.url({ timeout: 10000 }).should('include', '/login');

  // Verify auth token removed
  cy.window().then((win) => {
    const authToken = win.localStorage.getItem('authToken');
    expect(authToken).to.be.null;
  });
});

/**
 * Register Command
 *
 * REGISTERS: New user account
 *
 * PARAMETERS:
 * @param userData - User registration data
 */
Cypress.Commands.add('register', (userData: UserRegistrationData) => {
  cy.visit('/register');

  cy.get('[data-testid="username-input"]').type(userData.username);
  cy.get('[data-testid="email-input"]').type(userData.email);
  cy.get('[data-testid="password-input"]').type(userData.password);
  cy.get('[data-testid="confirm-password-input"]').type(userData.password);
  cy.get('[data-testid="first-name-input"]').type(userData.firstName);
  cy.get('[data-testid="last-name-input"]').type(userData.lastName);

  if (userData.organizationName) {
    cy.get('[data-testid="organization-name-input"]').type(userData.organizationName);
  }

  cy.get('[data-testid="register-button"]').click();

  // Verify successful registration
  cy.url({ timeout: 10000 }).should('not.include', '/register');
});

/**
 * Verify Authenticated Command
 *
 * VERIFIES: User is authenticated
 */
Cypress.Commands.add('verifyAuthenticated', () => {
  cy.window().then((win) => {
    const authToken = win.localStorage.getItem('authToken');
    expect(authToken).to.exist;
  });
});

/**
 * Verify Role Command
 *
 * VERIFIES: User has expected role
 *
 * PARAMETERS:
 * @param role - Expected role
 */
Cypress.Commands.add('verifyRole', (role: string) => {
  cy.window().then((win) => {
    const userRole = win.localStorage.getItem('userRole');
    expect(userRole).to.equal(role);
  });
});

/**
 * ============================================================================
 * NAVIGATION COMMANDS
 * ============================================================================
 */

/**
 * Navigate To Command
 *
 * NAVIGATES: To specified page
 *
 * PARAMETERS:
 * @param page - Page identifier
 */
Cypress.Commands.add('navigateTo', (page: string) => {
  const routes: Record<string, string> = {
    dashboard: '/dashboard',
    courses: '/courses',
    'my-courses': '/my-courses',
    analytics: '/analytics',
    settings: '/settings',
    users: '/users',
    organizations: '/organizations',
    tracks: '/tracks',
  };

  const route = routes[page] || page;
  cy.visit(route);
  cy.url().should('include', route);
});

/**
 * Go To Dashboard Command
 *
 * NAVIGATES: To user dashboard
 */
Cypress.Commands.add('goToDashboard', () => {
  cy.get('[data-testid="dashboard-nav"]').click();
  cy.url().should('include', '/dashboard');
});

/**
 * ============================================================================
 * COURSE COMMANDS
 * ============================================================================
 */

/**
 * Create Course Command
 *
 * CREATES: New course
 *
 * PARAMETERS:
 * @param courseData - Course data
 *
 * RETURNS: Course ID
 */
Cypress.Commands.add('createCourse', (courseData: CourseData) => {
  cy.navigateTo('courses');

  cy.get('[data-testid="create-course-button"]').click();

  cy.get('[data-testid="course-name-input"]').type(courseData.name);
  cy.get('[data-testid="course-description-input"]').type(courseData.description);

  if (courseData.category) {
    cy.get('[data-testid="course-category-select"]').select(courseData.category);
  }

  if (courseData.difficulty) {
    cy.get('[data-testid="course-difficulty-select"]').select(courseData.difficulty);
  }

  cy.get('[data-testid="create-course-submit"]').click();

  // Wait for success message
  cy.verifyToastMessage('Course created successfully');

  // Extract course ID from URL
  cy.url().then((url) => {
    const courseId = url.split('/').pop() || '';
    cy.wrap(courseId);
  });
});

/**
 * Enroll Student Command
 *
 * ENROLLS: Student in course
 *
 * PARAMETERS:
 * @param courseId - Course ID
 * @param studentId - Student ID (optional, uses current user if not provided)
 */
Cypress.Commands.add('enrollStudent', (courseId: string, studentId?: string) => {
  cy.visit(`/courses/${courseId}`);

  cy.get('[data-testid="enroll-button"]').click();

  if (studentId) {
    cy.get('[data-testid="student-search-input"]').type(studentId);
    cy.get(`[data-testid="student-option-${studentId}"]`).click();
  }

  cy.get('[data-testid="confirm-enrollment-button"]').click();

  cy.verifyToastMessage('Successfully enrolled');
});

/**
 * Publish Course Command
 *
 * PUBLISHES: Course (makes it available to students)
 *
 * PARAMETERS:
 * @param courseId - Course ID
 */
Cypress.Commands.add('publishCourse', (courseId: string) => {
  cy.visit(`/courses/${courseId}/settings`);

  cy.get('[data-testid="publish-course-button"]').click();
  cy.get('[data-testid="confirm-publish-button"]').click();

  cy.verifyToastMessage('Course published successfully');
});

/**
 * ============================================================================
 * CONTENT GENERATION COMMANDS
 * ============================================================================
 */

/**
 * Generate Slides Command
 *
 * GENERATES: Slides for course topic
 */
Cypress.Commands.add('generateSlides', (courseId: string, topicData: any) => {
  cy.visit(`/courses/${courseId}/content`);

  cy.get('[data-testid="generate-slides-button"]').click();
  cy.get('[data-testid="topic-input"]').type(topicData.topic);
  cy.get('[data-testid="generate-button"]').click();

  cy.waitForSpinner();
  cy.verifyToastMessage('Slides generated successfully');
});

/**
 * Generate Quiz Command
 *
 * GENERATES: Quiz for course
 */
Cypress.Commands.add('generateQuiz', (courseId: string, quizData: any) => {
  cy.visit(`/courses/${courseId}/quizzes`);

  cy.get('[data-testid="generate-quiz-button"]').click();
  cy.get('[data-testid="quiz-topic-input"]').type(quizData.topic);
  cy.get('[data-testid="question-count-input"]').type(quizData.questionCount.toString());
  cy.get('[data-testid="generate-button"]').click();

  cy.waitForSpinner();
  cy.verifyToastMessage('Quiz generated successfully');
});

/**
 * Generate Lab Command
 *
 * GENERATES: Lab environment for course
 */
Cypress.Commands.add('generateLab', (courseId: string, labData: any) => {
  cy.visit(`/courses/${courseId}/labs`);

  cy.get('[data-testid="create-lab-button"]').click();
  cy.get('[data-testid="lab-name-input"]').type(labData.name);
  cy.get('[data-testid="lab-description-input"]').type(labData.description);
  cy.get('[data-testid="create-button"]').click();

  cy.verifyToastMessage('Lab created successfully');
});

/**
 * ============================================================================
 * ADMIN COMMANDS
 * ============================================================================
 */

/**
 * Create Organization Command
 *
 * CREATES: New organization
 *
 * RETURNS: Organization ID
 */
Cypress.Commands.add('createOrganization', (orgData: OrganizationData) => {
  cy.navigateTo('organizations');

  cy.get('[data-testid="create-organization-button"]').click();
  cy.get('[data-testid="org-name-input"]').type(orgData.name);

  if (orgData.description) {
    cy.get('[data-testid="org-description-input"]').type(orgData.description);
  }

  cy.get('[data-testid="create-org-submit"]').click();

  cy.verifyToastMessage('Organization created successfully');

  cy.url().then((url) => {
    const orgId = url.split('/').pop() || '';
    cy.wrap(orgId);
  });
});

/**
 * Manage Users Command
 *
 * MANAGES: Organization users (add, remove, update roles)
 */
Cypress.Commands.add('manageUsers', (orgId: string, action: string, userData: any) => {
  cy.visit(`/organizations/${orgId}/users`);

  if (action === 'add') {
    cy.get('[data-testid="add-user-button"]').click();
    cy.get('[data-testid="user-email-input"]').type(userData.email);
    cy.get('[data-testid="user-role-select"]').select(userData.role);
    cy.get('[data-testid="add-user-submit"]').click();
  }

  cy.verifyToastMessage('User updated successfully');
});

/**
 * Create Track Command
 *
 * CREATES: Learning track
 *
 * RETURNS: Track ID
 */
Cypress.Commands.add('createTrack', (trackData: TrackData) => {
  cy.visit(`/organizations/${trackData.organizationId}/tracks`);

  cy.get('[data-testid="create-track-button"]').click();
  cy.get('[data-testid="track-name-input"]').type(trackData.name);
  cy.get('[data-testid="track-description-input"]').type(trackData.description);
  cy.get('[data-testid="create-track-submit"]').click();

  cy.verifyToastMessage('Track created successfully');

  cy.url().then((url) => {
    const trackId = url.split('/').pop() || '';
    cy.wrap(trackId);
  });
});

/**
 * ============================================================================
 * UTILITY COMMANDS
 * ============================================================================
 */

/**
 * Wait For Spinner Command
 *
 * WAITS: For loading spinner to disappear
 */
Cypress.Commands.add('waitForSpinner', () => {
  cy.get('[data-testid="loading-spinner"]', { timeout: 30000 }).should('not.exist');
});

/**
 * Fill Form Command
 *
 * FILLS: Form fields based on data-testid
 *
 * PARAMETERS:
 * @param formData - Object with field testIds as keys and values to fill
 */
Cypress.Commands.add('fillForm', (formData: Record<string, string>) => {
  Object.entries(formData).forEach(([testId, value]) => {
    cy.get(`[data-testid="${testId}"]`).clear().type(value);
  });
});

/**
 * Verify Toast Message Command
 *
 * VERIFIES: Toast notification message appears
 *
 * PARAMETERS:
 * @param message - Expected message text
 */
Cypress.Commands.add('verifyToastMessage', (message: string) => {
  cy.get('[data-testid="toast-message"]', { timeout: 10000 })
    .should('be.visible')
    .and('contain', message);
});

// Export to enable TypeScript support
export {};
