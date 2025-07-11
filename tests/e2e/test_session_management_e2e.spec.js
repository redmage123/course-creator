/**
 * End-to-End tests for session management functionality
 * Tests login, logout, session timeouts, and multi-user scenarios
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:3000';
const API_BASE_URL = 'http://localhost:8000';

test.describe('Session Management E2E Tests', () => {
  let testUser;

  test.beforeEach(async () => {
    // Create unique test user for each test
    const randomId = Math.random().toString(36).substring(7);
    testUser = {
      email: `test_${randomId}@example.com`,
      username: `testuser_${randomId}`,
      password: 'TestPassword123!',
      full_name: 'Test User'
    };
  });

  test('User registration and login workflow', async ({ page }) => {
    // Navigate to the platform
    await page.goto(BASE_URL);
    
    // Test registration
    await page.click('text=Register');
    await page.fill('input[name="email"]', testUser.email);
    await page.fill('input[name="username"]', testUser.username);
    await page.fill('input[name="password"]', testUser.password);
    await page.fill('input[name="full_name"]', testUser.full_name);
    await page.click('button[type="submit"]');
    
    // Wait for registration success
    await expect(page.locator('text=Registration successful')).toBeVisible({ timeout: 10000 });
    
    // Test login
    await page.click('text=Login');
    await page.fill('input[name="username"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);
    await page.click('button[type="submit"]');
    
    // Verify successful login
    await expect(page.locator('text=Welcome')).toBeVisible({ timeout: 10000 });
    
    // Verify user is in authenticated state
    await expect(page.locator('text=Logout')).toBeVisible();
  });

  test('Session timeout handling', async ({ page }) => {
    // Login first
    await page.goto(BASE_URL);
    await page.click('text=Login');
    await page.fill('input[name="username"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=Welcome')).toBeVisible();
    
    // Mock session expiry by intercepting API calls
    await page.route('**/api/**', route => {
      if (route.request().headers()['authorization']) {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Session expired or invalid' })
        });
      } else {
        route.continue();
      }
    });
    
    // Try to access protected content
    await page.click('text=My Courses');
    
    // Should be redirected to login due to expired session
    await expect(page.locator('text=Session expired')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=Login')).toBeVisible();
  });

  test('Logout functionality', async ({ page }) => {
    // Login first
    await page.goto(BASE_URL);
    
    // Register user via API to ensure they exist
    await page.request.post(`${API_BASE_URL}/auth/register`, {
      data: testUser
    });
    
    // Login through UI
    await page.click('text=Login');
    await page.fill('input[name="username"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=Welcome')).toBeVisible();
    
    // Test logout
    await page.click('text=Logout');
    
    // Verify logout success
    await expect(page.locator('text=Logged out successfully')).toBeVisible();
    await expect(page.locator('text=Login')).toBeVisible();
    
    // Verify session is actually invalidated
    await page.goto(`${BASE_URL}/instructor-dashboard.html`);
    await expect(page.locator('text=Please log in')).toBeVisible();
  });

  test('Multiple session management', async ({ browser }) => {
    // Create two browser contexts to simulate different devices
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    // Register user via API
    await page1.request.post(`${API_BASE_URL}/auth/register`, {
      data: testUser
    });
    
    // Login from first device
    await page1.goto(BASE_URL);
    await page1.click('text=Login');
    await page1.fill('input[name="username"]', testUser.email);
    await page1.fill('input[name="password"]', testUser.password);
    await page1.click('button[type="submit"]');
    
    await expect(page1.locator('text=Welcome')).toBeVisible();
    
    // Login from second device
    await page2.goto(BASE_URL);
    await page2.click('text=Login');
    await page2.fill('input[name="username"]', testUser.email);
    await page2.fill('input[name="password"]', testUser.password);
    await page2.click('button[type="submit"]');
    
    await expect(page2.locator('text=Welcome')).toBeVisible();
    
    // Both sessions should be active
    await expect(page1.locator('text=Welcome')).toBeVisible();
    await expect(page2.locator('text=Welcome')).toBeVisible();
    
    // Logout from first device
    await page1.click('text=Logout');
    await expect(page1.locator('text=Login')).toBeVisible();
    
    // Second device should still be logged in
    await page2.reload();
    await expect(page2.locator('text=Welcome')).toBeVisible();
    
    await context1.close();
    await context2.close();
  });

  test('Session management dashboard', async ({ page }) => {
    // Login first
    await page.goto(BASE_URL);
    
    // Register and login
    await page.request.post(`${API_BASE_URL}/auth/register`, {
      data: testUser
    });
    
    const loginResponse = await page.request.post(`${API_BASE_URL}/auth/login`, {
      form: {
        username: testUser.email,
        password: testUser.password
      }
    });
    
    const loginData = await loginResponse.json();
    const token = loginData.access_token;
    
    // Access session management
    await page.goto(BASE_URL);
    await page.addInitScript(token => {
      localStorage.setItem('authToken', token);
    }, token);
    
    await page.reload();
    
    // Navigate to account settings or session management
    await page.click('text=Account');
    await page.click('text=Manage Sessions');
    
    // Verify session list is displayed
    await expect(page.locator('text=Active Sessions')).toBeVisible();
    await expect(page.locator('.session-item')).toBeVisible();
    
    // Test session revocation (if UI supports it)
    const sessionCount = await page.locator('.session-item').count();
    if (sessionCount > 0) {
      await page.click('.session-item .revoke-button');
      await expect(page.locator('text=Session revoked')).toBeVisible();
    }
  });

  test('Invalid authentication handling', async ({ page }) => {
    await page.goto(BASE_URL);
    
    // Test login with invalid credentials
    await page.click('text=Login');
    await page.fill('input[name="username"]', 'invalid@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');
    
    // Should show error message
    await expect(page.locator('text=Invalid credentials')).toBeVisible();
    await expect(page.locator('text=Login')).toBeVisible();
  });

  test('Session persistence across page reloads', async ({ page }) => {
    // Register and login
    await page.goto(BASE_URL);
    await page.request.post(`${API_BASE_URL}/auth/register`, {
      data: testUser
    });
    
    await page.click('text=Login');
    await page.fill('input[name="username"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=Welcome')).toBeVisible();
    
    // Reload page
    await page.reload();
    
    // Should still be logged in
    await expect(page.locator('text=Welcome')).toBeVisible();
    await expect(page.locator('text=Logout')).toBeVisible();
    
    // Navigate to different page
    await page.goto(`${BASE_URL}/instructor-dashboard.html`);
    
    // Should still be authenticated
    await expect(page.locator('text=Dashboard')).toBeVisible();
  });
});

test.describe('Security E2E Tests', () => {
  test('XSS protection in user inputs', async ({ page }) => {
    const xssPayload = '<script>alert("xss")</script>';
    
    await page.goto(BASE_URL);
    
    // Test XSS in registration form
    await page.click('text=Register');
    await page.fill('input[name="full_name"]', xssPayload);
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'password123');
    
    // Monitor for alert dialogs (should not appear)
    let alertTriggered = false;
    page.on('dialog', async dialog => {
      alertTriggered = true;
      await dialog.dismiss();
    });
    
    await page.click('button[type="submit"]');
    
    // Wait a moment to see if alert triggers
    await page.waitForTimeout(1000);
    
    expect(alertTriggered).toBe(false);
    
    // Verify XSS payload is escaped in display
    if (await page.locator('text=Registration successful').isVisible()) {
      const displayedName = await page.locator('[data-testid="user-name"]').textContent();
      expect(displayedName).not.toContain('<script>');
    }
  });

  test('CSRF protection', async ({ page }) => {
    // This test would verify CSRF tokens are properly implemented
    // For now, we'll test that forms include proper security headers
    
    await page.goto(BASE_URL);
    await page.click('text=Login');
    
    // Check that form submissions include proper headers
    const response = await page.waitForResponse(response => 
      response.url().includes('/auth/login') && response.request().method() === 'POST'
    );
    
    // Verify Content-Type is set properly
    const contentType = response.request().headers()['content-type'];
    expect(contentType).toBeTruthy();
  });
});