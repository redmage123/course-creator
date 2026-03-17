#!/usr/bin/env python3
"""
Record Enhancement Demo Slides (15-19)

Records actual UI screen captures for the 5 new platform enhancement slides:
- Slide 15: Learning Analytics Dashboard (Enhancement 9)
- Slide 16: Instructor Insights Dashboard (Enhancement 10)
- Slide 17: Third-Party Integrations (Enhancement 12)
- Slide 18: Accessibility Settings (Enhancement 13)
- Slide 19: Mobile Experience (Enhancement 11)

Uses Playwright for browser automation and FFmpeg for screen recording.

USAGE:
    DISPLAY=:99 python3 scripts/record_enhancement_slides.py

REQUIREMENTS:
    - Xvfb running on DISPLAY :99
    - FFmpeg installed
    - Playwright installed
    - Frontend running on https://localhost:3000
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path
import logging
import time

sys.path.insert(0, '/home/bbrelin/course-creator')

from playwright.async_api import async_playwright

# Configuration
BASE_URL = "https://localhost:3000"
RESOLUTION = (1920, 1080)
VIDEOS_DIR = Path("/home/bbrelin/course-creator/frontend-react/public/demo/videos")
FRAME_RATE = 30

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Demo credentials - from database seed
DEMO_USERS = {
    'org_admin': {'email': 'orgadmin@example.com', 'password': 'password123'},
    'instructor': {'email': 'instructor@example.com', 'password': 'password123'},
    'student': {'email': 'student@example.com', 'password': 'password123'},
    'site_admin': {'email': 'admin@example.com', 'password': 'password123'}
}


class FFmpegRecorder:
    """H.264 screen recorder using FFmpeg"""

    def __init__(self):
        self.process = None
        self.output_file = None

    def start_recording(self, output_file, width=1920, height=1080):
        """Start FFmpeg screen recording"""
        self.output_file = output_file

        cmd = [
            'ffmpeg',
            '-f', 'x11grab',
            '-video_size', f'{width}x{height}',
            '-framerate', str(FRAME_RATE),
            '-i', os.environ.get('DISPLAY', ':99'),
            '-vcodec', 'libx264',
            '-preset', 'fast',
            '-pix_fmt', 'yuv420p',
            '-crf', '23',
            '-movflags', '+faststart',
            '-y',
            str(output_file)
        ]

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        logger.info(f"   Recording: {output_file.name}")
        return True

    def stop_recording(self):
        """Stop FFmpeg recording"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

            if self.output_file and self.output_file.exists():
                size_mb = self.output_file.stat().st_size / (1024 * 1024)
                logger.info(f"   Stopped: {self.output_file.name} ({size_mb:.2f} MB)")
                return True
            else:
                logger.error(f"   File not created: {self.output_file}")
                return False
        return False


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
    """Login as specific role using Playwright locators"""
    user = DEMO_USERS.get(role, DEMO_USERS['student'])
    logger.info(f"   Logging in as {role}: {user['email']}")

    try:
        await page.goto(f"{BASE_URL}/login", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)

        # Use Playwright locators for React form
        # Try multiple selectors for email field
        email_input = page.locator('input[type="email"]').first
        if not await email_input.is_visible():
            email_input = page.get_by_label('Email').first
        if not await email_input.is_visible():
            email_input = page.get_by_placeholder('email').first

        await email_input.fill(user['email'])
        await asyncio.sleep(0.5)

        # Try multiple selectors for password field
        password_input = page.locator('input[type="password"]').first
        if not await password_input.is_visible():
            password_input = page.get_by_label('Password').first

        await password_input.fill(user['password'])
        await asyncio.sleep(0.5)

        # Click submit button
        submit_btn = page.locator('button[type="submit"]').first
        await submit_btn.click()

        # Wait for navigation to complete
        try:
            await page.wait_for_url(lambda url: 'login' not in url, timeout=10000)
            logger.info(f"   Login successful, redirected to: {page.url}")
        except:
            logger.warning(f"   Login may have failed, still on: {page.url}")

        await asyncio.sleep(2)

    except Exception as e:
        logger.error(f"   Login failed: {e}")


async def remove_banners(page):
    """Remove privacy/cookie banners and modals"""
    try:
        await page.evaluate("""
            () => {
                // Remove privacy banners
                const selectors = [
                    '[class*="privacy"]',
                    '[class*="cookie"]',
                    '[class*="consent"]',
                    '[class*="gdpr"]',
                    '[class*="modal-backdrop"]',
                    '[class*="toast"]'
                ];
                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        if (el.style) el.style.display = 'none';
                    });
                });

                // Click accept buttons if present
                const acceptBtns = document.querySelectorAll('[class*="accept"], button:has-text("Accept")');
                acceptBtns.forEach(btn => btn.click && btn.click());
            }
        """)
    except:
        pass
    await asyncio.sleep(0.5)


async def hover_element(page, selector, description="element"):
    """Hover over an element with visual feedback"""
    try:
        element = await page.query_selector(selector)
        if element:
            await element.hover()
            await asyncio.sleep(0.5)
            logger.info(f"   Hovered: {description}")
            return True
    except Exception as e:
        logger.debug(f"   Hover failed for {description}: {e}")
    return False


async def click_element(page, selector, description="element"):
    """Click an element safely"""
    try:
        element = await page.query_selector(selector)
        if element:
            await element.click()
            await asyncio.sleep(1)
            logger.info(f"   Clicked: {description}")
            return True
    except Exception as e:
        logger.debug(f"   Click failed for {description}: {e}")
    return False


# ============================================================================
# SLIDE RECORDING FUNCTIONS
# ============================================================================

async def record_slide_15_learning_analytics(page, recorder):
    """
    Slide 15: Learning Analytics Dashboard (32 seconds)

    Shows student learning analytics with:
    - Skill mastery radar charts
    - Learning velocity metrics
    - Session activity patterns
    - Learning path progress
    """
    logger.info("="*60)
    logger.info("SLIDE 15: Learning Analytics Dashboard")
    logger.info("="*60)

    # Navigate directly to learning analytics (auth handled by React component)
    await page.goto(f"{BASE_URL}/learning-analytics", wait_until='networkidle', timeout=30000)
    await asyncio.sleep(3)
    await remove_banners(page)

    # Start recording
    recorder.start_recording(VIDEOS_DIR / "slide_15_learning_analytics.mp4")
    await asyncio.sleep(1)

    # Show overview (5s)
    await asyncio.sleep(5)

    # Scroll to skill mastery section (6s)
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(5)

    # Scroll to learning velocity (6s)
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(5)

    # Scroll to session activity (6s)
    await smooth_scroll(page, 900, 1000)
    await asyncio.sleep(5)

    # Scroll back to top for summary (6s)
    await smooth_scroll(page, 0, 1000)
    await asyncio.sleep(5)

    recorder.stop_recording()
    logger.info("Slide 15 complete")


async def record_slide_16_instructor_insights(page, recorder):
    """
    Slide 16: Instructor Insights Dashboard (35 seconds)

    Shows AI-powered teaching insights:
    - Course performance metrics
    - Student engagement widgets
    - Content effectiveness charts
    - AI recommendations
    """
    logger.info("="*60)
    logger.info("SLIDE 16: Instructor Insights Dashboard")
    logger.info("="*60)

    # Navigate directly to instructor insights
    await page.goto(f"{BASE_URL}/instructor/insights", wait_until='networkidle', timeout=30000)
    await asyncio.sleep(3)
    await remove_banners(page)

    # Start recording
    recorder.start_recording(VIDEOS_DIR / "slide_16_instructor_insights.mp4")
    await asyncio.sleep(1)

    # Show overview with metrics (6s)
    await asyncio.sleep(6)

    # Scroll to engagement section (6s)
    await smooth_scroll(page, 350, 1000)
    await asyncio.sleep(5)

    # Scroll to content effectiveness (6s)
    await smooth_scroll(page, 700, 1000)
    await asyncio.sleep(5)

    # Scroll to AI recommendations (8s)
    await smooth_scroll(page, 1000, 1000)
    await asyncio.sleep(7)

    # Scroll back to top (6s)
    await smooth_scroll(page, 0, 1000)
    await asyncio.sleep(5)

    recorder.stop_recording()
    logger.info("Slide 16 complete")


async def record_slide_17_integrations(page, recorder):
    """
    Slide 17: Third-Party Integrations (38 seconds)

    Shows integration settings:
    - Slack integration panel
    - Calendar sync options
    - OAuth connections
    - Webhook manager
    - LTI integration
    """
    logger.info("="*60)
    logger.info("SLIDE 17: Third-Party Integrations")
    logger.info("="*60)

    # Navigate directly to integrations settings
    await page.goto(f"{BASE_URL}/organization/integrations", wait_until='networkidle', timeout=30000)
    await asyncio.sleep(3)
    await remove_banners(page)

    # Start recording
    recorder.start_recording(VIDEOS_DIR / "slide_17_integrations.mp4")
    await asyncio.sleep(1)

    # Show overview (5s)
    await asyncio.sleep(5)

    # Scroll to Slack integration (6s)
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(5)

    # Scroll to Calendar sync (6s)
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(5)

    # Scroll to OAuth connections (6s)
    await smooth_scroll(page, 900, 1000)
    await asyncio.sleep(5)

    # Scroll to webhooks (6s)
    await smooth_scroll(page, 1200, 1000)
    await asyncio.sleep(5)

    # Scroll back to show LTI (6s)
    await smooth_scroll(page, 200, 1000)
    await asyncio.sleep(5)

    recorder.stop_recording()
    logger.info("Slide 17 complete")


async def record_slide_18_accessibility(page, recorder):
    """
    Slide 18: Accessibility Settings (30 seconds)

    Shows accessibility options:
    - Font size adjustment
    - Color scheme selection
    - Motion preferences
    - Focus indicators
    - Screen reader options
    - Keyboard shortcuts
    """
    logger.info("="*60)
    logger.info("SLIDE 18: Accessibility Settings")
    logger.info("="*60)

    # Navigate to accessibility settings (works without login)
    await page.goto(f"{BASE_URL}/settings/accessibility", wait_until='networkidle', timeout=30000)
    await asyncio.sleep(3)
    await remove_banners(page)

    # Start recording
    recorder.start_recording(VIDEOS_DIR / "slide_18_accessibility.mp4")
    await asyncio.sleep(1)

    # Show overview (4s)
    await asyncio.sleep(4)

    # Scroll to font size options (5s)
    await smooth_scroll(page, 250, 1000)
    await asyncio.sleep(4)

    # Scroll to color schemes (5s)
    await smooth_scroll(page, 500, 1000)
    await asyncio.sleep(4)

    # Scroll to motion preferences (5s)
    await smooth_scroll(page, 750, 1000)
    await asyncio.sleep(4)

    # Scroll to keyboard shortcuts (5s)
    await smooth_scroll(page, 1000, 1000)
    await asyncio.sleep(4)

    # Scroll back to top (4s)
    await smooth_scroll(page, 0, 1000)
    await asyncio.sleep(3)

    recorder.stop_recording()
    logger.info("Slide 18 complete")


async def record_slide_19_mobile(page, recorder, context):
    """
    Slide 19: Mobile Experience (28 seconds)

    Shows mobile-optimized UI:
    - Responsive design on phone viewport
    - Touch-friendly navigation
    - Course cards with swipe gesture hints
    - Offline sync indicator
    """
    logger.info("="*60)
    logger.info("SLIDE 19: Mobile Experience")
    logger.info("="*60)

    # Create a mobile viewport (iPhone 12 Pro dimensions)
    mobile_page = await context.new_page()
    await mobile_page.set_viewport_size({'width': 390, 'height': 844})

    # Navigate to homepage in mobile view (shows responsive design)
    await mobile_page.goto(f"{BASE_URL}/", wait_until='networkidle', timeout=30000)
    await asyncio.sleep(3)
    await remove_banners(mobile_page)

    # For recording, we need to show this in a centered position
    # Create a wrapper that shows mobile view centered
    await mobile_page.evaluate("""
        () => {
            document.body.style.margin = '0';
            document.body.style.padding = '0';
        }
    """)

    # Start recording (with mobile dimensions)
    recorder.start_recording(VIDEOS_DIR / "slide_19_mobile.mp4", width=390, height=844)
    await asyncio.sleep(1)

    # Show dashboard (5s)
    await asyncio.sleep(5)

    # Scroll through content (5s)
    await smooth_scroll(mobile_page, 300, 800)
    await asyncio.sleep(4)

    # Navigate to courses (5s)
    try:
        await mobile_page.click('a[href*="courses"], button:has-text("Courses")')
        await asyncio.sleep(4)
    except:
        await asyncio.sleep(5)

    # Scroll through courses (5s)
    await smooth_scroll(mobile_page, 400, 800)
    await asyncio.sleep(4)

    # Scroll back to show offline indicator (5s)
    await smooth_scroll(mobile_page, 0, 800)
    await asyncio.sleep(4)

    recorder.stop_recording()
    await mobile_page.close()
    logger.info("Slide 19 complete")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    """Main execution - record all 5 enhancement slides"""
    print("="*70)
    print("DEMO VIDEO RECORDING - Enhancement Slides 15-19")
    print("="*70)
    print(f"  Output: {VIDEOS_DIR}")
    print(f"  Resolution: {RESOLUTION[0]}x{RESOLUTION[1]} @ {FRAME_RATE}fps")
    print(f"  Codec: H.264 (libx264)")
    print("="*70)
    print()

    # Ensure output directory exists
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    recorder = FFmpegRecorder()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
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

        # Record each slide
        slides = [
            ("15", "Learning Analytics Dashboard", record_slide_15_learning_analytics),
            ("16", "Instructor Insights Dashboard", record_slide_16_instructor_insights),
            ("17", "Third-Party Integrations", record_slide_17_integrations),
            ("18", "Accessibility Settings", record_slide_18_accessibility),
        ]

        for slide_num, title, func in slides:
            print(f"\n{'='*70}")
            print(f"Recording Slide {slide_num}: {title}")
            print(f"{'='*70}")

            try:
                if slide_num == "19":
                    await func(page, recorder, context)
                else:
                    await func(page, recorder)

                # Verify output
                video_file = VIDEOS_DIR / f"slide_{slide_num}_*.mp4"
                video_files = list(VIDEOS_DIR.glob(f"slide_{slide_num}_*.mp4"))
                if video_files:
                    vf = video_files[0]
                    size_mb = vf.stat().st_size / (1024 * 1024)
                    print(f"   SUCCESS: {vf.name} ({size_mb:.2f} MB)")
                else:
                    print(f"   ERROR: Video file not found")

            except Exception as e:
                logger.error(f"   FAILED: {e}")

            await asyncio.sleep(2)

        # Record mobile slide separately (needs different viewport)
        print(f"\n{'='*70}")
        print("Recording Slide 19: Mobile Experience")
        print(f"{'='*70}")

        try:
            await record_slide_19_mobile(page, recorder, context)
            video_files = list(VIDEOS_DIR.glob("slide_19_*.mp4"))
            if video_files:
                vf = video_files[0]
                size_mb = vf.stat().st_size / (1024 * 1024)
                print(f"   SUCCESS: {vf.name} ({size_mb:.2f} MB)")
        except Exception as e:
            logger.error(f"   FAILED: {e}")

        await context.close()
        await browser.close()

    print("\n" + "="*70)
    print("RECORDING COMPLETE")
    print("="*70)
    print(f"\nVideos saved to: {VIDEOS_DIR}")
    print("\nGenerated files:")
    for f in sorted(VIDEOS_DIR.glob("slide_1[5-9]_*.mp4")):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  - {f.name} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    asyncio.run(main())
