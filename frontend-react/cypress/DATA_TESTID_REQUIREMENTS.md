# Data-TestID Requirements for E2E Testing

## Purpose
This document lists all `data-testid` attributes required in React components for Cypress E2E testing. These attributes provide reliable selectors that are resistant to UI changes.

## Naming Convention
- Use kebab-case for all data-testid values
- Be descriptive and specific
- Include component type where helpful (button, input, modal, etc.)
- Example: `create-course-button`, `username-input`, `enrollment-modal`

## Critical Requirements

### 1. Authentication Components

#### Login Page (`/login`)
```tsx
// Form and inputs
data-testid="login-form"
data-testid="username-input"
data-testid="password-input"
data-testid="login-button"
data-testid="remember-me-checkbox"
data-testid="forgot-password-link"
data-testid="register-link"
data-testid="error-message"

// Validation
data-testid="username-error"
data-testid="password-error"
```

#### Registration Page (`/register`)
```tsx
// Form fields
data-testid="username-input"
data-testid="email-input"
data-testid="password-input"
data-testid="confirm-password-input"
data-testid="first-name-input"
data-testid="last-name-input"
data-testid="organization-name-input"
data-testid="register-button"

// Validation
data-testid="password-strength-indicator"
data-testid="error-message"
data-testid="success-message"

// Privacy compliance
data-testid="privacy-policy-checkbox"
data-testid="privacy-policy-link"
data-testid="terms-of-service-link"
```

#### Password Reset Page (`/forgot-password`)
```tsx
data-testid="email-input"
data-testid="send-reset-link-button"
data-testid="success-message"
data-testid="error-message"
data-testid="back-to-login-link"
```

### 2. Dashboard Components

#### Common Dashboard Elements (All Roles)
```tsx
// Header
data-testid="page-title"
data-testid="welcome-message"
data-testid="user-profile"
data-testid="logout-button"
data-testid="notifications-bell"
data-testid="settings-button"

// Navigation
data-testid="dashboard-nav"
data-testid="courses-nav"
data-testid="analytics-nav"
data-testid="settings-nav"

// Mobile navigation
data-testid="mobile-menu-button"
data-testid="mobile-nav-courses"
data-testid="mobile-nav-dashboard"
```

#### Student Dashboard (`/dashboard` - Student Role)
```tsx
data-testid="enrolled-courses"
data-testid="continue-learning-section"
data-testid="progress-summary"
data-testid="completed-courses"
data-testid="courses-completed"
data-testid="quizzes-passed"
data-testid="labs-completed"
data-testid="recent-activity"
```

#### Instructor Dashboard (`/dashboard` - Instructor Role)
```tsx
data-testid="my-courses"
data-testid="create-course-button"
data-testid="student-stats"
data-testid="course-stats"
data-testid="recent-submissions"
data-testid="pending-reviews"
```

#### Organization Admin Dashboard
```tsx
data-testid="organizations-list"
data-testid="users-management"
data-testid="track-management"
data-testid="org-stats"
```

#### Site Admin Dashboard
```tsx
data-testid="platform-stats"
data-testid="all-organizations"
data-testid="system-health"
data-testid="user-statistics"
```

### 3. Course Components

#### Course Creation Page (`/courses/create`)
```tsx
// Basic information
data-testid="course-name-input"
data-testid="course-description-input"
data-testid="course-category-select"
data-testid="course-difficulty-select"
data-testid="estimated-hours-input"

// Advanced settings
data-testid="max-enrollments-input"
data-testid="start-date-input"
data-testid="end-date-input"
data-testid="enable-labs-checkbox"
data-testid="enable-quizzes-checkbox"

// Navigation buttons
data-testid="next-button"
data-testid="previous-button"
data-testid="create-course-submit"
data-testid="cancel-button"

// Feedback
data-testid="error-message"
data-testid="success-message"
```

#### Course List/Browse Page (`/courses`)
```tsx
// Search and filters
data-testid="course-search-input"
data-testid="search-button"
data-testid="category-filter"
data-testid="difficulty-filter"
data-testid="clear-filters-button"

// Course list
data-testid="course-list"
data-testid="course-card"
data-testid="course-card-{id}"  // Dynamic with course ID
data-testid="course-title"
data-testid="course-description"
data-testid="enroll-button"
data-testid="view-details-button"

// Tabs
data-testid="enrolled-courses-tab"
data-testid="available-courses-tab"
data-testid="my-courses-list"
```

#### Enrollment Components
```tsx
data-testid="enrollment-modal"
data-testid="confirm-enrollment-button"
data-testid="cancel-enrollment-button"
data-testid="enrollment-success-message"
data-testid="student-search-input"
data-testid="student-option-{email}"  // Dynamic with student email
```

### 4. Course Content Components

#### Slide Viewer (`/courses/:id/content`)
```tsx
data-testid="slide-viewer"
data-testid="slide-list"
data-testid="slide-card"
data-testid="slide-counter"
data-testid="slide-content"
data-testid="next-slide-button"
data-testid="previous-slide-button"
data-testid="mark-complete-button"
data-testid="edit-slide-button"
data-testid="slide-content-editor"
data-testid="save-slide-button"
```

#### Content Generation
```tsx
// Slide generation
data-testid="generate-slides-button"
data-testid="topic-input"
data-testid="slide-count-input"
data-testid="generate-button"

// Quiz generation
data-testid="generate-quiz-button"
data-testid="quiz-topic-input"
data-testid="question-count-input"

// Lab creation
data-testid="create-lab-button"
data-testid="lab-name-input"
data-testid="lab-description-input"
data-testid="lab-environment-select"
data-testid="create-button"
```

### 5. Quiz Components

#### Quiz Taking Interface (`/courses/:id/quizzes`)
```tsx
// Quiz list
data-testid="quiz-card-{id}"  // Dynamic with quiz ID
data-testid="start-quiz-button"

// Quiz questions
data-testid="quiz-question-{number}"  // Dynamic with question number
data-testid="answer-option-A"
data-testid="answer-option-B"
data-testid="answer-option-C"
data-testid="answer-option-D"
data-testid="next-question-button"
data-testid="previous-question-button"
data-testid="submit-quiz-button"
data-testid="confirm-submit-button"

// Results
data-testid="quiz-results"
data-testid="quiz-score"
data-testid="correct-answers"
data-testid="incorrect-answers"
data-testid="review-quiz-button"
data-testid="retake-quiz-button"
```

### 6. Lab Environment Components

#### Lab Interface (`/courses/:id/labs`)
```tsx
// Lab list
data-testid="lab-card-{id}"  // Dynamic with lab ID
data-testid="launch-lab-button"

// Lab environment
data-testid="lab-environment"
data-testid="code-editor"
data-testid="terminal"
data-testid="terminal-output"
data-testid="file-explorer"
data-testid="run-code-button"
data-testid="reset-lab-button"
data-testid="submit-lab-button"

// Lab instructions
data-testid="lab-instructions"
data-testid="lab-objectives"
data-testid="lab-hints"
```

### 7. Progress and Analytics Components

#### Student Progress (`/courses/:id/progress`)
```tsx
data-testid="progress-bar"
data-testid="completion-percentage"
data-testid="module-list"
data-testid="module-{id}"  // Dynamic with module ID
data-testid="course-complete-badge"
data-testid="time-spent"
data-testid="last-accessed"
```

#### Certificate Page (`/courses/:id/certificate`)
```tsx
data-testid="certificate"
data-testid="certificate-student-name"
data-testid="certificate-course-name"
data-testid="certificate-date"
data-testid="download-certificate-button"
data-testid="share-certificate-button"
```

#### Analytics Dashboard (`/courses/:id/analytics`)
```tsx
data-testid="analytics-dashboard"
data-testid="enrollment-stats"
data-testid="completion-rate"
data-testid="quiz-performance"
data-testid="student-progress-link"
data-testid="student-detail-view"
data-testid="performance-chart"
```

### 8. Student Management Components

#### Student List (`/courses/:id/students`)
```tsx
data-testid="student-list"
data-testid="student-row-{id}"  // Dynamic with student ID
data-testid="enroll-student-button"
data-testid="student-search-input"
data-testid="student-option-{email}"  // Dynamic
data-testid="confirm-enroll-button"
data-testid="remove-student-button"
data-testid="view-student-progress-button"
```

### 9. Discussion/Forum Components

#### Discussion Board (`/courses/:id/discussions`)
```tsx
data-testid="discussion-board"
data-testid="discussion-thread"
data-testid="thread-{id}"  // Dynamic with thread ID
data-testid="create-thread-button"
data-testid="reply-input"
data-testid="post-reply-button"
data-testid="edit-post-button"
data-testid="delete-post-button"
```

### 10. Organization Management Components

#### Organization Settings (`/organizations/:id/settings`)
```tsx
data-testid="org-name-input"
data-testid="org-description-input"
data-testid="org-domain-input"
data-testid="save-settings-button"
data-testid="cancel-button"
```

#### User Management (`/organizations/:id/users`)
```tsx
data-testid="user-list"
data-testid="add-user-button"
data-testid="user-email-input"
data-testid="user-role-select"
data-testid="add-user-submit"
data-testid="remove-user-button"
data-testid="edit-user-role-button"
```

#### Track Management (`/organizations/:id/tracks`)
```tsx
data-testid="track-list"
data-testid="create-track-button"
data-testid="track-name-input"
data-testid="track-description-input"
data-testid="create-track-submit"
data-testid="add-course-to-track"
data-testid="remove-course-from-track"
```

### 11. Site Admin Components

#### Organization Management (`/admin/organizations`)
```tsx
data-testid="organization-list"
data-testid="create-organization-button"
data-testid="org-card-{id}"  // Dynamic with org ID
data-testid="view-org-details"
data-testid="edit-org-button"
data-testid="delete-org-button"
```

#### System Settings (`/admin/settings`)
```tsx
data-testid="system-settings-form"
data-testid="max-organizations-input"
data-testid="max-users-per-org-input"
data-testid="enable-self-registration-checkbox"
data-testid="save-system-settings-button"
```

### 12. Common UI Components

#### Loading States
```tsx
data-testid="loading-spinner"
data-testid="skeleton-loader"
data-testid="progress-indicator"
```

#### Toast Notifications
```tsx
data-testid="toast-message"
data-testid="toast-success"
data-testid="toast-error"
data-testid="toast-warning"
data-testid="toast-info"
data-testid="toast-close-button"
```

#### Modals
```tsx
data-testid="modal-overlay"
data-testid="modal-content"
data-testid="modal-title"
data-testid="modal-body"
data-testid="modal-footer"
data-testid="modal-close-button"
data-testid="modal-confirm-button"
data-testid="modal-cancel-button"
```

#### Confirmation Dialogs
```tsx
data-testid="confirmation-dialog"
data-testid="confirmation-message"
data-testid="confirm-action-button"
data-testid="cancel-action-button"
```

## Implementation Guidelines

### 1. Add to All Interactive Elements
Every interactive element (buttons, inputs, links) should have a data-testid.

### 2. Add to Key Information Display Elements
Important information displays (user names, course titles, progress indicators) should have data-testids.

### 3. Dynamic IDs for Lists
For lists and collections, use dynamic IDs with the item's unique identifier:
```tsx
{courses.map(course => (
  <div key={course.id} data-testid={`course-card-${course.id}`}>
    <h3 data-testid="course-title">{course.name}</h3>
  </div>
))}
```

### 4. Consistent Naming
Use consistent naming patterns across similar components:
- Buttons: `-button` suffix
- Inputs: `-input` suffix
- Selects: `-select` suffix
- Links: `-link` suffix
- Modals: `-modal` suffix
- Cards: `-card` suffix

### 5. Avoid Over-Specification
Don't add data-testids to every div or span. Focus on:
- Interactive elements
- Key information displays
- Navigation elements
- Form elements
- Error/success messages

## Testing Priority

### Priority 0 (Must Have)
- Authentication components
- Course enrollment
- Course content viewing
- Quiz taking
- Lab environment

### Priority 1 (High Priority)
- Course creation
- Content generation
- Student management
- Progress tracking

### Priority 2 (Medium Priority)
- Analytics
- Organization management
- Discussion forums
- Certificate generation

### Priority 3 (Nice to Have)
- Advanced settings
- Admin panels
- System configuration

## Validation

To ensure all required data-testids are implemented:

1. Run E2E tests and check for missing selectors
2. Use Cypress Studio to identify missing elements
3. Review test failures for selector issues
4. Validate naming consistency across components

## Component Implementation Example

```tsx
/**
 * Example: Login Form Component
 */
export const LoginForm: React.FC = () => {
  return (
    <form data-testid="login-form" onSubmit={handleSubmit}>
      <input
        data-testid="username-input"
        type="text"
        name="username"
        placeholder="Username"
        required
      />
      <input
        data-testid="password-input"
        type="password"
        name="password"
        placeholder="Password"
        required
      />
      <button data-testid="login-button" type="submit">
        Login
      </button>
      {error && (
        <div data-testid="error-message" role="alert">
          {error}
        </div>
      )}
    </form>
  );
};
```

## Notes

- These data-testids are specifically for E2E testing and should not be used for styling
- Keep data-testids in sync with test files when refactoring
- Document any new data-testids as components are added
- Use TypeScript constants for data-testid values to avoid typos

## References

- [Cypress Best Practices](https://docs.cypress.io/guides/references/best-practices)
- [Testing Library: Priority](https://testing-library.com/docs/queries/about/#priority)
- [Page Object Model Pattern](https://martinfowler.com/bliki/PageObject.html)
