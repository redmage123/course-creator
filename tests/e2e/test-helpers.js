/**
 * Helper utilities for E2E tests
 * Provides common test functions and data setup
 */

import { expect } from '@playwright/test';

export const TestUsers = {
  admin: {
    email: 'admin@courseplatform.com',
    password: 'admin123',
    role: 'admin',
    name: 'Test Admin'
  },
  instructor: {
    email: 'instructor@test.com',
    password: 'instructor123', 
    role: 'instructor',
    name: 'Dr. Test Instructor'
  },
  student: {
    email: 'student@test.com',
    password: 'student123',
    role: 'student',
    name: 'Test Student'
  }
};

export const TestCourses = {
  basic: {
    title: 'Basic Programming Course',
    description: 'Learn the fundamentals of programming',
    category: 'Programming',
    difficulty: 'beginner'
  },
  advanced: {
    title: 'Advanced Data Structures',
    description: 'Deep dive into data structures and algorithms',
    category: 'Computer Science',
    difficulty: 'advanced'
  }
};

export class LoginHelper {
  constructor(page) {
    this.page = page;
  }

  async loginAs(userType) {
    const user = TestUsers[userType];
    if (!user) {
      throw new Error(`Unknown user type: ${userType}`);
    }

    await this.page.goto('/');
    await this.page.click('text=Login');
    await this.page.fill('input[name="email"]', user.email);
    await this.page.fill('input[name="password"]', user.password);
    await this.page.click('button[type="submit"]');
    
    // Wait for successful login redirect
    if (user.role === 'admin') {
      await expect(this.page).toHaveURL(/admin/);
    } else if (user.role === 'instructor') {
      await expect(this.page).toHaveURL(/instructor-dashboard/);
    } else if (user.role === 'student') {
      await expect(this.page).toHaveURL(/student-dashboard/);
    }
    
    return user;
  }

  async logout() {
    await this.page.click('text=Logout');
    await expect(this.page).toHaveURL('/');
  }
}

export class CourseHelper {
  constructor(page) {
    this.page = page;
  }

  async createCourse(courseData = TestCourses.basic) {
    await this.page.click('text=Create Course');
    
    await this.page.fill('input[name="title"]', courseData.title);
    await this.page.fill('textarea[name="description"]', courseData.description);
    await this.page.selectOption('select[name="category"]', courseData.category);
    await this.page.selectOption('select[name="difficulty"]', courseData.difficulty);
    
    await this.page.click('button:has-text("Create Course")');
    
    // Verify course was created
    await expect(this.page.locator(`text=${courseData.title}`)).toBeVisible();
    
    return courseData;
  }

  async createCourseInstance(startDaysFromNow = 1, endDaysFromNow = 14, maxStudents = 25) {
    const startDate = new Date();
    startDate.setDate(startDate.getDate() + startDaysFromNow);
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + endDaysFromNow);

    await this.page.click('text=Manage Instances');
    await this.page.click('button:has-text("Create Instance")');
    
    await this.page.fill('input[name="startDate"]', startDate.toISOString().split('T')[0]);
    await this.page.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
    await this.page.fill('input[name="maxStudents"]', maxStudents.toString());
    
    await this.page.click('button:has-text("Create Instance")');
    
    return {
      startDate,
      endDate,
      maxStudents
    };
  }
}

export class StudentHelper {
  constructor(page) {
    this.page = page;
  }

  async enrollStudent(studentEmail, courseTitle, startDaysFromNow = 1, endDaysFromNow = 14) {
    await this.page.click('text=Students');
    
    // Wait for students section to load
    await expect(this.page.locator('#students-section')).toBeVisible({ timeout: 10000 });
    
    // Select course
    await this.page.selectOption('#selectedCourse', { label: courseTitle });
    
    // Fill student email
    await this.page.fill('input[name="studentEmail"]', studentEmail);
    
    // Set dates
    const startDate = new Date();
    startDate.setDate(startDate.getDate() + startDaysFromNow);
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + endDaysFromNow);
    
    await this.page.fill('input[name="startDate"]', startDate.toISOString().split('T')[0]);
    await this.page.fill('input[name="endDate"]', endDate.toISOString().split('T')[0]);
    
    // Submit enrollment
    await this.page.click('button:has-text("Enroll Student")');
    
    // Verify success
    await expect(this.page.locator('text=Student enrolled successfully')).toBeVisible();
    
    return { studentEmail, startDate, endDate };
  }

  async verifyStudentEnrollment(studentEmail) {
    await expect(this.page.locator(`text=${studentEmail}`)).toBeVisible();
  }
}

export class DatabaseHelper {
  /**
   * Helper for database operations during testing
   */
  static async cleanupTestData() {
    // In a real implementation, this would clean up test data
    // For now, we'll rely on the global teardown
    console.log('Cleaning up test data...');
  }

  static async setupTestUsers() {
    // In a real implementation, this would ensure test users exist
    console.log('Setting up test users...');
  }
}

export class WaitHelper {
  /**
   * Helper for common wait operations
   */
  static async waitForServiceReady(page, timeout = 30000) {
    // Wait for backend services to be ready
    await page.waitForLoadState('networkidle', { timeout });
  }

  static async waitForElementToBeVisible(page, selector, timeout = 10000) {
    await expect(page.locator(selector)).toBeVisible({ timeout });
  }

  static async waitForTextContent(page, text, timeout = 10000) {
    await expect(page.locator(`text=${text}`)).toBeVisible({ timeout });
  }
}

export class AssertionHelper {
  /**
   * Custom assertions for common test scenarios
   */
  static async assertUserRole(page, expectedRole) {
    const roleIndicator = page.locator('[data-testid="user-role"]');
    if (await roleIndicator.isVisible()) {
      await expect(roleIndicator).toContainText(expectedRole);
    }
  }

  static async assertCourseCreated(page, courseTitle) {
    await expect(page.locator(`text=${courseTitle}`)).toBeVisible();
    await expect(page.locator('text=Course created successfully')).toBeVisible();
  }

  static async assertAccessDenied(page) {
    await expect(page.locator('text=Access Denied')).toBeVisible();
  }

  static async assertNotificationDisplayed(page, message) {
    await expect(page.locator(`text=${message}`)).toBeVisible();
  }
}

export const dateHelper = {
  /**
   * Helper functions for date manipulation in tests
   */
  getFutureDate(daysFromNow = 1) {
    const date = new Date();
    date.setDate(date.getDate() + daysFromNow);
    return date.toISOString().split('T')[0];
  },

  getPastDate(daysAgo = 1) {
    const date = new Date();
    date.setDate(date.getDate() - daysAgo);
    return date.toISOString().split('T')[0];
  },

  getCurrentDate() {
    return new Date().toISOString().split('T')[0];
  }
};

export const mockData = {
  /**
   * Mock data generators for testing
   */
  generateStudentEmail(prefix = 'student') {
    const timestamp = Date.now();
    return `${prefix}${timestamp}@test.com`;
  },

  generateCourseData(title = 'Test Course') {
    const timestamp = Date.now();
    return {
      title: `${title} ${timestamp}`,
      description: `Test course created at ${new Date().toISOString()}`,
      category: 'Programming',
      difficulty: 'beginner'
    };
  }
};