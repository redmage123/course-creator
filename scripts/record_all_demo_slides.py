#!/usr/bin/env python3
"""
Record ALL demo video slides (6-20) with proper authentication.

Uses Playwright's built-in video recording (headless) + ffmpeg conversion.
Each slide creates a fresh browser context, logs in as the appropriate role,
and navigates within the SPA.

USAGE:
    python3 scripts/record_all_demo_slides.py
    python3 scripts/record_all_demo_slides.py --slides 6 7 8
"""

import asyncio
import subprocess
import sys
import os
import argparse
import shutil
from pathlib import Path
import logging

from playwright.async_api import async_playwright

BASE_URL = "https://localhost:3000"
RESOLUTION = (1920, 1080)
VIDEOS_DIR = Path("/home/bbrelin/course-creator/frontend-react/public/demo/videos")
TEMP_DIR = Path("/tmp/pw_demo_videos")

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

DEMO_USERS = {
    'org_admin': {'email': 'orgadmin@example.com', 'password': 'password123'},
    'instructor': {'email': 'instructor@example.com', 'password': 'password123'},
    'student': {'email': 'student@example.com', 'password': 'password123'},
}


def get_duration(path):
    try:
        out = subprocess.check_output(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)],
            stderr=subprocess.DEVNULL
        )
        return float(out.strip())
    except:
        return 0.0


def convert_webm_to_mp4(webm_path, mp4_path):
    """Convert Playwright's WebM output to H.264 MP4."""
    subprocess.run([
        'ffmpeg', '-y', '-i', str(webm_path),
        '-vcodec', 'libx264', '-preset', 'fast', '-pix_fmt', 'yuv420p',
        '-crf', '23', '-movflags', '+faststart',
        str(mp4_path)
    ], capture_output=True)
    if mp4_path.exists():
        dur = get_duration(mp4_path)
        size_mb = mp4_path.stat().st_size / (1024 * 1024)
        logger.info(f"  -> {mp4_path.name} ({dur:.1f}s, {size_mb:.1f}MB)")
        return True
    return False


async def smooth_scroll(page, target_y, duration_ms=1200):
    try:
        await page.evaluate("""
            ({target, duration}) => new Promise(resolve => {
                const start = window.pageYOffset;
                const distance = target - start;
                const startTime = performance.now();
                function ease(t) { return t < 0.5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3)/2; }
                function step() {
                    const elapsed = performance.now() - startTime;
                    const progress = Math.min(elapsed / duration, 1);
                    window.scrollTo(0, start + distance * ease(progress));
                    if (progress < 1) requestAnimationFrame(step); else resolve();
                }
                step();
            })
        """, {'target': target_y, 'duration': duration_ms})
        await asyncio.sleep(duration_ms / 1000 + 0.3)
    except:
        await page.evaluate(f"window.scrollTo(0, {target_y})")
        await asyncio.sleep(1)


async def dismiss_popups(page):
    """Dismiss welcome popup and other overlays using React-safe clicks."""
    for text in ["Maybe Later", "Don't show again", "Close", "Dismiss"]:
        try:
            btn = page.locator(f'button:has-text("{text}")').first
            if await btn.is_visible(timeout=800):
                await btn.click()
                await asyncio.sleep(0.5)
        except:
            pass


async def spa_navigate(page, path):
    """Navigate within the SPA without full page reload."""
    await page.evaluate(f"""
        () => {{
            window.history.pushState({{}}, '', '{path}');
            window.dispatchEvent(new PopStateEvent('popstate'));
        }}
    """)
    await asyncio.sleep(2)
    await dismiss_popups(page)


async def create_recording_context(browser):
    """Create a new browser context with video recording enabled."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    context = await browser.new_context(
        viewport={'width': RESOLUTION[0], 'height': RESOLUTION[1]},
        ignore_https_errors=True,
        record_video_dir=str(TEMP_DIR),
        record_video_size={'width': RESOLUTION[0], 'height': RESOLUTION[1]},
    )
    return context


async def login_and_navigate(page, role, target_path):
    """Login via form, dismiss popups, and SPA-navigate to target."""
    user = DEMO_USERS[role]
    logger.info(f"  Login as {role} ({user['email']})")

    await page.goto(f"{BASE_URL}/login", wait_until='networkidle', timeout=30000)
    await asyncio.sleep(1)

    email_input = page.locator('input[placeholder*="example.com"]').first
    try:
        await email_input.wait_for(state='visible', timeout=5000)
    except:
        email_input = page.locator('input:not([type="password"]):not([type="hidden"]):not([type="checkbox"])').first
        await email_input.wait_for(state='visible', timeout=5000)

    await email_input.fill(user['email'])
    await asyncio.sleep(0.3)
    await page.locator('input[type="password"]').first.fill(user['password'])
    await asyncio.sleep(0.3)
    await page.locator('button[type="submit"]').first.click()

    try:
        await page.wait_for_url(lambda url: 'login' not in url, timeout=15000)
        logger.info(f"  Logged in -> {page.url}")
    except:
        logger.warning(f"  Login may have failed, on: {page.url}")

    await asyncio.sleep(2)
    await dismiss_popups(page)

    # SPA navigate to target if not already there
    if target_path not in page.url:
        await spa_navigate(page, target_path)

    await asyncio.sleep(1)


# ============================================================================
# SLIDE RECORDING FUNCTIONS
# Each returns the webm path for conversion
# ============================================================================

async def record_slide_06(browser):
    """Slide 6: Adding Instructors — org_admin → /organization/members"""
    context = await create_recording_context(browser)
    page = await context.new_page()
    await login_and_navigate(page, 'org_admin', '/organization/members')

    # Show members page
    await asyncio.sleep(5)
    await smooth_scroll(page, 300)
    await asyncio.sleep(5)

    # Try clicking Add Member
    try:
        btn = page.locator('button:has-text("Add"), button:has-text("Invite")').first
        if await btn.is_visible(timeout=2000):
            await btn.click()
            await asyncio.sleep(3)
    except:
        pass

    await smooth_scroll(page, 600)
    await asyncio.sleep(5)
    await smooth_scroll(page, 0)
    await asyncio.sleep(4)

    # Navigate to trainers
    await spa_navigate(page, '/organization/trainers')
    await asyncio.sleep(5)

    video_path = await page.video.path()
    await context.close()
    return video_path


async def record_slide_07(browser):
    """Slide 7: Instructor Dashboard — instructor → /dashboard/instructor"""
    context = await create_recording_context(browser)
    page = await context.new_page()
    await login_and_navigate(page, 'instructor', '/dashboard/instructor')

    await asyncio.sleep(8)
    await smooth_scroll(page, 400)
    await asyncio.sleep(7)
    await smooth_scroll(page, 800)
    await asyncio.sleep(7)
    await smooth_scroll(page, 0)
    await asyncio.sleep(5)

    # Navigate to programs
    await spa_navigate(page, '/instructor/programs')
    await asyncio.sleep(7)

    video_path = await page.video.path()
    await context.close()
    return video_path


async def record_slide_08(browser):
    """Slide 8: Course Content Creation — instructor → /instructor/content-generator"""
    context = await create_recording_context(browser)
    page = await context.new_page()
    await login_and_navigate(page, 'instructor', '/instructor/content-generator')

    await asyncio.sleep(7)
    await smooth_scroll(page, 300)
    await asyncio.sleep(6)

    # Try typing in form
    try:
        textarea = page.locator('textarea, input[type="text"]:not([placeholder*="example"])').first
        if await textarea.is_visible(timeout=2000):
            await textarea.click()
            await asyncio.sleep(0.5)
            await textarea.type("Introduction to Python Data Structures", delay=50)
            await asyncio.sleep(3)
    except:
        pass

    await smooth_scroll(page, 600)
    await asyncio.sleep(6)
    await smooth_scroll(page, 900)
    await asyncio.sleep(6)
    await smooth_scroll(page, 0)
    await asyncio.sleep(6)

    video_path = await page.video.path()
    await context.close()
    return video_path


async def record_slide_09(browser):
    """Slide 9: Student Enrollment — instructor → /instructor/students"""
    context = await create_recording_context(browser)
    page = await context.new_page()
    await login_and_navigate(page, 'instructor', '/instructor/students')

    await asyncio.sleep(6)

    await spa_navigate(page, '/instructor/students/enroll')
    await asyncio.sleep(6)
    await smooth_scroll(page, 300)
    await asyncio.sleep(5)

    await spa_navigate(page, '/instructor/students/bulk-enroll')
    await asyncio.sleep(6)
    await smooth_scroll(page, 400)
    await asyncio.sleep(5)
    await smooth_scroll(page, 0)
    await asyncio.sleep(4)

    await spa_navigate(page, '/instructor/students')
    await asyncio.sleep(5)

    video_path = await page.video.path()
    await context.close()
    return video_path


async def record_slide_10(browser):
    """Slide 10: Student Dashboard — student → /dashboard/student"""
    context = await create_recording_context(browser)
    page = await context.new_page()
    await login_and_navigate(page, 'student', '/dashboard/student')

    await asyncio.sleep(7)
    await smooth_scroll(page, 350)
    await asyncio.sleep(6)
    await smooth_scroll(page, 700)
    await asyncio.sleep(6)
    await smooth_scroll(page, 0)
    await asyncio.sleep(6)

    video_path = await page.video.path()
    await context.close()
    return video_path


async def record_slide_11(browser):
    """Slide 11: Course Browsing & Labs — student → /courses/my-courses"""
    context = await create_recording_context(browser)
    page = await context.new_page()
    await login_and_navigate(page, 'student', '/courses/my-courses')

    await asyncio.sleep(7)
    await smooth_scroll(page, 400)
    await asyncio.sleep(5)

    try:
        card = page.locator('[class*="card"], [class*="course"]').first
        if await card.is_visible(timeout=2000):
            await card.hover()
            await asyncio.sleep(2)
    except:
        pass

    await spa_navigate(page, '/labs')
    await asyncio.sleep(6)
    await smooth_scroll(page, 300)
    await asyncio.sleep(5)
    await smooth_scroll(page, 0)
    await asyncio.sleep(5)

    video_path = await page.video.path()
    await context.close()
    return video_path


async def record_slide_12(browser):
    """Slide 12: Quiz & Assessment — student → /quizzes"""
    context = await create_recording_context(browser)
    page = await context.new_page()
    await login_and_navigate(page, 'student', '/quizzes')

    await asyncio.sleep(7)
    await smooth_scroll(page, 350)
    await asyncio.sleep(6)

    await spa_navigate(page, '/quizzes/history')
    await asyncio.sleep(6)
    await smooth_scroll(page, 300)
    await asyncio.sleep(5)
    await smooth_scroll(page, 0)
    await asyncio.sleep(5)

    video_path = await page.video.path()
    await context.close()
    return video_path


async def record_slide_13(browser):
    """Slide 13: Student Progress — student → /progress"""
    context = await create_recording_context(browser)
    page = await context.new_page()
    await login_and_navigate(page, 'student', '/progress')

    await asyncio.sleep(7)
    await smooth_scroll(page, 400)
    await asyncio.sleep(6)
    await smooth_scroll(page, 700)
    await asyncio.sleep(5)
    await smooth_scroll(page, 0)
    await asyncio.sleep(4)

    await spa_navigate(page, '/certificates')
    await asyncio.sleep(5)

    video_path = await page.video.path()
    await context.close()
    return video_path


async def record_slide_14(browser):
    """Slide 14: Instructor Analytics — instructor → /instructor/analytics"""
    context = await create_recording_context(browser)
    page = await context.new_page()
    await login_and_navigate(page, 'instructor', '/instructor/analytics')

    await asyncio.sleep(8)
    await smooth_scroll(page, 400)
    await asyncio.sleep(7)
    await smooth_scroll(page, 800)
    await asyncio.sleep(7)
    await smooth_scroll(page, 1100)
    await asyncio.sleep(7)
    await smooth_scroll(page, 0)
    await asyncio.sleep(7)

    video_path = await page.video.path()
    await context.close()
    return video_path


async def record_slide_15(browser):
    """Slide 15: Learning Analytics — student → /learning-analytics"""
    context = await create_recording_context(browser)
    page = await context.new_page()
    await login_and_navigate(page, 'student', '/learning-analytics')

    await asyncio.sleep(8)
    await smooth_scroll(page, 400)
    await asyncio.sleep(8)
    await smooth_scroll(page, 800)
    await asyncio.sleep(8)
    await smooth_scroll(page, 1200)
    await asyncio.sleep(8)
    await smooth_scroll(page, 0)
    await asyncio.sleep(8)

    video_path = await page.video.path()
    await context.close()
    return video_path


async def record_slide_16(browser):
    """Slide 16: Instructor Insights — instructor → /instructor/programs (insights crashes)"""
    context = await create_recording_context(browser)
    page = await context.new_page()
    # /instructor/insights crashes, so show programs + analytics as alternative
    await login_and_navigate(page, 'instructor', '/instructor/programs')

    await asyncio.sleep(8)
    await smooth_scroll(page, 400)
    await asyncio.sleep(7)

    await spa_navigate(page, '/instructor/analytics')
    await asyncio.sleep(8)
    await smooth_scroll(page, 400)
    await asyncio.sleep(7)
    await smooth_scroll(page, 800)
    await asyncio.sleep(7)
    await smooth_scroll(page, 0)
    await asyncio.sleep(7)

    video_path = await page.video.path()
    await context.close()
    return video_path


async def record_slide_17(browser):
    """Slide 17: Integrations — org_admin → /organization/integrations"""
    context = await create_recording_context(browser)
    page = await context.new_page()
    await login_and_navigate(page, 'org_admin', '/organization/integrations')

    await asyncio.sleep(7)
    await smooth_scroll(page, 300)
    await asyncio.sleep(7)
    await smooth_scroll(page, 600)
    await asyncio.sleep(7)
    await smooth_scroll(page, 900)
    await asyncio.sleep(7)
    await smooth_scroll(page, 1200)
    await asyncio.sleep(7)
    await smooth_scroll(page, 0)
    await asyncio.sleep(7)

    video_path = await page.video.path()
    await context.close()
    return video_path


async def record_slide_18(browser):
    """Slide 18: Accessibility — show settings/password + org settings as alternatives
    since /settings/accessibility crashes with ErrorBoundary"""
    context = await create_recording_context(browser)
    page = await context.new_page()
    # Show password settings as user security/accessibility feature
    await login_and_navigate(page, 'student', '/settings/password')

    await asyncio.sleep(7)
    await smooth_scroll(page, 300)
    await asyncio.sleep(7)
    await smooth_scroll(page, 0)
    await asyncio.sleep(5)

    # Navigate to student dashboard to show keyboard shortcuts button
    await spa_navigate(page, '/dashboard/student')
    await asyncio.sleep(7)

    # Try clicking keyboard shortcuts button
    try:
        shortcuts_btn = page.locator('button:has-text("Shortcuts"), [aria-label*="shortcut"]').first
        if await shortcuts_btn.is_visible(timeout=2000):
            await shortcuts_btn.click()
            await asyncio.sleep(4)
    except:
        pass

    await smooth_scroll(page, 400)
    await asyncio.sleep(5)
    await smooth_scroll(page, 0)
    await asyncio.sleep(5)

    video_path = await page.video.path()
    await context.close()
    return video_path


async def record_slide_19(browser):
    """Slide 19: Mobile Experience — student in mobile viewport"""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    context = await browser.new_context(
        viewport={'width': 390, 'height': 844},
        ignore_https_errors=True,
        record_video_dir=str(TEMP_DIR),
        record_video_size={'width': 390, 'height': 844},
    )
    page = await context.new_page()
    await login_and_navigate(page, 'student', '/dashboard/student')

    await asyncio.sleep(8)
    await smooth_scroll(page, 400, 800)
    await asyncio.sleep(7)

    await spa_navigate(page, '/courses/my-courses')
    await asyncio.sleep(6)
    await smooth_scroll(page, 300, 800)
    await asyncio.sleep(6)

    await spa_navigate(page, '/progress')
    await asyncio.sleep(6)
    await smooth_scroll(page, 200, 800)
    await asyncio.sleep(6)

    await spa_navigate(page, '/dashboard/student')
    await asyncio.sleep(6)

    video_path = await page.video.path()
    await context.close()
    return video_path


async def record_slide_20(browser):
    """Slide 20: Summary / CTA — homepage scroll"""
    context = await create_recording_context(browser)
    page = await context.new_page()

    await page.goto(f"{BASE_URL}/", wait_until='networkidle', timeout=30000)
    await asyncio.sleep(3)
    await dismiss_popups(page)

    await asyncio.sleep(8)
    await smooth_scroll(page, 600, 2000)
    await asyncio.sleep(7)
    await smooth_scroll(page, 1200, 2000)
    await asyncio.sleep(7)
    await smooth_scroll(page, 1800, 2000)
    await asyncio.sleep(7)
    await smooth_scroll(page, 2400, 2000)
    await asyncio.sleep(7)
    await smooth_scroll(page, 0, 2500)
    await asyncio.sleep(8)

    try:
        btn = page.locator('a:has-text("Create Account"), a:has-text("Register"), a:has-text("Get Started")').first
        if await btn.is_visible(timeout=2000):
            await btn.hover()
            await asyncio.sleep(3)
    except:
        pass

    video_path = await page.video.path()
    await context.close()
    return video_path


# ============================================================================
# MAIN
# ============================================================================

SLIDE_FUNCS = {
    6: ("Adding Instructors", record_slide_06, "slide_06_adding_instructors.mp4"),
    7: ("Instructor Dashboard", record_slide_07, "slide_07_instructor_dashboard.mp4"),
    8: ("Course Content Creation", record_slide_08, "slide_08_course_content.mp4"),
    9: ("Student Enrollment", record_slide_09, "slide_09_enroll_students.mp4"),
    10: ("Student Dashboard", record_slide_10, "slide_10_student_dashboard.mp4"),
    11: ("Course Browsing & Labs", record_slide_11, "slide_11_course_browsing.mp4"),
    12: ("Quiz & Assessment", record_slide_12, "slide_12_quiz_assessment.mp4"),
    13: ("Student Progress", record_slide_13, "slide_13_student_progress.mp4"),
    14: ("Instructor Analytics", record_slide_14, "slide_14_instructor_analytics.mp4"),
    15: ("Learning Analytics", record_slide_15, "slide_15_learning_analytics.mp4"),
    16: ("Instructor Insights", record_slide_16, "slide_16_instructor_insights.mp4"),
    17: ("Integrations", record_slide_17, "slide_17_integrations.mp4"),
    18: ("Accessibility Settings", record_slide_18, "slide_18_accessibility.mp4"),
    19: ("Mobile Experience", record_slide_19, "slide_19_mobile.mp4"),
    20: ("Summary / CTA", record_slide_20, "slide_15_summary.mp4"),
}


async def main(slide_nums=None):
    if slide_nums is None:
        slide_nums = sorted(SLIDE_FUNCS.keys())

    print("=" * 70)
    print(f"RECORDING {len(slide_nums)} DEMO SLIDES (Playwright video)")
    print(f"  Output: {VIDEOS_DIR}")
    print(f"  Resolution: {RESOLUTION[0]}x{RESOLUTION[1]}")
    print(f"  Slides: {slide_nums}")
    print("=" * 70)

    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    # Clean temp dir
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--ignore-certificate-errors']
        )

        results = {}
        for num in slide_nums:
            if num not in SLIDE_FUNCS:
                logger.warning(f"  Unknown slide {num}, skipping")
                continue

            title, func, output_name = SLIDE_FUNCS[num]
            print(f"\n{'='*60}")
            print(f"  Slide {num}: {title}")
            print(f"{'='*60}")

            try:
                webm_path = await func(browser)
                mp4_path = VIDEOS_DIR / output_name
                if convert_webm_to_mp4(webm_path, mp4_path):
                    results[num] = 'OK'
                else:
                    results[num] = 'FAIL: conversion'
            except Exception as e:
                logger.error(f"  FAILED slide {num}: {e}")
                results[num] = f'FAIL: {e}'

        await browser.close()

    # Clean temp files
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)

    print("\n" + "=" * 70)
    print("RECORDING RESULTS")
    print("=" * 70)
    for num in slide_nums:
        status = results.get(num, 'SKIPPED')
        title = SLIDE_FUNCS.get(num, ("?",))[0]
        print(f"  Slide {num:2d} ({title:30s}): {status}")

    print("\nGenerated files:")
    for f in sorted(VIDEOS_DIR.glob("slide_*.mp4")):
        dur = get_duration(f)
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  {f.name:50s} {dur:6.1f}s  {size_mb:6.1f}MB")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--slides', nargs='+', type=int, help='Specific slides to record')
    args = parser.parse_args()
    asyncio.run(main(args.slides))
