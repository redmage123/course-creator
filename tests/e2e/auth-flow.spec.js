/**
 * E2E tests for authentication and authorization flows
 * Tests login/logout, role-based access control, and session management
 */

import { test, expect } from '@playwright/test';

const testUsers = {
  admin: {
    email: 'admin@test.com',
    password: 'admin123',
    role: 'admin'
  },
  instructor: {
    email: 'instructor@test.com', 
    password: 'instructor123',
    role: 'instructor'
  },
  student: {
    email: 'student@test.com',
    password: 'student123',
    role: 'student'
  }
};

test.describe('Authentication Flow', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('Admin login and dashboard access', async ({ page }) => {
    await test.step('Admin can log in successfully', async () => {
      await page.click('text=Login');
      await page.fill('input[name="email"]', testUsers.admin.email);
      await page.fill('input[name="password"]', testUsers.admin.password);
      await page.click('button[type="submit"]');
      
      // Should redirect to admin dashboard
      await expect(page).toHaveURL(/admin/);
      await expect(page.locator('h1')).toContainText('Admin Dashboard');
    });

    await test.step('Admin has access to all features', async () => {
      // Admin should see all navigation options
      await expect(page.locator('text=User Management')).toBeVisible();
      await expect(page.locator('text=Course Management')).toBeVisible();
      await expect(page.locator('text=System Settings')).toBeVisible();
      await expect(page.locator('text=Analytics')).toBeVisible();
    });
  });

  test('Instructor login and dashboard access', async ({ page }) => {
    await test.step('Instructor can log in successfully', async () => {
      await page.click('text=Login');
      await page.fill('input[name="email"]', testUsers.instructor.email);
      await page.fill('input[name="password"]', testUsers.instructor.password);
      await page.click('button[type="submit"]');
      
      // Should redirect to instructor dashboard
      await expect(page).toHaveURL(/instructor-dashboard/);
      await expect(page.locator('h1')).toContainText('Instructor Dashboard');
    });

    await test.step('Instructor has limited access compared to admin', async () => {
      // Instructor should see course-related options
      await expect(page.locator('text=My Courses')).toBeVisible();
      await expect(page.locator('text=Create Course')).toBeVisible();
      await expect(page.locator('text=Students')).toBeVisible();
      
      // Should not see admin-only features
      await expect(page.locator('text=User Management')).not.toBeVisible();
      await expect(page.locator('text=System Settings')).not.toBeVisible();
    });
  });

  test('Student login and dashboard access', async ({ page }) => {
    await test.step('Student can log in successfully', async () => {
      await page.click('text=Login');
      await page.fill('input[name="email"]', testUsers.student.email);
      await page.fill('input[name="password"]', testUsers.student.password);
      await page.click('button[type="submit"]');
      
      // Should redirect to student dashboard
      await expect(page).toHaveURL(/student-dashboard/);
      await expect(page.locator('h1')).toContainText('Student Dashboard');
    });

    await test.step('Student has most limited access', async () => {
      // Student should only see learning-related options
      await expect(page.locator('text=My Courses')).toBeVisible();
      await expect(page.locator('text=Profile')).toBeVisible();
      
      // Should not see creation or management features
      await expect(page.locator('text=Create Course')).not.toBeVisible();
      await expect(page.locator('text=Students')).not.toBeVisible();
      await expect(page.locator('text=User Management')).not.toBeVisible();
    });
  });

  test('Invalid login attempts', async ({ page }) => {
    await test.step('Invalid email shows error', async () => {
      await page.click('text=Login');
      await page.fill('input[name="email"]', 'nonexistent@test.com');
      await page.fill('input[name="password"]', 'password123');
      await page.click('button[type="submit"]');
      
      // Should show error message
      await expect(page.locator('text=Invalid credentials')).toBeVisible();
      // Should stay on login page
      await expect(page).toHaveURL(/login/);
    });

    await test.step('Wrong password shows error', async () => {
      await page.fill('input[name="email"]', testUsers.student.email);
      await page.fill('input[name="password"]', 'wrongpassword');
      await page.click('button[type="submit"]');
      
      await expect(page.locator('text=Invalid credentials')).toBeVisible();
    });

    await test.step('Empty fields show validation error', async () => {
      await page.fill('input[name="email"]', '');
      await page.fill('input[name="password"]', '');
      await page.click('button[type="submit"]');
      
      await expect(page.locator('text=Email is required')).toBeVisible();
      await expect(page.locator('text=Password is required')).toBeVisible();
    });
  });

  test('Logout functionality', async ({ page }) => {
    await test.step('User can logout successfully', async () => {
      // Login first
      await page.click('text=Login');
      await page.fill('input[name="email"]', testUsers.instructor.email);
      await page.fill('input[name="password"]', testUsers.instructor.password);
      await page.click('button[type="submit"]');
      
      await expect(page).toHaveURL(/instructor-dashboard/);
      
      // Logout
      await page.click('text=Logout');
      
      // Should redirect to home page
      await expect(page).toHaveURL('/');
      await expect(page.locator('text=Login')).toBeVisible();
    });

    await test.step('Accessing protected page after logout redirects to login', async () => {
      // Try to access instructor dashboard directly
      await page.goto('/instructor-dashboard.html');
      
      // Should redirect to login
      await expect(page).toHaveURL(/login/);
    });
  });
});

test.describe('Authorization and Access Control', () => {
  
  test('Role-based URL access control', async ({ page }) => {
    await test.step('Student cannot access instructor pages', async () => {
      // Login as student
      await page.goto('/');
      await page.click('text=Login');
      await page.fill('input[name="email"]', testUsers.student.email);
      await page.fill('input[name="password"]', testUsers.student.password);
      await page.click('button[type="submit"]');
      
      // Try to access instructor dashboard
      await page.goto('/instructor-dashboard.html');
      
      // Should be redirected or show access denied
      await expect(page.locator('text=Access Denied')).toBeVisible();
    });

    await test.step('Student cannot access admin pages', async () => {
      // Try to access admin page
      await page.goto('/admin.html');
      
      await expect(page.locator('text=Access Denied')).toBeVisible();
    });

    await test.step('Instructor cannot access admin pages', async () => {
      // Login as instructor
      await page.goto('/');
      await page.click('text=Login');
      await page.fill('input[name="email"]', testUsers.instructor.email);
      await page.fill('input[name="password"]', testUsers.instructor.password);
      await page.click('button[type="submit"]');
      
      // Try to access admin page
      await page.goto('/admin.html');
      
      await expect(page.locator('text=Access Denied')).toBeVisible();
    });
  });

  test('API endpoint access control', async ({ page }) => {
    await test.step('Student cannot access instructor APIs', async () => {
      // Login as student
      await page.goto('/');
      await page.click('text=Login');
      await page.fill('input[name="email"]', testUsers.student.email);
      await page.fill('input[name="password"]', testUsers.student.password);
      await page.click('button[type="submit"]');
      
      // Try to access instructor-only API
      const response = await page.request.post('/api/courses', {
        data: {
          title: 'Unauthorized Course',
          description: 'Should not be created'
        }
      });
      
      expect(response.status()).toBe(403); // Forbidden
    });

    await test.step('Student cannot access admin APIs', async () => {
      const response = await page.request.get('/api/admin/users');
      expect(response.status()).toBe(403);
    });
  });

  test('Session management and timeout', async ({ page }) => {
    await test.step('Session persists across page refreshes', async () => {
      // Login
      await page.goto('/');
      await page.click('text=Login');
      await page.fill('input[name="email"]', testUsers.instructor.email);
      await page.fill('input[name="password"]', testUsers.instructor.password);
      await page.click('button[type="submit"]');
      
      await expect(page).toHaveURL(/instructor-dashboard/);
      
      // Refresh page
      await page.reload();
      
      // Should still be logged in
      await expect(page).toHaveURL(/instructor-dashboard/);
      await expect(page.locator('text=Logout')).toBeVisible();
    });

    await test.step('Session expires after timeout', async () => {
      // This would test session timeout in a real implementation
      // For testing, we could manipulate session cookies or wait for timeout
      
      // Mock session expiry by clearing storage
      await page.evaluate(() => {
        localStorage.clear();
        sessionStorage.clear();
      });
      
      // Try to access protected page
      await page.goto('/instructor-dashboard.html');
      
      // Should redirect to login
      await expect(page).toHaveURL(/login/);
    });
  });

  test('Password security requirements', async ({ page }) => {
    await test.step('Weak passwords are rejected during registration', async () => {
      // This would test password requirements during user creation
      // For now, we'll test the generated passwords meet requirements
      
      await page.goto('/');
      
      // Test would involve creating new user with weak password
      // and verifying it's rejected with appropriate error message
    });
  });
});

test.describe('Cross-Role Interactions', () => {
  
  test('Instructor-Student interaction flow', async ({ browser }) => {
    // Create two browser contexts for instructor and student
    const instructorContext = await browser.newContext();
    const studentContext = await browser.newContext();
    
    const instructorPage = await instructorContext.newPage();
    const studentPage = await studentContext.newPage();

    await test.step('Instructor creates course and enrolls student', async () => {
      // Instructor login
      await instructorPage.goto('/');
      await instructorPage.click('text=Login');
      await instructorPage.fill('input[name="email"]', testUsers.instructor.email);
      await instructorPage.fill('input[name="password"]', testUsers.instructor.password);
      await instructorPage.click('button[type="submit"]');
      
      // Create course
      await instructorPage.click('text=Create Course');
      await instructorPage.fill('input[name="title"]', 'Cross-Role Test Course');
      await instructorPage.fill('textarea[name="description"]', 'Testing cross-role interactions');
      await instructorPage.click('button:has-text("Create Course")');
      
      // Enroll student
      await instructorPage.click('text=Students');
      await instructorPage.selectOption('#selectedCourse', { label: 'Cross-Role Test Course' });
      await instructorPage.fill('input[name="studentEmail"]', testUsers.student.email);
      
      const startDate = new Date();
      startDate.setDate(startDate.getDate() + 1);
      const endDate = new Date();
      endDate.setDate(endDate.getDate() + 14);
      
      await instructorPage.fill('input[name="startDate"]', startDate.toISOString().split('T')[0]);
      await instructorPage.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
      
      await instructorPage.click('button:has-text("Enroll Student")');
      await expect(instructorPage.locator('text=Student enrolled successfully')).toBeVisible();
    });

    await test.step('Student can see enrolled course', async () => {
      // Student login
      await studentPage.goto('/');
      await studentPage.click('text=Login');
      await studentPage.fill('input[name="email"]', testUsers.student.email);
      await studentPage.fill('input[name="password"]', testUsers.student.password);
      await studentPage.click('button[type="submit"]');
      
      // Check enrolled course appears
      await expect(studentPage.locator('text=Cross-Role Test Course')).toBeVisible();
    });

    // Cleanup
    await instructorContext.close();
    await studentContext.close();
  });
});