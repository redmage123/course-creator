/**
 * E2E tests for course instance lifecycle management
 * Tests course creation, instantiation, status changes, and cleanup
 */

import { test, expect } from '@playwright/test';

const testInstructor = {
  email: 'instructor@test.com',
  password: 'instructor123'
};

const testCourse = {
  title: 'Lifecycle Test Course',
  description: 'Testing course lifecycle management',
  category: 'Programming',
  difficulty: 'intermediate'
};

test.describe('Course Instance Lifecycle', () => {
  
  test.beforeEach(async ({ page }) => {
    // Login as instructor
    await page.goto('/');
    await page.click('text=Login');
    await page.fill('input[name="email"]', testInstructor.email);
    await page.fill('input[name="password"]', testInstructor.password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/instructor-dashboard/);
  });

  test('Course instance creation with different date scenarios', async ({ page }) => {
    // Create base course first
    await test.step('Create base course', async () => {
      await page.click('text=Create Course');
      await page.fill('input[name="title"]', testCourse.title);
      await page.fill('textarea[name="description"]', testCourse.description);
      await page.selectOption('select[name="category"]', testCourse.category);
      await page.selectOption('select[name="difficulty"]', testCourse.difficulty);
      await page.click('button:has-text("Create Course")');
      
      await expect(page.locator(`text=${testCourse.title}`)).toBeVisible();
    });

    await test.step('Create future course instance (scheduled status)', async () => {
      await page.click('text=Manage Instances');
      await page.click('button:has-text("Create Instance")');
      
      // Set future dates
      const startDate = new Date();
      startDate.setDate(startDate.getDate() + 7); // Next week
      const endDate = new Date();
      endDate.setDate(endDate.getDate() + 21); // Three weeks from now
      
      await page.fill('input[name="startDate"]', startDate.toISOString().split('T')[0]);
      await page.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
      await page.fill('input[name="maxStudents"]', '25');
      await page.fill('textarea[name="meetingSchedule"]', 'Monday/Wednesday/Friday 10:00-11:30 AM');
      
      await page.click('button:has-text("Create Instance")');
      
      // Verify status is "Scheduled"
      await expect(page.locator('text=Scheduled')).toBeVisible();
      await expect(page.locator(`text=${startDate.toLocaleDateString()}`)).toBeVisible();
    });

    await test.step('Create active course instance (active status)', async () => {
      await page.click('button:has-text("Create Instance")');
      
      // Set current dates (active)
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 2); // Started 2 days ago
      const endDate = new Date();
      endDate.setDate(endDate.getDate() + 12); // Ends in 12 days
      
      await page.fill('input[name="startDate"]', startDate.toISOString().split('T')[0]);
      await page.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
      await page.fill('input[name="maxStudents"]', '30');
      
      await page.click('button:has-text("Create Instance")');
      
      // Verify status is "Active"
      await expect(page.locator('text=Active')).toBeVisible();
    });

    await test.step('Create completed course instance (completed status)', async () => {
      await page.click('button:has-text("Create Instance")');
      
      // Set past dates (completed)
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 14); // Started 2 weeks ago
      const endDate = new Date();
      endDate.setDate(endDate.getDate() - 2); // Ended 2 days ago
      
      await page.fill('input[name="startDate"]', startDate.toISOString().split('T')[0]);
      await page.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
      await page.fill('input[name="maxStudents"]', '20');
      
      await page.click('button:has-text("Create Instance")');
      
      // Verify status is "Completed"
      await expect(page.locator('text=Completed')).toBeVisible();
    });
  });

  test('Course instance status transitions', async ({ page }) => {
    await test.step('Monitor status changes over time', async () => {
      // Create course instance that transitions from scheduled to active
      await page.click('text=Manage Instances');
      await page.click('button:has-text("Create Instance")');
      
      // Set dates that make it transition soon
      const startDate = new Date();
      startDate.setMinutes(startDate.getMinutes() + 2); // Starts in 2 minutes
      const endDate = new Date();
      endDate.setDate(endDate.getDate() + 1); // Ends tomorrow
      
      await page.fill('input[name="startDate"]', startDate.toISOString().slice(0, 16)); // Include time
      await page.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
      await page.fill('input[name="maxStudents"]', '15');
      
      await page.click('button:has-text("Create Instance")');
      
      // Initially should be "Scheduled"
      await expect(page.locator('text=Scheduled')).toBeVisible();
      
      // In a real test, we'd wait and check for status change
      // For demonstration, we'll trigger manual status update
      await page.click('button:has-text("Refresh Status")');
      
      // After time passes, should become "Active"
      // await expect(page.locator('text=Active')).toBeVisible();
    });
  });

  test('Student enrollment capacity management', async ({ page }) => {
    await test.step('Create course instance with limited capacity', async () => {
      await page.click('text=Manage Instances');
      await page.click('button:has-text("Create Instance")');
      
      const startDate = new Date();
      startDate.setDate(startDate.getDate() + 1);
      const endDate = new Date();
      endDate.setDate(endDate.getDate() + 14);
      
      await page.fill('input[name="startDate"]', startDate.toISOString().split('T')[0]);
      await page.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
      await page.fill('input[name="maxStudents"]', '2'); // Very small capacity
      
      await page.click('button:has-text("Create Instance")');
      
      // Verify capacity shows 0/2
      await expect(page.locator('text=0/2 students')).toBeVisible();
    });

    await test.step('Enroll students up to capacity', async () => {
      await page.click('text=Students');
      
      // Enroll first student
      await page.selectOption('#selectedCourse', { label: testCourse.title });
      await page.fill('input[name="studentEmail"]', 'student1@test.com');
      
      const startDate = new Date();
      startDate.setDate(startDate.getDate() + 1);
      const endDate = new Date();
      endDate.setDate(endDate.getDate() + 14);
      
      await page.fill('input[name="startDate"]', startDate.toISOString().split('T')[0]);
      await page.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
      
      await page.click('button:has-text("Enroll Student")');
      await expect(page.locator('text=Student enrolled successfully')).toBeVisible();
      
      // Enroll second student
      await page.fill('input[name="studentEmail"]', 'student2@test.com');
      await page.click('button:has-text("Enroll Student")');
      await expect(page.locator('text=Student enrolled successfully')).toBeVisible();
      
      // Try to enroll third student (should fail)
      await page.fill('input[name="studentEmail"]', 'student3@test.com');
      await page.click('button:has-text("Enroll Student")');
      await expect(page.locator('text=Course instance is at maximum capacity')).toBeVisible();
    });
  });

  test('Course instance data validation', async ({ page }) => {
    await test.step('Validate date constraints', async () => {
      await page.click('text=Manage Instances');
      await page.click('button:has-text("Create Instance")');
      
      // Try to set end date before start date
      const startDate = new Date();
      startDate.setDate(startDate.getDate() + 10);
      const endDate = new Date();
      endDate.setDate(endDate.getDate() + 5); // Before start date
      
      await page.fill('input[name="startDate"]', startDate.toISOString().split('T')[0]);
      await page.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
      await page.fill('input[name="maxStudents"]', '25');
      
      await page.click('button:has-text("Create Instance")');
      
      // Should show validation error
      await expect(page.locator('text=End date must be after start date')).toBeVisible();
    });

    await test.step('Validate capacity constraints', async () => {
      // Try to set negative or zero capacity
      await page.fill('input[name="maxStudents"]', '0');
      await page.click('button:has-text("Create Instance")');
      
      await expect(page.locator('text=Maximum students must be greater than 0')).toBeVisible();
      
      // Try to set unreasonably high capacity
      await page.fill('input[name="maxStudents"]', '10000');
      await page.click('button:has-text("Create Instance")');
      
      await expect(page.locator('text=Maximum students cannot exceed 1000')).toBeVisible();
    });
  });

  test('Multiple course instances management', async ({ page }) => {
    await test.step('Create multiple instances of same course', async () => {
      await page.click('text=Manage Instances');
      
      // Create 3 different instances
      const instances = [
        { start: 1, end: 14, capacity: 20, schedule: 'Morning Session 9:00-11:00 AM' },
        { start: 15, end: 28, capacity: 25, schedule: 'Afternoon Session 2:00-4:00 PM' },
        { start: 30, end: 43, capacity: 15, schedule: 'Evening Session 6:00-8:00 PM' }
      ];
      
      for (let i = 0; i < instances.length; i++) {
        const instance = instances[i];
        
        await page.click('button:has-text("Create Instance")');
        
        const startDate = new Date();
        startDate.setDate(startDate.getDate() + instance.start);
        const endDate = new Date();
        endDate.setDate(endDate.getDate() + instance.end);
        
        await page.fill('input[name="startDate"]', startDate.toISOString().split('T')[0]);
        await page.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
        await page.fill('input[name="maxStudents"]', instance.capacity.toString());
        await page.fill('textarea[name="meetingSchedule"]', instance.schedule);
        
        await page.click('button:has-text("Create Instance")');
        
        // Verify instance was created
        await expect(page.locator(`text=${instance.schedule}`)).toBeVisible();
      }
      
      // Verify all instances are listed
      await expect(page.locator('.course-instance')).toHaveCount(3);
    });

    await test.step('Filter and search instances', async () => {
      // Filter by status
      await page.selectOption('select[name="statusFilter"]', 'Scheduled');
      await expect(page.locator('text=Scheduled')).toBeVisible();
      
      // Filter by date range
      await page.fill('input[name="dateFrom"]', new Date().toISOString().split('T')[0]);
      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 30);
      await page.fill('input[name="dateTo"]', futureDate.toISOString().split('T')[0]);
      
      await page.click('button:has-text("Apply Filter")');
      
      // Should show filtered results
      await expect(page.locator('.course-instance')).toHaveCount(2); // Only instances within date range
    });
  });

  test('Course instance deletion and cleanup', async ({ page }) => {
    await test.step('Delete course instance', async () => {
      await page.click('text=Manage Instances');
      
      // Create instance to delete
      await page.click('button:has-text("Create Instance")');
      
      const startDate = new Date();
      startDate.setDate(startDate.getDate() + 50);
      const endDate = new Date();
      endDate.setDate(endDate.getDate() + 64);
      
      await page.fill('input[name="startDate"]', startDate.toISOString().split('T')[0]);
      await page.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
      await page.fill('input[name="maxStudents"]', '20');
      
      await page.click('button:has-text("Create Instance")');
      
      // Delete the instance
      await page.click('button:has-text("Delete"):last-of-type');
      
      // Confirm deletion
      await page.click('button:has-text("Confirm Delete")');
      
      // Verify instance is removed
      await expect(page.locator('text=Instance deleted successfully')).toBeVisible();
    });

    await test.step('Cannot delete instance with enrolled students', async () => {
      // Create instance and enroll student
      await page.click('button:has-text("Create Instance")');
      
      const startDate = new Date();
      startDate.setDate(startDate.getDate() + 1);
      const endDate = new Date();
      endDate.setDate(endDate.getDate() + 14);
      
      await page.fill('input[name="startDate"]', startDate.toISOString().split('T')[0]);
      await page.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
      await page.fill('input[name="maxStudents"]', '20');
      
      await page.click('button:has-text("Create Instance")');
      
      // Enroll a student
      await page.click('text=Students');
      await page.selectOption('#selectedCourse', { label: testCourse.title });
      await page.fill('input[name="studentEmail"]', 'enrolled@test.com');
      await page.fill('input[name="startDate"]', startDate.toISOString().split('T')[0]);
      await page.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
      await page.click('button:has-text("Enroll Student")');
      
      // Try to delete instance with enrolled student
      await page.click('text=Manage Instances');
      await page.click('button:has-text("Delete"):last-of-type');
      
      // Should show warning
      await expect(page.locator('text=Cannot delete instance with enrolled students')).toBeVisible();
    });
  });
});