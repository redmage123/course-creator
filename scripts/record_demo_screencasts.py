#!/usr/bin/env python3
"""
Demo Screencast Recording with Playwright

Records screencasts of each demo slide using Playwright's built-in
video recording capability. Videos are timed to match audio narration.

USAGE:
    python3 scripts/record_demo_screencasts.py
    python3 scripts/record_demo_screencasts.py --slide 2
"""

import asyncio
import os
import sys
import time
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright

# Configuration
BASE_URL = os.getenv('TEST_BASE_URL', 'https://localhost:3000')
VIDEO_DIR = Path('frontend-react/public/demo/videos')
AUDIO_DIR = Path('frontend-react/public/demo/audio')

# Demo credentials
ORG_ADMIN_EMAIL = 'sarah@acmelearning.edu'
ORG_ADMIN_PASSWORD = 'SecurePass123!'

# Slide definitions with durations = audio length + 2 second buffer
# Videos should be 1-2 seconds LONGER than audio to prevent audio cutoff
VIDEO_BUFFER_SECONDS = 2.0

SLIDES = [
    # Durations = audio length + buffer for smooth playback
    {'id': 1, 'filename': 'slide_01_platform_introduction.mp4', 'duration': 15.83 + VIDEO_BUFFER_SECONDS + 2.5, 'title': 'Platform Introduction'},  # Extra 2.5s buffer for slide 1 audio
    {'id': 2, 'filename': 'slide_02_organization_registration.mp4', 'duration': 25.94 + VIDEO_BUFFER_SECONDS + 8.0, 'title': 'Organization Registration'},  # Extra 8s for full form with submit
    {'id': 3, 'filename': 'slide_03_organization_admin_dashboard.mp4', 'duration': 81.21 + VIDEO_BUFFER_SECONDS, 'title': 'Organization Admin Dashboard'},
    {'id': 4, 'filename': 'slide_04_creating_training_tracks.mp4', 'duration': 41.40 + VIDEO_BUFFER_SECONDS, 'title': 'Creating Training Tracks'},
    {'id': 5, 'filename': 'slide_05_ai_assistant.mp4', 'duration': 47.23 + VIDEO_BUFFER_SECONDS, 'title': 'AI Assistant'},
    {'id': 6, 'filename': 'slide_06_adding_instructors.mp4', 'duration': 18.83 + VIDEO_BUFFER_SECONDS, 'title': 'Adding Instructors'},
    {'id': 7, 'filename': 'slide_07_instructor_dashboard.mp4', 'duration': 31.48 + VIDEO_BUFFER_SECONDS, 'title': 'Instructor Dashboard'},
    {'id': 8, 'filename': 'slide_08_course_content.mp4', 'duration': 35.84 + VIDEO_BUFFER_SECONDS, 'title': 'Course Content Generation'},
    {'id': 9, 'filename': 'slide_09_enroll_students.mp4', 'duration': 22.23 + VIDEO_BUFFER_SECONDS, 'title': 'Student Enrollment'},
    {'id': 10, 'filename': 'slide_10_student_dashboard.mp4', 'duration': 17.79 + VIDEO_BUFFER_SECONDS, 'title': 'Student Dashboard'},
    {'id': 11, 'filename': 'slide_11_course_browsing.mp4', 'duration': 34.51 + VIDEO_BUFFER_SECONDS, 'title': 'Course Browsing & Labs'},
    {'id': 12, 'filename': 'slide_12_quiz_assessment.mp4', 'duration': 27.53 + VIDEO_BUFFER_SECONDS, 'title': 'Quiz & Assessment'},
    {'id': 13, 'filename': 'slide_13_student_progress.mp4', 'duration': 20.30 + VIDEO_BUFFER_SECONDS, 'title': 'Student Progress'},
    {'id': 14, 'filename': 'slide_14_instructor_analytics.mp4', 'duration': 34.22 + VIDEO_BUFFER_SECONDS, 'title': 'Instructor Analytics'},
    {'id': 15, 'filename': 'slide_15_summary.mp4', 'duration': 26.28 + VIDEO_BUFFER_SECONDS, 'title': 'Summary & Next Steps'},
]


async def type_slowly(page, selector, text, delay=80):
    """Type text character by character for visual effect"""
    element = page.locator(selector)
    await element.click()
    for char in text:
        await element.type(char, delay=delay)


async def apply_enhanced_visibility(page, zoom_level=1.4):
    """
    Apply enhanced visibility settings to the page for better demo recording.
    - Zooms in for better readability
    - Increases contrast and font sizes
    - Adds visual borders and shadows for clarity
    - Uses inline styles that persist through React re-renders
    """
    # Wait for page to be fully loaded
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(0.5)

    # Apply zoom
    await page.evaluate(f"document.body.style.zoom = '{zoom_level}'")

    # Apply inline styles to html, body, and React root that persist through re-renders
    await page.evaluate("""
        // Apply persistent blue background via inline styles
        document.documentElement.style.cssText = 'background: linear-gradient(135deg, #1a365d 0%, #2563eb 50%, #3b82f6 100%) !important; min-height: 100vh !important;';
        document.body.style.background = 'transparent';
        document.body.style.minHeight = '100vh';

        // Make React root element transparent so background shows through
        const root = document.getElementById('root');
        if (root) {
            root.style.background = 'transparent';
            root.style.minHeight = '100vh';
        }

        // Create a persistent background overlay that sits behind everything
        if (!document.getElementById('demo-bg-overlay')) {
            const overlay = document.createElement('div');
            overlay.id = 'demo-bg-overlay';
            overlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: linear-gradient(135deg, #1a365d 0%, #2563eb 50%, #3b82f6 100%); z-index: -9999; pointer-events: none;';
            document.body.insertBefore(overlay, document.body.firstChild);
        }

        // Also ensure main app wrapper backgrounds are transparent
        const appWrappers = document.querySelectorAll('[class*="App"], [class*="app"], [class*="Layout"], [class*="layout"], [class*="Wrapper"], [class*="wrapper"]');
        appWrappers.forEach(el => {
            if (el.style) el.style.background = 'transparent';
        });
    """)

    # Inject CSS for better contrast and readability across ALL pages
    await page.add_style_tag(content="""
        /* ENHANCED VISIBILITY FOR DEMO RECORDINGS */

        /* Better background contrast - Blue gradient for visibility */
        html {
            background: linear-gradient(135deg, #1a365d 0%, #2563eb 50%, #3b82f6 100%) !important;
            min-height: 100vh !important;
        }

        body {
            background: transparent !important;
            min-height: 100vh !important;
        }

        /* Make React root and app wrappers transparent */
        #root, [class*="App"], [class*="app-"], [class*="Layout"], [class*="layout-"],
        [class*="Wrapper"], [class*="wrapper-"], [class*="Page"][class*="container"] {
            background: transparent !important;
        }

        /* Main content areas - white boxes on blue background */
        main, .main,
        .card, [class*="card"], [class*="Card"],
        .panel, [class*="panel"], [class*="Panel"],
        .dashboard, [class*="dashboard"], [class*="Dashboard"],
        [class*="content"], [class*="Content"] {
            background: white !important;
            border: 2px solid #444 !important;
            border-radius: 12px !important;
            box-shadow: 0 6px 24px rgba(0,0,0,0.25) !important;
            margin: 10px !important;
        }

        /* Forms and inputs - larger and more visible */
        form, .form, [class*="form"], [class*="Form"] {
            background: white !important;
            border: 3px solid #333 !important;
            border-radius: 12px !important;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3) !important;
            padding: 20px !important;
        }

        input, textarea, select {
            font-size: 16px !important;
            padding: 12px !important;
            border: 2px solid #555 !important;
            border-radius: 6px !important;
            background: #fff !important;
            color: #000 !important;
        }

        input:focus, textarea:focus, select:focus {
            border-color: #0066cc !important;
            box-shadow: 0 0 0 4px rgba(0,102,204,0.3) !important;
            outline: none !important;
        }

        /* Labels - bolder and clearer */
        label, .label, [class*="label"], [class*="Label"] {
            font-size: 15px !important;
            font-weight: 600 !important;
            color: #222 !important;
        }

        /* Buttons - larger and more prominent */
        button, [type="submit"], [type="button"], .btn, [class*="btn"], [class*="Btn"], [class*="button"], [class*="Button"] {
            font-size: 16px !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            border: 2px solid #333 !important;
            border-radius: 8px !important;
        }

        /* Headers and titles - larger */
        h1, h2, h3, h4, .title, [class*="title"], [class*="Title"],
        .heading, [class*="heading"], [class*="Heading"] {
            font-size: 24px !important;
            color: #111 !important;
            font-weight: 700 !important;
        }

        h1 { font-size: 32px !important; }
        h2 { font-size: 26px !important; }
        h3 { font-size: 22px !important; }

        /* Text content - more readable */
        p, span, div, li, td, th {
            font-size: 15px !important;
            color: #222 !important;
            line-height: 1.5 !important;
        }

        /* Navigation elements */
        nav, .nav, [class*="nav"], [class*="Nav"],
        .sidebar, [class*="sidebar"], [class*="Sidebar"],
        .menu, [class*="menu"], [class*="Menu"] {
            background: #f5f5f5 !important;
            border: 2px solid #ccc !important;
        }

        nav a, .nav a, [class*="nav"] a {
            font-size: 15px !important;
            font-weight: 500 !important;
            padding: 10px 16px !important;
        }

        /* Tabs */
        [role="tab"], .tab, [class*="tab"], [class*="Tab"] {
            font-size: 15px !important;
            font-weight: 600 !important;
            padding: 12px 20px !important;
        }

        /* Tables */
        table {
            border: 2px solid #444 !important;
        }
        th, td {
            border: 1px solid #666 !important;
            padding: 12px !important;
        }
        th {
            background: #e0e0e0 !important;
            font-weight: 700 !important;
        }

        /* Modal/Dialog */
        [role="dialog"], .modal, [class*="modal"], [class*="Modal"],
        .dialog, [class*="dialog"], [class*="Dialog"] {
            border: 3px solid #333 !important;
            box-shadow: 0 12px 48px rgba(0,0,0,0.4) !important;
        }

        /* Links */
        a {
            color: #0055cc !important;
            font-weight: 500 !important;
        }

        /* Icons - make them larger */
        svg, .icon, [class*="icon"], [class*="Icon"] {
            transform: scale(1.2);
        }
    """)
    await asyncio.sleep(0.3)


async def smooth_scroll(page, target_y, duration_ms=1000):
    """Smooth scroll to target Y position"""
    await page.evaluate(f"""
        window.scrollTo({{
            top: {target_y},
            behavior: 'smooth'
        }});
    """)
    await asyncio.sleep(duration_ms / 1000)


async def try_click(page, selectors, timeout_ms=2000):
    """
    Try to click any of the given selectors with a short timeout.
    Returns True if successful, False otherwise.
    This prevents 30-second default timeouts on non-existent elements.
    """
    for selector in selectors:
        try:
            element = page.locator(selector).first
            await element.click(timeout=timeout_ms)
            return True
        except:
            continue
    return False


async def try_fill(page, selectors, text, timeout_ms=2000, delay=100):
    """
    Try to fill any of the given selectors with a short timeout.
    Returns True if successful, False otherwise.

    Uses slower typing (delay=100ms) to ensure text entry is visible in recordings.
    """
    for selector in selectors:
        try:
            element = page.locator(selector).first
            # Wait for element to be visible
            await element.wait_for(state='visible', timeout=timeout_ms)
            # Click to focus
            await element.click(timeout=timeout_ms)
            await asyncio.sleep(0.3)  # Pause after click for visibility
            # Clear the field first
            await element.fill('')
            await asyncio.sleep(0.2)
            # Type character by character with visible delay
            for char in text:
                await element.type(char, delay=delay)
            await asyncio.sleep(0.3)  # Pause after typing to show completed text
            print(f"    Filled '{selector}' with '{text}'")
            return True
        except Exception as e:
            print(f"    Failed to fill '{selector}': {e}")
            continue
    return False


async def record_slide_01(page, slide):
    """Slide 1: Platform Introduction - Homepage tour"""
    print(f"  Recording: {slide['title']} ({slide['duration']}s)")

    # Navigate and wait for content to be visible BEFORE starting timer
    await page.goto(BASE_URL)
    await page.wait_for_load_state('networkidle')

    # Wait for main content to be visible (hero section)
    try:
        await page.locator('h1, [class*="hero"], [class*="Hero"], main').first.wait_for(state='visible', timeout=5000)
    except:
        pass  # Continue even if specific element not found

    # Apply styling
    await apply_enhanced_visibility(page, zoom_level=1.3)
    await asyncio.sleep(0.5)

    # NOW start the timer - content is visible
    start_time = time.time()
    target_duration = slide['duration']

    # Show hero section
    await asyncio.sleep(2.5)

    # Scroll through features
    await smooth_scroll(page, 300, 800)
    await asyncio.sleep(2)

    await smooth_scroll(page, 600, 800)
    await asyncio.sleep(2)

    # Scroll back to top
    await smooth_scroll(page, 0, 500)
    await asyncio.sleep(1)

    # Wait precisely for remaining time
    elapsed = time.time() - start_time
    remaining = target_duration - elapsed - 0.3
    if remaining > 0:
        await asyncio.sleep(remaining)


async def record_slide_02(page, slide):
    """Slide 2: Organization Registration - SYNCED WITH NARRATION

    Narration (25.94s):
    "To get started, simply click Register Organization on the home page. [0-4s]
     Now, let's fill in the details. [4-6s]
     Enter your organization name, website, and a brief description. [6-12s]
     Add your contact information, including business email and address. [12-17s]
     Finally, set up your administrator account with credentials. [17-22s]
     Click submit, and there you go! [22-24s]
     Your organization is successfully registered. Next, we'll show you how to create projects." [24-26s]
    """
    print(f"  Recording: {slide['title']} ({slide['duration']}s)")

    # Navigate and wait for form to be visible BEFORE starting timer
    await page.goto(f"{BASE_URL}/organization/register")
    await page.wait_for_load_state('networkidle')

    # Wait for form to be visible
    try:
        await page.locator('form, input[name="name"]').first.wait_for(state='visible', timeout=5000)
    except:
        pass

    # Apply styling
    await apply_enhanced_visibility(page, zoom_level=1.4)
    await asyncio.sleep(0.3)

    # Helper to wait until a specific time point
    async def wait_until(target_time):
        elapsed = time.time() - start_time
        if target_time > elapsed:
            await asyncio.sleep(target_time - elapsed)

    # START TIMER - synced with narration
    start_time = time.time()
    target_duration = slide['duration']

    # 0-4s: "To get started, simply click Register Organization..."
    # Form is already shown, just display it
    await asyncio.sleep(4)

    # 4-6s: "Now, let's fill in the details"
    # Show form, prepare for typing
    await asyncio.sleep(2)

    # 6-12s: "Enter your organization name, website, and a brief description"
    # 6-8s: Organization name
    await try_fill(page, ['input[name="name"]'], "Acme Training Corp", timeout_ms=2000, delay=60)

    # 8-10s: Website/domain
    await wait_until(8)
    await try_fill(page, ['input[name="domain"]'], "acmetraining.com", timeout_ms=1500, delay=60)

    # 10-12s: Scroll to show description area if exists, or slug
    await wait_until(10)
    await try_fill(page, ['input[name="slug"]'], "acme-training", timeout_ms=1500, delay=60)

    # 12-17s: "Add your contact information, including business email and address"
    await wait_until(12)
    await smooth_scroll(page, 300, 400)
    await try_fill(page, ['input[name="contact_email"]'], "contact@acmetraining.com", timeout_ms=1500, delay=50)

    # 17-22s: "Finally, set up your administrator account with credentials"
    await wait_until(17)
    await smooth_scroll(page, 500, 400)
    await try_fill(page, ['input[name="admin_full_name"]'], "John Smith", timeout_ms=1500, delay=50)
    await wait_until(18.5)
    await try_fill(page, ['input[name="admin_username"]'], "jsmith", timeout_ms=1500, delay=50)
    await wait_until(19.5)
    await try_fill(page, ['input[name="admin_email"]'], "john@acmetraining.com", timeout_ms=1500, delay=50)
    await wait_until(20.5)
    await smooth_scroll(page, 700, 300)
    await try_fill(page, ['input[name="admin_password"]'], "SecurePass123!", timeout_ms=1500, delay=40)
    await wait_until(21.5)
    await try_fill(page, ['input[name="admin_password_confirm"]'], "SecurePass123!", timeout_ms=1500, delay=40)

    # 22-24s: "Click submit, and there you go!"
    await wait_until(22)
    await smooth_scroll(page, 900, 300)
    try:
        submit_btn = page.locator('button[type="submit"], button:has-text("Register"), button:has-text("Submit"), button:has-text("Create")').first
        await submit_btn.click(timeout=2000)
        print("    Clicked submit button")
    except Exception as e:
        print(f"    Submit button not found: {e}")

    # 24-26s: "Your organization is successfully registered..."
    await wait_until(24)
    await asyncio.sleep(2)  # Show success/redirect

    # Wait for remaining duration
    await wait_until(target_duration - 0.3)


async def record_slide_03(page, slide):
    """Slide 3: Organization Admin Dashboard - Show dashboard features

    React frontend uses card-based layout with Link buttons, NOT tabs.
    Total duration: 81 seconds (matching audio)
    """
    print(f"  Recording: {slide['title']} ({slide['duration']}s)")
    start_time = time.time()
    target_duration = slide['duration']

    # Navigate directly to org admin dashboard
    await page.goto(f"{BASE_URL}/dashboard/org-admin")
    await asyncio.sleep(1)
    await apply_enhanced_visibility(page, zoom_level=1.3)
    await asyncio.sleep(2)

    # Show dashboard overview - stats cards
    await asyncio.sleep(3)

    # Scroll down to show management cards
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(4)

    # Click "Manage Members" button
    if await try_click(page, [
        'a[href="/organization/members"]',
        'button:has-text("Manage Members")'
    ], timeout_ms=1000):
        await asyncio.sleep(3)
        await page.goto(f"{BASE_URL}/dashboard/org-admin")
        await asyncio.sleep(2)

    # Scroll to Training Programs section
    await smooth_scroll(page, 500, 1000)
    await asyncio.sleep(4)

    # Click "Manage Tracks" button
    if await try_click(page, [
        'a[href="/organization/tracks"]',
        'button:has-text("Manage Tracks")'
    ], timeout_ms=1000):
        await asyncio.sleep(3)
        await page.goto(f"{BASE_URL}/dashboard/org-admin")
        await asyncio.sleep(2)

    # Scroll to Import & AI section
    await smooth_scroll(page, 700, 1000)
    await asyncio.sleep(4)

    # Show Import Template button
    if await try_click(page, [
        'button[data-action="import"]',
        'a[href="/organization/import"]'
    ], timeout_ms=1000):
        await asyncio.sleep(2)
        await page.goto(f"{BASE_URL}/dashboard/org-admin")
        await asyncio.sleep(2)

    # Scroll to Analytics section
    await smooth_scroll(page, 900, 1000)
    await asyncio.sleep(4)

    # Show View Reports
    if await try_click(page, [
        'a[href="/organization/analytics"]',
        'button:has-text("View Reports")'
    ], timeout_ms=1000):
        await asyncio.sleep(3)
        await page.goto(f"{BASE_URL}/dashboard/org-admin")
        await asyncio.sleep(2)

    # Scroll to Settings section
    await smooth_scroll(page, 1100, 1000)
    await asyncio.sleep(4)

    # Final scroll back to top
    await smooth_scroll(page, 0, 1000)
    await asyncio.sleep(2)

    # Wait precisely for remaining time
    elapsed = time.time() - start_time
    remaining = target_duration - elapsed - 0.3  # Small buffer for video finalization
    if remaining > 0:
        await asyncio.sleep(remaining)


async def record_slide_04(page, slide):
    """Slide 4: Creating Training Tracks

    React frontend uses /organization/tracks page with track list and creation.
    Total duration: 41 seconds (matching audio)
    """
    print(f"  Recording: {slide['title']} ({slide['duration']}s)")
    start_time = time.time()
    target_duration = slide['duration']

    # Navigate directly to tracks page
    await page.goto(f"{BASE_URL}/organization/tracks")
    await asyncio.sleep(1)
    await apply_enhanced_visibility(page, zoom_level=1.4)
    await asyncio.sleep(2)

    # Show the tracks list page
    await asyncio.sleep(3)

    # Scroll to show track list
    await smooth_scroll(page, 200, 1000)
    await asyncio.sleep(3)

    # Try to click Create/Add Track button
    if await try_click(page, [
        'button:has-text("Create Track")',
        'button:has-text("New Track")',
        'button:has-text("Create")'
    ], timeout_ms=1000):
        await asyncio.sleep(2)

        # If a form appears, try to fill it
        await try_fill(page, [
            'input[name="name"]',
            'input[name="trackName"]'
        ], 'Python Fundamentals', delay=80)
        await asyncio.sleep(1)

        # Try description
        await try_fill(page, [
            'textarea[name="description"]',
            'textarea'
        ], 'Learn Python basics for data science', delay=30)
        await asyncio.sleep(1)

        # Close modal/form
        await page.keyboard.press('Escape')

    # Show more of the tracks page
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(3)

    # Scroll back to top
    await smooth_scroll(page, 0, 800)
    await asyncio.sleep(2)

    # Wait precisely for remaining time
    elapsed = time.time() - start_time
    remaining = target_duration - elapsed - 0.3  # Small buffer for video finalization
    if remaining > 0:
        await asyncio.sleep(remaining)


async def record_slide_05(page, slide):
    """Slide 5: AI Assistant - Show AI content generation features

    The React frontend has AI content generation via /instructor/content-generator
    and AI Auto Create Project on org-admin dashboard.
    Total duration: 47 seconds (matching audio)
    """
    print(f"  Recording: {slide['title']} ({slide['duration']}s)")
    start_time = time.time()
    target_duration = slide['duration']

    # Navigate to org admin to show AI features
    await page.goto(f"{BASE_URL}/dashboard/org-admin")
    await asyncio.sleep(1)
    await apply_enhanced_visibility(page, zoom_level=1.4)
    await asyncio.sleep(2)

    # Scroll to Import & AI section
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(3)

    # Click AI Auto Create Project button
    if await try_click(page, [
        'button[data-action="ai-create-project"]',
        'a[href="/organization/ai-create"]'
    ], timeout_ms=1000):
        await asyncio.sleep(3)
        await page.goto(f"{BASE_URL}/dashboard/org-admin")
        await asyncio.sleep(1)

    # Now show the instructor's AI content generator
    await page.goto(f"{BASE_URL}/instructor/content-generator")
    await asyncio.sleep(2)
    await apply_enhanced_visibility(page, zoom_level=1.4)
    await asyncio.sleep(2)

    # Show the content generation interface
    await smooth_scroll(page, 200, 1000)
    await asyncio.sleep(4)

    # Try to click Generate Content button
    if await try_click(page, [
        'button[data-action="generate"]',
        'button:has-text("Generate")'
    ], timeout_ms=1000):
        await asyncio.sleep(3)

    # Scroll to show more options
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(4)

    # Show Create Quiz option
    if await try_click(page, [
        'button[data-action="create-quiz"]',
        'button:has-text("Create Quiz")'
    ], timeout_ms=1000):
        await asyncio.sleep(2)

    # Scroll back to top
    await smooth_scroll(page, 0, 800)
    await asyncio.sleep(2)

    # Wait precisely for remaining time
    elapsed = time.time() - start_time
    remaining = target_duration - elapsed - 0.3  # Small buffer for video finalization
    if remaining > 0:
        await asyncio.sleep(remaining)


async def record_slide_06(page, slide):
    """Slide 6: Adding Instructors - Show trainer management

    React frontend uses /organization/trainers page for trainer management.
    Total duration: 19 seconds (matching audio)
    """
    print(f"  Recording: {slide['title']} ({slide['duration']}s)")
    start_time = time.time()
    target_duration = slide['duration']

    # Navigate directly to trainers page
    await page.goto(f"{BASE_URL}/organization/trainers")
    await asyncio.sleep(1)
    await apply_enhanced_visibility(page, zoom_level=1.4)
    await asyncio.sleep(1)

    # Show the trainers list
    await asyncio.sleep(3)

    # Scroll to show trainer list
    await smooth_scroll(page, 200, 800)
    await asyncio.sleep(2)

    # Try to click Add/Invite button (quick timeout)
    if await try_click(page, [
        'button:has-text("Add Trainer")',
        'button:has-text("Invite")',
        'button:has-text("Add")'
    ], timeout_ms=1000):
        await asyncio.sleep(1)
        await page.keyboard.press('Escape')

    # Scroll back to top
    await smooth_scroll(page, 0, 800)
    await asyncio.sleep(1)

    # Wait precisely for remaining time
    elapsed = time.time() - start_time
    remaining = target_duration - elapsed - 0.3  # Small buffer for video finalization  # -1 for buffer
    if remaining > 0:
        await asyncio.sleep(remaining)


async def record_slide_07(page, slide):
    """Slide 7: Instructor Dashboard - Show corporate trainer dashboard

    React frontend uses card-based layout, NOT tabs.
    Total duration: 32 seconds (matching audio)
    """
    print(f"  Recording: {slide['title']} ({slide['duration']}s)")
    start_time = time.time()
    target_duration = slide['duration']

    await page.goto(f"{BASE_URL}/instructor")
    await asyncio.sleep(1)
    await apply_enhanced_visibility(page, zoom_level=1.3)
    await asyncio.sleep(2)

    # Show dashboard overview - welcome and stats
    await asyncio.sleep(3)

    # Scroll to show Training Programs card
    await smooth_scroll(page, 250, 1000)
    await asyncio.sleep(3)

    # Click "Manage Programs" button
    if await try_click(page, [
        'a[href="/instructor/programs"]',
        'button:has-text("Manage Programs")'
    ], timeout_ms=1000):
        await asyncio.sleep(2)
        await page.goto(f"{BASE_URL}/instructor")
        await asyncio.sleep(1)

    # Scroll to Student Enrollment card
    await smooth_scroll(page, 450, 1000)
    await asyncio.sleep(3)

    # Click "Manage Students" button
    if await try_click(page, [
        'a[href="/instructor/students"]',
        'button:has-text("Manage Students")'
    ], timeout_ms=1000):
        await asyncio.sleep(2)
        await page.goto(f"{BASE_URL}/instructor")
        await asyncio.sleep(1)

    # Scroll back to show full dashboard
    await smooth_scroll(page, 0, 1000)
    await asyncio.sleep(2)

    # Wait precisely for remaining time
    elapsed = time.time() - start_time
    remaining = target_duration - elapsed - 0.3  # Small buffer for video finalization
    if remaining > 0:
        await asyncio.sleep(remaining)


async def record_slide_08(page, slide):
    """Slide 8: Course Content Generation - Show AI content generation

    React frontend has /instructor/content-generator page.
    Total duration: 36 seconds (matching audio)
    """
    print(f"  Recording: {slide['title']} ({slide['duration']}s)")
    start_time = time.time()
    target_duration = slide['duration']

    # Navigate directly to content generator
    await page.goto(f"{BASE_URL}/instructor/content-generator")
    await asyncio.sleep(1)
    await apply_enhanced_visibility(page, zoom_level=1.4)
    await asyncio.sleep(2)

    # Show the content generation interface
    await asyncio.sleep(3)

    # Scroll to show options
    await smooth_scroll(page, 200, 1000)
    await asyncio.sleep(3)

    # Click Generate Content button
    if await try_click(page, [
        'button[data-action="generate"]',
        'button:has-text("Generate")'
    ], timeout_ms=1000):
        await asyncio.sleep(2)

    # Scroll to show more content options
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(3)

    # Show Create Slides option
    if await try_click(page, [
        'button[data-action="create-slides"]',
        'button:has-text("Create Slides")'
    ], timeout_ms=1000):
        await asyncio.sleep(2)

    # Scroll back to top
    await smooth_scroll(page, 0, 800)
    await asyncio.sleep(2)

    # Wait precisely for remaining time
    elapsed = time.time() - start_time
    remaining = target_duration - elapsed - 0.3  # Small buffer for video finalization
    if remaining > 0:
        await asyncio.sleep(remaining)


async def record_slide_09(page, slide):
    """Slide 9: Student Enrollment - Show bulk enrollment

    React frontend has /instructor/students and /instructor/students/bulk-enroll pages.
    Total duration: 22 seconds (matching audio)
    """
    print(f"  Recording: {slide['title']} ({slide['duration']}s)")
    start_time = time.time()
    target_duration = slide['duration']

    # Navigate directly to student management
    await page.goto(f"{BASE_URL}/instructor/students")
    await asyncio.sleep(1)
    await apply_enhanced_visibility(page, zoom_level=1.4)
    await asyncio.sleep(2)

    # Show the students list
    await asyncio.sleep(2)

    # Scroll to show student list
    await smooth_scroll(page, 200, 800)
    await asyncio.sleep(2)

    # Click bulk enroll button
    if await try_click(page, [
        'button[data-action="bulk-enroll"]',
        'a[href*="bulk-enroll"]',
        'button:has-text("Bulk")'
    ], timeout_ms=1000):
        await asyncio.sleep(2)

    # Scroll back to top
    await smooth_scroll(page, 0, 800)
    await asyncio.sleep(1)

    # Wait precisely for remaining time
    elapsed = time.time() - start_time
    remaining = target_duration - elapsed - 0.3  # Small buffer for video finalization
    if remaining > 0:
        await asyncio.sleep(remaining)


async def record_slide_10(page, slide):
    """Slide 10: Student Dashboard"""
    print(f"  Recording: {slide['title']} ({slide['duration']}s)")
    start_time = time.time()
    target_duration = slide['duration']

    await page.goto(f"{BASE_URL}/student")
    await asyncio.sleep(1)
    await apply_enhanced_visibility(page, zoom_level=1.4)
    await asyncio.sleep(1)

    # Show dashboard
    await smooth_scroll(page, 200, 500)
    await asyncio.sleep(2)

    await smooth_scroll(page, 400, 500)
    await asyncio.sleep(2)

    await smooth_scroll(page, 0, 500)
    await asyncio.sleep(1)

    # Wait precisely for remaining time
    elapsed = time.time() - start_time
    remaining = target_duration - elapsed - 0.3
    if remaining > 0:
        await asyncio.sleep(remaining)


async def record_slide_11(page, slide):
    """Slide 11: Course Browsing & Labs"""
    print(f"  Recording: {slide['title']} ({slide['duration']}s)")
    start_time = time.time()
    target_duration = slide['duration']

    await page.goto(f"{BASE_URL}/courses")
    await asyncio.sleep(1)
    await apply_enhanced_visibility(page, zoom_level=1.4)
    await asyncio.sleep(1)

    # Browse courses
    await smooth_scroll(page, 300, 800)
    await asyncio.sleep(3)

    await smooth_scroll(page, 600, 800)
    await asyncio.sleep(3)

    # Click on a course (quick timeout)
    if await try_click(page, ['.course-card', '.course-item', '[data-testid="course"]'], timeout_ms=1000):
        await asyncio.sleep(2)

    # Show lab environment (quick timeout)
    if await try_click(page, ['button:has-text("Lab")', 'a[href*="lab"]', '.start-lab-btn'], timeout_ms=1000):
        await asyncio.sleep(2)

    # Scroll back
    await smooth_scroll(page, 0, 500)
    await asyncio.sleep(1)

    # Wait precisely for remaining time
    elapsed = time.time() - start_time
    remaining = target_duration - elapsed - 0.3
    if remaining > 0:
        await asyncio.sleep(remaining)


async def record_slide_12(page, slide):
    """Slide 12: Quiz & Assessment"""
    print(f"  Recording: {slide['title']} ({slide['duration']}s)")
    start_time = time.time()
    target_duration = slide['duration']

    await page.goto(f"{BASE_URL}/student")
    await asyncio.sleep(1)
    await apply_enhanced_visibility(page, zoom_level=1.4)
    await asyncio.sleep(1)

    # Navigate to quizzes (quick timeout)
    if not await try_click(page, ['a[href*="quiz"]', 'button:has-text("Quiz")', '.quiz-link'], timeout_ms=1000):
        await page.goto(f"{BASE_URL}/quiz")
        await asyncio.sleep(1)
    else:
        await asyncio.sleep(1)

    # Show quiz interface
    await smooth_scroll(page, 200, 500)
    await asyncio.sleep(2)

    await smooth_scroll(page, 400, 500)
    await asyncio.sleep(2)

    await smooth_scroll(page, 0, 500)
    await asyncio.sleep(1)

    # Wait precisely for remaining time
    elapsed = time.time() - start_time
    remaining = target_duration - elapsed - 0.3
    if remaining > 0:
        await asyncio.sleep(remaining)


async def record_slide_13(page, slide):
    """Slide 13: Student Progress"""
    print(f"  Recording: {slide['title']} ({slide['duration']}s)")
    start_time = time.time()
    target_duration = slide['duration']

    await page.goto(f"{BASE_URL}/student")
    await asyncio.sleep(1)
    await apply_enhanced_visibility(page, zoom_level=1.4)
    await asyncio.sleep(1)

    # Navigate to progress (quick timeout)
    if await try_click(page, ['a[href*="progress"]', 'button:has-text("Progress")'], timeout_ms=1000):
        await asyncio.sleep(1)

    # Show progress charts
    await smooth_scroll(page, 200, 500)
    await asyncio.sleep(2)

    await smooth_scroll(page, 400, 500)
    await asyncio.sleep(2)

    await smooth_scroll(page, 0, 500)
    await asyncio.sleep(1)

    # Wait precisely for remaining time
    elapsed = time.time() - start_time
    remaining = target_duration - elapsed - 0.3
    if remaining > 0:
        await asyncio.sleep(remaining)


async def record_slide_14(page, slide):
    """Slide 14: Instructor Analytics - Show training analytics

    React frontend has /instructor/analytics page.
    Total duration: 34 seconds (matching audio)
    """
    print(f"  Recording: {slide['title']} ({slide['duration']}s)")
    start_time = time.time()
    target_duration = slide['duration']

    # Navigate directly to analytics page
    await page.goto(f"{BASE_URL}/instructor/analytics")
    await asyncio.sleep(1)
    await apply_enhanced_visibility(page, zoom_level=1.3)
    await asyncio.sleep(2)

    # Show the analytics overview
    await asyncio.sleep(3)

    # Scroll to show charts/metrics
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(4)

    # Scroll to show more analytics
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(4)

    # Scroll to show completion rates
    await smooth_scroll(page, 900, 1000)
    await asyncio.sleep(4)

    # Scroll back to top
    await smooth_scroll(page, 0, 1000)
    await asyncio.sleep(2)

    # Wait precisely for remaining time
    elapsed = time.time() - start_time
    remaining = target_duration - elapsed - 0.3  # Small buffer for video finalization
    if remaining > 0:
        await asyncio.sleep(remaining)


async def record_slide_15(page, slide):
    """Slide 15: Summary & Next Steps"""
    print(f"  Recording: {slide['title']} ({slide['duration']}s)")
    start_time = time.time()
    target_duration = slide['duration']

    await page.goto(BASE_URL)
    await asyncio.sleep(1)
    await apply_enhanced_visibility(page, zoom_level=1.3)
    await asyncio.sleep(1)

    # Show homepage with CTA
    await smooth_scroll(page, 400, 800)
    await asyncio.sleep(3)

    await smooth_scroll(page, 800, 800)
    await asyncio.sleep(3)

    await smooth_scroll(page, 0, 500)
    await asyncio.sleep(2)

    # Wait precisely for remaining time
    elapsed = time.time() - start_time
    remaining = target_duration - elapsed - 0.3
    if remaining > 0:
        await asyncio.sleep(remaining)


# Slide recorder mapping
SLIDE_RECORDERS = {
    1: record_slide_01,
    2: record_slide_02,
    3: record_slide_03,
    4: record_slide_04,
    5: record_slide_05,
    6: record_slide_06,
    7: record_slide_07,
    8: record_slide_08,
    9: record_slide_09,
    10: record_slide_10,
    11: record_slide_11,
    12: record_slide_12,
    13: record_slide_13,
    14: record_slide_14,
    15: record_slide_15,
}


async def record_slide(slide, headless=True):
    """Record a single slide with Playwright video recording"""

    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    # Use unique temp directory per slide to avoid race conditions in parallel recording
    temp_video_dir = Path(f'/tmp/playwright-videos-slide-{slide["id"]:02d}')
    # Clean up any existing temp files from previous runs
    if temp_video_dir.exists():
        import shutil
        shutil.rmtree(temp_video_dir)
    temp_video_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=['--ignore-certificate-errors', '--disable-web-security']
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            record_video_dir=str(temp_video_dir),
            record_video_size={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )

        page = await context.new_page()

        # Get the recorder function
        recorder = SLIDE_RECORDERS.get(slide['id'])
        if recorder:
            await recorder(page, slide)
        else:
            print(f"  No recorder for slide {slide['id']}, using generic")
            await page.goto(BASE_URL)
            await asyncio.sleep(slide['duration'])

        # Close context to save video
        await context.close()
        await browser.close()

        # Find and move the recorded video
        video_files = list(temp_video_dir.glob('*.webm'))
        if video_files:
            source_video = video_files[-1]  # Most recent
            output_path = VIDEO_DIR / slide['filename']

            # Convert webm to mp4 with H.264 baseline profile for maximum browser compatibility
            # Using baseline profile, level 3.0, and faststart for web streaming
            print(f"  Converting to H.264 MP4 (baseline profile for browser compatibility)...")
            result = subprocess.run([
                'ffmpeg', '-y',
                '-i', str(source_video),
                '-c:v', 'libx264',
                '-profile:v', 'baseline',  # Most compatible profile
                '-level', '3.0',  # Wide device support
                '-preset', 'fast',
                '-crf', '23',
                '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart',  # Enable progressive download/streaming
                '-an',  # No audio (we'll sync separately)
                str(output_path)
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print(f"  Saved: {output_path.name}")
                source_video.unlink()  # Clean up temp file
            else:
                print(f"  FFmpeg error: {result.stderr[:200]}")
        else:
            print(f"  Warning: No video file generated")


async def main(slide_id=None, headless=True):
    """Main recording function"""
    print("=" * 70)
    print("DEMO SCREENCAST RECORDING WITH PLAYWRIGHT")
    print("=" * 70)
    print()
    print(f"Base URL: {BASE_URL}")
    print(f"Output: {VIDEO_DIR}")
    print(f"Headless: {headless}")
    print()

    # Determine slides to record
    if slide_id:
        slides = [s for s in SLIDES if s['id'] == slide_id]
        if not slides:
            print(f"ERROR: Slide {slide_id} not found")
            return
    else:
        slides = SLIDES

    print(f"Recording {len(slides)} slide(s)...")
    print()

    for slide in slides:
        print(f"Slide {slide['id']:02d}: {slide['title']}")
        try:
            await record_slide(slide, headless)
        except Exception as e:
            print(f"  ERROR: {e}")
        print()

    print("=" * 70)
    print("RECORDING COMPLETE")
    print("=" * 70)
    print(f"Videos saved to: {VIDEO_DIR.absolute()}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--slide', type=int, help='Record specific slide')
    parser.add_argument('--visible', action='store_true', help='Show browser (not headless)')
    args = parser.parse_args()

    asyncio.run(main(slide_id=args.slide, headless=not args.visible))
