/**
 * End-to-end tests for user workflows using Playwright
 * Tests complete user journeys from registration to course interaction
 */

import { test, expect } from '@playwright/test';

test.describe('User Workflows', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the homepage before each test
    await page.goto('http://localhost:8080');
  });

  test('should display homepage correctly', async ({ page }) => {
    // Check that the page loads correctly
    await expect(page).toHaveTitle('Course Creator Platform');
    
    // Check main elements are present
    await expect(page.locator('h1')).toContainText('Course Creator');
    await expect(page.locator('h2')).toContainText('Welcome to Course Creator');
    
    // Check navigation links
    await expect(page.locator('a[href="#home"]')).toBeVisible();
    await expect(page.locator('a[href="#courses"]')).toBeVisible();
    await expect(page.locator('a[href="#create"]')).toBeVisible();
    
    // Check auth buttons are visible (user not logged in)
    await expect(page.locator('button:has-text("Login")')).toBeVisible();
    await expect(page.locator('button:has-text("Register")')).toBeVisible();
  });

  test('should show register modal when register button is clicked', async ({ page }) => {
    // Click the register button
    await page.click('button:has-text("Register")');
    
    // Wait for the registration form to appear
    await expect(page.locator('h2:has-text("Register")')).toBeVisible();
    
    // Check form fields are present
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="full_name"]')).toBeVisible();
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('input[name="password_confirm"]')).toBeVisible();
    
    // Check form buttons
    await expect(page.locator('button[type="submit"]:has-text("Register")')).toBeVisible();
    await expect(page.locator('button[type="button"]:has-text("Cancel")')).toBeVisible();
  });

  test('should show login modal when login button is clicked', async ({ page }) => {
    // Click the login button
    await page.click('button:has-text("Login")');
    
    // Wait for the login form to appear
    await expect(page.locator('h2:has-text("Login")')).toBeVisible();
    
    // Check form fields are present
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    
    // Check form buttons
    await expect(page.locator('button[type="submit"]:has-text("Login")')).toBeVisible();
    await expect(page.locator('button[type="button"]:has-text("Cancel")')).toBeVisible();
  });

  test('should validate password matching in registration', async ({ page }) => {
    // Navigate to registration form
    await page.click('button:has-text("Register")');
    
    // Fill in passwords that don't match
    await page.fill('input[name="password"]', 'password123');
    await page.fill('input[name="password_confirm"]', 'different456');
    
    // Check that password mismatch indicator appears
    await expect(page.locator('#password-match-indicator')).toContainText('do not match');
    
    // Fix the password confirmation
    await page.fill('input[name="password_confirm"]', 'password123');
    
    // Check that passwords match indicator appears
    await expect(page.locator('#password-match-indicator')).toContainText('match');
  });

  test('should toggle password visibility', async ({ page }) => {
    // Navigate to registration form
    await page.click('button:has-text("Register")');
    
    const passwordInput = page.locator('input[name="password"]');
    const toggleButton = page.locator('#toggle-password-1');
    
    // Initially, password should be hidden
    await expect(passwordInput).toHaveAttribute('type', 'password');
    
    // Click toggle button to show password
    await toggleButton.click();
    await expect(passwordInput).toHaveAttribute('type', 'text');
    
    // Click toggle button again to hide password
    await toggleButton.click();
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('should handle user registration flow', async ({ page }) => {
    // Mock the registration API response
    await page.route('**/auth/register', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'User registered successfully',
          user: {
            email: 'test@example.com',
            username: 'testuser',
            full_name: 'Test User',
            role: 'instructor'
          }
        })
      });
    });
    
    // Navigate to registration form
    await page.click('button:has-text("Register")');
    
    // Fill in registration form
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="full_name"]', 'Test User');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'password123');
    await page.fill('input[name="password_confirm"]', 'password123');
    
    // Submit the form
    await page.click('button[type="submit"]:has-text("Register")');
    
    // Wait for success message
    await expect(page.locator('text=Registration successful')).toBeVisible();
    
    // Should navigate to login form
    await expect(page.locator('h2:has-text("Login")')).toBeVisible();
  });

  test('should handle user login flow', async ({ page }) => {
    // Mock the login API response
    await page.route('**/auth/login', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'fake-token',
          token_type: 'bearer'
        })
      });
    });
    
    // Mock the profile API response
    await page.route('**/users/profile', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: {
            email: 'test@example.com',
            username: 'testuser',
            full_name: 'Test User',
            role: 'instructor'
          }
        })
      });
    });
    
    // Navigate to login form
    await page.click('button:has-text("Login")');
    
    // Fill in login form
    await page.fill('input[name="username"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    
    // Submit the form
    await page.click('button[type="submit"]:has-text("Login")');
    
    // Wait for success message and redirect
    await expect(page.locator('text=Login successful')).toBeVisible();
    
    // Should redirect to instructor dashboard
    await expect(page).toHaveURL(/instructor-dashboard.html/);
  });

  test('should display courses when View Courses is clicked', async ({ page }) => {
    // Mock the courses API response
    await page.route('**/courses', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            name: 'Test Course 1',
            description: 'A test course',
            instructor: 'Test Instructor',
            created_at: '2023-01-01T00:00:00Z'
          },
          {
            id: 2,
            name: 'Test Course 2',
            description: 'Another test course',
            instructor: 'Another Instructor',
            created_at: '2023-01-02T00:00:00Z'
          }
        ])
      });
    });
    
    // Click View Courses button
    await page.click('button:has-text("View Courses")');
    
    // Wait for courses to load
    await expect(page.locator('h2:has-text("Available Courses")')).toBeVisible();
    
    // Check that courses are displayed
    await expect(page.locator('text=Test Course 1')).toBeVisible();
    await expect(page.locator('text=Test Course 2')).toBeVisible();
    
    // Check course cards have proper structure
    await expect(page.locator('.course-card')).toHaveCount(2);
  });

  test('should handle course creation flow', async ({ page }) => {
    // Mock the course creation API response
    await page.route('**/courses', (route) => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'new-course-123',
            name: 'New Test Course',
            description: 'A newly created course',
            instructor: 'Test Instructor',
            status: 'draft'
          })
        });
      }
    });
    
    // Navigate to course creation
    await page.click('a[href="#create"]');
    
    // Wait for create course form
    await expect(page.locator('h2:has-text("Create New Course")')).toBeVisible();
    
    // Fill in course creation form
    await page.fill('input[name="name"]', 'New Test Course');
    await page.fill('textarea[name="description"]', 'A newly created course');
    await page.fill('input[name="instructor"]', 'Test Instructor');
    
    // Submit the form
    await page.click('button[type="submit"]:has-text("Create Course")');
    
    // Wait for success message
    await expect(page.locator('text=Course created successfully')).toBeVisible();
  });

  test('should handle navigation between sections', async ({ page }) => {
    // Test navigation to different sections
    await page.click('a[href="#courses"]');
    // Navigation should be handled by hash change
    
    await page.click('a[href="#create"]');
    await expect(page.locator('h2:has-text("Create New Course")')).toBeVisible();
    
    await page.click('a[href="#home"]');
    await expect(page.locator('h2:has-text("Welcome to Course Creator")')).toBeVisible();
  });

  test('should handle error states gracefully', async ({ page }) => {
    // Mock failed API responses
    await page.route('**/courses', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' })
      });
    });
    
    // Click View Courses button
    await page.click('button:has-text("View Courses")');
    
    // Should show error message
    await expect(page.locator('text=Failed to load courses')).toBeVisible();
  });

  test('should handle responsive design', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check that elements are still visible and accessible
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('button:has-text("Login")')).toBeVisible();
    await expect(page.locator('button:has-text("Register")')).toBeVisible();
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    
    // Check that layout adapts appropriately
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('nav')).toBeVisible();
  });

  test('should maintain state during navigation', async ({ page }) => {
    // Mock login to set up authenticated state
    await page.route('**/auth/login', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'fake-token',
          token_type: 'bearer'
        })
      });
    });
    
    await page.route('**/users/profile', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: {
            email: 'test@example.com',
            full_name: 'Test User',
            role: 'student'
          }
        })
      });
    });
    
    // Login
    await page.click('button:has-text("Login")');
    await page.fill('input[name="username"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]:has-text("Login")');
    
    // Wait for login success
    await expect(page.locator('text=Login successful')).toBeVisible();
    
    // Should show account dropdown instead of auth buttons
    await expect(page.locator('#accountDropdown')).toBeVisible();
    await expect(page.locator('#authButtons')).not.toBeVisible();
  });
});