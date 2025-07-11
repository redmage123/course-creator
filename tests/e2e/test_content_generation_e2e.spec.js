/**
 * End-to-End tests for content generation functionality
 * Tests complete workflow from syllabus generation to content creation
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:3000';
const API_BASE_URL = 'http://localhost:8000';

test.describe('Content Generation E2E Tests', () => {
  let testInstructor;
  let authToken;

  test.beforeEach(async ({ page }) => {
    // Create unique test instructor
    const randomId = Math.random().toString(36).substring(7);
    testInstructor = {
      email: `instructor_${randomId}@example.com`,
      username: `instructor_${randomId}`,
      password: 'InstructorPass123!',
      full_name: 'Test Instructor',
      role: 'instructor'
    };

    // Register and login instructor
    await page.request.post(`${API_BASE_URL}/auth/register`, {
      data: testInstructor
    });

    const loginResponse = await page.request.post(`${API_BASE_URL}/auth/login`, {
      form: {
        username: testInstructor.email,
        password: testInstructor.password
      }
    });

    const loginData = await loginResponse.json();
    authToken = loginData.access_token;

    // Set authentication in browser
    await page.goto(BASE_URL);
    await page.addInitScript(token => {
      localStorage.setItem('authToken', token);
      localStorage.setItem('userEmail', testInstructor.email);
    }, authToken);
  });

  test('Complete content generation workflow', async ({ page }) => {
    await page.goto(`${BASE_URL}/instructor-dashboard.html`);
    
    // Verify instructor dashboard loads
    await expect(page.locator('h1:has-text("Instructor Dashboard")')).toBeVisible();
    
    // Step 1: Create new course
    await page.click('text=Create New Course');
    
    // Fill course details
    await page.fill('input[name="title"]', 'Test Course - Python Programming');
    await page.fill('textarea[name="description"]', 'A comprehensive test course for Python programming basics and advanced concepts');
    await page.selectOption('select[name="category"]', 'Programming');
    await page.selectOption('select[name="difficulty"]', 'beginner');
    await page.fill('input[name="duration"]', '40');
    
    await page.click('button:has-text("Generate Syllabus")');
    
    // Step 2: Wait for syllabus generation
    await expect(page.locator('text=Generating syllabus...')).toBeVisible();
    await expect(page.locator('text=Syllabus generated successfully')).toBeVisible({ timeout: 30000 });
    
    // Verify syllabus content is displayed
    await expect(page.locator('.syllabus-overview')).toBeVisible();
    await expect(page.locator('.module-item')).toHaveCount(5, { timeout: 10000 }); // Should have 5 modules
    
    // Step 3: Review and approve syllabus
    await page.click('button:has-text("Approve Syllabus")');
    
    // Wait for content generation
    await expect(page.locator('text=Generating course content...')).toBeVisible();
    await expect(page.locator('text=Content generated successfully')).toBeVisible({ timeout: 60000 });
    
    // Step 4: Verify slides are generated
    await page.click('text=View Slides');
    await expect(page.locator('.slide-item')).toHaveCount(64, { timeout: 10000 }); // Should have multiple slides
    
    // Check slide content quality
    const firstSlide = page.locator('.slide-item').first();
    await expect(firstSlide.locator('.slide-title')).toBeVisible();
    await expect(firstSlide.locator('.slide-content')).toBeVisible();
    
    // Verify slide content is not empty or placeholder
    const slideContent = await firstSlide.locator('.slide-content').textContent();
    expect(slideContent.length).toBeGreaterThan(20); // Should have substantial content
    expect(slideContent).not.toContain('placeholder');
    
    // Step 5: Verify exercises are generated
    await page.click('text=View Exercises');
    await expect(page.locator('.exercise-item')).toHaveCount(28, { timeout: 10000 }); // Should have exercises
    
    // Check exercise quality
    const firstExercise = page.locator('.exercise-item').first();
    await expect(firstExercise.locator('.exercise-title')).toBeVisible();
    await expect(firstExercise.locator('.exercise-description')).toBeVisible();
    await expect(firstExercise.locator('.exercise-instructions')).toBeVisible();
    
    // Step 6: Verify quizzes are generated
    await page.click('text=View Quizzes');
    await expect(page.locator('.quiz-item')).toHaveCount(5, { timeout: 10000 }); // Should have quizzes
    
    // Check quiz quality
    const firstQuiz = page.locator('.quiz-item').first();
    await expect(firstQuiz.locator('.quiz-title')).toBeVisible();
    await expect(firstQuiz.locator('.quiz-questions')).toBeVisible();
    
    // Step 7: Verify lab environment is created
    await page.click('text=View Lab Environment');
    await expect(page.locator('.lab-environment')).toBeVisible();
    await expect(page.locator('text=AI Lab Environment')).toBeVisible();
    await expect(page.locator('.lab-status')).toBeVisible();
  });

  test('Syllabus refinement workflow', async ({ page }) => {
    await page.goto(`${BASE_URL}/instructor-dashboard.html`);
    
    // Create course and generate initial syllabus
    await page.click('text=Create New Course');
    await page.fill('input[name="title"]', 'Basic Python Course');
    await page.fill('textarea[name="description"]', 'Learn Python basics');
    await page.selectOption('select[name="category"]', 'Programming');
    await page.selectOption('select[name="difficulty"]', 'beginner');
    await page.fill('input[name="duration"]', '20');
    
    await page.click('button:has-text("Generate Syllabus")');
    await expect(page.locator('text=Syllabus generated successfully')).toBeVisible({ timeout: 30000 });
    
    // Test syllabus refinement
    await page.click('button:has-text("Refine Syllabus")');
    
    // Provide feedback
    await page.fill('textarea[name="feedback"]', 'Add more advanced topics like web development and data analysis. Include more practical projects.');
    await page.click('button:has-text("Refine")');
    
    // Wait for refinement
    await expect(page.locator('text=Refining syllabus...')).toBeVisible();
    await expect(page.locator('text=Syllabus refined successfully')).toBeVisible({ timeout: 30000 });
    
    // Verify refinements are applied
    const syllabusText = await page.locator('.syllabus-overview').textContent();
    expect(syllabusText.toLowerCase()).toContain('web development');
    expect(syllabusText.toLowerCase()).toContain('data analysis');
  });

  test('Content editing and customization', async ({ page }) => {
    await page.goto(`${BASE_URL}/instructor-dashboard.html`);
    
    // Generate course content first
    await page.click('text=Create New Course');
    await page.fill('input[name="title"]', 'Editable Test Course');
    await page.fill('textarea[name="description"]', 'Course for testing editing');
    await page.selectOption('select[name="category"]', 'Programming');
    await page.selectOption('select[name="difficulty"]', 'beginner');
    await page.fill('input[name="duration"]', '16');
    
    await page.click('button:has-text("Generate Syllabus")');
    await expect(page.locator('text=Syllabus generated successfully')).toBeVisible({ timeout: 30000 });
    
    await page.click('button:has-text("Approve Syllabus")');
    await expect(page.locator('text=Content generated successfully')).toBeVisible({ timeout: 60000 });
    
    // Test slide editing
    await page.click('text=View Slides');
    await page.click('.slide-item .edit-button');
    
    const newSlideContent = 'This is custom edited slide content for testing';
    await page.fill('textarea[name="slide-content"]', newSlideContent);
    await page.click('button:has-text("Save Changes")');
    
    // Verify changes are saved
    await expect(page.locator(`text=${newSlideContent}`)).toBeVisible();
    
    // Test exercise editing
    await page.click('text=View Exercises');
    await page.click('.exercise-item .edit-button');
    
    const newExerciseTitle = 'Custom Exercise Title';
    await page.fill('input[name="exercise-title"]', newExerciseTitle);
    await page.click('button:has-text("Save Changes")');
    
    // Verify exercise changes
    await expect(page.locator(`text=${newExerciseTitle}`)).toBeVisible();
  });

  test('Lab environment interaction', async ({ page }) => {
    await page.goto(`${BASE_URL}/instructor-dashboard.html`);
    
    // Generate course with lab environment
    await page.click('text=Create New Course');
    await page.fill('input[name="title"]', 'Interactive Lab Course');
    await page.fill('textarea[name="description"]', 'Course with interactive lab');
    await page.selectOption('select[name="category"]', 'Programming');
    await page.selectOption('select[name="difficulty"]', 'beginner');
    await page.fill('input[name="duration"]', '24');
    
    await page.click('button:has-text("Generate Syllabus")');
    await expect(page.locator('text=Syllabus generated successfully')).toBeVisible({ timeout: 30000 });
    
    await page.click('button:has-text("Approve Syllabus")');
    await expect(page.locator('text=Content generated successfully')).toBeVisible({ timeout: 60000 });
    
    // Access lab environment
    await page.click('text=View Lab Environment');
    await expect(page.locator('.lab-environment')).toBeVisible();
    
    // Test lab launch
    await page.click('button:has-text("Launch Lab")');
    await expect(page.locator('text=Lab launched successfully')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('.lab-status:has-text("Running")')).toBeVisible();
    
    // Test AI assistant interaction (if available)
    if (await page.locator('.ai-assistant-chat').isVisible()) {
      await page.fill('input[name="chat-message"]', 'Explain Python variables');
      await page.click('button:has-text("Send")');
      
      // Wait for AI response
      await expect(page.locator('.ai-response')).toBeVisible({ timeout: 10000 });
      
      const response = await page.locator('.ai-response').last().textContent();
      expect(response.length).toBeGreaterThan(20); // Should have substantial response
    }
    
    // Test lab stop
    await page.click('button:has-text("Stop Lab")');
    await expect(page.locator('text=Lab stopped')).toBeVisible();
    await expect(page.locator('.lab-status:has-text("Stopped")')).toBeVisible();
  });

  test('Content quality validation', async ({ page }) => {
    await page.goto(`${BASE_URL}/instructor-dashboard.html`);
    
    // Generate content for quality testing
    await page.click('text=Create New Course');
    await page.fill('input[name="title"]', 'Quality Test Course - Data Science');
    await page.fill('textarea[name="description"]', 'Comprehensive data science course covering statistics, machine learning, and data visualization');
    await page.selectOption('select[name="category"]', 'Data Science');
    await page.selectOption('select[name="difficulty"]', 'intermediate');
    await page.fill('input[name="duration"]', '50');
    
    await page.click('button:has-text("Generate Syllabus")');
    await expect(page.locator('text=Syllabus generated successfully')).toBeVisible({ timeout: 30000 });
    
    await page.click('button:has-text("Approve Syllabus")');
    await expect(page.locator('text=Content generated successfully')).toBeVisible({ timeout: 60000 });
    
    // Validate slide content quality
    await page.click('text=View Slides');
    
    const slides = page.locator('.slide-item');
    const slideCount = await slides.count();
    expect(slideCount).toBeGreaterThan(10); // Should have substantial number of slides
    
    // Check first few slides for quality
    for (let i = 0; i < Math.min(3, slideCount); i++) {
      const slide = slides.nth(i);
      const title = await slide.locator('.slide-title').textContent();
      const content = await slide.locator('.slide-content').textContent();
      
      // Basic quality checks
      expect(title.length).toBeGreaterThan(5);
      expect(content.length).toBeGreaterThan(50);
      expect(content).not.toContain('placeholder');
      expect(content).not.toContain('TODO');
      expect(content).toContain('data science'); // Should be relevant to topic
    }
    
    // Validate exercise quality
    await page.click('text=View Exercises');
    
    const exercises = page.locator('.exercise-item');
    const exerciseCount = await exercises.count();
    expect(exerciseCount).toBeGreaterThan(5);
    
    // Check exercise structure
    const firstExercise = exercises.first();
    await expect(firstExercise.locator('.exercise-title')).toBeVisible();
    await expect(firstExercise.locator('.exercise-description')).toBeVisible();
    await expect(firstExercise.locator('.exercise-instructions')).toBeVisible();
    await expect(firstExercise.locator('.exercise-difficulty')).toBeVisible();
    
    // Validate quiz quality
    await page.click('text=View Quizzes');
    
    const quizzes = page.locator('.quiz-item');
    const quizCount = await quizzes.count();
    expect(quizCount).toBeGreaterThan(2);
    
    // Check quiz structure
    const firstQuiz = quizzes.first();
    await expect(firstQuiz.locator('.quiz-title')).toBeVisible();
    await expect(firstQuiz.locator('.quiz-description')).toBeVisible();
    
    // Check if quiz has questions
    await firstQuiz.click();
    await expect(page.locator('.question-item')).toHaveCount(5, { timeout: 5000 }); // Should have multiple questions
  });

  test('Error handling in content generation', async ({ page }) => {
    // Test with invalid course data
    await page.goto(`${BASE_URL}/instructor-dashboard.html`);
    
    await page.click('text=Create New Course');
    
    // Try to generate with minimal/invalid data
    await page.fill('input[name="title"]', 'X'); // Very short title
    await page.fill('input[name="duration"]', '1'); // Very short duration
    
    await page.click('button:has-text("Generate Syllabus")');
    
    // Should show validation error or fallback content
    await expect(page.locator('text=Error')).toBeVisible({ timeout: 10000 });
    
    // Test recovery - provide better data
    await page.fill('input[name="title"]', 'Proper Course Title');
    await page.fill('textarea[name="description"]', 'Proper course description with enough detail');
    await page.selectOption('select[name="category"]', 'Programming');
    await page.selectOption('select[name="difficulty"]', 'beginner');
    await page.fill('input[name="duration"]', '20');
    
    await page.click('button:has-text("Generate Syllabus")');
    await expect(page.locator('text=Syllabus generated successfully')).toBeVisible({ timeout: 30000 });
  });

  test('Content generation performance', async ({ page }) => {
    await page.goto(`${BASE_URL}/instructor-dashboard.html`);
    
    // Test generation time for normal course
    const startTime = Date.now();
    
    await page.click('text=Create New Course');
    await page.fill('input[name="title"]', 'Performance Test Course');
    await page.fill('textarea[name="description"]', 'Testing content generation performance');
    await page.selectOption('select[name="category"]', 'Programming');
    await page.selectOption('select[name="difficulty"]', 'beginner');
    await page.fill('input[name="duration"]', '30');
    
    await page.click('button:has-text("Generate Syllabus")');
    await expect(page.locator('text=Syllabus generated successfully')).toBeVisible({ timeout: 60000 });
    
    const syllabusTime = Date.now() - startTime;
    expect(syllabusTime).toBeLessThan(45000); // Should complete within 45 seconds
    
    // Test content generation time
    const contentStartTime = Date.now();
    
    await page.click('button:has-text("Approve Syllabus")');
    await expect(page.locator('text=Content generated successfully')).toBeVisible({ timeout: 90000 });
    
    const contentTime = Date.now() - contentStartTime;
    expect(contentTime).toBeLessThan(75000); // Should complete within 75 seconds
    
    console.log(`Syllabus generation: ${syllabusTime}ms, Content generation: ${contentTime}ms`);
  });
});