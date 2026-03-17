# Cypress E2E Testing Framework

## Overview

This directory contains the complete Cypress E2E testing framework for the Course Creator Platform React application. The framework provides comprehensive test coverage for all user roles and critical user journeys.

## 📁 Directory Structure

```
cypress/
├── e2e/                          # E2E test files
│   ├── auth/                     # Authentication tests
│   │   ├── login.cy.ts          # Login workflows (all roles)
│   │   ├── registration.cy.ts   # User registration
│   │   ├── password-reset.cy.ts # Password reset flow
│   │   └── logout.cy.ts         # Logout functionality
│   ├── student/                  # Student role tests
│   │   ├── course-enrollment.cy.ts
│   │   ├── course-content.cy.ts
│   │   ├── quiz-taking.cy.ts
│   │   ├── lab-environment.cy.ts
│   │   └── progress-tracking.cy.ts
│   ├── instructor/               # Instructor role tests
│   │   ├── course-creation.cy.ts
│   │   ├── content-generation.cy.ts
│   │   ├── student-management.cy.ts
│   │   ├── analytics-review.cy.ts
│   │   └── course-publishing.cy.ts
│   ├── org-admin/                # Org admin role tests
│   │   ├── organization-settings.cy.ts
│   │   ├── user-management.cy.ts
│   │   ├── track-management.cy.ts
│   │   ├── bulk-enrollment.cy.ts
│   │   └── reporting.cy.ts
│   ├── site-admin/               # Site admin role tests
│   │   ├── platform-management.cy.ts
│   │   ├── organization-management.cy.ts
│   │   ├── system-settings.cy.ts
│   │   └── platform-analytics.cy.ts
│   └── critical-paths/           # Critical user journey tests
│       ├── complete-student-journey.cy.ts
│       ├── complete-instructor-journey.cy.ts
│       ├── complete-admin-journey.cy.ts
│       └── cross-role-workflows.cy.ts
├── fixtures/                     # Test data
│   ├── users.json               # User test data
│   ├── courses.json             # Course test data
│   ├── organizations.json       # Organization test data
│   └── test-data.json           # General test data
├── support/                      # Support files
│   ├── commands.ts              # Custom Cypress commands
│   ├── e2e.ts                   # Global test setup
│   └── page-objects/            # Page Object Models
│       ├── BasePage.ts
│       ├── LoginPage.ts
│       ├── DashboardPage.ts
│       ├── CourseCreationPage.ts
│       ├── EnrollmentPage.ts
│       └── index.ts
├── downloads/                    # Downloaded files during tests
├── screenshots/                  # Test failure screenshots
├── videos/                       # Test execution videos
├── DATA_TESTID_REQUIREMENTS.md  # Required data-testid attributes
└── README.md                    # This file
```

## 🚀 Quick Start

### Installation

Cypress is already installed as a dev dependency. If you need to reinstall:

```bash
npm install --save-dev cypress
```

### Running Tests

#### Interactive Mode (Cypress Test Runner)
```bash
# Open Cypress Test Runner
npm run cypress:open

# Or directly
npx cypress open
```

#### Headless Mode (CI/CD)
```bash
# Run all E2E tests
npm run test:e2e

# Run with video output
npm run test:e2e:headed

# Run critical path tests only
npm run test:e2e:critical
```

#### Role-Specific Tests
```bash
# Run student role tests
npm run test:e2e:student

# Run instructor role tests
npm run test:e2e:instructor

# Run org admin role tests
npm run test:e2e:org-admin

# Run site admin role tests
npm run test:e2e:site-admin

# Run authentication tests
npm run test:e2e:auth
```

#### Browser-Specific Tests
```bash
# Run in Chrome
npm run cypress:run:chrome

# Run in Firefox
npm run cypress:run:firefox

# Run in Edge
npm run cypress:run:edge
```

#### Responsive Testing
```bash
# Test on mobile viewport (375x667)
npm run test:e2e:mobile

# Test on tablet viewport (768x1024)
npm run test:e2e:tablet

# Test on desktop viewport (1920x1080)
npm run test:e2e:desktop
```

## 📝 Test Structure

### Test File Naming Convention

All E2E test files follow this pattern:
- Filename: `feature-name.cy.ts`
- Example: `login.cy.ts`, `course-creation.cy.ts`

### Test Organization

Tests are organized by:
1. **Feature area** (auth, course management, etc.)
2. **User role** (student, instructor, org_admin, site_admin)
3. **Test type** (happy path, error handling, edge cases)

### Example Test Structure

```typescript
describe('Feature E2E Tests', () => {
  beforeEach(() => {
    // Setup: Navigate to page, load fixtures
  });

  describe('Happy Path Tests', () => {
    it('should complete successful workflow', () => {
      // Test implementation
    });
  });

  describe('Error Handling', () => {
    it('should handle error gracefully', () => {
      // Test implementation
    });
  });

  describe('Edge Cases', () => {
    it('should handle edge case', () => {
      // Test implementation
    });
  });
});
```

## 🔧 Custom Commands

Custom commands are defined in `cypress/support/commands.ts`.

### Authentication Commands

```typescript
// Login as specific role
cy.login('student');
cy.login('instructor');
cy.login('org_admin');
cy.login('site_admin');

// Logout
cy.logout();

// Register new user
cy.register({
  username: 'newuser@test.com',
  email: 'newuser@test.com',
  password: 'Password123!',
  firstName: 'New',
  lastName: 'User',
});

// Verify authentication state
cy.verifyAuthenticated();
cy.verifyRole('student');
```

### Navigation Commands

```typescript
// Navigate to page
cy.navigateTo('courses');
cy.navigateTo('dashboard');

// Go to dashboard
cy.goToDashboard();
```

### Course Commands

```typescript
// Create course
cy.createCourse({
  name: 'Test Course',
  description: 'Test Description',
  category: 'Programming',
  difficulty: 'Beginner',
});

// Enroll student
cy.enrollStudent('course-123');

// Publish course
cy.publishCourse('course-123');
```

### Content Generation Commands

```typescript
// Generate slides
cy.generateSlides('course-123', {
  topic: 'Introduction',
  slideCount: 10,
});

// Generate quiz
cy.generateQuiz('course-123', {
  topic: 'Chapter 1',
  questionCount: 5,
});

// Generate lab
cy.generateLab('course-123', {
  name: 'Lab 1',
  description: 'First lab',
});
```

### Admin Commands

```typescript
// Create organization
cy.createOrganization({
  name: 'Test Org',
  description: 'Test Organization',
});

// Manage users
cy.manageUsers('org-123', 'add', {
  email: 'user@test.com',
  role: 'instructor',
});

// Create track
cy.createTrack({
  name: 'Learning Path',
  description: 'Path description',
  organizationId: 'org-123',
});
```

### Utility Commands

```typescript
// Wait for loading spinner
cy.waitForSpinner();

// Fill form
cy.fillForm({
  'username-input': 'user@test.com',
  'password-input': 'password123',
});

// Verify toast message
cy.verifyToastMessage('Success!');
```

## 🎯 Page Object Models

Page Object Models (POMs) encapsulate page interactions for maintainability.

### Available Page Objects

- `BasePage` - Base class with common methods
- `LoginPage` - Login page interactions
- `DashboardPage` - Dashboard interactions (all roles)
- `CourseCreationPage` - Course creation workflow
- `EnrollmentPage` - Course enrollment workflow

### Using Page Objects

```typescript
import { LoginPage, DashboardPage } from '../support/page-objects';

it('should login and view dashboard', () => {
  const loginPage = new LoginPage();
  const dashboardPage = new DashboardPage();

  loginPage.visit();
  loginPage.login('student@test.com', 'test123');
  loginPage.verifyLoginSuccess();

  dashboardPage.verifyDashboardLoaded();
  dashboardPage.verifyStudentDashboard();
});
```

## 📊 Test Data (Fixtures)

Test data is stored in `cypress/fixtures/` as JSON files.

### Loading Fixtures

```typescript
// Load in beforeEach
beforeEach(() => {
  cy.fixture('users').then((users) => {
    cy.wrap(users).as('users');
  });
});

// Use in test
it('should use fixture data', function() {
  const student = this.users.student;
  cy.login(student.username, student.password);
});

// Or load inline
cy.fixture('courses').then((courses) => {
  const course = courses.courses[0];
  // Use course data
});
```

## ✅ Test Coverage Requirements

### Critical User Journeys (Priority 0)

These tests MUST pass before any deployment:

1. **Complete Student Journey**
   - Login → Browse → Enroll → Learn → Quiz → Lab → Certificate

2. **Complete Instructor Journey**
   - Login → Create Course → Generate Content → Publish → Manage Students → Analytics

3. **Complete Org Admin Journey**
   - Login → Manage Org → Add Users → Create Tracks → View Reports

4. **Complete Site Admin Journey**
   - Login → Platform Overview → Manage Orgs → System Settings

### Test Coverage Goals

- **Overall E2E Coverage**: 90%+
- **Critical Paths**: 100%
- **All User Roles**: Complete coverage
- **Error Scenarios**: Major error paths tested
- **Responsive Design**: Mobile, tablet, desktop

## 🐛 Debugging Tests

### View Test Execution

```bash
# Run with video recording
npm run test:e2e:headed

# Run single spec file
npx cypress run --spec "cypress/e2e/auth/login.cy.ts"

# Run in debug mode
npx cypress open --config watchForFileChanges=true
```

### Using Cypress Studio

1. Open Cypress Test Runner: `npm run cypress:open`
2. Click on a test file
3. Click "Add New Test" or "Add Commands to Test"
4. Interact with the application
5. Cypress records your actions

### Console Logging

```typescript
// Log to Cypress command log
cy.log('Debug message');

// Log to Node console
cy.task('log', 'Server-side log message');

// Log table data
cy.task('table', { key: 'value', foo: 'bar' });
```

### Screenshots and Videos

- Screenshots: Automatically captured on test failure
- Videos: Recorded for all test runs (configurable)
- Location: `cypress/screenshots/` and `cypress/videos/`

## 🔒 Environment Variables

Set environment variables in `cypress.config.ts` or via command line:

```bash
# Via command line
npx cypress run --env apiUrl=http://localhost:8000

# Via config file (cypress.config.ts)
env: {
  apiUrl: 'http://localhost:80',
  userManagementApi: 'http://localhost:8000',
}

# Access in tests
cy.env('apiUrl')
```

## 📈 CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: cypress-screenshots
          path: cypress/screenshots
      - uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: cypress-videos
          path: cypress/videos
```

## 📚 Best Practices

### 1. Use data-testid Selectors

Always prefer `data-testid` over CSS classes or IDs:

```typescript
// Good
cy.get('[data-testid="login-button"]').click();

// Avoid
cy.get('.btn-primary').click();
cy.get('#loginBtn').click();
```

### 2. Wait for Asynchronous Operations

Always wait for async operations to complete:

```typescript
// Wait for API response
cy.intercept('POST', '/api/v1/login').as('loginRequest');
cy.get('[data-testid="login-button"]').click();
cy.wait('@loginRequest');

// Wait for loading spinner
cy.waitForSpinner();

// Wait for element
cy.get('[data-testid="dashboard"]', { timeout: 10000 })
  .should('be.visible');
```

### 3. Use Custom Commands

Encapsulate common operations in custom commands:

```typescript
// Instead of repeating login logic
cy.visit('/login');
cy.get('[data-testid="username-input"]').type('user@test.com');
cy.get('[data-testid="password-input"]').type('password');
cy.get('[data-testid="login-button"]').click();

// Use custom command
cy.login('student');
```

### 4. Keep Tests Independent

Each test should be independent and not rely on other tests:

```typescript
// Good
beforeEach(() => {
  cy.login('student');
  cy.visit('/courses');
});

it('should enroll in course', () => {
  // Test logic
});

it('should view course content', () => {
  // Test logic
});

// Avoid
it('should enroll and then view content', () => {
  // Too much in one test
});
```

### 5. Clean Up Test Data

Clean up any created test data:

```typescript
afterEach(() => {
  // Clean up created courses, users, etc.
  cy.task('cleanupTestData');
});
```

## 🎓 Learning Resources

- [Cypress Documentation](https://docs.cypress.io/)
- [Cypress Best Practices](https://docs.cypress.io/guides/references/best-practices)
- [Page Object Model](https://martinfowler.com/bliki/PageObject.html)
- [Testing Library](https://testing-library.com/)

## 🆘 Troubleshooting

### Common Issues

#### Tests Timing Out

```typescript
// Increase timeout for specific command
cy.get('[data-testid="slow-element"]', { timeout: 30000 });

// Or in config (cypress.config.ts)
defaultCommandTimeout: 20000
```

#### Element Not Visible

```typescript
// Wait for element to be visible
cy.get('[data-testid="element"]').should('be.visible');

// Force click if element is covered
cy.get('[data-testid="element"]').click({ force: true });
```

#### Flaky Tests

```typescript
// Use retry configuration
retries: {
  runMode: 2,  // Retry failed tests in CI
  openMode: 0, // No retries in interactive mode
}

// Or disable test retry for specific test
it('should not retry', { retries: 0 }, () => {
  // Test logic
});
```

## 📞 Support

For questions or issues:
1. Check this README
2. Review test examples in `cypress/e2e/`
3. Consult [Cypress Documentation](https://docs.cypress.io/)
4. Check `DATA_TESTID_REQUIREMENTS.md` for required attributes

## 🔄 Updates

This testing framework should be updated when:
- New features are added to the application
- User workflows change
- New user roles are introduced
- Critical bugs are fixed (add regression tests)

---

**Last Updated**: 2025-11-05
**Version**: 1.0.0
**Maintainer**: Course Creator Platform Team
