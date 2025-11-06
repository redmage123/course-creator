# React Integration Tests

## Overview

This directory contains integration tests for the Course Creator Platform React application. Integration tests validate how components, services, state management, and navigation work together to deliver complete user workflows.

## Directory Structure

```
integration/
├── auth/                              # Authentication workflows (41 tests)
│   ├── LoginFlow.integration.test.tsx
│   ├── RegistrationFlow.integration.test.tsx
│   ├── PasswordResetFlow.integration.test.tsx
│   └── AuthStateManagement.integration.test.tsx
├── courses/                           # Course management workflows (18 tests)
│   ├── CourseCreationFlow.integration.test.tsx
│   └── CourseEnrollmentFlow.integration.test.tsx
├── dashboard/                         # Dashboard integration tests (TODO)
│   ├── StudentDashboardIntegration.test.tsx
│   ├── InstructorDashboardIntegration.test.tsx
│   ├── OrgAdminDashboardIntegration.test.tsx
│   └── SiteAdminDashboardIntegration.test.tsx
├── enrollment/                        # Enrollment workflows (TODO)
│   ├── BulkEnrollmentFlow.integration.test.tsx
│   ├── StudentManagementFlow.integration.test.tsx
│   └── EnrollmentValidation.integration.test.tsx
└── navigation/                        # Navigation and routing (10 tests)
    ├── ProtectedRouteIntegration.test.tsx
    ├── RoleBasedNavigationIntegration.test.tsx (TODO)
    └── DashboardLayoutIntegration.test.tsx (TODO)
```

## Running Tests

### Run All Integration Tests
```bash
npm run test:integration
```

### Run Specific Category
```bash
# Auth integration tests
npm run test src/test/integration/auth

# Course integration tests
npm run test src/test/integration/courses

# Navigation integration tests
npm run test src/test/integration/navigation
```

### Run Single Test File
```bash
npm run test src/test/integration/auth/LoginFlow.integration.test.tsx
```

### Run in Watch Mode (TDD)
```bash
npm run test:watch src/test/integration
```

### Run with Coverage
```bash
npm run test:coverage
```

## Test Structure

Each integration test follows this structure:

```typescript
/**
 * [Feature] Integration Tests
 *
 * BUSINESS CONTEXT:
 * Explains why this workflow matters to the business
 *
 * TECHNICAL IMPLEMENTATION:
 * Describes how components integrate together
 *
 * INTEGRATION SCOPE:
 * Lists what's being tested (Component A + Service B + State C)
 */

describe('[Feature] Integration Tests', () => {
  const user = setupUserEvent();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should complete [specific workflow]', async () => {
    /**
     * INTEGRATION TEST: [Test Name]
     *
     * SIMULATES:
     * 1. Step 1 of user journey
     * 2. Step 2 of user journey
     * 3. Step 3 of user journey
     * ...
     */

    // Arrange - Setup initial state and mocks
    const mockResponse = {...};
    vi.mocked(service.method).mockResolvedValue(mockResponse);

    // Act - Simulate user interactions
    await user.type(input, 'value');
    await user.click(button);

    // Assert - Verify expected outcomes
    expect(service.method).toHaveBeenCalledWith(...);
    expect(store.getState().feature).toBe(...);
  });
});
```

## Test Utilities

All integration tests use custom utilities from `../utils.tsx`:

### renderWithProviders()
Renders components with Redux, Router, and Query Client:
```typescript
const { store } = renderWithProviders(<Component />, {
  preloadedState: { auth: {...} },
  initialEntries: ['/dashboard']
});
```

### setupUserEvent()
Provides realistic user interactions:
```typescript
const user = setupUserEvent();
await user.type(input, 'text');
await user.click(button);
```

### createMockUser()
Generates realistic user profiles:
```typescript
const mockUser = createMockUser({
  role: 'instructor',
  id: 'instructor-123'
});
```

### createMockAuthState()
Generates authentication state:
```typescript
const authState = createMockAuthState({
  role: 'student',
  userId: 'student-123'
});
```

## Integration Test Categories

### Authentication (4 files, 41 tests)
- **LoginFlow**: Login workflows for all 4 roles
- **RegistrationFlow**: User registration with auto-login
- **PasswordResetFlow**: Two-step password reset process
- **AuthStateManagement**: Redux state and localStorage sync

### Course Management (2 files, 18 tests)
- **CourseCreationFlow**: Multi-step course creation wizard
- **CourseEnrollmentFlow**: Student enrollment workflows

### Navigation (1 file, 10 tests)
- **ProtectedRouteIntegration**: RBAC and authentication enforcement

## What Integration Tests Cover

### ✅ Multi-Component Interactions
Tests how components work together to complete user workflows

### ✅ Service Integration
Mocks API calls but tests real service layer logic

### ✅ State Management
Validates Redux state propagation across components

### ✅ Navigation
Tests React Router navigation and protected routes

### ✅ Form Workflows
Tests complete form submission flows with validation

### ✅ Error Handling
Tests error propagation from API → Service → Component → UI

### ✅ Loading States
Tests loading indicators and disabled states during async operations

### ✅ User Scenarios
Tests actual user workflows from start to finish

## What Integration Tests DON'T Cover

### ❌ Unit-Level Logic
Use unit tests for testing individual functions/components in isolation

### ❌ Real API Calls
API calls are mocked - use E2E tests for real backend integration

### ❌ Browser-Specific Behavior
Use E2E tests with real browsers for browser-specific features

### ❌ Visual Regression
Use visual regression tools (e.g., Percy, Chromatic) for UI changes

### ❌ Performance Testing
Use dedicated performance tools (e.g., Lighthouse) for performance metrics

## Best Practices

### 1. Test User Workflows, Not Implementation Details
```typescript
// ✅ Good - Tests user workflow
it('should complete login and redirect to dashboard', async () => {
  await user.type(emailInput, 'user@example.com');
  await user.click(submitButton);
  expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
});

// ❌ Bad - Tests implementation details
it('should call setState with correct value', async () => {
  expect(component.state.value).toBe('expected');
});
```

### 2. Mock External Dependencies, Test Integration Logic
```typescript
// Mock API calls
vi.mock('@services/authService', () => ({
  authService: {
    login: vi.fn(),
  },
}));

// But test real service integration
const result = await authService.login(credentials);
expect(store.getState().auth.isAuthenticated).toBe(true);
```

### 3. Use Descriptive Test Names
```typescript
// ✅ Good - Clear what's being tested
it('should redirect unauthenticated user to login', async () => {});

// ❌ Bad - Vague test name
it('should work', async () => {});
```

### 4. Document Complex Workflows
```typescript
it('should complete enrollment workflow', async () => {
  /**
   * SIMULATES:
   * 1. Instructor searches for students
   * 2. Selects multiple students
   * 3. Submits enrollment form
   * 4. API enrolls students in course
   * 5. Success message is displayed
   */
  // Test implementation...
});
```

### 5. Test Both Happy and Error Paths
```typescript
// Happy path
it('should complete successful login', async () => {});

// Error path
it('should display error message on login failure', async () => {});
```

## Common Patterns

### Testing Async Operations
```typescript
it('should handle async API call', async () => {
  await user.click(submitButton);

  await waitFor(() => {
    expect(service.method).toHaveBeenCalled();
  });

  expect(screen.getByText('Success')).toBeInTheDocument();
});
```

### Testing Loading States
```typescript
it('should show loading state', async () => {
  // Mock slow API
  vi.mocked(service.method).mockImplementation(
    () => new Promise(resolve => setTimeout(resolve, 100))
  );

  await user.click(submitButton);

  expect(screen.getByText('Loading...')).toBeInTheDocument();
  expect(submitButton).toBeDisabled();

  await waitFor(() => {
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
  });
});
```

### Testing Navigation
```typescript
it('should navigate after success', async () => {
  const mockNavigate = vi.fn();
  // Setup...

  await user.click(submitButton);

  await waitFor(() => {
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });
});
```

### Testing Redux State
```typescript
it('should update Redux state', async () => {
  const { store } = renderWithProviders(<Component />);

  await user.click(button);

  const state = store.getState();
  expect(state.feature.value).toBe('expected');
});
```

## Troubleshooting

### Test Fails: "Element not found"
- Use `await waitFor()` for async operations
- Check if element is conditionally rendered
- Verify test data matches component expectations

### Test Fails: "API method not called"
- Ensure mock is setup before component render
- Check if form validation prevents submission
- Verify button is not disabled

### Test Fails: "State not updated"
- Ensure actions are dispatched
- Check if reducer logic is correct
- Verify preloaded state is correct

### Test Fails: "Navigation not called"
- Ensure navigation logic is not prevented
- Check if error prevents navigation
- Verify mock navigate function is setup

## Resources

- **Test Utilities Documentation**: `../utils.tsx`
- **Comprehensive Summary**: `/docs/INTEGRATION_TEST_SUITE_SUMMARY.md`
- **Vitest Documentation**: https://vitest.dev/
- **React Testing Library**: https://testing-library.com/react
- **User Event Documentation**: https://testing-library.com/docs/user-event/intro

## Contributing

When adding new integration tests:

1. Follow the established directory structure
2. Use consistent test naming conventions
3. Include comprehensive documentation (BUSINESS CONTEXT, SIMULATES, etc.)
4. Test both happy and error paths
5. Use the provided test utilities
6. Update this README if adding new categories

---

**Total Integration Tests**: 69+ tests
**Test Coverage**: 80%+ of critical workflows
**Execution Time**: ~15-30 seconds for full suite
**Last Updated**: November 5, 2025
