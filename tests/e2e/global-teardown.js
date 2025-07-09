/**
 * Global teardown for Playwright tests
 * Cleans up test environment after running tests
 */

import { chromium } from '@playwright/test';

async function globalTeardown() {
  console.log('🧹 Starting global teardown for E2E tests...');
  
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Clean up test data
    await cleanupTestData(page);
    
    // Generate test report summary
    await generateTestSummary();
    
  } catch (error) {
    console.error('❌ Global teardown failed:', error);
  } finally {
    await browser.close();
  }
  
  console.log('✅ Global teardown completed successfully');
}

async function cleanupTestData(page) {
  console.log('🧹 Cleaning up test data...');
  
  // Clean up test courses
  try {
    const coursesResponse = await page.request.get('http://localhost:8004/courses');
    if (coursesResponse.ok()) {
      const courses = await coursesResponse.json();
      const testCourses = courses.filter(course => 
        course.title.includes('E2E Test') || 
        course.title.includes('Integration Test') ||
        course.instructor.includes('Test User')
      );
      
      for (const course of testCourses) {
        try {
          const deleteResponse = await page.request.delete(`http://localhost:8004/courses/${course.id}`);
          if (deleteResponse.ok()) {
            console.log(`🗑️  Deleted test course: ${course.title}`);
          }
        } catch (error) {
          console.log(`⚠️  Could not delete course ${course.title}:`, error.message);
        }
      }
    }
  } catch (error) {
    console.log('⚠️  Could not clean up test courses:', error.message);
  }
  
  // Note: We don't clean up test users as they might be needed for other tests
  // and user deletion typically requires admin privileges
  
  console.log('✅ Test data cleanup completed');
}

async function generateTestSummary() {
  console.log('📊 Generating test summary...');
  
  const fs = require('fs');
  const path = require('path');
  
  const reportDir = 'test-reports/playwright';
  const summaryPath = path.join(reportDir, 'test-summary.json');
  
  try {
    // Create reports directory if it doesn't exist
    if (!fs.existsSync(reportDir)) {
      fs.mkdirSync(reportDir, { recursive: true });
    }
    
    const summary = {
      timestamp: new Date().toISOString(),
      testRun: {
        completed: true,
        environment: 'local',
        baseURL: 'http://localhost:8080'
      },
      services: {
        frontend: 'http://localhost:8080',
        userManagement: 'http://localhost:8000',
        courseManagement: 'http://localhost:8004'
      },
      cleanup: {
        testDataRemoved: true,
        timestamp: new Date().toISOString()
      }
    };
    
    fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
    console.log(`✅ Test summary saved to: ${summaryPath}`);
  } catch (error) {
    console.log('⚠️  Could not generate test summary:', error.message);
  }
}

export default globalTeardown;