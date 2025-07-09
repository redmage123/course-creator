/**
 * Global setup for Playwright tests
 * Sets up test environment before running tests
 */

import { chromium } from '@playwright/test';

async function globalSetup() {
  console.log('🚀 Starting global setup for E2E tests...');
  
  // Check if services are running
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Check if frontend is accessible
    console.log('📡 Checking frontend service...');
    await page.goto('http://localhost:8080', { timeout: 10000 });
    console.log('✅ Frontend service is running');
    
    // Check if backend services are accessible
    console.log('📡 Checking backend services...');
    
    // Check user management service
    try {
      const userServiceResponse = await page.request.get('http://localhost:8000/health');
      if (userServiceResponse.ok()) {
        console.log('✅ User management service is running');
      } else {
        console.log('⚠️  User management service responded with:', userServiceResponse.status());
      }
    } catch (error) {
      console.log('⚠️  User management service is not accessible:', error.message);
    }
    
    // Check course management service
    try {
      const courseServiceResponse = await page.request.get('http://localhost:8004/health');
      if (courseServiceResponse.ok()) {
        console.log('✅ Course management service is running');
      } else {
        console.log('⚠️  Course management service responded with:', courseServiceResponse.status());
      }
    } catch (error) {
      console.log('⚠️  Course management service is not accessible:', error.message);
    }
    
    // Set up test data if needed
    await setupTestData(page);
    
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
  
  console.log('✅ Global setup completed successfully');
}

async function setupTestData(page) {
  console.log('🔧 Setting up test data...');
  
  // Create test user for E2E tests
  const testUser = {
    email: 'e2e.test@example.com',
    username: 'e2etest',
    full_name: 'E2E Test User',
    password: 'testpass123'
  };
  
  try {
    const response = await page.request.post('http://localhost:8000/auth/register', {
      data: testUser
    });
    
    if (response.ok()) {
      console.log('✅ Test user created successfully');
    } else if (response.status() === 400) {
      console.log('ℹ️  Test user already exists');
    } else {
      console.log('⚠️  Failed to create test user:', response.status());
    }
  } catch (error) {
    console.log('⚠️  Could not create test user:', error.message);
  }
  
  // Create test course
  const testCourse = {
    title: 'E2E Test Course',
    description: 'A course for end-to-end testing',
    instructor: 'E2E Test User',
    category: 'Testing',
    difficulty: 'beginner',
    duration: '1 week'
  };
  
  try {
    const response = await page.request.post('http://localhost:8004/courses', {
      data: testCourse
    });
    
    if (response.ok()) {
      console.log('✅ Test course created successfully');
    } else {
      console.log('⚠️  Failed to create test course:', response.status());
    }
  } catch (error) {
    console.log('⚠️  Could not create test course:', error.message);
  }
}

export default globalSetup;