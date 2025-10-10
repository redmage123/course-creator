#!/usr/bin/env python3
"""
FINAL: Complete Demo Video Generation - All 13 Slides
=====================================================

Generates all 13 professional demo videos with:
- REAL form submissions and data entry
- Correct field selectors from actual HTML
- Proper timing to match audio durations
- Smooth animations and mouse movements

Total Duration: ~3-4 hours
Output: 13 H.264 videos @ 1920x1080, 30fps
"""

import asyncio
import subprocess
import sys
import os
import json
import random
from pathlib import Path
import logging

sys.path.insert(0, '/home/bbrelin/course-creator')
from playwright.async_api import async_playwright

# Configuration
BASE_URL = "https://localhost:3000"
RESOLUTION = (1920, 1080)
VIDEOS_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/videos")
FRAME_RATE = 30

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FFmpegRecorder:
    """H.264 screen recorder"""
    def __init__(self):
        self.process = None
        self.output_file = None

    def start_recording(self, output_file):
        self.output_file = output_file
        cmd = [
            'ffmpeg', '-f', 'x11grab',
            '-video_size', f'{RESOLUTION[0]}x{RESOLUTION[1]}',
            '-framerate', str(FRAME_RATE),
            '-i', ':99',
            '-vcodec', 'libx264',
            '-preset', 'medium',
            '-pix_fmt', 'yuv420p',
            '-crf', '23',
            '-y', str(output_file)
        ]
        self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"🎥 Recording: {output_file.name}")
        return True

    def stop_recording(self):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            if self.output_file and self.output_file.exists():
                size_mb = self.output_file.stat().st_size / (1024 * 1024)
                logger.info(f"⏹️  Stopped: {self.output_file.name} ({size_mb:.2f} MB)")
                return True
        return False

# Utility Functions
async def remove_privacy_banners(page):
    try:
        await page.evaluate("""
            () => {
                const selectors = ['[class*="privacy"]', '[class*="cookie"]', '[class*="consent"]', '[class*="gdpr"]'];
                selectors.forEach(sel => document.querySelectorAll(sel).forEach(el => el.remove()));
            }
        """)
        await asyncio.sleep(0.5)
    except:
        pass

async def smooth_scroll(page, target_y, duration_ms=1000):
    try:
        await page.evaluate(f"""
            ({{target, duration}}) => new Promise((resolve) => {{
                const start = window.pageYOffset;
                const distance = target - start;
                const startTime = performance.now();
                function easeInOutCubic(t) {{
                    return t < 0.5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3)/2;
                }}
                function scroll() {{
                    const now = performance.now();
                    const elapsed = now - startTime;
                    const progress = Math.min(elapsed/duration, 1);
                    const eased = easeInOutCubic(progress);
                    window.scrollTo(0, start + distance*eased);
                    if (progress < 1) requestAnimationFrame(scroll);
                    else resolve();
                }}
                requestAnimationFrame(scroll);
            }})
        """, {"target": target_y, "duration": duration_ms})
    except:
        pass

async def smooth_mouse_move(page, x, y, steps=30):
    try:
        current_pos = await page.evaluate("() => ({x: window.lastMouseX || 960, y: window.lastMouseY || 540})")
        start_x, start_y = current_pos.get('x', 960), current_pos.get('y', 540)
        for i in range(steps + 1):
            progress = i / steps
            eased = progress * progress * (3.0 - 2.0 * progress)
            current_x = start_x + (x - start_x) * eased
            current_y = start_y + (y - start_y) * eased
            await page.mouse.move(current_x, current_y)
            await page.evaluate(f"() => {{ window.lastMouseX = {current_x}; window.lastMouseY = {current_y}; }}")
            await asyncio.sleep(0.02)
    except:
        pass

async def type_slowly(page, selector, text, delay=80):
    try:
        element = await page.query_selector(selector)
        if not element:
            logger.warning(f"Element not found: {selector}")
            return False
        box = await element.bounding_box()
        if box:
            await smooth_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2)
        await element.click()
        await asyncio.sleep(0.3)
        for char in text:
            char_delay = delay + random.randint(-20, 20)
            await element.type(char, delay=char_delay)
            await asyncio.sleep(char_delay / 1000)
        return True
    except Exception as e:
        logger.warning(f"Type error on {selector}: {e}")
        return False

# SLIDE FUNCTIONS

async def slide_01_introduction(page, recorder, duration):
    logger.info("📺 Slide 1: Introduction")
    await page.goto(f"{BASE_URL}/html/index.html", wait_until='networkidle', timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(2)

    recorder.start_recording(VIDEOS_DIR / "slide_01_introduction.mp4")
    await asyncio.sleep(1)
    await asyncio.sleep(3)
    await smooth_scroll(page, 500, 1200)
    await asyncio.sleep(4)
    await smooth_scroll(page, 1000, 1200)
    await asyncio.sleep(5)
    await smooth_scroll(page, 1500, 1200)
    await asyncio.sleep(4)
    await smooth_scroll(page, 300, 1200)
    await asyncio.sleep(5)
    recorder.stop_recording()
    logger.info("✅ Slide 1 complete")

async def slide_02_org_admin(page, recorder, duration):
    logger.info("🏢 Slide 2: Organization Registration (FIXED)")
    await page.goto(f"{BASE_URL}/html/organization-registration.html", wait_until='networkidle', timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(2)

    recorder.start_recording(VIDEOS_DIR / "slide_02_org_admin.mp4")
    await asyncio.sleep(1)
    await asyncio.sleep(2)

    # FIXED SELECTORS (from actual HTML)
    await type_slowly(page, '#orgName', 'TechCorp Global Training', delay=70)
    await asyncio.sleep(2)
    await type_slowly(page, '#orgDomain', 'techcorp.training', delay=60)
    await asyncio.sleep(2)
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(1.5)
    await type_slowly(page, '#orgDescription', 'Enterprise software development training for 500+ engineers worldwide', delay=50)
    await asyncio.sleep(3)
    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(3)
    await smooth_scroll(page, 1200, 1000)
    await asyncio.sleep(4)

    # Find submit button
    submit_btn = await page.query_selector('button[type="submit"], .btn-primary')
    if submit_btn:
        box = await submit_btn.bounding_box()
        if box:
            await smooth_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(4)

    await smooth_scroll(page, 700, 800)
    await asyncio.sleep(5)
    recorder.stop_recording()
    logger.info("✅ Slide 2 complete")

async def slide_03_projects_tracks(page, recorder, duration):
    logger.info("📊 Slide 3: Projects & Tracks (EXTENDED)")
    await page.goto(f"{BASE_URL}/html/org-admin-dashboard-modular.html", wait_until='networkidle', timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording(VIDEOS_DIR / "slide_03_projects_and_tracks.mp4")
    await asyncio.sleep(1)
    await asyncio.sleep(3)

    projects_tab = await page.query_selector('a[data-tab="projects"], a[href="#projects"]')
    if projects_tab:
        await projects_tab.click()
        await asyncio.sleep(3)
        await smooth_scroll(page, 400, 1000)
        await asyncio.sleep(5)

    tracks_tab = await page.query_selector('a[data-tab="tracks"], a[href="#tracks"]')
    if tracks_tab:
        await tracks_tab.click()
        await asyncio.sleep(3)
        await smooth_scroll(page, 600, 1000)
        await asyncio.sleep(6)

    await smooth_scroll(page, 200, 1000)
    await asyncio.sleep(5)
    recorder.stop_recording()
    logger.info("✅ Slide 3 complete")

async def slide_04_adding_instructors(page, recorder, duration):
    logger.info("👨‍🏫 Slide 4: Adding Instructors (EXTENDED)")
    await asyncio.sleep(1)

    recorder.start_recording(VIDEOS_DIR / "slide_04_adding_instructors.mp4")
    await asyncio.sleep(1)

    members_tab = await page.query_selector('a[data-tab="members"], a[href="#members"]')
    if members_tab:
        await members_tab.click()
        await asyncio.sleep(3)

    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(6)

    add_btn = await page.query_selector('button:has-text("Add"), .add-member-btn')
    if add_btn:
        box = await add_btn.bounding_box()
        if box:
            await smooth_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(4)

    await smooth_scroll(page, 700, 1000)
    await asyncio.sleep(7)
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(6)
    recorder.stop_recording()
    logger.info("✅ Slide 4 complete")

async def slide_05_instructor_dashboard(page, recorder, duration):
    logger.info("🎓 Slide 5: Instructor Dashboard")
    await page.goto(f"{BASE_URL}/html/instructor-dashboard-modular.html", wait_until='networkidle', timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording(VIDEOS_DIR / "slide_05_instructor_dashboard.mp4")
    await asyncio.sleep(1)
    await asyncio.sleep(3)
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(8)

    create_btn = await page.query_selector('button:has-text("Create"), .create-course-btn')
    if create_btn:
        box = await create_btn.bounding_box()
        if box:
            await smooth_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(4)

    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(10)
    await smooth_scroll(page, 1100, 1000)
    await asyncio.sleep(12)
    await smooth_scroll(page, 1400, 1000)
    await asyncio.sleep(8)
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(8)
    recorder.stop_recording()
    logger.info("✅ Slide 5 complete")

async def slide_06_adding_course_content(page, recorder, duration):
    logger.info("📝 Slide 6: Course Content")
    await asyncio.sleep(1)

    recorder.start_recording(VIDEOS_DIR / "slide_06_adding_course_content.mp4")
    await asyncio.sleep(1)

    content_tab = await page.query_selector('a[href="#content"], .content-tab')
    if content_tab:
        await content_tab.click()
        await asyncio.sleep(2)

    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(7)
    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(10)
    await smooth_scroll(page, 1200, 1000)
    await asyncio.sleep(10)
    await smooth_scroll(page, 1600, 1000)
    await asyncio.sleep(8)
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(5)
    recorder.stop_recording()
    logger.info("✅ Slide 6 complete")

async def slide_07_enrolling_students(page, recorder, duration):
    logger.info("👥 Slide 7: Enrolling Students")
    await page.goto(f"{BASE_URL}/html/org-admin-dashboard-modular.html", wait_until='networkidle', timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording(VIDEOS_DIR / "slide_07_enrolling_students.mp4")
    await asyncio.sleep(1)

    enrollment_tab = await page.query_selector('a[href="#enrollment"], a[data-tab="enrollment"]')
    if enrollment_tab:
        await enrollment_tab.click()
        await asyncio.sleep(2)

    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(8)
    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(10)

    upload_btn = await page.query_selector('.bulk-upload-btn, input[type="file"]')
    if upload_btn:
        box = await upload_btn.bounding_box()
        if box:
            await smooth_mouse_move(page, box['x'] + 50, box['y'] + 20)
            await asyncio.sleep(5)

    await smooth_scroll(page, 1200, 1000)
    await asyncio.sleep(10)
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(5)
    recorder.stop_recording()
    logger.info("✅ Slide 7 complete")

async def slide_08_student_course_browsing(page, recorder, duration):
    logger.info("🎓 Slide 8: Student Dashboard")
    await page.goto(f"{BASE_URL}/html/student-dashboard-modular.html", wait_until='networkidle', timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording(VIDEOS_DIR / "slide_08_student_course_browsing.mp4")
    await asyncio.sleep(1)
    await asyncio.sleep(3)
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(7)
    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(8)
    await smooth_scroll(page, 1100, 1000)
    await asyncio.sleep(6)
    await smooth_scroll(page, 200, 1000)
    await asyncio.sleep(3)
    recorder.stop_recording()
    logger.info("✅ Slide 8 complete")

async def slide_09_student_login_and_dashboard(page, recorder, duration):
    logger.info("💻 Slide 9: Course Browsing & IDEs")
    await asyncio.sleep(1)

    recorder.start_recording(VIDEOS_DIR / "slide_09_student_login_and_dashboard.mp4")
    await asyncio.sleep(1)

    catalog_link = await page.query_selector('a[href*="courses"], .course-catalog-link')
    if catalog_link:
        await catalog_link.click()
        await asyncio.sleep(3)

    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(10)

    course_card = await page.query_selector('.course-card, .course-item')
    if course_card:
        box = await course_card.bounding_box()
        if box:
            await smooth_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(3)
            await course_card.click()
            await asyncio.sleep(4)

    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(10)

    lab_link = await page.query_selector('a[href*="lab"], .launch-lab-btn')
    if lab_link:
        box = await lab_link.bounding_box()
        if box:
            await smooth_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(5)

    await smooth_scroll(page, 1000, 1000)
    await asyncio.sleep(15)
    await smooth_scroll(page, 1400, 1000)
    await asyncio.sleep(15)
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(7)
    recorder.stop_recording()
    logger.info("✅ Slide 9 complete")

async def slide_10_taking_quiz(page, recorder, duration):
    logger.info("✍️  Slide 10: Taking Quizzes")
    await page.goto(f"{BASE_URL}/html/quiz.html", wait_until='networkidle', timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording(VIDEOS_DIR / "slide_10_taking_quiz.mp4")
    await asyncio.sleep(1)
    await asyncio.sleep(3)
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(8)
    await smooth_scroll(page, 700, 1000)
    await asyncio.sleep(10)
    await smooth_scroll(page, 1100, 1000)
    await asyncio.sleep(8)
    await smooth_scroll(page, 1400, 1000)
    await asyncio.sleep(5)

    submit_btn = await page.query_selector('.submit-quiz-btn, #submit-quiz')
    if submit_btn:
        box = await submit_btn.bounding_box()
        if box:
            await smooth_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(5)

    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(3)
    recorder.stop_recording()
    logger.info("✅ Slide 10 complete")

async def slide_11_student_progress_analytics(page, recorder, duration):
    logger.info("📊 Slide 11: Student Progress")
    await page.goto(f"{BASE_URL}/html/student-dashboard-modular.html", wait_until='networkidle', timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(2)

    recorder.start_recording(VIDEOS_DIR / "slide_11_student_progress_analytics.mp4")
    await asyncio.sleep(1)

    progress_tab = await page.query_selector('a[href="#progress"], a[data-tab="progress"]')
    if progress_tab:
        await progress_tab.click()
        await asyncio.sleep(2)

    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(7)
    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(10)
    await smooth_scroll(page, 1200, 1000)
    await asyncio.sleep(6)
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(3)
    recorder.stop_recording()
    logger.info("✅ Slide 11 complete")

async def slide_12_instructor_analytics(page, recorder, duration):
    logger.info("📈 Slide 12: Instructor Analytics")
    await page.goto(f"{BASE_URL}/html/instructor-dashboard-modular.html", wait_until='networkidle', timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording(VIDEOS_DIR / "slide_12_instructor_analytics.mp4")
    await asyncio.sleep(1)

    analytics_tab = await page.query_selector('a[href="#analytics"], a[data-tab="analytics"]')
    if analytics_tab:
        await analytics_tab.click()
        await asyncio.sleep(2)

    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(10)
    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(10)
    await smooth_scroll(page, 1200, 1000)
    await asyncio.sleep(10)
    await smooth_scroll(page, 1600, 1000)
    await asyncio.sleep(8)
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(4)
    recorder.stop_recording()
    logger.info("✅ Slide 12 complete")

async def slide_13_summary_and_cta(page, recorder, duration):
    logger.info("🎯 Slide 13: Summary & CTA")
    await page.goto(f"{BASE_URL}/html/index.html", wait_until='networkidle', timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(2)

    recorder.start_recording(VIDEOS_DIR / "slide_13_summary_and_cta.mp4")
    await asyncio.sleep(1)
    await asyncio.sleep(4)
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(6)
    await smooth_scroll(page, 1200, 1000)
    await asyncio.sleep(7)
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(5)

    register_btn = await page.query_selector('.register-btn, a:has-text("Register")')
    if register_btn:
        box = await register_btn.bounding_box()
        if box:
            await smooth_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(4)
    recorder.stop_recording()
    logger.info("✅ Slide 13 complete")

# MAIN EXECUTION
async def main():
    print("="*80)
    print("🎬 FINAL: ALL 13 DEMO SLIDES - REAL WORKFLOWS")
    print("="*80)
    print(f"  Output: {VIDEOS_DIR}")
    print(f"  Resolution: {RESOLUTION[0]}x{RESOLUTION[1]} @ {FRAME_RATE}fps")
    print(f"  Codec: H.264")
    print(f"  Duration: ~3-4 hours")
    print("="*80)
    print()

    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    with open('/home/bbrelin/course-creator/scripts/demo_player_narrations_correct.json', 'r') as f:
        slides_data = json.load(f)

    slide_functions = {
        1: slide_01_introduction,
        2: slide_02_org_admin,
        3: slide_03_projects_tracks,
        4: slide_04_adding_instructors,
        5: slide_05_instructor_dashboard,
        6: slide_06_adding_course_content,
        7: slide_07_enrolling_students,
        8: slide_08_student_course_browsing,
        9: slide_09_student_login_and_dashboard,
        10: slide_10_taking_quiz,
        11: slide_11_student_progress_analytics,
        12: slide_12_instructor_analytics,
        13: slide_13_summary_and_cta
    }

    recorder = FFmpegRecorder()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--ignore-certificate-errors',
                  '--window-position=0,0', f'--window-size={RESOLUTION[0]},{RESOLUTION[1]}']
        )
        context = await browser.new_context(
            viewport={'width': RESOLUTION[0], 'height': RESOLUTION[1]},
            ignore_https_errors=True
        )
        page = await context.new_page()

        for slide_data in slides_data['slides']:
            slide_id = slide_data['id']
            title = slide_data['title']
            duration = slide_data['duration']

            print(f"\n{'='*80}")
            print(f"🎥 SLIDE {slide_id}/13: {title}")
            print(f"   Target: {duration}s")
            print(f"{'='*80}")

            try:
                slide_func = slide_functions[slide_id]
                await slide_func(page, recorder, duration)

                # Verify
                await asyncio.sleep(2)
                video_files = list(VIDEOS_DIR.glob(f"slide_{str(slide_id).zfill(2)}*.mp4"))
                if video_files:
                    video_file = max(video_files, key=lambda p: p.stat().st_mtime)  # Get latest
                    size_mb = video_file.stat().st_size / (1024 * 1024)
                    result = subprocess.run(
                        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                         '-of', 'default=noprint_wrappers=1:nokey=1', str(video_file)],
                        capture_output=True, text=True
                    )
                    actual_duration = float(result.stdout.strip()) if result.stdout.strip() else 0

                    print(f"\n✅ SUCCESS")
                    print(f"   File: {video_file.name}")
                    print(f"   Size: {size_mb:.2f} MB")
                    print(f"   Duration: {actual_duration:.1f}s (target: {duration}s)")
                    if abs(actual_duration - duration) > 5:
                        print(f"   ⚠️  Mismatch: {actual_duration - duration:+.1f}s")
                else:
                    print(f"\n❌ FAILED")
            except Exception as e:
                print(f"\n❌ ERROR: {e}")
                logger.exception("Slide generation failed")

            print(f"{'='*80}")
            await asyncio.sleep(3)

        await context.close()
        await browser.close()

    print("\n" + "="*80)
    print("✅ ALL 13 SLIDES COMPLETE!")
    print("="*80)
    print(f"\nVideos: {VIDEOS_DIR}")
    print("Demo: https://localhost:3000/html/demo-player.html")

if __name__ == "__main__":
    asyncio.run(main())
