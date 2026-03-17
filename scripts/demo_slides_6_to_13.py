#!/usr/bin/env python3
"""
Demo Slides 6-13 - Remaining Workflow Functions

Add these functions to the main demo generation script
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

# Import utility functions from main script
# (smooth_scroll, smooth_mouse_move, type_slowly, remove_privacy_banners, etc.)

# ============================================================================
# SLIDE 6: Course Content (45 seconds)
# ============================================================================

async def slide_06_adding_course_content(page, recorder, duration):
    """
    Course content creation with AI assistance
    - Content editor interface
    - AI content generation
    - Adding lessons and materials
    """
    logger.info("📝 Slide 6: Course Content Creation")

    # Stay on instructor dashboard, navigate to content section
    await asyncio.sleep(1)

    recorder.start_recording(VIDEOS_DIR / "slide_06_adding_course_content.mp4")
    await asyncio.sleep(1)

    # Show content creation interface
    content_tab = await page.query_selector('a[href="#content"], .content-tab')
    if content_tab:
        await content_tab.click()
        await asyncio.sleep(2)

    # Show lesson editor
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(7)

    # Demonstrate AI content generation section
    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(10)

    # Show quiz creation
    await smooth_scroll(page, 1200, 1000)
    await asyncio.sleep(10)

    # Show file upload section
    await smooth_scroll(page, 1600, 1000)
    await asyncio.sleep(8)

    # Back to content overview
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(5)

    recorder.stop_recording()
    logger.info("✅ Slide 6 complete")

# ============================================================================
# SLIDE 7: Enroll Employees (45 seconds)
# ============================================================================

async def slide_07_enrolling_students(page, recorder, duration):
    """
    Student enrollment workflow
    - Navigate back to org admin
    - Show enrollment interface
    - Bulk CSV upload demonstration
    - Enrollment confirmation
    """
    logger.info("👥 Slide 7: Enrolling Students")

    await page.goto(f"{BASE_URL}/html/org-admin-dashboard-modular.html",
                   wait_until='networkidle',
                   timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording(VIDEOS_DIR / "slide_07_enrolling_students.mp4")
    await asyncio.sleep(1)

    # Navigate to enrollment section
    enrollment_tab = await page.query_selector('a[href="#enrollment"], a[data-tab="enrollment"]')
    if enrollment_tab:
        await enrollment_tab.click()
        await asyncio.sleep(2)

    # Show individual enrollment
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(8)

    # Show bulk enrollment section
    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(10)

    # Hover over CSV upload button
    upload_btn = await page.query_selector('.bulk-upload-btn, #csv-upload-btn, input[type="file"]')
    if upload_btn:
        box = await upload_btn.bounding_box()
        if box:
            await smooth_mouse_move(page, box['x'] + 50, box['y'] + 20)
            await asyncio.sleep(5)

    # Show enrolled students list
    await smooth_scroll(page, 1200, 1000)
    await asyncio.sleep(10)

    # Back to overview
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(5)

    recorder.stop_recording()
    logger.info("✅ Slide 7 complete")

# ============================================================================
# SLIDE 8: Student Dashboard (30 seconds)
# ============================================================================

async def slide_08_student_course_browsing(page, recorder, duration):
    """
    Student dashboard experience
    - Login as student
    - Show personalized dashboard
    - Assigned courses
    - Progress tracking
    """
    logger.info("🎓 Slide 8: Student Dashboard")

    await page.goto(f"{BASE_URL}/html/student-dashboard-modular.html",
                   wait_until='networkidle',
                   timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording(VIDEOS_DIR / "slide_08_student_course_browsing.mp4")
    await asyncio.sleep(1)

    # Show dashboard overview
    await asyncio.sleep(3)

    # Show assigned courses
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(7)

    # Show progress section
    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(8)

    # Show recent activity
    await smooth_scroll(page, 1100, 1000)
    await asyncio.sleep(6)

    # Back to top
    await smooth_scroll(page, 200, 1000)
    await asyncio.sleep(3)

    recorder.stop_recording()
    logger.info("✅ Slide 8 complete")

# ============================================================================
# SLIDE 9: Course Browsing + IDEs (75 seconds - LONGEST SLIDE)
# ============================================================================

async def slide_09_student_login_and_dashboard(page, recorder, duration):
    """
    Student learning experience with browser IDEs
    - Browse course catalog
    - Enroll in course
    - Launch coding lab
    - Show VSCode/PyCharm/JupyterLab in browser
    """
    logger.info("💻 Slide 9: Course Browsing & Browser IDEs")

    # Stay on student dashboard
    await asyncio.sleep(1)

    recorder.start_recording(VIDEOS_DIR / "slide_09_student_login_and_dashboard.mp4")
    await asyncio.sleep(1)

    # Navigate to course catalog
    catalog_link = await page.query_selector('a[href*="courses"], .course-catalog-link')
    if catalog_link:
        await catalog_link.click()
        await asyncio.sleep(3)

    # Browse courses
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(10)

    # Click on a course
    course_card = await page.query_selector('.course-card, .course-item')
    if course_card:
        box = await course_card.bounding_box()
        if box:
            await smooth_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(3)
            await course_card.click()
            await asyncio.sleep(4)

    # Show course details
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(10)

    # Look for lab/IDE link
    lab_link = await page.query_selector('a[href*="lab"], .launch-lab-btn, .ide-link')
    if lab_link:
        box = await lab_link.bounding_box()
        if box:
            await smooth_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(5)

    # Show IDE features section
    await smooth_scroll(page, 1000, 1000)
    await asyncio.sleep(15)

    # Show different IDE options
    await smooth_scroll(page, 1400, 1000)
    await asyncio.sleep(15)

    # Back to course view
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(7)

    recorder.stop_recording()
    logger.info("✅ Slide 9 complete")

# ============================================================================
# SLIDE 10: Taking Quizzes (45 seconds)
# ============================================================================

async def slide_10_taking_quiz(page, recorder, duration):
    """
    Quiz taking experience
    - Navigate to quiz
    - Show different question types
    - Submit quiz
    - Show feedback
    """
    logger.info("✍️  Slide 10: Taking Quizzes")

    # Navigate to quiz page
    await page.goto(f"{BASE_URL}/html/quiz.html",
                   wait_until='networkidle',
                   timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording(VIDEOS_DIR / "slide_10_taking_quiz.mp4")
    await asyncio.sleep(1)

    # Show quiz introduction
    await asyncio.sleep(3)

    # Show multiple choice question
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(8)

    # Show code challenge question
    await smooth_scroll(page, 700, 1000)
    await asyncio.sleep(10)

    # Show short answer question
    await smooth_scroll(page, 1100, 1000)
    await asyncio.sleep(8)

    # Scroll to submit button
    await smooth_scroll(page, 1400, 1000)
    await asyncio.sleep(5)

    # Hover over submit
    submit_btn = await page.query_selector('.submit-quiz-btn, #submit-quiz')
    if submit_btn:
        box = await submit_btn.bounding_box()
        if box:
            await smooth_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(5)

    # Back to questions
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(3)

    recorder.stop_recording()
    logger.info("✅ Slide 10 complete")

# ============================================================================
# SLIDE 11: Student Progress (30 seconds)
# ============================================================================

async def slide_11_student_progress_analytics(page, recorder, duration):
    """
    Student progress tracking
    - Progress dashboard
    - Completion rates
    - Achievements
    - Certificates
    """
    logger.info("📊 Slide 11: Student Progress")

    await page.goto(f"{BASE_URL}/html/student-dashboard-modular.html",
                   wait_until='networkidle',
                   timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(2)

    recorder.start_recording(VIDEOS_DIR / "slide_11_student_progress_analytics.mp4")
    await asyncio.sleep(1)

    # Navigate to progress tab
    progress_tab = await page.query_selector('a[href="#progress"], a[data-tab="progress"]')
    if progress_tab:
        await progress_tab.click()
        await asyncio.sleep(2)

    # Show progress overview
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(7)

    # Show detailed statistics
    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(10)

    # Show achievements/certificates
    await smooth_scroll(page, 1200, 1000)
    await asyncio.sleep(6)

    # Back to overview
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(3)

    recorder.stop_recording()
    logger.info("✅ Slide 11 complete")

# ============================================================================
# SLIDE 12: Instructor Analytics (45 seconds)
# ============================================================================

async def slide_12_instructor_analytics(page, recorder, duration):
    """
    Instructor analytics dashboard with AI insights
    - Navigate to analytics
    - Show AI-powered insights
    - Student risk detection
    - Performance metrics
    - Export reports
    """
    logger.info("📈 Slide 12: Instructor Analytics")

    await page.goto(f"{BASE_URL}/html/instructor-dashboard-modular.html",
                   wait_until='networkidle',
                   timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording(VIDEOS_DIR / "slide_12_instructor_analytics.mp4")
    await asyncio.sleep(1)

    # Navigate to analytics tab
    analytics_tab = await page.query_selector('a[href="#analytics"], a[data-tab="analytics"]')
    if analytics_tab:
        await analytics_tab.click()
        await asyncio.sleep(2)

    # Show AI insights section
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(10)

    # Show student performance metrics
    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(10)

    # Show content engagement analysis
    await smooth_scroll(page, 1200, 1000)
    await asyncio.sleep(10)

    # Show export/integration options
    await smooth_scroll(page, 1600, 1000)
    await asyncio.sleep(8)

    # Back to insights
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(4)

    recorder.stop_recording()
    logger.info("✅ Slide 12 complete")

# ============================================================================
# SLIDE 13: Summary & Next Steps (27 seconds - EXTENDED from 15s)
# ============================================================================

async def slide_13_summary_and_cta(page, recorder, duration):
    """
    Platform summary and call to action
    - Return to homepage
    - Show key features summary
    - Integration logos
    - Call to action
    """
    logger.info("🎯 Slide 13: Summary & CTA")

    await page.goto(f"{BASE_URL}/html/index.html",
                   wait_until='networkidle',
                   timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(2)

    recorder.start_recording(VIDEOS_DIR / "slide_13_summary_and_cta.mp4")
    await asyncio.sleep(1)

    # Show hero with CTA
    await asyncio.sleep(4)

    # Scroll to features summary
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(6)

    # Show integrations
    await smooth_scroll(page, 1200, 1000)
    await asyncio.sleep(7)

    # Scroll to final CTA
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(5)

    # Hover over Register button
    register_btn = await page.query_selector('.register-btn, #register-org-btn, a:has-text("Register")')
    if register_btn:
        box = await register_btn.bounding_box()
        if box:
            await smooth_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(3)

    recorder.stop_recording()
    logger.info("✅ Slide 13 complete")
