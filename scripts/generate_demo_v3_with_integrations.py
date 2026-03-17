#!/usr/bin/env python3
"""
Demo Video Generation v3.0 - With Third Party Integrations
===========================================================

Generates all 14 demo slides including NEW Slide 5: Third Party Integrations

NEW in v3.0:
- Slide 5: Meeting Rooms & Notifications (60s)
- Shows Teams, Zoom, Slack integration
- Demonstrates bulk room creation
- Shows organization-wide notifications

Duration: ~10 minutes total
Output: 14 H.264 videos (1920x1080 @ 30fps)
"""

import asyncio
import subprocess
import sys
import os
import json
from pathlib import Path
import logging
import random

sys.path.insert(0, '/home/bbrelin/course-creator')

from playwright.async_api import async_playwright

# Configuration
BASE_URL = "https://localhost:3000"
RESOLUTION = (1920, 1080)
VIDEOS_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/videos")
FRAME_RATE = 30

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Demo credentials - Using E2E test credentials that work
DEMO_USERS = {
    'org_admin': {'email': 'orgadmin@e2etest.com', 'password': 'org_admin_password'},
    'instructor': {'email': 'demo.instructor@example.com', 'password': 'DemoPass123!'},
    'student': {'email': 'demo.student@example.com', 'password': 'DemoPass123!'}
}

class FFmpegRecorder:
    """H.264 screen recorder using FFmpeg"""

    def __init__(self):
        self.process = None
        self.output_file = None

    def start_recording(self, output_file):
        """Start FFmpeg screen recording"""
        self.output_file = output_file

        cmd = [
            'ffmpeg',
            '-f', 'x11grab',
            '-video_size', f'{RESOLUTION[0]}x{RESOLUTION[1]}',
            '-framerate', str(FRAME_RATE),
            '-i', ':99',  # DISPLAY :99
            '-vcodec', 'libx264',
            '-preset', 'medium',
            '-pix_fmt', 'yuv420p',
            '-crf', '23',
            '-y',
            str(output_file)
        ]

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        logger.info(f"🎥 Recording: {output_file.name}")
        return True

    def stop_recording(self):
        """Stop FFmpeg recording"""
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
            else:
                logger.error(f"   File not created: {self.output_file}")
                return False
        return False

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def remove_privacy_banners(page):
    """Remove privacy/cookie consent banners"""
    try:
        await page.evaluate("""
            () => {
                const selectors = [
                    '[class*="privacy"]',
                    '[class*="cookie"]',
                    '[class*="consent"]',
                    '[class*="gdpr"]',
                    '[id*="privacy"]',
                    '[id*="cookie"]'
                ];
                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => el.remove());
                });
            }
        """)
        await asyncio.sleep(0.5)
    except Exception as e:
        logger.debug(f"Privacy banner removal: {e}")

async def smooth_scroll(page, target_y, duration_ms=1000):
    """Smooth animated scroll to position"""
    try:
        await page.evaluate(f"""
            ({{ target, duration }}) => {{
                return new Promise((resolve) => {{
                    const start = window.pageYOffset;
                    const distance = target - start;
                    const startTime = performance.now();

                    function easeInOutCubic(t) {{
                        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
                    }}

                    function scroll() {{
                        const now = performance.now();
                        const elapsed = now - startTime;
                        const progress = Math.min(elapsed / duration, 1);
                        const eased = easeInOutCubic(progress);

                        window.scrollTo(0, start + distance * eased);

                        if (progress < 1) {{
                            requestAnimationFrame(scroll);
                        }} else {{
                            resolve();
                        }}
                    }}

                    scroll();
                }});
            }}
        """, {'target': target_y, 'duration': duration_ms})
        await asyncio.sleep(duration_ms / 1000 + 0.2)
    except Exception as e:
        logger.debug(f"Scroll error: {e}")
        await page.evaluate(f"window.scrollTo(0, {target_y});")
        await asyncio.sleep(1)

async def login_as(page, role):
    """Login as specific role with proper redirect handling"""
    user = DEMO_USERS[role]
    logger.info(f"🔐 Logging in as {role}: {user['email']}")

    try:
        # Simple approach that works
        await page.goto(f"{BASE_URL}/html/student-login.html",
                       wait_until='networkidle',
                       timeout=30000)
        await asyncio.sleep(2)

        # Fill login form
        await page.fill('#email', user['email'])
        await page.fill('#password', user['password'])

        # Click submit
        submit_btn = await page.query_selector('button[type="submit"]')
        if submit_btn:
            await submit_btn.click()

            # Wait for URL to change
            try:
                await page.wait_for_url(lambda url: 'dashboard' in url, timeout=10000)
                logger.info(f"✅ Logged in as {role}, redirected to: {page.url}")
                await asyncio.sleep(3)  # Wait for dashboard to initialize
            except Exception as e:
                logger.error(f"❌ Redirect failed: {e}")
                logger.error(f"   Current URL: {page.url}")
                await asyncio.sleep(3)
        else:
            logger.error(f"❌ Login button not found")

    except Exception as e:
        logger.error(f"❌ Login failed: {e}")

# ============================================================================
# SLIDE GENERATION FUNCTIONS (v3.0 - 14 SLIDES)
# ============================================================================

async def slide_01_introduction(page, recorder, duration):
    """
    Slide 1: Introduction (25s)
    Show homepage with platform overview
    """
    logger.info("📺 Slide 1: Introduction")

    await page.goto(f"{BASE_URL}/html/index.html",
                   wait_until='networkidle',
                   timeout=60000)
    await remove_privacy_banners(page)
    await asyncio.sleep(2)

    recorder.start_recording(VIDEOS_DIR / "slide_01_introduction.mp4")
    await asyncio.sleep(1)

    # Show hero section
    await asyncio.sleep(4)

    # Scroll to features
    await smooth_scroll(page, 600, 1200)
    await asyncio.sleep(5)

    # Scroll to integrations/benefits
    await smooth_scroll(page, 1200, 1200)
    await asyncio.sleep(6)

    # Back to hero
    await smooth_scroll(page, 200, 1200)
    await asyncio.sleep(6)

    recorder.stop_recording()
    logger.info("✅ Slide 1 complete")

async def slide_02_org_dashboard(page, recorder, duration):
    """
    Slide 2: Organization Dashboard (45s)
    Show organization creation/management
    """
    logger.info("🏢 Slide 2: Organization Dashboard")

    # For demo purposes, show dashboard overview
    await login_as(page, 'org_admin')
    await page.goto(f"{BASE_URL}/html/org-admin-dashboard-modular.html",
                   wait_until='networkidle',
                   timeout=30000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording(VIDEOS_DIR / "slide_02_org_admin.mp4")
    await asyncio.sleep(1)

    # Show dashboard overview
    await asyncio.sleep(5)

    # Scroll through overview tab
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(8)

    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(8)

    # Scroll through stats/metrics
    await smooth_scroll(page, 1200, 1000)
    await asyncio.sleep(10)

    # Back to top
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(10)

    recorder.stop_recording()
    logger.info("✅ Slide 2 complete")

async def slide_03_projects_tracks(page, recorder, duration):
    """
    Slide 3: Projects & Tracks (30s)
    Show project and track management
    """
    logger.info("📁 Slide 3: Projects & Tracks")

    # Navigate to projects tab
    await page.click('#projects-tab')
    await asyncio.sleep(3)

    recorder.start_recording(VIDEOS_DIR / "slide_03_projects_and_tracks.mp4")
    await asyncio.sleep(1)

    # Show projects list
    await asyncio.sleep(5)

    # Scroll through projects
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(6)

    # Navigate to tracks (if exists as separate tab)
    try:
        tracks_btn = await page.query_selector('button:has-text("Tracks"), a:has-text("Tracks")')
        if tracks_btn:
            await tracks_btn.click()
            await asyncio.sleep(4)
    except:
        pass

    # Show structure
    await asyncio.sleep(6)

    # Scroll through tracks
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(6)

    recorder.stop_recording()
    logger.info("✅ Slide 3 complete")

async def slide_04_adding_instructors(page, recorder, duration):
    """
    Slide 4: Adding Instructors (30s)
    Show instructor management (updated narration teases integrations)
    """
    logger.info("👨‍🏫 Slide 4: Adding Instructors")

    # Navigate to members tab
    await page.click('#members-tab')
    await asyncio.sleep(3)

    recorder.start_recording(VIDEOS_DIR / "slide_04_adding_instructors.mp4")
    await asyncio.sleep(1)

    # Show members list
    await asyncio.sleep(5)

    # Scroll through members
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(8)

    # Show instructor roles
    await smooth_scroll(page, 700, 1000)
    await asyncio.sleep(8)

    # Back to show full list
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(6)

    recorder.stop_recording()
    logger.info("✅ Slide 4 complete")

async def slide_05_third_party_integrations(page, recorder, duration):
    """
    ✨ NEW SLIDE 5: Third Party Integrations (60s)
    Show meeting rooms & notifications integration

    Demonstrates:
    - Meeting Rooms tab navigation
    - Bulk room creation (Teams, Zoom, Slack)
    - Organization-wide notifications
    - Platform filtering
    """
    logger.info("🔗 Slide 5: Third Party Integrations (NEW)")

    # Check if we're already on a dashboard (from login redirect or previous slide)
    current_url = page.url
    if 'dashboard' not in current_url:
        # Only navigate if not already on dashboard
        logger.info("Not on dashboard, navigating to org-admin-enhanced.html...")
        await page.goto(f"{BASE_URL}/html/org-admin-enhanced.html",
                       wait_until='networkidle',
                       timeout=30000)
        await asyncio.sleep(3)
    else:
        logger.info(f"Already on dashboard: {current_url}")
        await asyncio.sleep(2)

    # Wait for dashboard to fully initialize
    try:
        # Wait for sidebar to be visible
        await page.wait_for_selector('.dashboard-sidebar', state='visible', timeout=15000)
        logger.info("Dashboard sidebar loaded")
        await asyncio.sleep(2)
    except Exception as e:
        logger.warning(f"Dashboard sidebar not visible: {e}")

    # Navigate to Meeting Rooms tab
    try:
        # Wait for tabs to be ready
        await page.wait_for_selector('#meeting-rooms-tab', state='visible', timeout=10000)
        logger.info("Meeting Rooms tab found, clicking...")

        # Click the meeting rooms tab
        await page.click('#meeting-rooms-tab')
        await asyncio.sleep(2)

        # Wait for meeting rooms content to load
        try:
            await page.wait_for_selector('#meeting-rooms-panel', state='visible', timeout=10000)
            logger.info("Meeting rooms panel loaded successfully")
            await asyncio.sleep(2)
        except Exception as panel_e:
            # Fallback: Manually show the panel using JavaScript
            logger.warning(f"Panel not visible after click, using JavaScript fallback: {panel_e}")
            await page.evaluate("""
                () => {
                    // Hide all panels
                    document.querySelectorAll('.tab-panel').forEach(panel => {
                        panel.style.display = 'none';
                        panel.setAttribute('aria-hidden', 'true');
                    });

                    // Show meeting rooms panel
                    const meetingRoomsPanel = document.getElementById('meeting-rooms-panel');
                    if (meetingRoomsPanel) {
                        meetingRoomsPanel.style.display = 'block';
                        meetingRoomsPanel.setAttribute('aria-hidden', 'false');
                    }

                    // Update tab states
                    document.querySelectorAll('.nav-tab').forEach(tab => {
                        tab.setAttribute('aria-selected', 'false');
                        tab.classList.remove('active');
                    });

                    const meetingRoomsTab = document.getElementById('meeting-rooms-tab');
                    if (meetingRoomsTab) {
                        meetingRoomsTab.setAttribute('aria-selected', 'true');
                        meetingRoomsTab.classList.add('active');
                    }
                }
            """)
            await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"Could not navigate to meeting rooms: {e}")
        # Continue anyway - recorder will capture whatever is visible

    recorder.start_recording(VIDEOS_DIR / "slide_05_third_party_integrations.mp4")
    await asyncio.sleep(1)

    # Show meeting rooms overview (5s)
    await asyncio.sleep(5)

    # Scroll to Quick Actions section (5s)
    try:
        await smooth_scroll(page, 400, 1000)
        await asyncio.sleep(4)
    except:
        await asyncio.sleep(5)

    # Highlight bulk creation buttons (10s)
    try:
        # Hover over Teams instructor button
        teams_btn = await page.query_selector('button:has-text("Create Teams Rooms")')
        if teams_btn:
            await teams_btn.hover()
            await asyncio.sleep(3)
    except:
        pass

    await asyncio.sleep(7)

    # Click bulk create button (10s)
    try:
        teams_btn = await page.query_selector('button:has-text("Create Teams Rooms for All Instructors")')
        if teams_btn:
            await teams_btn.click()
            await asyncio.sleep(2)

            # Handle confirmation alert if appears
            try:
                page.on('dialog', lambda dialog: asyncio.create_task(dialog.accept()))
                await asyncio.sleep(2)
            except:
                pass

            # Wait for success notification
            await asyncio.sleep(6)
    except Exception as e:
        logger.debug(f"Bulk create interaction: {e}")
        await asyncio.sleep(10)

    # Scroll back to top actions (5s)
    try:
        await smooth_scroll(page, 100, 800)
        await asyncio.sleep(4)
    except:
        await asyncio.sleep(5)

    # Click Send Notification button (15s)
    try:
        send_notif_btn = await page.query_selector('button:has-text("Send Notification")')
        if send_notif_btn:
            await send_notif_btn.click()
            await asyncio.sleep(3)

            # Wait for modal to appear
            await page.wait_for_selector('#sendNotificationModal', state='visible', timeout=5000)
            await asyncio.sleep(2)

            # Select notification type
            await page.select_option('#notificationType', 'organization')
            await asyncio.sleep(1)

            # Fill in title
            await page.fill('#notificationTitle', 'New Course Content Available')
            await asyncio.sleep(1)

            # Fill in message (using JavaScript due to visibility issues)
            await page.evaluate("""
                () => {
                    const textarea = document.getElementById('notificationMessage');
                    if (textarea) {
                        textarea.value = "We've just published 3 new courses in the Web Development track!";
                        textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }
            """)
            await asyncio.sleep(1)

            # Select priority
            await page.select_option('#notificationPriority', 'normal')
            await asyncio.sleep(2)

            # Hover over send button (don't click to avoid actual sending)
            send_btn = await page.query_selector('button:has-text("Send Notification")')
            if send_btn:
                await send_btn.hover()
                await asyncio.sleep(3)
    except Exception as e:
        logger.debug(f"Notification modal interaction: {e}")
        await asyncio.sleep(15)

    # Final view (5s)
    await asyncio.sleep(5)

    recorder.stop_recording()
    logger.info("✅ Slide 5 complete (NEW - Third Party Integrations)")

# Slides 6-14 are renumbered from previous 5-13
# These would be implemented following the same pattern
# For now, creating placeholders

async def slide_06_instructor_dashboard(page, recorder, duration):
    """Slide 6: Instructor Dashboard (formerly slide 5)"""
    logger.info("📊 Slide 6: Instructor Dashboard")
    # Implementation would go here
    recorder.start_recording(VIDEOS_DIR / "slide_06_instructor_dashboard.mp4")
    await asyncio.sleep(duration)
    recorder.stop_recording()
    logger.info("✅ Slide 6 complete (placeholder)")

async def slide_07_course_content(page, recorder, duration):
    """Slide 7: Course Content (formerly slide 6)"""
    logger.info("📚 Slide 7: Course Content")
    recorder.start_recording(VIDEOS_DIR / "slide_07_course_content.mp4")
    await asyncio.sleep(duration)
    recorder.stop_recording()
    logger.info("✅ Slide 7 complete (placeholder)")

async def slide_08_enroll_employees(page, recorder, duration):
    """Slide 8: Enroll Employees (formerly slide 7)"""
    logger.info("👥 Slide 8: Enroll Employees")
    recorder.start_recording(VIDEOS_DIR / "slide_08_enroll_employees.mp4")
    await asyncio.sleep(duration)
    recorder.stop_recording()
    logger.info("✅ Slide 8 complete (placeholder)")

async def slide_09_student_dashboard(page, recorder, duration):
    """Slide 9: Student Dashboard (formerly slide 8)"""
    logger.info("🎓 Slide 9: Student Dashboard")
    recorder.start_recording(VIDEOS_DIR / "slide_09_student_dashboard.mp4")
    await asyncio.sleep(duration)
    recorder.stop_recording()
    logger.info("✅ Slide 9 complete (placeholder)")

async def slide_10_course_browsing(page, recorder, duration):
    """Slide 10: Course Browsing (formerly slide 9)"""
    logger.info("🔍 Slide 10: Course Browsing")
    recorder.start_recording(VIDEOS_DIR / "slide_10_course_browsing.mp4")
    await asyncio.sleep(duration)
    recorder.stop_recording()
    logger.info("✅ Slide 10 complete (placeholder)")

async def slide_11_taking_quizzes(page, recorder, duration):
    """Slide 11: Taking Quizzes (formerly slide 10)"""
    logger.info("✍️ Slide 11: Taking Quizzes")
    recorder.start_recording(VIDEOS_DIR / "slide_11_taking_quizzes.mp4")
    await asyncio.sleep(duration)
    recorder.stop_recording()
    logger.info("✅ Slide 11 complete (placeholder)")

async def slide_12_student_progress(page, recorder, duration):
    """Slide 12: Student Progress (formerly slide 11)"""
    logger.info("📈 Slide 12: Student Progress")
    recorder.start_recording(VIDEOS_DIR / "slide_12_student_progress.mp4")
    await asyncio.sleep(duration)
    recorder.stop_recording()
    logger.info("✅ Slide 12 complete (placeholder)")

async def slide_13_instructor_analytics(page, recorder, duration):
    """Slide 13: Instructor Analytics (formerly slide 12)"""
    logger.info("📊 Slide 13: Instructor Analytics")
    recorder.start_recording(VIDEOS_DIR / "slide_13_instructor_analytics.mp4")
    await asyncio.sleep(duration)
    recorder.stop_recording()
    logger.info("✅ Slide 13 complete (placeholder)")

async def slide_14_summary_cta(page, recorder, duration):
    """Slide 14: Summary & Next Steps (formerly slide 13 - UPDATED NARRATION)"""
    logger.info("🎯 Slide 14: Summary & Call to Action")
    recorder.start_recording(VIDEOS_DIR / "slide_14_summary_and_next_steps.mp4")
    await asyncio.sleep(duration)
    recorder.stop_recording()
    logger.info("✅ Slide 14 complete (placeholder)")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    """
    Main execution flow
    Generates all 14 demo videos (v3.0) including third party integrations
    """
    print("="*80)
    print("🎬 DEMO VIDEO GENERATION v3.0 - WITH THIRD PARTY INTEGRATIONS")
    print("="*80)
    print(f"  Output Directory: {VIDEOS_DIR}")
    print(f"  Resolution: {RESOLUTION[0]}x{RESOLUTION[1]} @ {FRAME_RATE}fps")
    print(f"  Codec: H.264 (libx264)")
    print(f"  Total Slides: 14 (NEW Slide 5: Third Party Integrations)")
    print(f"  Expected Duration: ~10 minutes total")
    print("="*80)
    print()

    # Create videos directory
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    # Load slide definitions
    narrations_file = Path('/home/bbrelin/course-creator/scripts/demo_player_narrations_v3.json')
    if narrations_file.exists():
        with open(narrations_file, 'r') as f:
            slides_data = json.load(f)
    else:
        logger.warning("Narrations file not found, using defaults")
        slides_data = {'slides': [{'id': i, 'title': f'Slide {i}', 'duration': 30} for i in range(1, 15)]}

    # Map slide functions (all 14 slides)
    slide_functions = {
        1: slide_01_introduction,
        2: slide_02_org_dashboard,
        3: slide_03_projects_tracks,
        4: slide_04_adding_instructors,
        5: slide_05_third_party_integrations,  # ✨ NEW
        6: slide_06_instructor_dashboard,       # Renumbered
        7: slide_07_course_content,             # Renumbered
        8: slide_08_enroll_employees,           # Renumbered
        9: slide_09_student_dashboard,          # Renumbered
        10: slide_10_course_browsing,           # Renumbered
        11: slide_11_taking_quizzes,            # Renumbered
        12: slide_12_student_progress,          # Renumbered
        13: slide_13_instructor_analytics,      # Renumbered
        14: slide_14_summary_cta,               # Renumbered
    }

    recorder = FFmpegRecorder()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Set to True for headless
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--ignore-certificate-errors',
                '--window-position=0,0',
                f'--window-size={RESOLUTION[0]},{RESOLUTION[1]}'
            ]
        )

        context = await browser.new_context(
            viewport={'width': RESOLUTION[0], 'height': RESOLUTION[1]},
            ignore_https_errors=True
        )

        page = await context.new_page()

        # Generate slides (start with first 5 including new integration slide)
        slides_to_generate = slides_data['slides'][:5]  # Change to [:14] for all

        for slide_data in slides_to_generate:
            slide_id = slide_data['id']
            title = slide_data['title']
            duration = slide_data['duration']

            if slide_id not in slide_functions:
                logger.warning(f"⚠️  Slide {slide_id} not yet implemented, skipping")
                continue

            print(f"\n{'='*80}")
            print(f"🎥 SLIDE {slide_id}/14: {title}")
            print(f"   Duration Target: {duration}s")
            if slide_id == 5:
                print(f"   ✨ NEW SLIDE: Third Party Integrations")
            print(f"{'='*80}")

            try:
                slide_func = slide_functions[slide_id]
                await slide_func(page, recorder, duration)

                # Verify output
                await asyncio.sleep(2)
                video_file = VIDEOS_DIR / f"slide_{str(slide_id).zfill(2)}*.mp4"
                video_files = list(VIDEOS_DIR.glob(f"slide_{str(slide_id).zfill(2)}*.mp4"))

                if video_files:
                    video_file = video_files[0]
                    size_mb = video_file.stat().st_size / (1024 * 1024)

                    # Get actual duration
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
                        print(f"   ⚠️  Duration mismatch: {actual_duration - duration:+.1f}s")
                else:
                    print(f"\n❌ FAILED - Video file not created")

            except Exception as e:
                print(f"\n❌ ERROR: {e}")
                logger.exception("Slide generation failed")

            # Pause between slides
            print(f"\n{'='*80}")
            await asyncio.sleep(3)

        await context.close()
        await browser.close()

    print("\n" + "="*80)
    print("✅ DEMO GENERATION COMPLETE (v3.0)")
    print("="*80)
    print(f"\nVideos saved to: {VIDEOS_DIR}")
    print(f"\n✨ NEW: Slide 5 - Third Party Integrations generated")
    print("\nNext Steps:")
    print("1. Review generated videos")
    print("2. Update demo-player.html with 14 slides")
    print("3. Test complete demo playthrough")
    print("\nView demo at: https://localhost:3000/html/demo-player.html")

if __name__ == "__main__":
    asyncio.run(main())
