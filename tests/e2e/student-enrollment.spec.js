/**
 * E2E tests for student enrollment workflow
 * Tests the complete flow from instructor enrolling students to student login and access
 */

import { test, expect } from '@playwright/test';

// Test data
const testInstructor = {
  email: 'instructor@test.com',
  password: 'instructor123',
  name: 'Dr. Test Instructor'
};

const testStudent = {
  email: 'student@test.com',
  name: 'Test Student'
};

const testCourse = {
  title: 'E2E Test Course',
  description: 'A course created for E2E testing',
  category: 'Programming',
  difficulty: 'beginner'
};

test.describe('Student Enrollment Workflow', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    await expect(page).toHaveTitle(/Course Creator/);
  });

  test('Complete instructor enrolls student workflow', async ({ page }) => {
    // Step 1: Instructor Login
    await test.step('Instructor logs in', async () => {
      await page.click('text=Login');
      await page.fill('input[name="email"]', testInstructor.email);
      await page.fill('input[name="password"]', testInstructor.password);
      await page.click('button[type="submit"]');
      
      // Wait for redirect to instructor dashboard
      await expect(page).toHaveURL(/instructor-dashboard/);
      await expect(page.locator('h1')).toContainText('Instructor Dashboard');
    });

    // Step 2: Create a new course
    await test.step('Instructor creates a new course', async () => {
      await page.click('text=Create Course');
      
      // Fill course creation form
      await page.fill('input[name="title"]', testCourse.title);
      await page.fill('textarea[name="description"]', testCourse.description);
      await page.selectOption('select[name="category"]', testCourse.category);
      await page.selectOption('select[name="difficulty"]', testCourse.difficulty);
      
      // Submit course creation
      await page.click('button:has-text("Create Course")');
      
      // Verify course was created
      await expect(page.locator('text=' + testCourse.title)).toBeVisible();
    });

    // Step 3: Navigate to Students section and enroll student
    await test.step('Instructor enrolls a student', async () => {
      await page.click('text=Students');
      
      // Wait for students section to load
      await expect(page.locator('#students-section')).toBeVisible();
      
      // Select the course for enrollment
      await page.selectOption('#selectedCourse', { label: testCourse.title });
      
      // Fill student email
      await page.fill('input[name="studentEmail"]', testStudent.email);
      
      // Set course instance dates
      const startDate = new Date();
      startDate.setDate(startDate.getDate() + 1); // Tomorrow
      const endDate = new Date();
      endDate.setDate(endDate.getDate() + 14); // Two weeks from now
      
      await page.fill('input[name="startDate"]', startDate.toISOString().split('T')[0]);
      await page.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
      
      // Submit enrollment
      await page.click('button:has-text("Enroll Student")');
      
      // Verify enrollment success message
      await expect(page.locator('text=Student enrolled successfully')).toBeVisible();
    });

    // Step 4: Verify enrollment in the system
    await test.step('Verify student appears in enrolled list', async () => {
      // Check if student appears in the enrolled students list
      await expect(page.locator(`text=${testStudent.email}`)).toBeVisible();
    });
  });

  test('Student login with generated credentials', async ({ page, context }) => {
    // This test simulates receiving the email with credentials
    // In a real scenario, we'd extract credentials from email service
    const generatedPassword = 'TestPass123!'; // Mock generated password
    
    await test.step('Student attempts login with generated credentials', async () => {
      await page.click('text=Login');
      await page.fill('input[name="email"]', testStudent.email);
      await page.fill('input[name="password"]', generatedPassword);
      await page.click('button[type="submit"]');
      
      // Verify redirect to student dashboard
      await expect(page).toHaveURL(/student-dashboard/);
      await expect(page.locator('h1')).toContainText('Student Dashboard');
    });

    await test.step('Student can see enrolled courses', async () => {
      // Verify student can see their enrolled course
      await expect(page.locator(`text=${testCourse.title}`)).toBeVisible();
    });

    await test.step('Student has limited permissions', async () => {
      // Verify student cannot access instructor features
      await expect(page.locator('text=Create Course')).not.toBeVisible();
      await expect(page.locator('text=Students')).not.toBeVisible();
      
      // Verify student can only see student-relevant navigation
      await expect(page.locator('text=My Courses')).toBeVisible();
      await expect(page.locator('text=Profile')).toBeVisible();
    });
  });

  test('Student access control based on course dates', async ({ page }) => {
    // Test that students cannot access course content before start date
    await test.step('Student cannot access course before start date', async () => {
      // Login as student
      await page.click('text=Login');
      await page.fill('input[name="email"]', testStudent.email);
      await page.fill('input[name="password"]', 'TestPass123!');
      await page.click('button[type="submit"]');
      
      // Try to access course content
      await page.click(`text=${testCourse.title}`);
      
      // Should see access restricted message
      await expect(page.locator('text=Course access will be available on')).toBeVisible();
    });
  });

  test('Email notification content validation', async ({ page }) => {
    // This test would validate email content in a real implementation
    // For now, we'll test the email service endpoint directly
    
    await test.step('Validate enrollment notification email format', async () => {
      // Mock test - in real implementation, we'd check email service logs
      // or integrate with email testing service
      
      const response = await page.request.get('/api/test/last-email');
      expect(response.ok()).toBeTruthy();
      
      const emailData = await response.json();
      expect(emailData.subject).toContain(testCourse.title);
      expect(emailData.body).toContain(testStudent.email); // Login email
      expect(emailData.body).toContain('password'); // Generated password
      expect(emailData.body).toContain(testInstructor.name); // Instructor name
    });
  });

  test('Course instance status management', async ({ page }) => {
    await test.step('Course instance status changes based on dates', async () => {
      // Login as instructor
      await page.click('text=Login');
      await page.fill('input[name="email"]', testInstructor.email);
      await page.fill('input[name="password"]', testInstructor.password);
      await page.click('button[type="submit"]');
      
      // Navigate to course management
      await page.click('text=My Courses');
      
      // Create course instance with past dates (should be completed)
      await page.click('text=Create Instance');
      
      const pastStart = new Date();
      pastStart.setDate(pastStart.getDate() - 7);
      const pastEnd = new Date();
      pastEnd.setDate(pastEnd.getDate() - 2);
      
      await page.fill('input[name="startDate"]', pastStart.toISOString().split('T')[0]);
      await page.fill('input[name="endDate"]', pastEnd.toISOString().split('T')[0]);
      await page.click('button:has-text("Create Instance")');
      
      // Verify status shows as "Completed"
      await expect(page.locator('text=Completed')).toBeVisible();
    });
  });

  test('Multiple student enrollment and management', async ({ page }) => {
    const students = [
      { email: 'student1@test.com' },
      { email: 'student2@test.com' },
      { email: 'student3@test.com' }
    ];

    await test.step('Instructor enrolls multiple students', async () => {
      // Login as instructor
      await page.click('text=Login');
      await page.fill('input[name="email"]', testInstructor.email);
      await page.fill('input[name="password"]', testInstructor.password);
      await page.click('button[type="submit"]');
      
      await page.click('text=Students');
      
      // Enroll each student
      for (const student of students) {
        await page.selectOption('#selectedCourse', { label: testCourse.title });
        await page.fill('input[name="studentEmail"]', student.email);
        
        const startDate = new Date();
        startDate.setDate(startDate.getDate() + 1);
        const endDate = new Date();
        endDate.setDate(endDate.getDate() + 14);
        
        await page.fill('input[name="startDate"]', startDate.toISOString().split('T')[0]);
        await page.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
        
        await page.click('button:has-text("Enroll Student")');
        await expect(page.locator('text=Student enrolled successfully')).toBeVisible();
      }
    });

    await test.step('Verify all students are listed', async () => {
      // Check that all students appear in enrolled list
      for (const student of students) {
        await expect(page.locator(`text=${student.email}`)).toBeVisible();
      }
    });
  });

  test('Error handling and validation', async ({ page }) => {
    await test.step('Handle invalid email addresses', async () => {
      // Login as instructor
      await page.click('text=Login');
      await page.fill('input[name="email"]', testInstructor.email);
      await page.fill('input[name="password"]', testInstructor.password);
      await page.click('button[type="submit"]');
      
      await page.click('text=Students');
      
      // Try to enroll with invalid email
      await page.selectOption('#selectedCourse', { label: testCourse.title });
      await page.fill('input[name="studentEmail"]', 'invalid-email');
      
      await page.click('button:has-text("Enroll Student")');
      
      // Should show validation error
      await expect(page.locator('text=Please enter a valid email address')).toBeVisible();
    });

    await test.step('Handle invalid course dates', async () => {
      // Try to create course instance with end date before start date
      await page.selectOption('#selectedCourse', { label: testCourse.title });
      await page.fill('input[name="studentEmail"]', 'valid@test.com');
      
      const startDate = new Date();
      startDate.setDate(startDate.getDate() + 14);
      const endDate = new Date();
      endDate.setDate(endDate.getDate() + 7); // Before start date
      
      await page.fill('input[name="startDate"]', startDate.toISOString().split('T')[0]);
      await page.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
      
      await page.click('button:has-text("Enroll Student")');
      
      // Should show validation error
      await expect(page.locator('text=End date must be after start date')).toBeVisible();
    });
  });
});

test.describe('Student Dashboard Functionality', () => {
  
  test.beforeEach(async ({ page }) => {
    // Login as student before each test
    await page.goto('/');
    await page.click('text=Login');
    await page.fill('input[name="email"]', testStudent.email);
    await page.fill('input[name="password"]', 'TestPass123!');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/student-dashboard/);
  });

  test('Student can navigate course content', async ({ page }) => {
    await test.step('Student can access course materials', async () => {
      // Click on enrolled course
      await page.click(`text=${testCourse.title}`);
      
      // Should see course content
      await expect(page.locator('text=Course Content')).toBeVisible();
      await expect(page.locator('text=Slides')).toBeVisible();
    });

    await test.step('Student cannot access instructor features', async () => {
      // Verify no instructor navigation options
      await expect(page.locator('text=Create Course')).not.toBeVisible();
      await expect(page.locator('text=Manage Students')).not.toBeVisible();
      await expect(page.locator('text=Course Analytics')).not.toBeVisible();
    });
  });

  test('Student lab environment access', async ({ page }) => {
    await test.step('Student can launch lab environment', async () => {
      await page.click(`text=${testCourse.title}`);
      
      // Click on lab section
      await page.click('text=Lab');
      
      // Should be able to launch lab
      await page.click('button:has-text("Launch Lab")');
      
      // Verify lab environment loads
      await expect(page.locator('#lab-container')).toBeVisible();
    });
  });

  test('Student quiz access without answers', async ({ page }) => {
    await test.step('Student can take quizzes but not see answers', async () => {
      await page.click(`text=${testCourse.title}`);
      await page.click('text=Quiz');
      
      // Should see quiz questions
      await expect(page.locator('.quiz-question')).toBeVisible();
      
      // Should not see answer key or correct answers
      await expect(page.locator('text=Answer Key')).not.toBeVisible();
      await expect(page.locator('.correct-answer')).not.toBeVisible();
    });
  });
});